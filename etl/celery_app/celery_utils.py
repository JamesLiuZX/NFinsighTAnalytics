from datetime import datetime


def format_timestring(timestamp: str):
    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
