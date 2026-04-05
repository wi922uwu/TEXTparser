"""EasyOCR engine — single path, best accuracy for Russian+English."""
import cv2
import numpy as np
from PIL import Image

from backend.models.schemas import TextRegion


class EasyOCREngine:
    """EasyOCR engine optimized for Russian+English document text."""

    def __init__(self):
        self._reader = None

    def _get_reader(self):
        if self._reader is None:
            import easyocr
            self._reader = easyocr.Reader(['ru', 'en'], gpu=False, verbose=False)
        return self._reader

    def extract_text(self, image: Image.Image) -> tuple[str, float]:
        """Extract text using EasyOCR with CLAHE preprocessing."""
        reader = self._get_reader()

        arr = np.array(image)
        if len(arr.shape) == 3:
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        else:
            gray = arr

        # CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(6, 6))
        enhanced = clahe.apply(gray)

        result = reader.readtext(enhanced, detail=0, paragraph=True)
        text = '\n'.join(result)

        # Estimate confidence from word presence
        words = len(text.split())
        confidence = min(100.0, words * 0.5) if text.strip() else 0.0

        return text, confidence

    def extract_regions(self, image: Image.Image, min_confidence: int = 30) -> list[TextRegion]:
        """Extract text as regions."""
        text, conf = self.extract_text(image)
        return [TextRegion(text=text, confidence=conf)]
