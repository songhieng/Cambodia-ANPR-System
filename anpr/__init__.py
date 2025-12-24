"""
Cambodia ANPR System

A production-ready Automatic Number Plate Recognition system using YOLOv8 and EasyOCR.
"""

__version__ = "2.0.0"
__author__ = "Cambodia ANPR Team"

from anpr.core.detector import ANPRDetector
from anpr.models.manager import ModelManager
from anpr.utils.config import Config

__all__ = ["ANPRDetector", "ModelManager", "Config"]
