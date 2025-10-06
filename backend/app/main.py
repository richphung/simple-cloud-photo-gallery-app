from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import init_db
from .init_db import init_database
from .api import categories, images, upload, files, ai_analysis, search, metadata_edit, system
import os

# Create FastAPI app
app = FastAPI(
    title="Simple Cloud Photo Gallery API",
    description="""
    A comprehensive photo gallery application with AI-powered image analysis and metadata management.
    
    ## Features
    
    * **Image Management**: Upload, download, and manage image files
    * **AI Analysis**: Automatic image analysis using Claude 3.5 Sonnet Vision
    * **Search & Filtering**: Advanced search with text, category, and tag filters
    * **Metadata Editing**: Manual metadata editing with AI suggestions
    * **Category Management**: Dynamic category creation and management
    * **File Storage**: Local and cloud storage support
    
    ## Authentication
    
    Currently, no authentication is required for development. In production, implement proper authentication.
    
    ## Rate Limiting
    
    No rate limiting is currently implemented. Consider adding rate limiting for production use.
    """,
    version="1.0.0",
    contact={
        "name": "Simple Cloud Photo Gallery Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://127.0.0.1:8002",
            "description": "Development server"
        },
        {
            "url": "https://api.example.com",
            "description": "Production server"
        }
    ]
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    try:
        init_database()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        # Don't fail startup if database init fails
        pass

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",   # Vue.js dev server
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:3001",   # Vue.js dev server (alternative)
        "http://127.0.0.1:5173",   # Vite dev server (alternative)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# Mount static files for serving uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include API routers
app.include_router(categories.router)
app.include_router(images.router)
app.include_router(upload.router)
app.include_router(files.router)
app.include_router(ai_analysis.router)
app.include_router(search.router)
app.include_router(metadata_edit.router)
app.include_router(system.router)

@app.get("/")
async def root():
    return {"message": "Simple Cloud Photo Gallery API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
