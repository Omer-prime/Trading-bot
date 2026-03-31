from app.adapters.mt5_stub import MT5StubAdapter
from app.strategy.orchestrator import evaluate_setup
from app.strategy.risk import calculate_lot_size


def main():
    adapter = MT5StubAdapter()
    if not adapter.connect():
        raise RuntimeError("Could not connect to MT5 adapter")

    result = evaluate_setup()
    print("Strategy evaluation:", result)

    if result["action"] == "buy":
        lots = calculate_lot_size(balance=10000, risk_pct=1.0, stop_distance_points=150, point_value=1.0)
        order = adapter.place_order(side="buy", lot_size=lots, stop_loss=2448.0, take_profit=2456.0)
        print("Order result:", order)
    else:
        print("No trade opened.")


if __name__ == "__main__":
    main()
