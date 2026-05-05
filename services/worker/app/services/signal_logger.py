from __future__ import annotations

from app.api_client import WorkerApiClient
from app.services.strategy import StrategyDecision


class SignalLogger:
    def __init__(self, api_client: WorkerApiClient):
        self.api_client = api_client

    def log_decision(self, *, account_id: int, decision: StrategyDecision) -> dict:
        return self.api_client.log_dry_run_signal(decision.as_signal_payload(account_id=account_id))
