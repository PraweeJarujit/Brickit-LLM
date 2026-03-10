"""
Production-ready Security Module
Includes Rate Limiting, Input Validation, and Security Headers
"""

import time
import hashlib
import secrets
from typing import Dict, Optional, List
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import json

# Rate Limiting Storage
class RateLimiter:
    def __init__(self, storage_type: str = "memory", redis_url: Optional[str] = None):
        self.storage_type = storage_type
        self.memory_storage: Dict[str, Dict] = {}
        self.redis_client = None
        
        if storage_type == "redis" and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
            except Exception:
                self.storage_type = "memory"
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit"""
        now = int(time.time())
        
        if self.storage_type == "redis":
            return self._redis_check(key, limit, window)
        else:
            return self._memory_check(key, limit, window, now)
    
    def _memory_check(self, key: str, limit: int, window: int, now: int) -> bool:
        """Memory-based rate limiting"""
        if key not in self.memory_storage:
            self.memory_storage[key] = {"count": 0, "reset_time": now + window}
        
        data = self.memory_storage[key]
        
        if now > data["reset_time"]:
            data["count"] = 0
            data["reset_time"] = now + window
        
        if data["count"] >= limit:
            return False
        
        data["count"] += 1
        return True
    
    def _redis_check(self, key: str, limit: int, window: int) -> bool:
        """Redis-based rate limiting"""
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            results = pipe.execute()
            return results[0] <= limit
        except Exception:
            return True  # Fail open

# Security Middleware
class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next):
        # Add security headers
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

# Rate Limiting Middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limiter: RateLimiter, requests: int = 100, window: int = 60):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.requests = requests
        self.window = window
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Create rate limit key
        key = f"rate_limit:{client_ip}:{request.url.path}"
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(key, self.requests, self.window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(self.window)}
            )
        
        return await call_next(request)

# Input Validation
class InputValidator:
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not text:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r', '\t']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        # Limit length
        return text[:max_length]
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        return True, "Password is valid"

# JWT Authentication
class JWTAuth:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(self, data: dict, expires_delta: Optional[int] = None):
        """Create JWT access token"""
        import jwt
        from datetime import datetime, timedelta
        
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token"""
        import jwt
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

# CSRF Protection
class CSRFProtection:
    def __init__(self):
        self.tokens = {}
    
    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token"""
        token = secrets.token_urlsafe(32)
        self.tokens[session_id] = token
        return token
    
    def validate_token(self, session_id: str, token: str) -> bool:
        """Validate CSRF token"""
        return self.tokens.get(session_id) == token

# Security Headers Helper
def get_security_headers() -> dict:
    """Get security headers for responses"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'"
    }
