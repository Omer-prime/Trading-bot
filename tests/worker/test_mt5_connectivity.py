import sys
from pathlib import Path
from types import SimpleNamespace

WORKER_ROOT = Path(__file__).resolve().parents[2] / "services" / "worker"
sys.path.insert(0, str(WORKER_ROOT))

from app.adapters.mt5_connectivity import MT5ConnectivityChecker
from app.runtime import check_runtime_connectivity


class FakeMT5:
    def __init__(
        self,
        *,
        initialize_result=True,
        terminal_info=None,
        account_info=None,
        symbol_info=None,
        symbol_select_result=True,
    ):
        self.initialize_result = initialize_result
        self._terminal_info = terminal_info if terminal_info is not None else SimpleNamespace(name="MT5")
        self._account_info = account_info if account_info is not None else SimpleNamespace(login=123456)
        self._symbol_info = symbol_info if symbol_info is not None else SimpleNamespace(visible=True)
        self.symbol_select_result = symbol_select_result
        self.shutdown_called = False

    def initialize(self, **kwargs):
        self.initialize_kwargs = kwargs
        return self.initialize_result

    def terminal_info(self):
        return self._terminal_info

    def account_info(self):
        return self._account_info

    def symbol_info(self, symbol):
        self.symbol_checked = symbol
        return self._symbol_info

    def symbol_select(self, symbol, selected):
        self.symbol_selected = (symbol, selected)
        return self.symbol_select_result

    def last_error(self):
        return (1, "fake mt5 error")

    def shutdown(self):
        self.shutdown_called = True


def test_mt5_connectivity_success():
    fake_mt5 = FakeMT5()
    checker = MT5ConnectivityChecker(mt5_module=fake_mt5)

    result = checker.check(expected_login="123456", symbol="XAUUSD")

    assert result.ok is True
    assert result.terminal_detected is True
    assert result.session_valid is True
    assert result.account_access_valid is True
    assert result.symbol_available is True
    assert result.account_login == 123456
    assert result.symbol == "XAUUSD"
    assert fake_mt5.shutdown_called is True


def test_mt5_connectivity_detects_terminal_initialization_failure():
    fake_mt5 = FakeMT5(initialize_result=False)
    checker = MT5ConnectivityChecker(mt5_module=fake_mt5)

    result = checker.check(expected_login="123456", symbol="XAUUSD")

    assert result.ok is False
    assert result.terminal_detected is False
    assert "initialization failed" in result.error


def test_mt5_connectivity_detects_missing_session():
    fake_mt5 = FakeMT5(account_info=None)
    fake_mt5._account_info = None
    checker = MT5ConnectivityChecker(mt5_module=fake_mt5)

    result = checker.check(expected_login="123456", symbol="XAUUSD")

    assert result.ok is False
    assert result.terminal_detected is True
    assert result.session_valid is False
    assert result.account_access_valid is False
    assert "session is unavailable" in result.error


def test_mt5_connectivity_detects_login_mismatch():
    fake_mt5 = FakeMT5(account_info=SimpleNamespace(login=999999))
    checker = MT5ConnectivityChecker(mt5_module=fake_mt5)

    result = checker.check(expected_login="123456", symbol="XAUUSD")

    assert result.ok is False
    assert result.session_valid is True
    assert result.account_access_valid is False
    assert "login mismatch" in result.error


def test_mt5_connectivity_detects_missing_symbol():
    fake_mt5 = FakeMT5(symbol_info=None)
    fake_mt5._symbol_info = None
    checker = MT5ConnectivityChecker(mt5_module=fake_mt5)

    result = checker.check(expected_login="123456", symbol="XAUUSD")

    assert result.ok is False
    assert result.account_access_valid is True
    assert result.symbol_available is False
    assert result.error == "MT5 symbol is unavailable: XAUUSD"


def test_mt5_connectivity_selects_hidden_symbol():
    fake_mt5 = FakeMT5(symbol_info=SimpleNamespace(visible=False))
    checker = MT5ConnectivityChecker(mt5_module=fake_mt5)

    result = checker.check(expected_login="123456", symbol="XAUUSD")

    assert result.ok is True
    assert fake_mt5.symbol_selected == ("XAUUSD", True)


def test_runtime_connectivity_uses_runtime_account_symbol():
    fake_mt5 = FakeMT5()
    checker = MT5ConnectivityChecker(mt5_module=fake_mt5)
    runtime = {
        "account": {
            "mt5_login": "123456",
            "symbol": "XAUUSD",
        },
        "bot_config": {},
    }

    result = check_runtime_connectivity(runtime, checker)

    assert result.ok is True
    assert fake_mt5.symbol_checked == "XAUUSD"
