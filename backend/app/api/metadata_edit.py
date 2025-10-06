"""
Manual Metadata Editing API endpoints for the Simple Cloud Photo Gallery App.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from ..database import get_db
from ..models import Image, Category
from pydantic import BaseModel
from datetime import datetime
import json

router = APIRouter(prefix="/api/metadata", tags=["metadata-edit"])

class MetadataUpdateRequest(BaseModel):
    user_name: Optional[str] = None
    user_description: Optional[str] = None
    user_tags: Optional[List[str]] = None
    user_category_id: Optional[int] = None

class BulkMetadataUpdateRequest(BaseModel):
    image_ids: List[int]
    updates: MetadataUpdateRequest

class MetadataUpdateResponse(BaseModel):
    success: bool
    message: str
    image_id: int
    updated_fields: List[str]
    error: Optional[str] = None

class BulkMetadataUpdateResponse(BaseModel):
    total_images: int
    successful_updates: int
    failed_updates: int
    results: List[MetadataUpdateResponse]

class EditHistoryResponse(BaseModel):
    image_id: int
    field_name: str
    old_value: str
    new_value: str
    edited_at: datetime
    edited_by: str = "user"  # For now, always "user"

@router.put("/{image_id}", response_model=MetadataUpdateResponse)
async def update_image_metadata(
    image_id: int,
    update_request: MetadataUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update metadata for a specific image.
    """
    try:
        # Get the image
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")

        updated_fields = []
        
        # Update user-provided fields
        if update_request.user_name is not None:
            image.user_name = update_request.user_name
            updated_fields.append("user_name")
        
        if update_request.user_description is not None:
            image.user_description = update_request.user_description
            updated_fields.append("user_description")
        
        if update_request.user_tags is not None:
            image.user_tags = json.dumps(update_request.user_tags) if update_request.user_tags else None
            updated_fields.append("user_tags")
        
        if update_request.user_category_id is not None:
            # Validate category exists
            if update_request.user_category_id != 0:  # 0 means no category
                category = db.query(Category).filter(Category.id == update_request.user_category_id).first()
                if not category:
                    raise HTTPException(status_code=400, detail="Category not found")
                image.user_category_id = update_request.user_category_id
            else:
                image.user_category_id = None
            updated_fields.append("user_category_id")
        
        # Mark as manually edited and no longer needing manual metadata
        if updated_fields:
            image.is_manually_edited = True
            image.needs_manual_metadata = False
            image.last_edited_date = datetime.now()
            image.updated_at = datetime.now()
            updated_fields.extend(["is_manually_edited", "needs_manual_metadata", "last_edited_date"])
        
        # Update category usage count if category changed
        if "user_category_id" in updated_fields and image.user_category_id:
            category = db.query(Category).filter(Category.id == image.user_category_id).first()
            if category:
                category.usage_count += 1
        
        db.commit()
        db.refresh(image)
        
        return MetadataUpdateResponse(
            success=True,
            message=f"Metadata updated successfully for image {image_id}",
            image_id=image_id,
            updated_fields=updated_fields
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return MetadataUpdateResponse(
            success=False,
            message=f"Failed to update metadata for image {image_id}",
            image_id=image_id,
            updated_fields=[],
            error=str(e)
        )

@router.put("/bulk", response_model=BulkMetadataUpdateResponse)
async def bulk_update_metadata(
    bulk_request: BulkMetadataUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update metadata for multiple images at once.
    """
    results = []
    successful_updates = 0
    failed_updates = 0
    
    for image_id in bulk_request.image_ids:
        try:
            # Create individual update request
            individual_request = MetadataUpdateRequest(
                user_name=bulk_request.updates.user_name,
                user_description=bulk_request.updates.user_description,
                user_tags=bulk_request.updates.user_tags,
                user_category_id=bulk_request.updates.user_category_id
            )
            
            # Update the image
            result = await update_image_metadata(image_id, individual_request, db)
            results.append(result)
            
            if result.success:
                successful_updates += 1
            else:
                failed_updates += 1
                
        except Exception as e:
            results.append(MetadataUpdateResponse(
                success=False,
                message=f"Failed to update image {image_id}",
                image_id=image_id,
                updated_fields=[],
                error=str(e)
            ))
            failed_updates += 1
    
    return BulkMetadataUpdateResponse(
        total_images=len(bulk_request.image_ids),
        successful_updates=successful_updates,
        failed_updates=failed_updates,
        results=results
    )

@router.get("/{image_id}/history", response_model=List[EditHistoryResponse])
async def get_edit_history(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Get edit history for a specific image.
    Note: This is a simplified version. In a real application, you'd have a separate edit_history table.
    """
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # For now, return basic edit information
        history = []
        
        if image.is_manually_edited and image.last_edited_date:
            history.append(EditHistoryResponse(
                image_id=image_id,
                field_name="metadata",
                old_value="AI-generated or empty",
                new_value="User-edited",
                edited_at=image.last_edited_date,
                edited_by="user"
            ))
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get edit history: {str(e)}")

@router.post("/{image_id}/reanalyze")
async def trigger_reanalysis(
    image_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger AI re-analysis for an image.
    """
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Reset AI processing status to pending
        image.ai_processing_status = 'pending'
        image.needs_manual_metadata = False
        image.updated_at = datetime.now()
        
        db.commit()
        
        # Import here to avoid circular imports
        from ..services.ai_processor import process_image_metadata
        
        # Trigger AI analysis in background
        background_tasks.add_task(process_image_metadata, image.id, image.file_path, db)
        
        return {
            "success": True,
            "message": f"Re-analysis triggered for image {image_id}",
            "image_id": image_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to trigger re-analysis: {str(e)}")

@router.get("/{image_id}/suggestions")
async def get_metadata_suggestions(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Get metadata suggestions for an image based on similar images.
    """
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        suggestions = {
            "category_suggestions": [],
            "tag_suggestions": [],
            "name_suggestions": []
        }
        
        # Get category suggestions based on AI category
        if image.ai_category_id:
            ai_category = db.query(Category).filter(Category.id == image.ai_category_id).first()
            if ai_category:
                suggestions["category_suggestions"].append({
                    "id": ai_category.id,
                    "name": ai_category.name,
                    "confidence": "high",
                    "source": "ai_analysis"
                })
        
        # Get similar images for tag suggestions
        similar_images = db.query(Image).filter(
            Image.id != image_id,
            Image.ai_category_id == image.ai_category_id
        ).limit(5).all()
        
        # Collect tags from similar images
        all_tags = []
        for similar_image in similar_images:
            if similar_image.ai_tags:
                try:
                    tags = json.loads(similar_image.ai_tags)
                    all_tags.extend(tags)
                except json.JSONDecodeError:
                    continue
        
        # Get most common tags
        from collections import Counter
        tag_counts = Counter(all_tags)
        suggestions["tag_suggestions"] = [
            {"tag": tag, "count": count} 
            for tag, count in tag_counts.most_common(10)
        ]
        
        # Get name suggestions based on AI name
        if image.ai_name:
            suggestions["name_suggestions"].append({
                "name": image.ai_name,
                "confidence": "high",
                "source": "ai_analysis"
            })
        
        if image.ai_user_suggested_name:
            suggestions["name_suggestions"].append({
                "name": image.ai_user_suggested_name,
                "confidence": "medium",
                "source": "ai_suggestion"
            })
        
        return suggestions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

@router.get("/needs-metadata")
async def get_images_needing_metadata(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get images that need manual metadata editing.
    """
    try:
        # Get images that need manual metadata
        query = db.query(Image).filter(Image.needs_manual_metadata == True)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        images = query.offset(offset).limit(limit).all()
        
        # Format response
        formatted_images = []
        for image in images:
            # Get category names
            user_category_name = None
            ai_category_name = None
            
            if image.user_category_id:
                user_cat = db.query(Category).filter(Category.id == image.user_category_id).first()
                user_category_name = user_cat.name if user_cat else None
            
            if image.ai_category_id:
                ai_cat = db.query(Category).filter(Category.id == image.ai_category_id).first()
                ai_category_name = ai_cat.name if ai_cat else None
            
            formatted_images.append({
                "id": image.id,
                "filename": image.filename,
                "original_filename": image.original_filename,
                "file_path": image.file_path,
                "user_name": image.user_name,
                "user_description": image.user_description,
                "user_tags": json.loads(image.user_tags) if image.user_tags else [],
                "user_category_id": image.user_category_id,
                "user_category_name": user_category_name,
                "ai_name": image.ai_name,
                "ai_description": image.ai_description,
                "ai_tags": json.loads(image.ai_tags) if image.ai_tags else [],
                "ai_category_id": image.ai_category_id,
                "ai_category_name": ai_category_name,
                "ai_confidence_score": image.ai_confidence_score,
                "created_at": image.created_at.isoformat(),
                "updated_at": image.updated_at.isoformat()
            })
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "images": formatted_images,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get images needing metadata: {str(e)}")

@router.delete("/{image_id}")
async def reset_image_metadata(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Reset image metadata to AI-generated values (remove user edits).
    """
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Reset user-provided fields to None
        image.user_name = None
        image.user_description = None
        image.user_tags = None
        image.user_category_id = None
        
        # Reset manual edit flags
        image.is_manually_edited = False
        image.last_edited_date = None
        
        # Mark as needing manual metadata if no AI data exists
        if not image.ai_name and not image.ai_description:
            image.needs_manual_metadata = True
        
        image.updated_at = datetime.now()
        
        db.commit()
        db.refresh(image)
        
        return {
            "success": True,
            "message": f"Metadata reset for image {image_id}",
            "image_id": image_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset metadata: {str(e)}")


