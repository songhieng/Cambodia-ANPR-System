"""
Model Management Module

Handles model loading, versioning, and validation following MLOps best practices.
Implements lazy loading and caching for optimal performance.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
import hashlib
from ultralytics import YOLO

from anpr.utils.logger import get_logger
from anpr.utils.config import Config

logger = get_logger(__name__)


class ModelManager:
    """
    Centralized model management with version control and validation.
    Implements singleton pattern for efficient resource usage.
    """
    
    _instance: Optional['ModelManager'] = None
    _models: Dict[str, YOLO] = {}
    _model_info: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize model manager."""
        if not hasattr(self, 'initialized'):
            self.initialized = True
            logger.info("Model Manager initialized")
    
    def _validate_model_file(self, model_path: str) -> bool:
        """
        Validate that model file exists and is readable.
        
        Args:
            model_path: Path to model file.
            
        Returns:
            True if valid, False otherwise.
        """
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return False
        
        if not os.access(model_path, os.R_OK):
            logger.error(f"Model file not readable: {model_path}")
            return False
        
        file_size = os.path.getsize(model_path)
        if file_size == 0:
            logger.error(f"Model file is empty: {model_path}")
            return False
        
        logger.debug(f"Model validation passed: {model_path} ({file_size / 1024 / 1024:.2f} MB)")
        return True
    
    def _get_model_hash(self, model_path: str) -> str:
        """
        Calculate MD5 hash of model file for version tracking.
        
        Args:
            model_path: Path to model file.
            
        Returns:
            MD5 hash string.
        """
        hash_md5 = hashlib.md5()
        with open(model_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def load_model(
        self,
        model_key: str,
        model_path: str,
        force_reload: bool = False
    ) -> Optional[YOLO]:
        """
        Load a YOLO model with caching and validation.
        
        Args:
            model_key: Unique identifier for the model.
            model_path: Path to model file.
            force_reload: Force reload even if cached.
            
        Returns:
            Loaded YOLO model or None if failed.
        """
        # Return cached model if available
        if model_key in self._models and not force_reload:
            logger.debug(f"Using cached model: {model_key}")
            return self._models[model_key]
        
        # Validate model file
        if not self._validate_model_file(model_path):
            return None
        
        try:
            # Load model
            logger.info(f"Loading model: {model_key} from {model_path}")
            model = YOLO(model_path)
            
            # Calculate hash for version tracking
            model_hash = self._get_model_hash(model_path)
            
            # Cache model and metadata
            self._models[model_key] = model
            self._model_info[model_key] = {
                'path': model_path,
                'hash': model_hash,
                'size': os.path.getsize(model_path)
            }
            
            logger.info(f"Model loaded successfully: {model_key} (hash: {model_hash[:8]}...)")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model {model_key}: {e}")
            return None
    
    def get_model(self, model_key: str) -> Optional[YOLO]:
        """
        Retrieve a cached model.
        
        Args:
            model_key: Model identifier.
            
        Returns:
            Cached model or None if not found.
        """
        return self._models.get(model_key)
    
    def get_model_info(self, model_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve model metadata.
        
        Args:
            model_key: Model identifier.
            
        Returns:
            Model metadata dictionary or None if not found.
        """
        return self._model_info.get(model_key)
    
    def preload_all_models(self) -> bool:
        """
        Preload all configured models at startup.
        
        Returns:
            True if all models loaded successfully, False otherwise.
        """
        models_to_load = {
            'vehicle_detector': Config.YOLO_MODEL_PATH,
            'plate_detector': Config.LICENSE_PLATE_MODEL_PATH,
            'type_classifier': Config.CAR_TYPE_MODEL_PATH,
            'color_classifier': Config.CAR_COLOR_MODEL_PATH,
        }
        
        success = True
        for key, path in models_to_load.items():
            if not self.load_model(key, path):
                logger.error(f"Failed to preload model: {key}")
                success = False
        
        return success
    
    def clear_cache(self) -> None:
        """Clear all cached models."""
        self._models.clear()
        self._model_info.clear()
        logger.info("Model cache cleared")
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """
        List all loaded models with metadata.
        
        Returns:
            Dictionary of model information.
        """
        return {
            key: {
                'loaded': True,
                **info
            }
            for key, info in self._model_info.items()
        }
