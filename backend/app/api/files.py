"""
File management API endpoints for the Simple Cloud Photo Gallery App.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models import Image
from ..services.file_service import FileService
import os

router = APIRouter(prefix="/api/files", tags=["files"])

# Initialize file service
file_service = FileService()

@router.get("/download/{image_id}")
async def download_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Download an image file by its ID.
    """
    # Get image from database
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Check if file exists
    if not file_service.file_exists(image.file_path):
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    
    # Return file
    return FileResponse(
        path=image.file_path,
        media_type=image.mime_type,
        filename=image.original_filename
    )

@router.get("/thumbnail/{image_id}")
async def get_image_thumbnail(
    image_id: int,
    size: int = Query(200, ge=50, le=800, description="Thumbnail size in pixels"),
    db: Session = Depends(get_db)
):
    """
    Get a thumbnail of an image.
    TODO: Implement thumbnail generation in future phase.
    """
    # For now, return the original image
    # In a future phase, we'll implement proper thumbnail generation
    return await download_image(image_id, db)

@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an image and its file.
    """
    # Get image from database
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete file from filesystem
    file_deleted = file_service.delete_file(image.file_path)
    
    # Delete from database
    db.delete(image)
    db.commit()
    
    return {
        "success": True,
        "message": "Image deleted successfully",
        "file_deleted": file_deleted
    }

@router.get("/info/{image_id}")
async def get_image_file_info(
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed file information for an image.
    """
    # Get image from database
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Get file info
    file_info = file_service.get_file_info(image.file_path)
    
    return {
        "image_id": image.id,
        "filename": image.filename,
        "original_filename": image.original_filename,
        "file_path": image.file_path,
        "file_size": image.file_size,
        "mime_type": image.mime_type,
        "file_extension": image.file_extension,
        "file_exists": file_info.get("exists", False),
        "created_at": image.created_at,
        "updated_at": image.updated_at
    }

@router.get("/stats")
async def get_file_stats(db: Session = Depends(get_db)):
    """
    Get file storage statistics.
    """
    # Get total images
    total_images = db.query(Image).count()
    
    # Get total file size
    total_size_query = db.query(Image.file_size).all()
    total_size = sum(size[0] for size in total_size_query) if total_size_query else 0
    
    # Get file type breakdown
    from sqlalchemy import func
    file_types = db.query(
        Image.file_extension,
        func.count(Image.id).label('count'),
        func.sum(Image.file_size).label('total_size')
    ).group_by(Image.file_extension).all()
    
    # Get images by size ranges
    small_images = db.query(Image).filter(Image.file_size < 1024 * 1024).count()  # < 1MB
    medium_images = db.query(Image).filter(
        Image.file_size >= 1024 * 1024,
        Image.file_size < 5 * 1024 * 1024
    ).count()  # 1-5MB
    large_images = db.query(Image).filter(Image.file_size >= 5 * 1024 * 1024).count()  # > 5MB
    
    return {
        "total_images": total_images,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "average_size_bytes": round(total_size / total_images, 2) if total_images > 0 else 0,
        "file_types": [
            {
                "extension": ext,
                "count": count,
                "total_size_bytes": total_size or 0,
                "total_size_mb": round((total_size or 0) / (1024 * 1024), 2)
            }
            for ext, count, total_size in file_types
        ],
        "size_ranges": {
            "small_images": small_images,
            "medium_images": medium_images,
            "large_images": large_images
        }
    }

@router.post("/cleanup")
async def cleanup_orphaned_files(db: Session = Depends(get_db)):
    """
    Clean up orphaned files (files on disk but not in database).
    """
    # Get all file paths from database
    db_files = set()
    for image in db.query(Image.file_path).all():
        db_files.add(image[0])
    
    # Find orphaned files
    orphaned_files = []
    base_upload_dir = file_service.base_upload_dir
    
    if os.path.exists(base_upload_dir):
        for root, dirs, files in os.walk(base_upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if file_path not in db_files:
                    orphaned_files.append(file_path)
    
    # Delete orphaned files
    deleted_count = 0
    for file_path in orphaned_files:
        if file_service.delete_file(file_path):
            deleted_count += 1
    
    # Clean up empty directories
    file_service.cleanup_empty_directories()
    
    return {
        "success": True,
        "orphaned_files_found": len(orphaned_files),
        "files_deleted": deleted_count,
        "message": f"Cleanup completed. Deleted {deleted_count} orphaned files."
    }
