def calculate_lot_size(balance: float, risk_pct: float, stop_distance_points: float, point_value: float) -> float:
    if stop_distance_points <= 0 or point_value <= 0:
        return 0.0
    risk_amount = balance * (risk_pct / 100.0)
    lots = risk_amount / (stop_distance_points * point_value)
    return round(max(lots, 0.0), 2)


def risk_reward_ok(stop_distance: float, target_distance: float, minimum_rr: float = 2.0) -> bool:
    if stop_distance <= 0:
        return False
    rr = target_distance / stop_distance
    return rr >= minimum_rr
