import string



SAFE_CHAR_VALUES = {
    *"[]()^ #%&!@+={}'`~-_",
    *string.ascii_letters,
    *string.digits,
}


def escape_name(name: str, escape="_"):
    return "".join(char if char in SAFE_CHAR_VALUES else escape
        for char in name)


def format_name(fmt: str, data: dict):
    transformed_data = {
        key: escape_name(str(value))
        for key, value in data.items()
    }
    return fmt.format(**transformed_data)
