from typing import Optional, Dict, Any, List
import uuid
import base64
import json
from datetime import datetime
from src.utils.s3_client import S3Client
from src.utils.dynamodb_client import DynamoDBClient
from src.utils.validators import ImageValidator, MetadataValidator
from src.models.image_model import ImageMetadata, ImageUploadRequest, ImageResponse, ImageListResponse
import logging

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.s3_client = S3Client()
        self.dynamodb_client = DynamoDBClient()

    def _convert_dynamo_to_api_format(self, dynamo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DynamoDB data format to API format"""
        api_data = dynamo_data.copy()
        # Convert tags string back to list
        if api_data.get('tags') and isinstance(api_data['tags'], str):
            if api_data['tags'].strip():
                api_data['tags'] = [tag.strip() for tag in api_data['tags'].split(',') if tag.strip()]
            else:
                api_data['tags'] = []
        return api_data

    def upload_image(self, file_content: bytes, filename: str,
                    upload_request: ImageUploadRequest) -> Dict[str, Any]:
        """Upload image and store metadata"""
        try:
            # Validate file extension
            if not ImageValidator.validate_file_extension(filename):
                return {
                    'success': False,
                    'error': 'Invalid file extension. Allowed: jpg, jpeg, png, gif, webp'
                }

            # Validate file size
            if not ImageValidator.validate_file_size(len(file_content)):
                return {
                    'success': False,
                    'error': f'File size must be between 1KB and 10MB'
                }

            # Validate image content and extract metadata
            image_validation = ImageValidator.validate_image_content(file_content)
            if not image_validation['valid']:
                return {
                    'success': False,
                    'error': image_validation['error']
                }

            # Validate metadata
            title_validation = MetadataValidator.validate_title(upload_request.title)
            if not title_validation['valid']:
                return {'success': False, 'error': title_validation['error']}

            desc_validation = MetadataValidator.validate_description(upload_request.description)
            if not desc_validation['valid']:
                return {'success': False, 'error': desc_validation['error']}

            tags_validation = MetadataValidator.validate_tags(upload_request.tags)
            if not tags_validation['valid']:
                return {'success': False, 'error': tags_validation['error']}

            user_validation = MetadataValidator.validate_user_id(upload_request.user_id)
            if not user_validation['valid']:
                return {'success': False, 'error': user_validation['error']}

            # Create image metadata
            image_metadata = ImageMetadata.create_new(
                upload_request=upload_request,
                file_name=filename,
                file_size=len(file_content),
                content_type=f"image/{image_validation['format']}",
                width=image_validation['width'],
                height=image_validation['height'],
                format=image_validation['format']
            )

            # Upload to S3
            if not self.s3_client.upload_image(
                file_content=file_content,
                key=image_metadata.s3_key,
                content_type=image_metadata.content_type
            ):
                return {
                    'success': False,
                    'error': 'Failed to upload image to storage'
                }

            # Store metadata in DynamoDB
            # Convert data for DynamoDB storage (tags as string for GSI)
            dynamo_data = image_metadata.model_dump()
            if dynamo_data.get('tags'):
                # Convert tags list to comma-separated string for DynamoDB GSI
                dynamo_data['tags'] = ','.join(dynamo_data['tags'])
            else:
                dynamo_data['tags'] = ''

            if not self.dynamodb_client.put_image_metadata(dynamo_data):
                # Rollback S3 upload if DynamoDB fails
                self.s3_client.delete_image(image_metadata.s3_key)
                return {
                    'success': False,
                    'error': 'Failed to store image metadata'
                }

            return {
                'success': True,
                'image_id': image_metadata.image_id,
                'message': 'Image uploaded successfully'
            }

        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error during upload'
            }

    def get_image(self, image_id: str, include_download_url: bool = True) -> Dict[str, Any]:
        """Get image metadata and optionally generate download URL"""
        try:
            # Get metadata from DynamoDB
            metadata = self.dynamodb_client.get_image_metadata_by_id(image_id)
            if not metadata:
                return {
                    'success': False,
                    'error': 'Image not found'
                }

            # Check if image is deleted
            if metadata.get('is_deleted', False):
                return {
                    'success': False,
                    'error': 'Image not found'
                }

            # Convert DynamoDB format to API format
            api_metadata = self._convert_dynamo_to_api_format(metadata)

            # Create response
            image_response = ImageResponse(**api_metadata)

            # Generate download URL if requested
            if include_download_url:
                download_url = self.s3_client.generate_presigned_url(metadata['s3_key'])
                if download_url:
                    image_response.download_url = download_url

            return {
                'success': True,
                'image': image_response.model_dump()
            }

        except Exception as e:
            logger.error(f"Error getting image {image_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }

    def list_images(self, limit: int = 20, page_token: Optional[str] = None,
                   user_id: Optional[str] = None, tags: Optional[str] = None) -> Dict[str, Any]:
        """List images with optional filters"""
        try:
            last_evaluated_key = None
            if page_token:
                try:
                    # In production, you'd want to encrypt/sign this token
                    last_evaluated_key = json.loads(base64.b64decode(page_token).decode())
                except Exception:
                    return {
                        'success': False,
                        'error': 'Invalid page token'
                    }

            # Query images based on filters
            if user_id:
                result = self.dynamodb_client.query_images_by_user(
                    user_id=user_id,
                    limit=limit,
                    last_evaluated_key=last_evaluated_key
                )
            else:
                # Use scan with filter for tag searches since we need partial matching
                result = self.dynamodb_client.list_images(
                    limit=limit,
                    last_evaluated_key=last_evaluated_key,
                    user_id=user_id,
                    tags=tags
                )

            # Filter out deleted images
            active_images = [
                img for img in result['items']
                if not img.get('is_deleted', False)
            ]

            # Convert to response format
            image_responses = []
            for img in active_images:
                # Convert DynamoDB format to API format
                api_img = self._convert_dynamo_to_api_format(img)
                image_response = ImageResponse(**api_img)
                # Generate download URL
                download_url = self.s3_client.generate_presigned_url(img['s3_key'])
                if download_url:
                    image_response.download_url = download_url
                image_responses.append(image_response)

            # Generate next page token
            next_page_token = None
            if result['last_evaluated_key']:
                next_page_token = base64.b64encode(
                    json.dumps(result['last_evaluated_key']).encode()
                ).decode()

            return {
                'success': True,
                'images': [img.model_dump() for img in image_responses],
                'total_count': len(image_responses),
                'next_page_token': next_page_token,
                'has_more': result['last_evaluated_key'] is not None
            }

        except Exception as e:
            logger.error(f"Error listing images: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }

    def delete_image(self, image_id: str, user_id: str) -> Dict[str, Any]:
        """Delete image (soft delete)"""
        try:
            # Get image metadata
            metadata = self.dynamodb_client.get_image_metadata_by_id(image_id)
            if not metadata:
                return {
                    'success': False,
                    'error': 'Image not found'
                }

            # Check if user owns the image
            if metadata.get('user_id') != user_id:
                return {
                    'success': False,
                    'error': 'Unauthorized to delete this image'
                }

            # Check if already deleted
            if metadata.get('is_deleted', False):
                return {
                    'success': False,
                    'error': 'Image already deleted'
                }

            # Soft delete - update metadata
            updates = {
                'is_deleted': True,
                'updated_at': datetime.utcnow().isoformat()
            }

            if not self.dynamodb_client.update_image_metadata(
                image_id=image_id,
                created_at=metadata['created_at'],
                updates=updates
            ):
                return {
                    'success': False,
                    'error': 'Failed to delete image'
                }

            # Optional: Delete from S3 immediately or schedule for later cleanup
            # For now, we'll keep the S3 object for potential recovery

            return {
                'success': True,
                'message': 'Image deleted successfully',
                'image_id': image_id
            }

        except Exception as e:
            logger.error(f"Error deleting image {image_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Internal server error'
            }