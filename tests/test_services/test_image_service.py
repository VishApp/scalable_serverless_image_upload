import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io
from src.services.image_service import ImageService
from src.models.image_model import ImageUploadRequest

class TestImageService:
    """Test ImageService class"""

    @pytest.fixture
    def image_service(self):
        """Create ImageService instance with mocked dependencies"""
        with patch('src.services.image_service.S3Client') as mock_s3, \
             patch('src.services.image_service.DynamoDBClient') as mock_dynamo:
            service = ImageService()
            service.s3_client = mock_s3.return_value
            service.dynamodb_client = mock_dynamo.return_value
            return service

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes for testing"""
        img = Image.new('RGB', (200, 200), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        return img_bytes.getvalue()

    @pytest.fixture
    def sample_upload_request(self):
        """Create sample upload request"""
        return ImageUploadRequest(
            title="Test Image",
            description="A test image",
            tags=["test", "sample"],
            user_id="user123"
        )

    def test_upload_image_success(self, image_service, sample_image_bytes, sample_upload_request):
        """Test successful image upload"""
        # Mock S3 and DynamoDB success
        image_service.s3_client.upload_image.return_value = True
        image_service.dynamodb_client.put_image_metadata.return_value = True

        result = image_service.upload_image(
            file_content=sample_image_bytes,
            filename="test.jpg",
            upload_request=sample_upload_request
        )

        assert result['success'] is True
        assert 'image_id' in result
        assert result['message'] == 'Image uploaded successfully'

    def test_upload_image_invalid_extension(self, image_service, sample_image_bytes, sample_upload_request):
        """Test upload with invalid file extension"""
        result = image_service.upload_image(
            file_content=sample_image_bytes,
            filename="test.txt",
            upload_request=sample_upload_request
        )

        assert result['success'] is False
        assert 'Invalid file extension' in result['error']

    def test_upload_image_invalid_size(self, image_service, sample_upload_request):
        """Test upload with invalid file size"""
        # Create content that's too small
        small_content = b"small"

        result = image_service.upload_image(
            file_content=small_content,
            filename="test.jpg",
            upload_request=sample_upload_request
        )

        assert result['success'] is False
        assert 'File size must be' in result['error']

    def test_upload_image_s3_failure(self, image_service, sample_image_bytes, sample_upload_request):
        """Test upload when S3 fails"""
        # Mock S3 failure
        image_service.s3_client.upload_image.return_value = False

        result = image_service.upload_image(
            file_content=sample_image_bytes,
            filename="test.jpg",
            upload_request=sample_upload_request
        )

        assert result['success'] is False
        assert 'Failed to upload image to storage' in result['error']

    def test_upload_image_dynamodb_failure(self, image_service, sample_image_bytes, sample_upload_request):
        """Test upload when DynamoDB fails"""
        # Mock S3 success but DynamoDB failure
        image_service.s3_client.upload_image.return_value = True
        image_service.dynamodb_client.put_image_metadata.return_value = False
        image_service.s3_client.delete_image.return_value = True

        result = image_service.upload_image(
            file_content=sample_image_bytes,
            filename="test.jpg",
            upload_request=sample_upload_request
        )

        assert result['success'] is False
        assert 'Failed to store image metadata' in result['error']
        # Should have attempted rollback
        image_service.s3_client.delete_image.assert_called_once()

    def test_get_image_success(self, image_service):
        """Test successful image retrieval"""
        # Mock DynamoDB response
        mock_metadata = {
            'image_id': 'test123',
            'user_id': 'user123',
            'title': 'Test Image',
            's3_key': 'images/2023/01/test123.jpg',
            'created_at': '2023-01-01T00:00:00',
            'file_name': 'test.jpg',
            'file_size': 12345,
            'content_type': 'image/jpeg',
            'width': 200,
            'height': 200,
            'format': 'jpeg',
            'is_deleted': False
        }
        image_service.dynamodb_client.get_image_metadata_by_id.return_value = mock_metadata
        image_service.s3_client.generate_presigned_url.return_value = "https://presigned-url.com"

        result = image_service.get_image(image_id='test123')

        assert result['success'] is True
        assert result['image']['image_id'] == 'test123'
        assert result['image']['download_url'] == "https://presigned-url.com"

    def test_get_image_not_found(self, image_service):
        """Test image not found"""
        image_service.dynamodb_client.get_image_metadata_by_id.return_value = None

        result = image_service.get_image(image_id='nonexistent')

        assert result['success'] is False
        assert 'Image not found' in result['error']

    def test_get_image_deleted(self, image_service):
        """Test getting deleted image"""
        mock_metadata = {
            'image_id': 'test123',
            'is_deleted': True
        }
        image_service.dynamodb_client.get_image_metadata_by_id.return_value = mock_metadata

        result = image_service.get_image(image_id='test123')

        assert result['success'] is False
        assert 'Image not found' in result['error']

    def test_list_images_success(self, image_service):
        """Test successful image listing"""
        mock_images = [
            {
                'image_id': 'img1',
                'user_id': 'user123',
                's3_key': 'images/2023/01/img1.jpg',
                'created_at': '2023-01-01T00:00:00',
                'file_name': 'img1.jpg',
                'file_size': 12345,
                'content_type': 'image/jpeg',
                'width': 200,
                'height': 200,
                'format': 'jpeg',
                'is_deleted': False
            }
        ]
        image_service.dynamodb_client.list_images.return_value = {
            'items': mock_images,
            'last_evaluated_key': None,
            'count': 1
        }
        image_service.s3_client.generate_presigned_url.return_value = "https://presigned-url.com"

        result = image_service.list_images()

        assert result['success'] is True
        assert len(result['images']) == 1
        assert result['images'][0]['image_id'] == 'img1'

    def test_delete_image_success(self, image_service):
        """Test successful image deletion"""
        mock_metadata = {
            'image_id': 'test123',
            'user_id': 'user123',
            'created_at': '2023-01-01T00:00:00',
            'is_deleted': False
        }
        image_service.dynamodb_client.get_image_metadata_by_id.return_value = mock_metadata
        image_service.dynamodb_client.update_image_metadata.return_value = True

        result = image_service.delete_image(image_id='test123', user_id='user123')

        assert result['success'] is True
        assert result['message'] == 'Image deleted successfully'
        assert result['image_id'] == 'test123'

    def test_delete_image_not_found(self, image_service):
        """Test deleting non-existent image"""
        image_service.dynamodb_client.get_image_metadata_by_id.return_value = None

        result = image_service.delete_image(image_id='nonexistent', user_id='user123')

        assert result['success'] is False
        assert 'Image not found' in result['error']

    def test_delete_image_unauthorized(self, image_service):
        """Test deleting image by different user"""
        mock_metadata = {
            'image_id': 'test123',
            'user_id': 'other_user',
            'created_at': '2023-01-01T00:00:00',
            'is_deleted': False
        }
        image_service.dynamodb_client.get_image_metadata_by_id.return_value = mock_metadata

        result = image_service.delete_image(image_id='test123', user_id='user123')

        assert result['success'] is False
        assert 'Unauthorized' in result['error']

    def test_delete_image_already_deleted(self, image_service):
        """Test deleting already deleted image"""
        mock_metadata = {
            'image_id': 'test123',
            'user_id': 'user123',
            'created_at': '2023-01-01T00:00:00',
            'is_deleted': True
        }
        image_service.dynamodb_client.get_image_metadata_by_id.return_value = mock_metadata

        result = image_service.delete_image(image_id='test123', user_id='user123')

        assert result['success'] is False
        assert 'already deleted' in result['error']

    @patch('src.services.image_service.json')
    @patch('src.services.image_service.base64')
    def test_list_images_with_pagination(self, mock_base64, mock_json, image_service):
        """Test image listing with pagination"""
        # Mock page token decoding
        mock_base64.b64decode.return_value.decode.return_value = '{"key": "value"}'
        mock_json.loads.return_value = {"key": "value"}

        mock_images = []
        image_service.dynamodb_client.list_images.return_value = {
            'items': mock_images,
            'last_evaluated_key': {"next": "page"},
            'count': 0
        }

        # Mock encoding for next page token
        mock_json.dumps.return_value = '{"next": "page"}'
        mock_base64.b64encode.return_value.decode.return_value = "encoded_token"

        result = image_service.list_images(page_token="valid_token")

        assert result['success'] is True
        assert result['next_page_token'] == "encoded_token"
        assert result['has_more'] is True