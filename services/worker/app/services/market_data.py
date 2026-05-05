from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


TIMEFRAMES = {
    "M1": "TIMEFRAME_M1",
    "M5": "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1",
}


@dataclass
class Candle:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int

    def as_dict(self) -> dict:
        return {
            "time": self.time.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "tick_volume": self.tick_volume,
        }


class MarketDataService:
    def __init__(self, mt5_module: Any):
        self.mt5 = mt5_module

    def get_candles(self, *, symbol: str, timeframe: str, count: int = 120) -> list[dict]:
        mt5_timeframe = self._resolve_timeframe(timeframe)
        raw_rates = self.mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)
        if raw_rates is None:
            raise RuntimeError(f"Could not fetch candles for {symbol} {timeframe}")
        return [self._normalize_rate(rate).as_dict() for rate in raw_rates]

    def get_runtime_candles(
        self,
        *,
        symbol: str,
        entry_timeframe: str,
        confirmation_timeframe: str,
        bias_timeframe: str,
        count: int = 120,
    ) -> dict[str, list[dict]]:
        return {
            entry_timeframe: self.get_candles(symbol=symbol, timeframe=entry_timeframe, count=count),
            confirmation_timeframe: self.get_candles(symbol=symbol, timeframe=confirmation_timeframe, count=count),
            bias_timeframe: self.get_candles(symbol=symbol, timeframe=bias_timeframe, count=count),
        }

    def _resolve_timeframe(self, timeframe: str):
        attr_name = TIMEFRAMES.get(timeframe)
        if not attr_name:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        return getattr(self.mt5, attr_name)

    @staticmethod
    def _normalize_rate(rate: Any) -> Candle:
        if isinstance(rate, dict):
            value = rate
        else:
            value = {
                "time": rate["time"],
                "open": rate["open"],
                "high": rate["high"],
                "low": rate["low"],
                "close": rate["close"],
                "tick_volume": rate["tick_volume"],
            }
        return Candle(
            time=datetime.fromtimestamp(int(value["time"]), tz=timezone.utc),
            open=float(value["open"]),
            high=float(value["high"]),
            low=float(value["low"]),
            close=float(value["close"]),
            tick_volume=int(value.get("tick_volume", 0)),
        )
