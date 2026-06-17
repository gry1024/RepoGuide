"""Entry point. Runs training then evaluation."""
from model import SimpleClassifier
from train import train
from evaluate import evaluate


def cli_main() -> None:
    """CLI entry point: train then evaluate."""
    model = train(num_epochs=2, lr=1e-3)
    metrics = evaluate(model)
    print(f"Final accuracy: {metrics['accuracy']:.4f}")


if __name__ == "__main__":
    cli_main()
