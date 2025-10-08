# AI Gateway Product Requirements Document (PRD)

## 1. Executive Summary

### 1.1 Product Overview
The AI Gateway is a unified API service that replicates Vercel AI Gateway functionality while providing enhanced cost tracking and multi-provider routing capabilities. It serves as a transparent proxy that routes user requests to Vercel AI Gateway and two additional AI providers, maintaining full OpenAI API compatibility while implementing comprehensive internal cost tracking.

### 1.2 Key Objectives
- **Unified API Interface**: Provide a single OpenAI-compatible endpoint that abstracts multiple AI providers
- **Cost Transparency**: Implement detailed cost tracking and mapping for each request to provider-specific costs
- **High Availability**: Ensure robust failover and load balancing across providers
- **Seamless Integration**: Maintain 100% OpenAI API compatibility for existing client libraries
- **Analytics & Reporting**: Store comprehensive usage and cost data for analysis

### 1.3 Success Metrics
- 99.9% uptime with <100ms average latency overhead
- 100% OpenAI API compatibility score
- Real-time cost tracking with <1 second data availability
- Support for 10,000+ concurrent requests

## 2. Product Requirements

### 2.1 Functional Requirements

#### 2.1.1 OpenAI API Compatibility
The gateway MUST implement the complete OpenAI API specification including:

**Core Endpoints:**
- `GET /v1/models` - List available models across all providers
- `GET /v1/models/{model}` - Retrieve specific model information
- `POST /v1/chat/completions` - Chat completions with full feature support
- `POST /v1/embeddings` - Vector embeddings generation
- `GET /v1/credits` - Credit balance and usage information
- `GET /v1/generation` - Generation lookup by ID

**Advanced Features:**
- Streaming responses (Server-Sent Events)
- Tool/Function calling
- Image attachments and analysis
- PDF document processing
- Structured outputs (JSON schema)
- Reasoning configuration
- Provider options and routing preferences
- Image generation capabilities

#### 2.1.2 Request Routing System
- **Primary Provider**: Vercel AI Gateway (https://ai-gateway.vercel.sh/v1)
- **Secondary Providers**: Two additional AI providers (configurable)
- **Routing Logic**: 
  - Configurable provider priority order
  - Automatic failover on provider errors
  - Load balancing based on cost and performance
  - Provider-specific model mapping

#### 2.1.3 Cost Tracking System
- **Real-time Cost Calculation**: Map each request to provider-specific pricing
- **Detailed Logging**: Store request metadata, costs, and performance metrics
- **Cost Attribution**: Track costs by user, organization, and usage patterns
- **Provider Cost Mapping**: Maintain up-to-date pricing for all providers

#### 2.1.4 Authentication & Security
- **API Key Authentication**: Bearer token support
- **OIDC Token Support**: Vercel-compatible authentication
- **Rate Limiting**: Per-user and per-organization limits
- **Request Validation**: Input sanitization and validation

### 2.2 Non-Functional Requirements

#### 2.2.1 Performance
- **Latency**: <100ms overhead compared to direct provider calls
- **Throughput**: Support 10,000+ concurrent requests
- **Response Time**: 95th percentile <500ms for non-streaming requests
- **Streaming**: Real-time token delivery with <50ms latency

#### 2.2.2 Reliability
- **Uptime**: 99.9% availability target
- **Failover**: Automatic provider switching on errors
- **Error Handling**: Graceful degradation and informative error messages
- **Data Consistency**: ACID compliance for cost tracking data

#### 2.2.3 Scalability
- **Horizontal Scaling**: Auto-scaling based on load
- **Database Performance**: Optimized queries for cost tracking
- **Caching**: Intelligent caching for model lists and metadata
- **Resource Management**: Efficient memory and CPU utilization

## 3. Technical Architecture

### 3.1 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   AI Gateway     │    │   Providers     │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ OpenAI SDK  │ │◄──►│ │ API Gateway  │ │◄──►│ │ Vercel AI   │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ │ Gateway      │ │
│                 │    │                  │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ Custom Apps │ │    │ │ Cost Tracker │ │    │ │ Provider 2   │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
│                 │    │                  │    │ ┌─────────────┐ │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ │ Provider 3   │ │
│ │ REST Clients│ │    │ │ Router        │ │    │ └─────────────┘ │
│ └─────────────┘ │    │ └──────────────┘ │    │                 │
└─────────────────┘    │                  │    └─────────────────┘
                       │ ┌──────────────┐ │
                       │ │ Database     │ │
                       │ └──────────────┘ │
                       └──────────────────┘
```

### 3.2 Core Components

#### 3.2.1 API Gateway Layer
- **Request Handler**: Validates and processes incoming requests
- **Response Formatter**: Ensures OpenAI-compatible response format
- **Middleware Stack**: Authentication, rate limiting, logging
- **Error Handler**: Standardized error responses

#### 3.2.2 Routing Engine
- **Provider Selector**: Chooses optimal provider based on configuration
- **Load Balancer**: Distributes requests across providers
- **Failover Manager**: Handles provider failures and switching
- **Model Mapper**: Maps generic model names to provider-specific models

#### 3.2.3 Cost Tracking System
- **Cost Calculator**: Real-time cost calculation per request
- **Usage Tracker**: Records detailed usage metrics
- **Billing Engine**: Aggregates costs by user/organization
- **Analytics Processor**: Generates usage reports and insights

#### 3.2.4 Provider Adapters
- **Vercel Adapter**: Direct integration with Vercel AI Gateway
- **Provider 2 Adapter**: Custom adapter for second provider
- **Provider 3 Adapter**: Custom adapter for third provider
- **Generic Adapter**: Extensible framework for additional providers

### 3.3 Database Schema

#### 3.3.1 Core Tables

**Users Table**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    api_key_hash VARCHAR(255) UNIQUE NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Organizations Table**
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    billing_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Requests Table**
```sql
CREATE TABLE requests (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    request_type VARCHAR(50) NOT NULL, -- 'chat', 'embedding', etc.
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    latency_ms INTEGER,
    status VARCHAR(20) NOT NULL, -- 'success', 'error', 'timeout'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Provider Costs Table**
```sql
CREATE TABLE provider_costs (
    id UUID PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    input_cost_per_1k DECIMAL(10, 6),
    output_cost_per_1k DECIMAL(10, 6),
    effective_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Usage Analytics Table**
```sql
CREATE TABLE usage_analytics (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    date DATE NOT NULL,
    total_requests INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10, 2) DEFAULT 0,
    provider_breakdown JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3.3.2 Indexes for Performance
```sql
-- Performance indexes
CREATE INDEX idx_requests_user_id_created_at ON requests(user_id, created_at);
CREATE INDEX idx_requests_organization_id_created_at ON requests(organization_id, created_at);
CREATE INDEX idx_requests_provider_model ON requests(provider, model);
CREATE INDEX idx_usage_analytics_date_org ON usage_analytics(date, organization_id);
CREATE INDEX idx_provider_costs_provider_model ON provider_costs(provider, model);
```

## 4. API Specification

### 4.1 Base URL and Authentication

**Base URL**: `https://your-gateway.com/v1`

**Authentication**: 
- API Key: `Authorization: Bearer <api_key>`
- OIDC Token: `Authorization: Bearer <oidc_token>`

### 4.2 Core Endpoints

#### 4.2.1 List Models
```http
GET /v1/models
```

**Response Format**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "anthropic/claude-sonnet-4",
      "object": "model",
      "created": 1677610602,
      "owned_by": "anthropic"
    },
    {
      "id": "openai/gpt-4o",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai"
    }
  ]
}
```

#### 4.2.2 Chat Completions
```http
POST /v1/chat/completions
```

**Request Body**:
```json
{
  "model": "anthropic/claude-sonnet-4",
  "messages": [
    {
      "role": "user",
      "content": "Hello, world!"
    }
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response Format**:
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "anthropic/claude-sonnet-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 12,
    "total_tokens": 22
  },
  "providerMetadata": {
    "gateway": {
      "provider": "vercel",
      "cost": "0.000123",
      "latency": 150,
      "routing": {
        "selected_provider": "vercel",
        "fallback_providers": ["provider2", "provider3"]
      }
    }
  }
}
```

#### 4.2.3 Embeddings
```http
POST /v1/embeddings
```

**Request Body**:
```json
{
  "model": "openai/text-embedding-3-small",
  "input": "The quick brown fox jumps over the lazy dog"
}
```

**Response Format**:
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [-0.0038, 0.021, ...]
    }
  ],
  "model": "openai/text-embedding-3-small",
  "usage": {
    "prompt_tokens": 9,
    "total_tokens": 9
  },
  "providerMetadata": {
    "gateway": {
      "provider": "vercel",
      "cost": "0.000001",
      "latency": 45
    }
  }
}
```

#### 4.2.4 Credits
```http
GET /v1/credits
```

**Response Format**:
```json
{
  "balance": "95.50",
  "total_used": "4.50",
  "usage_breakdown": {
    "vercel": "2.30",
    "provider2": "1.20",
    "provider3": "1.00"
  }
}
```

#### 4.2.5 Generation Lookup
```http
GET /v1/generation?id={generation_id}
```

**Response Format**:
```json
{
  "data": {
    "id": "gen_01ARZ3NDEKTSV4RRFFQ69G5FAV",
    "total_cost": 0.00123,
    "usage": 0.00123,
    "created_at": "2024-01-01T00:00:00.000Z",
    "model": "anthropic/claude-sonnet-4",
    "provider_name": "vercel",
    "streamed": false,
    "latency": 200,
    "generation_time": 1500,
    "tokens_prompt": 100,
    "tokens_completion": 50
  }
}
```

### 4.3 Advanced Features

#### 4.3.1 Streaming Responses
Streaming follows OpenAI's Server-Sent Events (SSE) format:

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"anthropic/claude-sonnet-4","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"anthropic/claude-sonnet-4","choices":[{"index":0,"delta":{"content":" there"},"finish_reason":null}]}

data: [DONE]
```

#### 4.3.2 Tool Calling
```json
{
  "model": "anthropic/claude-sonnet-4",
  "messages": [
    {
      "role": "user",
      "content": "What's the weather like in San Francisco?"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "City name"
            }
          },
          "required": ["location"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

#### 4.3.3 Image Attachments
```json
{
  "model": "anthropic/claude-sonnet-4",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Describe this image"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD..."
          }
        }
      ]
    }
  ]
}
```

## 5. Cost Tracking System

### 5.1 Cost Calculation Logic

#### 5.1.1 Provider Pricing Models
Each provider maintains its own pricing structure:

**Vercel AI Gateway**:
- Inherits pricing from underlying providers
- Additional gateway fees (if any)

**Provider 2** (Example: OpenAI Direct):
- GPT-4o: $5.00/1M input tokens, $15.00/1M output tokens
- GPT-4o-mini: $0.15/1M input tokens, $0.60/1M output tokens

**Provider 3** (Example: Anthropic Direct):
- Claude Sonnet 4: $3.00/1M input tokens, $15.00/1M output tokens
- Claude Haiku: $0.25/1M input tokens, $1.25/1M output tokens

#### 5.1.2 Real-time Cost Calculation
```python
def calculate_cost(provider, model, input_tokens, output_tokens):
    pricing = get_provider_pricing(provider, model)
    
    input_cost = (input_tokens / 1000) * pricing['input_cost_per_1k']
    output_cost = (output_tokens / 1000) * pricing['output_cost_per_1k']
    
    total_cost = input_cost + output_cost
    return {
        'input_cost': input_cost,
        'output_cost': output_cost,
        'total_cost': total_cost,
        'provider': provider,
        'model': model
    }
```

### 5.2 Cost Tracking Implementation

#### 5.2.1 Request Lifecycle Tracking
1. **Request Received**: Log initial request metadata
2. **Provider Selected**: Record routing decision
3. **Provider Response**: Capture usage metrics and costs
4. **Response Sent**: Finalize cost calculation and logging

#### 5.2.2 Cost Attribution
- **User Level**: Track costs per individual user
- **Organization Level**: Aggregate costs per organization
- **Project Level**: Optional project-based cost tracking
- **Provider Level**: Compare costs across providers

### 5.3 Analytics and Reporting

#### 5.3.1 Real-time Dashboards
- Current usage and costs
- Provider performance metrics
- Cost trends and projections
- Error rates and failover events

#### 5.3.2 Historical Reports
- Daily, weekly, monthly usage summaries
- Cost breakdown by provider and model
- User and organization usage patterns
- Performance optimization insights

## 6. Implementation Plan

### 6.1 Development Phases

#### Phase 1: Core Infrastructure (Weeks 1-4)
- Set up basic API gateway structure
- Implement OpenAI-compatible endpoints
- Basic routing to Vercel AI Gateway
- Simple cost tracking

#### Phase 2: Multi-Provider Support (Weeks 5-8)
- Add Provider 2 and Provider 3 adapters
- Implement intelligent routing logic
- Advanced cost tracking system
- Database schema implementation

#### Phase 3: Advanced Features (Weeks 9-12)
- Streaming response support
- Tool calling implementation
- Image and file attachment support
- Structured outputs

#### Phase 4: Production Readiness (Weeks 13-16)
- Performance optimization
- Security hardening
- Monitoring and alerting
- Documentation and testing

### 6.2 Technology Stack

#### 6.2.1 Backend Framework
- **Language**: Python 3.11+
- **Framework**: FastAPI (for async support and automatic OpenAPI docs)
- **ASGI Server**: Uvicorn with Gunicorn workers

#### 6.2.2 Database
- **Primary**: PostgreSQL 15+ (for ACID compliance and complex queries)
- **Cache**: Redis (for session management and rate limiting)
- **Analytics**: ClickHouse (for high-volume analytics data)

#### 6.2.3 Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes for production deployment
- **Load Balancer**: NGINX or cloud load balancer
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging with ELK stack

#### 6.2.4 External Dependencies
- **HTTP Client**: httpx (async HTTP client)
- **Database ORM**: SQLAlchemy with async support
- **Authentication**: JWT tokens with OIDC support
- **Rate Limiting**: Redis-based rate limiting
- **Background Tasks**: Celery with Redis broker

### 6.3 Security Considerations

#### 6.3.1 Authentication & Authorization
- API key management with secure hashing
- OIDC token validation
- Rate limiting per user and organization
- Request signing for sensitive operations

#### 6.3.2 Data Protection
- Encryption at rest for sensitive data
- TLS 1.3 for all communications
- Input validation and sanitization
- SQL injection prevention

#### 6.3.3 Infrastructure Security
- Container security scanning
- Network segmentation
- Secrets management (HashiCorp Vault or cloud KMS)
- Regular security audits

## 7. Monitoring and Observability

### 7.1 Key Metrics

#### 7.1.1 Performance Metrics
- Request latency (p50, p95, p99)
- Throughput (requests per second)
- Error rates by endpoint and provider
- Provider response times

#### 7.1.2 Business Metrics
- Total requests processed
- Cost per request by provider
- User and organization usage patterns
- Provider utilization rates

#### 7.1.3 System Health Metrics
- CPU and memory utilization
- Database connection pool status
- Cache hit rates
- Queue depths for background tasks

### 7.2 Alerting Strategy

#### 7.2.1 Critical Alerts
- Service downtime or high error rates
- Database connectivity issues
- Provider API failures
- Unusual cost spikes

#### 7.2.2 Warning Alerts
- High latency trends
- Rate limit approaching
- Storage capacity warnings
- Performance degradation

## 8. Testing Strategy

### 8.1 Test Types

#### 8.1.1 Unit Tests
- Individual component testing
- Cost calculation accuracy
- Request validation logic
- Provider adapter functionality

#### 8.1.2 Integration Tests
- End-to-end API testing
- Database integration
- Provider API integration
- Authentication flow testing

#### 8.1.3 Performance Tests
- Load testing with realistic traffic
- Stress testing for failure scenarios
- Latency benchmarking
- Cost tracking accuracy under load

#### 8.1.4 Compatibility Tests
- OpenAI SDK compatibility
- Various client library testing
- Streaming response validation
- Error response format verification

### 8.2 Test Data Management
- Synthetic test data generation
- Provider API mocking for testing
- Database test fixtures
- Performance baseline establishment

## 9. Deployment Strategy

### 9.1 Environment Setup

#### 9.1.1 Development Environment
- Local Docker Compose setup
- Mock provider APIs for development
- Test database with sample data
- Hot reloading for rapid development

#### 9.1.2 Staging Environment
- Production-like infrastructure
- Real provider API integration
- Performance testing environment
- User acceptance testing

#### 9.1.3 Production Environment
- High availability deployment
- Auto-scaling configuration
- Disaster recovery setup
- Continuous monitoring

### 9.2 CI/CD Pipeline

#### 9.2.1 Continuous Integration
- Automated testing on every commit
- Code quality checks (linting, formatting)
- Security vulnerability scanning
- Dependency updates

#### 9.2.2 Continuous Deployment
- Automated deployment to staging
- Manual approval for production
- Blue-green deployment strategy
- Rollback capabilities

## 10. Success Criteria and KPIs

### 10.1 Technical KPIs
- **API Compatibility**: 100% OpenAI API compliance
- **Performance**: <100ms latency overhead
- **Reliability**: 99.9% uptime
- **Scalability**: 10,000+ concurrent requests

### 10.2 Business KPIs
- **Cost Accuracy**: 99.9% cost tracking accuracy
- **User Adoption**: Successful migration from direct provider usage
- **Provider Utilization**: Balanced usage across providers
- **Cost Optimization**: 10-20% cost savings through intelligent routing

### 10.3 Quality KPIs
- **Error Rate**: <0.1% error rate
- **Response Time**: 95th percentile <500ms
- **Data Accuracy**: 100% cost attribution accuracy
- **Security**: Zero security incidents

## 11. Risk Assessment and Mitigation

### 11.1 Technical Risks

#### 11.1.1 Provider API Changes
- **Risk**: Provider APIs may change, breaking compatibility
- **Mitigation**: Version pinning, adapter pattern, monitoring

#### 11.1.2 Performance Bottlenecks
- **Risk**: High latency or throughput issues
- **Mitigation**: Performance testing, caching, optimization

#### 11.1.3 Data Consistency
- **Risk**: Cost tracking data inconsistencies
- **Mitigation**: ACID transactions, data validation, reconciliation

### 11.2 Business Risks

#### 11.2.1 Provider Dependency
- **Risk**: Over-reliance on single provider
- **Mitigation**: Multi-provider strategy, failover mechanisms

#### 11.2.2 Cost Accuracy
- **Risk**: Incorrect cost calculations
- **Mitigation**: Regular pricing updates, validation checks

#### 11.2.3 Security Breaches
- **Risk**: Unauthorized access to API keys or data
- **Mitigation**: Security best practices, regular audits

## 12. Future Enhancements

### 12.1 Short-term Enhancements (3-6 months)
- Additional AI providers integration
- Advanced analytics dashboard
- Cost optimization recommendations
- A/B testing framework

### 12.2 Medium-term Enhancements (6-12 months)
- Machine learning-based routing optimization
- Custom model fine-tuning support
- Advanced security features (encryption, audit logs)
- Multi-region deployment

### 12.3 Long-term Enhancements (12+ months)
- AI-powered cost prediction
- Automated provider negotiation
- Enterprise features (SSO, advanced reporting)
- Global edge deployment

## 13. Conclusion

This AI Gateway PRD outlines a comprehensive solution for creating a unified, OpenAI-compatible API that routes requests to multiple AI providers while providing detailed cost tracking and analytics. The system is designed for high performance, reliability, and scalability while maintaining full compatibility with existing OpenAI client libraries.

The implementation plan provides a clear roadmap for development, with phased delivery ensuring early value while building toward a production-ready system. The focus on cost tracking and provider optimization will provide significant value to users while the OpenAI compatibility ensures seamless integration.

Success will be measured through technical performance metrics, business value delivery, and user satisfaction, with continuous improvement based on feedback and usage patterns.
