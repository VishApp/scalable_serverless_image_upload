from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from mangum import Mangum
import json
import logging
from typing import Optional, List
from src.services.image_service import ImageService
from src.models.image_model import ImageUploadRequest, UploadResponse, ErrorResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Image Upload Service",
    description="Upload images with metadata",
    version="1.0.0"
)

image_service = ImageService()

@app.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    title: Optional[str] = Form(None, description="Image title"),
    description: Optional[str] = Form(None, description="Image description"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    user_id: str = Form(..., description="User ID")
):
    """Upload an image with metadata"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )

        # Read file content
        file_content = await file.read()

        # Parse tags
        parsed_tags = None
        if tags:
            parsed_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]

        # Create upload request
        upload_request = ImageUploadRequest(
            title=title,
            description=description,
            tags=parsed_tags,
            user_id=user_id
        )

        # Upload image
        result = image_service.upload_image(
            file_content=file_content,
            filename=file.filename or "unknown.jpg",
            upload_request=upload_request
        )

        if not result['success']:
            raise HTTPException(
                status_code=400,
                detail=result['error']
            )

        return UploadResponse(
            message=result['message'],
            image_id=result['image_id']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "upload"}

# Lambda handler
handler = Mangum(app, lifespan="off")