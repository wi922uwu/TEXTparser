"""
Image preprocessing for better OCR accuracy.
"""
import cv2
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Detect and correct image skew.

    Args:
        image: Input image as numpy array

    Returns:
        Deskewed image
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Detect edges
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Detect lines using Hough transform
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

    if lines is None:
        return image

    # Calculate average angle
    angles = []
    for rho, theta in lines[:, 0]:
        angle = np.degrees(theta) - 90
        if -45 < angle < 45:
            angles.append(angle)

    if not angles:
        return image

    median_angle = np.median(angles)

    # Rotate image if skew is significant
    if abs(median_angle) > 0.5:
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h),
                                 flags=cv2.INTER_CUBIC,
                                 borderMode=cv2.BORDER_REPLICATE)
        return rotated

    return image


def enhance_image(image: np.ndarray) -> np.ndarray:
    """
    Enhance image quality for better OCR.

    Args:
        image: Input image

    Returns:
        Enhanced image
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    # Enhance contrast using CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # Binarization using adaptive thresholding
    binary = cv2.adaptiveThreshold(
        enhanced, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    return binary


def preprocess_for_ocr(image_path: str, output_path: str = None) -> str:
    """
    Full preprocessing pipeline for OCR.

    Args:
        image_path: Path to input image
        output_path: Optional path to save preprocessed image

    Returns:
        Path to preprocessed image
    """
    try:
        # Read image
        image = cv2.imread(image_path)

        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        # Deskew
        deskewed = deskew_image(image)

        # Enhance
        enhanced = enhance_image(deskewed)

        # Save preprocessed image
        if output_path is None:
            path = Path(image_path)
            output_path = str(path.parent / f"{path.stem}_preprocessed{path.suffix}")

        cv2.imwrite(output_path, enhanced)

        logger.info(f"Preprocessed image saved to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error preprocessing image {image_path}: {e}")
        # Return original path if preprocessing fails
        return image_path


def resize_if_needed(image: np.ndarray, max_dimension: int = 4096) -> np.ndarray:
    """
    Resize image if it's too large.

    Args:
        image: Input image
        max_dimension: Maximum width or height

    Returns:
        Resized image if needed
    """
    h, w = image.shape[:2]

    if max(h, w) > max_dimension:
        scale = max_dimension / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logger.info(f"Resized image from {w}x{h} to {new_w}x{new_h}")
        return resized

    return image
