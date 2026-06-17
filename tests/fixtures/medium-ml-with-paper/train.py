"""Training loop implementing Algorithm 1 in paper.pdf."""
import torch
from model import SimpleClassifier
from dataset import build_dataloaders


def train_epoch(model: SimpleClassifier, dataloader, optimizer, criterion) -> float:
    """Train for one epoch. Returns average loss."""
    model.train()
    total_loss = 0.0
    for x, y in dataloader:
        optimizer.zero_grad()
        pred = model(x)
        loss = criterion(pred, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(dataloader)


def train(num_epochs: int = 10, lr: float = 1e-3) -> SimpleClassifier:
    """Full training pipeline."""
    model = SimpleClassifier(input_dim=100, hidden_dim=64, num_classes=10)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = torch.nn.CrossEntropyLoss()
    train_loader, _ = build_dataloaders()

    for epoch in range(num_epochs):
        loss = train_epoch(model, train_loader, optimizer, criterion)
        print(f"Epoch {epoch + 1}/{num_epochs}, loss={loss:.4f}")
    return model
