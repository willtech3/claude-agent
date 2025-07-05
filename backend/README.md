# Claude Agent Backend

FastAPI-based serverless backend running on AWS Lambda.

## Development

```bash
# Install dependencies
uv sync

# Run locally with SAM
sam local start-api

# Run locally with Uvicorn (for development)
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Build for deployment
sam build
```

## Architecture

- FastAPI for API framework
- Deployed to AWS Lambda via SAM
- Uses SQS for async task processing
- PostgreSQL for data storage
- Redis for caching

## Environment Variables

Copy `.env.example` to `.env` and configure all required variables.

## API Documentation

When running locally, visit http://localhost:3001/docs for interactive API documentation.