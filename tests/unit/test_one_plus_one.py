import pytest


@pytest.mark.asyncio
async def test_one_plus_one() -> None:
    """Test that 1 + 1 equals 2."""
    assert 1 + 1 == 2
