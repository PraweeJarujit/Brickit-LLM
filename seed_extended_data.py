"""
Seed database with sample data for BRICKIT
Includes: Products, Stocks, Promotions, Analytics
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import models
from database import engine, get_db

def seed_sample_data():
    """เพิ่มข้อมูลตัวอย่างในฐานข้อมูล"""
    db = next(get_db())
    
    try:
        # สร้างสต็อกสำหรับสินค้าที่มีอยู่แล้ว
        products = db.query(models.Product).all()
        
        for product in products:
            # ตรวจสอบว่ามีสต็อกอยู่แล้วหรือไม่
            existing_stock = db.query(models.Stock).filter(
                models.Stock.product_id == product.id
            ).first()
            
            if not existing_stock:
                # สร้างสต็อกใหม่
                new_stock = models.Stock(
                    product_id=product.id,
                    quantity=50,  # สต็อกเริ่มต้น
                    reserved=0,
                    low_stock_threshold=10
                )
                db.add(new_stock)
        
        # สร้างโปรโมชั่นตัวอย่าง
        promotions = [
            {
                "code": "WELCOME10",
                "description": "ส่วนลด 10% สำหรับการสั่งซื้อครั้งแรก",
                "discount_type": "percentage",
                "discount_value": 10.0,
                "min_order_amount": 100.0,
                "max_discount": 50.0,
                "usage_limit": 100,
                "starts_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=30)
            },
            {
                "code": "SAVE20",
                "description": "ส่วนลด 20% เมื่อซื้อขั้นต่ำ 500 บาท",
                "discount_type": "percentage",
                "discount_value": 20.0,
                "min_order_amount": 500.0,
                "max_discount": 100.0,
                "usage_limit": 50,
                "starts_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=15)
            },
            {
                "code": "FLAT50",
                "description": "ส่วนลด 50 บาทสำหรับการสั่งซื้อทุกครั้ง",
                "discount_type": "fixed",
                "discount_value": 50.0,
                "min_order_amount": 200.0,
                "usage_limit": None,
                "starts_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=60)
            }
        ]
        
        for promo_data in promotions:
            existing_promo = db.query(models.Promotion).filter(
                models.Promotion.code == promo_data["code"]
            ).first()
            
            if not existing_promo:
                new_promo = models.Promotion(**promo_data)
                db.add(new_promo)
        
        # สร้างข้อมูล Analytics ตัวอย่าง (30 วันล่าสุด)
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            
            existing_analytics = db.query(models.SalesAnalytics).filter(
                models.SalesAnalytics.date == date.date()
            ).first()
            
            if not existing_analytics:
                # สร้างข้อมูลสถิติสุ่ม
                analytics = models.SalesAnalytics(
                    date=date,
                    total_orders=5 + (i % 10),  # 5-14 ออเดอร์ต่อวัน
                    total_revenue=1000.0 + (i * 100),  # รายได้เพิ่มขึ้นเรื่อยๆ
                    total_users=10 + (i % 5),
                    top_product_id=1,  # สมมติว่าสินค้า ID 1 ขายดีที่สุด
                    top_product_sales=2 + (i % 3)
                )
                db.add(analytics)
        
        # สร้างรีวิวตัวอย่าง
        sample_reviews = [
            {
                "product_id": 1,
                "user_id": 1,
                "rating": 5,
                "comment": "สินค้าคุณภาพดีมาก สวยงาม ตรงตามรูป จัดส่งเร็ว"
            },
            {
                "product_id": 2,
                "user_id": 1,
                "rating": 4,
                "comment": "ดีครับ แต่ควรมีคู่มือการประกอบที่ชัดเจนกว่านี้"
            },
            {
                "product_id": 3,
                "user_id": 1,
                "rating": 5,
                "comment": "รักมาก! ใช้พื้นที่ได้อย่างมีประสิทธิภาพ"
            }
        ]
        
        for review_data in sample_reviews:
            existing_review = db.query(models.ProductReview).filter(
                models.ProductReview.product_id == review_data["product_id"],
                models.ProductReview.user_id == review_data["user_id"]
            ).first()
            
            if not existing_review:
                new_review = models.ProductReview(**review_data)
                db.add(new_review)
        
        db.commit()
        print("✅ เพิ่มข้อมูลตัวอย่างสำเร็จ!")
        
        # แสดงสถิติ
        total_products = db.query(models.Product).count()
        total_stocks = db.query(models.Stock).count()
        total_promotions = db.query(models.Promotion).count()
        total_reviews = db.query(models.ProductReview).count()
        total_analytics = db.query(models.SalesAnalytics).count()
        
        print(f"📊 สถิติฐานข้อมูล:")
        print(f"   - สินค้า: {total_products} รายการ")
        print(f"   - สต็อก: {total_stocks} รายการ")
        print(f"   - โปรโมชั่น: {total_promotions} รายการ")
        print(f"   - รีวิว: {total_reviews} รายการ")
        print(f"   - ข้อมูล Analytics: {total_analytics} รายการ")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_sample_data()
