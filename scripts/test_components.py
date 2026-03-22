#!/usr/bin/env python3
"""
Simple test script to verify OCR functionality.
Run this after installing dependencies to test the OCR engine.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.ocr_engine import OCREngine
from app.core.preprocessor import preprocess_for_ocr
from app.exporters.txt_exporter import TXTExporter
from app.exporters.docx_exporter import DOCXExporter
from app.exporters.xlsx_exporter import XLSXExporter
from app.exporters.csv_exporter import CSVExporter


def test_ocr_engine():
    """Test OCR engine initialization."""
    print("Testing OCR engine initialization...")
    try:
        engine = OCREngine()
        print("✓ OCR engine initialized successfully")
        return True
    except Exception as e:
        print(f"✗ OCR engine initialization failed: {e}")
        return False


def test_exporters():
    """Test all exporters."""
    print("\nTesting exporters...")

    test_data = {
        "text": {
            "full_text": "Тестовый текст для проверки экспорта.\nВторая строка текста.",
            "page_count": 1
        },
        "tables": [
            {
                "cells": [
                    ["Заголовок 1", "Заголовок 2"],
                    ["Значение 1", "Значение 2"]
                ]
            }
        ],
        "has_tables": True
    }

    exporters = {
        "TXT": TXTExporter(),
        "DOCX": DOCXExporter(),
        "XLSX": XLSXExporter(),
        "CSV": CSVExporter()
    }

    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    all_passed = True
    for name, exporter in exporters.items():
        try:
            output_path = output_dir / f"test.{name.lower()}"
            exporter.export(test_data, str(output_path))

            if output_path.exists():
                print(f"✓ {name} exporter works")
            else:
                print(f"✗ {name} exporter failed - file not created")
                all_passed = False
        except Exception as e:
            print(f"✗ {name} exporter failed: {e}")
            all_passed = False

    return all_passed


def main():
    """Run all tests."""
    print("=" * 50)
    print("OCR Web Service - Component Tests")
    print("=" * 50)

    results = []

    # Test OCR engine
    results.append(("OCR Engine", test_ocr_engine()))

    # Test exporters
    results.append(("Exporters", test_exporters()))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
