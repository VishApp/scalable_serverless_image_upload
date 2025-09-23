# Instagram-like Image Service API Documentation

## Overview

This API provides scalable image upload, storage, and retrieval services similar to Instagram's core functionality. It supports image upload with metadata, listing with filters, individual image retrieval, and deletion.

## Base URL

- **Local Development**: `http://localhost:8000`
- **LocalStack**: `http://localhost:4566`

## Authentication

The API uses header-based authentication:
- **X-User-Id**: Required for delete operations

## API Endpoints

### Health Check

#### `GET /health`

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "instagram-image-service",
  "version": "1.0.0"
}
```

### Image Upload

#### `POST /images`

Upload an image with metadata.

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (required): Image file (JPEG, PNG, GIF, WebP)
- `user_id` (required): User ID who owns the image
- `title` (optional): Image title (max 200 characters)
- `description` (optional): Image description (max 1000 characters)
- `tags` (optional): Comma-separated tags (max 10 tags, 50 chars each)

**Example Request:**
```bash
curl -X POST "http://localhost:8000/images" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@image.jpg" \
  -F "user_id=user123" \
  -F "title=Beautiful Sunset" \
  -F "description=A stunning sunset over the mountains" \
  -F "tags=nature,sunset,mountains"
```

**Success Response (200):**
```json
{
  "message": "Image uploaded successfully",
  "image_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file, validation error
- `500 Internal Server Error`: Server error

### List Images

#### `GET /images`

List images with optional filters and pagination.

**Query Parameters:**
- `limit` (optional): Number of images to return (1-100, default: 20)
- `page_token` (optional): Pagination token for next page
- `user_id` (optional): Filter by user ID
- `tags` (optional): Filter by tag
- `start_date` (optional): Filter images created after date (ISO format)
- `end_date` (optional): Filter images created before date (ISO format)

**Example Request:**
```bash
curl "http://localhost:8000/images?limit=10&user_id=user123&tags=nature"
```

**Success Response (200):**
```json
{
  "images": [
    {
      "image_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2023-01-01T12:00:00Z",
      "user_id": "user123",
      "title": "Beautiful Sunset",
      "description": "A stunning sunset over the mountains",
      "tags": ["nature", "sunset", "mountains"],
      "file_name": "sunset.jpg",
      "file_size": 2048576,
      "content_type": "image/jpeg",
      "width": 1920,
      "height": 1080,
      "format": "jpeg",
      "download_url": "https://presigned-url.amazonaws.com/image.jpg",
      "thumbnail_url": null
    }
  ],
  "total_count": 1,
  "next_page_token": "eyJrZXkiOiJ2YWx1ZSJ9",
  "has_more": false
}
```

### Get Specific Image

#### `GET /images/{image_id}`

Get metadata and download URL for a specific image.

**Path Parameters:**
- `image_id` (required): Unique image identifier

**Query Parameters:**
- `include_url` (optional): Include download URL (default: true)

**Example Request:**
```bash
curl "http://localhost:8000/images/550e8400-e29b-41d4-a716-446655440000"
```

**Success Response (200):**
```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2023-01-01T12:00:00Z",
  "user_id": "user123",
  "title": "Beautiful Sunset",
  "description": "A stunning sunset over the mountains",
  "tags": ["nature", "sunset", "mountains"],
  "file_name": "sunset.jpg",
  "file_size": 2048576,
  "content_type": "image/jpeg",
  "width": 1920,
  "height": 1080,
  "format": "jpeg",
  "download_url": "https://presigned-url.amazonaws.com/image.jpg"
}
```

**Error Responses:**
- `404 Not Found`: Image not found or deleted

### Get Download URL

#### `GET /images/{image_id}/download`

Get a presigned download URL for direct image access.

**Path Parameters:**
- `image_id` (required): Unique image identifier

**Query Parameters:**
- `expires_in` (optional): URL expiration time in seconds (60-86400, default: 3600)

**Example Request:**
```bash
curl "http://localhost:8000/images/550e8400-e29b-41d4-a716-446655440000/download?expires_in=7200"
```

**Success Response (200):**
```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "download_url": "https://presigned-url.amazonaws.com/image.jpg",
  "expires_in": 7200,
  "content_type": "image/jpeg",
  "file_size": 2048576
}
```

### Delete Image

#### `DELETE /images/{image_id}`

Soft delete an image (only the owner can delete).

**Path Parameters:**
- `image_id` (required): Unique image identifier

**Headers:**
- `X-User-Id` (required): User ID for authorization

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/images/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-User-Id: user123"
```

**Success Response (200):**
```json
{
  "message": "Image deleted successfully",
  "image_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**
- `403 Forbidden`: Unauthorized to delete
- `404 Not Found`: Image not found
- `410 Gone`: Image already deleted

### List User Images

#### `GET /users/{user_id}/images`

List all images for a specific user.

**Path Parameters:**
- `user_id` (required): User ID

**Query Parameters:**
- `limit` (optional): Number of images to return (1-100, default: 20)
- `page_token` (optional): Pagination token

**Example Request:**
```bash
curl "http://localhost:8000/users/user123/images?limit=20"
```

### List Images by Tag

#### `GET /tags/{tag}/images`

List all images with a specific tag.

**Path Parameters:**
- `tag` (required): Tag name

**Query Parameters:**
- `limit` (optional): Number of images to return (1-100, default: 20)
- `page_token` (optional): Pagination token

**Example Request:**
```bash
curl "http://localhost:8000/tags/nature/images"
```

## Error Handling

### Standard Error Response Format

```json
{
  "error": "Error Type",
  "message": "Detailed error message",
  "details": {
    "field": "Additional error context"
  }
}
```

### HTTP Status Codes

- `200 OK`: Successful operation
- `400 Bad Request`: Invalid request or validation error
- `403 Forbidden`: Unauthorized access
- `404 Not Found`: Resource not found
- `410 Gone`: Resource deleted
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing:
- Per-user rate limits
- IP-based rate limits
- Upload size limits per user

## File Constraints

### Supported Formats
- JPEG/JPG
- PNG
- GIF
- WebP

### Size Limits
- **Minimum**: 1KB
- **Maximum**: 10MB

### Dimension Limits
- **Minimum**: 50x50 pixels
- **Maximum**: 4000x4000 pixels

### Metadata Limits
- **Title**: 200 characters
- **Description**: 1000 characters
- **Tags**: Maximum 10 tags, 50 characters each
- **Tag format**: Letters, numbers, spaces, hyphens, underscores only

## Interactive Documentation

When running the service, interactive API documentation is available:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Examples

### Complete Upload Workflow

1. **Upload Image:**
```bash
curl -X POST "http://localhost:8000/images" \
  -F "file=@vacation.jpg" \
  -F "user_id=user123" \
  -F "title=Beach Vacation" \
  -F "tags=beach,vacation,summer"
```

2. **List My Images:**
```bash
curl "http://localhost:8000/users/user123/images"
```

3. **Get Download URL:**
```bash
curl "http://localhost:8000/images/{image_id}/download"
```

4. **Delete Image:**
```bash
curl -X DELETE "http://localhost:8000/images/{image_id}" \
  -H "X-User-Id: user123"
```

### Search and Filter Examples

1. **Search by Tag:**
```bash
curl "http://localhost:8000/tags/beach/images"
```

2. **List with Pagination:**
```bash
# First page
curl "http://localhost:8000/images?limit=5"

# Next page (using token from previous response)
curl "http://localhost:8000/images?limit=5&page_token=eyJrZXkiOiJ2YWx1ZSJ9"
```

3. **Filter by User and Tag:**
```bash
curl "http://localhost:8000/images?user_id=user123&tags=vacation"
```