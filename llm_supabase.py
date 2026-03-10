"""
BRICKIT with Supabase Integration
Production-ready FastAPI with Supabase backend
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import httpx
import os
from supabase import create_client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# Initialize FastAPI
app = FastAPI(
    title="BRICKIT Supabase API",
    description="Production-ready furniture design API with Supabase backend",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama Configuration
OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma3:4b"

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class OrderItem(BaseModel):
    name: str
    price: float
    quantity: int
    image: str

class OrderCreate(BaseModel):
    user_id: int
    full_name: str
    address: str
    phone: str
    items: List[OrderItem]
    total_amount: float

class ChatMessage(BaseModel):
    user_id: Optional[int] = None
    role: str
    content: str

# --- API Routes ---

@app.get("/")
async def root():
    return {"message": "BRICKIT API with Supabase", "version": "2.0.0"}

@app.get("/api/products")
async def get_products(size: Optional[str] = None):
    """Get products with optional size filter"""
    try:
        query = supabase.table("products").select("*")
        
        if size:
            query = query.eq("size_category", size.upper())
        
        result = query.execute()
        return {"products": result.data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/{size}")
async def get_products_by_size(size: str):
    """Get products by size category"""
    return await get_products(size)

@app.post("/api/auth/register")
async def register(user: UserCreate):
    """Register new user with Supabase Auth"""
    try:
        # Create user with Supabase Auth
        auth_result = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "username": user.username
                }
            }
        })
        
        if auth_result.user:
            # Create user profile in users table
            user_data = {
                "id": auth_result.user.id,
                "username": user.username,
                "email": user.email
            }
            
            profile_result = supabase.table("users").insert(user_data).execute()
            
            return {
                "id": auth_result.user.id,
                "username": user.username,
                "email": user.email,
                "message": "User registered successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login(user: UserLogin):
    """Login user with Supabase Auth"""
    try:
        # First get user by username from users table
        users_result = supabase.table("users").select("*").eq("username", user.username).execute()
        
        if not users_result.data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user_email = users_result.data[0]["email"]
        
        # Sign in with Supabase Auth
        auth_result = supabase.auth.sign_in_with_password({
            "email": user_email,
            "password": user.password
        })
        
        if auth_result.user:
            return {
                "id": auth_result.user.id,
                "username": user.username,
                "email": user_email,
                "access_token": auth_result.session.access_token
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/orders")
async def create_order(order_data: OrderCreate):
    """Create new order"""
    try:
        # Create order
        order_result = supabase.table("orders").insert({
            "user_id": str(order_data.user_id),
            "full_name": order_data.full_name,
            "address": order_data.address,
            "phone": order_data.phone,
            "total_amount": order_data.total_amount
        }).execute()
        
        if order_result.data:
            order_id = order_result.data[0]["id"]
            
            # Create order items
            for item in order_data.items:
                supabase.table("order_items").insert({
                    "order_id": order_id,
                    "product_name": item.name,
                    "price": item.price,
                    "quantity": item.quantity,
                    "image_url": item.image
                }).execute()
            
            return {"status": "success", "order_id": order_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to create order")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_ai(message: dict):
    """Chat with AI assistant"""
    try:
        user_message = message.get("message", "")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Call Ollama API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": f"""You are BrickBot, a professional furniture design assistant.

User: {user_message}

Provide helpful furniture design advice and product recommendations in Thai language.""",
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {"response": result.get("response", "Sorry, I couldn't process your request.")}
            else:
                raise HTTPException(status_code=500, detail="AI service unavailable")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/activities")
async def log_activity(activity: dict):
    """Log user activity"""
    try:
        activity_data = {
            "user_id": activity.get("user_id"),
            "activity_type": activity.get("activity_type"),
            "activity_data": activity.get("activity_data", {}),
            "ip_address": activity.get("ip_address"),
            "user_agent": activity.get("user_agent")
        }
        
        result = supabase.table("user_activities").insert(activity_data).execute()
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/{user_id}")
async def get_user_orders(user_id: str):
    """Get user's orders"""
    try:
        result = supabase.table("orders").select("*").eq("user_id", user_id).execute()
        return {"orders": result.data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/wishlist")
async def add_to_wishlist(item: dict):
    """Add item to wishlist"""
    try:
        wishlist_data = {
            "user_id": item.get("user_id"),
            "product_id": item.get("product_id")
        }
        
        result = supabase.table("wishlists").insert(wishlist_data).execute()
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/wishlist/{user_id}")
async def get_wishlist(user_id: str):
    """Get user's wishlist"""
    try:
        result = supabase.table("wishlists").select(
            "*, products(*)"
        ).eq("user_id", user_id).execute()
        return {"wishlist": result.data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Supabase connection
        products_result = supabase.table("products").select("count").execute()
        
        return {
            "status": "healthy",
            "database": "connected",
            "products_count": len(products_result.data)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
