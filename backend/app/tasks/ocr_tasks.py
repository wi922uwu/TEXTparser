"""
OCR processing tasks.
"""
import logging
from pathlib import Path
from typing import List
import fitz  # PyMuPDF
from PIL import Image

from app.tasks.celery_app import celery_app
from app.core.ocr_engine import OCREngine
from app.core.preprocessor import preprocess_for_ocr
from app.exporters.txt_exporter import TXTExporter
from app.exporters.docx_exporter import DOCXExporter
from app.exporters.xlsx_exporter import XLSXExporter
from app.exporters.csv_exporter import CSVExporter
from app.storage.file_manager import FileManager
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize components
ocr_engine = OCREngine()
file_manager = FileManager()

EXPORTERS = {
    "txt": TXTExporter(),
    "docx": DOCXExporter(),
    "xlsx": XLSXExporter(),
    "csv": CSVExporter()
}


@celery_app.task(bind=True)
def process_document(self, file_id: str, export_formats: List[str]):
    """
    Process document with OCR and export to requested formats.

    Args:
        file_id: Uploaded file ID
        export_formats: List of formats to export (txt, docx, xlsx, csv)

    Returns:
        Dictionary with processing results
    """
    try:
        self.update_state(state='PROGRESS', meta={'step': 'loading', 'progress': 10})

        # Get uploaded file
        file_path = file_manager.get_upload_path(file_id)
        if not file_path:
            raise FileNotFoundError(f"File not found: {file_id}")

        logger.info(f"Processing file: {file_id}")

        # Convert PDF to images if needed
        image_paths = []
        if file_path.suffix.lower() == '.pdf':
            self.update_state(state='PROGRESS', meta={'step': 'pdf_conversion', 'progress': 20})
            image_paths = convert_pdf_to_images(file_path)
        else:
            image_paths = [str(file_path)]

        # Preprocess images
        self.update_state(state='PROGRESS', meta={'step': 'preprocessing', 'progress': 30})
        preprocessed_paths = []
        for img_path in image_paths:
            preprocessed = preprocess_for_ocr(img_path)
            preprocessed_paths.append(preprocessed)

        # Run OCR on all pages
        self.update_state(state='PROGRESS', meta={'step': 'ocr_processing', 'progress': 50})
        all_results = []
        for idx, img_path in enumerate(preprocessed_paths):
            progress = 50 + (30 * (idx + 1) / len(preprocessed_paths))
            self.update_state(
                state='PROGRESS',
                meta={'step': f'ocr_page_{idx+1}', 'progress': int(progress)}
            )
            result = ocr_engine.process_document(img_path)
            all_results.append(result)

        # Combine results from all pages
        combined_result = combine_page_results(all_results)

        # Export to requested formats
        self.update_state(state='PROGRESS', meta={'step': 'exporting', 'progress': 85})
        result_paths = {}

        for format in export_formats:
            if format in EXPORTERS:
                output_path = settings.result_dir / file_id / f"result.{format}"
                output_path.parent.mkdir(parents=True, exist_ok=True)

                exporter = EXPORTERS[format]
                exported_path = exporter.export(combined_result, str(output_path))
                result_paths[format] = exported_path

        self.update_state(state='PROGRESS', meta={'step': 'completed', 'progress': 100})

        logger.info(f"Completed processing: {file_id}")

        return {
            'status': 'completed',
            'file_id': file_id,
            'results': result_paths,
            'page_count': len(all_results),
            'has_tables': combined_result.get('has_tables', False)
        }

    except Exception as e:
        logger.error(f"Error processing {file_id}: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


def convert_pdf_to_images(pdf_path: Path) -> List[str]:
    """
    Convert PDF pages to images.

    Args:
        pdf_path: Path to PDF file

    Returns:
        List of image file paths
    """
    image_paths = []
    doc = fitz.open(pdf_path)

    output_dir = pdf_path.parent / "pages"
    output_dir.mkdir(exist_ok=True)

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality

        image_path = output_dir / f"page_{page_num + 1}.png"
        pix.save(str(image_path))
        image_paths.append(str(image_path))

    doc.close()
    logger.info(f"Converted PDF to {len(image_paths)} images")
    return image_paths


def combine_page_results(results: List[dict]) -> dict:
    """
    Combine OCR results from multiple pages.

    Args:
        results: List of page results

    Returns:
        Combined result dictionary
    """
    combined_text = []
    all_tables = []
    has_tables = False

    for page_result in results:
        text_data = page_result.get("text", {})
        full_text = text_data.get("full_text", "")
        if full_text:
            combined_text.append(full_text)

        tables = page_result.get("tables", [])
        if tables:
            all_tables.extend(tables)
            has_tables = True

    return {
        "text": {
            "full_text": "\n\n".join(combined_text),
            "page_count": len(results)
        },
        "tables": all_tables,
        "has_tables": has_tables
    }
