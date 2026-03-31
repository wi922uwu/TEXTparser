"""
Image preprocessing for better OCR accuracy.
"""
import cv2
import numpy as np
from pathlib import Path
import logging

from app.constants import (
    PREPROCESS_MAX_DIMENSION,
    PREPROCESS_LOW_CONTRAST_STD_DEV_THRESHOLD,
    ENHANCE_LARGE_IMAGE_THRESHOLD,
    ENHANCE_BILATERAL_FILTER_D,
    ENHANCE_BILATERAL_FILTER_SIGMA_COLOR,
    ENHANCE_BILATERAL_FILTER_SIGMA_SPACE,
    ENHANCE_NL_MEANS_H,
    ENHANCE_NL_MEANS_TEMPLATE_WINDOW,
    ENHANCE_NL_MEANS_SEARCH_WINDOW,
    ENHANCE_CLAHE_CLIP_LIMIT,
    ENHANCE_CLAHE_TILE_GRID_SIZE,
    DESKEW_CANNY_THRESH1,
    DESKEW_CANNY_THRESH2,
    DESKEW_CANNY_APERTURE_SIZE,
    DESKEW_HOUGH_THRESHOLD,
    DESKEW_ANGLE_THRESHOLD,
)

logger = logging.getLogger(__name__)


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert image to grayscale if needed.

    Args:
        image: Input image as numpy array

    Returns:
        Grayscale image
    """
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image.copy()


def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Detect and correct image skew.

    Args:
        image: Input image as numpy array

    Returns:
        Deskewed image
    """
    # Convert to grayscale using helper function
    gray = to_grayscale(image)

    # Detect edges
    edges = cv2.Canny(gray, DESKEW_CANNY_THRESH1, DESKEW_CANNY_THRESH2, apertureSize=DESKEW_CANNY_APERTURE_SIZE)

    # Detect lines using Hough transform
    lines = cv2.HoughLines(edges, 1, np.pi / 180, DESKEW_HOUGH_THRESHOLD)

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
    if abs(median_angle) > DESKEW_ANGLE_THRESHOLD:
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h),
                                 flags=cv2.INTER_CUBIC,
                                 borderMode=cv2.BORDER_REPLICATE)
        return rotated

    return image


def enhance_image(image: np.ndarray, fast_mode: bool = False, quality_mode: bool = True) -> np.ndarray:
    """
    Enhance image quality for better OCR.
    Optimized for speed (target: <60 sec for 5MB file).

    Args:
        image: Input image
        fast_mode: Use faster processing
        quality_mode: Use enhanced processing for better quality

    Returns:
        Enhanced grayscale image
    """
    # Convert to grayscale using helper function (Проблема 9 - устранение дублирования)
    gray = to_grayscale(image)

    # Denoise - optimized for speed
    height, width = gray.shape
    if max(height, width) > ENHANCE_LARGE_IMAGE_THRESHOLD:
        # Fast bilateral filter for large images (5x faster)
        denoised = cv2.bilateralFilter(
            gray,
            ENHANCE_BILATERAL_FILTER_D,
            ENHANCE_BILATERAL_FILTER_SIGMA_COLOR,
            ENHANCE_BILATERAL_FILTER_SIGMA_SPACE
        )
    else:
        # Standard denoise for smaller images
        denoised = cv2.fastNlMeansDenoising(
            gray, None,
            h=ENHANCE_NL_MEANS_H,
            templateWindowSize=ENHANCE_NL_MEANS_TEMPLATE_WINDOW,
            searchWindowSize=ENHANCE_NL_MEANS_SEARCH_WINDOW
        )

    # Enhance contrast using CLAHE - balanced settings
    clahe = cv2.createCLAHE(
        clipLimit=ENHANCE_CLAHE_CLIP_LIMIT,
        tileGridSize=ENHANCE_CLAHE_TILE_GRID_SIZE
    )
    enhanced = clahe.apply(denoised)

    # Light sharpening only for quality mode
    if quality_mode and not fast_mode:
        kernel = np.array([[-1, -1, -1],
                           [-1,  9, -1],
                           [-1, -1, -1]])
        enhanced = cv2.filter2D(enhanced, -1, kernel)

    # Return grayscale - PaddleOCR handles grayscale better
    return enhanced


def preprocess_for_ocr(image_path: str, output_path: str = None, use_smart_binarize: bool = False, fast_mode: bool = False) -> str:
    """
    Full preprocessing pipeline for OCR.

    Args:
        image_path: Path to input image
        output_path: Optional path to save preprocessed image
        use_smart_binarize: Enable smart binarization for low contrast documents
        fast_mode: Use fast preprocessing for speed

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

        # Enhance (with fast mode support)
        enhanced = enhance_image(deskewed, fast_mode=fast_mode)

        # Optional smart binarization for low contrast documents
        if use_smart_binarize:
            enhanced = smart_binarize(enhanced)

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


def smart_binarize(image: np.ndarray) -> np.ndarray:
    """
    Smart binarization with automatic threshold selection.
    Only used for documents with very low contrast.

    Args:
        image: Input grayscale image

    Returns:
        Binarized image if low contrast, otherwise original
    """
    # Calculate standard deviation to determine contrast
    std_dev = np.std(image)

    if std_dev < PREPROCESS_LOW_CONTRAST_STD_DEV_THRESHOLD:  # Low contrast - apply binarization
        # Use Otsu's thresholding after Gaussian blur
        blur = cv2.GaussianBlur(image, (5, 5), 0)
        _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        logger.info(f"Applied Otsu binarization (std_dev={std_dev:.1f})")
        return binary
    else:
        # Good contrast - keep grayscale
        logger.info(f"Skipping binarization (std_dev={std_dev:.1f})")
        return image


def resize_if_needed(image: np.ndarray, max_dimension: int = PREPROCESS_MAX_DIMENSION) -> np.ndarray:
    """
    Resize image if it's too large.

    Args:
        image: Input image
        max_dimension: Maximum width or height (default: PREPROCESS_MAX_DIMENSION)

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
