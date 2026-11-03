from pathlib import Path

import pytest

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"


@pytest.fixture
def raw_dir() -> Path:
    """The real raw-data folder; tests that need it are skipped when it is missing."""
    if not RAW.is_dir():
        pytest.skip(f"data mentah tidak ada di {RAW}")
    return RAW
