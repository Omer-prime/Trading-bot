from __future__ import annotations

import platform

from app.adapters.mt5_connectivity import MT5ConnectivityChecker, MT5ConnectivityResult
from app.api_client import WorkerApiClient
from app.core.config import settings
from app.runtime import check_runtime_connectivity


def resolve_machine_name() -> str:
    return settings.worker_machine_name or platform.node() or "unknown-worker"


def run_connectivity_cycle() -> MT5ConnectivityResult:
    api_client = WorkerApiClient(
        base_url=settings.api_base_url.rstrip("/"),
        worker_secret=settings.worker_shared_secret,
        timeout_seconds=settings.api_timeout_seconds,
    )
    registered_worker = api_client.register_worker(
        account_id=settings.account_id,
        machine_name=resolve_machine_name(),
        version=settings.worker_version,
    )
    worker_id = registered_worker["id"]

    runtime = api_client.fetch_runtime(worker_id=worker_id)
    checker = MT5ConnectivityChecker(terminal_path=settings.mt5_terminal_path)
    result = check_runtime_connectivity(runtime, checker)

    api_client.heartbeat(
        worker_id=worker_id,
        status="online" if result.ok else "error",
        last_error=None if result.ok else result.error,
    )
    return result


def main() -> None:
    result = run_connectivity_cycle()
    print("MT5 connectivity status:", result)


if __name__ == "__main__":
    main()
