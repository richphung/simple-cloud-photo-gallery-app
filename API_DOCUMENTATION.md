# Simple Cloud Photo Gallery API Documentation

## Overview

The Simple Cloud Photo Gallery API is a RESTful service built with FastAPI that provides comprehensive image management, AI-powered analysis, and metadata editing capabilities. The API supports both local development and cloud deployment scenarios.

## Base URL

- **Development**: `http://127.0.0.1:8002`
- **Production**: `https://your-domain.com` (when deployed)

## Authentication

Currently, the API does not require authentication for development purposes. In production, you should implement proper authentication mechanisms.

## API Endpoints

### Health & Status

#### GET /health
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

#### GET /
Get basic API information.

**Response:**
```json
{
  "message": "Simple Cloud Photo Gallery API",
  "status": "running"
}
```

### Categories

#### GET /api/categories/
Get all categories.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Nature",
    "description": "Natural landscapes and wildlife",
    "is_ai_generated": false,
    "usage_count": 15,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### POST /api/categories/
Create a new category.

**Request Body:**
```json
{
  "name": "New Category",
  "description": "Category description",
  "is_ai_generated": false
}
```

#### GET /api/categories/{category_id}
Get a specific category by ID.

#### PUT /api/categories/{category_id}
Update a category.

#### DELETE /api/categories/{category_id}
Delete a category.

### Images

#### GET /api/images/
Get all images with pagination.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20)
- `sort_by` (str): Sort field (default: "created_at")
- `sort_order` (str): Sort order - "asc" or "desc" (default: "desc")

**Response:**
```json
{
  "images": [
    {
      "id": 1,
      "filename": "20241004_120100_sample_cat.jpg",
      "original_filename": "my_cat.jpg",
      "file_path": "uploads/2024/10/04/20241004_120100_sample_cat.jpg",
      "file_size": 1536000,
      "mime_type": "image/jpeg",
      "file_extension": ".jpg",
      "user_name": "My Cat",
      "user_description": "A cute cat in the garden",
      "user_tags": ["cat", "garden", "cute"],
      "user_category_id": 1,
      "user_category_name": "Pets",
      "ai_name": "Domestic Cat in Garden",
      "ai_description": "A domestic cat sitting in a well-maintained garden...",
      "ai_tags": ["cat", "garden", "outdoor", "pet"],
      "ai_category_id": 1,
      "ai_category_name": "Pets",
      "ai_confidence_score": 0.95,
      "needs_manual_metadata": false,
      "is_manually_edited": false,
      "created_at": "2024-10-04T12:01:00Z",
      "updated_at": "2024-10-04T12:01:00Z"
    }
  ],
  "total_count": 1,
  "page": 1,
  "limit": 20,
  "total_pages": 1,
  "has_next": false,
  "has_prev": false
}
```

#### GET /api/images/{image_id}
Get a specific image by ID.

#### GET /api/images/stats
Get image statistics.

**Response:**
```json
{
  "total_images": 150,
  "total_size_bytes": 157286400,
  "total_size_mb": 150.0,
  "average_size_mb": 1.0,
  "images_by_category": {
    "Nature": 45,
    "Pets": 30,
    "People": 25
  },
  "images_by_extension": {
    ".jpg": 120,
    ".png": 25,
    ".gif": 5
  },
  "recent_uploads": 15,
  "needs_manual_metadata": 5
}
```

### File Upload

#### POST /api/upload/single
Upload a single image file.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field and optional metadata fields

**Form Fields:**
- `file` (file): Image file to upload
- `user_name` (string, optional): User-provided name
- `user_description` (string, optional): User-provided description
- `user_tags` (string, optional): Comma-separated tags
- `user_category_id` (int, optional): Category ID

**Response:**
```json
{
  "success": true,
  "message": "Image uploaded successfully",
  "image_id": 1,
  "filename": "20241004_120100_sample_cat.jpg",
  "file_path": "uploads/2024/10/04/20241004_120100_sample_cat.jpg",
  "needs_manual_metadata": true
}
```

#### POST /api/upload/batch
Upload multiple image files.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `files` field (array of files)

**Response:**
```json
{
  "total_files": 3,
  "successful_uploads": 2,
  "failed_uploads": 1,
  "results": [
    {
      "success": true,
      "message": "Uploaded: image1.jpg",
      "image_id": 1,
      "filename": "20241004_120100_image1.jpg",
      "file_path": "uploads/2024/10/04/20241004_120100_image1.jpg",
      "needs_manual_metadata": true
    }
  ]
}
```

### File Management

#### GET /api/files/{image_id}/download
Download an image file.

#### DELETE /api/files/{image_id}
Delete an image and its file.

#### GET /api/files/{image_id}/info
Get file information.

#### GET /api/files/stats
Get file statistics.

### Search

#### POST /api/search/
Advanced search with filters.

**Request Body:**
```json
{
  "query": "cat garden",
  "categories": [1, 2],
  "tags": ["outdoor", "cute"],
  "date_from": "2024-01-01",
  "date_to": "2024-12-31",
  "sort_by": "created_at",
  "sort_order": "desc",
  "page": 1,
  "limit": 20,
  "needs_manual_metadata": false
}
```

**Response:**
```json
{
  "images": [...],
  "total_count": 25,
  "page": 1,
  "limit": 20,
  "total_pages": 2,
  "has_next": true,
  "has_prev": false,
  "search_filters": {
    "query": "cat garden",
    "categories": [1, 2],
    "tags": ["outdoor", "cute"],
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "sort_by": "created_at",
    "sort_order": "desc",
    "needs_manual_metadata": false
  }
}
```

#### GET /api/search/gallery
Get paginated gallery view.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20)
- `sort_by` (str): Sort field (default: "created_at")
- `sort_order` (str): Sort order (default: "desc")
- `category_id` (int, optional): Filter by category
- `needs_manual_metadata` (bool, optional): Filter by metadata status

#### GET /api/search/suggestions
Get search suggestions.

**Query Parameters:**
- `q` (string): Search query
- `limit` (int): Maximum suggestions (default: 10)

**Response:**
```json
{
  "suggestions": ["cat", "garden", "outdoor"],
  "query": "cat",
  "count": 3
}
```

#### GET /api/search/stats
Get search statistics.

### AI Analysis

#### GET /api/ai/status
Get AI service status.

**Response:**
```json
{
  "ai_enabled": true,
  "model": "anthropic/claude-3.5-sonnet",
  "max_retries": 3,
  "retry_delay": 1.0
}
```

#### GET /api/ai/cost-estimate
Get AI analysis cost estimate.

**Query Parameters:**
- `num_images` (int): Number of images to analyze

**Response:**
```json
{
  "cost_per_image": 0.01,
  "total_cost": 0.05,
  "currency": "USD",
  "note": "Costs are approximate and may vary based on image complexity and API pricing changes"
}
```

#### POST /api/ai/analyze/{image_id}
Trigger AI analysis for a specific image.

#### POST /api/ai/analyze/batch
Trigger AI analysis for multiple images.

### Metadata Editing

#### PUT /api/metadata/{image_id}
Update image metadata.

**Request Body:**
```json
{
  "user_name": "Updated Name",
  "user_description": "Updated description",
  "user_tags": ["tag1", "tag2"],
  "user_category_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "Metadata updated successfully for image 1",
  "image_id": 1,
  "updated_fields": ["user_name", "user_description", "user_tags", "user_category_id"]
}
```

#### PUT /api/metadata/bulk
Bulk update metadata for multiple images.

**Request Body:**
```json
{
  "image_ids": [1, 2, 3],
  "updates": {
    "user_category_id": 1,
    "user_tags": ["bulk", "updated"]
  }
}
```

#### GET /api/metadata/{image_id}/history
Get edit history for an image.

#### POST /api/metadata/{image_id}/reanalyze
Trigger AI re-analysis for an image.

#### GET /api/metadata/{image_id}/suggestions
Get metadata suggestions for an image.

**Response:**
```json
{
  "category_suggestions": [
    {
      "id": 1,
      "name": "Pets",
      "confidence": "high",
      "source": "ai_analysis"
    }
  ],
  "tag_suggestions": [
    {"tag": "cat", "count": 15},
    {"tag": "garden", "count": 8}
  ],
  "name_suggestions": [
    {
      "name": "Domestic Cat in Garden",
      "confidence": "high",
      "source": "ai_analysis"
    }
  ]
}
```

#### GET /api/metadata/needs-metadata
Get images that need manual metadata editing.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20)

#### DELETE /api/metadata/{image_id}
Reset image metadata to AI-generated values.

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "VALIDATION_ERROR",
  "field": "user_name",
  "timestamp": "2024-10-04T12:00:00Z"
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Request data validation failed
- `FILE_NOT_FOUND`: Requested file does not exist
- `CATEGORY_NOT_FOUND`: Specified category does not exist
- `UPLOAD_FAILED`: File upload failed
- `AI_ANALYSIS_FAILED`: AI analysis failed
- `DATABASE_ERROR`: Database operation failed

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting to prevent abuse.

## File Storage

### Local Development
Files are stored in the `uploads/` directory with the following structure:
```
uploads/
├── 2024/
│   ├── 10/
│   │   ├── 04/
│   │   │   ├── 20241004_120100_image1.jpg
│   │   │   └── 20241004_120200_image2.png
│   │   └── 05/
│   └── 11/
└── 2025/
```

### File Naming Convention
Files are renamed using the format: `YYYYMMDD_HHMMSS_original_name.ext`

### Supported File Types
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)
- BMP (.bmp)
- TIFF (.tiff)

### File Size Limits
- Maximum file size: 10MB (configurable)
- Maximum dimensions: No limit (for local development)

## AI Integration

### OpenRouter Configuration
The API integrates with OpenRouter for AI-powered image analysis using Claude 3.5 Sonnet Vision.

**Required Environment Variables:**
- `OPENROUTER_API_KEY`: Your OpenRouter API key

**AI Features:**
- Automatic image analysis
- Metadata extraction
- Category suggestions
- Tag generation
- Confidence scoring

### AI Analysis Process
1. Image is uploaded
2. Basic metadata is extracted (file size, dimensions, etc.)
3. Image is sent to OpenRouter for AI analysis
4. AI response is parsed and stored
5. Categories are created or matched
6. Image is marked as processed

## Database Schema

### Categories Table
- `id`: Primary key
- `name`: Category name (unique)
- `description`: Category description
- `is_ai_generated`: Whether category was created by AI
- `usage_count`: Number of images using this category
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Images Table
- `id`: Primary key
- `filename`: Generated filename
- `original_filename`: Original uploaded filename
- `file_path`: Path to stored file
- `file_size`: File size in bytes
- `mime_type`: MIME type
- `file_extension`: File extension
- `user_name`: User-provided name
- `user_description`: User-provided description
- `user_tags`: JSON array of user tags
- `user_category_id`: Foreign key to categories
- `ai_name`: AI-generated name
- `ai_description`: AI-generated description
- `ai_tags`: JSON array of AI tags
- `ai_category_id`: Foreign key to AI-suggested category
- `ai_user_suggested_name`: AI-suggested user-friendly name
- `ai_user_suggested_description`: AI-suggested user-friendly description
- `ai_user_suggested_tags`: JSON array of AI-suggested user tags
- `ai_user_suggested_category_id`: Foreign key to AI-suggested category
- `ai_objects`: JSON array of detected objects
- `ai_scene_description`: AI scene description
- `ai_color_palette`: JSON array of dominant colors
- `ai_emotions`: JSON array of detected emotions
- `ai_confidence_score`: AI analysis confidence (0.0-1.0)
- `needs_manual_metadata`: Whether image needs manual metadata editing
- `is_manually_edited`: Whether image has been manually edited
- `last_edited_date`: Last manual edit timestamp
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- SQLite (for local development)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python run_server.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
Create a `.env` file in the backend directory:
```env
OPENROUTER_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///./photo_gallery.db
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=10
```

## Testing

### API Testing
The API includes comprehensive test coverage. Run tests with:
```bash
cd backend
pytest
```

### Manual Testing
Use the interactive API documentation at:
- Swagger UI: `http://127.0.0.1:8002/docs`
- ReDoc: `http://127.0.0.1:8002/redoc`

## Deployment

### Local Development
Both frontend and backend run on localhost with hot reloading enabled.

### Production Considerations
- Use a production WSGI server (e.g., Gunicorn)
- Set up proper database (PostgreSQL recommended)
- Configure cloud storage (AWS S3, Google Cloud Storage)
- Implement authentication and authorization
- Set up monitoring and logging
- Configure HTTPS
- Implement rate limiting
- Set up backup strategies

## Support

For issues and questions:
1. Check the API documentation
2. Review error messages and status codes
3. Check server logs
4. Verify environment configuration
5. Test with the interactive API documentation

## Changelog

### Version 1.0.0
- Initial release
- Complete CRUD operations for images and categories
- AI-powered image analysis
- Advanced search and filtering
- Manual metadata editing
- File upload and management
- Comprehensive API documentation


