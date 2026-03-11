#!/usr/bin/env python3
"""
Startup script for BRICKKIT application
Handles database seeding and server startup
"""

import uvicorn
import sys
import os
from database import engine, get_db
import models
from config import settings

def initialize_database():
    """Initialize database with tables and sample data"""
    print("🔧 Initializing database...")
    
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Seed data if needed
    db = next(get_db())
    try:
        if db.query(models.Product).count() == 0:
            print("📦 Seeding database with sample data...")
            from seed_database import seed_database
            seed_database()
        else:
            print("✅ Database already contains data")
    finally:
        db.close()

def check_ollama_connection():
    """Check if Ollama is running and model is available"""
    import httpx
    
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{settings.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                
                if settings.ollama_model in model_names:
                    print(f"✅ Ollama model '{settings.ollama_model}' is available")
                    return True
                else:
                    print(f"⚠️  Model '{settings.ollama_model}' not found. Available models: {model_names}")
                    print("💡 Run: ollama pull " + settings.ollama_model)
                    return False
            else:
                print("❌ Ollama API not responding")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("💡 Make sure Ollama is running: ollama serve")
        return False

def main():
    """Main startup function"""
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print("=" * 50)
    
    # Initialize database
    initialize_database()
    
    # Check Ollama
    ollama_ok = check_ollama_connection()
    
    print("=" * 50)
    print(f"🌐 Server will run on: http://{settings.api_host}:{settings.api_port}")
    print(f"🤖 AI Studio: http://{settings.api_host}:{settings.api_port}/ai-studio")
    print(f"📱 Main Site: http://{settings.api_host}:{settings.api_port}/")
    
    if not ollama_ok:
        print("⚠️  Warning: Ollama connection issues detected")
        print("   AI responses may not work properly")
    
    print("=" * 50)
    print("🎯 Ready to serve! Press Ctrl+C to stop")
    
    # Start server
    try:
        uvicorn.run(
            "llm:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.debug,
            log_level="info" if settings.debug else "warning"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")

if __name__ == "__main__":
    main()
