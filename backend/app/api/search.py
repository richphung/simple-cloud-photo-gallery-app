"""
Search API endpoints for the Simple Cloud Photo Gallery App.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import List, Optional, Dict, Any
from ..database import get_db
from ..models import Image, Category
from pydantic import BaseModel
from datetime import datetime, date
import json

router = APIRouter(prefix="/api/search", tags=["search"])

class SearchRequest(BaseModel):
    query: Optional[str] = None
    categories: Optional[List[int]] = None
    tags: Optional[List[str]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    page: Optional[int] = 1
    limit: Optional[int] = 20
    needs_manual_metadata: Optional[bool] = None

class SearchResponse(BaseModel):
    images: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
    search_filters: Dict[str, Any]

class GalleryResponse(BaseModel):
    images: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
    categories: List[Dict[str, Any]]
    stats: Dict[str, Any]

@router.post("/", response_model=SearchResponse)
async def search_images(
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search images with various filters and sorting options.
    """
    try:
        # Build base query
        query = db.query(Image)
        
        # Apply filters
        filters = []
        
        # Text search across multiple fields
        if search_request.query:
            search_term = f"%{search_request.query}%"
            text_filters = or_(
                Image.user_name.ilike(search_term),
                Image.ai_name.ilike(search_term),
                Image.user_description.ilike(search_term),
                Image.ai_description.ilike(search_term),
                Image.ai_scene_description.ilike(search_term),
                Image.user_tags.ilike(search_term),
                Image.ai_tags.ilike(search_term),
                Image.ai_user_suggested_tags.ilike(search_term)
            )
            filters.append(text_filters)
        
        # Category filter
        if search_request.categories:
            category_filters = or_(
                Image.user_category_id.in_(search_request.categories),
                Image.ai_category_id.in_(search_request.categories),
                Image.ai_user_suggested_category_id.in_(search_request.categories)
            )
            filters.append(category_filters)
        
        # Tag filter
        if search_request.tags:
            tag_filters = []
            for tag in search_request.tags:
                tag_pattern = f"%{tag}%"
                tag_filters.append(
                    or_(
                        Image.user_tags.ilike(tag_pattern),
                        Image.ai_tags.ilike(tag_pattern),
                        Image.ai_user_suggested_tags.ilike(tag_pattern)
                    )
                )
            if tag_filters:
                filters.append(or_(*tag_filters))
        
        # Date range filter
        if search_request.date_from:
            filters.append(Image.created_at >= search_request.date_from)
        if search_request.date_to:
            filters.append(Image.created_at <= search_request.date_to)
        
        # Manual metadata filter
        if search_request.needs_manual_metadata is not None:
            filters.append(Image.needs_manual_metadata == search_request.needs_manual_metadata)
        
        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting
        sort_column = getattr(Image, search_request.sort_by, Image.created_at)
        if search_request.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (search_request.page - 1) * search_request.limit
        query = query.offset(offset).limit(search_request.limit)
        
        # Execute query
        images = query.all()
        
        # Format response
        formatted_images = []
        for image in images:
            # Parse JSON fields
            user_tags = json.loads(image.user_tags) if image.user_tags else []
            ai_tags = json.loads(image.ai_tags) if image.ai_tags else []
            ai_user_suggested_tags = json.loads(image.ai_user_suggested_tags) if image.ai_user_suggested_tags else []
            ai_objects = json.loads(image.ai_objects) if image.ai_objects else []
            ai_color_palette = json.loads(image.ai_color_palette) if image.ai_color_palette else []
            ai_emotions = json.loads(image.ai_emotions) if image.ai_emotions else []
            
            # Get category names
            user_category_name = None
            ai_category_name = None
            ai_user_suggested_category_name = None
            
            if image.user_category_id:
                user_cat = db.query(Category).filter(Category.id == image.user_category_id).first()
                user_category_name = user_cat.name if user_cat else None
            
            if image.ai_category_id:
                ai_cat = db.query(Category).filter(Category.id == image.ai_category_id).first()
                ai_category_name = ai_cat.name if ai_cat else None
            
            if image.ai_user_suggested_category_id:
                ai_suggested_cat = db.query(Category).filter(Category.id == image.ai_user_suggested_category_id).first()
                ai_user_suggested_category_name = ai_suggested_cat.name if ai_suggested_cat else None
            
            formatted_images.append({
                "id": image.id,
                "filename": image.filename,
                "original_filename": image.original_filename,
                "file_path": image.file_path,
                "file_size": image.file_size,
                "mime_type": image.mime_type,
                "file_extension": image.file_extension,
                "user_name": image.user_name,
                "user_description": image.user_description,
                "user_tags": user_tags,
                "user_category_id": image.user_category_id,
                "user_category_name": user_category_name,
                "ai_name": image.ai_name,
                "ai_description": image.ai_description,
                "ai_tags": ai_tags,
                "ai_category_id": image.ai_category_id,
                "ai_category_name": ai_category_name,
                "ai_user_suggested_name": image.ai_user_suggested_name,
                "ai_user_suggested_description": image.ai_user_suggested_description,
                "ai_user_suggested_tags": ai_user_suggested_tags,
                "ai_user_suggested_category_id": image.ai_user_suggested_category_id,
                "ai_user_suggested_category_name": ai_user_suggested_category_name,
                "ai_objects": ai_objects,
                "ai_scene_description": image.ai_scene_description,
                "ai_color_palette": ai_color_palette,
                "ai_emotions": ai_emotions,
                "ai_confidence_score": image.ai_confidence_score,
                "ai_processing_status": image.ai_processing_status,
                "needs_manual_metadata": image.needs_manual_metadata,
                "is_manually_edited": image.is_manually_edited,
                "last_edited_date": image.last_edited_date.isoformat() if image.last_edited_date else None,
                "created_at": image.created_at.isoformat(),
                "updated_at": image.updated_at.isoformat()
            })
        
        # Calculate pagination info
        total_pages = (total_count + search_request.limit - 1) // search_request.limit
        has_next = search_request.page < total_pages
        has_prev = search_request.page > 1
        
        # Prepare search filters for response
        search_filters = {
            "query": search_request.query,
            "categories": search_request.categories,
            "tags": search_request.tags,
            "date_from": search_request.date_from.isoformat() if search_request.date_from else None,
            "date_to": search_request.date_to.isoformat() if search_request.date_to else None,
            "sort_by": search_request.sort_by,
            "sort_order": search_request.sort_order,
            "needs_manual_metadata": search_request.needs_manual_metadata
        }
        
        return SearchResponse(
            images=formatted_images,
            total_count=total_count,
            page=search_request.page,
            limit=search_request.limit,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
            search_filters=search_filters
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/tags")
async def get_available_tags(db: Session = Depends(get_db)):
    """
    Get all available tags from all images.
    """
    try:
        # Get all images with their tags
        images = db.query(Image).all()
        
        all_tags = set()
        for image in images:
            # Add AI tags
            if image.ai_tags:
                try:
                    ai_tags = json.loads(image.ai_tags) if isinstance(image.ai_tags, str) else image.ai_tags
                    if isinstance(ai_tags, list):
                        all_tags.update(ai_tags)
                except:
                    pass
            
            # Add user tags
            if image.user_tags:
                try:
                    user_tags = json.loads(image.user_tags) if isinstance(image.user_tags, str) else image.user_tags
                    if isinstance(user_tags, list):
                        all_tags.update(user_tags)
                except:
                    pass
        
        # Convert to sorted list
        tags_list = sorted(list(all_tags))
        
        return {
            "tags": tags_list,
            "count": len(tags_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tags: {str(e)}")

@router.get("/gallery", response_model=GalleryResponse)
async def get_gallery(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    query: Optional[str] = Query(None),
    category_id: Optional[List[int]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    needs_manual_metadata: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get paginated gallery view with basic filtering.
    """
    try:
        # Build base query
        db_query = db.query(Image)
        
        # Apply text search filter
        if query:
            search_term = f"%{query}%"
            db_query = db_query.filter(
                or_(
                    Image.user_name.ilike(search_term),
                    Image.ai_name.ilike(search_term),
                    Image.user_description.ilike(search_term),
                    Image.ai_description.ilike(search_term),
                    Image.ai_scene_description.ilike(search_term),
                    Image.user_tags.ilike(search_term),
                    Image.ai_tags.ilike(search_term),
                    Image.ai_user_suggested_tags.ilike(search_term)
                )
            )
        
        # Apply filters
        if category_id and len(category_id) > 0:
            # Handle multiple category IDs
            category_conditions = []
            for cat_id in category_id:
                category_conditions.append(
                    or_(
                        Image.user_category_id == cat_id,
                        Image.ai_category_id == cat_id,
                        Image.ai_user_suggested_category_id == cat_id
                    )
                )
            db_query = db_query.filter(or_(*category_conditions))
        
        if needs_manual_metadata is not None:
            db_query = db_query.filter(Image.needs_manual_metadata == needs_manual_metadata)
        
        # Apply tag filter
        if tags and len(tags) > 0:
            tag_filters = []
            for tag in tags:
                tag_pattern = f"%{tag}%"
                tag_filters.append(
                    or_(
                        Image.user_tags.ilike(tag_pattern),
                        Image.ai_tags.ilike(tag_pattern),
                        Image.ai_user_suggested_tags.ilike(tag_pattern)
                    )
                )
            if tag_filters:
                db_query = db_query.filter(or_(*tag_filters))
        
        # Get total count
        total_count = db_query.count()
        
        # Apply sorting
        sort_column = getattr(Image, sort_by, Image.created_at)
        if sort_order == "desc":
            db_query = db_query.order_by(desc(sort_column))
        else:
            db_query = db_query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (page - 1) * limit
        db_query = db_query.offset(offset).limit(limit)
        
        # Execute query
        images = db_query.all()
        
        # Format images (same as search)
        formatted_images = []
        for image in images:
            # Parse JSON fields
            user_tags = json.loads(image.user_tags) if image.user_tags else []
            ai_tags = json.loads(image.ai_tags) if image.ai_tags else []
            ai_user_suggested_tags = json.loads(image.ai_user_suggested_tags) if image.ai_user_suggested_tags else []
            ai_objects = json.loads(image.ai_objects) if image.ai_objects else []
            ai_color_palette = json.loads(image.ai_color_palette) if image.ai_color_palette else []
            ai_emotions = json.loads(image.ai_emotions) if image.ai_emotions else []
            
            # Get category names
            user_category_name = None
            ai_category_name = None
            ai_user_suggested_category_name = None
            
            if image.user_category_id:
                user_cat = db.query(Category).filter(Category.id == image.user_category_id).first()
                user_category_name = user_cat.name if user_cat else None
            
            if image.ai_category_id:
                ai_cat = db.query(Category).filter(Category.id == image.ai_category_id).first()
                ai_category_name = ai_cat.name if ai_cat else None
            
            if image.ai_user_suggested_category_id:
                ai_suggested_cat = db.query(Category).filter(Category.id == image.ai_user_suggested_category_id).first()
                ai_user_suggested_category_name = ai_suggested_cat.name if ai_suggested_cat else None
            
            formatted_images.append({
                "id": image.id,
                "filename": image.filename,
                "original_filename": image.original_filename,
                "file_path": image.file_path,
                "file_size": image.file_size,
                "mime_type": image.mime_type,
                "file_extension": image.file_extension,
                "user_name": image.user_name,
                "user_description": image.user_description,
                "user_tags": user_tags,
                "user_category_id": image.user_category_id,
                "user_category_name": user_category_name,
                "ai_name": image.ai_name,
                "ai_description": image.ai_description,
                "ai_tags": ai_tags,
                "ai_category_id": image.ai_category_id,
                "ai_category_name": ai_category_name,
                "ai_user_suggested_name": image.ai_user_suggested_name,
                "ai_user_suggested_description": image.ai_user_suggested_description,
                "ai_user_suggested_tags": ai_user_suggested_tags,
                "ai_user_suggested_category_id": image.ai_user_suggested_category_id,
                "ai_user_suggested_category_name": ai_user_suggested_category_name,
                "ai_objects": ai_objects,
                "ai_scene_description": image.ai_scene_description,
                "ai_color_palette": ai_color_palette,
                "ai_emotions": ai_emotions,
                "ai_confidence_score": image.ai_confidence_score,
                "ai_processing_status": image.ai_processing_status,
                "needs_manual_metadata": image.needs_manual_metadata,
                "is_manually_edited": image.is_manually_edited,
                "last_edited_date": image.last_edited_date.isoformat() if image.last_edited_date else None,
                "created_at": image.created_at.isoformat(),
                "updated_at": image.updated_at.isoformat()
            })
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        # Get categories for filter dropdown with actual usage counts
        categories = db.query(Category).order_by(Category.name).all()
        categories_data = []
        for cat in categories:
            # Calculate actual usage count by counting unique images in this category
            # Use a subquery to get distinct image IDs first, then count them
            subquery = db.query(Image.id).filter(
                or_(
                    Image.user_category_id == cat.id,
                    Image.ai_category_id == cat.id,
                    Image.ai_user_suggested_category_id == cat.id
                )
            ).distinct().subquery()
            
            actual_usage_count = db.query(subquery).count()
            
            categories_data.append({
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "is_ai_generated": cat.is_ai_generated,
                "usage_count": actual_usage_count
            })
        
        # Get gallery statistics
        stats = {
            "total_images": db.query(Image).count(),
            "needs_manual_metadata": db.query(Image).filter(Image.needs_manual_metadata == True).count(),
            "manually_edited": db.query(Image).filter(Image.is_manually_edited == True).count(),
            "total_categories": len(categories_data),
            "ai_generated_categories": len([c for c in categories_data if c["is_ai_generated"]]),
            "user_categories": len([c for c in categories_data if not c["is_ai_generated"]])
        }
        
        return GalleryResponse(
            images=formatted_images,
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
            categories=categories_data,
            stats=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gallery request failed: {str(e)}")

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get search suggestions based on existing data.
    """
    try:
        suggestions = set()
        search_term = f"%{q}%"
        
        # Get suggestions from image names
        names = db.query(Image.user_name, Image.ai_name).filter(
            or_(
                Image.user_name.ilike(search_term),
                Image.ai_name.ilike(search_term)
            )
        ).limit(limit).all()
        
        for user_name, ai_name in names:
            if user_name:
                suggestions.add(user_name)
            if ai_name:
                suggestions.add(ai_name)
        
        # Get suggestions from categories
        categories = db.query(Category.name).filter(
            Category.name.ilike(search_term)
        ).limit(limit).all()
        
        for (name,) in categories:
            suggestions.add(name)
        
        # Get suggestions from tags
        tag_images = db.query(Image.user_tags, Image.ai_tags, Image.ai_user_suggested_tags).filter(
            or_(
                Image.user_tags.ilike(search_term),
                Image.ai_tags.ilike(search_term),
                Image.ai_user_suggested_tags.ilike(search_term)
            )
        ).limit(limit).all()
        
        for user_tags, ai_tags, ai_user_suggested_tags in tag_images:
            for tag_list in [user_tags, ai_tags, ai_user_suggested_tags]:
                if tag_list:
                    try:
                        tags = json.loads(tag_list)
                        for tag in tags:
                            if q.lower() in tag.lower():
                                suggestions.add(tag)
                    except json.JSONDecodeError:
                        continue
        
        # Convert to list and sort
        suggestions_list = sorted(list(suggestions))[:limit]
        
        return {
            "suggestions": suggestions_list,
            "query": q,
            "count": len(suggestions_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestions request failed: {str(e)}")

@router.get("/stats")
async def get_search_stats(db: Session = Depends(get_db)):
    """
    Get search-related statistics.
    """
    try:
        # Basic counts
        total_images = db.query(Image).count()
        images_with_ai_data = db.query(Image).filter(Image.ai_name.isnot(None)).count()
        images_needing_metadata = db.query(Image).filter(Image.needs_manual_metadata == True).count()
        
        # Category distribution
        category_stats = db.query(
            Category.name,
            func.count(Image.id).label('count')
        ).outerjoin(Image, or_(
            Image.user_category_id == Category.id,
            Image.ai_category_id == Category.id,
            Image.ai_user_suggested_category_id == Category.id
        )).group_by(Category.id, Category.name).order_by(desc('count')).all()
        
        # Tag frequency (simplified)
        all_tags = []
        tag_images = db.query(Image.user_tags, Image.ai_tags, Image.ai_user_suggested_tags).all()
        
        for user_tags, ai_tags, ai_user_suggested_tags in tag_images:
            for tag_list in [user_tags, ai_tags, ai_user_suggested_tags]:
                if tag_list:
                    try:
                        tags = json.loads(tag_list)
                        all_tags.extend(tags)
                    except json.JSONDecodeError:
                        continue
        
        # Count tag frequency
        from collections import Counter
        tag_counts = Counter(all_tags)
        top_tags = tag_counts.most_common(10)
        
        return {
            "total_images": total_images,
            "images_with_ai_data": images_with_ai_data,
            "images_needing_metadata": images_needing_metadata,
            "ai_coverage_percentage": round((images_with_ai_data / total_images * 100) if total_images > 0 else 0, 2),
            "category_distribution": [
                {"name": name, "count": count} for name, count in category_stats
            ],
            "top_tags": [
                {"tag": tag, "count": count} for tag, count in top_tags
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats request failed: {str(e)}")
