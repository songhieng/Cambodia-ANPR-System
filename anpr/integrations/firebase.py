"""
Firebase Integration Module

Manages Firebase connections, storage uploads, and database operations.
Implements singleton pattern for Firebase app initialization.
"""

import os
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, db, storage

from anpr.utils.logger import get_logger

logger = get_logger(__name__)


class FirebaseManager:
    """Manages Firebase connections and operations."""
    
    _instance: Optional['FirebaseManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase Manager (singleton pattern)."""
        if not self._initialized:
            self._initialized = True
            self.app = None
            self.ref = None
    
    def initialize(
        self,
        credentials_path: str,
        database_url: str,
        storage_bucket: str
    ) -> None:
        """
        Initialize Firebase with the provided credentials.
        
        Args:
            credentials_path: Path to Firebase credentials JSON file.
            database_url: Firebase Realtime Database URL.
            storage_bucket: Firebase Storage bucket name.
            
        Raises:
            FileNotFoundError: If credentials file doesn't exist.
        """
        if self.app is not None:
            logger.warning("Firebase already initialized")
            return
        
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Firebase credentials file not found: {credentials_path}"
            )
        
        try:
            cred = credentials.Certificate(credentials_path)
            self.app = firebase_admin.initialize_app(cred, {
                'databaseURL': database_url,
                'storageBucket': storage_bucket
            })
            self.ref = db.reference('/')
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def upload_to_storage(
        self,
        filename: str,
        destination_blob_name: str
    ) -> str:
        """
        Upload a file to Firebase Cloud Storage.
        
        Args:
            filename: Path to the file to upload.
            destination_blob_name: Storage object name.
            
        Returns:
            Public URL of the uploaded file.
            
        Raises:
            RuntimeError: If Firebase is not initialized.
            IOError: If file upload fails.
        """
        if self.app is None:
            raise RuntimeError("Firebase not initialized. Call initialize() first.")
        
        try:
            bucket = storage.bucket()
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(filename)
            
            logger.info(f"File {filename} uploaded to {destination_blob_name}")
            return blob.public_url
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {e}")
            raise IOError(f"File upload failed: {e}")
    
    def push_data(self, path: str, data: Dict[str, Any]) -> Any:
        """
        Push data to Firebase Realtime Database.
        
        Args:
            path: Database path where data should be pushed.
            data: Dictionary containing the data to push.
            
        Returns:
            Reference to the newly created data.
            
        Raises:
            RuntimeError: If Firebase is not initialized.
        """
        if self.ref is None:
            raise RuntimeError("Firebase not initialized. Call initialize() first.")
        
        try:
            child_ref = self.ref.child(path)
            new_ref = child_ref.push(data)
            logger.info(f"Data pushed to {path}")
            return new_ref
        except Exception as e:
            logger.error(f"Failed to push data to {path}: {e}")
            raise
    
    def set_data(self, path: str, data: Any) -> None:
        """
        Set data at a specific path in Firebase Realtime Database.
        
        Args:
            path: Database path where data should be set.
            data: Data to set at the path.
            
        Raises:
            RuntimeError: If Firebase is not initialized.
        """
        if self.ref is None:
            raise RuntimeError("Firebase not initialized. Call initialize() first.")
        
        try:
            child_ref = self.ref.child(path)
            child_ref.set(data)
            logger.info(f"Data set at {path}")
        except Exception as e:
            logger.error(f"Failed to set data at {path}: {e}")
            raise
    
    def get_data(self, path: str) -> Any:
        """
        Get data from a specific path in Firebase Realtime Database.
        
        Args:
            path: Database path to retrieve data from.
            
        Returns:
            Data at the specified path.
            
        Raises:
            RuntimeError: If Firebase is not initialized.
        """
        if self.ref is None:
            raise RuntimeError("Firebase not initialized. Call initialize() first.")
        
        try:
            child_ref = self.ref.child(path)
            data = child_ref.get()
            logger.info(f"Data retrieved from {path}")
            return data
        except Exception as e:
            logger.error(f"Failed to get data from {path}: {e}")
            raise


def get_firebase_manager() -> FirebaseManager:
    """
    Get the Firebase Manager singleton instance.
    
    Returns:
        FirebaseManager instance.
    """
    return FirebaseManager()
