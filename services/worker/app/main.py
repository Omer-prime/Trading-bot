from app.services.runtime_loop import build_runtime_loop


def main() -> None:
    result = build_runtime_loop().run_once()
    print("Dry-run strategy status:", result.heartbeat_summary)


if __name__ == "__main__":
    main()
