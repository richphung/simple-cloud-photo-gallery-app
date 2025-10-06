"""
Database models for the Simple Cloud Photo Gallery App.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Category(Base):
    """
    Categories table for organizing images.
    """
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_ai_generated = Column(Boolean, default=False, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user_images = relationship("Image", foreign_keys="Image.user_category_id", back_populates="user_category")
    ai_images = relationship("Image", foreign_keys="Image.ai_category_id", back_populates="ai_category")
    ai_suggested_images = relationship("Image", foreign_keys="Image.ai_user_suggested_category_id", back_populates="ai_user_suggested_category")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_category_name', 'name'),
        Index('idx_category_usage', 'usage_count'),
    )

class Image(Base):
    """
    Images table storing all image metadata and file information.
    """
    __tablename__ = "images"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # File information
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=False)
    file_extension = Column(String(10), nullable=False)
    
    # User-provided metadata
    user_name = Column(String(200), nullable=True, index=True)
    user_description = Column(Text, nullable=True)
    user_tags = Column(Text, nullable=True)  # JSON string of tags
    user_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    
    # AI-generated metadata
    ai_name = Column(String(200), nullable=True, index=True)
    ai_description = Column(Text, nullable=True)
    ai_tags = Column(Text, nullable=True)  # JSON string of tags
    ai_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    
    # AI user-friendly suggestions
    ai_user_suggested_name = Column(String(200), nullable=True, index=True)
    ai_user_suggested_description = Column(Text, nullable=True)
    ai_user_suggested_tags = Column(Text, nullable=True)  # JSON string of tags
    ai_user_suggested_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    
    # AI analysis results
    ai_objects = Column(Text, nullable=True)  # JSON string of detected objects
    ai_scene_description = Column(Text, nullable=True)
    ai_color_palette = Column(Text, nullable=True)  # JSON string of colors
    ai_emotions = Column(Text, nullable=True)  # JSON string of emotions
    ai_confidence_score = Column(Float, nullable=True)
    
    # Processing status
    ai_processing_status = Column(String(20), default='pending', nullable=False, index=True)  # pending, processing, completed, failed
    needs_manual_metadata = Column(Boolean, default=False, nullable=False, index=True)
    is_manually_edited = Column(Boolean, default=False, nullable=False)
    last_edited_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user_category = relationship("Category", foreign_keys=[user_category_id], back_populates="user_images")
    ai_category = relationship("Category", foreign_keys=[ai_category_id], back_populates="ai_images")
    ai_user_suggested_category = relationship("Category", foreign_keys=[ai_user_suggested_category_id], back_populates="ai_suggested_images")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_image_filename', 'filename'),
        Index('idx_image_user_name', 'user_name'),
        Index('idx_image_ai_name', 'ai_name'),
        Index('idx_image_created_at', 'created_at'),
        Index('idx_image_manual_metadata', 'needs_manual_metadata'),
        Index('idx_image_user_category', 'user_category_id'),
        Index('idx_image_ai_category', 'ai_category_id'),
    )
    
    def __repr__(self):
        return f"<Image(id={self.id}, filename='{self.filename}', user_name='{self.user_name}')>"


