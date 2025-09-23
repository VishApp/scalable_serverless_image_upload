from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from mangum import Mangum
import logging
from typing import Optional
from src.services.image_service import ImageService
from src.models.image_model import ImageListResponse
from src.utils.validators import QueryValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Image List Service",
    description="List and search images",
    version="1.0.0"
)

image_service = ImageService()

@app.get("/images", response_model=ImageListResponse)
async def list_images(
    limit: int = Query(default=20, ge=1, le=100, description="Number of images to return"),
    page_token: Optional[str] = Query(None, description="Pagination token for next page"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    tags: Optional[str] = Query(None, description="Filter by tag"),
    start_date: Optional[str] = Query(None, description="Filter images created after this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter images created before this date (ISO format)")
):
    """List images with optional filters"""
    try:
        # Validate limit
        limit_validation = QueryValidator.validate_limit(limit)
        if not limit_validation['valid']:
            raise HTTPException(
                status_code=400,
                detail=limit_validation['error']
            )
        validated_limit = limit_validation['value']

        # Validate page token
        token_validation = QueryValidator.validate_last_evaluated_key(page_token)
        if not token_validation['valid']:
            raise HTTPException(
                status_code=400,
                detail=token_validation['error']
            )
        validated_token = token_validation['value']

        # Get images
        result = image_service.list_images(
            limit=validated_limit,
            page_token=validated_token,
            user_id=user_id,
            tags=tags
        )

        if not result['success']:
            raise HTTPException(
                status_code=400,
                detail=result['error']
            )

        return ImageListResponse(
            images=result['images'],
            total_count=result['total_count'],
            next_page_token=result.get('next_page_token'),
            has_more=result.get('has_more', False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in list_images: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/images/user/{user_id}")
async def list_user_images(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    page_token: Optional[str] = Query(None)
):
    """List images for a specific user"""
    try:
        result = image_service.list_images(
            limit=limit,
            page_token=page_token,
            user_id=user_id
        )

        if not result['success']:
            raise HTTPException(
                status_code=400,
                detail=result['error']
            )

        return ImageListResponse(
            images=result['images'],
            total_count=result['total_count'],
            next_page_token=result.get('next_page_token'),
            has_more=result.get('has_more', False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in list_user_images: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/images/tags/{tag}")
async def list_images_by_tag(
    tag: str,
    limit: int = Query(default=20, ge=1, le=100),
    page_token: Optional[str] = Query(None)
):
    """List images with a specific tag"""
    try:
        result = image_service.list_images(
            limit=limit,
            page_token=page_token,
            tags=tag
        )

        if not result['success']:
            raise HTTPException(
                status_code=400,
                detail=result['error']
            )

        return ImageListResponse(
            images=result['images'],
            total_count=result['total_count'],
            next_page_token=result.get('next_page_token'),
            has_more=result.get('has_more', False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in list_images_by_tag: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "list"}

# Lambda handler
handler = Mangum(app, lifespan="off")