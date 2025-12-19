import time


def is_time_up(end_timestamp: float) -> bool:
    return time.monotonic() - end_timestamp >= 0
