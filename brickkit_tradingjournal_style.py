"""
BRICKIT API - TradingJournal Style Architecture
NestJS-inspired service pattern with FastAPI
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
import os
from contextlib import asynccontextmanager

# Import our services
from BRICKIT_prisma_service import (
    get_db_service, get_auth_service, get_product_service, 
    get_order_service, get_wishlist_service, get_activity_service,
    BRICKITPrismaService
)

# Supabase integration
try:
    from supabase import create_client
    from dotenv import load_dotenv
    load_dotenv()
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )
    SUPABASE_AVAILABLE = True
    print("✅ Supabase connected")
except ImportError:
    print("⚠️ Supabase not available")
    SUPABASE_AVAILABLE = False
    supabase = None

# Pydantic Models (DTOs)
class UserRegisterDto(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    phone: Optional[str] = None
    address: Optional[str] = None

class UserLoginDto(BaseModel):
    email: EmailStr
    password: str

class ProductCreateDto(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    size_category: str
    pattern: Optional[str] = None
    material: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    stock_count: Optional[int] = 0
    is_featured: Optional[bool] = False

class OrderItemDto(BaseModel):
    name: str
    price: float
    quantity: int
    image_url: Optional[str] = None
    product_id: Optional[int] = None

class OrderCreateDto(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: str
    items: List[OrderItemDto]
    subtotal: float
    tax_amount: Optional[float] = 0
    shipping_cost: Optional[float] = 0
    total_amount: float
    notes: Optional[str] = None

class ActivityTrackDto(BaseModel):
    activity_type: str
    activity_data: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

# Response Models
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    phone: Optional[str]
    address: Optional[str]
    role: str
    created_at: datetime

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    image_url: Optional[str]
    size_category: str
    pattern: Optional[str]
    material: Optional[str]
    weight: Optional[float]
    dimensions: Optional[str]
    stock_count: int
    is_active: bool
    is_featured: bool
    created_at: datetime

class OrderResponse(BaseModel):
    id: int
    order_number: str
    full_name: str
    email: str
    status: str
    subtotal: float
    tax_amount: float
    shipping_cost: float
    total_amount: float
    created_at: datetime

# Application Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    print("🚀 BRICKIT API Starting up...")
    
    # Initialize database connection
    db_service = BRICKITPrismaService()
    print("✅ Database connected")
    
    # Sync with Supabase if available
    if SUPABASE_AVAILABLE:
        try:
            # Test Supabase connection
            result = supabase.table("products").select("count").execute()
            print(f"✅ Supabase sync ready: {len(result.data)} products")
        except Exception as e:
            print(f"⚠️ Supabase sync issue: {e}")
    
    yield
    
    print("🛑 BRICKIT API Shutting down...")
    db_service.close()

# Initialize FastAPI
app = FastAPI(
    title="BRICKIT API - TradingJournal Style",
    description="Production-ready furniture design API with service architecture",
    version="2.0.0",
    lifespan=lifespan
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

# --- Controllers (like NestJS) ---

class AuthController:
    """Authentication Controller"""
    
    @staticmethod
    async def register(
        user_data: UserRegisterDto,
        auth_service: AuthService = Depends(get_auth_service)
    ):
        """Register new user"""
        try:
            result = await auth_service.register(user_data.dict())
            
            # Sync with Supabase
            if SUPABASE_AVAILABLE:
                try:
                    supabase.auth.sign_up({
                        "email": user_data.email,
                        "password": user_data.password,
                        "options": {
                            "data": {
                                "username": user_data.username,
                                "full_name": user_data.full_name
                            }
                        }
                    })
                    
                    # Create profile in Supabase
                    supabase.table("users").insert({
                        "id": str(result["user_id"]),
                        "username": user_data.username,
                        "email": user_data.email,
                        "full_name": user_data.full_name
                    }).execute()
                except Exception as e:
                    print(f"Supabase sync error: {e}")
            
            return result
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Registration failed")
    
    @staticmethod
    async def login(
        login_data: UserLoginDto,
        auth_service: AuthService = Depends(get_auth_service)
    ):
        """Login user"""
        try:
            result = await auth_service.login(login_data.dict())
            
            # Try Supabase login
            if SUPABASE_AVAILABLE:
                try:
                    supabase.auth.sign_in_with_password({
                        "email": login_data.email,
                        "password": login_data.password
                    })
                except Exception as e:
                    print(f"Supabase login error: {e}")
            
            return result
            
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Login failed")

class ProductController:
    """Product Controller"""
    
    @staticmethod
    async def get_all_products(
        size: Optional[str] = None,
        product_service: ProductService = Depends(get_product_service)
    ):
        """Get all products"""
        try:
            # Try Supabase first
            if SUPABASE_AVAILABLE:
                try:
                    query = supabase.table("products").select("*")
                    if size:
                        query = query.eq("size_category", size.upper())
                    
                    result = query.execute()
                    if result.data:
                        return {"products": result.data}
                except Exception as e:
                    print(f"Supabase error: {e}")
            
            # Fallback to local database
            products = await product_service.find_all(size_category=size)
            return {"products": products}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to fetch products")
    
    @staticmethod
    async def get_featured_products(
        product_service: ProductService = Depends(get_product_service)
    ):
        """Get featured products"""
        try:
            products = await product_service.find_featured()
            return {"products": products}
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to fetch featured products")
    
    @staticmethod
    async def get_product_by_id(
        product_id: int,
        product_service: ProductService = Depends(get_product_service)
    ):
        """Get product by ID"""
        try:
            product = await product_service.find_by_id(product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            return {"product": product}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to fetch product")

class OrderController:
    """Order Controller"""
    
    @staticmethod
    async def create_order(
        order_data: OrderCreateDto,
        user_id: int,
        order_service: OrderService = Depends(get_order_service)
    ):
        """Create new order"""
        try:
            order = await order_service.create(user_id, order_data.dict())
            
            # Sync with Supabase
            if SUPABASE_AVAILABLE:
                try:
                    supabase.table("orders").insert({
                        "user_id": str(user_id),
                        "full_name": order_data.full_name,
                        "email": order_data.email,
                        "address": order_data.address,
                        "total_amount": order_data.total_amount,
                        "status": "pending"
                    }).execute()
                except Exception as e:
                    print(f"Supabase order sync error: {e}")
            
            return {"order": order}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to create order")
    
    @staticmethod
    async def get_user_orders(
        user_id: int,
        order_service: OrderService = Depends(get_order_service)
    ):
        """Get user's orders"""
        try:
            orders = await order_service.find_user_orders(user_id)
            return {"orders": orders}
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to fetch orders")

class WishlistController:
    """Wishlist Controller"""
    
    @staticmethod
    async def get_user_wishlist(
        user_id: int,
        wishlist_service: WishlistService = Depends(get_wishlist_service)
    ):
        """Get user's wishlist"""
        try:
            wishlist = await wishlist_service.find_user_wishlist(user_id)
            return {"wishlist": wishlist}
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to fetch wishlist")
    
    @staticmethod
    async def add_to_wishlist(
        user_id: int,
        product_id: int,
        wishlist_service: WishlistService = Depends(get_wishlist_service)
    ):
        """Add product to wishlist"""
        try:
            item = await wishlist_service.add_to_wishlist(user_id, product_id)
            
            # Sync with Supabase
            if SUPABASE_AVAILABLE:
                try:
                    supabase.table("wishlists").insert({
                        "user_id": str(user_id),
                        "product_id": str(product_id)
                    }).execute()
                except Exception as e:
                    print(f"Supabase wishlist sync error: {e}")
            
            return {"message": "Added to wishlist", "item": item}
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to add to wishlist")
    
    @staticmethod
    async def remove_from_wishlist(
        user_id: int,
        product_id: int,
        wishlist_service: WishlistService = Depends(get_wishlist_service)
    ):
        """Remove product from wishlist"""
        try:
            success = await wishlist_service.remove_from_wishlist(user_id, product_id)
            
            if success and SUPABASE_AVAILABLE:
                try:
                    supabase.table("wishlists").delete().match({
                        "user_id": str(user_id),
                        "product_id": str(product_id)
                    }).execute()
                except Exception as e:
                    print(f"Supabase wishlist delete error: {e}")
            
            return {"message": "Removed from wishlist" if success else "Item not found"}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to remove from wishlist")

class ActivityController:
    """Activity Controller"""
    
    @staticmethod
    async def track_activity(
        activity_data: ActivityTrackDto,
        user_id: Optional[int] = None,
        activity_service: ActivityService = Depends(get_activity_service)
    ):
        """Track user activity"""
        try:
            activity = await activity_service.track_activity(
                user_id=user_id,
                **activity_data.dict()
            )
            
            # Sync with Supabase
            if SUPABASE_AVAILABLE and user_id:
                try:
                    supabase.table("user_activities").insert({
                        "user_id": str(user_id),
                        "activity_type": activity_data.activity_type,
                        "activity_data": activity_data.activity_data,
                        "ip_address": activity_data.ip_address,
                        "user_agent": activity_data.user_agent
                    }).execute()
                except Exception as e:
                    print(f"Supabase activity sync error: {e}")
            
            return {"message": "Activity tracked", "activity_id": activity.id}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to track activity")

# --- API Routes (like NestJS Controllers) ---

# Authentication Routes
@app.post("/api/auth/register")
async def register(user_data: UserRegisterDto):
    return await AuthController.register(user_data)

@app.post("/api/auth/login")
async def login(login_data: UserLoginDto):
    return await AuthController.login(login_data)

# Product Routes
@app.get("/api/products")
async def get_products(size: Optional[str] = None):
    return await ProductController.get_all_products(size)

@app.get("/api/products/featured")
async def get_featured_products():
    return await ProductController.get_featured_products()

@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    return await ProductController.get_product_by_id(product_id)

@app.get("/api/products/size/{size}")
async def get_products_by_size(size: str):
    return await ProductController.get_all_products(size)

# Order Routes
@app.post("/api/orders")
async def create_order(order_data: OrderCreateDto, user_id: int = 1):  # TODO: Get from auth token
    return await OrderController.create_order(order_data, user_id)

@app.get("/api/orders/{user_id}")
async def get_user_orders(user_id: int):
    return await OrderController.get_user_orders(user_id)

# Wishlist Routes
@app.get("/api/wishlist/{user_id}")
async def get_wishlist(user_id: int):
    return await WishlistController.get_user_wishlist(user_id)

@app.post("/api/wishlist")
async def add_to_wishlist(user_id: int = 1, product_id: int = 1):  # TODO: Get from request body
    return await WishlistController.add_to_wishlist(user_id, product_id)

@app.delete("/api/wishlist/{user_id}/{product_id}")
async def remove_from_wishlist(user_id: int, product_id: int):
    return await WishlistController.remove_from_wishlist(user_id, product_id)

# Activity Routes
@app.post("/api/activities")
async def track_activity(activity_data: ActivityTrackDto, user_id: Optional[int] = None):
    return await ActivityController.track_activity(activity_data, user_id)

# Chat Route (AI Assistant)
@app.post("/api/chat")
async def chat_with_ai(message: dict):
    """Chat with AI assistant"""
    user_message = message.get("message", "")
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": f"""You are BrickBot, a professional furniture design assistant for BRICKIT.

User: {user_message}

Provide helpful furniture design advice in Thai language. Recommend products and ask clarifying questions about their space and needs.""",
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {"response": result.get("response", "Sorry, I couldn't process your request.")}
            else:
                raise HTTPException(status_code=500, detail="AI service unavailable")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail="Chat service unavailable")

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_service = BRICKITPrismaService()
        
        # Test database
        db_service.get_db().execute("SELECT 1")
        
        # Test Supabase
        supabase_status = "connected" if SUPABASE_AVAILABLE else "not available"
        
        return {
            "status": "healthy",
            "database": "connected",
            "supabase": supabase_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "BRICKIT API - TradingJournal Style",
        "version": "2.0.0",
        "architecture": "Service-based with Supabase integration",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
