from datetime import datetime

TIME_INPUT_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

"2023-06-19T02:22:58.166"
GALLOP_TIME_MICROS_INPUT_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
GALLOP_TIME_INPUT_FORMAT = "%Y-%m-%dT%H:%M:%S"


def format_timestring(timestamp: str):
    return datetime.strptime(timestamp, TIME_INPUT_FORMAT).strftime(
        "%Y-%m-%dT%H:%M:%S+0000"
    )


def or_else(value, default_value="0"):
    return default_value if not value else value


def format_gallop_timestamp(timestamp: str):
    try:
        return datetime.strptime(timestamp, GALLOP_TIME_INPUT_FORMAT)
    except ValueError:
        return datetime.strptime(timestamp, GALLOP_TIME_MICROS_INPUT_FORMAT)
