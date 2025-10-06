"""
Images API endpoints for the Simple Cloud Photo Gallery App.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Image, Category
from pydantic import BaseModel
from datetime import datetime
import json

router = APIRouter(prefix="/api/images", tags=["images"])

class ImageResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    file_extension: str
    user_name: Optional[str]
    user_description: Optional[str]
    user_tags: Optional[List[str]]
    user_category_id: Optional[int]
    ai_name: Optional[str]
    ai_description: Optional[str]
    ai_tags: Optional[List[str]]
    ai_category_id: Optional[int]
    ai_user_suggested_name: Optional[str]
    ai_user_suggested_description: Optional[str]
    ai_user_suggested_tags: Optional[List[str]]
    ai_user_suggested_category_id: Optional[int]
    ai_objects: Optional[List[str]]
    ai_scene_description: Optional[str]
    ai_color_palette: Optional[List[str]]
    ai_emotions: Optional[List[str]]
    ai_confidence_score: Optional[float]
    ai_processing_status: str
    needs_manual_metadata: bool
    is_manually_edited: bool
    last_edited_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

def parse_json_field(json_str: Optional[str]) -> Optional[List[str]]:
    """Parse JSON string field to list."""
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None

@router.get("/", response_model=List[ImageResponse])
async def get_images(
    skip: int = Query(0, ge=0, description="Number of images to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of images to return"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    needs_metadata: Optional[bool] = Query(None, description="Filter by needs manual metadata"),
    db: Session = Depends(get_db)
):
    """
    Get images with optional filtering and pagination.
    """
    query = db.query(Image)
    
    # Apply filters
    if category_id:
        query = query.filter(
            (Image.user_category_id == category_id) |
            (Image.ai_category_id == category_id) |
            (Image.ai_user_suggested_category_id == category_id)
        )
    
    if needs_metadata is not None:
        query = query.filter(Image.needs_manual_metadata == needs_metadata)
    
    # Apply pagination
    images = query.offset(skip).limit(limit).all()
    
    # Convert to response format
    result = []
    for img in images:
        img_dict = img.__dict__.copy()
        # Parse JSON fields
        img_dict['user_tags'] = parse_json_field(img.user_tags)
        img_dict['ai_tags'] = parse_json_field(img.ai_tags)
        img_dict['ai_user_suggested_tags'] = parse_json_field(img.ai_user_suggested_tags)
        img_dict['ai_objects'] = parse_json_field(img.ai_objects)
        img_dict['ai_color_palette'] = parse_json_field(img.ai_color_palette)
        img_dict['ai_emotions'] = parse_json_field(img.ai_emotions)
        result.append(ImageResponse(**img_dict))
    
    return result

@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: int, db: Session = Depends(get_db)):
    """
    Get a specific image by ID.
    """
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Convert to response format
    img_dict = image.__dict__.copy()
    img_dict['user_tags'] = parse_json_field(image.user_tags)
    img_dict['ai_tags'] = parse_json_field(image.ai_tags)
    img_dict['ai_user_suggested_tags'] = parse_json_field(image.ai_user_suggested_tags)
    img_dict['ai_objects'] = parse_json_field(image.ai_objects)
    img_dict['ai_color_palette'] = parse_json_field(image.ai_color_palette)
    img_dict['ai_emotions'] = parse_json_field(image.ai_emotions)
    
    return ImageResponse(**img_dict)

@router.get("/stats/summary")
async def get_image_stats(db: Session = Depends(get_db)):
    """
    Get image statistics.
    """
    total_images = db.query(Image).count()
    needs_metadata_count = db.query(Image).filter(Image.needs_manual_metadata == True).count()
    manually_edited_count = db.query(Image).filter(Image.is_manually_edited == True).count()
    
    # Get total file size
    total_size = db.query(Image.file_size).all()
    total_file_size = sum(size[0] for size in total_size) if total_size else 0
    
    # Get images by category
    from sqlalchemy import func
    category_stats = db.query(
        Category.name,
        func.count(Image.id).label('image_count')
    ).outerjoin(Image, Category.id == Image.user_category_id).group_by(Category.id, Category.name).all()
    
    return {
        "total_images": total_images,
        "needs_manual_metadata": needs_metadata_count,
        "manually_edited": manually_edited_count,
        "total_file_size_bytes": total_file_size,
        "total_file_size_mb": round(total_file_size / (1024 * 1024), 2),
        "category_breakdown": [
            {"category": cat[0], "count": cat[1]}
            for cat in category_stats
        ]
    }
