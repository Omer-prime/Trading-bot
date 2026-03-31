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

    def place_order(self, side: str, lot_size: float, stop_loss: float, take_profit: float) -> dict:
        return {
            "status": "stubbed",
            "side": side,
            "lot_size": lot_size,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        }
