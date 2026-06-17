"""Entry point for small-python fixture."""
from utils import greet, parse_args


def cli_main() -> None:
    """CLI entry point registered in pyproject.toml."""
    args = parse_args()
    print(greet(args.name))


class Application:
    """Main application orchestrator."""

    def __init__(self, name: str) -> None:
        self.name = name

    def run(self) -> str:
        """Execute the main workflow."""
        return greet(self.name)


if __name__ == "__main__":
    cli_main()
