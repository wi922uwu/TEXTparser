"""
OCR Engine wrapper for PaddleOCR.
Handles text and table recognition from images.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional
from paddleocr import PaddleOCR, PPStructure
import cv2
import numpy as np
from bs4 import BeautifulSoup

from app.config import settings

logger = logging.getLogger(__name__)


class OCREngine:
    """Wrapper for PaddleOCR with Russian language support."""

    def __init__(self):
        """Initialize OCR engines."""
        logger.info("Initializing OCR engine...")

        # Text OCR engine with Russian language support
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=settings.ocr_language,
            use_gpu=settings.use_gpu,
            show_log=False
        )

        # Table structure recognition engine
        # Note: PPStructure only supports 'en' and 'ch' for layout models
        # Use 'en' for table structure, but text within tables will use Russian OCR
        self.table_engine = PPStructure(
            lang='en',  # Use English for layout detection
            show_log=False,
            use_gpu=settings.use_gpu
        )

        logger.info("OCR engine initialized successfully")

    def process_image(self, image_path: str) -> Dict:
        """
        Process image and extract text.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with OCR results
        """
        try:
            result = self.ocr.ocr(image_path, cls=True)

            if not result or not result[0]:
                return {"text_blocks": [], "full_text": ""}

            text_blocks = []
            for line in result[0]:
                box = line[0]  # Bounding box coordinates
                text_info = line[1]  # (text, confidence)
                text = text_info[0]
                confidence = text_info[1]

                text_blocks.append({
                    "text": text,
                    "confidence": confidence,
                    "box": box
                })

            # Sort by vertical position (top to bottom)
            text_blocks.sort(key=lambda x: x["box"][0][1])

            full_text = "\n".join([block["text"] for block in text_blocks])

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

                    col_idx += 1

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

    def process_document(self, image_path: str) -> Dict:
        """
        Process document with both text and table detection.

        Args:
            image_path: Path to image file

        Returns:
            Combined results with text and tables
        """
        text_result = self.process_image(image_path)
        tables = self.detect_tables(image_path)

        return {
            "text": text_result,
            "tables": tables,
            "has_tables": len(tables) > 0
        }
