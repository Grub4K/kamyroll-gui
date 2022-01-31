import json
import logging

from PySide6.QtCore import QEventLoop, QUrl, QUrlQuery
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest

from .blocking import wait_for_event



_logger = logging.getLogger(__name__)

class WebManager:
    def __init__(self, /):
        self._network_manager = QNetworkAccessManager()

    def _get_request(self, url, /, params=None):
        q_url = QUrl(url)

        if params:
            query = QUrlQuery()
            for key, value in params.items():
                query.addQueryItem(key, value)

            q_url.setQuery(query.query())

        return QNetworkRequest(q_url)

    def get(self, /, url, params=None):
        _logger.info("GET %s", url)
        request = self._get_request(url, params)

        reply = self._network_manager.get(request)
        wait_for_event(reply.finished)

        data = bytes(reply.readAll())
        _logger.debug("Web response: %s", data)
        return data

    def post(self, /, url, data=None, params=None):
        _logger.info("POST %s", url)
        data = data or {}
        bin_data = json.dumps(data).encode()

        request = self._get_request(url, params)

        reply = self._network_manager.post(request, bin_data)
        wait_for_event(reply.finished)

        data = bytes(reply.readAll())
        _logger.debug("Web response: %s", data)
        return data

web_manager = WebManager()
