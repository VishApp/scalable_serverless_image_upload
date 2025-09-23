import pytest
from src.utils.validators import ImageValidator, MetadataValidator, QueryValidator
from PIL import Image
import io

class TestImageValidator:
    """Test ImageValidator class"""

    def test_validate_file_extension_valid(self):
        """Test valid file extensions"""
        valid_extensions = ['image.jpg', 'image.jpeg', 'image.png', 'image.gif', 'image.webp']
        for filename in valid_extensions:
            assert ImageValidator.validate_file_extension(filename) is True

    def test_validate_file_extension_invalid(self):
        """Test invalid file extensions"""
        invalid_extensions = ['image.txt', 'image.pdf', 'image.doc', 'noextension', '']
        for filename in invalid_extensions:
            assert ImageValidator.validate_file_extension(filename) is False

    def test_validate_mime_type_valid(self):
        """Test valid MIME types"""
        valid_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        for mime_type in valid_types:
            assert ImageValidator.validate_mime_type(mime_type) is True

    def test_validate_mime_type_invalid(self):
        """Test invalid MIME types"""
        invalid_types = ['text/plain', 'application/pdf', 'video/mp4', '']
        for mime_type in invalid_types:
            assert ImageValidator.validate_mime_type(mime_type) is False

    def test_validate_file_size_valid(self):
        """Test valid file sizes"""
        valid_sizes = [1024, 5 * 1024 * 1024, 10 * 1024 * 1024]  # 1KB, 5MB, 10MB
        for size in valid_sizes:
            assert ImageValidator.validate_file_size(size) is True

    def test_validate_file_size_invalid(self):
        """Test invalid file sizes"""
        invalid_sizes = [500, 11 * 1024 * 1024]  # 500B, 11MB
        for size in invalid_sizes:
            assert ImageValidator.validate_file_size(size) is False

    def test_validate_image_content_valid(self):
        """Test valid image content"""
        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes = img_bytes.getvalue()

        result = ImageValidator.validate_image_content(img_bytes)
        assert result['valid'] is True
        assert result['width'] == 100
        assert result['height'] == 100
        assert result['format'] == 'jpeg'

    def test_validate_image_content_invalid(self):
        """Test invalid image content"""
        invalid_content = b"This is not an image"
        result = ImageValidator.validate_image_content(invalid_content)
        assert result['valid'] is False
        assert 'error' in result

    def test_validate_image_content_dimensions_too_small(self):
        """Test image with dimensions too small"""
        img = Image.new('RGB', (30, 30), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes = img_bytes.getvalue()

        result = ImageValidator.validate_image_content(img_bytes)
        assert result['valid'] is False
        assert 'dimensions' in result['error']

class TestMetadataValidator:
    """Test MetadataValidator class"""

    def test_validate_title_valid(self):
        """Test valid titles"""
        valid_titles = [None, "", "Short title", "A" * 200]
        for title in valid_titles:
            result = MetadataValidator.validate_title(title)
            assert result['valid'] is True

    def test_validate_title_invalid(self):
        """Test invalid titles"""
        # Title too long
        long_title = "A" * 201
        result = MetadataValidator.validate_title(long_title)
        assert result['valid'] is False

    def test_validate_description_valid(self):
        """Test valid descriptions"""
        valid_descriptions = [None, "Short description", "A" * 1000]
        for desc in valid_descriptions:
            result = MetadataValidator.validate_description(desc)
            assert result['valid'] is True

    def test_validate_description_invalid(self):
        """Test invalid descriptions"""
        # Description too long
        long_desc = "A" * 1001
        result = MetadataValidator.validate_description(long_desc)
        assert result['valid'] is False

    def test_validate_tags_valid(self):
        """Test valid tags"""
        valid_tags = [
            None,
            [],
            ["tag1", "tag2"],
            ["a" * 50]  # Max length tag
        ]
        for tags in valid_tags:
            result = MetadataValidator.validate_tags(tags)
            assert result['valid'] is True

    def test_validate_tags_invalid(self):
        """Test invalid tags"""
        invalid_tags = [
            "not a list",  # Not a list
            [""] * 11,  # Too many tags
            ["a" * 51],  # Tag too long
            [""],  # Empty tag
            ["tag with @special!"],  # Invalid characters
        ]
        for tags in invalid_tags:
            result = MetadataValidator.validate_tags(tags)
            assert result['valid'] is False

    def test_validate_user_id_valid(self):
        """Test valid user IDs"""
        valid_ids = ["user123", "user_123", "user-123"]
        for user_id in valid_ids:
            result = MetadataValidator.validate_user_id(user_id)
            assert result['valid'] is True

    def test_validate_user_id_invalid(self):
        """Test invalid user IDs"""
        invalid_ids = [None, "", "   ", "user@123", "user with spaces"]
        for user_id in invalid_ids:
            result = MetadataValidator.validate_user_id(user_id)
            assert result['valid'] is False

class TestQueryValidator:
    """Test QueryValidator class"""

    def test_validate_limit_valid(self):
        """Test valid limits"""
        valid_limits = [1, 20, 100]
        for limit in valid_limits:
            result = QueryValidator.validate_limit(limit)
            assert result['valid'] is True
            assert result['value'] == limit

    def test_validate_limit_default(self):
        """Test default limit"""
        result = QueryValidator.validate_limit(None)
        assert result['valid'] is True
        assert result['value'] == 20

    def test_validate_limit_invalid(self):
        """Test invalid limits"""
        invalid_limits = [0, 101, "not a number", -1]
        for limit in invalid_limits:
            result = QueryValidator.validate_limit(limit)
            assert result['valid'] is False

    def test_validate_last_evaluated_key_valid(self):
        """Test valid pagination keys"""
        valid_keys = [None, "valid_key_string"]
        for key in valid_keys:
            result = QueryValidator.validate_last_evaluated_key(key)
            assert result['valid'] is True

    def test_validate_last_evaluated_key_invalid(self):
        """Test invalid pagination keys"""
        invalid_keys = ["", "   "]
        for key in invalid_keys:
            result = QueryValidator.validate_last_evaluated_key(key)
            assert result['valid'] is False