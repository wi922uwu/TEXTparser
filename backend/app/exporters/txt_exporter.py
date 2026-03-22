"""
TXT exporter for plain text output.
"""
from typing import Dict
import logging
from app.exporters.base import BaseExporter

logger = logging.getLogger(__name__)


class TXTExporter(BaseExporter):
    """Export OCR results to plain text format."""

    def export(self, data: Dict, output_path: str) -> str:
        """
        Export to TXT file.

        Args:
            data: OCR result data
            output_path: Output file path

        Returns:
            Path to created file
        """
        self._ensure_output_dir(output_path)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write text content
                text_data = data.get("text", {})
                full_text = text_data.get("full_text", "")

                if full_text:
                    f.write(full_text)
                    f.write("\n\n")

                # Write tables as ASCII tables
                tables = data.get("tables", [])
                if tables:
                    f.write("=" * 80 + "\n")
                    f.write("ТАБЛИЦЫ\n")
                    f.write("=" * 80 + "\n\n")

                    for idx, table in enumerate(tables, 1):
                        f.write(f"Таблица {idx}:\n")
                        f.write("-" * 80 + "\n")

                        cells = table.get("cells", [])
                        if cells:
                            # Simple tab-separated format
                            for row in cells:
                                f.write("\t".join(str(cell) for cell in row))
                                f.write("\n")

                        f.write("\n")

            logger.info(f"Exported to TXT: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting to TXT: {e}")
            raise
