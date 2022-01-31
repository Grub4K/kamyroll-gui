import re
import logging

from datetime import timedelta

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QMessageBox



re_hex = r"[\da-fA-F]"
re_float = r"-?\d*(?:\.\d+)?"
re_time = r"-?\d+:\d+:\d+\.\d+"

TIME_REGEX = re.compile(r"(?P<hours>-?\d+?):(?P<minutes>-?\d+?):(?P<seconds>-?\d+?\.\d+?)?")
PROGRESS_REGEX = re.compile((r""
    + r"(?:"
        + r"(?:"
            # Current frame position
            + r"frame=\s*?(?P<frame>\d+) "
            # fps getting encoded (not fps of the video)
            + r"fps=\s*?(?P<fps>{float}) "
        + r")?"
        # Stream quality for current timespan
        + r"q=\s*?(?P<q>{float}) "
    + r")?"
    # Indicator for last progress update
    + r"(?P<last>L)?"
    # quantization parameter histogram as concated hex ints
    + r"(?P<qp_history>{hex}+)?"
    # peak signal to noise ratio
    + r"(?:PSNR="
        + r"Y:(?P<psnr_y>{float}) "
        + r"U:(?P<psnr_u>{float}) "
        + r"V:(?P<psnr_v>{float}) "
        + r"*:(?P<psnr_all>{float}) "
    + r")?"
    # output file size
    + r"size=(?:(?:N/A)|(?:\s*?(?P<size>{float})kB)) "
    # output file length as time
    + r"time=(?:(?:N/A)|(?:\s*?(?P<time>{time}))) "
    # output bitrate
    + r"bitrate=(?:(?:N/A)|(?:\s*?(?P<bitrate>{float})kbits/s))"
    + r"(?:"
        # duplicate frames
        + r" dup=(?P<dup>\d+)"
        # dropped frames
        + r" drop=(?P<drop>\d+)"
    + r")?"
    # encoding speed ratio (encoding / realtime)
    + r" speed=(?:(?:N/A)|(?:\s*?(?P<speed>[^x]+)x))"
).format(time=re_time, hex=re_hex, float=re_float))


class FFmpeg:
    _logger = logging.getLogger(__name__).getChild(__qualname__)

    def __init__(self, /, parent, progress, text_edit,
            success_callback, fail_callback):
        self.parent = parent
        self.success_callback = success_callback
        self.fail_callback = fail_callback
        self.is_stopped = True
        self.first_update = True
        self.max_time: timedelta

        self.leftover_bytes = b""

        self.progress = progress
        self.text_edit = text_edit

        self.process = QProcess()
        self.process.readyReadStandardError.connect(self.readAll)
        self.process.finished.connect(self.finished)

    def start(self, arguments, max_time, /):
        self.max_time = max_time
        self.progress.setMaximum(0)

        prepended_args = [
            "-hide_banner",
            "-stats",
            "-loglevel", "error",
            "-reconnect", "1",
            #"-reconnect_at_eof", "1",
            "-reconnect_streamed", "1",
            "-reconnect_on_network_error", "1",
            "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 Edg/94.0.992.50",
        ]
        arguments = prepended_args + arguments

        self.is_stopped = False
        self.first_update = True
        self._logger.info("Started ffmpeg process with arguments: %r", arguments)
        self.process.start("ffmpeg", arguments)

    def stop(self, /):
        self.is_stopped = True
        self.process.kill()
        self._logger.info("FFmpeg process stopped")

    def readAll(self, /):
        data = bytes(self.process.readAllStandardError())
        self._logger.debug("Read data: %s", data)
        self._process_data(data)

    def _process_data(self, chunk, /):
        if self.is_stopped:
            return
        # newline translation
        chunk = chunk.replace(b"\r\n", b"\n")
        chunk = chunk.replace(b"\r", b"\n")
        if b"\n" in chunk:
            split_chunk = chunk.split(b"\n")
            split_chunk[0] = self.leftover_bytes + split_chunk[0]
            self.leftover_bytes = split_chunk.pop()

            for line in map(bytes.decode, split_chunk):
                if not line:
                    continue
                self.text_edit.append(line)
                self._process_line(line)
        else:
            self.leftover_bytes += chunk

        if self.leftover_bytes.endswith(b"[y/N] "):
            line = self.leftover_bytes.decode()
            self.text_edit.insertPlainText(line)
            question = line.rstrip("[y/N] ")
            self.ask_question(question)
            self.leftover_bytes = b""

    def ask_question(self, question, /):
        reply = QMessageBox.question(self.parent,
            "Question - FFmpeg - Kamyroll", question)
        response = "y" if reply == QMessageBox.Yes else "n"
        self.text_edit.insertPlainText(response)
        self.process.write(response.encode() + b'\n')

    def _process_line(self, line, /):
        if self.is_stopped:
            return

        if line.startswith("["):
            self.is_stopped = True
            self.process.kill()

            module, _, message = line.partition("] ")
            module, _, offset = module[1:].partition("@")
            module = module.strip()
            offset = offset.strip()
            message, _, data = message.partition(": ")
            info_line = "\n".join([
                f"Module: {module}",
                f"Offset: {offset}",
                f"Message: {message}",
                f"Data: {data}"
            ])
            QMessageBox.critical(self.parent, "Error - FFmpeg - Kamyroll", info_line)
            self._logger.error("FFmpeg error: %s", line)

            self.fail_callback()
            return

        match = PROGRESS_REGEX.match(line)
        if match:
            try:
                parsed_time = _parse_ffmpeg_time(match["time"])
            except ValueError:
                return
            if self.first_update:
                maximum = int(self.max_time.total_seconds())
                self.progress.setMaximum(maximum)

            if parsed_time > self.max_time:
                self.progress.setMaximum(0)
                self.progress.setValue(0)
                return

            self.progress.setValue(int(parsed_time.total_seconds()))
            return

        QMessageBox.information(self.parent, "Info - FFmpeg - Kamyroll", line)

    def finished(self, exit_code, status: QProcess.ExitStatus, /):
        if status == QProcess.ExitStatus.CrashExit:
            if not self.is_stopped:
                self._logger.info("FFmpeg process crashed (%s)", exit_code)
                self.fail_callback()
            return

        # status == NormalExit
        self.progress.setMaximum(1)
        self.progress.setValue(1)
        self._logger.info("FFmpeg process exited successfully (%s)", exit_code)
        self.success_callback()


def _parse_ffmpeg_time(time: str):
    match = TIME_REGEX.fullmatch(time)
    if not match:
        raise ValueError("Unknown time format")

    hours = int(match["hours"])
    minutes = int(match["minutes"])
    seconds = float(match["seconds"])

    return timedelta(hours=hours, minutes=minutes, seconds=seconds)
