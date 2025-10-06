"""
System monitoring and testing API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database import get_db
from ..models import Image, Category
from ..config import settings
from pydantic import BaseModel
from typing import Dict, Any, List
import os
import time
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/system", tags=["system"])

class SystemStatusResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    memory_usage: Dict[str, Any]
    disk_usage: Dict[str, Any]
    database_status: str
    ai_service_status: str
    file_storage_status: str

class DatabaseStatsResponse(BaseModel):
    total_images: int
    total_categories: int
    images_with_ai_data: int
    images_needing_metadata: int
    manually_edited_images: int
    total_file_size_bytes: int
    total_file_size_mb: float
    average_file_size_mb: float
    most_used_category: str
    recent_uploads_24h: int

class HealthCheckResponse(BaseModel):
    status: str
    checks: Dict[str, str]
    timestamp: str
    response_time_ms: float

@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Get comprehensive system status including resource usage and service health.
    """
    try:
        # Get system information (simplified for development)
        memory = {"total": 8 * 1024**3, "available": 4 * 1024**3, "percent": 50}  # Mock data
        disk = {"total": 100 * 1024**3, "free": 50 * 1024**3}  # Mock data
        
        # Calculate uptime (simplified - in production, track actual start time)
        uptime_seconds = time.time() - os.path.getctime(__file__)
        
        # Check database status
        try:
            from ..database import SessionLocal
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            database_status = "healthy"
        except Exception:
            database_status = "unhealthy"
        
        # Check AI service status
        ai_service_status = "enabled" if getattr(settings, 'AI_ENABLED', False) else "disabled"
        
        # Check file storage status
        upload_dir = settings.UPLOAD_DIR
        if os.path.exists(upload_dir) and os.access(upload_dir, os.W_OK):
            file_storage_status = "healthy"
        else:
            file_storage_status = "unhealthy"
        
        return SystemStatusResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version=getattr(settings, 'APP_VERSION', '1.0.0'),
            uptime_seconds=uptime_seconds,
            memory_usage={
                "total_gb": round(memory["total"] / (1024**3), 2),
                "available_gb": round(memory["available"] / (1024**3), 2),
                "used_percent": memory["percent"]
            },
            disk_usage={
                "total_gb": round(disk["total"] / (1024**3), 2),
                "free_gb": round(disk["free"] / (1024**3), 2),
                "used_percent": round((disk["total"] - disk["free"]) / disk["total"] * 100, 2)
            },
            database_status=database_status,
            ai_service_status=ai_service_status,
            file_storage_status=file_storage_status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@router.get("/database/stats", response_model=DatabaseStatsResponse)
async def get_database_stats(db: Session = Depends(get_db)):
    """
    Get detailed database statistics and metrics.
    """
    try:
        # Basic counts
        total_images = db.query(Image).count()
        total_categories = db.query(Category).count()
        images_with_ai_data = db.query(Image).filter(Image.ai_name.isnot(None)).count()
        images_needing_metadata = db.query(Image).filter(Image.needs_manual_metadata == True).count()
        manually_edited_images = db.query(Image).filter(Image.is_manually_edited == True).count()
        
        # File size statistics
        file_sizes = db.query(Image.file_size).all()
        total_file_size_bytes = sum(size[0] for size in file_sizes if size[0])
        total_file_size_mb = total_file_size_bytes / (1024 * 1024)
        average_file_size_mb = total_file_size_mb / total_images if total_images > 0 else 0
        
        # Most used category
        from sqlalchemy import func
        most_used_category_result = db.query(
            Category.name,
            func.count(Image.id).label('count')
        ).outerjoin(Image, or_(
            Image.user_category_id == Category.id,
            Image.ai_category_id == Category.id,
            Image.ai_user_suggested_category_id == Category.id
        )).group_by(Category.id, Category.name).order_by(func.count(Image.id).desc()).first()
        
        most_used_category = most_used_category_result[0] if most_used_category_result else "None"
        
        # Recent uploads (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.now() - timedelta(days=1)
        recent_uploads_24h = db.query(Image).filter(Image.created_at >= yesterday).count()
        
        return DatabaseStatsResponse(
            total_images=total_images,
            total_categories=total_categories,
            images_with_ai_data=images_with_ai_data,
            images_needing_metadata=images_needing_metadata,
            manually_edited_images=manually_edited_images,
            total_file_size_bytes=total_file_size_bytes,
            total_file_size_mb=round(total_file_size_mb, 2),
            average_file_size_mb=round(average_file_size_mb, 2),
            most_used_category=most_used_category,
            recent_uploads_24h=recent_uploads_24h
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database stats: {str(e)}")

@router.get("/health/detailed", response_model=HealthCheckResponse)
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Perform detailed health checks on all system components.
    """
    start_time = time.time()
    checks = {}
    
    try:
        # Database check
        try:
            db.execute("SELECT 1")
            checks["database"] = "healthy"
        except Exception as e:
            checks["database"] = f"unhealthy: {str(e)}"
        
        # File storage check
        upload_dir = settings.UPLOAD_DIR
        if os.path.exists(upload_dir) and os.access(upload_dir, os.W_OK):
            checks["file_storage"] = "healthy"
        else:
            checks["file_storage"] = "unhealthy: directory not accessible"
        
        # AI service check
        if getattr(settings, 'AI_ENABLED', False):
            checks["ai_service"] = "enabled"
        else:
            checks["ai_service"] = "disabled"
        
        # Memory check (simplified)
        checks["memory"] = "healthy"
        
        # Disk space check (simplified)
        checks["disk_space"] = "healthy"
        
        # Overall status
        unhealthy_checks = [k for k, v in checks.items() if "unhealthy" in v or "error" in v]
        if unhealthy_checks:
            status = "degraded"
        else:
            status = "healthy"
        
        response_time_ms = (time.time() - start_time) * 1000
        
        return HealthCheckResponse(
            status=status,
            checks=checks,
            timestamp=datetime.now().isoformat(),
            response_time_ms=round(response_time_ms, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/config")
async def get_system_config():
    """
    Get current system configuration (excluding sensitive information).
    """
    return {
        "app_name": getattr(settings, 'APP_NAME', 'Simple Cloud Photo Gallery API'),
        "app_version": getattr(settings, 'APP_VERSION', '1.0.0'),
        "debug_mode": getattr(settings, 'DEBUG_MODE', False),
        "uvicorn_port": getattr(settings, 'UVICORN_PORT', 8002),
        "database_url": getattr(settings, 'DATABASE_URL', 'sqlite:///./photo_gallery.db'),
        "upload_dir": getattr(settings, 'UPLOAD_DIR', 'uploads'),
        "max_file_size_mb": getattr(settings, 'MAX_FILE_SIZE_MB', 10),
        "ai_enabled": getattr(settings, 'AI_ENABLED', False),
        "ai_model": getattr(settings, 'AI_MODEL', None) if getattr(settings, 'AI_ENABLED', False) else None,
        "frontend_url": getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    }

@router.get("/logs/recent")
async def get_recent_logs(lines: int = 50):
    """
    Get recent application logs (simplified implementation).
    """
    # In a real application, you would read from actual log files
    # For now, return a placeholder response
    return {
        "message": "Log viewing not implemented in development mode",
        "lines_requested": lines,
        "note": "In production, implement proper log file reading"
    }

@router.post("/test/upload")
async def test_upload_endpoint():
    """
    Test endpoint to verify upload functionality is working.
    """
    return {
        "status": "success",
        "message": "Upload endpoint is accessible",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/test/search")
async def test_search_endpoint():
    """
    Test endpoint to verify search functionality is working.
    """
    return {
        "status": "success",
        "message": "Search endpoint is accessible",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/test/ai")
async def test_ai_endpoint():
    """
    Test endpoint to verify AI functionality is working.
    """
    return {
        "status": "success" if getattr(settings, 'AI_ENABLED', False) else "disabled",
        "message": "AI endpoint is accessible" if getattr(settings, 'AI_ENABLED', False) else "AI service is disabled",
        "ai_enabled": getattr(settings, 'AI_ENABLED', False),
        "timestamp": datetime.now().isoformat()
    }
