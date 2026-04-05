"""Surya OCR engine for complex/low-quality documents."""
from PIL import Image

from backend.config import USE_SURYA


class SuryaEngine:
    """Surya OCR engine for documents where Tesseract struggles."""

    def __init__(self):
        self._loaded = False
        self._detect_model = None
        self._detect_config = None
        self._recognition_model = None
        self._rec_processor = None

    def _load_models(self):
        """Lazy load Surya models on first use."""
        if self._loaded:
            return

        if not USE_SURYA:
            return

        try:
            from surya.model.detection.model import (
                load_model as load_det_model,
            )
            from surya.model.detection.config import (
                load_config as load_det_config,
            )
            from surya.model.recognition.model import (
                load_model as load_rec_model,
            )
            from surya.model.recognition.processor import (
                load_processor as load_rec_processor,
            )

            det_model, det_config = load_det_model()
            rec_model = load_rec_model()
            rec_processor = load_rec_processor()

            self._detect_model = det_model
            self._detect_config = det_config
            self._recognition_model = rec_model
            self._rec_processor = rec_processor
            self._loaded = True
        except ImportError:
            self._loaded = False

    def extract_text(self, image: Image.Image) -> tuple[str, float]:
        """Extract text using Surya OCR."""
        self._load_models()

        if not self._loaded:
            return "", 0.0

        try:
            from surya.input.processing import convert_if_not_rgb
            from surya.detection import batch_text_detection
            from surya.ocr import run_ocr

            images = convert_if_not_rgb([image])

            det_results = batch_text_detection(
                images, self._detect_model, self._detect_config
            )

            rec_results = run_ocr(
                images,
                det_results,
                self._recognition_model,
                self._rec_processor,
            )

            if rec_results:
                full_text = rec_results[0].text

                # Use real recognition confidence if available
                if hasattr(rec_results[0], "confidence_scores"):
                    scores = rec_results[0].confidence_scores
                    if scores and len(scores) > 0:
                        import statistics
                        confidence = float(
                            statistics.median(scores) * 100
                            if scores[0] <= 1.0
                            else statistics.median(scores)
                        )
                    else:
                        confidence = 0.0
                elif hasattr(det_results[0], "confidence"):
                    confidence = float(det_results[0].confidence)
                else:
                    confidence = 0.0

                return full_text, confidence

            return "", 0.0

        except Exception:
            return "", 0.0
