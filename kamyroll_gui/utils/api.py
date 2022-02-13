import json
import logging


from . import json_helper
from .web_manager import web_manager
from .blocking import wait
from ..data_types import (
    ConfigResponse,
    StreamResponse,
)



BASE_URL = "https://kamyroll-server.herokuapp.com"


_logger = logging.getLogger(__name__)


class ApiError(Exception):
    pass


def parse_url(url):
    for service in config.services:
        if not service.active:
            continue

        match = service.regex.match(url)
        if not match:
            continue

        return service.id, match.groupdict()
    return None

def get_config():
    global config

    data = call_api("/v2/config")
    config = json_helper.load(data, ConfigResponse)
    _logger.info("Loaded config: %s", config)

def get_media(name, params, /, username=None, password=None, retries=3):
    use_login = username and password
    use_bypass = False

    params["channel_id"] = name

    if name=="adn":
        params["country"] = "fr"

    if use_login:
        params["email"] = username
        params["password"] = password
    else:
        use_bypass = True

    if retries < 1:
        retries = 1
    data = {}
    for _ in range(retries):
        params["bypass"] = "true"
        if not use_bypass:
            del params["bypass"]

        data = call_api("/v1/streams", params=params)
        if "error" in data:
            return_val = _handle_error(data["code"], data["message"],
                use_login, name)
            if return_val is not None:
                use_bypass = return_val
            continue
        try:
            return json_helper.load(data, StreamResponse)
        except Exception as error:
            message = f"Unknown error while parsing response: {error}"
            raise ApiError(message)

    _logger.error("Api call failed after too many retries")
    message = data.get("message") or "Unknown error"
    raise ApiError(message)


def call_api(path, /, params=None):
    _logger.info("Calling api endpoing %s with %s", path, params)
    url = BASE_URL + path
    data = web_manager.get(url, params=params)

    # TEMP: this checks if we have internet
    if not data:
        raise ApiError("Internet or API not available")

    json_data = {}
    try:
        json_data = json.loads(data)
    except ValueError as exception:
        _logger.error("Error decoding returned json: %s", exception)

    if "error" in json_data:
        error_code = json_data.get("code", "unknown")
        error_message = json_data.get("message", "Unknown Error")
        _logger.error("Api call returned '%s': %s", error_code, error_message)
        json_data["code"] = error_code
        json_data["message"] = error_message

    return json_data


def _handle_error(code, message, use_login, channel_id):
    _logger.error("Api returned error code %s: %s", code, message)
    if code == "premium_only":
        if use_login:
            message += "\nConsider using the premium bypass"
            raise ApiError(message)

        # this should only ever happen if
        # the api backend user runs out of premium
        raise ApiError("Unexpected bypass error, try again later")

    if code == "bad_player_connection":
        wait(2000)
        return

    if code == "bad_initialize":
        wait(2000)
        return

    if code in ["unknown_id"]:
        raise ApiError("The provided id of the url is not valid")


    wait(1000)
    return

config = None
