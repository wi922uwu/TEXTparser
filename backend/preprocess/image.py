"""Image preprocessing pipeline for maximum OCR accuracy."""
import cv2
import numpy as np
from PIL import Image


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """No-op preprocessing: return grayscale only.

    Tesseract 5 has built-in Leptonica binarization that works best
    on unmodified grayscale images. CLAHE, denoise, and morphological
    ops were found to reduce word count on scanned documents.
    """
    img_array = np.array(image)

    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    # Only deskew if angle > 1 degree
    result = deskew_image(gray)

    # Scale up only if truly tiny
    h, w = result.shape[:2]
    if h < 400 or w < 400:
        scale = max(400 / h, 400 / w)
        result = cv2.resize(
            result,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_CUBIC,
        )

    return Image.fromarray(result)


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


def pdf_to_images(pdf_path: str, dpi: int = 200) -> list[Image.Image]:
    """Extract pages from PDF as PIL Images.

    200 DPI empirically gives the best Tesseract results on scanned documents:
    - Better than 300: no scaling artifacts
    - Better than 150: enough resolution for Cyrillic characters
    """
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
