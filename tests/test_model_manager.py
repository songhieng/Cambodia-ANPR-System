"""
Unit Tests for Model Manager

Tests model loading, caching, and validation.
"""

import unittest
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import sys
sys.path.insert(0, '..')

from model_manager import ModelManager, get_model_manager


class TestModelManager(unittest.TestCase):
    """Test ModelManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ModelManager()
        # Clear any cached models
        self.manager._models.clear()
        self.manager._model_info.clear()
    
    def test_singleton_pattern(self):
        """Test that ModelManager is a singleton."""
        manager1 = ModelManager()
        manager2 = ModelManager()
        self.assertIs(manager1, manager2)
    
    def test_get_model_manager(self):
        """Test get_model_manager function."""
        manager = get_model_manager()
        self.assertIsInstance(manager, ModelManager)
    
    def test_validate_model_file_missing(self):
        """Test validation fails for missing file."""
        result = self.manager._validate_model_file('nonexistent_model.pt')
        self.assertFalse(result)
    
    def test_get_loaded_models_empty(self):
        """Test get_loaded_models returns empty list initially."""
        models = self.manager.get_loaded_models()
        self.assertEqual(models, [])
    
    def test_get_model_not_loaded(self):
        """Test get_model returns None for unloaded model."""
        model = self.manager.get_model('nonexistent_key')
        self.assertIsNone(model)
    
    def test_get_model_info_not_loaded(self):
        """Test get_model_info returns None for unloaded model."""
        info = self.manager.get_model_info('nonexistent_key')
        self.assertIsNone(info)
    
    def test_unload_model_not_loaded(self):
        """Test unload_model returns False for unloaded model."""
        result = self.manager.unload_model('nonexistent_key')
        self.assertFalse(result)
    
    @patch('model_manager.YOLO')
    @patch('model_manager.os.path.exists')
    @patch('model_manager.os.access')
    @patch('model_manager.os.path.getsize')
    def test_load_model_success(self, mock_getsize, mock_access, mock_exists, mock_yolo):
        """Test successful model loading."""
        # Mock file system checks
        mock_exists.return_value = True
        mock_access.return_value = True
        mock_getsize.return_value = 1024 * 1024  # 1 MB
        
        # Mock YOLO model
        mock_model = Mock()
        mock_yolo.return_value = mock_model
        
        # Load model
        with patch.object(self.manager, '_get_model_hash', return_value='test_hash'):
            model = self.manager.load_model('test_model', 'test_path.pt')
        
        self.assertIsNotNone(model)
        self.assertEqual(model, mock_model)
        self.assertIn('test_model', self.manager._models)
        self.assertIn('test_model', self.manager._model_info)
    
    @patch('model_manager.YOLO')
    @patch('model_manager.os.path.exists')
    @patch('model_manager.os.access')
    @patch('model_manager.os.path.getsize')
    def test_model_caching(self, mock_getsize, mock_access, mock_exists, mock_yolo):
        """Test that models are cached and reused."""
        # Setup mocks
        mock_exists.return_value = True
        mock_access.return_value = True
        mock_getsize.return_value = 1024 * 1024
        mock_model = Mock()
        mock_yolo.return_value = mock_model
        
        # Load model twice
        with patch.object(self.manager, '_get_model_hash', return_value='test_hash'):
            model1 = self.manager.load_model('test_model', 'test_path.pt')
            model2 = self.manager.load_model('test_model', 'test_path.pt')
        
        # Should be same instance (cached)
        self.assertIs(model1, model2)
        
        # YOLO should only be called once
        mock_yolo.assert_called_once()


if __name__ == '__main__':
    unittest.main()
