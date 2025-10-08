# AI Gateway MVP

A simple OpenAI-compatible AI Gateway that routes requests to multiple providers with cost tracking.

## Quick Start

### Prerequisites

You'll need Python 3.8+ and PostgreSQL installed on your macOS system.

### 1. Install Python Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Set up PostgreSQL

```bash
# Install PostgreSQL (if not already installed)
brew install postgresql

# Start PostgreSQL service
brew services start postgresql

# Create database
createdb ai_gateway
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp env.example .env

# Edit .env file with your settings
# You'll need to add your API keys for the providers
```

### 4. Set up Database Tables

```bash
# Create database tables
python setup.py
```

### 5. Run the Server

```bash
# Start the AI Gateway server
python -m app.main

# Or use uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at `http://localhost:8000`

## API Usage

### 1. Create a User (for testing)

```bash
curl -X POST "http://localhost:8000/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "api_key": "your-api-key-here"
  }'
```

### 2. Test Chat Completions

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-sonnet-4",
    "messages": [
      {
        "role": "user",
        "content": "Hello, world!"
      }
    ]
  }'
```

### 3. Test Embeddings

```bash
curl -X POST "http://localhost:8000/v1/embeddings" \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/text-embedding-3-small",
    "input": "The quick brown fox jumps over the lazy dog"
  }'
```

### 4. List Available Models

```bash
curl -X GET "http://localhost:8000/v1/models" \
  -H "Authorization: Bearer your-api-key-here"
```

### 5. Check Credits

```bash
curl -X GET "http://localhost:8000/v1/credits" \
  -H "Authorization: Bearer your-api-key-here"
```

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `VERCEL_AI_GATEWAY_API_KEY`: Your Vercel AI Gateway API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `API_SECRET_KEY`: Secret key for JWT tokens
- `API_KEY_HASH_SALT`: Salt for API key hashing

### Provider Configuration

The gateway supports three providers:
1. **Vercel AI Gateway** (primary)
2. **OpenAI Direct** (fallback)
3. **Anthropic Direct** (fallback)

## Features

- ✅ OpenAI-compatible API endpoints
- ✅ Multi-provider routing with failover
- ✅ Cost tracking and logging
- ✅ User authentication
- ✅ Credit balance tracking
- ✅ Generation lookup
- ✅ Model listing

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Make sure PostgreSQL is running
   - Check your DATABASE_URL in .env file

2. **Provider API Errors**
   - Verify your API keys are correct
   - Check if you have sufficient credits with providers

3. **Import Errors**
   - Make sure you're in the project directory
   - Install all dependencies with `pip install -r requirements.txt`

### Logs

The server logs all requests and errors. Check the console output for debugging information.

## Next Steps

This is an MVP. For production use, consider:

- Adding Redis for caching and rate limiting
- Implementing proper error handling and retries
- Adding monitoring and alerting
- Setting up proper deployment infrastructure
- Adding more providers and advanced routing logic
