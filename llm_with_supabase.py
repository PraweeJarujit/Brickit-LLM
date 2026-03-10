"""
LLM API - FastAPI backend for BRICKIT (Original Layout + Supabase)
Includes: Auth, RAG Chat, Cart System, Order Management, and Data Seeding
"""
import httpx
import json
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import os
import sys

# Add current directory to path for imports
sys.path.append(os.getcwd())

try:
    from supabase import create_client
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize Supabase
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )
    SUPABASE_AVAILABLE = True
except ImportError:
    print("⚠️ Supabase not available, using local database only")
    SUPABASE_AVAILABLE = False
    supabase = None

try:
    import models
    from database import engine, get_db
    LOCAL_DB_AVAILABLE = True
except ImportError:
    print("⚠️ Local database not available")
    LOCAL_DB_AVAILABLE = False

# สร้างตารางในฐานข้อมูล
if LOCAL_DB_AVAILABLE:
    models.Base.metadata.create_all(bind=engine)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-seed products on startup if database is empty."""
    if LOCAL_DB_AVAILABLE:
        from database import SessionLocal
        db = SessionLocal()
        try:
            _do_seed(db)
        finally:
            db.close()
    yield

app = FastAPI(title="BRICKIT Full-Stack API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma3:4b" 

SYSTEM_PROMPT = """You are BrickBot, a professional furniture design assistant for BRICKIT.

CRITICAL INSTRUCTIONS:
1. ALWAYS reply in the user's language (Thai, English, or other languages)
2. For Thai users: Use natural, polite Thai with appropriate particles (ครับ/ค่ะ)
3. BE PROACTIVE: Ask clarifying questions to understand user needs better
4. COLLECT REQUIREMENTS: Ask about size, style, materials, budget, usage
5. Recommend ONLY from catalog with <image_url>URL</image_url> format
6. Guide users through design process step-by-step
7. Maintain professional yet friendly tone

DESIGN PROCESS:
- Start by understanding their space and needs
- Ask specific questions about dimensions, style preferences
- Suggest suitable products from catalog
- Provide detailed recommendations with images
- Help them visualize the final result

PRODUCT CATALOG:
- Smart Drawer Kit A (S): Modular dividers for shallow drawers, $24, White
- Monitor Riser M1 (S): Ergonomic height, recycled HDPE, $45, Black  
- Cable Brick 4-Pack (S): Snap-fit cable management blocks, $18, Pastel Green
- M-01 Sofa Table (M): Minimalist sofa side table with marble pattern, $85, Marble
- Storage Cube Set (M): Stackable cubes for home office, $120, Solid
- Modu-Counter L200 (L): Professional reception desk for events, $1104, Terrazzo
- Exhibition Stand Pro (L): Modular booth structure for trade shows, $2500, Speckled Black

RESPONSE FORMAT:
- Start with friendly greeting in user's language
- Ask clarifying questions about their space
- Recommend specific products with images
- Provide practical advice
- End with helpful follow-up questions"""

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Pydantic Models ---
class UserCreate(BaseModel):
    username: str
    email: str
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
    user_id: int
    role: str
    content: str

# --- Static Routes ---
@app.get("/")
async def root():
    return FileResponse('index.html')

@app.get("/login")
async def login_page():
    return FileResponse('login.html')

@app.get("/shared.js")
async def shared_js():
    return FileResponse('shared.js')

# --- API: Authentication ---
@app.post("/api/auth/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | 
        (models.User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Create new user
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Also create in Supabase
    try:
        supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "username": user.username
                }
            }
        })
        
        # Create user profile in Supabase
        user_data = {
            "id": str(db_user.id),
            "username": user.username,
            "email": user.email
        }
        supabase.table("users").insert(user_data).execute()
    except Exception as e:
        print(f"Supabase sync error: {e}")
    
    return {"id": db_user.id, "username": db_user.username, "email": db_user.email}

@app.post("/api/auth/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Also try Supabase login
    try:
        auth_result = supabase.auth.sign_in_with_password({
            "email": db_user.email,
            "password": user.password
        })
    except Exception as e:
        print(f"Supabase login error: {e}")
    
    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email
    }

@app.post("/api/forgot-password")
def forgot_password(request: dict, db: Session = Depends(get_db)):
    email_or_username = request.get("email_or_username")
    
    if not email_or_username:
        raise HTTPException(status_code=400, detail="Email or username is required")
    
    # ค้นหาผู้ใช้จาก username หรือ email
    user = db.query(models.User).filter(
        (models.User.username == email_or_username) | 
        (models.User.email == email_or_username)
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้นี้ในระบบ")
    
    # ในระบบจริงควรส่งอีเมล แต่ตอนนี้แสดงรหัสผ่านเดิม (ไม่ปลอดภัยแต่เป็น demo)
    # สมมติว่าเราเก็บรหัสผ่านเดิมไว้ หรือสร้างรหัสผ่านใหม่
    new_password = f"temp_{user.username[:3]}123"
    
    # อัปเดตรหัสผ่านใหม่
    user.hashed_password = pwd_context.hash(new_password)
    db.commit()
    
    return {"password": new_password, "message": "รหัสผ่านถูกรีเซ็ตแล้ว"}

# --- API: Products ---
@app.get("/api/products")
async def get_products(size: str = None):
    """Get products with optional size filter"""
    try:
        # Try Supabase first
        query = supabase.table("products").select("*")
        
        if size:
            query = query.eq("size_category", size.upper())
        
        result = query.execute()
        
        if result.data:
            return {"products": result.data}
        else:
            # Fallback to local database
            from database import SessionLocal
            db = SessionLocal()
            try:
                query = db.query(models.Product)
                if size:
                    query = query.filter(models.Product.size_category == size.upper())
                products = query.all()
                return {"products": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "description": p.description,
                        "price": p.price,
                        "image_url": p.image_url,
                        "size_category": p.size_category,
                        "pattern": p.pattern,
                        "is_active": p.is_active
                    } for p in products
                ]}
            finally:
                db.close()
                
    except Exception as e:
        # Fallback to local database
        from database import SessionLocal
        db = SessionLocal()
        try:
            query = db.query(models.Product)
            if size:
                query = query.filter(models.Product.size_category == size.upper())
            products = query.all()
            return {"products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price": p.price,
                    "image_url": p.image_url,
                    "size_category": p.size_category,
                    "pattern": p.pattern,
                    "is_active": p.is_active
                } for p in products
            ]}
        finally:
            db.close()

@app.get("/api/products/{size}")
async def get_products_by_size(size: str):
    return await get_products(size)

# --- API: Orders ---
@app.post("/api/orders")
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    try:
        new_order = models.Order(
            user_id=order_data.user_id,
            full_name=order_data.full_name,
            address=order_data.address,
            phone=order_data.phone,
            total_amount=order_data.total_amount
        )
        db.add(new_order)
        db.flush() 

        for item in order_data.items:
            order_item = models.OrderItem(
                order_id=new_order.id,
                product_name=item.name,
                price=item.price,
                quantity=item.quantity,
                image_url=item.image
            )
            db.add(order_item)

        db.commit()
        
        # Also create in Supabase
        try:
            order_result = supabase.table("orders").insert({
                "user_id": str(order_data.user_id),
                "full_name": order_data.full_name,
                "address": order_data.address,
                "phone": order_data.phone,
                "total_amount": order_data.total_amount
            }).execute()
            
            if order_result.data:
                order_id = order_result.data[0]["id"]
                
                for item in order_data.items:
                    supabase.table("order_items").insert({
                        "order_id": order_id,
                        "product_name": item.name,
                        "price": item.price,
                        "quantity": item.quantity,
                        "image_url": item.image
                    }).execute()
        except Exception as e:
            print(f"Supabase order sync error: {e}")
        
        return {"status": "success", "order_id": new_order.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/{user_id}")
def get_user_orders(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.user_id == user_id).all()
    return {"orders": orders}

# --- API: Chat ---
@app.post("/api/chat")
async def chat_with_ai(message: dict):
    user_message = message.get("message", "")
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Get product catalog for context
    try:
        products_result = supabase.table("products").select("*").execute()
        products = products_result.data if products_result.data else []
    except:
        products = []
    
    # Build product context
    product_context = ""
    for product in products:
        product_context += f"- {product['name']} ({product['size_category']}): ${product['price']}, {product['description']}\n"
    
    # Call Ollama API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": f"""{SYSTEM_PROMPT}

Available Products:
{product_context}

User: {user_message}

BrickBot:""",
                "stream": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return {"response": result.get("response", "Sorry, I couldn't process your request.")}
        else:
            raise HTTPException(status_code=500, detail="AI service unavailable")

@app.post("/api/activities")
def log_activity(activity: dict, db: Session = Depends(get_db)):
    user_id = activity.get("user_id")
    activity_type = activity.get("activity_type")
    activity_data = activity.get("activity_data", {})
    
    if user_id and activity_type:
        activity = models.UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            activity_data=activity_data
        )
        db.add(activity)
        db.commit()
        
        # Also log to Supabase
        try:
            supabase.table("user_activities").insert({
                "user_id": str(user_id),
                "activity_type": activity_type,
                "activity_data": activity_data
            }).execute()
        except Exception as e:
            print(f"Supabase activity sync error: {e}")
        
        return {"status": "success"}
    return {"status": "error", "message": "Missing required fields"}

# --- API: Wishlist ---
@app.post("/api/wishlist")
def add_to_wishlist(item: dict, db: Session = Depends(get_db)):
    user_id = item.get("user_id")
    product_id = item.get("product_id")
    
    if user_id and product_id:
        # Check if already exists
        existing = db.query(models.Wishlist).filter(
            models.Wishlist.user_id == user_id,
            models.Wishlist.product_id == product_id
        ).first()
        
        if existing:
            return {"status": "exists", "message": "Product already in wishlist"}
        
        wishlist_item = models.Wishlist(
            user_id=user_id,
            product_id=product_id
        )
        db.add(wishlist_item)
        db.commit()
        
        # Also add to Supabase
        try:
            supabase.table("wishlists").insert({
                "user_id": str(user_id),
                "product_id": str(product_id)
            }).execute()
        except Exception as e:
            print(f"Supabase wishlist sync error: {e}")
        
        return {"status": "success"}
    return {"status": "error", "message": "Missing required fields"}

@app.get("/api/wishlist/{user_id}")
def get_wishlist(user_id: int, db: Session = Depends(get_db)):
    wishlist_items = db.query(models.Wishlist).filter(models.Wishlist.user_id == user_id).all()
    return {"wishlist": wishlist_items}

# --- Data Seeding ---
def _do_seed(db: Session):
    """Seed products if database is empty"""
    if db.query(models.Product).count() == 0:
        print("Seeding products...")
        
        products = [
            models.Product(
                name="Smart Drawer Kit A",
                description="Modular dividers for shallow drawers",
                price=24.0,
                image_url="https://via.placeholder.com/300x200/3B82F6/FFFFFF?text=Smart+Drawer",
                size_category="S",
                pattern="White",
                is_active=True
            ),
            models.Product(
                name="Monitor Riser M1",
                description="Ergonomic height, recycled HDPE",
                price=45.0,
                image_url="https://via.placeholder.com/300x200/10B981/FFFFFF?text=Monitor+Riser",
                size_category="S",
                pattern="Black",
                is_active=True
            ),
            models.Product(
                name="Cable Brick 4-Pack",
                description="Snap-fit cable management blocks",
                price=18.0,
                image_url="https://via.placeholder.com/300x200/F59E0B/FFFFFF?text=Cable+Brick",
                size_category="S",
                pattern="Pastel Green",
                is_active=True
            ),
            models.Product(
                name="M-01 Sofa Table",
                description="Minimalist sofa side table with marble pattern",
                price=85.0,
                image_url="https://via.placeholder.com/300x200/EF4444/FFFFFF?text=Sofa+Table",
                size_category="M",
                pattern="Marble",
                is_active=True
            ),
            models.Product(
                name="Storage Cube Set",
                description="Stackable cubes for home office",
                price=120.0,
                image_url="https://via.placeholder.com/300x200/8B5CF6/FFFFFF?text=Storage+Cubes",
                size_category="M",
                pattern="Solid",
                is_active=True
            ),
            models.Product(
                name="Modu-Counter L200",
                description="Professional reception desk for events",
                price=1104.0,
                image_url="https://via.placeholder.com/300x200/EC4899/FFFFFF?text=Modu-Counter",
                size_category="L",
                pattern="Terrazzo",
                is_active=True
            ),
            models.Product(
                name="Exhibition Stand Pro",
                description="Modular booth structure for trade shows",
                price=2500.0,
                image_url="https://via.placeholder.com/300x200/14B8A6/FFFFFF?text=Exhibition+Stand",
                size_category="L",
                pattern="Speckled Black",
                is_active=True
            )
        ]
        
        for product in products:
            db.add(product)
        
        db.commit()
        print("Products seeded successfully!")
        
        # Also seed to Supabase
        try:
            supabase_products = []
            for product in products:
                supabase_products.append({
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "image_url": product.image_url,
                    "size_category": product.size_category,
                    "pattern": product.pattern,
                    "is_active": product.is_active
                })
            
            supabase.table("products").insert(supabase_products).execute()
            print("Supabase products seeded successfully!")
        except Exception as e:
            print(f"Supabase seeding error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
