"""Utility functions for small-python fixture."""
import argparse


def greet(name: str) -> str:
    """Return a greeting message for the given name."""
    return f"Hello, {name}!"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Small Python CLI")
    parser.add_argument("name", nargs="?", default="World", help="Name to greet")
    return parser.parse_args()
