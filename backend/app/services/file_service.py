"""
File service for handling file operations in the Simple Cloud Photo Gallery App.
"""

import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import UploadFile
import mimetypes

class FileService:
    """
    Service for handling file operations including validation, storage, and management.
    """
    
    # Configuration
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'image/bmp', 'image/webp', 'image/tiff', 'image/tif'
    }
    
    def __init__(self, base_upload_dir: str = "uploads"):
        self.base_upload_dir = base_upload_dir
        self.ensure_base_directory()
    
    def ensure_base_directory(self):
        """Ensure the base upload directory exists."""
        os.makedirs(self.base_upload_dir, exist_ok=True)
    
    def is_valid_image(self, file: UploadFile) -> bool:
        """
        Validate if the uploaded file is a valid image.
        """
        if not file.filename:
            return False
        
        # Check file extension
        file_extension = self.get_file_extension(file.filename)
        if file_extension not in self.ALLOWED_EXTENSIONS:
            return False
        
        # Check MIME type
        if file.content_type and file.content_type not in self.ALLOWED_MIME_TYPES:
            return False
        
        return True
    
    def is_valid_size(self, file: UploadFile) -> bool:
        """
        Validate if the file size is within limits.
        """
        if hasattr(file, 'size') and file.size:
            return file.size <= self.MAX_FILE_SIZE
        
        # If size is not available, we'll check after reading
        return True
    
    def get_file_extension(self, filename: str) -> str:
        """
        Get file extension from filename.
        """
        if not filename:
            return ""
        
        _, ext = os.path.splitext(filename.lower())
        return ext
    
    def generate_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename using the naming convention:
        YYYYMMDD_HHMMSS_original_name.ext
        """
        if not original_filename:
            original_filename = "unknown"
        
        # Get current timestamp
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        # Get file extension
        file_extension = self.get_file_extension(original_filename)
        
        # Clean original filename (remove extension and sanitize)
        name_without_ext = os.path.splitext(original_filename)[0]
        # Replace spaces and special characters with underscores
        clean_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in name_without_ext)
        # Limit length
        clean_name = clean_name[:50]
        
        # Generate unique filename
        unique_filename = f"{timestamp}_{clean_name}{file_extension}"
        
        return unique_filename
    
    def create_directory_structure(self, filename: str) -> str:
        """
        Create directory structure based on current date: uploads/YYYY/MM/DD/
        """
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        
        # Create directory path
        dir_path = os.path.join(self.base_upload_dir, year, month, day)
        os.makedirs(dir_path, exist_ok=True)
        
        # Return full file path with forward slashes for web URLs
        full_path = os.path.join(dir_path, filename)
        return full_path.replace('\\', '/')
    
    async def save_file(self, file: UploadFile, file_path: str) -> str:
        """
        Save uploaded file to the specified path.
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Read file content
            content = await file.read()
            
            # Check file size if not already checked
            if len(content) > self.MAX_FILE_SIZE:
                raise ValueError(f"File size {len(content)} exceeds maximum allowed size {self.MAX_FILE_SIZE}")
            
            # Write file
            with open(file_path, "wb") as f:
                f.write(content)
            
            return file_path
            
        except Exception as e:
            # Clean up if file was partially written
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
    
    def get_file_size(self, file_path: str) -> int:
        """
        Get file size in bytes.
        """
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    def detect_mime_type(self, file_path: str) -> str:
        """
        Detect MIME type of a file.
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from the filesystem.
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except OSError:
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.
        """
        return os.path.exists(file_path)
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Get file information including size, MIME type, etc.
        """
        if not self.file_exists(file_path):
            return {}
        
        return {
            "path": file_path,
            "size": self.get_file_size(file_path),
            "mime_type": self.detect_mime_type(file_path),
            "extension": self.get_file_extension(file_path),
            "exists": True
        }
    
    def cleanup_empty_directories(self, base_path: str = None):
        """
        Clean up empty directories in the upload folder.
        """
        if base_path is None:
            base_path = self.base_upload_dir
        
        try:
            # Walk through directories bottom-up
            for root, dirs, files in os.walk(base_path, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        # Try to remove empty directory
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                    except OSError:
                        # Directory not empty or permission error
                        pass
        except OSError:
            pass
