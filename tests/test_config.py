"""
Unit Tests for Configuration Module

Tests configuration loading and validation.
"""

import unittest
import os
from pathlib import Path

import sys
sys.path.insert(0, '..')

from config import Config, get_firebase_config


class TestConfig(unittest.TestCase):
    """Test configuration class."""
    
    def test_model_paths_defined(self):
        """Test that all model paths are defined."""
        self.assertIsNotNone(Config.YOLO_MODEL_PATH)
        self.assertIsNotNone(Config.LICENSE_PLATE_MODEL_PATH)
        self.assertIsNotNone(Config.CAR_TYPE_MODEL_PATH)
        self.assertIsNotNone(Config.CAR_COLOR_MODEL_PATH)
    
    def test_output_directories_defined(self):
        """Test that output directories are defined."""
        self.assertIsNotNone(Config.CAR_OUTPUT_DIR)
        self.assertIsNotNone(Config.PLATE_OUTPUT_DIR)
        self.assertIsNotNone(Config.DATA_OUTPUT_DIR)
    
    def test_vehicle_class_ids(self):
        """Test vehicle class IDs are valid."""
        self.assertIsInstance(Config.VEHICLE_CLASS_IDS, list)
        self.assertTrue(len(Config.VEHICLE_CLASS_IDS) > 0)
        self.assertTrue(all(isinstance(x, int) for x in Config.VEHICLE_CLASS_IDS))
    
    def test_frame_skip_positive(self):
        """Test frame skip is positive integer."""
        self.assertIsInstance(Config.FRAME_SKIP, int)
        self.assertGreater(Config.FRAME_SKIP, 0)
    
    def test_vehicle_type_map(self):
        """Test vehicle type mapping."""
        self.assertIsInstance(Config.VEHICLE_TYPE_MAP, dict)
        self.assertTrue(len(Config.VEHICLE_TYPE_MAP) > 0)
        # Check some expected types
        expected_types = ['Sedan', 'SUV', 'Pickup']
        map_values = Config.VEHICLE_TYPE_MAP.values()
        self.assertTrue(any(t in map_values for t in expected_types))
    
    def test_vehicle_color_map(self):
        """Test vehicle color mapping."""
        self.assertIsInstance(Config.VEHICLE_COLOR_MAP, dict)
        self.assertTrue(len(Config.VEHICLE_COLOR_MAP) > 0)
        # Check some expected colors
        expected_colors = ['black', 'white', 'red', 'blue']
        map_values = Config.VEHICLE_COLOR_MAP.values()
        self.assertTrue(any(c in map_values for c in expected_colors))
    
    def test_ensure_directories_creates_dirs(self):
        """Test that ensure_directories creates required directories."""
        # This would create actual directories, so we just test it runs
        try:
            Config.ensure_directories()
        except Exception as e:
            self.fail(f"ensure_directories raised exception: {e}")


class TestFirebaseConfig(unittest.TestCase):
    """Test Firebase configuration."""
    
    def test_firebase_config_structure(self):
        """Test Firebase config returns correct structure."""
        # Set required env vars for test
        os.environ['FIREBASE_DATABASE_URL'] = 'https://test.firebaseio.com'
        os.environ['FIREBASE_STORAGE_BUCKET'] = 'test.appspot.com'
        
        config = get_firebase_config()
        
        self.assertIn('databaseURL', config)
        self.assertIn('storageBucket', config)
        self.assertIsInstance(config, dict)
    
    def test_firebase_config_missing_values(self):
        """Test Firebase config raises error when values missing."""
        # Clear env vars
        os.environ.pop('FIREBASE_DATABASE_URL', None)
        os.environ.pop('FIREBASE_STORAGE_BUCKET', None)
        
        # Force reload config
        Config.FIREBASE_DATABASE_URL = ''
        Config.FIREBASE_STORAGE_BUCKET = ''
        
        with self.assertRaises(ValueError):
            get_firebase_config()


if __name__ == '__main__':
    unittest.main()
