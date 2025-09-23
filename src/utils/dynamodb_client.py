import boto3
import os
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DynamoDBClient:
    def __init__(self):
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'ImageMetadata')
        self.endpoint_url = os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566')

        self.dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'test'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'test'),
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )

        self.table = self.dynamodb.Table(self.table_name)

    def put_image_metadata(self, image_data: Dict[str, Any]) -> bool:
        """Store image metadata in DynamoDB"""
        try:
            self.table.put_item(Item=image_data)
            logger.info(f"Successfully stored metadata for image: {image_data.get('image_id')}")
            return True
        except ClientError as e:
            logger.error(f"Failed to store image metadata: {str(e)}")
            return False

    def get_image_metadata(self, image_id: str, created_at: str) -> Optional[Dict[str, Any]]:
        """Get image metadata by ID and creation timestamp"""
        try:
            response = self.table.get_item(
                Key={
                    'image_id': image_id,
                    'created_at': created_at
                }
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Failed to get image metadata for {image_id}: {str(e)}")
            return None

    def get_image_metadata_by_id(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Get image metadata by ID only (queries all timestamps for this ID)"""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('image_id').eq(image_id)
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except ClientError as e:
            logger.error(f"Failed to get image metadata for {image_id}: {str(e)}")
            return None

    def list_images(self, limit: int = 20, last_evaluated_key: Optional[Dict] = None,
                   user_id: Optional[str] = None, tags: Optional[str] = None) -> Dict[str, Any]:
        """List images with optional filters"""
        try:
            scan_kwargs = {
                'Limit': limit
            }

            if last_evaluated_key:
                scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

            filter_expressions = []

            if user_id:
                filter_expressions.append(Attr('user_id').eq(user_id))

            if tags:
                filter_expressions.append(Attr('tags').contains(tags))

            if filter_expressions:
                filter_expression = filter_expressions[0]
                for expr in filter_expressions[1:]:
                    filter_expression = filter_expression & expr
                scan_kwargs['FilterExpression'] = filter_expression

            response = self.table.scan(**scan_kwargs)

            return {
                'items': response.get('Items', []),
                'last_evaluated_key': response.get('LastEvaluatedKey'),
                'count': response.get('Count', 0)
            }
        except ClientError as e:
            logger.error(f"Failed to list images: {str(e)}")
            return {'items': [], 'last_evaluated_key': None, 'count': 0}

    def query_images_by_user(self, user_id: str, limit: int = 20,
                           last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """Query images by user using GSI"""
        try:
            query_kwargs = {
                'IndexName': 'UserIndex',
                'KeyConditionExpression': Key('user_id').eq(user_id),
                'Limit': limit,
                'ScanIndexForward': False  # Sort by created_at descending
            }

            if last_evaluated_key:
                query_kwargs['ExclusiveStartKey'] = last_evaluated_key

            response = self.table.query(**query_kwargs)

            return {
                'items': response.get('Items', []),
                'last_evaluated_key': response.get('LastEvaluatedKey'),
                'count': response.get('Count', 0)
            }
        except ClientError as e:
            logger.error(f"Failed to query images by user {user_id}: {str(e)}")
            return {'items': [], 'last_evaluated_key': None, 'count': 0}

    def query_images_by_tags(self, tags: str, limit: int = 20,
                           last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """Query images by tags using GSI"""
        try:
            query_kwargs = {
                'IndexName': 'TagsIndex',
                'KeyConditionExpression': Key('tags').eq(tags),
                'Limit': limit,
                'ScanIndexForward': False  # Sort by created_at descending
            }

            if last_evaluated_key:
                query_kwargs['ExclusiveStartKey'] = last_evaluated_key

            response = self.table.query(**query_kwargs)

            return {
                'items': response.get('Items', []),
                'last_evaluated_key': response.get('LastEvaluatedKey'),
                'count': response.get('Count', 0)
            }
        except ClientError as e:
            logger.error(f"Failed to query images by tags {tags}: {str(e)}")
            return {'items': [], 'last_evaluated_key': None, 'count': 0}

    def delete_image_metadata(self, image_id: str, created_at: str) -> bool:
        """Delete image metadata"""
        try:
            self.table.delete_item(
                Key={
                    'image_id': image_id,
                    'created_at': created_at
                }
            )
            logger.info(f"Successfully deleted metadata for image: {image_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete image metadata for {image_id}: {str(e)}")
            return False

    def update_image_metadata(self, image_id: str, created_at: str,
                            updates: Dict[str, Any]) -> bool:
        """Update image metadata"""
        try:
            update_expression_parts = []
            expression_attribute_values = {}

            for key, value in updates.items():
                update_expression_parts.append(f"{key} = :{key}")
                expression_attribute_values[f":{key}"] = value

            update_expression = "SET " + ", ".join(update_expression_parts)

            self.table.update_item(
                Key={
                    'image_id': image_id,
                    'created_at': created_at
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            logger.info(f"Successfully updated metadata for image: {image_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to update image metadata for {image_id}: {str(e)}")
            return False