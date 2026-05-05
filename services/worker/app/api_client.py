from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class WorkerApiClient:
    base_url: str
    worker_secret: str
    timeout_seconds: int = 10

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-Worker-Secret": self.worker_secret}

    def register_worker(
        self,
        *,
        account_id: int,
        machine_name: str | None,
        version: str | None,
    ) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/v1/workers/register",
            headers=self._headers,
            json={
                "account_id": account_id,
                "machine_name": machine_name,
                "version": version,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def fetch_runtime(self, *, worker_id: int) -> dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/api/v1/workers/{worker_id}/runtime",
            headers=self._headers,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def heartbeat(
        self,
        *,
        worker_id: int,
        status: str,
        last_error: str | None = None,
    ) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/v1/workers/heartbeat",
            headers=self._headers,
            json={
                "worker_id": worker_id,
                "status": status,
                "last_error": last_error,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
