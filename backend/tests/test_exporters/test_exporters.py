"""
Tests for exporters.
"""
import pytest
from pathlib import Path
from app.exporters.txt_exporter import TXTExporter
from app.exporters.docx_exporter import DOCXExporter
from app.exporters.xlsx_exporter import XLSXExporter
from app.exporters.csv_exporter import CSVExporter


@pytest.fixture
def sample_data():
    """Sample OCR data for testing."""
    return {
        "text": {
            "full_text": "Test text\nSecond line",
            "page_count": 1
        },
        "tables": [
            {
                "cells": [
                    ["Header 1", "Header 2"],
                    ["Value 1", "Value 2"]
                ]
            }
        ],
        "has_tables": True
    }


def test_txt_exporter(sample_data, tmp_path):
    """Test TXT exporter."""
    exporter = TXTExporter()
    output_path = tmp_path / "test.txt"

    result = exporter.export(sample_data, str(output_path))

    assert Path(result).exists()
    assert Path(result).suffix == ".txt"


def test_docx_exporter(sample_data, tmp_path):
    """Test DOCX exporter."""
    exporter = DOCXExporter()
    output_path = tmp_path / "test.docx"

    result = exporter.export(sample_data, str(output_path))

    assert Path(result).exists()
    assert Path(result).suffix == ".docx"


def test_xlsx_exporter(sample_data, tmp_path):
    """Test XLSX exporter."""
    exporter = XLSXExporter()
    output_path = tmp_path / "test.xlsx"

    result = exporter.export(sample_data, str(output_path))

    assert Path(result).exists()
    assert Path(result).suffix == ".xlsx"


def test_csv_exporter(sample_data, tmp_path):
    """Test CSV exporter."""
    exporter = CSVExporter()
    output_path = tmp_path / "test.csv"

    result = exporter.export(sample_data, str(output_path))

    assert Path(result).exists()
    assert Path(result).suffix == ".csv"
