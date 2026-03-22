"""
Table detection and structure extraction.
"""
from typing import List, Dict, Tuple
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class TableDetector:
    """Handles table detection and structure extraction."""

    def detect_table_structure(self, table_data: Dict) -> Dict:
        """
        Analyze table structure from OCR result.

        Args:
            table_data: Table data from OCR engine

        Returns:
            Structured table information
        """
        cells = table_data.get("cells", [])

        if not cells:
            return {
                "rows": 0,
                "cols": 0,
                "cells": [],
                "has_header": False
            }

        rows = len(cells)
        cols = max(len(row) for row in cells) if cells else 0

        # Detect if first row is header (simple heuristic)
        has_header = self._detect_header(cells)

        return {
            "rows": rows,
            "cols": cols,
            "cells": cells,
            "has_header": has_header
        }

    def _detect_header(self, cells: List[List[str]]) -> bool:
        """
        Simple heuristic to detect if first row is a header.

        Args:
            cells: 2D array of cell values

        Returns:
            True if first row appears to be a header
        """
        if not cells or len(cells) < 2:
            return False

        first_row = cells[0]

        # Check if first row has different characteristics
        # (e.g., shorter text, no numbers)
        first_row_has_numbers = any(
            any(char.isdigit() for char in cell)
            for cell in first_row
        )

        second_row_has_numbers = any(
            any(char.isdigit() for char in cell)
            for cell in cells[1]
        )

        # If second row has numbers but first doesn't, likely a header
        return second_row_has_numbers and not first_row_has_numbers

    def extract_table_data(self, table_data: Dict) -> pd.DataFrame:
        """
        Extract table data as pandas DataFrame.

        Args:
            table_data: Table data from OCR

        Returns:
            DataFrame with table data
        """
        structure = self.detect_table_structure(table_data)
        cells = structure["cells"]

        if not cells:
            return pd.DataFrame()

        # Create DataFrame
        if structure["has_header"]:
            df = pd.DataFrame(cells[1:], columns=cells[0])
        else:
            df = pd.DataFrame(cells)

        return df

    def reconstruct_table(self, cells: List[List[str]]) -> Dict:
        """
        Reconstruct table with proper structure.

        Args:
            cells: 2D array of cell values

        Returns:
            Reconstructed table structure
        """
        if not cells:
            return {"headers": [], "rows": []}

        # Normalize row lengths
        max_cols = max(len(row) for row in cells)
        normalized_cells = []

        for row in cells:
            normalized_row = row + [""] * (max_cols - len(row))
            normalized_cells.append(normalized_row)

        # Detect merged cells (cells with same content in adjacent positions)
        merged_cells = self._detect_merged_cells(normalized_cells)

        return {
            "headers": normalized_cells[0] if normalized_cells else [],
            "rows": normalized_cells[1:] if len(normalized_cells) > 1 else [],
            "merged_cells": merged_cells,
            "dimensions": (len(normalized_cells), max_cols)
        }

    def _detect_merged_cells(self, cells: List[List[str]]) -> List[Dict]:
        """
        Detect merged cells in table.

        Args:
            cells: Normalized 2D array of cells

        Returns:
            List of merged cell regions
        """
        merged = []

        # Simple detection: look for repeated values in adjacent cells
        for i, row in enumerate(cells):
            j = 0
            while j < len(row):
                cell_value = row[j]
                if not cell_value:
                    j += 1
                    continue

                # Check horizontal merge
                merge_end = j + 1
                while merge_end < len(row) and row[merge_end] == cell_value:
                    merge_end += 1

                if merge_end > j + 1:
                    merged.append({
                        "row": i,
                        "col_start": j,
                        "col_end": merge_end - 1,
                        "type": "horizontal"
                    })

                j = merge_end

        return merged
