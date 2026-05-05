from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any


@dataclass
class MT5ConnectivityResult:
    terminal_detected: bool
    session_valid: bool
    account_access_valid: bool
    symbol_available: bool
    ok: bool
    error: str | None = None
    terminal_name: str | None = None
    account_login: int | None = None
    symbol: str | None = None


class MT5ConnectivityChecker:
    """Connectivity checks only. This class must not place or modify orders."""

    def __init__(self, *, terminal_path: str | None = None, mt5_module: Any | None = None):
        self.terminal_path = terminal_path
        self._mt5 = mt5_module

    def check(self, *, expected_login: str, symbol: str) -> MT5ConnectivityResult:
        mt5 = self._load_mt5()
        if mt5 is None:
            return self._failed("MetaTrader5 Python package is not installed")

        initialized = self._initialize(mt5)
        if not initialized:
            return self._failed(f"MT5 terminal initialization failed: {self._last_error(mt5)}")

        try:
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                return self._failed(
                    f"MT5 terminal was not detected: {self._last_error(mt5)}",
                    terminal_detected=False,
                )

            account_info = mt5.account_info()
            if account_info is None:
                return MT5ConnectivityResult(
                    terminal_detected=True,
                    session_valid=False,
                    account_access_valid=False,
                    symbol_available=False,
                    ok=False,
                    error=f"MT5 account session is unavailable: {self._last_error(mt5)}",
                    terminal_name=self._attr(terminal_info, "name"),
                    symbol=symbol,
                )

            account_login = self._attr(account_info, "login")
            if str(account_login) != str(expected_login):
                return MT5ConnectivityResult(
                    terminal_detected=True,
                    session_valid=True,
                    account_access_valid=False,
                    symbol_available=False,
                    ok=False,
                    error=f"MT5 account login mismatch: expected {expected_login}, got {account_login}",
                    terminal_name=self._attr(terminal_info, "name"),
                    account_login=account_login,
                    symbol=symbol,
                )

            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return MT5ConnectivityResult(
                    terminal_detected=True,
                    session_valid=True,
                    account_access_valid=True,
                    symbol_available=False,
                    ok=False,
                    error=f"MT5 symbol is unavailable: {symbol}",
                    terminal_name=self._attr(terminal_info, "name"),
                    account_login=account_login,
                    symbol=symbol,
                )

            symbol_selected = self._attr(symbol_info, "visible")
            if not symbol_selected and not mt5.symbol_select(symbol, True):
                return MT5ConnectivityResult(
                    terminal_detected=True,
                    session_valid=True,
                    account_access_valid=True,
                    symbol_available=False,
                    ok=False,
                    error=f"MT5 symbol could not be selected: {symbol}",
                    terminal_name=self._attr(terminal_info, "name"),
                    account_login=account_login,
                    symbol=symbol,
                )

            return MT5ConnectivityResult(
                terminal_detected=True,
                session_valid=True,
                account_access_valid=True,
                symbol_available=True,
                ok=True,
                terminal_name=self._attr(terminal_info, "name"),
                account_login=account_login,
                symbol=symbol,
            )
        finally:
            shutdown = getattr(mt5, "shutdown", None)
            if shutdown:
                shutdown()

    def _load_mt5(self) -> Any | None:
        if self._mt5 is not None:
            return self._mt5
        try:
            return import_module("MetaTrader5")
        except ImportError:
            return None

    def _initialize(self, mt5: Any) -> bool:
        if self.terminal_path:
            return bool(mt5.initialize(path=self.terminal_path))
        return bool(mt5.initialize())

    @staticmethod
    def _last_error(mt5: Any) -> str:
        last_error = getattr(mt5, "last_error", None)
        if not last_error:
            return "unknown error"
        return str(last_error())

    @staticmethod
    def _attr(value: Any, name: str) -> Any:
        if isinstance(value, dict):
            return value.get(name)
        return getattr(value, name, None)

    @staticmethod
    def _failed(
        error: str,
        *,
        terminal_detected: bool = False,
    ) -> MT5ConnectivityResult:
        return MT5ConnectivityResult(
            terminal_detected=terminal_detected,
            session_valid=False,
            account_access_valid=False,
            symbol_available=False,
            ok=False,
            error=error,
        )
