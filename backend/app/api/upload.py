"""
File upload API endpoints for the Simple Cloud Photo Gallery App.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Image, Category
from ..services.file_service import FileService
from ..services.metadata_service import MetadataService
from ..services.ai_processor import process_image_metadata
from pydantic import BaseModel
from datetime import datetime
import os
import uuid

router = APIRouter(prefix="/api/upload", tags=["upload"])

class UploadResponse(BaseModel):
    success: bool
    message: str
    image_id: Optional[int] = None
    filename: Optional[str] = None
    file_path: Optional[str] = None
    needs_manual_metadata: bool = False

class BatchUploadResponse(BaseModel):
    total_files: int
    successful_uploads: int
    failed_uploads: int
    results: List[UploadResponse]

# Initialize services
file_service = FileService()
metadata_service = MetadataService()

@router.post("/single", response_model=UploadResponse)
async def upload_single_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_name: Optional[str] = Form(None),
    user_description: Optional[str] = Form(None),
    user_tags: Optional[str] = Form(None),
    user_category_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a single image with optional user metadata.
    """
    try:
        # Validate file
        if not file_service.is_valid_image(file):
            raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")
        
        if not file_service.is_valid_size(file):
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
        
        # Generate unique filename
        file_extension = file_service.get_file_extension(file.filename)
        unique_filename = file_service.generate_filename(file.filename)
        
        # Create directory structure
        file_path = file_service.create_directory_structure(unique_filename)
        
        # Save file
        saved_path = await file_service.save_file(file, file_path)
        
        # Extract basic metadata
        file_size = file_service.get_file_size(saved_path)
        mime_type = file.content_type or file_service.detect_mime_type(saved_path)
        
        # Create image record in database
        image_data = {
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": saved_path,
            "file_size": file_size,
            "mime_type": mime_type,
            "file_extension": file_extension,
            "user_name": user_name,
            "user_description": user_description,
            "user_tags": user_tags,
            "user_category_id": user_category_id,
            "needs_manual_metadata": True  # Will be updated after AI analysis
        }
        
        # Create image record
        image = Image(**image_data)
        db.add(image)
        db.commit()
        db.refresh(image)
        
        # Start AI analysis in background
        background_tasks.add_task(process_image_metadata, image.id, saved_path, db)
        
        return UploadResponse(
            success=True,
            message="Image uploaded successfully",
            image_id=image.id,
            filename=unique_filename,
            file_path=saved_path,
            needs_manual_metadata=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if database operation fails
        if 'saved_path' in locals() and os.path.exists(saved_path):
            os.remove(saved_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/batch", response_model=BatchUploadResponse)
async def upload_multiple_images(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload multiple images with individual processing.
    """
    results = []
    successful_uploads = 0
    failed_uploads = 0
    
    for file in files:
        try:
            # Validate file
            if not file_service.is_valid_image(file):
                results.append(UploadResponse(
                    success=False,
                    message=f"Invalid file type: {file.filename}"
                ))
                failed_uploads += 1
                continue
            
            if not file_service.is_valid_size(file):
                results.append(UploadResponse(
                    success=False,
                    message=f"File too large: {file.filename}"
                ))
                failed_uploads += 1
                continue
            
            # Generate unique filename
            file_extension = file_service.get_file_extension(file.filename)
            unique_filename = file_service.generate_filename(file.filename)
            
            # Create directory structure
            file_path = file_service.create_directory_structure(unique_filename)
            
            # Save file
            saved_path = await file_service.save_file(file, file_path)
            
            # Extract basic metadata
            file_size = file_service.get_file_size(saved_path)
            mime_type = file.content_type or file_service.detect_mime_type(saved_path)
            
            # Create image record in database
            image_data = {
                "filename": unique_filename,
                "original_filename": file.filename,
                "file_path": saved_path,
                "file_size": file_size,
                "mime_type": mime_type,
                "file_extension": file_extension,
                "needs_manual_metadata": True  # Will be updated after AI analysis
            }
            
            # Create image record
            image = Image(**image_data)
            db.add(image)
            db.commit()
            db.refresh(image)
            
            # Start AI analysis in background
            background_tasks.add_task(process_image_metadata, image.id, saved_path, db)
            
            results.append(UploadResponse(
                success=True,
                message=f"Uploaded: {file.filename}",
                image_id=image.id,
                filename=unique_filename,
                file_path=saved_path,
                needs_manual_metadata=True
            ))
            successful_uploads += 1
            
        except Exception as e:
            # Clean up file if database operation fails
            if 'saved_path' in locals() and os.path.exists(saved_path):
                os.remove(saved_path)
            
            results.append(UploadResponse(
                success=False,
                message=f"Failed to upload {file.filename}: {str(e)}"
            ))
            failed_uploads += 1
    
    return BatchUploadResponse(
        total_files=len(files),
        successful_uploads=successful_uploads,
        failed_uploads=failed_uploads,
        results=results
    )

@router.get("/progress/{upload_id}")
async def get_upload_progress(upload_id: str):
    """
    Get upload progress for a specific upload session.
    This will be used for tracking AI analysis progress in Phase 4.
    """
    # TODO: Implement in Phase 4 with AI analysis
    return {"upload_id": upload_id, "status": "completed", "progress": 100}
