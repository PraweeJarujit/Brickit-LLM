"""
Production-ready API Documentation
Enhanced OpenAPI/Swagger documentation with examples and schemas
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, EmailStr
from fastapi import FastAPI
from datetime import datetime

# Enhanced Pydantic Models for Documentation
class UserResponse(BaseModel):
    """User response model"""
    id: int = Field(..., description="User ID", example=1)
    username: str = Field(..., description="Username", example="john_doe")
    email: EmailStr = Field(..., description="User email", example="john@example.com")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com"
            }
        }

class UserCreateRequest(BaseModel):
    """User creation request model"""
    username: str = Field(..., min_length=3, max_length=50, description="Username", example="john_doe")
    email: EmailStr = Field(..., description="Email address", example="john@example.com")
    password: str = Field(..., min_length=8, description="Password", example="SecurePass123!")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass123!"
            }
        }

class UserLoginRequest(BaseModel):
    """User login request model"""
    username: str = Field(..., description="Username", example="john_doe")
    password: str = Field(..., description="Password", example="SecurePass123!")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePass123!"
            }
        }

class ProductResponse(BaseModel):
    """Product response model"""
    id: int = Field(..., description="Product ID", example=1)
    name: str = Field(..., description="Product name", example="Smart Drawer Kit A")
    description: str = Field(..., description="Product description", example="Modular dividers for shallow drawers")
    price: float = Field(..., description="Product price", example=24.0)
    image_url: str = Field(..., description="Product image URL", example="https://example.com/image.jpg")
    size_category: str = Field(..., description="Size category (S/M/L)", example="S")
    pattern: str = Field(..., description="Pattern", example="White")
    is_active: bool = Field(..., description="Product availability", example=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Smart Drawer Kit A",
                "description": "Modular dividers for shallow drawers",
                "price": 24.0,
                "image_url": "https://example.com/image.jpg",
                "size_category": "S",
                "pattern": "White",
                "is_active": True
            }
        }

class OrderItemRequest(BaseModel):
    """Order item request model"""
    name: str = Field(..., description="Product name", example="Smart Drawer Kit A")
    price: float = Field(..., description="Item price", example=24.0)
    quantity: int = Field(..., ge=1, description="Quantity", example=2)
    image: str = Field(..., description="Product image URL", example="https://example.com/image.jpg")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Smart Drawer Kit A",
                "price": 24.0,
                "quantity": 2,
                "image": "https://example.com/image.jpg"
            }
        }

class OrderCreateRequest(BaseModel):
    """Order creation request model"""
    user_id: int = Field(..., description="User ID", example=1)
    full_name: str = Field(..., description="Customer full name", example="John Doe")
    address: str = Field(..., description="Shipping address", example="123 Main St, City, State 12345")
    phone: str = Field(..., description="Phone number", example="+1234567890")
    items: List[OrderItemRequest] = Field(..., description="Order items")
    total_amount: float = Field(..., description="Total order amount", example=48.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "full_name": "John Doe",
                "address": "123 Main St, City, State 12345",
                "phone": "+1234567890",
                "items": [
                    {
                        "name": "Smart Drawer Kit A",
                        "price": 24.0,
                        "quantity": 2,
                        "image": "https://example.com/image.jpg"
                    }
                ],
                "total_amount": 48.0
            }
        }

class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role (user/assistant)", example="user")
    content: str = Field(..., description="Message content", example="What furniture do you recommend for a small apartment?")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What furniture do you recommend for a small apartment?"
            }
        }

class ChatRequest(BaseModel):
    """Chat request model"""
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "role": "user",
                        "content": "What furniture do you recommend for a small apartment?"
                    }
                ]
            }
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error message", example="Resource not found")
    error_code: Optional[str] = Field(None, description="Error code", example="NOT_FOUND")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Resource not found",
                "error_code": "NOT_FOUND",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }

class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Overall health status", example="healthy")
    timestamp: datetime = Field(..., description="Check timestamp")
    checks: Dict[str, Any] = Field(..., description="Individual health checks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "checks": {
                    "database": {
                        "status": "healthy",
                        "response_time": 0.05,
                        "details": {"response_time": 0.05}
                    }
                }
            }
        }

# API Documentation Configuration
def setup_openapi_docs(app: FastAPI):
    """Setup enhanced OpenAPI documentation"""
    
    # Custom OpenAPI configuration
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = {
            "openapi": "3.0.0",
            "info": {
                "title": "BRICKIT API",
                "version": "1.0.0",
                "description": """
## BRICKIT Furniture Design API

A comprehensive API for furniture design consultation and e-commerce.

### Features
- **Authentication**: Secure user authentication with JWT tokens
- **Product Catalog**: Browse and search furniture products
- **AI Chat**: Intelligent furniture design assistance
- **Order Management**: Complete order processing system
- **User Management**: User profiles and preferences
- **Analytics**: Sales and user activity tracking

### Getting Started

1. **Register a new user**
   ```bash
   curl -X POST "http://localhost:8000/api/auth/register" \\
     -H "Content-Type: application/json" \\
     -d '{
       "username": "john_doe",
       "email": "john@example.com",
       "password": "SecurePass123!"
     }'
   ```

2. **Login to get access token**
   ```bash
   curl -X POST "http://localhost:8000/api/auth/login" \\
     -H "Content-Type: application/json" \\
     -d '{
       "username": "john_doe",
       "password": "SecurePass123!"
     }'
   ```

3. **Chat with AI assistant**
   ```bash
   curl -X POST "http://localhost:8000/api/chat" \\
     -H "Content-Type: application/json" \\
     -d '{
       "messages": [
         {
           "role": "user",
           "content": "What furniture do you recommend for a small apartment?"
         }
       ]
     }'
   ```

### Authentication

Most endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Rate Limiting

API requests are limited to 100 requests per minute per IP address.

### Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Monitoring

Health checks and metrics are available at:
- `/monitoring/health` - Application health status
- `/monitoring/metrics` - Performance metrics
- `/monitoring/alerts` - System alerts
                """,
                "contact": {
                    "name": "BRICKIT Support",
                    "email": "support@BRICKIT.com",
                    "url": "https://BRICKIT.com/support"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "Development server"
                },
                {
                    "url": "https://api.BRICKIT.com",
                    "description": "Production server"
                }
            ],
            "components": {
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                },
                "schemas": {
                    "UserResponse": UserResponse.model_json_schema(),
                    "UserCreateRequest": UserCreateRequest.model_json_schema(),
                    "UserLoginRequest": UserLoginRequest.model_json_schema(),
                    "ProductResponse": ProductResponse.model_json_schema(),
                    "OrderItemRequest": OrderItemRequest.model_json_schema(),
                    "OrderCreateRequest": OrderCreateRequest.model_json_schema(),
                    "ChatMessage": ChatMessage.model_json_schema(),
                    "ChatRequest": ChatRequest.model_json_schema(),
                    "ErrorResponse": ErrorResponse.model_json_schema(),
                    "HealthCheckResponse": HealthCheckResponse.model_json_schema()
                }
            },
            "paths": {},
            "security": [{"BearerAuth": []}]
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # Setup Swagger UI configuration
    app.swagger_ui_init_oauth = {
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": "BRICKIT-swagger",
        "clientSecret": "your-client-secret"
    }
    
    # Custom ReDoc configuration
    app.redoc_url = "/docs/redoc"
    
    return app

# API Tags for better organization
API_TAGS = [
    {
        "name": "Authentication",
        "description": "User authentication and authorization operations"
    },
    {
        "name": "Products",
        "description": "Product catalog and management operations"
    },
    {
        "name": "Orders",
        "description": "Order management and processing operations"
    },
    {
        "name": "Chat",
        "description": "AI-powered chat and consultation operations"
    },
    {
        "name": "Users",
        "description": "User profile and preference management"
    },
    {
        "name": "Monitoring",
        "description": "System health checks and monitoring endpoints"
    },
    {
        "name": "Analytics",
        "description": "Sales analytics and reporting operations"
    }
]

# Response examples for documentation
RESPONSE_EXAMPLES = {
    "user_created": {
        "summary": "User created successfully",
        "value": {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com"
        }
    },
    "login_success": {
        "summary": "Login successful",
        "value": {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com"
        }
    },
    "product_list": {
        "summary": "Product list",
        "value": [
            {
                "id": 1,
                "name": "Smart Drawer Kit A",
                "description": "Modular dividers for shallow drawers",
                "price": 24.0,
                "image_url": "https://example.com/image.jpg",
                "size_category": "S",
                "pattern": "White",
                "is_active": True
            }
        ]
    },
    "order_created": {
        "summary": "Order created successfully",
        "value": {
            "status": "success",
            "order_id": 123
        }
    },
    "chat_response": {
        "summary": "AI chat response",
        "description": "Streaming response from AI assistant"
    },
    "health_check": {
        "summary": "Health check response",
        "value": {
            "status": "healthy",
            "timestamp": "2024-01-01T12:00:00Z",
            "checks": {
                "database": {
                    "status": "healthy",
                    "response_time": 0.05,
                    "details": {"response_time": 0.05}
                },
                "cache": {
                    "status": "healthy",
                    "response_time": 0.01,
                    "details": {"backend": "MemoryCache"}
                }
            }
        }
    }
}

# Error examples
ERROR_EXAMPLES = {
    "validation_error": {
        "summary": "Validation error",
        "value": {
            "detail": [
                {
                    "loc": ["body", "username"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }
    },
    "unauthorized": {
        "summary": "Unauthorized access",
        "value": {
            "detail": "Invalid authentication credentials",
            "error_code": "UNAUTHORIZED",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    },
    "not_found": {
        "summary": "Resource not found",
        "value": {
            "detail": "Product not found",
            "error_code": "NOT_FOUND",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    },
    "rate_limit": {
        "summary": "Rate limit exceeded",
        "value": {
            "detail": "Rate limit exceeded",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    }
}

# Documentation utilities
def add_endpoint_examples(endpoint_func, examples: Dict[str, Any]):
    """Add examples to endpoint documentation"""
    endpoint_func.__doc__ = endpoint_func.__doc__ or ""
    
    if "responses" not in examples:
        examples["responses"] = {}
    
    # Add examples to docstring for better documentation
    for status_code, example in examples.items():
        if isinstance(example, dict) and "summary" in example:
            endpoint_func.__doc__ += f"\n\n**{status_code}**: {example['summary']}"
    
    return endpoint_func

# API Documentation Helper Class
class APIDocHelper:
    """Helper class for API documentation"""
    
    @staticmethod
    def create_success_response(description: str, model: BaseModel = None):
        """Create success response documentation"""
        response = {"description": description}
        if model:
            response["content"] = {
                "application/json": {
                    "schema": model.model_json_schema(),
                    "example": model.model_json_schema().get("example", {})
                }
            }
        return response
    
    @staticmethod
    def create_error_response(status_code: int, description: str, example_key: str = None):
        """Create error response documentation"""
        response = {"description": description}
        
        if example_key and example_key in ERROR_EXAMPLES:
            example = ERROR_EXAMPLES[example_key]
            response["content"] = {
                "application/json": {
                    "schema": ErrorResponse.model_json_schema(),
                    "example": example["value"]
                }
            }
        
        return response
    
    @staticmethod
    def add_parameter_docs(params: Dict[str, Any]):
        """Add parameter documentation"""
        return {
            "parameters": [
                {
                    "name": name,
                    "in": param.get("in", "query"),
                    "description": param.get("description", ""),
                    "required": param.get("required", False),
                    "schema": {"type": param.get("type", "string")}
                }
                for name, param in params.items()
            ]
        }

# Initialize documentation helper
doc_helper = APIDocHelper()
