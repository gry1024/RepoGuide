"""Python main that calls into Rust extension via PyO3."""
# Note: actual PyO3 binding is mocked for testing
def process_data(data):
    """Process data via Rust FFI (mocked)."""
    # Real implementation would: from _native import process
    return [x * 2.0 for x in data]


def main():
    """CLI entry."""
    result = process_data([1.0, 2.0, 3.0])
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
