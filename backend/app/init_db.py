"""
Database initialization script for the Simple Cloud Photo Gallery App.
Creates tables and populates with initial data.
"""

from sqlalchemy.orm import Session
from .database import engine, SessionLocal, init_db, reset_db
from .models import Category, Image
import json

def create_initial_categories():
    """
    Create initial categories with common photo categories.
    """
    categories_data = [
        {
            "name": "Nature",
            "description": "Natural landscapes, wildlife, plants, and outdoor scenes",
            "is_ai_generated": False,
            "usage_count": 0
        },
        {
            "name": "People",
            "description": "Portraits, group photos, candid shots, and people-focused images",
            "is_ai_generated": False,
            "usage_count": 0
        },
        {
            "name": "Architecture",
            "description": "Buildings, structures, urban landscapes, and architectural details",
            "is_ai_generated": False,
            "usage_count": 0
        },
        {
            "name": "Food",
            "description": "Meals, ingredients, cooking, restaurants, and culinary scenes",
            "is_ai_generated": False,
            "usage_count": 0
        },
        {
            "name": "Travel",
            "description": "Vacation photos, landmarks, tourist attractions, and travel experiences",
            "is_ai_generated": False,
            "usage_count": 0
        },
        {
            "name": "Events",
            "description": "Celebrations, parties, ceremonies, and special occasions",
            "is_ai_generated": False,
            "usage_count": 0
        },
        {
            "name": "Pets",
            "description": "Dogs, cats, and other animal companions",
            "is_ai_generated": False,
            "usage_count": 0
        },
        {
            "name": "Art",
            "description": "Artwork, creative projects, artistic compositions, and visual art",
            "is_ai_generated": False,
            "usage_count": 0
        },
        {
            "name": "Technology",
            "description": "Gadgets, computers, electronics, and tech-related subjects",
            "is_ai_generated": False,
            "usage_count": 0
        },
        {
            "name": "Sports",
            "description": "Athletic activities, sports events, fitness, and physical activities",
            "is_ai_generated": False,
            "usage_count": 0
        },
        {
            "name": "Abstract",
            "description": "Abstract compositions, patterns, textures, and non-representational art",
            "is_ai_generated": False,
            "usage_count": 0
        },
        {
            "name": "Other",
            "description": "Miscellaneous images that don't fit other categories",
            "is_ai_generated": False,
            "usage_count": 0
        }
    ]
    
    db = SessionLocal()
    try:
        # Check if categories already exist
        existing_categories = db.query(Category).count()
        if existing_categories > 0:
            print(f"Categories already exist ({existing_categories} found). Skipping initialization.")
            return
        
        # Create categories
        for cat_data in categories_data:
            category = Category(**cat_data)
            db.add(category)
        
        db.commit()
        print(f"Successfully created {len(categories_data)} initial categories.")
        
    except Exception as e:
        print(f"Error creating initial categories: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_sample_images():
    """
    Create a few sample images for testing (without actual files).
    """
    sample_images = [
        {
            "filename": "20241004_120000_sample_sunset.jpg",
            "original_filename": "sunset.jpg",
            "file_path": "uploads/2024/10/04/20241004_120000_sample_sunset.jpg",
            "file_size": 2048576,  # 2MB
            "mime_type": "image/jpeg",
            "file_extension": "jpg",
            "user_name": "Beautiful Sunset",
            "user_description": "A stunning sunset over the mountains",
            "user_tags": json.dumps(["sunset", "mountains", "nature", "landscape"]),
            "ai_name": "Mountain Sunset Landscape",
            "ai_description": "A breathtaking sunset scene featuring dramatic mountain silhouettes against a vibrant orange and pink sky",
            "ai_tags": json.dumps(["sunset", "mountains", "landscape", "golden hour", "dramatic sky", "nature"]),
            "ai_objects": json.dumps(["mountain", "sky", "clouds", "horizon"]),
            "ai_scene_description": "A peaceful mountain landscape during golden hour with dramatic cloud formations",
            "ai_color_palette": json.dumps(["#FF6B35", "#F7931E", "#FFD23F", "#4A90E2", "#2E86AB"]),
            "ai_emotions": json.dumps(["peaceful", "awe", "serenity", "wonder"]),
            "ai_confidence_score": 0.95,
            "needs_manual_metadata": False,
            "is_manually_edited": False
        },
        {
            "filename": "20241004_120100_sample_cat.jpg",
            "original_filename": "my_cat.jpg",
            "file_path": "uploads/2024/10/04/20241004_120100_sample_cat.jpg",
            "file_size": 1536000,  # 1.5MB
            "mime_type": "image/jpeg",
            "file_extension": "jpg",
            "user_name": "My Cat Whiskers",
            "user_description": "My adorable cat sitting in the garden",
            "user_tags": json.dumps(["cat", "pet", "garden", "cute"]),
            "ai_name": "Domestic Cat in Garden",
            "ai_description": "A fluffy orange tabby cat sitting peacefully in a well-maintained garden setting",
            "ai_tags": json.dumps(["cat", "pet", "garden", "orange", "tabby", "outdoor", "cute"]),
            "ai_objects": json.dumps(["cat", "plants", "grass", "fence"]),
            "ai_scene_description": "A domestic cat in a residential garden with lush greenery",
            "ai_color_palette": json.dumps(["#FFA500", "#228B22", "#8B4513", "#F5F5DC", "#2F4F4F"]),
            "ai_emotions": json.dumps(["content", "peaceful", "cute", "relaxed"]),
            "ai_confidence_score": 0.92,
            "needs_manual_metadata": False,
            "is_manually_edited": False
        }
    ]
    
    db = SessionLocal()
    try:
        # Check if images already exist
        existing_images = db.query(Image).count()
        if existing_images > 0:
            print(f"Images already exist ({existing_images} found). Skipping sample creation.")
            return
        
        # Get the first category for sample images
        nature_category = db.query(Category).filter(Category.name == "Nature").first()
        pets_category = db.query(Category).filter(Category.name == "Pets").first()
        
        if not nature_category or not pets_category:
            print("Required categories not found. Please run create_initial_categories() first.")
            return
        
        # Create sample images
        for i, img_data in enumerate(sample_images):
            # Assign appropriate category
            if "sunset" in img_data["filename"]:
                img_data["user_category_id"] = nature_category.id
                img_data["ai_category_id"] = nature_category.id
                img_data["ai_user_suggested_category_id"] = nature_category.id
            elif "cat" in img_data["filename"]:
                img_data["user_category_id"] = pets_category.id
                img_data["ai_category_id"] = pets_category.id
                img_data["ai_user_suggested_category_id"] = pets_category.id
            
            image = Image(**img_data)
            db.add(image)
        
        db.commit()
        print(f"Successfully created {len(sample_images)} sample images.")
        
    except Exception as e:
        print(f"Error creating sample images: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """
    Initialize the complete database with tables and initial data.
    """
    print("Initializing database...")
    
    # Create all tables
    init_db()
    print("Database tables created.")
    
    # Create initial categories
    create_initial_categories()
    
    # Create sample images
    create_sample_images()
    
    print("Database initialization complete!")

def reset_database():
    """
    Reset the complete database (drop and recreate all tables and data).
    """
    print("Resetting database...")
    
    # Drop and recreate all tables
    reset_db()
    print("Database tables reset.")
    
    # Create initial categories
    create_initial_categories()
    
    # Create sample images
    create_sample_images()
    
    print("Database reset complete!")

if __name__ == "__main__":
    # Run database initialization
    init_database()



