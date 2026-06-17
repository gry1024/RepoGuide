"""Evaluation script. Reproduces Table 2 in paper.pdf."""
import torch
from model import SimpleClassifier
from dataset import build_dataloaders


def evaluate(model: SimpleClassifier) -> dict:
    """Evaluate model on validation set. Returns accuracy and loss."""
    model.eval()
    _, val_loader = build_dataloaders()
    correct = 0
    total = 0
    with torch.no_grad():
        for x, y in val_loader:
            pred = model(x).argmax(dim=1)
            correct += (pred == y).sum().item()
            total += y.size(0)
    return {"accuracy": correct / total, "num_samples": total}
