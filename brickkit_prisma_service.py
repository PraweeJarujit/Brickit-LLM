"""
BRICKIT Prisma Service (Python Version)
Inspired by TradingJournal Backend Architecture
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext
import json
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./BRICKIT.db")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Initialize SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database Models (following Prisma schema structure)
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    wishlists = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("ProductReview", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(Text)
    size_category = Column(String(10), nullable=False, index=True)
    pattern = Column(String(100))
    material = Column(String(100))
    weight = Column(Numeric(8, 2))
    dimensions = Column(String(100))
    stock_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")
    wishlists = relationship("Wishlist", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20))
    address = Column(Text, nullable=False)
    status = Column(String(20), default="pending", index=True)
    payment_method = Column(String(50))
    payment_status = Column(String(20), default="pending")
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    shipping_cost = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text)
    tracking_number = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    image_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

class Wishlist(Base):
    __tablename__ = "wishlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="wishlists")
    product = relationship("Product", back_populates="wishlists")

class ProductReview(Base):
    __tablename__ = "product_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False, index=True)
    title = Column(String(255))
    comment = Column(Text)
    is_verified = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

class UserActivity(Base):
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    activity_type = Column(String(100), nullable=False, index=True)
    activity_data = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activities")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    session_id = Column(String(255), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_messages")

# Create tables
Base.metadata.create_all(bind=engine)

# Service Classes (inspired by TradingJournal)
class BRICKITPrismaService:
    """Main database service for BRICKIT"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def get_db(self) -> Session:
        return self.db
    
    def close(self):
        self.db.close()

class AuthService:
    """Authentication service (inspired by TradingJournal)"""
    
    def __init__(self, db_service: BRICKITPrismaService):
        self.db = db_service.get_db()
    
    async def register(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Register new user"""
        # Check if email exists
        existing_user = self.db.query(User).filter(User.email == data["email"]).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Hash password
        hashed_password = pwd_context.hash(data["password"])
        
        # Create user
        new_user = User(
            email=data["email"],
            username=data["username"],
            full_name=data["full_name"],
            password=hashed_password,
            phone=data.get("phone"),
            address=data.get("address")
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        return {"message": "Registration successful", "user_id": new_user.id}
    
    async def login(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Login user"""
        # Find user by email
        user = self.db.query(User).filter(User.email == data["email"]).first()
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not pwd_context.verify(data["password"], user.password):
            raise ValueError("Invalid email or password")
        
        return {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name
            }
        }

class ProductService:
    """Product management service"""
    
    def __init__(self, db_service: BRICKITPrismaService):
        self.db = db_service.get_db()
    
    async def find_all(self, size_category: Optional[str] = None, is_active: bool = True) -> List[Product]:
        """Get all products with optional filters"""
        query = self.db.query(Product).filter(Product.is_active == is_active)
        
        if size_category:
            query = query.filter(Product.size_category == size_category.upper())
        
        return query.order_by(Product.created_at.desc()).all()
    
    async def find_featured(self, limit: int = 6) -> List[Product]:
        """Get featured products"""
        return self.db.query(Product).filter(
            Product.is_active == True,
            Product.is_featured == True
        ).limit(limit).all()
    
    async def find_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    async def create(self, data: Dict[str, Any]) -> Product:
        """Create new product"""
        new_product = Product(
            name=data["name"],
            description=data.get("description"),
            price=data["price"],
            image_url=data.get("image_url"),
            size_category=data["size_category"],
            pattern=data.get("pattern"),
            material=data.get("material"),
            weight=data.get("weight"),
            dimensions=data.get("dimensions"),
            stock_count=data.get("stock_count", 0),
            is_featured=data.get("is_featured", False)
        )
        
        self.db.add(new_product)
        self.db.commit()
        self.db.refresh(new_product)
        
        return new_product

class OrderService:
    """Order management service"""
    
    def __init__(self, db_service: BRICKITPrismaService):
        self.db = db_service.get_db()
    
    async def find_user_orders(self, user_id: int) -> List[Order]:
        """Get all orders for a user"""
        return self.db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    
    async def create(self, user_id: int, data: Dict[str, Any]) -> Order:
        """Create new order"""
        # Generate order number
        order_number = f"BK{datetime.utcnow().strftime('%Y%m%d')}{user_id:04d}"
        
        new_order = Order(
            user_id=user_id,
            order_number=order_number,
            full_name=data["full_name"],
            email=data["email"],
            phone=data.get("phone"),
            address=data["address"],
            subtotal=data["subtotal"],
            tax_amount=data.get("tax_amount", 0),
            shipping_cost=data.get("shipping_cost", 0),
            total_amount=data["total_amount"],
            notes=data.get("notes")
        )
        
        self.db.add(new_order)
        self.db.flush()  # Get the ID
        
        # Add order items
        for item_data in data["items"]:
            order_item = OrderItem(
                order_id=new_order.id,
                product_name=item_data["name"],
                product_id=item_data.get("product_id"),
                price=item_data["price"],
                quantity=item_data["quantity"],
                image_url=item_data.get("image_url")
            )
            self.db.add(order_item)
        
        self.db.commit()
        self.db.refresh(new_order)
        
        return new_order

class WishlistService:
    """Wishlist management service"""
    
    def __init__(self, db_service: BRICKITPrismaService):
        self.db = db_service.get_db()
    
    async def find_user_wishlist(self, user_id: int) -> List[Wishlist]:
        """Get user's wishlist"""
        return self.db.query(Wishlist).filter(Wishlist.user_id == user_id).all()
    
    async def add_to_wishlist(self, user_id: int, product_id: int) -> Wishlist:
        """Add product to wishlist"""
        # Check if already exists
        existing = self.db.query(Wishlist).filter(
            Wishlist.user_id == user_id,
            Wishlist.product_id == product_id
        ).first()
        
        if existing:
            raise ValueError("Product already in wishlist")
        
        new_item = Wishlist(user_id=user_id, product_id=product_id)
        self.db.add(new_item)
        self.db.commit()
        self.db.refresh(new_item)
        
        return new_item
    
    async def remove_from_wishlist(self, user_id: int, product_id: int) -> bool:
        """Remove product from wishlist"""
        item = self.db.query(Wishlist).filter(
            Wishlist.user_id == user_id,
            Wishlist.product_id == product_id
        ).first()
        
        if item:
            self.db.delete(item)
            self.db.commit()
            return True
        
        return False

class ActivityService:
    """User activity tracking service"""
    
    def __init__(self, db_service: BRICKITPrismaService):
        self.db = db_service.get_db()
    
    async def track_activity(self, user_id: Optional[int], activity_type: str, 
                           activity_data: Optional[Dict] = None, 
                           ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None,
                           session_id: Optional[str] = None) -> UserActivity:
        """Track user activity"""
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            activity_data=activity_data,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
        
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        
        return activity
    
    async def get_user_activities(self, user_id: int, limit: int = 50) -> List[UserActivity]:
        """Get user activities"""
        return self.db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).order_by(UserActivity.created_at.desc()).limit(limit).all()

# Dependency function (similar to NestJS)
def get_db_service() -> BRICKITPrismaService:
    return BRICKITPrismaService()

def get_auth_service(db_service: BRICKITPrismaService = None) -> AuthService:
    if db_service is None:
        db_service = get_db_service()
    return AuthService(db_service)

def get_product_service(db_service: BRICKITPrismaService = None) -> ProductService:
    if db_service is None:
        db_service = get_db_service()
    return ProductService(db_service)

def get_order_service(db_service: BRICKITPrismaService = None) -> OrderService:
    if db_service is None:
        db_service = get_db_service()
    return OrderService(db_service)

def get_wishlist_service(db_service: BRICKITPrismaService = None) -> WishlistService:
    if db_service is None:
        db_service = get_db_service()
    return WishlistService(db_service)

def get_activity_service(db_service: BRICKITPrismaService = None) -> ActivityService:
    if db_service is None:
        db_service = get_db_service()
    return ActivityService(db_service)

# Context manager for database sessions
@asynccontextmanager
async def get_db_session():
    """Database session context manager"""
    db_service = BRICKITPrismaService()
    try:
        yield db_service
    finally:
        db_service.close()
