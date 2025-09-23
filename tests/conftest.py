import pytest
import os
from unittest.mock import patch


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables"""
    test_env = {
        "AWS_ACCESS_KEY_ID": "test",
        "AWS_SECRET_ACCESS_KEY": "test",
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_ENDPOINT_URL": "http://localhost:4566",
        "S3_BUCKET_NAME": "test-bucket",
        "DYNAMODB_TABLE_NAME": "test-table",
    }

    with patch.dict(os.environ, test_env):
        yield


@pytest.fixture
def mock_aws_services():
    """Mock AWS services for testing"""
    with patch("boto3.client") as mock_client, patch("boto3.resource") as mock_resource:
        yield {"client": mock_client, "resource": mock_resource}
