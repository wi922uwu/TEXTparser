"""
Pytest configuration and fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent.parent.parent / "test_data"


@pytest.fixture
def sample_image_path(test_data_dir):
    """Return path to sample image."""
    # This would be a real test image in production
    return test_data_dir / "samples" / "test.png"


@pytest.fixture
def sample_pdf_path(test_data_dir):
    """Return path to sample PDF."""
    return test_data_dir / "samples" / "test.pdf"
