from datetime import datetime


def trading_session_allowed(now: datetime) -> bool:
    # PKT rough initial rule: 12 PM to 9 PM
    return 12 <= now.hour < 21
