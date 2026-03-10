"""
Production-ready Configuration management for BRICKIT
Supports both development and production environments
"""

import os
from typing import List, Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Application
    app_name: str = "BRICKIT"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Database
    database_url: str = "sqlite:///./BRICKIT.db"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    ollama_timeout: int = 300
    
    # API
    api_host: str = "localhost"
    api_port: int = 8000
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS - Production ready
    allowed_origins: List[str] = ["http://localhost:3000"]
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["*"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    rate_limit_storage: str = "memory"  # or "redis"
    
    # Redis Cache
    redis_url: Optional[str] = None
    cache_ttl: int = 3600  # 1 hour
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_rotation: str = "1 day"
    log_retention: str = "30 days"
    
    # Monitoring
    enable_metrics: bool = True
    health_check_interval: int = 30
    
    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_dir: str = "uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @classmethod
    def from_env(cls):
        """Create settings from environment variables"""
        return cls(
            app_name=os.getenv("APP_NAME", "BRICKIT"),
            debug=os.getenv("DEBUG", "False").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "development"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./BRICKIT.db"),
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "gemma3:4b"),
            api_host=os.getenv("API_HOST", "localhost"),
            api_port=int(os.getenv("API_PORT", "8000")),
            secret_key=os.getenv("SECRET_KEY", "your-secret-key-here"),
            allowed_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if os.getenv("ALLOWED_ORIGINS") else ["http://localhost:3000"],
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
            redis_url=os.getenv("REDIS_URL"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "logs/app.log"),
            enable_metrics=os.getenv("ENABLE_METRICS", "True").lower() == "true"
        )

# Global settings instance
settings = Settings.from_env()

# System prompts in multiple languages
SYSTEM_PROMPTS = {
    "en": """You are BrickBot, a professional furniture design assistant for BRICKIT.
1. IMPORTANT: Always reply in the user's language (Thai, English, or other languages).
2. For Thai users: Use natural, polite Thai language with appropriate particles (ครับ/ค่ะ).
3. Recommend products ONLY from the catalog.
4. Every recommendation MUST end with: <image_url>URL</image_url>
5. For Thai responses: Use clear, professional Thai that's easy to understand.
6. Maintain friendly and helpful tone appropriate for furniture design consultation.""",
    
    "th": """คุณคือ BrickBot ผู้ช่วยออกแบบเฟอร์นิเจอร์มืออาชีพสำหรับ BRICKIT
1. สำคัญ: ตอบเป็นภาษาเดียวกับผู้ใช้เสมอ (ไทย, อังกฤษ หรือภาษาอื่น)
2. สำหรับผู้ใช้ชาวไทย: ใช้ภาษาไทยธรรมชาติและสุภาพ พูดคุยด้วยคำลงท้ายที่เหมาะสม (ครับ/ค่ะ)
3. แนะนำสินค้าจากแคตตาล็อกเท่านั้น
4. ทุกคำแนะนำต้องลงท้ายด้วย: <image_url>URL</image_url>
5. สำหรับคำตอบภาษาไทย: ใช้ภาษาไทยที่ชัดเจน เข้าใจง่าย และเป็นมืออาชีพ
6. รักษาโทนเสียงที่เป็นกันเองและมีประโยชน์เหมาะสำหรับการปรึกษาออกแบบเฟอร์นิเจอร์"""
}

def get_system_prompt(language: str = "en") -> str:
    """Get system prompt in specified language"""
    return SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en"])