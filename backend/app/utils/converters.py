"""
Format conversion utilities.
"""
from pathlib import Path
from typing import List
import fitz  # PyMuPDF
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def pdf_to_images(pdf_path: str, output_dir: str = None, dpi: int = 300) -> List[str]:
    """
    Convert PDF pages to images.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for images
        dpi: Resolution for conversion

    Returns:
        List of image file paths
    """
    pdf_path = Path(pdf_path)

    if output_dir is None:
        output_dir = pdf_path.parent / "pages"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths = []
    doc = fitz.open(pdf_path)

    try:
        for page_num in range(len(doc)):
            page = doc[page_num]

            # Calculate zoom for desired DPI
            zoom = dpi / 72  # 72 is default DPI
            mat = fitz.Matrix(zoom, zoom)

            pix = page.get_pixmap(matrix=mat)

            image_path = output_dir / f"page_{page_num + 1}.png"
            pix.save(str(image_path))
            image_paths.append(str(image_path))

        logger.info(f"Converted PDF to {len(image_paths)} images")
        return image_paths

    finally:
        doc.close()


def image_to_pdf(image_paths: List[str], output_path: str) -> str:
    """
    Convert images to PDF.

    Args:
        image_paths: List of image file paths
        output_path: Output PDF path

    Returns:
        Path to created PDF
    """
    images = []

    for img_path in image_paths:
        img = Image.open(img_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        images.append(img)

    if images:
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:] if len(images) > 1 else []
        )

    logger.info(f"Created PDF with {len(images)} pages")
    return output_path
