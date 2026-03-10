from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base  # สำคัญมาก: ต้อง import Base ตัวเดียวกับที่ใช้ใน database.py

# 1. ตารางสมาชิก (User)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # ความสัมพันธ์: หนึ่งคนมีได้หลายแชท, หลายออเดอร์, หลายรีวิว, หลาย wishlist
    messages = relationship("ChatMessage", back_populates="user")
    orders = relationship("Order", back_populates="user")
    reviews = relationship("ProductReview", back_populates="user")
    wishlist_items = relationship("Wishlist", back_populates="user")

# 2. ตารางสินค้า (Product)
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    image_url = Column(String)
    size_category = Column(String) # S, M, L
    pattern = Column(String)
    is_active = Column(Boolean, default=True)
    # created_at = Column(DateTime, default=datetime.utcnow)  # Commented out due to SQLite limitation
    
    # ความสัมพันธ์: สินค้าหนึ่งรุ่นมีได้หลายสต็อก, หลายรีวิว, หลาย wishlist
    stocks = relationship("Stock", back_populates="product")
    reviews = relationship("ProductReview", back_populates="product")
    wishlist_items = relationship("Wishlist", back_populates="product")

# 3. ตารางเก็บประวัติแชท (ChatMessage)
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String) # user หรือ assistant
    content = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
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

# 6. ตารางสต็อกสินค้า (Stock)
class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=0)
    reserved = Column(Integer, default=0)  # สินค้าที่ถูกจองในตะกร้า
    low_stock_threshold = Column(Integer, default=5)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # ความสัมพันธ์
    product = relationship("Product", back_populates="stocks")

# 7. ตารางรีวิวสินค้า (ProductReview)
class ProductReview(Base):
    __tablename__ = "product_reviews"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)  # 1-5
    comment = Column(Text)
    is_verified = Column(Boolean, default=False)  # ผู้ซื้อจริงหรือไม่
    helpful_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # ความสัมพันธ์
    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

# 8. ตาราง Wishlist
class Wishlist(Base):
    __tablename__ = "wishlists"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # ความสัมพันธ์
    user = relationship("User", back_populates="wishlist_items")
    product = relationship("Product", back_populates="wishlist_items")

# 9. ตารางโปรโมชั่น (Promotion)
class Promotion(Base):
    __tablename__ = "promotions"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    description = Column(String)
    discount_type = Column(String)  # percentage, fixed
    discount_value = Column(Float)
    min_order_amount = Column(Float, default=0)
    max_discount = Column(Float)
    usage_limit = Column(Integer)  # null = unlimited
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    starts_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# 10. ตารางการใช้โปรโมชั่น (PromotionUsage)
class PromotionUsage(Base):
    __tablename__ = "promotion_usage"
    id = Column(Integer, primary_key=True, index=True)
    promotion_id = Column(Integer, ForeignKey("promotions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    order_id = Column(Integer, ForeignKey("orders.id"))
    discount_amount = Column(Float)
    used_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# 11. ตาราง Analytics (SalesAnalytics)
class SalesAnalytics(Base):
    __tablename__ = "sales_analytics"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime)
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Float, default=0)
    total_users = Column(Integer, default=0)
    top_product_id = Column(Integer)
    top_product_sales = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# 12. ตาราง UserActivity
class UserActivity(Base):
    __tablename__ = "user_activities"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String)  # login, view_product, add_to_cart, purchase
    activity_data = Column(Text)  # JSON data
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # ความสัมพันธ์
    user = relationship("User", back_populates="activities")

# เพิ่มความสัมพันธ์ activities ใน User model
User.activities = relationship("UserActivity", back_populates="user")