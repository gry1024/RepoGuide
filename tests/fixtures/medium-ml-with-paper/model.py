"""Neural network model definition."""
import torch
import torch.nn as nn


class SimpleClassifier(nn.Module):
    """A simple 2-layer classifier corresponding to Eq.(3) in paper.pdf."""

    def __init__(self, input_dim: int, hidden_dim: int, num_classes: int) -> None:
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass: h = ReLU(W1*x + b1); y = W2*h + b2"""
        h = self.relu(self.fc1(x))
        return self.fc2(h)
