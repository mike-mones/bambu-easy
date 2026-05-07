from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def squish_3mf() -> Path:
    p = FIXTURES / "squish_test.3mf"
    assert p.exists(), f"missing fixture: {p}"
    return p
