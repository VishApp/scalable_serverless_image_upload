from fastapi import FastAPI, Path, HTTPException, Query
from mangum import Mangum
import logging
from typing import Optional
from src.services.image_service import ImageService
from src.models.image_model import ImageResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Image Retrieval Service",
    description="Get individual images and metadata",
    version="1.0.0",
)

image_service = ImageService()


@app.get("/images/{image_id}", response_model=ImageResponse)
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


@app.get("/images/{image_id}/download")
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


@app.get("/images/{image_id}/metadata")
async def get_image_metadata(
    image_id: str = Path(..., description="Unique image identifier")
):
    """Get only image metadata without download URL"""
    try:
        result = image_service.get_image(image_id=image_id, include_download_url=False)

        if not result["success"]:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=400, detail=result["error"])

        # Remove s3_key from response for security
        image_data = result["image"].copy()
        image_data.pop("s3_key", None)

        return image_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_image_metadata: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "get"}


# Lambda handler
handler = Mangum(app, lifespan="off")
