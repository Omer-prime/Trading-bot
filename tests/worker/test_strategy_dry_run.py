import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

WORKER_ROOT = Path(__file__).resolve().parents[2] / "services" / "worker"
sys.path.insert(0, str(WORKER_ROOT))
for module_name in list(sys.modules):
    if module_name == "app" or module_name.startswith("app."):
        del sys.modules[module_name]

from app.adapters.mt5_connectivity import MT5ConnectivityChecker
from app.core.config import settings
from app.services.runtime_loop import RuntimeLoop
from app.services.signal_logger import SignalLogger
from app.services.strategy import StrategyEvaluationService


class FakeMT5:
    TIMEFRAME_M1 = 1
    TIMEFRAME_M5 = 5
    TIMEFRAME_M15 = 15
    TIMEFRAME_M30 = 30
    TIMEFRAME_H1 = 60
    TIMEFRAME_H4 = 240
    TIMEFRAME_D1 = 1440

    def __init__(self, candles_by_timeframe):
        self.candles_by_timeframe = candles_by_timeframe
        self.execution_called = False

    def initialize(self, **kwargs):
        return True

    def terminal_info(self):
        return SimpleNamespace(name="MT5")

    def account_info(self):
        return SimpleNamespace(login=123456)

    def symbol_info(self, symbol):
        return SimpleNamespace(visible=True)

    def symbol_select(self, symbol, selected):
        return True

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        return self.candles_by_timeframe[timeframe]

    def last_error(self):
        return (0, "ok")

    def place_order(self, *args, **kwargs):
        self.execution_called = True
        raise AssertionError("dry-run must not place orders")


class FakeApiClient:
    def __init__(self, runtime):
        self.runtime = runtime
        self.logged_signals = []
        self.heartbeats = []

    def register_worker(self, **kwargs):
        return {"id": 10}

    def fetch_runtime(self, *, worker_id):
        return self.runtime

    def log_dry_run_signal(self, payload):
        self.logged_signals.append(payload)
        return {"id": len(self.logged_signals), **payload}

    def heartbeat(self, **payload):
        self.heartbeats.append(payload)
        return payload


def runtime_config(**overrides):
    config = {
        "entry_timeframe": "M5",
        "confirmation_timeframe": "H1",
        "bias_timeframe": "H4",
        "min_rr": 2.0,
        "trend_only": True,
        "london_newyork_only": False,
        "news_filter_enabled": False,
    }
    config.update(overrides)
    return {
        "account": {"id": 1, "mt5_login": "123456", "symbol": "XAUUSD"},
        "bot_config": config,
    }


def candles(start_close: float, end_close: float):
    return [
        {"time": 1, "open": start_close - 0.1, "high": start_close + 0.5, "low": start_close - 0.5, "close": start_close, "tick_volume": 100},
        {"time": 2, "open": end_close - 0.2, "high": end_close + 0.5, "low": end_close - 0.5, "close": end_close, "tick_volume": 120},
        {"time": 3, "open": end_close - 0.1, "high": end_close + 0.6, "low": end_close - 0.4, "close": end_close, "tick_volume": 130},
    ]


def candle_map(*, trend: str = "up"):
    bias = candles(100.0, 103.0) if trend == "up" else candles(100.0, 100.0)
    return {
        FakeMT5.TIMEFRAME_M5: candles(102.0, 103.0),
        FakeMT5.TIMEFRAME_H1: candles(101.0, 102.0),
        FakeMT5.TIMEFRAME_H4: bias,
    }


def test_strategy_generates_signal_in_happy_path():
    service = StrategyEvaluationService()

    decision = service.evaluate(
        runtime=runtime_config(),
        candles_by_timeframe={
            "M5": [candle for candle in candles(102.0, 103.0)],
            "H1": [candle for candle in candles(101.0, 102.0)],
            "H4": [candle for candle in candles(100.0, 103.0)],
        },
        now=datetime(2026, 5, 5, 13, tzinfo=timezone.utc),
    )

    assert decision.accepted is True
    assert decision.direction == "buy"
    assert decision.trend_bias == "up"
    assert decision.rr_estimate == 2.0


def test_strategy_rejects_when_trend_filter_fails():
    service = StrategyEvaluationService()

    decision = service.evaluate(
        runtime=runtime_config(trend_only=True),
        candles_by_timeframe={
            "M5": candles(102.0, 103.0),
            "H1": candles(101.0, 102.0),
            "H4": candles(100.0, 100.0),
        },
        now=datetime(2026, 5, 5, 13, tzinfo=timezone.utc),
    )

    assert decision.accepted is False
    assert decision.reason == "trend filter blocked"


def test_strategy_rejects_when_session_or_news_filter_blocks():
    service = StrategyEvaluationService()

    session_decision = service.evaluate(
        runtime=runtime_config(london_newyork_only=True),
        candles_by_timeframe={
            "M5": candles(102.0, 103.0),
            "H1": candles(101.0, 102.0),
            "H4": candles(100.0, 103.0),
        },
        now=datetime(2026, 5, 5, 3, tzinfo=timezone.utc),
    )
    assert session_decision.reason == "session filter blocked"

    news_decision = service.evaluate(
        runtime=runtime_config(news_filter_enabled=True),
        candles_by_timeframe={
            "M5": candles(102.0, 103.0),
            "H1": candles(101.0, 102.0),
            "H4": candles(100.0, 103.0),
        },
        now=datetime(2026, 5, 5, 13, tzinfo=timezone.utc),
        minutes_to_news_event=0,
    )
    assert news_decision.reason == "news filter blocked"


def test_dry_run_loop_logs_signal_heartbeat_and_never_executes(monkeypatch):
    monkeypatch.setattr(settings, "account_id", 1)
    fake_mt5 = FakeMT5(candle_map(trend="up"))
    api_client = FakeApiClient(runtime_config())
    loop = RuntimeLoop(
        api_client=api_client,
        connectivity_checker=MT5ConnectivityChecker(mt5_module=fake_mt5),
        strategy_service=StrategyEvaluationService(),
        signal_logger=SignalLogger(api_client),
    )

    result = loop.run_once()

    assert result.decision.accepted is True
    assert fake_mt5.execution_called is False
    assert api_client.logged_signals[0]["status"] == "accepted"
    assert api_client.logged_signals[0]["worker_id"] == 10
    assert api_client.logged_signals[0]["timeframes_json"] == ["M5", "H1", "H4"]
    assert api_client.logged_signals[0]["payload_json"]["market_snapshot"]["M5"]["count"] == 3
    assert api_client.heartbeats[-1]["status"] == "online"
    summary = api_client.heartbeats[-1]["dry_run_summary"]
    assert summary["runtime_ok"] is True
    assert summary["mt5_ok"] is True
    assert summary["last_signal_status"] == "accepted"
    assert summary["last_dry_run_result"]["signal_id"] == 1
    assert summary["last_dry_run_result"]["direction"] == "buy"
    assert summary["last_symbol_checked"] == "XAUUSD"
    assert summary["last_timeframes_checked"] == ["M5", "H1", "H4"]


def test_dry_run_loop_uses_failure_backoff(monkeypatch):
    monkeypatch.setattr(settings, "account_id", 1)
    monkeypatch.setattr(settings, "dry_run_failure_backoff_seconds", 7)
    sleeps = []
    monkeypatch.setattr("app.services.runtime_loop.time.sleep", sleeps.append)

    class FailingApiClient(FakeApiClient):
        def fetch_runtime(self, *, worker_id):
            raise RuntimeError("runtime unavailable")

    loop = RuntimeLoop(
        api_client=FailingApiClient(runtime_config()),
        connectivity_checker=MT5ConnectivityChecker(mt5_module=FakeMT5(candle_map())),
        strategy_service=StrategyEvaluationService(),
        signal_logger=SignalLogger(FailingApiClient(runtime_config())),
    )

    loop.run_forever(max_cycles=1)

    assert sleeps == [7]
