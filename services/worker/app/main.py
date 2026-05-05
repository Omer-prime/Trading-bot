from app.services.runtime_loop import build_runtime_loop


def main() -> None:
    build_runtime_loop().run_forever()


if __name__ == "__main__":
    main()
