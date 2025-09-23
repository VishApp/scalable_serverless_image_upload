#!/bin/bash

echo "Setting up LocalStack services..."

# Wait for LocalStack to be ready
sleep 10

# Set AWS CLI to use LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566

# Create S3 bucket for images
echo "Creating S3 bucket..."
awslocal s3 mb s3://instagram-images-dev

# Configure S3 bucket for public read access (for development)
awslocal s3api put-bucket-cors --bucket instagram-images-dev --cors-configuration '{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "POST", "PUT", "DELETE"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}'

# Create DynamoDB table for image metadata
echo "Creating DynamoDB table..."
awslocal dynamodb create-table \
    --table-name ImageMetadata-dev \
    --attribute-definitions \
        AttributeName=image_id,AttributeType=S \
        AttributeName=created_at,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
        AttributeName=tags,AttributeType=S \
    --key-schema \
        AttributeName=image_id,KeyType=HASH \
        AttributeName=created_at,KeyType=RANGE \
    --global-secondary-indexes \
        'IndexName=UserIndex,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}' \
        'IndexName=TagsIndex,KeySchema=[{AttributeName=tags,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}' \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5

# Create IAM role for Lambda functions
echo "Creating IAM role for Lambda..."
awslocal iam create-role \
    --role-name lambda-execution-role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }'

# Attach policies to the Lambda role
awslocal iam attach-role-policy \
    --role-name lambda-execution-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

awslocal iam put-role-policy \
    --role-name lambda-execution-role \
    --policy-name S3DynamoDBAccess \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:GetObjectAcl",
                    "s3:PutObjectAcl"
                ],
                "Resource": "arn:aws:s3:::instagram-images-dev/*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [
                    "arn:aws:dynamodb:us-east-1:000000000000:table/ImageMetadata-dev",
                    "arn:aws:dynamodb:us-east-1:000000000000:table/ImageMetadata-dev/index/*"
                ]
            }
        ]
    }'

echo "LocalStack setup completed successfully!"
echo "Services available at: http://localhost:4566"
echo "S3 bucket: instagram-images-dev"
echo "DynamoDB table: ImageMetadata-dev"