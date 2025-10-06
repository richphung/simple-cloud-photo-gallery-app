"""
AI processor for handling image analysis and metadata extraction.
"""

from sqlalchemy.orm import Session
from ..models import Image, Category
from .ai_service import AIService
import json
from datetime import datetime

# Initialize AI service
ai_service = AIService()

async def process_image_metadata(image_id: int, file_path: str, db: Session):
    """
    Process image metadata using AI service integration.
    This function calls the OpenRouter API with Claude 3.5 Sonnet Vision.
    """
    print(f"Starting AI metadata processing for image ID: {image_id}, path: {file_path}")
    
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        print(f"Image with ID {image_id} not found for metadata processing.")
        return

    try:
        # Set status to processing
        image.ai_processing_status = 'processing'
        db.commit()
        print(f"Set AI processing status to 'processing' for image ID: {image_id}")
        # Get existing categories for AI context
        categories = db.query(Category).all()
        categories_data = [
            {"id": cat.id, "name": cat.name, "description": cat.description}
            for cat in categories
        ]
        
        # Analyze image using AI service
        analysis_result = await ai_service.analyze_image(file_path, categories_data)
        
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
            
            # Mark as no longer needing manual metadata and set status to completed
            image.needs_manual_metadata = False
            image.ai_processing_status = 'completed'
            image.updated_at = datetime.now()
            
            db.add(image)
            db.commit()
            db.refresh(image)
            print(f"AI metadata processing completed successfully for image ID: {image_id}")
        else:
            # AI analysis failed, mark for manual review and set status to failed
            image.needs_manual_metadata = True
            image.ai_processing_status = 'failed'
            image.updated_at = datetime.now()
            db.add(image)
            db.commit()
            db.refresh(image)
            print(f"AI metadata processing failed for image ID: {image_id}. Error: {analysis_result.get('error_message', 'Unknown error')}")

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error during AI metadata processing for image ID {image_id}: {e}")
        print(f"Full error details: {error_details}")
        image.needs_manual_metadata = True # Mark for manual review if AI fails
        image.ai_processing_status = 'failed'
        image.updated_at = datetime.now()
        db.add(image)
        db.commit()
        db.refresh(image)


