"""
Constants for OCR application.
Centralized configuration for magic numbers and settings.
"""

# OCR Detection limits
OCR_DET_LIMIT_SIDE_LEN = 1920  # Balanced resolution for detection
OCR_DET_LIMIT_SIDE_LEN_FAST = 960  # Lower resolution for speed
OCR_DET_LIMIT_SIDE_LEN_HQ = 2560  # High resolution for best quality

# OCR Detection thresholds
OCR_DET_DB_THRESH = 0.15  # Lower threshold for better text detection
OCR_DET_DB_THRESH_FAST = 0.25  # Higher threshold for speed
OCR_DET_DB_THRESH_HQ = 0.1  # Very low threshold for maximum sensitivity
OCR_DET_DB_BOX_THRESH = 0.45  # Lower threshold for better bounding boxes
OCR_DET_DB_BOX_THRESH_FAST = 0.55
OCR_DET_DB_BOX_THRESH_HQ = 0.4  # Maximum sensitivity for bounding boxes
OCR_DET_DB_UNCLIP_RATIO = 1.8  # Good for contours
OCR_DET_DB_UNCLIP_RATIO_FAST = 1.6
OCR_DET_DB_UNCLIP_RATIO_HQ = 2.0  # More aggressive expansion for better coverage

# OCR Recognition settings
OCR_REC_BATCH_NUM = 12  # Larger batch size for better quality
OCR_REC_BATCH_NUM_FAST = 6
OCR_REC_BATCH_NUM_HQ = 24  # Maximum batch size for best quality
OCR_MAX_TEXT_LENGTH = 200  # Support longer text lines
OCR_MAX_TEXT_LENGTH_FAST = 80
OCR_MAX_TEXT_LENGTH_HQ = 300  # Support very long text lines

# OCR Processing settings
OCR_TOTAL_PROCESS_NUM = 2  # 2 processes for dual-core+ CPUs
OCR_USE_MP = True  # Enable multiprocessing

# Image preprocessing settings
PREPROCESS_MAX_DIMENSION = 4096
PREPROCESS_LOW_CONTRAST_STD_DEV_THRESHOLD = 30
PREPROCESS_LINE_THRESHOLD = 30  # Vertical distance for new paragraph

# Enhancement settings
ENHANCE_LARGE_IMAGE_THRESHOLD = 1000
ENHANCE_BILATERAL_FILTER_D = 9
ENHANCE_BILATERAL_FILTER_SIGMA_COLOR = 50
ENHANCE_BILATERAL_FILTER_SIGMA_SPACE = 50
ENHANCE_NL_MEANS_H = 8
ENHANCE_NL_MEANS_TEMPLATE_WINDOW = 7
ENHANCE_NL_MEANS_SEARCH_WINDOW = 21
ENHANCE_CLAHE_CLIP_LIMIT = 2.0
ENHANCE_CLAHE_TILE_GRID_SIZE = (8, 8)

# Deskew settings
DESKEW_CANNY_THRESH1 = 50
DESKEW_CANNY_THRESH2 = 150
DESKEW_CANNY_APERTURE_SIZE = 3
DESKEW_HOUGH_THRESHOLD = 200
DESKEW_ANGLE_THRESHOLD = 0.5  # Degrees

# Table detection
TABLE_COLSPAN_INCREMENT = True  # Use colspan for column index increment

# Confidence thresholds
CONFIDENCE_LOW_THRESHOLD = 0.5  # Warning if average confidence below this

# File retention
FILE_RETENTION_HOURS = 24

# Task timeouts
TASK_TIME_LIMIT_SECONDS = 90  # Increased for HQ mode
TASK_SOFT_TIME_LIMIT_SECONDS = 85
