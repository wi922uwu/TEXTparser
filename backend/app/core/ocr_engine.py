"""
OCR Engine wrapper for PaddleOCR.
Handles text and table recognition from images.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Import PaddleOCR components
# PPStructure is available directly from paddleocr in version 2.8.x
from paddleocr import PaddleOCR, PPStructure

import cv2
import numpy as np
from bs4 import BeautifulSoup

from app.config import settings
from app.constants import (
    OCR_DET_LIMIT_SIDE_LEN,
    OCR_DET_LIMIT_SIDE_LEN_FAST,
    OCR_DET_LIMIT_SIDE_LEN_HQ,
    OCR_DET_DB_THRESH,
    OCR_DET_DB_THRESH_FAST,
    OCR_DET_DB_THRESH_HQ,
    OCR_DET_DB_BOX_THRESH,
    OCR_DET_DB_BOX_THRESH_FAST,
    OCR_DET_DB_BOX_THRESH_HQ,
    OCR_DET_DB_UNCLIP_RATIO,
    OCR_DET_DB_UNCLIP_RATIO_FAST,
    OCR_DET_DB_UNCLIP_RATIO_HQ,
    OCR_REC_BATCH_NUM,
    OCR_REC_BATCH_NUM_FAST,
    OCR_REC_BATCH_NUM_HQ,
    OCR_MAX_TEXT_LENGTH,
    OCR_MAX_TEXT_LENGTH_FAST,
    OCR_MAX_TEXT_LENGTH_HQ,
    OCR_TOTAL_PROCESS_NUM,
    OCR_USE_MP,
    CONFIDENCE_LOW_THRESHOLD,
)
from app.core.text_extractor import sort_reading_order, group_into_paragraphs

logger = logging.getLogger(__name__)


class OCREngine:
    """Wrapper for PaddleOCR with Russian language support."""

    def __init__(self):
        """Initialize OCR engines lazily (on first use)."""
        logger.info("OCR engine created (lazy initialization)")
        self._ocr = None
        self._ocr_fast = None
        self._ocr_hq = None
        self._table_engine = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of OCR engines on first use."""
        if self._initialized:
            return

        logger.info("Initializing OCR engine (first use)...")

        # Text OCR engine with Russian language support
        # Optimized for BALANCED speed and quality (target: <60 sec for 5MB file)
        self._ocr = PaddleOCR(
            use_angle_cls=True,
            lang=settings.ocr_language,
            use_gpu=settings.use_gpu,
            show_log=False,
            # Balanced settings for speed + quality:
            det_limit_side_len=OCR_DET_LIMIT_SIDE_LEN,
            det_db_thresh=OCR_DET_DB_THRESH,
            det_db_box_thresh=OCR_DET_DB_BOX_THRESH,
            det_db_unclip_ratio=OCR_DET_DB_UNCLIP_RATIO,
            rec_batch_num=OCR_REC_BATCH_NUM,
            max_text_length=OCR_MAX_TEXT_LENGTH,
            use_mp=OCR_USE_MP,
            total_process_num=OCR_TOTAL_PROCESS_NUM,
        )

        # Fast OCR mode for simple documents (maximum speed)
        self._ocr_fast = PaddleOCR(
            use_angle_cls=True,
            lang=settings.ocr_language,
            use_gpu=settings.use_gpu,
            show_log=False,
            # Maximum speed settings:
            det_limit_side_len=OCR_DET_LIMIT_SIDE_LEN_FAST,
            det_db_thresh=OCR_DET_DB_THRESH_FAST,
            det_db_box_thresh=OCR_DET_DB_BOX_THRESH_FAST,
            det_db_unclip_ratio=OCR_DET_DB_UNCLIP_RATIO_FAST,
            rec_batch_num=OCR_REC_BATCH_NUM_FAST,
            max_text_length=OCR_MAX_TEXT_LENGTH_FAST,
            use_mp=OCR_USE_MP,
            total_process_num=OCR_TOTAL_PROCESS_NUM,
        )


        # High Quality OCR mode for difficult documents (maximum accuracy)
        self._ocr_hq = PaddleOCR(
            use_angle_cls=True,
            lang=settings.ocr_language,
            use_gpu=settings.use_gpu,
            show_log=False,
            det_limit_side_len=OCR_DET_LIMIT_SIDE_LEN_HQ,
            det_db_thresh=OCR_DET_DB_THRESH_HQ,
            det_db_box_thresh=OCR_DET_DB_BOX_THRESH_HQ,
            det_db_unclip_ratio=OCR_DET_DB_UNCLIP_RATIO_HQ,
            rec_batch_num=OCR_REC_BATCH_NUM_HQ,
            max_text_length=OCR_MAX_TEXT_LENGTH_HQ,
            use_mp=OCR_USE_MP,
            total_process_num=OCR_TOTAL_PROCESS_NUM,
        )

        # Table structure recognition engine
        # Note: PPStructure only supports 'en' and 'ch' for layout models
        # Use 'en' for table structure, but text within tables will use Russian OCR
        self._table_engine = PPStructure(
            lang='en',  # Use English for layout detection
            show_log=False,
            use_gpu=settings.use_gpu
        )

        self._initialized = True
        logger.info("OCR engine initialized successfully")

    @property
    def ocr(self):
        """Lazy access to OCR engine."""
        self._ensure_initialized()
        return self._ocr

    @property
    def ocr_fast(self):
        """Lazy access to fast OCR engine."""
        self._ensure_initialized()
        return self._ocr_fast


    @property
    def ocr_hq(self):
        """Lazy access to high quality OCR engine."""
        self._ensure_initialized()
        return self._ocr_hq


    @property
    def table_engine(self):
        """Lazy access to table engine."""
        self._ensure_initialized()
        return self._table_engine

    def process_image(self, image_path: str, quality_preset: str = "balanced") -> Dict:
        """
        Process image and extract text.

        Args:
            image_path: Path to image file
            quality_preset: Quality preset - "fast", "balanced", or "high_quality"

        Returns:
            Dictionary with OCR results

        Raises:
            FileNotFoundError: If image file does not exist
            ValueError: If file format is not supported
        """
        try:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")

            supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
            if path.suffix.lower() not in supported_extensions:
                raise ValueError(f"Unsupported image format: {path.suffix}")

            # Select OCR engine based on quality preset
            if quality_preset == "fast":
                ocr_engine = self.ocr_fast
                mode_name = "fast"
            elif quality_preset == "high_quality":
                ocr_engine = self.ocr_hq
                mode_name = "high_quality"
            else:
                ocr_engine = self.ocr
                mode_name = "balanced"

            result = ocr_engine.ocr(image_path, cls=True)

            logger.info(f"OCR completed in {mode_name} mode")

            if not result or not result[0]:
                return {"text_blocks": [], "full_text": ""}

            text_blocks = []
            for line in result[0]:
                box = line[0]  # Bounding box coordinates
                text_info = line[1]  # (text, confidence)
                text = text_info[0]
                confidence = text_info[1] if text_info[1] is not None else 0.0

                text_blocks.append({
                    "text": text,
                    "confidence": confidence,
                    "box": box
                })

            # Sort in reading order (top-to-bottom, left-to-right)
            text_blocks = sort_reading_order(text_blocks)

            full_text = "\n".join([block["text"] for block in text_blocks])

            # Log average confidence for quality monitoring
            if text_blocks:
                avg_confidence = sum(block["confidence"] for block in text_blocks) / len(text_blocks)
                logger.info(f"OCR completed. Average confidence: {avg_confidence:.2f}")
                if avg_confidence < CONFIDENCE_LOW_THRESHOLD:
                    logger.warning(f"Low OCR confidence ({avg_confidence:.2f}). Consider improving image quality.")

            return {
                "text_blocks": text_blocks,
                "full_text": full_text
            }

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            raise

    def detect_tables(self, image_path: str) -> List[Dict]:
        """
        Detect and extract tables from image.

        Args:
            image_path: Path to image file

        Returns:
            List of detected tables with structure and merged cell information
        """
        try:
            result = self.table_engine(image_path)

            tables = []
            for item in result:
                if item['type'] == 'table':
                    parsed = self._parse_table_cells(item)
                    tables.append({
                        "bbox": item.get('bbox', []),
                        "html": item.get('res', {}).get('html', ''),
                        "cells": parsed.get('cells', []),
                        "merged_regions": parsed.get('merged_regions', [])
                    })

            return tables

        except Exception as e:
            logger.error(f"Error detecting tables in {image_path}: {e}")
            return []

    def _parse_table_cells(self, table_item: Dict) -> Dict:
        """
        Parse table structure into 2D array of cells with merged cell information.

        Args:
            table_item: Table data from PPStructure

        Returns:
            Dictionary with cells and merged_regions
        """
        try:
            html = table_item.get('res', {}).get('html', '')
            if not html:
                return {'cells': [], 'merged_regions': []}

            soup = BeautifulSoup(html, 'html.parser')

            cells = []
            merged_regions = []

            for row_idx, tr in enumerate(soup.find_all('tr')):
                row_cells = []
                col_idx = 0

                for td in tr.find_all(['td', 'th']):
                    # Get colspan and rowspan attributes
                    colspan = int(td.get('colspan', 1))
                    rowspan = int(td.get('rowspan', 1))

                    # Extract text content
                    cell_text = td.get_text(strip=True)
                    row_cells.append(cell_text)

                    # Record merged cell information
                    if colspan > 1 or rowspan > 1:
                        merged_regions.append({
                            'row': row_idx,
                            'col': col_idx,
                            'rowspan': rowspan,
                            'colspan': colspan,
                            'text': cell_text
                        })

                    col_idx += colspan

                if row_cells:
                    cells.append(row_cells)

            return {
                'cells': cells,
                'merged_regions': merged_regions
            }

        except Exception as e:
            logger.error(f"Error parsing table cells: {e}")
            # Fallback to simple parsing
            return self._parse_table_cells_simple(table_item)

    def _parse_table_cells_simple(self, table_item: Dict) -> Dict:
        """Fallback simple HTML parsing for table cells."""
        try:
            html = table_item.get('res', {}).get('html', '')
            if not html:
                return {'cells': [], 'merged_regions': []}

            # Simple HTML parsing for table cells
            cells = []
            rows = html.split('<tr>')

            for row in rows[1:]:  # Skip first empty split
                if '</tr>' not in row:
                    continue

                row_cells = []
                cell_tags = row.split('<td>')

                for cell in cell_tags[1:]:  # Skip first empty split
                    if '</td>' in cell:
                        cell_text = cell.split('</td>')[0]
                        # Remove HTML tags
                        cell_text = cell_text.replace('<b>', '').replace('</b>', '')
                        row_cells.append(cell_text.strip())

                if row_cells:
                    cells.append(row_cells)

            return {'cells': cells, 'merged_regions': []}

        except Exception as e:
            logger.error(f"Error in simple parsing: {e}")
            return {'cells': [], 'merged_regions': []}

    def process_document(self, image_path: str, enable_tables: bool = True, quality_preset: str = "balanced") -> Dict:
        """
        Process document with both text and table detection.

        Args:
            image_path: Path to image file
            enable_tables: Whether to detect tables (disable for faster processing)
            quality_preset: Quality preset - "fast", "balanced", or "high_quality"

        Returns:
            Combined results with text and tables
        """
        # Use fast OCR mode if requested
        text_result = self.process_image(image_path, quality_preset=quality_preset)

        # Only detect tables if enabled (skip in fast mode for speed)
        tables = []
        if enable_tables and quality_preset != "fast":
            tables = self.detect_tables(image_path)

        return {
            "text": text_result,
            "tables": tables,
            "has_tables": len(tables) > 0
        }
