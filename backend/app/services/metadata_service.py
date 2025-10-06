"""
Metadata service for handling image metadata extraction and processing.
"""

import json
from typing import Optional, Dict, Any, List
from PIL import Image as PILImage
from PIL.ExifTags import TAGS
import os

class MetadataService:
    """
    Service for extracting and processing image metadata.
    """
    
    def __init__(self):
        pass
    
    def extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract basic metadata from an image file.
        """
        metadata = {
            "width": None,
            "height": None,
            "format": None,
            "mode": None,
            "exif_data": {},
            "has_exif": False
        }
        
        try:
            with PILImage.open(file_path) as img:
                metadata["width"] = img.width
                metadata["height"] = img.height
                metadata["format"] = img.format
                metadata["mode"] = img.mode
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    exif_data = img._getexif()
                    metadata["has_exif"] = True
                    
                    # Convert EXIF data to readable format
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        metadata["exif_data"][tag] = str(value)
                
        except Exception as e:
            # If metadata extraction fails, return basic info
            metadata["error"] = str(e)
        
        return metadata
    
    def extract_color_palette(self, file_path: str, max_colors: int = 5) -> List[str]:
        """
        Extract dominant colors from an image.
        """
        try:
            with PILImage.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize image for faster processing
                img.thumbnail((150, 150))
                
                # Get colors
                colors = img.getcolors(maxcolors=256*256*256)
                if not colors:
                    return []
                
                # Sort by frequency and get top colors
                colors.sort(key=lambda x: x[0], reverse=True)
                top_colors = colors[:max_colors]
                
                # Convert to hex
                hex_colors = []
                for count, (r, g, b) in top_colors:
                    hex_color = f"#{r:02x}{g:02x}{b:02x}".upper()
                    hex_colors.append(hex_color)
                
                return hex_colors
                
        except Exception as e:
            return []
    
    def extract_image_properties(self, file_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive image properties.
        """
        properties = {
            "file_size": 0,
            "dimensions": {"width": 0, "height": 0},
            "format": None,
            "mode": None,
            "color_palette": [],
            "aspect_ratio": 0.0,
            "orientation": "unknown"
        }
        
        try:
            # Get file size
            properties["file_size"] = os.path.getsize(file_path)
            
            # Get image properties
            with PILImage.open(file_path) as img:
                properties["dimensions"]["width"] = img.width
                properties["dimensions"]["height"] = img.height
                properties["format"] = img.format
                properties["mode"] = img.mode
                
                # Calculate aspect ratio
                if img.height > 0:
                    properties["aspect_ratio"] = round(img.width / img.height, 2)
                
                # Determine orientation
                if img.width > img.height:
                    properties["orientation"] = "landscape"
                elif img.height > img.width:
                    properties["orientation"] = "portrait"
                else:
                    properties["orientation"] = "square"
                
                # Extract color palette
                properties["color_palette"] = self.extract_color_palette(file_path)
                
        except Exception as e:
            properties["error"] = str(e)
        
        return properties
    
    def parse_user_tags(self, tags_string: Optional[str]) -> List[str]:
        """
        Parse user-provided tags string into a list.
        """
        if not tags_string:
            return []
        
        try:
            # Try to parse as JSON first
            if tags_string.startswith('[') and tags_string.endswith(']'):
                return json.loads(tags_string)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Parse as comma-separated string
        tags = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
        return tags
    
    def format_tags_for_storage(self, tags: List[str]) -> str:
        """
        Format tags list for database storage.
        """
        if not tags:
            return None
        
        return json.dumps(tags)
    
    def validate_category_id(self, category_id: Optional[int], db) -> bool:
        """
        Validate that a category ID exists in the database.
        """
        if category_id is None:
            return True
        
        from ..models import Category
        category = db.query(Category).filter(Category.id == category_id).first()
        return category is not None
    
    def create_metadata_summary(self, image_data: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of image metadata.
        """
        summary_parts = []
        
        # Basic info
        if image_data.get("width") and image_data.get("height"):
            summary_parts.append(f"{image_data['width']}x{image_data['height']}")
        
        if image_data.get("format"):
            summary_parts.append(f"{image_data['format']} format")
        
        if image_data.get("file_size"):
            size_mb = image_data["file_size"] / (1024 * 1024)
            summary_parts.append(f"{size_mb:.1f}MB")
        
        # Orientation
        if image_data.get("orientation"):
            summary_parts.append(image_data["orientation"])
        
        return ", ".join(summary_parts) if summary_parts else "Image uploaded"



