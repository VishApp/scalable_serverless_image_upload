# Scalable Serverless Image Upload Service

A scalable serverless image upload, storage, and retrieval service built with FastAPI, AWS services, and LocalStack for local development.

## 🚀 Features

- **Image Upload**: Support for JPEG, PNG, GIF, WebP formats with metadata
- **Image Listing**: Paginated listing with filtering by user, tags, and date
- **Image Retrieval**: Get individual images with presigned download URLs
- **Image Deletion**: Soft delete with user authorization
- **Scalable Architecture**: Built on AWS serverless services
- **Local Development**: Complete LocalStack setup for offline development
- **Comprehensive Testing**: Unit tests with high coverage
- **API Documentation**: Interactive Swagger/ReDoc documentation

## 🏗️ Architecture

- **API Gateway**: HTTP API entry point
- **Lambda Functions**: Serverless compute with FastAPI
- **S3**: Object storage for images
- **DynamoDB**: NoSQL database for metadata with GSIs for efficient querying
- **LocalStack**: Local AWS service emulation

## 📋 Prerequisites

- Python 3.7+
- Docker and Docker Compose
- AWS CLI (for LocalStack)

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd scalable_serverless_image_upload
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start LocalStack

```bash
cd infrastructure
docker-compose up -d
```

Wait for LocalStack to start (about 30 seconds), then verify services:
```bash
docker-compose logs localstack
```

### 3. Install AWS CLI for LocalStack (if not installed)

```bash
pip install awscli-local
```

### 4. Verify LocalStack Setup

```bash
awslocal s3 ls
awslocal dynamodb list-tables
```

You should see:
- S3 bucket: `instagram-images-dev`
- DynamoDB table: `ImageMetadata-dev`

### 5. Run the Application

#### For Local Development:
```bash
cd ..
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### For Lambda Testing:
```bash
python -c "from src.main import handler; print('Lambda handler ready')"
```

### 6. Access the API

- **API Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📝 Usage Examples

### Upload an Image

```bash
curl -X POST "http://localhost:8000/images" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/image.jpg" \
  -F "user_id=user123" \
  -F "title=Beautiful Sunset" \
  -F "description=A stunning sunset over the mountains" \
  -F "tags=nature,sunset,mountains"
```

### List Images

```bash
# List all images
curl "http://localhost:8000/images"

# List with filters
curl "http://localhost:8000/images?user_id=user123&tags=nature&limit=10"

# List user images
curl "http://localhost:8000/users/user123/images"

# List by tag
curl "http://localhost:8000/tags/nature/images"
```

### Get Image Details

```bash
curl "http://localhost:8000/images/{image_id}"
```

### Get Download URL

```bash
curl "http://localhost:8000/images/{image_id}/download"
```

### Delete Image

```bash
curl -X DELETE "http://localhost:8000/images/{image_id}" \
  -H "X-User-Id: user123"
```

## 🧪 Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-cov pytest-mock httpx
```

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/test_utils/ tests/test_services/

# Integration tests
pytest tests/test_handlers/

# Specific test file
pytest tests/test_services/test_image_service.py -v
```

## 🏃‍♂️ Development Workflow

### 1. Start LocalStack Services

```bash
cd infrastructure
docker-compose up -d
```

### 2. Set Environment Variables

```bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566
export S3_BUCKET_NAME=instagram-images-dev
export DYNAMODB_TABLE_NAME=ImageMetadata-dev
```

### 3. Development Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## 📊 Project Structure

```
scalable_serverless_image_upload/
├── src/
│   ├── handlers/           # Individual Lambda handlers
│   ├── services/          # Business logic
│   ├── models/            # Pydantic data models
│   ├── utils/             # Utility classes
│   └── main.py            # Main FastAPI application
├── tests/                 # Comprehensive test suite
├── infrastructure/        # LocalStack and AWS setup
├── docs/                  # API documentation
├── requirements.txt       # Python dependencies
├── pytest.ini           # Test configuration
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | `test` | AWS access key (LocalStack) |
| `AWS_SECRET_ACCESS_KEY` | `test` | AWS secret key (LocalStack) |
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region |
| `AWS_ENDPOINT_URL` | `http://localhost:4566` | LocalStack endpoint |
| `S3_BUCKET_NAME` | `instagram-images-dev` | S3 bucket name |
| `DYNAMODB_TABLE_NAME` | `ImageMetadata-dev` | DynamoDB table name |

### File Constraints

- **Formats**: JPEG, PNG, GIF, WebP
- **Size**: 1KB - 10MB
- **Dimensions**: 50x50 - 4000x4000 pixels
- **Metadata**: Title (200 chars), Description (1000 chars), Tags (10 max, 50 chars each)

## 🚀 Deployment

### AWS Lambda Deployment

1. **Package the application:**
```bash
pip install -t package/ -r requirements.txt
cp -r src/ package/
cd package && zip -r ../deployment.zip . && cd ..
```

2. **Deploy with AWS CLI:**
```bash
aws lambda create-function \
  --function-name instagram-image-service \
  --runtime python3.9 \
  --role arn:aws:iam::account:role/lambda-role \
  --handler src.main.handler \
  --zip-file fileb://deployment.zip
```

3. **Configure API Gateway:**
- Create HTTP API
- Add Lambda integration
- Configure routes: `ANY /{proxy+}`

### Serverless Framework (Alternative)

```bash
npm install -g serverless
sls deploy
```

## 🔍 Monitoring and Observability

### Local Development

- **Logs**: Application logs via Python logging
- **Metrics**: Basic FastAPI metrics
- **Health**: `/health` endpoint

### Production Recommendations

- **AWS CloudWatch**: Lambda logs and metrics
- **AWS X-Ray**: Distributed tracing
- **Custom Metrics**: Business metrics via CloudWatch
- **Alarms**: Error rate and latency monitoring

## 🔒 Security Considerations

### Current Implementation

- Input validation and sanitization
- File type and size restrictions
- User authorization for delete operations
- Presigned URLs for secure downloads

### Production Enhancements

- **Authentication**: JWT or OAuth integration
- **Rate Limiting**: Per-user and IP-based limits
- **CORS**: Proper origin configuration
- **Encryption**: S3 encryption at rest
- **WAF**: Web Application Firewall
- **Secrets**: AWS Secrets Manager for credentials

## 🐛 Troubleshooting

### Common Issues

1. **LocalStack not starting:**
   ```bash
   docker-compose down
   docker-compose up -d
   docker-compose logs localstack
   ```

2. **Permission errors:**
   ```bash
   chmod +x infrastructure/setup-localstack.sh
   ```

3. **Module import errors:**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

4. **Tests failing:**
   ```bash
   pip install -e .
   pytest --verbose
   ```

### Debug Mode

```bash
export DEBUG=1
python -m uvicorn src.main:app --reload --log-level debug
```

## 📚 API Documentation

Detailed API documentation is available at:
- **Interactive Docs**: http://localhost:8000/docs
- **Static Docs**: [docs/api-documentation.md](docs/api-documentation.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing issues
3. Create a new issue with detailed information