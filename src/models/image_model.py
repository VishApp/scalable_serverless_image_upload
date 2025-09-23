from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class ImageUploadRequest(BaseModel):
    """Request model for image upload"""
    title: Optional[str] = Field(None, max_length=200, description="Image title")
    description: Optional[str] = Field(None, max_length=1000, description="Image description")
    tags: Optional[List[str]] = Field(None, max_items=10, description="Image tags")
    user_id: str = Field(..., min_length=1, description="User ID who uploaded the image")

    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            for tag in v:
                if not tag.strip():
                    raise ValueError('Tags cannot be empty')
                if len(tag) > 50:
                    raise ValueError('Each tag must be less than 50 characters')
        return v

class ImageMetadata(BaseModel):
    """Image metadata model for DynamoDB"""
    image_id: str = Field(..., description="Unique image identifier")
    created_at: str = Field(..., description="ISO timestamp of creation")
    user_id: str = Field(..., description="User ID who uploaded the image")
    title: Optional[str] = Field(None, description="Image title")
    description: Optional[str] = Field(None, description="Image description")
    tags: Optional[List[str]] = Field(None, description="Image tags")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    format: str = Field(..., description="Image format")
    s3_key: str = Field(..., description="S3 object key")
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    updated_at: Optional[str] = Field(None, description="ISO timestamp of last update")

    @classmethod
    def create_new(cls, upload_request: ImageUploadRequest, file_name: str,
                   file_size: int, content_type: str, width: int, height: int,
                   format: str) -> "ImageMetadata":
        """Create new image metadata instance"""
        image_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        # Generate S3 key with organized structure
        date_path = datetime.utcnow().strftime('%Y/%m')
        s3_key = f"images/{date_path}/{image_id}.{format.lower()}"

        return cls(
            image_id=image_id,
            created_at=now,
            user_id=upload_request.user_id,
            title=upload_request.title,
            description=upload_request.description,
            tags=upload_request.tags,
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
            width=width,
            height=height,
            format=format,
            s3_key=s3_key
        )

class ImageResponse(BaseModel):
    """Response model for image data"""
    image_id: str
    created_at: str
    user_id: str
    title: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    file_name: str
    file_size: int
    content_type: str
    width: int
    height: int
    format: str
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

class ImageListResponse(BaseModel):
    """Response model for image list"""
    images: List[ImageResponse]
    total_count: int
    next_page_token: Optional[str] = None
    has_more: bool = False

class ImageListQuery(BaseModel):
    """Query parameters for listing images"""
    limit: int = Field(default=20, ge=1, le=100, description="Number of images to return")
    page_token: Optional[str] = Field(None, description="Pagination token")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    tags: Optional[str] = Field(None, description="Filter by tag")
    start_date: Optional[str] = Field(None, description="Filter images created after this date (ISO format)")
    end_date: Optional[str] = Field(None, description="Filter images created before this date (ISO format)")

class UploadResponse(BaseModel):
    """Response model for successful upload"""
    message: str
    image_id: str
    upload_url: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

class DeleteResponse(BaseModel):
    """Response model for delete operation"""
    message: str
    image_id: str