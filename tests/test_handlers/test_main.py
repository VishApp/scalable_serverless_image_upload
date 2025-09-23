import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from src.main import app
import io
from PIL import Image


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing"""
    img = Image.new("RGB", (200, 200), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return ("test.jpg", img_bytes, "image/jpeg")


class TestMainAPI:
    """Test main FastAPI application"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "instagram-image-service"

    @patch("src.main.image_service")
    def test_upload_image_success(self, mock_service, client, sample_image_file):
        """Test successful image upload"""
        # Mock service response
        mock_service.upload_image.return_value = {
            "success": True,
            "image_id": "test123",
            "message": "Image uploaded successfully",
        }

        filename, file_content, content_type = sample_image_file

        response = client.post(
            "/images",
            files={"file": (filename, file_content, content_type)},
            data={
                "title": "Test Image",
                "description": "A test image",
                "tags": "test,sample",
                "user_id": "user123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Image uploaded successfully"
        assert data["image_id"] == "test123"

    def test_upload_image_invalid_file_type(self, client):
        """Test upload with invalid file type"""
        response = client.post(
            "/images",
            files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
            data={"user_id": "user123"},
        )

        assert response.status_code == 400
        response_data = response.json()
        assert "File must be an image" in response_data.get(
            "detail", response_data.get("message", "")
        )

    @patch("src.main.image_service")
    def test_upload_image_service_error(self, mock_service, client, sample_image_file):
        """Test upload with service error"""
        # Mock service error
        mock_service.upload_image.return_value = {
            "success": False,
            "error": "Service error",
        }

        filename, file_content, content_type = sample_image_file

        response = client.post(
            "/images",
            files={"file": (filename, file_content, content_type)},
            data={"user_id": "user123"},
        )

        assert response.status_code == 400
        response_data = response.json()
        assert "Service error" in response_data.get(
            "detail", response_data.get("message", "")
        )

    @patch("src.main.image_service")
    def test_list_images_success(self, mock_service, client):
        """Test successful image listing"""
        mock_service.list_images.return_value = {
            "success": True,
            "images": [
                {
                    "image_id": "img1",
                    "user_id": "user123",
                    "title": "Test Image",
                    "description": "Test description",
                    "tags": ["test", "sample"],
                    "created_at": "2023-01-01T00:00:00",
                    "file_name": "test.jpg",
                    "file_size": 12345,
                    "content_type": "image/jpeg",
                    "width": 200,
                    "height": 200,
                    "format": "jpeg",
                    "download_url": "https://example.com/image.jpg",
                }
            ],
            "total_count": 1,
            "next_page_token": None,
            "has_more": False,
        }

        response = client.get("/images")
        assert response.status_code == 200
        data = response.json()
        assert len(data["images"]) == 1
        assert data["images"][0]["image_id"] == "img1"

    def test_list_images_invalid_limit(self, client):
        """Test listing with invalid limit"""
        response = client.get("/images?limit=200")
        assert response.status_code == 422  # Validation error

    @patch("src.main.image_service")
    def test_get_image_success(self, mock_service, client):
        """Test successful image retrieval"""
        mock_service.get_image.return_value = {
            "success": True,
            "image": {
                "image_id": "test123",
                "user_id": "user123",
                "title": "Test Image",
                "description": "Test description",
                "tags": ["test", "sample"],
                "created_at": "2023-01-01T00:00:00",
                "file_name": "test.jpg",
                "file_size": 12345,
                "content_type": "image/jpeg",
                "width": 200,
                "height": 200,
                "format": "jpeg",
                "download_url": "https://example.com/image.jpg",
            },
        }

        response = client.get("/images/test123")
        assert response.status_code == 200
        data = response.json()
        assert data["image_id"] == "test123"

    @patch("src.main.image_service")
    def test_get_image_not_found(self, mock_service, client):
        """Test get non-existent image"""
        mock_service.get_image.return_value = {
            "success": False,
            "error": "Image not found",
        }

        response = client.get("/images/nonexistent")
        assert response.status_code == 404

    @patch("src.main.image_service")
    def test_get_download_url_success(self, mock_service, client):
        """Test successful download URL generation"""
        mock_service.get_image.return_value = {
            "success": True,
            "image": {
                "image_id": "test123",
                "user_id": "user123",
                "title": "Test Image",
                "description": "Test description",
                "tags": ["test", "sample"],
                "created_at": "2023-01-01T00:00:00",
                "file_name": "test.jpg",
                "s3_key": "images/test.jpg",
                "content_type": "image/jpeg",
                "width": 200,
                "height": 200,
                "format": "jpeg",
                "file_size": 12345,
            },
        }

        with patch("src.utils.s3_client.S3Client") as mock_s3_class:
            mock_s3 = mock_s3_class.return_value
            mock_s3.generate_presigned_url.return_value = "https://presigned-url.com"

            response = client.get("/images/test123/download")
            assert response.status_code == 200
            data = response.json()
            assert data["download_url"] == "https://presigned-url.com"

    @patch("src.main.image_service")
    def test_delete_image_success(self, mock_service, client):
        """Test successful image deletion"""
        mock_service.delete_image.return_value = {
            "success": True,
            "message": "Image deleted successfully",
            "image_id": "test123",
        }

        response = client.delete("/images/test123", headers={"X-User-Id": "user123"})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Image deleted successfully"

    @patch("src.main.image_service")
    def test_delete_image_unauthorized(self, mock_service, client):
        """Test unauthorized image deletion"""
        mock_service.delete_image.return_value = {
            "success": False,
            "error": "Unauthorized to delete this image",
        }

        response = client.delete("/images/test123", headers={"X-User-Id": "wrong_user"})
        assert response.status_code == 403

    @patch("src.main.image_service")
    def test_list_user_images(self, mock_service, client):
        """Test listing user-specific images"""
        mock_service.list_images.return_value = {
            "success": True,
            "images": [],
            "total_count": 0,
            "has_more": False,
        }

        response = client.get("/users/user123/images")
        assert response.status_code == 200

    @patch("src.main.image_service")
    def test_list_images_by_tag(self, mock_service, client):
        """Test listing images by tag"""
        mock_service.list_images.return_value = {
            "success": True,
            "images": [],
            "total_count": 0,
            "has_more": False,
        }

        response = client.get("/tags/nature/images")
        assert response.status_code == 200

    def test_missing_user_id_in_delete(self, client):
        """Test delete without user ID header"""
        response = client.delete("/images/test123")
        assert response.status_code == 422  # Missing required header
