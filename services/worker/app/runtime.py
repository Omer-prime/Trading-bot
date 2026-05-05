from __future__ import annotations

from app.adapters.mt5_connectivity import MT5ConnectivityChecker, MT5ConnectivityResult
from app.core.config import settings


def check_runtime_connectivity(runtime: dict, checker: MT5ConnectivityChecker) -> MT5ConnectivityResult:
    account = runtime["account"]
    symbol = account.get("symbol") or settings.symbol

    return checker.check(
        expected_login=account["mt5_login"],
        symbol=symbol,
    )
