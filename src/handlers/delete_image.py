from fastapi import FastAPI, Path, HTTPException, Header
from mangum import Mangum
import logging
from typing import Optional
from src.services.image_service import ImageService
from src.models.image_model import DeleteResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Image Delete Service",
    description="Delete images",
    version="1.0.0"
)

image_service = ImageService()

@app.delete("/images/{image_id}", response_model=DeleteResponse)
async def delete_image(
    image_id: str = Path(..., description="Unique image identifier"),
    x_user_id: str = Header(..., description="User ID from authentication header")
):
    """Delete an image (soft delete)"""
    try:
        result = image_service.delete_image(
            image_id=image_id,
            user_id=x_user_id
        )

        if not result['success']:
            if 'not found' in result['error'].lower():
                raise HTTPException(
                    status_code=404,
                    detail=result['error']
                )
            elif 'unauthorized' in result['error'].lower():
                raise HTTPException(
                    status_code=403,
                    detail=result['error']
                )
            elif 'already deleted' in result['error'].lower():
                raise HTTPException(
                    status_code=410,  # Gone
                    detail=result['error']
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=result['error']
                )

        return DeleteResponse(
            message=result['message'],
            image_id=result['image_id']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in delete_image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.delete("/images/{image_id}/permanent")
async def permanently_delete_image(
    image_id: str = Path(..., description="Unique image identifier"),
    x_user_id: str = Header(..., description="User ID from authentication header"),
    confirmation: str = Header(..., description="Must be 'PERMANENT_DELETE' to confirm")
):
    """Permanently delete an image (hard delete - removes from S3 and DynamoDB)"""
    try:
        # Require explicit confirmation
        if confirmation != "PERMANENT_DELETE":
            raise HTTPException(
                status_code=400,
                detail="Missing or invalid confirmation header"
            )

        # First perform soft delete
        result = image_service.delete_image(
            image_id=image_id,
            user_id=x_user_id
        )

        if not result['success']:
            # Handle cases where image might already be soft deleted
            if 'already deleted' not in result['error'].lower():
                if 'not found' in result['error'].lower():
                    raise HTTPException(
                        status_code=404,
                        detail=result['error']
                    )
                elif 'unauthorized' in result['error'].lower():
                    raise HTTPException(
                        status_code=403,
                        detail=result['error']
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=result['error']
                    )

        # TODO: Implement permanent deletion from S3 and DynamoDB
        # This would typically be done by a background job for safety
        logger.info(f"Permanent deletion requested for image {image_id} by user {x_user_id}")

        return {
            "message": "Image marked for permanent deletion",
            "image_id": image_id,
            "note": "Permanent deletion will be processed by background job"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in permanently_delete_image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "delete"}

# Lambda handler
handler = Mangum(app, lifespan="off")