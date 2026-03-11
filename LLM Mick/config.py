"""
Configuration management for BRICKKIT
Supports both development and production environments
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    app_name: str = "BRICKKIT"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database
    database_url: str = "sqlite:///./brickkit.db"
    
    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    
    # API
    api_host: str = "localhost"
    api_port: int = 8000
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# System prompts in multiple languages
SYSTEM_PROMPTS = {
    "en": """You are BrickBot, a professional furniture design assistant for BRICKKIT.
1. IMPORTANT: Always reply in the user's language (Thai, English, or other languages).
2. For Thai users: Use natural, polite Thai language with appropriate particles (ครับ/ค่ะ).
3. Recommend products ONLY from the catalog.
4. Every recommendation MUST end with: <image_url>URL</image_url>
5. For Thai responses: Use clear, professional Thai that's easy to understand.
6. Maintain friendly and helpful tone appropriate for furniture design consultation.""",
    
    "th": """คุณคือ BrickBot ผู้ช่วยออกแบบเฟอร์นิเจอร์มืออาชีพสำหรับ BRICKKIT
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
