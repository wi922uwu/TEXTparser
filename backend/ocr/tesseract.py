"""Tesseract 5 OCR engine optimized for maximum text capture."""
import statistics
import pytesseract
from PIL import Image

from backend.config import TESSERACT_CMD, TESSERACT_LANG
from backend.models.schemas import TextRegion


class TesseractEngine:
    """Tesseract 5 OCR engine using image_to_string for best structure preservation."""

    def __init__(
        self,
        lang: str = TESSERACT_LANG,
        tesseract_cmd: str = TESSERACT_CMD,
    ):
        self.lang = lang
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def extract_text_with_string(
        self,
        image: Image.Image,
        psm: int = 4,
    ) -> tuple[str, float]:
        """Extract text using image_to_string (preserves original line structure).

        image_to_string maintains the spatial layout of the document much
        better than rebuilding from image_to_data (TSV). For scanned
        legal documents, this is critical: numbered lists, table headers,
        and signature blocks all depend on accurate line breaks.
        """
        config = f"--psm {psm} -l {self.lang}"
        text = pytesseract.image_to_string(image, config=config)

        # Calculate confidence from HOCR data
        data = pytesseract.image_to_data(
            image,
            lang=self.lang,
            config=f"--psm {psm}",
            output_type=pytesseract.Output.DICT,
        )
        confidences = [
            int(data["conf"][i])
            for i in range(len(data["text"]))
            if data["text"][i].strip() and int(data["conf"][i]) > 0
        ]
        avg_conf = float(statistics.median(confidences)) if confidences else 0.0

        return text.strip(), avg_conf

    def extract_text(
        self,
        image: Image.Image,
    ) -> tuple[str, float]:
        """Extract text using the best method (image_to_string for structure)."""
        return self.extract_text_with_string(image, psm=4)

    def extract_regions(
        self,
        image: Image.Image,
        min_confidence: int = 30,
    ) -> list[TextRegion]:
        """Extract text regions (one per paragraph) with positions and confidence."""
        data = pytesseract.image_to_data(
            image,
            lang=self.lang,
            output_type=pytesseract.Output.DICT,
        )

        paras: dict[tuple[int, int], list[tuple[str, int, int, int, int, int]]] = {}

        for i in range(len(data["text"])):
            word = data["text"][i].strip()
            conf = int(data["conf"][i])

            if not word or conf < min_confidence:
                continue

            block = int(data["block_num"][i])
            par = int(data["par_num"][i])
            para_key = (block, par)

            left = data["left"][i]
            top = data["top"][i]
            width = data["width"][i]
            height = data["height"][i]

            if para_key not in paras:
                paras[para_key] = []
            paras[para_key].append((word, conf, left, top, width, height))

        regions = []
        for _para_key, words in sorted(paras.items()):
            current_block = [w[0] for w in words]
            current_conf = [w[1] for w in words]

            bbox = (
                min(w[2] for w in words),
                min(w[3] for w in words),
                max(w[2] + w[4] for w in words) - min(w[2] for w in words),
                max(w[3] + w[5] for w in words) - min(w[3] for w in words),
            )

            regions.append(
                TextRegion(
                    text=" ".join(current_block),
                    confidence=sum(current_conf) / len(current_conf),
                    bbox=bbox,
                )
            )

        return regions
