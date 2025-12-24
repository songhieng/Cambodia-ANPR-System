"""
Unit Tests for Utility Functions

Tests OCR functionality, license plate validation, and character mapping.
"""

import unittest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, '..')

from util import (
    license_complies_format,
    format_license,
    DICT_CHAR_TO_INT,
    DICT_INT_TO_CHAR
)


class TestLicensePlateValidation(unittest.TestCase):
    """Test license plate format validation."""
    
    def test_valid_format(self):
        """Test valid license plate formats."""
        valid_plates = [
            "AB12CDE",
            "XY99ZZZ",
            "PP00QQQ"
        ]
        for plate in valid_plates:
            with self.subTest(plate=plate):
                self.assertTrue(license_complies_format(plate))
    
    def test_invalid_length(self):
        """Test plates with wrong length."""
        invalid_plates = [
            "ABC123",      # Too short
            "AB12CDEF",    # Too long
            "",            # Empty
            "A"            # Single char
        ]
        for plate in invalid_plates:
            with self.subTest(plate=plate):
                self.assertFalse(license_complies_format(plate))
    
    def test_invalid_pattern(self):
        """Test plates with wrong character patterns."""
        invalid_plates = [
            "1234567",     # All numbers
            "ABCDEFG",     # All letters
            "12AB345",     # Wrong position
            "ABCD123"      # Wrong pattern
        ]
        for plate in invalid_plates:
            with self.subTest(plate=plate):
                self.assertFalse(license_complies_format(plate))


class TestLicensePlateFormatting(unittest.TestCase):
    """Test license plate character correction."""
    
    def test_character_correction(self):
        """Test that characters are corrected properly."""
        # O -> 0 in digit positions
        self.assertEqual(format_license("AB0OCDE"), "AB00CDE")
        
        # 0 -> O in letter positions
        self.assertEqual(format_license("0B12CDE"), "OB12CDE")
        
        # Multiple corrections
        self.assertEqual(format_license("0BII3DE"), "OBII3DE")
    
    def test_no_correction_needed(self):
        """Test plates that don't need correction."""
        plate = "AB12CDE"
        self.assertEqual(format_license(plate), plate)


class TestGetCar(unittest.TestCase):
    """Test vehicle-to-plate association."""
    
    def test_plate_inside_vehicle(self):
        """Test when plate is inside vehicle bounds."""
        from util import get_car
        
        # License plate coordinates
        license_plate = [50, 50, 100, 80, 0.95, 0]
        
        # Vehicle tracks (x1, y1, x2, y2, id)
        vehicle_track_ids = [
            [10, 10, 200, 200, 1],  # Vehicle 1 contains the plate
            [300, 300, 400, 400, 2]  # Vehicle 2 doesn't
        ]
        
        result = get_car(license_plate, vehicle_track_ids)
        self.assertEqual(result[4], 1)  # Should match vehicle ID 1
    
    def test_plate_outside_vehicles(self):
        """Test when plate is not inside any vehicle."""
        from util import get_car
        
        license_plate = [500, 500, 550, 530, 0.95, 0]
        vehicle_track_ids = [
            [10, 10, 200, 200, 1],
            [300, 300, 400, 400, 2]
        ]
        
        result = get_car(license_plate, vehicle_track_ids)
        self.assertEqual(result, (-1, -1, -1, -1, -1))


class TestCharacterMappings(unittest.TestCase):
    """Test character mapping dictionaries."""
    
    def test_char_to_int_mapping(self):
        """Test character to integer mapping."""
        self.assertEqual(DICT_CHAR_TO_INT['O'], '0')
        self.assertEqual(DICT_CHAR_TO_INT['I'], '1')
        self.assertEqual(DICT_CHAR_TO_INT['S'], '5')
    
    def test_int_to_char_mapping(self):
        """Test integer to character mapping."""
        self.assertEqual(DICT_INT_TO_CHAR['0'], 'O')
        self.assertEqual(DICT_INT_TO_CHAR['1'], 'I')
        self.assertEqual(DICT_INT_TO_CHAR['5'], 'S')
    
    def test_mapping_symmetry(self):
        """Test that mappings are somewhat symmetric."""
        for char, num in DICT_CHAR_TO_INT.items():
            # The reverse mapping should exist
            self.assertIn(num, DICT_INT_TO_CHAR)


if __name__ == '__main__':
    unittest.main()
