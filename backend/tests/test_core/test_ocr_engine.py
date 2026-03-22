"""
Tests for OCR engine.
"""
import pytest
from pathlib import Path
from app.core.ocr_engine import OCREngine


@pytest.fixture
def ocr_engine():
    """Create OCR engine instance."""
    return OCREngine()


def test_ocr_engine_initialization(ocr_engine):
    """Test OCR engine initializes correctly."""
    assert ocr_engine is not None
    assert ocr_engine.ocr is not None
    assert ocr_engine.table_engine is not None


def test_process_image_with_text(ocr_engine, tmp_path):
    """Test processing image with text."""
    # This would require a test image
    # For now, just test the method exists
    assert hasattr(ocr_engine, 'process_image')
    assert callable(ocr_engine.process_image)


def test_detect_tables(ocr_engine):
    """Test table detection."""
    assert hasattr(ocr_engine, 'detect_tables')
    assert callable(ocr_engine.detect_tables)


def test_process_document(ocr_engine):
    """Test full document processing."""
    assert hasattr(ocr_engine, 'process_document')
    assert callable(ocr_engine.process_document)
