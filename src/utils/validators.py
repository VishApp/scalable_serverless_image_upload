import re
from typing import List, Optional, Dict, Any
from PIL import Image
import io

class ImageValidator:
    """Validator for image uploads and metadata"""

    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png',
        'image/gif', 'image/webp'
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MIN_FILE_SIZE = 1024  # 1KB
    MAX_DIMENSION = 4000  # 4000px
    MIN_DIMENSION = 50   # 50px

    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """Validate file extension"""
        if not filename:
            return False

        extension = filename.lower().split('.')[-1]
        return extension in ImageValidator.ALLOWED_EXTENSIONS

    @staticmethod
    def validate_mime_type(mime_type: str) -> bool:
        """Validate MIME type"""
        return mime_type.lower() in ImageValidator.ALLOWED_MIME_TYPES

    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Validate file size"""
        return ImageValidator.MIN_FILE_SIZE <= file_size <= ImageValidator.MAX_FILE_SIZE

    @staticmethod
    def validate_image_content(file_content: bytes) -> Dict[str, Any]:
        """Validate image content and extract metadata"""
        try:
            image = Image.open(io.BytesIO(file_content))
            width, height = image.size
            format_type = image.format.lower() if image.format else 'unknown'

            # Validate dimensions
            if (width < ImageValidator.MIN_DIMENSION or
                height < ImageValidator.MIN_DIMENSION or
                width > ImageValidator.MAX_DIMENSION or
                height > ImageValidator.MAX_DIMENSION):
                return {
                    'valid': False,
                    'error': f'Image dimensions must be between {ImageValidator.MIN_DIMENSION}px and {ImageValidator.MAX_DIMENSION}px'
                }

            return {
                'valid': True,
                'width': width,
                'height': height,
                'format': format_type,
                'mode': image.mode
            }

        except Exception as e:
            return {
                'valid': False,
                'error': f'Invalid image file: {str(e)}'
            }

class MetadataValidator:
    """Validator for image metadata"""

    MAX_TITLE_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_TAGS_COUNT = 10
    MAX_TAG_LENGTH = 50

    @staticmethod
    def validate_title(title: Optional[str]) -> Dict[str, Any]:
        """Validate image title"""
        if not title:
            return {'valid': True}  # Title is optional

        if len(title.strip()) == 0:
            return {'valid': False, 'error': 'Title cannot be empty'}

        if len(title) > MetadataValidator.MAX_TITLE_LENGTH:
            return {
                'valid': False,
                'error': f'Title must be less than {MetadataValidator.MAX_TITLE_LENGTH} characters'
            }

        return {'valid': True}

    @staticmethod
    def validate_description(description: Optional[str]) -> Dict[str, Any]:
        """Validate image description"""
        if not description:
            return {'valid': True}  # Description is optional

        if len(description) > MetadataValidator.MAX_DESCRIPTION_LENGTH:
            return {
                'valid': False,
                'error': f'Description must be less than {MetadataValidator.MAX_DESCRIPTION_LENGTH} characters'
            }

        return {'valid': True}

    @staticmethod
    def validate_tags(tags: Optional[List[str]]) -> Dict[str, Any]:
        """Validate image tags"""
        if not tags:
            return {'valid': True}  # Tags are optional

        if not isinstance(tags, list):
            return {'valid': False, 'error': 'Tags must be a list'}

        if len(tags) > MetadataValidator.MAX_TAGS_COUNT:
            return {
                'valid': False,
                'error': f'Maximum {MetadataValidator.MAX_TAGS_COUNT} tags allowed'
            }

        for tag in tags:
            if not isinstance(tag, str):
                return {'valid': False, 'error': 'Each tag must be a string'}

            if len(tag.strip()) == 0:
                return {'valid': False, 'error': 'Tags cannot be empty'}

            if len(tag) > MetadataValidator.MAX_TAG_LENGTH:
                return {
                    'valid': False,
                    'error': f'Each tag must be less than {MetadataValidator.MAX_TAG_LENGTH} characters'
                }

            # Validate tag format (alphanumeric and basic punctuation)
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', tag):
                return {
                    'valid': False,
                    'error': 'Tags can only contain letters, numbers, spaces, hyphens, and underscores'
                }

        return {'valid': True}

    @staticmethod
    def validate_user_id(user_id: Optional[str]) -> Dict[str, Any]:
        """Validate user ID"""
        if not user_id:
            return {'valid': False, 'error': 'User ID is required'}

        if not isinstance(user_id, str):
            return {'valid': False, 'error': 'User ID must be a string'}

        if len(user_id.strip()) == 0:
            return {'valid': False, 'error': 'User ID cannot be empty'}

        # Basic format validation (can be extended based on requirements)
        if not re.match(r'^[a-zA-Z0-9\-_]+$', user_id):
            return {
                'valid': False,
                'error': 'User ID can only contain letters, numbers, hyphens, and underscores'
            }

        return {'valid': True}

class QueryValidator:
    """Validator for query parameters"""

    MAX_LIMIT = 100
    MIN_LIMIT = 1

    @staticmethod
    def validate_limit(limit: Optional[int]) -> Dict[str, Any]:
        """Validate pagination limit"""
        if limit is None:
            return {'valid': True, 'value': 20}  # Default limit

        try:
            limit = int(limit)
            if limit < QueryValidator.MIN_LIMIT:
                return {'valid': False, 'error': f'Limit must be at least {QueryValidator.MIN_LIMIT}'}

            if limit > QueryValidator.MAX_LIMIT:
                return {'valid': False, 'error': f'Limit cannot exceed {QueryValidator.MAX_LIMIT}'}

            return {'valid': True, 'value': limit}
        except (ValueError, TypeError):
            return {'valid': False, 'error': 'Limit must be a valid integer'}

    @staticmethod
    def validate_last_evaluated_key(key: Optional[str]) -> Dict[str, Any]:
        """Validate pagination key"""
        if key is None:
            return {'valid': True, 'value': None}

        try:
            # In a real implementation, you might want to decrypt/decode this key
            # For now, we'll just check if it's a non-empty string
            if isinstance(key, str) and len(key.strip()) > 0:
                return {'valid': True, 'value': key}
            else:
                return {'valid': False, 'error': 'Invalid pagination key'}
        except Exception:
            return {'valid': False, 'error': 'Invalid pagination key format'}