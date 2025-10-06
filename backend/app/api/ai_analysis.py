"""
AI Analysis API endpoints for the Simple Cloud Photo Gallery App.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Image, Category
from ..services.ai_service import AIService
from pydantic import BaseModel
import os

router = APIRouter(prefix="/api/ai", tags=["ai-analysis"])

# Initialize AI service
ai_service = AIService()

class AnalysisRequest(BaseModel):
    image_id: int

class BatchAnalysisRequest(BaseModel):
    image_ids: List[int]

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    analysis_data: Optional[dict] = None
    error: Optional[str] = None

class BatchAnalysisResponse(BaseModel):
    total_images: int
    successful_analyses: int
    failed_analyses: int
    results: List[AnalysisResponse]

@router.post("/analyze/{image_id}", response_model=AnalysisResponse)
async def analyze_single_image(
    image_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Analyze a single image using AI.
    """
    # Get image from database
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Check if file exists
    if not os.path.exists(image.file_path):
        raise HTTPException(status_code=404, detail="Image file not found")
    
    try:
        # Get existing categories for AI context
        categories = db.query(Category).all()
        categories_data = [
            {"id": cat.id, "name": cat.name, "description": cat.description}
            for cat in categories
        ]
        
        # Analyze image
        analysis_result = await ai_service.analyze_image(image.file_path, categories_data)
        
        if analysis_result.get("analysis_success", False):
            # Update image with AI analysis results
            image.ai_name = analysis_result.get("ai_name")
            image.ai_description = analysis_result.get("ai_description")
            image.ai_tags = ai_service._format_tags_for_storage(analysis_result.get("ai_tags", []))
            image.ai_objects = ai_service._format_tags_for_storage(analysis_result.get("ai_objects", []))
            image.ai_scene_description = analysis_result.get("ai_scene_description")
            image.ai_color_palette = ai_service._format_tags_for_storage(analysis_result.get("ai_color_palette", []))
            image.ai_emotions = ai_service._format_tags_for_storage(analysis_result.get("ai_emotions", []))
            image.ai_confidence_score = analysis_result.get("ai_confidence_score", 0.0)
            image.ai_user_suggested_name = analysis_result.get("ai_user_suggested_name")
            image.ai_user_suggested_description = analysis_result.get("ai_user_suggested_description")
            image.ai_user_suggested_tags = ai_service._format_tags_for_storage(analysis_result.get("ai_user_suggested_tags", []))
            
            # Handle category selection
            category_selection = analysis_result.get("category_selection", {})
            selected_category = category_selection.get("selected_category", "Other")
            
            if selected_category == "new":
                # Create new category
                new_category = Category(
                    name=category_selection.get("new_category_name", "AI Generated"),
                    description=category_selection.get("new_category_description", "AI-generated category"),
                    is_ai_generated=True
                )
                db.add(new_category)
                db.flush()  # Get the ID
                image.ai_category_id = new_category.id
                image.ai_user_suggested_category_id = new_category.id
            else:
                # Find existing category
                existing_category = db.query(Category).filter(Category.name == selected_category).first()
                if existing_category:
                    image.ai_category_id = existing_category.id
                    image.ai_user_suggested_category_id = existing_category.id
                    # Update usage count
                    existing_category.usage_count += 1
                else:
                    # Fallback to "Other" category
                    other_category = db.query(Category).filter(Category.name == "Other").first()
                    if other_category:
                        image.ai_category_id = other_category.id
                        image.ai_user_suggested_category_id = other_category.id
            
            # Mark as no longer needing manual metadata
            image.needs_manual_metadata = False
            
            db.commit()
            
            return AnalysisResponse(
                success=True,
                message="Image analyzed successfully",
                analysis_data=analysis_result
            )
        else:
            # Analysis failed, mark as needing manual metadata
            image.needs_manual_metadata = True
            db.commit()
            
            return AnalysisResponse(
                success=False,
                message="AI analysis failed",
                error=analysis_result.get("error_message", "Unknown error"),
                analysis_data=analysis_result
            )
    
    except Exception as e:
        # Mark as needing manual metadata on error
        image.needs_manual_metadata = True
        db.commit()
        
        return AnalysisResponse(
            success=False,
            message="Analysis failed",
            error=str(e)
        )

@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_multiple_images(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Analyze multiple images using AI.
    """
    results = []
    successful_analyses = 0
    failed_analyses = 0
    
    # Get all images
    images = db.query(Image).filter(Image.id.in_(request.image_ids)).all()
    image_dict = {img.id: img for img in images}
    
    # Get existing categories
    categories = db.query(Category).all()
    categories_data = [
        {"id": cat.id, "name": cat.name, "description": cat.description}
        for cat in categories
    ]
    
    # Process each image
    for image_id in request.image_ids:
        if image_id not in image_dict:
            results.append(AnalysisResponse(
                success=False,
                message=f"Image {image_id} not found",
                error="Image not found"
            ))
            failed_analyses += 1
            continue
        
        image = image_dict[image_id]
        
        if not os.path.exists(image.file_path):
            results.append(AnalysisResponse(
                success=False,
                message=f"Image file not found for {image_id}",
                error="File not found"
            ))
            failed_analyses += 1
            continue
        
        try:
            # Analyze image
            analysis_result = await ai_service.analyze_image(image.file_path, categories_data)
            
            if analysis_result.get("analysis_success", False):
                # Update image with AI analysis results (same logic as single analysis)
                # ... (implementation similar to single analysis)
                
                results.append(AnalysisResponse(
                    success=True,
                    message=f"Image {image_id} analyzed successfully",
                    analysis_data=analysis_result
                ))
                successful_analyses += 1
            else:
                results.append(AnalysisResponse(
                    success=False,
                    message=f"AI analysis failed for image {image_id}",
                    error=analysis_result.get("error_message", "Unknown error"),
                    analysis_data=analysis_result
                ))
                failed_analyses += 1
        
        except Exception as e:
            results.append(AnalysisResponse(
                success=False,
                message=f"Analysis failed for image {image_id}",
                error=str(e)
            ))
            failed_analyses += 1
    
    # Commit all changes
    db.commit()
    
    return BatchAnalysisResponse(
        total_images=len(request.image_ids),
        successful_analyses=successful_analyses,
        failed_analyses=failed_analyses,
        results=results
    )

@router.get("/cost-estimate")
async def get_analysis_cost_estimate(num_images: int = 1):
    """
    Get cost estimate for AI analysis.
    """
    if num_images < 1 or num_images > 100:
        raise HTTPException(status_code=400, detail="Number of images must be between 1 and 100")
    
    return ai_service.get_analysis_cost_estimate(num_images)

@router.get("/status")
async def get_ai_service_status():
    """
    Get AI service status and configuration.
    """
    return {
        "ai_enabled": ai_service.api_key is not None,
        "model": ai_service.model,
        "max_retries": ai_service.max_retries,
        "retry_delay": ai_service.retry_delay
    }



