"""Table extraction using Microsoft Table Transformer."""
import torch
from PIL import Image
from transformers import TableTransformerForObjectDetection, AutoImageProcessor

from backend.models.schemas import TableRegion


class TableTransformerEngine:
    """Extract tables from document images using Table Transformer."""

    MODEL_NAME = "microsoft/table-transformer-structure-recognition"

    def __init__(self, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = AutoImageProcessor.from_pretrained(self.MODEL_NAME)
        self.model = TableTransformerForObjectDetection.from_pretrained(
            self.MODEL_NAME
        ).to(self.device)
        self.model.eval()

    def detect_tables(self, image: Image.Image) -> list[dict]:
        """Detect table regions in image."""
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

        target_sizes = [image.size[::-1]]
        results = self.processor.post_process_object_detection(
            outputs,
            threshold=0.7,
            target_sizes=target_sizes,
        )

        tables = []
        for score, label, box in zip(
            results[0]["scores"],
            results[0]["labels"],
            results[0]["boxes"],
        ):
            if label.item() == 0 and score.item() > 0.7:
                x1, y1, x2, y2 = box.tolist()
                tables.append({
                    "bbox": (int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
                    "confidence": score.item(),
                })

        return tables

    def extract_table_cells(
        self,
        image: Image.Image,
        table_bbox: tuple[int, int, int, int],
    ) -> list[list[str]]:
        """Extract cell data from a cropped table region."""
        from backend.ocr.tesseract import TesseractEngine

        x, y, w, h = table_bbox
        cropped = image.crop((x, y, x + w, y + h))

        inputs = self.processor(images=cropped, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

        target_sizes = [cropped.size[::-1]]
        results = self.processor.post_process_object_detection(
            outputs,
            threshold=0.5,
            target_sizes=target_sizes,
        )

        cells = []
        for score, label, box in zip(
            results[0]["scores"],
            results[0]["labels"],
            results[0]["boxes"],
        ):
            if label.item() in (1, 2):
                cells.append(box.tolist())

        if not cells:
            return self._fallback_extract(cropped)

        cells.sort(key=lambda b: (b[1], b[0]))
        rows = self._cluster_cells_into_rows(cells, 10)

        tesseract = TesseractEngine()
        grid = []
        for row_cells in rows:
            row_texts = []
            for cell_box in row_cells:
                cx1, cy1, cx2, cy2 = [int(c) for c in cell_box]
                cell_img = cropped.crop((cx1, cy1, cx2, cy2))
                text, _ = tesseract.extract_text(cell_img)
                row_texts.append(text)
            grid.append(row_texts)

        return grid

    def _cluster_cells_into_rows(
        self,
        cells: list[list[float]],
        threshold: float,
    ) -> list[list[list[float]]]:
        """Cluster cell boxes into rows based on Y coordinate."""
        rows = []
        current_row = []
        last_y = None

        for cell in sorted(cells, key=lambda c: c[1]):
            if last_y is None or abs(cell[1] - last_y) < threshold:
                current_row.append(cell)
            else:
                rows.append(sorted(current_row, key=lambda c: c[0]))
                current_row = [cell]
            last_y = cell[1]

        if current_row:
            rows.append(sorted(current_row, key=lambda c: c[0]))

        return rows

    def _fallback_extract(self, image: Image.Image) -> list[list[str]]:
        """Fallback: split image by horizontal projection."""
        import numpy as np

        gray = np.array(image.convert("L"))
        row_projection = np.mean(gray, axis=1)
        threshold = np.mean(row_projection) + np.std(row_projection)
        white_rows = np.where(row_projection > threshold)[0]

        if len(white_rows) < 2:
            from backend.ocr.tesseract import TesseractEngine
            text, _ = TesseractEngine().extract_text(image)
            return [[text]]

        row_bands = []
        start = white_rows[0]
        for i in range(1, len(white_rows)):
            if white_rows[i] - white_rows[i - 1] > 5:
                row_bands.append((start, white_rows[i - 1]))
                start = white_rows[i]
        row_bands.append((start, white_rows[-1]))

        from backend.ocr.tesseract import TesseractEngine
        tesseract = TesseractEngine()
        grid = []

        for y1, y2 in row_bands:
            row_img = image.crop((0, int(y1), image.width, int(y2)))
            text, _ = tesseract.extract_text(row_img)
            cols = text.split()
            grid.append(cols)

        return grid
