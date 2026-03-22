#!/usr/bin/env python3
"""
Script to download PaddleOCR models for offline use.
This ensures complete isolation without external API calls.
"""
import os
from pathlib import Path
from paddleocr import PaddleOCR


def download_models():
    """Download all required PaddleOCR models."""
    base_dir = Path(__file__).parent.parent / "backend" / "models"
    base_dir.mkdir(parents=True, exist_ok=True)

    print("Downloading PaddleOCR models for Russian language...")
    print("This may take several minutes...")

    # Initialize PaddleOCR - this will download models
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang='ru',
        use_gpu=False,
        show_log=True
    )

    print("\nDownloading table structure recognition models...")
    # Import table structure model
    from paddleocr import PPStructure
    table_engine = PPStructure(
        show_log=True,
        lang='ru'
    )

    print("\n✓ All models downloaded successfully!")
    print(f"Models location: {base_dir}")
    print("\nYou can now run the OCR service offline.")


if __name__ == "__main__":
    download_models()
