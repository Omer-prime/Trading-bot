from __future__ import annotations

import platform
import time
from dataclasses import dataclass
from typing import Any

from app.adapters.mt5_connectivity import MT5ConnectivityChecker, MT5ConnectivityResult
from app.api_client import WorkerApiClient
from app.core.config import settings
from app.services.market_data import MarketDataService
from app.services.signal_logger import SignalLogger
from app.services.strategy import StrategyDecision, StrategyEvaluationService


@dataclass
class DryRunLoopResult:
    runtime_ok: bool
    mt5_ok: bool
    decision: StrategyDecision | None
    heartbeat_summary: dict[str, Any]
    error: str | None = None


class RuntimeLoop:
    def __init__(
        self,
        *,
        api_client: WorkerApiClient,
        connectivity_checker: MT5ConnectivityChecker,
        strategy_service: StrategyEvaluationService,
        signal_logger: SignalLogger,
    ):
        self.api_client = api_client
        self.connectivity_checker = connectivity_checker
        self.strategy_service = strategy_service
        self.signal_logger = signal_logger

    def run_once(self) -> DryRunLoopResult:
        registered_worker = self.api_client.register_worker(
            account_id=settings.account_id,
            machine_name=settings.worker_machine_name or platform.node() or "unknown-worker",
            version=settings.worker_version,
        )
        worker_id = registered_worker["id"]

        try:
            runtime = self.api_client.fetch_runtime(worker_id=worker_id)
            account = runtime["account"]
            config = runtime["bot_config"]
            symbol = account["symbol"]

            connectivity = self.connectivity_checker.check(
                expected_login=account["mt5_login"],
                symbol=symbol,
            )
            if not connectivity.ok:
                summary = self._summary(
                    runtime_ok=True,
                    mt5_ok=False,
                    symbol=symbol,
                    timeframes=[],
                    decision=None,
                    logged_signal=None,
                    error=connectivity.error,
                )
                self.api_client.heartbeat(
                    worker_id=worker_id,
                    status="error",
                    last_error=connectivity.error,
                    dry_run_summary=summary,
                )
                return DryRunLoopResult(True, False, None, summary, connectivity.error)

            market_data = MarketDataService(self.connectivity_checker.mt5_module)
            timeframes = [
                config["entry_timeframe"],
                config["confirmation_timeframe"],
                config["bias_timeframe"],
            ]
            candles = market_data.get_runtime_candles(
                symbol=symbol,
                entry_timeframe=config["entry_timeframe"],
                confirmation_timeframe=config["confirmation_timeframe"],
                bias_timeframe=config["bias_timeframe"],
            )
            decision = self.strategy_service.evaluate(runtime=runtime, candles_by_timeframe=candles)
            logged_signal = self.signal_logger.log_decision(
                account_id=account["id"],
                worker_id=worker_id,
                timeframes=timeframes,
                market_snapshot=self._market_snapshot(candles),
                decision=decision,
            )

            summary = self._summary(
                runtime_ok=True,
                mt5_ok=True,
                symbol=symbol,
                timeframes=timeframes,
                decision=decision,
                logged_signal=logged_signal,
                error=None,
            )
            self.api_client.heartbeat(
                worker_id=worker_id,
                status="online",
                dry_run_summary=summary,
            )
            return DryRunLoopResult(True, True, decision, summary)
        except Exception as exc:
            summary = self._summary(
                runtime_ok=False,
                mt5_ok=False,
                symbol=None,
                timeframes=[],
                decision=None,
                logged_signal=None,
                error=str(exc),
            )
            self.api_client.heartbeat(
                worker_id=worker_id,
                status="error",
                last_error=str(exc),
                dry_run_summary=summary,
            )
            return DryRunLoopResult(False, False, None, summary, str(exc))

    def run_forever(self, *, max_cycles: int | None = None) -> None:
        completed_cycles = 0
        while max_cycles is None or completed_cycles < max_cycles:
            result = self.run_once()
            completed_cycles += 1
            sleep_seconds = (
                settings.dry_run_poll_interval_seconds
                if result.error is None
                else settings.dry_run_failure_backoff_seconds
            )
            time.sleep(sleep_seconds)

    @staticmethod
    def _summary(
        *,
        runtime_ok: bool,
        mt5_ok: bool,
        symbol: str | None,
        timeframes: list[str],
        decision: StrategyDecision | None,
        logged_signal: dict[str, Any] | None,
        error: str | None,
    ) -> dict[str, Any]:
        last_result = {
            "signal_id": logged_signal.get("id") if logged_signal else None,
            "status": decision.status if decision else None,
            "reason": decision.reason if decision else error,
            "direction": decision.direction if decision else None,
            "trend_bias": decision.trend_bias if decision else None,
            "rr_estimate": decision.rr_estimate if decision else None,
            "rejection_reason": None if decision and decision.accepted else (decision.reason if decision else error),
        }
        return {
            "runtime_ok": runtime_ok,
            "mt5_ok": mt5_ok,
            "last_signal_status": last_result["status"],
            "last_signal_reason": last_result["reason"],
            "last_symbol_checked": symbol,
            "last_timeframes_checked": timeframes,
            "last_dry_run_result": last_result,
            "dry_run": True,
        }

    @staticmethod
    def _market_snapshot(candles: dict[str, list[dict]]) -> dict[str, dict | None]:
        return {
            timeframe: {
                "first": values[0] if values else None,
                "last": values[-1] if values else None,
                "count": len(values),
            }
            for timeframe, values in candles.items()
        }


def build_runtime_loop() -> RuntimeLoop:
    api_client = WorkerApiClient(
        base_url=settings.api_base_url.rstrip("/"),
        worker_secret=settings.worker_shared_secret,
        timeout_seconds=settings.api_timeout_seconds,
    )
    return RuntimeLoop(
        api_client=api_client,
        connectivity_checker=MT5ConnectivityChecker(terminal_path=settings.mt5_terminal_path),
        strategy_service=StrategyEvaluationService(),
        signal_logger=SignalLogger(api_client),
    )
