from pathlib import Path

import pytest


@pytest.fixture
def fixture_root() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def contract_root() -> Path:
    return Path(__file__).resolve().parents[3] / "contracts"
