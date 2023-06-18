from datetime import datetime


def format_timestring(timestamp: str):
    return datetime \
        .strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ") \
        .strftime("%Y-%m-%dT%H:%M:%S+0000")


def or_else(value):
    return "0" if not value else value
