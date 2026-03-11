from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base  # สำคัญมาก: ต้อง import Base ตัวเดียวกับที่ใช้ใน database.py

# 1. ตารางสมาชิก (User)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # ความสัมพันธ์: หนึ่งคนมีได้หลายแชท และหลายออเดอร์
    messages = relationship("ChatMessage", back_populates="user")
    orders = relationship("Order", back_populates="user")

# 2. ตารางสินค้า (Product)
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    image_url = Column(String)
    size_category = Column(String) # S, M, L
    pattern = Column(String)

# 3. ตารางเก็บประวัติแชท (ChatMessage)
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String) # user หรือ assistant
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="messages")

# 4. ตารางหัวข้อคำสั่งซื้อ (Order)
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # เชื่อมไปหา users
    full_name = Column(String)
    address = Column(String)
    phone = Column(String)
    total_amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # ความสัมพันธ์ไปยังสมาชิกและรายการสินค้า
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

# 5. ตารางรายการสินค้าในแต่ละคำสั่งซื้อ (OrderItem)
class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_name = Column(String)
    price = Column(Float)
    quantity = Column(Integer)
    image_url = Column(String)

    order = relationship("Order", back_populates="items")