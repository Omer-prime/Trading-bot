from datetime import datetime

from app.strategy.trend import detect_trend
from app.strategy.liquidity import liquidity_sweep_detected
from app.strategy.bos import bos_confirmed
from app.strategy.zones import valid_retrace_to_ob_or_fvg
from app.strategy.session_filter import trading_session_allowed
from app.strategy.news_filter import high_impact_news_blocked


def evaluate_setup() -> dict:
    # Placeholder values until real market parsers are implemented.
    trend = detect_trend(higher_highs=2, higher_lows=2, lower_highs=0, lower_lows=0)
    session_ok = trading_session_allowed(datetime.now())
    news_block = high_impact_news_blocked(minutes_to_event=None)
    sweep = liquidity_sweep_detected(swept_equal_levels=True, fake_breakout=True)
    bos = bos_confirmed(direction="buy", strong_close=True)
    retrace = valid_retrace_to_ob_or_fvg(touched_zone=True)

    should_buy = trend == "up" and session_ok and not news_block and sweep and bos and retrace
    should_sell = trend == "down" and session_ok and not news_block and sweep and bos and retrace

    return {
        "trend": trend,
        "session_ok": session_ok,
        "news_block": news_block,
        "sweep": sweep,
        "bos": bos,
        "retrace": retrace,
        "action": "buy" if should_buy else "sell" if should_sell else "hold",
    }
