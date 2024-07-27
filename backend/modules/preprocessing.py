import cv2
import numpy as np
import os

def preprocess_image(image_path):
    # Check if the image file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # Check if the image was loaded successfully
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")

    # Increase resolution
    scale_percent = 200  # percent of original size
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    image = cv2.resize(image, dim, interpolation=cv2.INTER_LINEAR)

    # Apply adaptive thresholding
    preprocessed_image = cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    # Deskew the image
    coords = np.column_stack(np.where(preprocessed_image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = preprocessed_image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    preprocessed_image = cv2.warpAffine(preprocessed_image, M, (w, h),
                                        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # I added these gaussian blurs to remove noises and remove dots
    # Adjusting these values to see if they improve clarity
    preprocessed_image = cv2.GaussianBlur(preprocessed_image, (1, 1), 0)
    preprocessed_image = cv2.medianBlur(preprocessed_image, 1)

    # Remove borders and lines
    kernel = np.ones((5, 5), np.uint8)
    preprocessed_image = cv2.morphologyEx(preprocessed_image, cv2.MORPH_CLOSE, kernel)
    preprocessed_image = cv2.erode(preprocessed_image, kernel, iterations=1)
    preprocessed_image = cv2.dilate(preprocessed_image, kernel, iterations=1)

    # Save the preprocessed image
    preprocessed_image_path = f"preprocessed_{image_path}"
    cv2.imwrite(preprocessed_image_path, preprocessed_image)

    return preprocessed_image_path
