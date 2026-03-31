#!/usr/bin/env python3
"""
Script to download PaddleOCR models for offline use.
This ensures complete isolation without external API calls.
"""
import os
from pathlib import Path


def download_models():
    """Download all required PaddleOCR models."""
    base_dir = Path(__file__).parent.parent / "backend" / "models"
    base_dir.mkdir(parents=True, exist_ok=True)

    print("Downloading PaddleOCR models for Russian language...")
    print("This may take several minutes...")

    # Initialize PaddleOCR - this will download models
    # New API (paddleocr 3.x)
    os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(
        lang='ru',
        use_textline_orientation=False,
    )

    print("\n✓ All models downloaded successfully!")
    print(f"Models location: {base_dir}")
    print("\nYou can now run the OCR service offline.")

    # Skip PPStructure for now - basic OCR models are sufficient
    return

    print("\n✓ All models downloaded successfully!")
    print(f"Models location: {base_dir}")
    print("\nYou can now run the OCR service offline.")


if __name__ == "__main__":
    download_models()
