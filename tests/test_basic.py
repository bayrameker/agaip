"""Basic tests to ensure CI/CD pipeline works."""

import pytest
from agaip import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ is not None
    assert isinstance(__version__, str)


def test_import():
    """Test that main package can be imported."""
    import agaip
    assert agaip is not None


def test_basic_functionality():
    """Basic functionality test."""
    assert 1 + 1 == 2


@pytest.mark.asyncio
async def test_async_basic():
    """Test async functionality."""
    async def dummy_async():
        return True
    
    result = await dummy_async()
    assert result is True
