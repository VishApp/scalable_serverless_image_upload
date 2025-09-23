import boto3
import os
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self):
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'instagram-images')
        self.endpoint_url = os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566')

        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'test'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'test'),
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )

    def upload_image(self, file_content: bytes, key: str, content_type: str = 'image/jpeg') -> bool:
        """Upload image to S3 bucket"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentType=content_type,
                ACL='public-read'
            )
            logger.info(f"Successfully uploaded image: {key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload image {key}: {str(e)}")
            return False

    def get_image(self, key: str) -> Optional[bytes]:
        """Get image from S3 bucket"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Failed to get image {key}: {str(e)}")
            return None

    def delete_image(self, key: str) -> bool:
        """Delete image from S3 bucket"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted image: {key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete image {key}: {str(e)}")
            return False

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for image access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {key}: {str(e)}")
            return None

    def generate_presigned_upload_url(self, key: str, expiration: int = 3600) -> Optional[Dict[str, Any]]:
        """Generate presigned URL for uploading"""
        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=key,
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"Failed to generate presigned upload URL for {key}: {str(e)}")
            return None

    def image_exists(self, key: str) -> bool:
        """Check if image exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False