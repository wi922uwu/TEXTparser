"""
Base exporter interface.
"""
from abc import ABC, abstractmethod
from typing import Dict
from pathlib import Path


class BaseExporter(ABC):
    """Abstract base class for all exporters."""

    @abstractmethod
    def export(self, data: Dict, output_path: str) -> str:
        """
        Export data to specified format.

        Args:
            data: Processed OCR data
            output_path: Path to save exported file

        Returns:
            Path to exported file
        """
        pass

    def _ensure_output_dir(self, output_path: str) -> None:
        """Ensure output directory exists."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
