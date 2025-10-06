"""
Categories API endpoints for the Simple Cloud Photo Gallery App.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Category
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/categories", tags=["categories"])

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str
    is_ai_generated: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """
    Get all categories.
    """
    categories = db.query(Category).all()
    return categories

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """
    Get a specific category by ID.
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.get("/stats/summary")
async def get_category_stats(db: Session = Depends(get_db)):
    """
    Get category statistics.
    """
    total_categories = db.query(Category).count()
    ai_generated_categories = db.query(Category).filter(Category.is_ai_generated == True).count()
    user_categories = total_categories - ai_generated_categories
    
    # Get top 5 most used categories
    top_categories = db.query(Category).order_by(Category.usage_count.desc()).limit(5).all()
    
    return {
        "total_categories": total_categories,
        "user_categories": user_categories,
        "ai_generated_categories": ai_generated_categories,
        "top_categories": [
            {
                "id": cat.id,
                "name": cat.name,
                "usage_count": cat.usage_count
            }
            for cat in top_categories
        ]
    }
