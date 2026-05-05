from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.strategy.news_filter import high_impact_news_blocked
from app.strategy.session_filter import trading_session_allowed


@dataclass
class StrategyDecision:
    status: str
    reason: str
    symbol: str
    timeframe: str
    direction: str
    trend_bias: str
    entry_price: float | None
    stop_loss: float | None
    take_profit: float | None
    rr_estimate: float | None
    liquidity_sweep_detected: bool
    bos_detected: bool

    @property
    def accepted(self) -> bool:
        return self.status == "accepted"

    def as_signal_payload(
        self,
        *,
        account_id: int,
        worker_id: int | None = None,
        timeframes: list[str] | None = None,
        market_snapshot: dict | None = None,
    ) -> dict:
        return {
            "account_id": account_id,
            "worker_id": worker_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timeframes_json": timeframes,
            "direction": self.direction,
            "trend_bias": self.trend_bias,
            "liquidity_sweep_detected": self.liquidity_sweep_detected,
            "bos_detected": self.bos_detected,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "rr_estimate": self.rr_estimate,
            "status": self.status,
            "rejection_reason": None if self.accepted else self.reason,
            "payload_json": {
                "dry_run": True,
                "reason": self.reason,
                "market_snapshot": market_snapshot,
            },
        }


class StrategyEvaluationService:
    def evaluate(
        self,
        *,
        runtime: dict,
        candles_by_timeframe: dict[str, list[dict]],
        now: datetime | None = None,
        minutes_to_news_event: int | None = None,
    ) -> StrategyDecision:
        checked_at = now or datetime.now(timezone.utc)
        account = runtime["account"]
        config = runtime["bot_config"]
        symbol = account["symbol"]
        entry_timeframe = config["entry_timeframe"]
        bias_timeframe = config["bias_timeframe"]

        if config.get("london_newyork_only") and not trading_session_allowed(checked_at):
            return self._rejected(symbol, entry_timeframe, "range", "session filter blocked")

        if config.get("news_filter_enabled") and high_impact_news_blocked(minutes_to_news_event):
            return self._rejected(symbol, entry_timeframe, "range", "news filter blocked")

        trend_bias = self._trend_bias(candles_by_timeframe[bias_timeframe])
        if config.get("trend_only") and trend_bias == "range":
            return self._rejected(symbol, entry_timeframe, trend_bias, "trend filter blocked")

        entry_candles = candles_by_timeframe[entry_timeframe]
        if len(entry_candles) < 3:
            return self._rejected(symbol, entry_timeframe, trend_bias, "not enough candle data")

        direction = "buy" if trend_bias == "up" else "sell"
        entry_price = entry_candles[-1]["close"]
        recent_low = min(candle["low"] for candle in entry_candles[-3:])
        recent_high = max(candle["high"] for candle in entry_candles[-3:])
        min_rr = float(config["min_rr"])

        if direction == "buy":
            stop_loss = recent_low
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * min_rr)
        else:
            stop_loss = recent_high
            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * min_rr)

        if risk <= 0:
            return self._rejected(symbol, entry_timeframe, trend_bias, "invalid risk candidate")

        return StrategyDecision(
            status="accepted",
            reason="dry-run candidate generated",
            symbol=symbol,
            timeframe=entry_timeframe,
            direction=direction,
            trend_bias=trend_bias,
            entry_price=round(entry_price, 6),
            stop_loss=round(stop_loss, 6),
            take_profit=round(take_profit, 6),
            rr_estimate=min_rr,
            liquidity_sweep_detected=True,
            bos_detected=True,
        )

    @staticmethod
    def _trend_bias(candles: list[dict]) -> str:
        if len(candles) < 2:
            return "range"
        first_close = candles[0]["close"]
        last_close = candles[-1]["close"]
        if last_close > first_close:
            return "up"
        if last_close < first_close:
            return "down"
        return "range"

    @staticmethod
    def _rejected(symbol: str, timeframe: str, trend_bias: str, reason: str) -> StrategyDecision:
        return StrategyDecision(
            status="rejected",
            reason=reason,
            symbol=symbol,
            timeframe=timeframe,
            direction="none",
            trend_bias=trend_bias,
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            rr_estimate=None,
            liquidity_sweep_detected=False,
            bos_detected=False,
        )
