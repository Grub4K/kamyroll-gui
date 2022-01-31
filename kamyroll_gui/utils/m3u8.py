import re



PROGRAM_INFO_REGEX = re.compile(r'[:,]([^=]*)=(?:"([^"]*)"|([^,]*))')


def get_resolutions(data, /):
    audio_program_id = None
    resolutions = {}
    data_lines = (
        line
        for line in data.splitlines(keepends=False)
        if line.startswith("#EXT-X-STREAM-INF:") or line.startswith("#EXT-X-MEDIA:")
    )
    for program_id, line in enumerate(data_lines):
        matches = PROGRAM_INFO_REGEX.findall(line)
        info_dict = {
            key: first or second
            for key, first, second in matches
        }

        if "RESOLUTION" in info_dict:
            resolution = info_dict["RESOLUTION"]
            bandwidth = int(info_dict["BANDWIDTH"])
            frame_rate = float(info_dict.get("FRAME-RATE", 30))
            width, _, height = resolution.partition("x")
            width, height = int(width), int(height)
            item = (width, height, frame_rate, bandwidth, program_id)

            if height in resolutions:
                if resolutions[height] > item:
                    continue

            resolutions[height] = item

        elif "TYPE" in info_dict:
            # VERIFY
            if info_dict["TYPE"].lower() == "audio":
                audio_program_id = program_id

    resolution_dict = {}
    for key, value in resolutions.items():
        _, _, _, _, program_id = value
        program_ids = [program_id]
        if audio_program_id is not None:
            program_ids.append(audio_program_id)
        resolution_dict[key] = program_ids

    return resolution_dict
