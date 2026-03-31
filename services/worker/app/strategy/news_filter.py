def high_impact_news_blocked(minutes_to_event: int | None) -> bool:
    if minutes_to_event is None:
        return False
    return abs(minutes_to_event) <= 30
