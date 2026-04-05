# Document Processor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack web application that extracts text and tables from PDF/image documents with maximum OCR accuracy, running entirely locally.

**Architecture:** FastAPI backend with combined OCR engines (Tesseract 5 + Surya + Table Transformer) + React frontend. Docker Compose for deployment. Files uploaded via web UI, processed through OCR pipeline, downloaded in TXT/DOCX/XLSX format.

**Tech Stack:** Python 3.11+, FastAPI, Tesseract 5, Surya OCR, Table Transformer, OpenCV, PyMuPDF, python-docx, openpyxl, React 18, TypeScript, Vite, Docker.

---

## File Map

| File | Purpose | Phase |
|---|---|---|
| `backend/requirements.txt` | Python dependencies | Task 1 |
| `backend/config.py` | App configuration | Task 1 |
| `backend/models/schemas.py` | Pydantic request/response models | Task 1 |
| `backend/ocr/__init__.py` | Package init | Task 2 |
| `backend/ocr/tesseract.py` | Tesseract 5 OCR engine | Task 2 |
| `backend/ocr/surya.py` | Surya OCR for complex docs | Task 4 |
| `backend/ocr/table.py` | Table Transformer for tables | Task 4 |
| `backend/ocr/engine.py` | Combined OCR orchestrator | Task 4 |
| `backend/preprocess/__init__.py` | Package init | Task 3 |
| `backend/preprocess/image.py` | Image preprocessing pipeline | Task 3 |
| `backend/export/__init__.py` | Package init | Task 5 |
| `backend/export/text.py` | TXT/DOCX export | Task 5 |
| `backend/export/table.py` | XLSX export | Task 5 |
| `backend/pipeline.py` | Document processing pipeline | Task 6 |
| `backend/main.py` | FastAPI app, routes | Task 7 |
| `backend/Dockerfile` | Backend container | Task 13 |
| `frontend/package.json` | Frontend dependencies | Task 8 |
| `frontend/tsconfig.json` | TypeScript config | Task 8 |
| `frontend/vite.config.ts` | Vite config | Task 8 |
| `frontend/index.html` | HTML entry | Task 8 |
| `frontend/src/main.tsx` | React entry point | Task 8 |
| `frontend/src/api/client.ts` | Axios API client | Task 9 |
| `frontend/src/App.tsx` | Main app component | Task 10 |
| `frontend/src/components/Uploader.tsx` | File upload component | Task 11 |
| `frontend/src/components/ResultView.tsx` | Result preview component | Task 11 |
| `frontend/src/index.css` | Global styles | Task 12 |
| `frontend/nginx.conf` | Nginx config for Docker | Task 13 |
| `frontend/Dockerfile` | Frontend container | Task 13 |
| `docker-compose.yml` | Docker orchestration | Task 13 |
| `.dockerignore` | Docker ignore rules | Task 13 |

---

### Task 1: Backend foundation — config, models, dependencies

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/config.py`
- Create: `backend/models/__init__.py`
- Create: `backend/models/schemas.py`

- [ ] **Step 1: Create backend/requirements.txt**

```
# Web framework
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
python-multipart>=0.0.12
pydantic>=2.0.0
aiofiles>=24.1.0

# OCR engines
pytesseract>=0.3.13
surya-ocr>=0.11.0

# Table extraction
transformers>=4.46.0
torch>=2.5.0
table-transformer>=0.1.0
pikepdf>=9.4.0

# Image processing
Pillow>=11.0.0
opencv-python-headless>=4.10.0
scikit-image>=0.24.0
numpy>=2.0.0

# PDF processing
PyMuPDF>=1.24.0

# Export
python-docx>=1.1.0
openpyxl>=3.1.0
```

- [ ] **Step 2: Create backend/config.py**

```python
"""Application configuration."""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Upload settings
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

RESULT_DIR = BASE_DIR / "results"
RESULT_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif"}

# OCR settings
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
TESSERACT_LANG = os.getenv("TESSERACT_LANG", "rus+eng")
OCR_TIMEOUT_SECONDS = int(os.getenv("OCR_TIMEOUT_SECONDS", "60"))
USE_SURYA = os.getenv("USE_SURYA", "true").lower() == "true"

# Export settings
DEFAULT_EXPORT_FORMAT = "txt"
```

- [ ] **Step 3: Create backend/models/__init__.py**

```python
"""Pydantic models for request/response."""
```

- [ ] **Step 4: Create backend/models/schemas.py**

```python
"""API request and response schemas."""
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class ExportFormat(str, Enum):
    TXT = "txt"
    DOCX = "docx"
    XLSX = "xlsx"


class DocumentType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    COMBINED = "combined"


class UploadResponse(BaseModel):
    job_id: str
    filename: str
    status: str = "processing"


class ProcessingStatus(BaseModel):
    job_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    error: Optional[str] = None
    document_type: Optional[DocumentType] = None


class TextRegion(BaseModel):
    text: str
    confidence: float
    bbox: Optional[tuple[int, int, int, int]] = None


class TableRegion(BaseModel):
    cells: list[list[str]]
    bbox: Optional[tuple[int, int, int, int]] = None


class ProcessingResult(BaseModel):
    job_id: str
    document_type: DocumentType
    text_regions: list[TextRegion] = []
    table_regions: list[TableRegion] = []
    full_text: str = ""
    processing_time_ms: int = 0
```

---

### Task 2: Tesseract 5 OCR engine

**Files:**
- Create: `backend/ocr/__init__.py`
- Create: `backend/ocr/tesseract.py`

- [ ] **Step 1: Create backend/ocr/__init__.py**

```python
"""OCR engines."""
from .engine import CombinedOCREngine
from .tesseract import TesseractEngine

__all__ = ["CombinedOCREngine", "TesseractEngine"]
```

- [ ] **Step 2: Create backend/ocr/tesseract.py**

```python
"""Tesseract 5 OCR engine with maximum accuracy settings."""
import pytesseract
from PIL import Image

from backend.config import TESSERACT_CMD, TESSERACT_LANG
from backend.models.schemas import TextRegion


class TesseractEngine:
    """Tesseract 5 OCR engine with high-accuracy configuration."""

    PSM_MODES = {
        "auto": 3,
        "single_column": 4,
        "uniform_block": 6,
        "single_line": 7,
        "single_word": 8,
    }

    def __init__(
        self,
        lang: str = TESSERACT_LANG,
        tesseract_cmd: str = TESSERACT_CMD,
    ):
        self.lang = lang
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def extract_text(
        self,
        image: Image.Image,
        psm: str = "auto",
    ) -> tuple[str, float]:
        """Extract text from image with confidence score.

        Returns:
            Tuple of (full_text, average_confidence_0_100)
        """
        config = f"--psm {self.PSM_MODES[psm]} -c tessedit_create_tsv=1"

        data = pytesseract.image_to_data(
            image,
            lang=self.lang,
            config=config,
            output_type=pytesseract.Output.DICT,
        )

        texts = []
        confidences = []
        for i, word in enumerate(data["text"]):
            word = word.strip()
            if word:
                texts.append(word)
                conf = int(data["conf"][i])
                if conf > 0:
                    confidences.append(conf)

        avg_confidence = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )
        full_text = " ".join(texts)

        return full_text, avg_confidence

    def extract_regions(
        self,
        image: Image.Image,
        min_confidence: int = 30,
    ) -> list[TextRegion]:
        """Extract text regions with positions and confidence."""
        data = pytesseract.image_to_data(
            image,
            lang=self.lang,
            output_type=pytesseract.Output.DICT,
        )

        regions = []
        current_block = []
        current_conf = []
        current_bbox = None

        for i in range(len(data["text"])):
            word = data["text"][i].strip()
            conf = int(data["conf"][i])

            if not word or conf < min_confidence:
                continue

            current_block.append(word)
            current_conf.append(conf)

            left = data["left"][i]
            top = data["top"][i]
            width = data["width"][i]
            height = data["height"][i]

            if current_bbox is None:
                current_bbox = (left, top, width, height)
            else:
                current_bbox = (
                    min(current_bbox[0], left),
                    min(current_bbox[1], top),
                    max(current_bbox[2], width),
                    max(current_bbox[3], height),
                )

        if current_block:
            regions.append(
                TextRegion(
                    text=" ".join(current_block),
                    confidence=sum(current_conf) / len(current_conf),
                    bbox=current_bbox,
                )
            )

        return regions
```

---

### Task 3: Image preprocessing pipeline

**Files:**
- Create: `backend/preprocess/__init__.py`
- Create: `backend/preprocess/image.py`

- [ ] **Step 1: Create backend/preprocess/__init__.py**

```python
"""Image preprocessing utilities."""
```

- [ ] **Step 2: Create backend/preprocess/image.py**

```python
"""Image preprocessing pipeline for maximum OCR accuracy."""
import numpy as np
import cv2
from PIL import Image


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Full preprocessing pipeline to maximize OCR accuracy.

    Steps:
    1. Convert to grayscale
    2. Denoise (Non-local Means)
    3. Deskew (rotate to correct angle)
    4. Binarize (adaptive threshold)
    5. Scale if resolution is too low
    """
    img_array = np.array(image)

    # Convert to grayscale
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    # Denoise
    denoised = cv2.fastNlMeansDenoising(
        gray,
        h=10,
        templateWindowSize=7,
        searchWindowSize=21,
    )

    # Deskew
    deskewed = deskew_image(denoised)

    # Binarize
    binary = adaptive_binarize(deskewed)

    # Scale up if resolution too low
    h, w = binary.shape[:2]
    if h < 600 and w < 600:
        scale = max(600 / h, 600 / w)
        binary = cv2.resize(
            binary,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_CUBIC,
        )

    return Image.fromarray(binary)


def deskew_image(gray: np.ndarray) -> np.ndarray:
    """Detect and correct document skew angle."""
    coords = np.column_stack(np.where(gray > 0))

    if len(coords) < 100:
        return gray

    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = 90 + angle

    if abs(angle) > 1.0:
        h, w = gray.shape
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            gray,
            matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return rotated

    return gray


def adaptive_binarize(gray: np.ndarray) -> np.ndarray:
    """Apply adaptive thresholding for binarization."""
    hist_variance = np.var(gray)

    if hist_variance > 3000:
        _, binary = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
    else:
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=31,
            C=10,
        )

    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    return binary


def pdf_to_images(pdf_path: str, dpi: int = 300) -> list[Image.Image]:
    """Extract pages from PDF as high-resolution PIL Images."""
    import fitz

    doc = fitz.open(pdf_path)
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(image)

    doc.close()
    return images


def load_image_from_file(file_path: str) -> list[Image.Image]:
    """Load image file(s) from disk. Returns list of images."""
    ext = file_path.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        return pdf_to_images(file_path)

    if ext == "tiff" or ext == "tif":
        img = Image.open(file_path)
        images = []
        try:
            while True:
                images.append(img.convert("RGB").copy())
                img.seek(img.tell() + 1)
        except EOFError:
            pass
        return images

    img = Image.open(file_path).convert("RGB")
    return [img]
```

---

### Task 4: Table extraction + Surya OCR + Combined engine

**Files:**
- Create: `backend/ocr/table.py`
- Create: `backend/ocr/surya.py`
- Create: `backend/ocr/engine.py`

- [ ] **Step 1: Create backend/ocr/table.py**

```python
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
```

- [ ] **Step 2: Create backend/ocr/surya.py**

```python
"""Surya OCR engine for complex/low-quality documents."""
from PIL import Image
from typing import Optional

from backend.config import USE_SURYA
from backend.models.schemas import TextRegion


class SuryaEngine:
    """Surya OCR engine for documents where Tesseract struggles."""

    def __init__(self):
        self._loaded = False
        self._detect_model = None
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
                confidence = (
                    det_results[0].confidence
                    if hasattr(det_results[0], "confidence")
                    else 85.0
                )
                return full_text, confidence

            return "", 0.0

        except Exception:
            return "", 0.0
```

- [ ] **Step 3: Create backend/ocr/engine.py**

```python
"""Combined OCR engine that selects the best engine per document."""
from PIL import Image

from backend.config import USE_SURYA
from backend.ocr.tesseract import TesseractEngine
from backend.ocr.surya import SuryaEngine


class CombinedOCREngine:
    """Orchestrates multiple OCR engines for maximum accuracy.

    Strategy:
    1. Run Tesseract (fast, good for quality docs)
    2. If confidence < 60%, also run Surya
    3. Return the higher-confidence result
    """

    CONFIDENCE_THRESHOLD = 60.0

    def __init__(self):
        self.tesseract = TesseractEngine()
        self.surya = SuryaEngine() if USE_SURYA else None

    def extract_text(self, image: Image.Image) -> tuple[str, float]:
        """Extract text using the best available engine."""
        tess_text, tess_conf = self.tesseract.extract_text(image)

        if tess_conf >= self.CONFIDENCE_THRESHOLD:
            return tess_text, tess_conf

        if self.surya:
            surya_text, surya_conf = self.surya.extract_text(image)
            if surya_conf > tess_conf and surya_text.strip():
                return surya_text, surya_conf

        return tess_text, tess_conf

    def is_table_image(self, image: Image.Image) -> bool:
        """Heuristic: check if image contains table-like structure."""
        text, _ = self.tesseract.extract_text(image)
        lines = text.strip().split("\n")

        if len(lines) < 2:
            return False

        col_counts = [len(line.split()) for line in lines if line.strip()]

        if not col_counts:
            return False

        avg_cols = sum(col_counts) / len(col_counts)
        consistent = sum(
            1 for c in col_counts if abs(c - avg_cols) <= 2
        )
        return consistent >= len(col_counts) * 0.6
```

---

### Task 5: Export generators

**Files:**
- Create: `backend/export/__init__.py`
- Create: `backend/export/text.py`
- Create: `backend/export/table.py`

- [ ] **Step 1: Create backend/export/__init__.py**

```python
"""Export generators for different formats."""
```

- [ ] **Step 2: Create backend/export/text.py**

```python
"""Export text to TXT and DOCX formats."""
from pathlib import Path
from docx import Document as DocxDocument
from docx.shared import Pt

from backend.models.schemas import TextRegion, TableRegion


def export_txt(
    text_regions: list[TextRegion],
    table_regions: list[TableRegion],
    output_path: Path,
) -> Path:
    """Export extracted content as plain text."""
    lines = []

    for region in text_regions:
        lines.append(region.text)

    if table_regions and text_regions:
        lines.append("")
        lines.append("--- TABLES ---")
        lines.append("")

    for table in table_regions:
        for row in table.cells:
            lines.append(" | ".join(str(cell) for cell in row))
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def export_docx(
    text_regions: list[TextRegion],
    table_regions: list[TableRegion],
    output_path: Path,
) -> Path:
    """Export extracted content as DOCX with formatted tables."""
    doc = DocxDocument()

    for region in text_regions:
        para = doc.add_paragraph(region.text)
        for run in para.runs:
            run.font.size = Pt(11)

    for table_data in table_regions:
        if not table_data.cells:
            continue

        table = doc.add_table(
            rows=len(table_data.cells),
            cols=max(len(row) for row in table_data.cells),
        )
        table.style = "Table Grid"

        for i, row_cells in enumerate(table_data.cells):
            for j, cell_text in enumerate(row_cells):
                table.cell(i, j).text = str(cell_text)
                for paragraph in table.cell(i, j).paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(10)

        doc.add_paragraph()

    doc.save(str(output_path))
    return output_path
```

- [ ] **Step 3: Create backend/export/table.py**

```python
"""Export tables to XLSX format."""
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

from backend.models.schemas import TableRegion


def export_xlsx(
    table_regions: list[TableRegion],
    output_path: Path,
) -> Path:
    """Export extracted tables as XLSX with formatting."""
    wb = Workbook()
    wb.remove(wb.active)

    header_font = Font(bold=True, size=11)
    header_fill = PatternFill(
        start_color="D9E2F3",
        end_color="D9E2F3",
        fill_type="solid",
    )
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for table_idx, table_data in enumerate(table_regions):
        if not table_data.cells:
            continue

        ws = wb.create_sheet(title=f"Table_{table_idx + 1}")

        for row_idx, row_cells in enumerate(table_data.cells):
            is_header = row_idx == 0
            for col_idx, cell_value in enumerate(row_cells, 1):
                cell = ws.cell(
                    row=row_idx + 1,
                    column=col_idx,
                    value=str(cell_value),
                )
                cell.alignment = Alignment(wrap_text=True)
                cell.border = thin_border

                if is_header:
                    cell.font = header_font
                    cell.fill = header_fill

        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            adjusted = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted

    wb.save(str(output_path))
    return output_path
```

---

### Task 6: Document processing pipeline

**Files:**
- Create: `backend/pipeline.py`

- [ ] **Step 1: Create backend/pipeline.py**

```python
"""Document processing pipeline orchestrator."""
import time
import uuid
from pathlib import Path
from typing import Optional
from PIL import Image
import asyncio
from concurrent.futures import ThreadPoolExecutor

from backend.config import UPLOAD_DIR, RESULT_DIR, OCR_TIMEOUT_SECONDS
from backend.models.schemas import (
    ProcessingResult,
    ProcessingStatus,
    DocumentType,
    TextRegion,
    TableRegion,
    ExportFormat,
)
from backend.preprocess.image import (
    preprocess_for_ocr,
    load_image_from_file,
)
from backend.ocr.engine import CombinedOCREngine
from backend.ocr.table import TableTransformerEngine
from backend.export.text import export_txt, export_docx
from backend.export.table import export_xlsx


_jobs: dict[str, dict] = {}
_executor = ThreadPoolExecutor(max_workers=2)


def process_document(file_path: str) -> str:
    """Start processing a document. Returns job_id."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": ProcessingStatus(
            job_id=job_id,
            status="processing",
            progress=0,
        ),
        "result": None,
        "file_path": file_path,
    }

    loop = asyncio.get_event_loop()
    loop.run_in_executor(_executor, _run_pipeline, job_id, file_path)

    return job_id


def get_job_status(job_id: str) -> Optional[ProcessingStatus]:
    """Get current processing status for a job."""
    job = _jobs.get(job_id)
    if job:
        return job["status"]
    return None


def get_job_result(job_id: str) -> Optional[ProcessingResult]:
    """Get processing result for a job."""
    job = _jobs.get(job_id)
    if job and job["result"]:
        return job["result"]
    return None


def generate_export(job_id: str, fmt: ExportFormat) -> Optional[Path]:
    """Generate export file for a completed job."""
    job = _jobs.get(job_id)
    if not job or not job["result"]:
        return None

    result: ProcessingResult = job["result"]
    output_path = RESULT_DIR / f"{job_id}.{fmt.value}"

    if fmt == ExportFormat.TXT:
        export_txt(result.text_regions, result.table_regions, output_path)
    elif fmt == ExportFormat.DOCX:
        export_docx(result.text_regions, result.table_regions, output_path)
    elif fmt == ExportFormat.XLSX:
        export_xlsx(result.table_regions, output_path)

    return output_path


def _run_pipeline(job_id: str, file_path: str):
    """Execute the full processing pipeline."""
    start_time = time.time()

    try:
        _update_status(job_id, "processing", 10)

        images = load_image_from_file(file_path)
        if not images:
            _fail_job(job_id, "Failed to load images from file")
            return

        _update_status(job_id, "processing", 25)

        all_text_regions: list[TextRegion] = []
        all_table_regions: list[TableRegion] = []
        all_text_lines: list[str] = []
        has_tables = False

        ocr_engine = CombinedOCREngine()

        for img_idx, image in enumerate(images):
            processed = preprocess_for_ocr(image)
            is_table = ocr_engine.is_table_image(image)

            if is_table:
                has_tables = True
                table_engine = TableTransformerEngine()
                tables = table_engine.detect_tables(processed)
                for table_bbox in tables:
                    cells = table_engine.extract_table_cells(
                        processed, table_bbox["bbox"]
                    )
                    all_table_regions.append(
                        TableRegion(cells=cells, bbox=table_bbox["bbox"])
                    )

            text, confidence = ocr_engine.extract_text(processed)
            all_text_lines.append(text)
            all_text_regions.append(
                TextRegion(text=text, confidence=confidence)
            )

            progress = 25 + int(((img_idx + 1) / len(images)) * 50)
            _update_status(job_id, "processing", progress)

        if has_tables and all_text_lines:
            doc_type = DocumentType.COMBINED
        elif has_tables:
            doc_type = DocumentType.TABLE
        else:
            doc_type = DocumentType.TEXT

        elapsed_ms = int((time.time() - start_time) * 1000)

        _jobs[job_id]["result"] = ProcessingResult(
            job_id=job_id,
            document_type=doc_type,
            text_regions=all_text_regions,
            table_regions=all_table_regions,
            full_text="\n\n".join(all_text_lines),
            processing_time_ms=elapsed_ms,
        )

        _update_status(job_id, "completed", 100, doc_type)

    except Exception as e:
        _fail_job(job_id, str(e))


def _update_status(
    job_id: str,
    status: str,
    progress: int,
    doc_type: Optional[DocumentType] = None,
):
    """Update job status."""
    job = _jobs.get(job_id)
    if job:
        job["status"] = ProcessingStatus(
            job_id=job_id,
            status=status,
            progress=progress,
            document_type=doc_type,
        )


def _fail_job(job_id: str, error: str):
    """Mark job as failed."""
    job = _jobs.get(job_id)
    if job:
        job["status"] = ProcessingStatus(
            job_id=job_id,
            status="failed",
            progress=0,
            error=error,
        )
```

---

### Task 7: FastAPI application and routes

**Files:**
- Create: `backend/main.py`

- [ ] **Step 1: Create backend/main.py**

```python
"""FastAPI application with document processing endpoints."""
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.config import (
    UPLOAD_DIR,
    RESULT_DIR,
    MAX_FILE_SIZE_MB,
    ALLOWED_EXTENSIONS,
)
from backend.models.schemas import (
    UploadResponse,
    ProcessingStatus,
    ProcessingResult,
    ExportFormat,
)
from backend.pipeline import (
    process_document,
    get_job_status,
    get_job_result,
    generate_export,
)

app = FastAPI(
    title="Document Processor",
    description="OCR document processing API with maximum accuracy",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for OCR processing."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {ALLOWED_EXTENSIONS}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum: {MAX_FILE_SIZE_MB}MB",
        )

    safe_filename = "".join(
        c for c in file.filename if c.isalnum() or c in "._- "
    )
    file_path = UPLOAD_DIR / safe_filename
    file_path.write_bytes(contents)

    job_id = process_document(str(file_path))

    return UploadResponse(
        job_id=job_id,
        filename=safe_filename,
    )


@app.get("/api/status/{job_id}", response_model=ProcessingStatus)
async def get_processing_status(job_id: str):
    """Get processing status for a job."""
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@app.get("/api/result/{job_id}", response_model=ProcessingResult)
async def get_processing_result(job_id: str):
    """Get processing result for a completed job."""
    result = get_job_result(job_id)
    if not result:
        status = get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        if status.status == "processing":
            raise HTTPException(status_code=202, detail="Job still processing")
        raise HTTPException(status_code=500, detail=f"Job failed: {status.error}")
    return result


@app.get("/api/download/{job_id}/{format}")
async def download_result(job_id: str, format: ExportFormat):
    """Download processed result in specified format."""
    result = get_job_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found or failed")

    output_path = generate_export(job_id, format)
    if not output_path or not output_path.exists():
        raise HTTPException(status_code=500, detail="Export generation failed")

    return FileResponse(
        path=str(output_path),
        filename=f"{job_id}.{format.value}",
        media_type=_get_media_type(format),
    )


def _get_media_type(fmt: ExportFormat) -> str:
    types = {
        ExportFormat.TXT: "text/plain",
        ExportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ExportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    return types[fmt]
```

---

### Task 8: Frontend project scaffolding

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`

- [ ] **Step 1: Create frontend/package.json**

```json
{
  "name": "document-processor-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "axios": "^1.7.0",
    "react-dropzone": "^14.3.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "~5.6.0",
    "vite": "^6.0.0"
  }
}
```

- [ ] **Step 2: Create frontend/tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true
  },
  "include": ["src"]
}
```

- [ ] **Step 3: Create frontend/vite.config.ts**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

- [ ] **Step 4: Create frontend/index.html**

```html
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Document Processor</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Create frontend/src/main.tsx**

```typescript
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

---

### Task 9: Frontend API client

**Files:**
- Create: `frontend/src/api/client.ts`

- [ ] **Step 1: Create frontend/src/api/client.ts**

```typescript
interface UploadResponse {
  job_id: string;
  filename: string;
  status: string;
}

interface ProcessingStatus {
  job_id: string;
  status: "processing" | "completed" | "failed";
  progress: number;
  error?: string;
  document_type?: string;
}

interface ProcessingResult {
  job_id: string;
  document_type: string;
  text_regions: Array<{ text: string; confidence: number }>;
  table_regions: Array<{ cells: string[][] }>;
  full_text: string;
  processing_time_ms: number;
}

const API_BASE = import.meta.env.VITE_API_URL || "";

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Upload failed");
  }

  return response.json();
}

export async function getJobStatus(jobId: string): Promise<ProcessingStatus> {
  const response = await fetch(`${API_BASE}/api/status/${jobId}`);
  return response.json();
}

export async function getJobResult(jobId: string): Promise<ProcessingResult> {
  const response = await fetch(`${API_BASE}/api/result/${jobId}`);
  return response.json();
}

export function getDownloadUrl(jobId: string, format: string): string {
  return `${API_BASE}/api/download/${jobId}/${format}`;
}
```

---

### Task 10: Frontend App component

**Files:**
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Create frontend/src/App.tsx**

```typescript
import { useState, useCallback } from "react";
import { Uploader } from "./components/Uploader";
import { ResultView } from "./components/ResultView";
import type { ProcessingResult, ProcessingStatus } from "./api/client";

type AppPhase = "idle" | "uploading" | "processing" | "done" | "error";

export default function App() {
  const [phase, setPhase] = useState<AppPhase>("idle");
  const [status, setStatus] = useState<ProcessingStatus | null>(null);
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [error, setError] = useState<string>("");

  const handleUploadStart = useCallback(() => {
    setPhase("uploading");
    setError("");
  }, []);

  const handleUploadSuccess = useCallback((jobId: string) => {
    setPhase("processing");

    const pollStatus = async () => {
      try {
        const data: ProcessingStatus = await fetch(
          `/api/status/${jobId}`
        ).then((r) => r.json());
        setStatus(data);

        if (data.status === "completed") {
          const resultData: ProcessingResult = await fetch(
            `/api/result/${jobId}`
          ).then((r) => r.json());
          setResult(resultData);
          setPhase("done");
        } else if (data.status === "failed") {
          setError(data.error || "Processing failed");
          setPhase("error");
        } else {
          setTimeout(pollStatus, 1000);
        }
      } catch {
        setError("Failed to check status");
        setPhase("error");
      }
    };

    setTimeout(pollStatus, 1000);
  }, []);

  const handleUploadError = useCallback((message: string) => {
    setError(message);
    setPhase("error");
  }, []);

  const handleReset = useCallback(() => {
    setPhase("idle");
    setStatus(null);
    setResult(null);
    setError("");
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Document Processor</h1>
        <p className="app-subtitle">
          Загрузите документ для извлечения текста и таблиц
        </p>
      </header>

      <main className="app-main">
        {phase === "idle" && (
          <Uploader
            onUploadStart={handleUploadStart}
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        )}

        {phase === "uploading" && (
          <div className="status-card">
            <div className="spinner" />
            <p>Загрузка файла...</p>
          </div>
        )}

        {phase === "processing" && status && (
          <div className="status-card">
            <div className="spinner" />
            <p>Обработка документа...</p>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${status.progress}%` }}
              />
            </div>
            <span className="progress-text">{status.progress}%</span>
          </div>
        )}

        {phase === "done" && result && (
          <ResultView result={result} onReset={handleReset} />
        )}

        {phase === "error" && (
          <div className="error-card">
            <p className="error-message">{error}</p>
            <button className="btn btn-primary" onClick={handleReset}>
              Попробовать снова
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
```

---

### Task 11: Frontend components — Uploader and ResultView

**Files:**
- Create: `frontend/src/components/Uploader.tsx`
- Create: `frontend/src/components/ResultView.tsx`

- [ ] **Step 1: Create frontend/src/components/Uploader.tsx**

```typescript
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

const ACCEPTED_FILES = {
  "application/pdf": [".pdf"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
  "image/tiff": [".tiff", ".tif"],
};

interface UploaderProps {
  onUploadStart: () => void;
  onUploadSuccess: (jobId: string) => void;
  onUploadError: (message: string) => void;
}

export function Uploader({
  onUploadStart,
  onUploadSuccess,
  onUploadError,
}: UploaderProps) {
  const [dragActive, setDragActive] = useState(false);

  const handleFile = useCallback(
    async (file: File) => {
      onUploadStart();

      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("/api/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const error = await response.json();
          onUploadError(error.detail || "Upload failed");
          return;
        }

        const data = await response.json();
        onUploadSuccess(data.job_id);
      } catch {
        onUploadError("Network error. Check backend connection.");
      }
    },
    [onUploadStart, onUploadSuccess, onUploadError]
  );

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        handleFile(acceptedFiles[0]);
      }
    },
    [handleFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILES,
    maxFiles: 1,
  });

  return (
    <div
      {...getRootProps()}
      className={`dropzone ${isDragActive ? "dropzone-active" : ""}`}
    >
      <input {...getInputProps()} />
      <div className="dropzone-content">
        <svg
          className="dropzone-icon"
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <p className="dropzone-title">
          Перетащите файл сюда или{" "}
          <span className="dropzone-link">выберите файл</span>
        </p>
        <p className="dropzone-formats">
          PDF, JPG, PNG, TIFF (многостраничные)
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create frontend/src/components/ResultView.tsx**

```typescript
import { getDownloadUrl } from "../api/client";
import type { ProcessingResult } from "../api/client";

interface ResultViewProps {
  result: ProcessingResult;
  onReset: () => void;
}

export function ResultView({ result, onReset }: ResultViewProps) {
  const formats = getAvailableFormats(result);

  return (
    <div className="result-card">
      <div className="result-header">
        <h2>Обработка завершена</h2>
        <span className="result-time">
          {result.processing_time_ms} мс
        </span>
      </div>

      <div className="result-type">
        Тип документа:{" "}
        <strong>
          {result.document_type === "text" && "Текст"}
          {result.document_type === "table" && "Таблица"}
          {result.document_type === "combined" && "Комбинированный"}
        </strong>
      </div>

      {result.text_regions.length > 0 && (
        <details className="result-preview">
          <summary>Предпросмотр текста</summary>
          <pre className="result-text">{result.full_text}</pre>
        </details>
      )}

      {result.table_regions.length > 0 && (
        <div className="result-tables">
          <h3>Обнаружено таблиц: {result.table_regions.length}</h3>
          {result.table_regions.map((table, i) => (
            <details key={i} className="table-preview">
              <summary>Таблица {i + 1}</summary>
              <table className="data-table">
                <tbody>
                  {table.cells.map((row, ri) => (
                    <tr key={ri}>
                      {row.map((cell, ci) => (
                        <td key={ci}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          ))}
        </div>
      )}

      <div className="download-section">
        <h3>Скачать результат</h3>
        <div className="download-buttons">
          {formats.map((fmt) => (
            <a
              key={fmt}
              href={getDownloadUrl(result.job_id, fmt)}
              className="btn btn-download"
              download
            >
              {fmt.toUpperCase()}
            </a>
          ))}
        </div>
      </div>

      <button className="btn btn-secondary" onClick={onReset}>
        Загрузить другой документ
      </button>
    </div>
  );
}

function getAvailableFormats(result: ProcessingResult): string[] {
  if (result.document_type === "table") {
    return ["xlsx"];
  }
  const formats = ["txt", "docx"];
  if (result.table_regions.length > 0) {
    formats.push("xlsx");
  }
  return formats;
}
```

---

### Task 12: Frontend styles

**Files:**
- Create: `frontend/src/index.css`

- [ ] **Step 1: Create frontend/src/index.css**

```css
:root {
  --color-bg: #f8f9fa;
  --color-surface: #ffffff;
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-text: #1e293b;
  --color-text-muted: #64748b;
  --color-border: #e2e8f0;
  --color-success: #22c55e;
  --color-error: #ef4444;
  --radius: 8px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  line-height: 1.6;
}

.app {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.app-header {
  text-align: center;
  margin-bottom: 2rem;
}

.app-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
}

.app-subtitle {
  color: var(--color-text-muted);
  margin-top: 0.5rem;
}

.dropzone {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius);
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--color-surface);
}

.dropzone-active {
  border-color: var(--color-primary);
  background: #eff6ff;
}

.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.dropzone-icon {
  color: var(--color-text-muted);
}

.dropzone-title {
  font-size: 1rem;
  color: var(--color-text);
}

.dropzone-link {
  color: var(--color-primary);
  font-weight: 600;
}

.dropzone-formats {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.status-card,
.error-card {
  background: var(--color-surface);
  border-radius: var(--radius);
  padding: 2rem;
  text-align: center;
  box-shadow: var(--shadow);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.progress-bar {
  height: 8px;
  background: var(--color-border);
  border-radius: 4px;
  overflow: hidden;
  margin: 1rem 0 0.5rem;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.result-card {
  background: var(--color-surface);
  border-radius: var(--radius);
  padding: 2rem;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-time {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.result-type {
  padding: 0.75rem 1rem;
  background: #f1f5f9;
  border-radius: var(--radius);
  font-size: 0.875rem;
}

.result-preview,
.table-preview {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1rem;
}

.result-preview summary,
.table-preview summary {
  cursor: pointer;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.result-text {
  background: #f8fafc;
  padding: 1rem;
  border-radius: 4px;
  font-size: 0.875rem;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 300px;
  overflow-y: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.data-table td,
.data-table th {
  border: 1px solid var(--color-border);
  padding: 0.5rem;
  text-align: left;
}

.download-section {
  border-top: 1px solid var(--color-border);
  padding-top: 1.5rem;
}

.download-section h3 {
  margin-bottom: 1rem;
}

.download-buttons {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius);
  font-size: 0.875rem;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: none;
  transition: background 0.2s;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

.btn-secondary {
  background: var(--color-border);
  color: var(--color-text);
}

.btn-secondary:hover {
  background: #cbd5e1;
}

.btn-download {
  background: var(--color-success);
  color: white;
}

.btn-download:hover {
  background: #16a34a;
}

.error-message {
  color: var(--color-error);
  font-weight: 500;
  margin-bottom: 1rem;
}
```

---

### Task 13: Docker configuration

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

- [ ] **Step 1: Create backend/Dockerfile**

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create frontend/Dockerfile**

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 3: Create frontend/nginx.conf**

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }
}
```

- [ ] **Step 4: Create docker-compose.yml**

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - uploads_data:/app/uploads
      - results_data:/app/results
    environment:
      - TESSERACT_LANG=rus+eng
      - USE_SURYA=true
      - OCR_TIMEOUT_SECONDS=60
    deploy:
      resources:
        limits:
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 10s
      timeout: 5s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy

volumes:
  uploads_data:
  results_data:
```

- [ ] **Step 5: Create .dockerignore**

```
.git
.gitignore
*.md
docs/
.remember/
tz.txt
node_modules/
__pycache__/
*.pyc
.pytest_cache/
.venv/
```

---

## Task Ordering & Dependencies

```
Task 1 (backend foundation)
  -> Task 2 (Tesseract engine)
  -> Task 3 (preprocessing)
     -> Task 4 (Table + Surya + combined engine)
        -> Task 5 (export generators)
           -> Task 6 (pipeline)
              -> Task 7 (FastAPI app)

Task 8 (frontend scaffold)
  -> Task 9 (API client)
     -> Task 10 (App component)
        -> Task 11 (Uploader + ResultView)
           -> Task 12 (styles)

Task 7 + Task 12
  -> Task 13 (Docker)
```

## Verification

1. `docker compose up --build` — builds and starts both services
2. Open `http://localhost` in browser
3. Upload a test PDF with text and tables
4. Verify text extraction quality in preview
5. Verify table extraction in preview
6. Download TXT, DOCX, XLSX — verify content
7. Check processing time < 30 seconds in result display
