from dataclasses import dataclass


@dataclass
class Tick:
    bid: float
    ask: float


class MT5StubAdapter:
    """Temporary local stub until real MT5 integration is added."""

    def connect(self) -> bool:
        return True

    def get_tick(self, symbol: str) -> Tick:
        return Tick(bid=2450.10, ask=2450.40)
