"""Dataset loading and preprocessing."""
from torch.utils.data import Dataset, DataLoader


class SyntheticDataset(Dataset):
    """A synthetic dataset for testing."""

    def __init__(self, num_samples: int = 1000, input_dim: int = 100) -> None:
        self.num_samples = num_samples
        self.input_dim = input_dim

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> tuple:
        import torch
        x = torch.randn(self.input_dim)
        y = torch.randint(0, 10, (1,)).item()
        return x, y


def build_dataloaders(batch_size: int = 32) -> tuple[DataLoader, DataLoader]:
    """Build train and validation dataloaders."""
    train_ds = SyntheticDataset()
    val_ds = SyntheticDataset(num_samples=200)
    return (
        DataLoader(train_ds, batch_size=batch_size),
        DataLoader(val_ds, batch_size=batch_size),
    )
