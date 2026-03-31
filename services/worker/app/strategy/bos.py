def bos_confirmed(direction: str, strong_close: bool) -> bool:
    return direction in {"buy", "sell"} and strong_close
