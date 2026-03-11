"""
LLM API - FastAPI backend for BRICKKIT
Includes: Auth, RAG Chat, Cart System, Order Management, and Data Seeding
"""
import httpx
import json
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext

import models
from database import engine, get_db

# สร้างตารางในฐานข้อมูล
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="BRICKKIT Full-Stack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma3:4b" 

SYSTEM_PROMPT = """You are BrickBot, a professional furniture design assistant for BRICKKIT.
1. IMPORTANT: Always reply in the user's language (Thai, English, or other languages).
2. For Thai users: Use natural, polite Thai language with appropriate particles (ครับ/ค่ะ).
3. Recommend products ONLY from the catalog.
4. Every recommendation MUST end with: <image_url>URL</image_url>
5. For Thai responses: Use clear, professional Thai that's easy to understand.
6. Maintain friendly and helpful tone appropriate for furniture design consultation."""

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
    full_name: str
    address: str
    phone: str
    total_amount: float
    items: List[OrderItemSchema]

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

@app.on_event("startup")
async def startup_event():
    """Auto-seed products on startup if database is empty."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        _do_seed(db)
    finally:
        db.close()

@app.get("/api/seed-products")
def seed_products(db: Session = Depends(get_db)):
    seeded = _do_seed(db)
    if seeded:
        return {"message": "Successfully seeded 7 sample products", "status": "success"}
    count = db.query(models.Product).count()
    return {"message": f"Already have {count} products.", "status": "skipped"}

# --- API: Authentication ---
@app.post("/api/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter((models.User.username == user.username) | (models.User.email == user.email)).first()
    if existing: raise HTTPException(status_code=400, detail="User already exists")
    hashed = pwd_context.hash(user.password)
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    return {"message": "Success"}

@app.post("/api/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid")
    return {"username": db_user.username, "user_id": db_user.id}

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
    products = db.query(models.Product).all()
    catalog = "Catalog:\n" + "\n".join([f"- {p.name}: ${p.price}, {p.image_url}" for p in products])
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    messages.insert(0, {"role": "system", "content": f"{SYSTEM_PROMPT}\n{catalog}"})
    return StreamingResponse(stream_ollama(messages), media_type="application/x-ndjson")

async def stream_ollama(messages: list):
    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream("POST", f"{OLLAMA_URL}/api/chat", json={"model": MODEL, "messages": messages}) as resp:
            async for chunk in resp.aiter_text(): yield chunk + "\n"

@app.get("/api/products/{size}")
def get_products(size: str, db: Session = Depends(get_db)):
    return db.query(models.Product).filter(models.Product.size_category == size.upper()).all()

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
    # Check if user exists
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
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
    
    return {"id": db_user.id, "username": db_user.username, "email": db_user.email}

@app.post("/api/auth/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    
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
    return new_product

# --- Page Routes ---
@app.get("/")
async def index(): return FileResponse("index.html")
@app.get("/ai-studio")
async def ai_studio(): return FileResponse("ai-studio.html")
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
@app.get("/shared.js")
async def shared_js(): return FileResponse("shared.js", media_type="application/javascript")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)