"""
LLM API - FastAPI backend for BRICKIT
Includes: Auth, RAG Chat, Cart System, Order Management, and Data Seeding
WITH SUPABASE INTEGRATION
"""
import httpx
import json
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import os

# Supabase Integration
try:
    from supabase import create_client
    print("✅ Supabase module found")
    SUPABASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Supabase not available: {e}")
    SUPABASE_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
    
    if SUPABASE_AVAILABLE:
        # Initialize Supabase
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        print("✅ Supabase connected successfully")
    else:
        supabase = None
        print("⚠️ Using local database only")
        
except Exception as e:
    print(f"⚠️ Environment setup failed: {e}")
    SUPABASE_AVAILABLE = False
    supabase = None

import models
from database import engine, get_db

# สร้างตารางในฐานข้อมูล
models.Base.metadata.create_all(bind=engine)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-seed products on startup if database is empty."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        _do_seed(db)
    finally:
        db.close()
    yield

app = FastAPI(title="BRICKIT Full-Stack API", lifespan=lifespan)

# Create static directories if they don't exist
STATIC_DIRS = ["css", "js", "images", "static"]
for dir_name in STATIC_DIRS:
    dir_path = os.path.join(os.getcwd(), dir_name)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 Created directory: {dir_path}")

# Mount static files (only if directories exist)
print(f"🔍 Debug: Current working directory: {os.getcwd()}")

css_path = os.path.join(os.getcwd(), "css")
js_path = os.path.join(os.getcwd(), "js") 
images_path = os.path.join(os.getcwd(), "images")
static_path = os.path.join(os.getcwd(), "static")

if os.path.exists(css_path):
    app.mount("/css", StaticFiles(directory=css_path), name="css")
    print(f"✅ Mounted /css static directory from: {css_path}")
else:
    print(f"❌ CSS directory not found at: {css_path}")
    
if os.path.exists(js_path):
    app.mount("/js", StaticFiles(directory=js_path), name="js")
    print(f"✅ Mounted /js static directory from: {js_path}")
if os.path.exists(images_path):
    app.mount("/images", StaticFiles(directory=images_path), name="images")
    print(f"✅ Mounted /images static directory from: {images_path}")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    print(f"✅ Mounted /static static directory from: {static_path}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma3:4b" 

SYSTEM_PROMPT = """You are BrickBot, a professional AI furniture design consultant for BRICKIT.
Our furniture is crafted from 100% recycled plastic bottle caps.

CRITICAL INSTRUCTIONS:
1. AUTO-DETECT LANGUAGE: If the user speaks English, reply in English. If the user speaks Thai, reply in natural, polite Thai (ending with ครับ/ค่ะ).
2. Ask for requirements iteratively if missing: Product type, Dimensions (width, length, height), and Color.
3. DEFAULT COLOR IS WHITE (#FFFFFF) if not specified.
4. NEVER output technical jargon to the user.
5. When all requirements are met, output EXACTLY ONE JSON block to trigger the 3D generation.

REQUIRED JSON FORMAT:
```json
{
  "generate_3d": true,
  "product_type": "shoe_rack",
  "width": 80,
  "length": 40,
  "height": 50,
  "color": "#FFFFFF",
  "has_walls": true
}
"""

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Pydantic Models ---
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ChatMessageBase(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessageBase]

class SaveMessageRequest(BaseModel):
    user_id: int
    role: str
    content: str

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    image_url: str
    size_category: str
    pattern: str

class OrderItemSchema(BaseModel):
    name: str
    price: float
    quantity: int
    image: str

class OrderCreate(BaseModel):
    user_id: int
    full_name: str
    address: str
    phone: str
    items: List[OrderItemSchema]
    total_amount: float

# --- Seed helper (ใช้ได้ทั้งจาก route และ startup) ---
def _do_seed(db: Session):
    if db.query(models.Product).count() > 0:
        return False
    samples = [
        # Size S
        models.Product(name="Smart Drawer Kit A", description="Modular dividers for shallow drawers", price=24.0, image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuAzmWSiYRkx2LyFa4inZdc5plnRv0JxmzOPxaLpt6S5sO9AZ70kdl90C7sdegQTBJrv61CTKUXx2iUS6_LXgHNfCBp2-h4PpgNSI7GVZe12d8tSurGYR2gAu_mbtxuHNxrUqdFT4e0XyKLLRvRN0Bp61hkZwD_0d8uwLZGgTgkWNuios4TxSy1h5FLTCwtUQPmcKi008Vm0z9AfdL7SWFEi2AGTwIzefNF2O9XDYtPDpRQHu4oxh6o3PxviPnKJ_HwX9z74Zz1zH6to", size_category="S", pattern="White"),
        models.Product(name="Monitor Riser M1", description="Ergonomic height, recycled HDPE", price=45.0, image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuDixyum7QgGueLFJzevEcCULMA2Pk6zRe09E9oNyrEOqTjc6POANAuO28xWtrV-52IUJUj9Yr7XWHj1n5QDkcjkGekA2oSlGVK_Cnj9kMXgELEnHVRiqYXCsqmGOjZDUAxE-2uBjZWWI9n1rUtP-SvLgVQx3aA0Bc0kuvp1aTn1dHJHDOt-lJEfjOecYi830ChXhfyUTG9Q4EfF57SEZ8RD0xmv5QTugTLYwH-TS7AuTU84Cj_Tdpwq-ckzudX6fJY7ClwFDGqyoAya", size_category="S", pattern="Black"),
        models.Product(name="Cable Brick 4-Pack", description="Snap-fit cable management blocks", price=18.0, image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuD1Nguv765R3BDTwgZUhsOn-bXp1PIzLwUAGYIpUFPJ6GSBQ5FYpkTXIZWHOZ78TD7iwRVSuImYIs9MPY_OzeMLuZrfPXTWGPV6GcSAJtJlsqQTb6M4gRq4tRcaooUgZ9ArEaAp7nvGrkEm1KpS65aUHV8VG8qV0aIfLPwYHqEbCi1q8mwy1A2A3zTnn2RirfY1JQOY4PBpb2p6r-MgOAvZK-HndnGRR2xChu60imdylB4M1ZkCOaRJau4al78w-S5YlF4rh8CVdvi5", size_category="S", pattern="Pastel Green"),
        
        # Size M
        models.Product(name="M-01 Sofa Table", description="Minimalist sofa side table with marble pattern", price=85.0, image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuArWeoXQvMD1RsboqiWWfsb2fJ_dZtHG_CiMG30y2ZKv7AlqLejZnPBirfHsi8TQR_EYluSC2jCKC5XkVpYjVoaq0roD5SoTa59PHNy09KlThFHE7rSBU7VOrGYV3ESSkAqrZqNAbb6SuNLYI4SeY_x1XnaXKGY7noEog06W7ihuePcuBumqW01Lwfzjwxn30ZrefwzzedVcLKm68-L_-BmQiYZx5gtcrY4HVnTaN0FufURf_xD4ZciZazzCdbepucWc5ezw8RPU-WD", size_category="M", pattern="HDPE Marble"),
        models.Product(name="Storage Cube Set", description="Stackable cubes for home office", price=120.0, image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCK575dkB7kzE9sOCzLJ6XugQ1TumfGah5eF-jN7oM0Eph4-HrgExaf2R81Ge6Rum_Qmggfw5GtPyOSFZb5POwdzTYdJjBfUkHIyYLIIxnZY3VZCeueXvkba9t37bhffnejt1JmAIZ3DkxeavcIl9DL-y0l_CrP5WsEnxEyPTtfspwmZIdm9xocCfU_2CmEH1ndCDhwq_wDTYwzg-V8OBlzQmFlN_A0LEqEuNnTeKpOLqcxwj-I9YMuJDHJ_s_sCQB6ND0hrGqvMWIW", size_category="M", pattern="Solid Mix"),
        
        # Size L
        models.Product(name="Modu-Counter L200", description="Professional reception desk for events", price=1104.0, image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCK4kS1gaDd5cot348l0PFfgeeJrlmi2t4LnAui62lKoRTZAhRsqeWn2hHbeXOBVJzr4usgZO8sEEErirYouNjrc2lWNC5w6KgCsgNEz9ePFljcDxM3UmFH6GUnNu-lQJCctal97HBmT0o_G9nCzpuQQg0_zUhePpAc6DW0vJw25DFcFcMXedCM-hQwY3pUUA8a--Sg0p0WM_R4ueraMKumfg_CHn4M3PHlA18pDDYMz18kzIQwqbds-aymUag2-8Z0BNn9ul7PFC15", size_category="L", pattern="Terrazzo White"),
        models.Product(name="Exhibition Stand Pro", description="Modular booth structure for trade shows", price=2500.0, image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuC7yAL5w9r2Db9S969QuDxrMreiJ7gsuv_DY5zVAnuBz7rCU7QtYM_bDCiQYpLCLY2fhkas8JPkHLMAK2gF3_EY9YeJOW0UnA8Nh-Ws3WjThGBJAsQ0kjc8-_cqHjCG51ZLFpw9EjKlDrS-TeUUGLyU4DdgMAvjYrBmzWOd62aSwghleBLNkKPHL4WJisailvUy1JRZhTgLgBCEG8CiZ4CAUz79cbNUomuHFHf6i-GJ5ajHk1xk799r9l6q9RqI0_Eo-jz7fZ9Xn71M", size_category="L", pattern="Speckled Black")
    ]
    
    db.add_all(samples)
    db.commit()
    return True


@app.get("/api/seed-products")
def seed_products(db: Session = Depends(get_db)):
    seeded = _do_seed(db)
    if seeded:
        return {"message": "Successfully seeded 7 sample products", "status": "success"}
    count = db.query(models.Product).count()
    return {"message": f"Already have {count} products.", "status": "skipped"}


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
    new_password = f"temp_{user.username[:3]}123"
    
    # อัปเดตรหัสผ่านใหม่
    user.hashed_password = pwd_context.hash(new_password)
    db.commit()
    
    return {"password": new_password, "message": "รหัสผ่านถูกรีเซ็ตแล้ว"}

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
        return {"status": "success", "order_id": new_order.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/my-orders/{user_id}")
def get_user_orders(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.user_id == user_id).all()
    # ดึงข้อมูลสินค้าในแต่ละออเดอร์มาด้วย
    result = []
    for o in orders:
        items = db.query(models.OrderItem).filter(models.OrderItem.order_id == o.id).all()
        result.append({
            "id": o.id,
            "total": o.total_amount,
            "timestamp": o.timestamp,
            "items": items
        })
    return result

# --- API: Chat & Products ---
@app.post("/api/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        print(f"🤖 Chat API called with messages: {len(request.messages) if request.messages else 0}")
        
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        try:
            print(f"🔄 Calling Ollama at {OLLAMA_URL} with model {MODEL}")
            return StreamingResponse(stream_ollama(messages), media_type="application/x-ndjson")
        except Exception as e:
            print(f"❌ Ollama connection error: {e}")
            return {"response": "ขออภัยครับ ไม่สามารถเชื่อมต่อกับ AI ได้ กรุณาตรวจสอบว่า Ollama ทำงานอยู่หรือไม่", "error": "ollama_connection_failed"}
            
    except Exception as e:
        print(f"❌ Chat API Error: {str(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        
        return {
            "response": "ขออภัยครับ ระบบเกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง",
            "error": str(e),
            "error_type": type(e).__name__
        }

async def stream_ollama(messages: list):
    """Stream response from Ollama API"""
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            async with client.stream("POST", f"{OLLAMA_URL}/api/chat", json={"model": MODEL, "messages": messages, "stream": True}) as resp:
                async for chunk in resp.aiter_text():
                    if chunk.strip():
                        try:
                            data = json.loads(chunk)
                            if "message" in data and "content" in data["message"]:
                                yield json.dumps({"message": {"content": data["message"]["content"]}}) + "\n"
                            elif "content" in data:
                                yield json.dumps({"message": {"content": data["content"]}}) + "\n"
                        except json.JSONDecodeError:
                            yield json.dumps({"message": {"content": chunk}}) + "\n"
        except Exception as e:
            print(f"❌ Ollama streaming error: {e}")
            yield json.dumps({"error": f"Streaming error: {str(e)}"}) + "\n"


# --- Chat History API ---
@app.get("/api/chat/history")
async def get_chat_history(user_id: int = None, db: Session = Depends(get_db)):
    if user_id:
        messages = db.query(models.ChatMessage).filter(models.ChatMessage.user_id == user_id).order_by(models.ChatMessage.timestamp.desc()).all()
        return [{"role": msg.role, "content": msg.content, "timestamp": msg.timestamp} for msg in messages]
    return []

@app.post("/api/chat/save")
async def save_chat_message(request: dict, db: Session = Depends(get_db)):
    user_id = request.get("user_id")
    role = request.get("role")
    content = request.get("content")
    
    if user_id and role and content:
        chat_msg = models.ChatMessage(
            user_id=user_id,
            role=role,
            content=content
        )
        db.add(chat_msg)
        db.commit()
        return {"status": "success"}
    return {"status": "error", "message": "Missing required fields"}

# --- User Management API ---
@app.post("/api/auth/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user exists in local database
        existing_user = db.query(models.User).filter(
            (models.User.username == user.username) | 
            (models.User.email == user.email)
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already registered")
        
        # Create new user in local database
        hashed_password = pwd_context.hash(user.password)
        db_user = models.User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Also create in Supabase if available
        if SUPABASE_AVAILABLE and supabase:
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
                
                # Create user profile in Supabase (let Supabase generate UUID)
                user_data = {
                    "username": user.username,
                    "email": user.email
                }
                supabase.table("users").insert(user_data).execute()
                print(f"✅ User synced to Supabase: {user.username}")
            except Exception as e:
                print(f"⚠️ Supabase sync error: {e}")
        
        return {"id": db_user.id, "username": db_user.username, "email": db_user.email}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    # Try to find user by username or email
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.username)
    ).first()
    
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email
    }

# --- Product Management API ---
@app.get("/api/products")
def get_all_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@app.get("/api/products/{size}")
def get_products_by_size(size: str, db: Session = Depends(get_db)):
    return db.query(models.Product).filter(models.Product.size_category == size.upper()).all()

@app.post("/api/products")
def create_product(product: dict, db: Session = Depends(get_db)):
    new_product = models.Product(
        name=product.get("name"),
        description=product.get("description"),
        price=product.get("price"),
        image_url=product.get("image_url"),
        size_category=product.get("size_category"),
        pattern=product.get("pattern")
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    # Create stock record for new product
    new_stock = models.Stock(
        product_id=new_product.id,
        quantity=product.get("stock_quantity", 10),
        low_stock_threshold=product.get("low_stock_threshold", 5)
    )
    db.add(new_stock)
    db.commit()
    
    return new_product

# --- Stock Management API ---
@app.get("/api/stocks")
def get_all_stocks(db: Session = Depends(get_db)):
    """ดูสต็อกสินค้าทั้งหมด"""
    return db.query(models.Stock).join(models.Product).all()

@app.get("/api/products/{product_id}/stock")
def get_product_stock(product_id: int, db: Session = Depends(get_db)):
    """ดูสต็อกสินค้าตาม ID"""
    stock = db.query(models.Stock).filter(models.Stock.product_id == product_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock

@app.put("/api/products/{product_id}/stock")
def update_product_stock(product_id: int, stock_data: dict, db: Session = Depends(get_db)):
    """อัปเดตจำนวนสต็อก"""
    stock = db.query(models.Stock).filter(models.Stock.product_id == product_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    stock.quantity = stock_data.get("quantity", stock.quantity)
    stock.reserved = stock_data.get("reserved", stock.reserved)
    stock.low_stock_threshold = stock_data.get("low_stock_threshold", stock.low_stock_threshold)
    stock.last_updated = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(stock)
    return stock

@app.get("/api/products/low-stock")
def get_low_stock_products(db: Session = Depends(get_db)):
    """ดูสินค้าที่สต็อกต่ำ"""
    return db.query(models.Stock).join(models.Product).filter(
        models.Stock.quantity <= models.Stock.low_stock_threshold
    ).all()

# --- Product Reviews API ---
@app.get("/api/products/{product_id}/reviews")
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    """ดูรีวิวสินค้า"""
    return db.query(models.ProductReview).filter(
        models.ProductReview.product_id == product_id
    ).order_by(models.ProductReview.created_at.desc()).all()

@app.post("/api/products/{product_id}/reviews")
def create_product_review(product_id: int, review: dict, db: Session = Depends(get_db)):
    """สร้างรีวิวสินค้า"""
    # ตรวจสอบว่าผู้ใช้ซื้อสินค้านี้จริงหรือไม่
    user_id = review.get("user_id")
    has_purchased = db.query(models.Order).join(models.OrderItem).filter(
        models.Order.user_id == user_id
    ).filter(models.OrderItem.product_name.contains(str(product_id))).first()
    
    new_review = models.ProductReview(
        product_id=product_id,
        user_id=user_id,
        rating=review.get("rating"),
        comment=review.get("comment"),
        is_verified=bool(has_purchased)
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

@app.put("/api/reviews/{review_id}")
def update_review(review_id: int, review_data: dict, db: Session = Depends(get_db)):
    """อัปเดตรีวิว"""
    review = db.query(models.ProductReview).filter(models.ProductReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review.rating = review_data.get("rating", review.rating)
    review.comment = review_data.get("comment", review.comment)
    db.commit()
    db.refresh(review)
    return review

@app.delete("/api/reviews/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db)):
    """ลบรีวิว"""
    review = db.query(models.ProductReview).filter(models.ProductReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    db.delete(review)
    db.commit()
    return {"message": "Review deleted successfully"}

# --- Wishlist API ---
@app.get("/api/users/{user_id}/wishlist")
def get_user_wishlist(user_id: int, db: Session = Depends(get_db)):
    """ดู wishlist ของผู้ใช้"""
    return db.query(models.Wishlist).join(models.Product).filter(
        models.Wishlist.user_id == user_id
    ).all()

@app.post("/api/wishlist")
def add_to_wishlist(wishlist_item: dict, db: Session = Depends(get_db)):
    """เพิ่มสินค้าใน wishlist"""
    # ตรวจสอบว่ามีอยู่แล้วหรือไม่
    existing = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == wishlist_item.get("user_id"),
        models.Wishlist.product_id == wishlist_item.get("product_id")
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Product already in wishlist")
    
    new_item = models.Wishlist(
        user_id=wishlist_item.get("user_id"),
        product_id=wishlist_item.get("product_id")
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.delete("/api/wishlist/{item_id}")
def remove_from_wishlist(item_id: int, db: Session = Depends(get_db)):
    """ลบสินค้าจาก wishlist"""
    item = db.query(models.Wishlist).filter(models.Wishlist.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Item removed from wishlist"}

# --- Promotion API ---
@app.get("/api/promotions")
def get_all_promotions(db: Session = Depends(get_db)):
    """ดูโปรโมชั่นทั้งหมด"""
    return db.query(models.Promotion).filter(
        models.Promotion.is_active == True,
        models.Promotion.starts_at <= datetime.now(timezone.utc),
        models.Promotion.expires_at >= datetime.now(timezone.utc)
    ).all()

@app.post("/api/promotions/validate")
def validate_promotion(promo_data: dict, db: Session = Depends(get_db)):
    """ตรวจสอบคูปอง"""
    code = promo_data.get("code")
    user_id = promo_data.get("user_id")
    order_amount = promo_data.get("order_amount", 0)
    
    promotion = db.query(models.Promotion).filter(
        models.Promotion.code == code,
        models.Promotion.is_active == True,
        models.Promotion.starts_at <= datetime.now(timezone.utc),
        models.Promotion.expires_at >= datetime.now(timezone.utc)
    ).first()
    
    if not promotion:
        raise HTTPException(status_code=404, detail="Invalid promotion code")
    
    # ตรวจสอบขั้นต่ำ
    if order_amount < promotion.min_order_amount:
        raise HTTPException(status_code=400, detail="Order amount too low")
    
    # ตรวจสอบการใช้งาน
    if promotion.usage_limit and promotion.usage_count >= promotion.usage_limit:
        raise HTTPException(status_code=400, detail="Promotion usage limit reached")
    
    # ตรวจสอบว่าผู้ใช้ใช้ไปแล้วหรือไม่
    user_usage = db.query(models.PromotionUsage).filter(
        models.PromotionUsage.promotion_id == promotion.id,
        models.PromotionUsage.user_id == user_id
    ).first()
    
    if user_usage:
        raise HTTPException(status_code=400, detail="Promotion already used by this user")
    
    # คำนวณส่วนลด
    if promotion.discount_type == "percentage":
        discount = order_amount * (promotion.discount_value / 100)
        if promotion.max_discount:
            discount = min(discount, promotion.max_discount)
    else:
        discount = promotion.discount_value
    
    return {
        "promotion_id": promotion.id,
        "discount_amount": discount,
        "final_amount": order_amount - discount
    }

# --- Analytics API ---
@app.get("/api/analytics/sales")
def get_sales_analytics(db: Session = Depends(get_db)):
    """ดูสถิติการขาย"""
    return db.query(models.SalesAnalytics).order_by(
        models.SalesAnalytics.date.desc()
    ).limit(30).all()

@app.get("/api/analytics/products")
def get_product_analytics(db: Session = Depends(get_db)):
    """ดูสถิติสินค้า"""
    # สินค้าขายดี
    top_products = db.query(models.OrderItem).group_by(
        models.OrderItem.product_name
    ).order_by(
        db.func.sum(models.OrderItem.quantity).desc()
    ).limit(10).all()
    
    return {"top_products": top_products}

@app.get("/api/analytics/users")
def get_user_analytics(db: Session = Depends(get_db)):
    """ดูสถิติผู้ใช้"""
    total_users = db.query(models.User).count()
    active_users = db.query(models.UserActivity).filter(
        models.UserActivity.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
    ).distinct(models.UserActivity.user_id).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users
    }

# --- User Activity Tracking ---
@app.post("/api/activities")
def track_user_activity(activity: dict, db: Session = Depends(get_db)):
    """บันทึกกิจกรรมผู้ใช้"""
    new_activity = models.UserActivity(
        user_id=activity.get("user_id"),
        activity_type=activity.get("activity_type"),
        activity_data=json.dumps(activity.get("data", {})),
        ip_address=activity.get("ip_address"),
        user_agent=activity.get("user_agent")
    )
    db.add(new_activity)
    db.commit()
    return {"message": "Activity tracked"}

# --- 3D Model Generation API ---
@app.post("/api/generate-model")
async def generate_model(request: Request):
    try:
        payload = await request.json()
        print(f"🎨 Model generation request: {payload}")
        
        # --- Default Color Check ---
        payload['color'] = payload.get('color', '#FFFFFF')
        
        # --- NEW VALIDATION ADDED HERE ---
        # ตรวจสอบว่ามีข้อมูลจำเป็นถูกส่งมาครบถ้วนก่อนโยนให้ furniture_model
        required_keys = ["product_type", "width", "length", "height", "color"]
        missing_keys = [key for key in required_keys if key not in payload]

        if missing_keys:
            error_msg = f"Missing required parameters: {', '.join(missing_keys)}"
            print(f"❌ {error_msg}")
            return JSONResponse(
                status_code=400,
                content={"error": error_msg, "details": "AI did not generate a complete JSON block."}
            )
        
        # --- BOTTLE CAPS CALCULATION ---
        # คำนวณจำนวน bottle caps ที่ใช้
        try:
            # คำนวณปริมาตรจากขนาด (volume)
            volume = payload.get('width', 50) * payload.get('length', 50) * payload.get('height', 50)
            estimated_bricks = max(10, int(volume / 200))  # สูตรสำหรับคำนวณ bricks
            
            # 1 brick = 45 bottle caps (based on standard LEGO 2x4 brick)
            CAPS_PER_BRICK = 45
            total_bottle_caps = estimated_bricks * CAPS_PER_BRICK
            
            # เพิ่มข้อมูล bottle caps ลงใน response
            bottle_caps_calculation = {
                'total_bricks': estimated_bricks,
                'caps_per_brick': CAPS_PER_BRICK,
                'total_bottle_caps': total_bottle_caps,
                'caps_weight_kg': round(total_bottle_caps * 0.002, 2)  # 1 cap = 2 grams
            }
            
            print(f"🧮 Bottle Caps Calculation: {estimated_bricks} bricks × {CAPS_PER_BRICK} caps = {total_bottle_caps:,} bottle caps")
            
        except Exception as e:
            print(f"⚠️ Error calculating bottle caps: {e}")
            bottle_caps_calculation = {
                'total_bricks': 0,
                'caps_per_brick': 45,
                'total_bottle_caps': 0,
                'caps_weight_kg': 0.0
            }
        # ---------------------------------

        # Import furniture_model
        from furniture_model import generate_model_from_requirements
        
        # Generate model using the new furniture_model.py
        result = generate_model_from_requirements(payload)
        
        if result is None:
            print(f"❌ Model generation failed - invalid parameters: {payload}")
            return JSONResponse(
                status_code=400, 
                content={"error": f"Failed to generate model - internal function rejected the parameters. Request: {payload}"}
            )
        
        # แทรกผลการคำนวณลงใน Result ที่จะส่งกลับไปหน้า UI
        result['bottle_caps_calculation'] = bottle_caps_calculation
        
        # Save model to file for debugging
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        product_name = payload.get("product_type", "unknown")
        filename = f"models/{product_name}_{timestamp}.json"
        
        # Create models directory if it doesn't exist
        os.makedirs("models", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Model saved to: {filename}")
        print(f"📊 Model stats: {result.get('total_pieces', 'N/A')} pieces, color: {result.get('color', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error generating model: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- Page Routes ---
@app.get("/")
async def index(): return FileResponse("index.html")
@app.get("/ai-studio")
async def ai_studio(): return FileResponse("ai-studio.html")
@app.get("/ai-studio/mobile")
async def ai_studio_mobile(): return FileResponse("ai-studio-mobile.html")
@app.get("/ai-studio/fixed")
async def ai_studio_fixed(): return FileResponse("ai-studio-fixed.html")
@app.get("/how-it-works.html")
async def how_it_works(): return FileResponse("how-it-works.html")
@app.get("/size-s")
async def size_s(): return FileResponse("size-s.html")
@app.get("/size-m")
async def size_m(): return FileResponse("size-m.html")
@app.get("/size-l")
async def size_l(): return FileResponse("size-l.html")
@app.get("/login")
async def login_page(): return FileResponse("login.html")
@app.get("/checkout")
async def checkout_page(): return FileResponse("checkout.html")
@app.get("/orders")
async def orders_page(): return FileResponse("orders.html")
@app.get("/admin")
async def admin_page(): return FileResponse("admin.html")
@app.get("/shared.js")
async def shared_js(): return FileResponse("shared.js", media_type="application/javascript")

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get configuration from environment variables with fallbacks
    HOST = os.getenv("HOST", "localhost")
    PORT = int(os.getenv("PORT", 8001))  
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    RELOAD = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"🚀 Starting BRICKIT API Server...")
    print(f"📍 Host: {HOST}")
    print(f"🔌 Port: {PORT}")
    print(f"🐛 Debug: {DEBUG}")
    print(f"🔄 Auto-reload: {RELOAD}")
    print(f"🌐 Server URL: http://{HOST}:{PORT}")
    
    try:
        uvicorn.run(
            "llm:app", 
            host=HOST, 
            port=PORT,
            reload=RELOAD,
            log_level="debug" if DEBUG else "info"
        )
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {PORT} is already in use!")
            print(f"💡 Try one of these solutions:")
            print(f"   1. Set a different port: set PORT=8002 && python llm.py")
            print(f"   2. Kill the process using port {PORT}:")
            print(f"      Windows: netstat -ano | findstr :{PORT} && taskkill /PID <PID> /F")
            print(f"      Linux/Mac: lsof -ti:{PORT} | xargs kill -9")
            print(f"   3. Use a different port directly: python -c \"import os; os.environ['PORT']='8002'; exec(open('llm.py').read())\"")
        else:
            print(f"❌ Server startup error: {e}")
        exit(1)