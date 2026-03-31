from typing import Literal

Trend = Literal["up", "down", "range"]


def detect_trend(higher_highs: int, higher_lows: int, lower_highs: int, lower_lows: int) -> Trend:
    if higher_highs >= 2 and higher_lows >= 2:
        return "up"
    if lower_highs >= 2 and lower_lows >= 2:
        return "down"
    return "range"
