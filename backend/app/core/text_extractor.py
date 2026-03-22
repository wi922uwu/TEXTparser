"""
Text extraction and structuring from OCR results.
"""
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def extract_text_blocks(ocr_result: Dict) -> List[Dict]:
    """
    Extract and structure text blocks from OCR result.

    Args:
        ocr_result: OCR result dictionary

    Returns:
        List of structured text blocks
    """
    return ocr_result.get("text_blocks", [])


def sort_reading_order(blocks: List[Dict]) -> List[Dict]:
    """
    Sort text blocks in reading order (top-to-bottom, left-to-right).

    Args:
        blocks: List of text blocks with bounding boxes

    Returns:
        Sorted list of blocks
    """
    if not blocks:
        return blocks

    # Sort by vertical position first (y-coordinate)
    # Then by horizontal position (x-coordinate) for blocks on same line
    sorted_blocks = sorted(blocks, key=lambda b: (
        b["box"][0][1],  # Top y-coordinate
        b["box"][0][0]   # Left x-coordinate
    ))

    return sorted_blocks


def group_into_paragraphs(blocks: List[Dict], line_threshold: int = 30) -> List[str]:
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


def assemble_text(blocks: List[Dict], preserve_structure: bool = True) -> str:
    """
    Assemble final text from blocks.

    Args:
        blocks: Text blocks
        preserve_structure: Whether to preserve paragraph structure

    Returns:
        Final assembled text
    """
    if not blocks:
        return ""

    sorted_blocks = sort_reading_order(blocks)

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
    blocks = extract_text_blocks(ocr_result)
    sorted_blocks = sort_reading_order(blocks)
    paragraphs = group_into_paragraphs(sorted_blocks)
    full_text = assemble_text(blocks)

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
