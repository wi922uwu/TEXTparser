"""
CSV exporter for comma-separated values.
"""
import csv
from typing import Dict
import logging
from app.exporters.base import BaseExporter

logger = logging.getLogger(__name__)


class CSVExporter(BaseExporter):
    """Export OCR results to CSV format."""

    def export(self, data: Dict, output_path: str) -> str:
        """
        Export to CSV file.

        Args:
            data: OCR result data
            output_path: Output file path

        Returns:
            Path to created file
        """
        self._ensure_output_dir(output_path)

        try:
            # CSV export is primarily for tables
            tables = data.get("tables", [])

            if not tables:
                # If no tables, create a simple CSV with text
                with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    text_data = data.get("text", {})
                    full_text = text_data.get("full_text", "")
                    if full_text:
                        writer.writerow(["Текст"])
                        for line in full_text.split("\n"):
                            if line.strip():
                                writer.writerow([line.strip()])
            else:
                # Export first table to CSV
                # For multiple tables, we'd need separate files
                with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)

                    cells = tables[0].get("cells", [])
                    for row in cells:
                        writer.writerow(row)

            logger.info(f"Exported to CSV: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
