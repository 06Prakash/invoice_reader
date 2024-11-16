import cv2
import numpy as np
import os


def analyze_image(image_path):
    """
    Analyzes the image to determine the required preprocessing level.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")
    
    analysis = {}

    # Check resolution
    height, width = image.shape
    resolution_threshold = (800, 600)
    analysis['low_resolution'] = height < resolution_threshold[1] or width < resolution_threshold[0]

    # Noise levels (variance of Laplacian)
    laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
    noise_threshold = 100  # Lower values indicate high noise
    analysis['high_noise'] = laplacian_var < noise_threshold

    # Skew detection
    edges = cv2.Canny(image, 50, 150)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)
    if lines is not None:
        angles = [np.degrees(theta) for rho, theta in lines[:, 0]]
        dominant_angle = np.median(angles)
        analysis['skewed'] = abs(dominant_angle - 90) > 5  # Allowable deviation
    else:
        analysis['skewed'] = False

    # Border detection
    try:
        border_pixels = np.concatenate([image[:10, :], image[-10:, :], image[:, :10], image[:, -10:]])
        border_variance = np.var(border_pixels)
        border_threshold = 50
        analysis['has_borders'] = border_variance > border_threshold
    except ValueError:
        # If concatenation fails, default to True as a fallback
        analysis['has_borders'] = True

    # Overall determination
    analysis['preprocessing_level'] = 'deep_cleansing' if (
        analysis['low_resolution'] or analysis['high_noise'] or analysis['skewed'] or analysis['has_borders']
    ) else 'standard'

    return analysis


def preprocess_image(image_path):
    """
    Selects and applies the appropriate preprocessing method based on image analysis.
    Dynamically adjusts preprocessing levels if over-processing is detected.
    """
    analysis = analyze_image(image_path)
    original_path = image_path

    # Initial preprocessing decision
    preprocessing_level = analysis['preprocessing_level']
    print(f"Initial analysis: {analysis}")

    # Apply the decided preprocessing method
    if preprocessing_level == 'deep_cleansing':
        preprocessed_image_path = deep_cleansing_preprocessing(original_path)
    else:
        preprocessed_image_path = standard_preprocessing(original_path)

    # Validate image readability after preprocessing
    if not validate_image_readability(preprocessed_image_path):
        print("Over-processing detected, reverting to standard preprocessing.")
        if preprocessing_level == 'deep_cleansing':
            preprocessed_image_path = standard_preprocessing(original_path)

    return preprocessed_image_path


def validate_image_readability(image_path):
    """
    Validates if the image is over-processed by checking pixel distribution and text clarity.
    """
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return False

    # Analyze pixel intensity histogram
    hist = cv2.calcHist([image], [0], None, [256], [0, 256])
    total_pixels = image.size

    # Check for over-threshold black or white pixels (over or under-processing)
    black_pixels = hist[0][0] / total_pixels
    white_pixels = hist[255][0] / total_pixels

    if black_pixels > 0.9 or white_pixels > 0.9:
        print(f"Over-processing detected: black_pixels={black_pixels}, white_pixels={white_pixels}")
        return False

    return True


def standard_preprocessing(image_path):
    """
    Applies standard preprocessing to the image.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")

    # Resize the image to a standard size
    standard_width = 1024
    aspect_ratio = standard_width / image.shape[1]
    new_dimensions = (standard_width, int(image.shape[0] * aspect_ratio))
    image = cv2.resize(image, new_dimensions, interpolation=cv2.INTER_LINEAR)

    # Apply Gaussian blur to reduce noise
    image = cv2.GaussianBlur(image, (5, 5), 0)

    # Apply adaptive thresholding
    preprocessed_image = cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 10
    )

    # Save the preprocessed image
    preprocessed_image_path = f"preprocessed_standard_{os.path.basename(image_path)}"
    cv2.imwrite(preprocessed_image_path, preprocessed_image)

    return preprocessed_image_path


def deep_cleansing_preprocessing(image_path):
    """
    Applies deep cleansing preprocessing to the image.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")

    # Increase resolution
    scale_percent = 200
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    image = cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)

    # Apply adaptive thresholding
    preprocessed_image = cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Deskew the image
    coords = np.column_stack(np.where(preprocessed_image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle

    # Rotate with borders
    (h, w) = preprocessed_image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    preprocessed_image = cv2.warpAffine(
        preprocessed_image, M, (w, h),
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0
    )

    # Morphological operations to clean up noise
    kernel = np.ones((5, 5), np.uint8)
    preprocessed_image = cv2.morphologyEx(preprocessed_image, cv2.MORPH_CLOSE, kernel)

    # Save the preprocessed image
    preprocessed_image_path = f"preprocessed_deep_{os.path.basename(image_path)}"
    cv2.imwrite(preprocessed_image_path, preprocessed_image)

    return preprocessed_image_path
