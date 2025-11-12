"""
Utility functions for license plate detection and processing.
Includes OCR reading, character mapping, and vehicle tracking utilities.
"""

import string
from typing import Tuple, Optional, Dict, List, Any
import easyocr
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the OCR reader
try:
    reader = easyocr.Reader(['en'], gpu=False)
except Exception as e:
    logger.error(f"Failed to initialize EasyOCR reader: {e}")
    raise

# Mapping dictionaries for character conversion
DICT_CHAR_TO_INT: Dict[str, str] = {
    'O': '0',
    'I': '1',
    'J': '3',
    'A': '4',
    'G': '6',
    'S': '5'
}

DICT_INT_TO_CHAR: Dict[str, str] = {
    '0': 'O',
    '1': 'I',
    '3': 'J',
    '4': 'A',
    '6': 'G',
    '5': 'S'
}


def write_csv(results: Dict[int, Dict[int, Any]], output_path: str) -> None:
    """
    Write the detection results to a CSV file.

    Args:
        results: Dictionary containing the detection results by frame and car ID.
        output_path: Path to the output CSV file.
        
    Raises:
        IOError: If unable to write to the file.
    """
    try:
        with open(output_path, 'w') as f:
            f.write('{},{},{},{},{},{},{}\n'.format(
                'frame_nmr', 'car_id', 'car_bbox',
                'license_plate_bbox', 'license_plate_bbox_score',
                'license_number', 'license_number_score'
            ))

            for frame_nmr in results.keys():
                for car_id in results[frame_nmr].keys():
                    if ('car' in results[frame_nmr][car_id].keys() and
                        'license_plate' in results[frame_nmr][car_id].keys() and
                        'text' in results[frame_nmr][car_id]['license_plate'].keys()):
                        
                        car_bbox = results[frame_nmr][car_id]['car']['bbox']
                        plate_bbox = results[frame_nmr][car_id]['license_plate']['bbox']
                        
                        f.write('{},{},{},{},{},{},{}\n'.format(
                            frame_nmr,
                            car_id,
                            '[{} {} {} {}]'.format(*car_bbox),
                            '[{} {} {} {}]'.format(*plate_bbox),
                            results[frame_nmr][car_id]['license_plate']['bbox_score'],
                            results[frame_nmr][car_id]['license_plate']['text'],
                            results[frame_nmr][car_id]['license_plate']['text_score']
                        ))
    except IOError as e:
        logger.error(f"Failed to write CSV file to {output_path}: {e}")
        raise


def license_complies_format(text: str) -> bool:
    """
    Check if the license plate text complies with the required format.
    Expected format: 2 letters, 2 digits, 3 letters (e.g., AB12CDE).

    Args:
        text: License plate text to validate.

    Returns:
        True if the license plate complies with the format, False otherwise.
    """
    if len(text) != 7:
        return False

    return (
        (text[0] in string.ascii_uppercase or text[0] in DICT_INT_TO_CHAR.keys()) and
        (text[1] in string.ascii_uppercase or text[1] in DICT_INT_TO_CHAR.keys()) and
        (text[2] in '0123456789' or text[2] in DICT_CHAR_TO_INT.keys()) and
        (text[3] in '0123456789' or text[3] in DICT_CHAR_TO_INT.keys()) and
        (text[4] in string.ascii_uppercase or text[4] in DICT_INT_TO_CHAR.keys()) and
        (text[5] in string.ascii_uppercase or text[5] in DICT_INT_TO_CHAR.keys()) and
        (text[6] in string.ascii_uppercase or text[6] in DICT_INT_TO_CHAR.keys())
    )


def format_license(text: str) -> str:
    """
    Format the license plate text by converting characters using mapping dictionaries.

    Args:
        text: License plate text to format.

    Returns:
        Formatted license plate text.
    """
    license_plate = ''
    mapping = {
        0: DICT_INT_TO_CHAR,
        1: DICT_INT_TO_CHAR,
        2: DICT_CHAR_TO_INT,
        3: DICT_CHAR_TO_INT,
        4: DICT_INT_TO_CHAR,
        5: DICT_INT_TO_CHAR,
        6: DICT_INT_TO_CHAR
    }
    
    for j in range(7):
        if text[j] in mapping[j].keys():
            license_plate += mapping[j][text[j]]
        else:
            license_plate += text[j]

    return license_plate


def read_license_plate(license_plate_crop) -> Tuple[Optional[str], Optional[float]]:
    """
    Read the license plate text from the given cropped image using OCR.

    Args:
        license_plate_crop: Cropped image containing the license plate (numpy array).

    Returns:
        Tuple containing the formatted license plate text and its confidence score.
        Returns (None, None) if no valid license plate is detected.
    """
    try:
        detections = reader.readtext(license_plate_crop)

        for detection in detections:
            bbox, text, score = detection
            text = text.upper().replace(' ', '')

            if license_complies_format(text):
                return format_license(text), score

        return None, None
    except Exception as e:
        logger.error(f"Error reading license plate: {e}")
        return None, None


def get_car(license_plate: Tuple, vehicle_track_ids: List) -> Tuple[float, float, float, float, int]:
    """
    Retrieve the vehicle coordinates and ID based on the license plate coordinates.

    Args:
        license_plate: Tuple containing the coordinates of the license plate
                      (x1, y1, x2, y2, score, class_id).
        vehicle_track_ids: List of vehicle track IDs and their corresponding coordinates.

    Returns:
        Tuple containing the vehicle coordinates (x1, y1, x2, y2) and ID.
        Returns (-1, -1, -1, -1, -1) if no matching vehicle is found.
    """
    x1, y1, x2, y2, score, class_id = license_plate

    for j in range(len(vehicle_track_ids)):
        xcar1, ycar1, xcar2, ycar2, car_id = vehicle_track_ids[j]

        if x1 > xcar1 and y1 > ycar1 and x2 < xcar2 and y2 < ycar2:
            return vehicle_track_ids[j]

    return -1, -1, -1, -1, -1
