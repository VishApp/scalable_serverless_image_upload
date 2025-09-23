from fastapi import FastAPI, File, UploadFile, Form, Query, Path, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import logging
from typing import Optional
from src.services.image_service import ImageService
from src.models.image_model import (
    ImageUploadRequest,
    UploadResponse,
    ImageResponse,
    ImageListResponse,
    DeleteResponse,
    ErrorResponse,
)
from src.utils.validators import QueryValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Instagram-like Image Service",
    description="A scalable image upload, storage, and retrieval service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
image_service = ImageService()


# Exception handler for custom errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Error", "message": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "instagram-image-service",
        "version": "1.0.0",
    }


# Upload image endpoint
@app.post("/images", response_model=UploadResponse, tags=["Images"])
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    title: Optional[str] = Form(None, description="Image title"),
    description: Optional[str] = Form(None, description="Image description"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    user_id: str = Form(..., description="User ID"),
):
    """Upload an image with metadata"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Read file content
        file_content = await file.read()

        # Parse tags
        parsed_tags = None
        if tags:
            parsed_tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Create upload request
        upload_request = ImageUploadRequest(
            title=title, description=description, tags=parsed_tags, user_id=user_id
        )

        # Upload image
        result = image_service.upload_image(
            file_content=file_content,
            filename=file.filename or "unknown.jpg",
            upload_request=upload_request,
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return UploadResponse(message=result["message"], image_id=result["image_id"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# List images endpoint
@app.get("/images", response_model=ImageListResponse, tags=["Images"])
async def list_images(
    limit: int = Query(
        default=20, ge=1, le=100, description="Number of images to return"
    ),
    page_token: Optional[str] = Query(
        None, description="Pagination token for next page"
    ),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    tags: Optional[str] = Query(None, description="Filter by tag"),
    start_date: Optional[str] = Query(
        None, description="Filter images created after this date (ISO format)"
    ),
    end_date: Optional[str] = Query(
        None, description="Filter images created before this date (ISO format)"
    ),
):
    """List images with optional filters"""
    try:
        # Validate limit
        limit_validation = QueryValidator.validate_limit(limit)
        if not limit_validation["valid"]:
            raise HTTPException(status_code=400, detail=limit_validation["error"])
        validated_limit = limit_validation["value"]

        # Validate page token
        token_validation = QueryValidator.validate_last_evaluated_key(page_token)
        if not token_validation["valid"]:
            raise HTTPException(status_code=400, detail=token_validation["error"])
        validated_token = token_validation["value"]

        # Get images
        result = image_service.list_images(
            limit=validated_limit,
            page_token=validated_token,
            user_id=user_id,
            tags=tags,
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return ImageListResponse(
            images=result["images"],
            total_count=result["total_count"],
            next_page_token=result.get("next_page_token"),
            has_more=result.get("has_more", False),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in list_images: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Get specific image endpoint
@app.get("/images/{image_id}", response_model=ImageResponse, tags=["Images"])
async def get_image(
    image_id: str = Path(..., description="Unique image identifier"),
    include_url: bool = Query(
        default=True, description="Include download URL in response"
    ),
):
    """Get image metadata and download URL"""
    try:
        result = image_service.get_image(
            image_id=image_id, include_download_url=include_url
        )

        if not result["success"]:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=400, detail=result["error"])

        return ImageResponse(**result["image"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_image: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Get download URL endpoint
@app.get("/images/{image_id}/download", tags=["Images"])
async def get_image_download_url(
    image_id: str = Path(..., description="Unique image identifier"),
    expires_in: int = Query(
        default=3600, ge=60, le=86400, description="URL expiration time in seconds"
    ),
):
    """Get presigned download URL for image"""
    try:
        # First check if image exists
        result = image_service.get_image(image_id=image_id, include_download_url=False)

        if not result["success"]:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=400, detail=result["error"])

        image_data = result["image"]

        # Generate presigned URL with custom expiration
        from src.utils.s3_client import S3Client

        s3_client = S3Client()
        download_url = s3_client.generate_presigned_url(
            key=image_data["s3_key"], expiration=expires_in
        )

        if not download_url:
            raise HTTPException(
                status_code=500, detail="Failed to generate download URL"
            )

        return {
            "image_id": image_id,
            "download_url": download_url,
            "expires_in": expires_in,
            "content_type": image_data["content_type"],
            "file_size": image_data["file_size"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_image_download_url: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Delete image endpoint
@app.delete("/images/{image_id}", response_model=DeleteResponse, tags=["Images"])
async def delete_image(
    image_id: str = Path(..., description="Unique image identifier"),
    x_user_id: str = Header(..., description="User ID from authentication header"),
):
    """Delete an image (soft delete)"""
    try:
        result = image_service.delete_image(image_id=image_id, user_id=x_user_id)

        if not result["success"]:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            elif "unauthorized" in result["error"].lower():
                raise HTTPException(status_code=403, detail=result["error"])
            elif "already deleted" in result["error"].lower():
                raise HTTPException(status_code=410, detail=result["error"])  # Gone
            else:
                raise HTTPException(status_code=400, detail=result["error"])

        return DeleteResponse(message=result["message"], image_id=result["image_id"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in delete_image: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# User-specific endpoints
@app.get("/users/{user_id}/images", response_model=ImageListResponse, tags=["Users"])
async def list_user_images(
    user_id: str = Path(..., description="User ID"),
    limit: int = Query(default=20, ge=1, le=100),
    page_token: Optional[str] = Query(None),
):
    """List images for a specific user"""
    try:
        result = image_service.list_images(
            limit=limit, page_token=page_token, user_id=user_id
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return ImageListResponse(
            images=result["images"],
            total_count=result["total_count"],
            next_page_token=result.get("next_page_token"),
            has_more=result.get("has_more", False),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in list_user_images: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Tag-specific endpoints
@app.get("/tags/{tag}/images", response_model=ImageListResponse, tags=["Tags"])
async def list_images_by_tag(
    tag: str = Path(..., description="Tag name"),
    limit: int = Query(default=20, ge=1, le=100),
    page_token: Optional[str] = Query(None),
):
    """List images with a specific tag"""
    try:
        result = image_service.list_images(limit=limit, page_token=page_token, tags=tag)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return ImageListResponse(
            images=result["images"],
            total_count=result["total_count"],
            next_page_token=result.get("next_page_token"),
            has_more=result.get("has_more", False),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in list_images_by_tag: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Lambda handler for AWS deployment
handler = Mangum(app, lifespan="off")

# For local development
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
