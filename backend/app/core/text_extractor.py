"""
Text extraction and structuring from OCR results.
"""
from typing import List, Dict
import logging

from app.constants import PREPROCESS_LINE_THRESHOLD

logger = logging.getLogger(__name__)


def sort_reading_order(blocks: List[Dict], line_tolerance: int = 10) -> List[Dict]:
    """
    Sort text blocks in reading order (top-to-bottom, left-to-right).

    Uses line grouping to handle multi-column documents correctly:
    1. Group blocks by Y-coordinate with tolerance
    2. Sort groups by Y (top-to-bottom)
    3. Sort each group by X (left-to-right)

    Args:
        blocks: List of text blocks with bounding boxes
        line_tolerance: Pixels of vertical tolerance for grouping blocks on same line

    Returns:
        Sorted list of blocks
    """
    if not blocks:
        return blocks

    # Group blocks by vertical position with tolerance
    # This handles multi-column documents correctly
    groups = []
    for block in blocks:
        y_center = block["box"][0][1]
        placed = False

        for group in groups:
            # Check if this block belongs to an existing group (same line)
            group_y = group[0]["box"][0][1]
            if abs(y_center - group_y) <= line_tolerance:
                group.append(block)
                placed = True
                break

        if not placed:
            groups.append([block])

    # Sort each group by X-coordinate (left-to-right)
    for group in groups:
        group.sort(key=lambda b: b["box"][0][0])

    # Sort groups by Y-coordinate (top-to-bottom) and flatten
    groups.sort(key=lambda g: g[0]["box"][0][1])

    sorted_blocks = []
    for group in groups:
        sorted_blocks.extend(group)

    return sorted_blocks


def group_into_paragraphs(blocks: List[Dict], line_threshold: int = PREPROCESS_LINE_THRESHOLD) -> List[str]:
    """
    Group text blocks into paragraphs based on vertical spacing.

    Args:
        blocks: Sorted text blocks
        line_threshold: Vertical distance threshold for new paragraph

    Returns:
        List of paragraph strings
    """
    if not blocks:
        return []

    paragraphs = []
    current_paragraph = []
    prev_y = None

    for block in blocks:
        current_y = block["box"][0][1]

        if prev_y is not None and abs(current_y - prev_y) > line_threshold:
            # Start new paragraph
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph))
                current_paragraph = []

        current_paragraph.append(block["text"])
        prev_y = current_y

    # Add last paragraph
    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))

    return paragraphs


def assemble_text(blocks: List[Dict], preserve_structure: bool = True, already_sorted: bool = False) -> str:
    """
    Assemble final text from blocks.

    Args:
        blocks: Text blocks
        preserve_structure: Whether to preserve paragraph structure
        already_sorted: If True, blocks are already sorted (skip redundant sorting)

    Returns:
        Final assembled text
    """
    if not blocks:
        return ""

    # Проблема 13: Убираем повторную сортировку, если блоки уже отсортированы
    sorted_blocks = blocks if already_sorted else sort_reading_order(blocks)

    if preserve_structure:
        paragraphs = group_into_paragraphs(sorted_blocks)
        return "\n\n".join(paragraphs)
    else:
        return "\n".join([block["text"] for block in sorted_blocks])


def extract_structured_text(ocr_result: Dict) -> Dict:
    """
    Extract structured text with metadata.

    Args:
        ocr_result: OCR result dictionary

    Returns:
        Structured text with metadata
    """
    # Проблема 12: Удалена функция extract_text_blocks(), используем напрямую
    blocks = ocr_result.get("text_blocks", [])
    sorted_blocks = sort_reading_order(blocks)
    paragraphs = group_into_paragraphs(sorted_blocks)
    # Проблема 13: Используем уже отсортированные блоки
    full_text = assemble_text(sorted_blocks, already_sorted=True)

    # Calculate average confidence
    confidences = [b["confidence"] for b in blocks if "confidence" in b]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return {
        "full_text": full_text,
        "paragraphs": paragraphs,
        "block_count": len(blocks),
        "average_confidence": avg_confidence,
        "blocks": sorted_blocks
    }
