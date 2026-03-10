"""
ทดสอบการเชื่อมต่อ Supabase และตรวจสอบข้อมูล
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def test_supabase_connection():
    try:
        # เชื่อมต่อ Supabase
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        print("✅ เชื่อมต่อ Supabase สำเร็จ")
        
        # ตรวจสอบว่ามีตารางอะไรบ้าง
        print("\n=== ตรวจสอบตาราง ===")
        
        # ตรวจสอบตาราง users
        try:
            users_result = supabase.table("users").select("count").execute()
            users_count = len(users_result.data) if users_result.data else 0
            print(f"📊 Users table: {users_count} records")
            
            if users_count > 0:
                print("⚠️ ไม่มีข้อมูลในตาราง users")
            else:
                print("✅ มีข้อมูลในตาราง users")
                # แสดงข้อมูลตัวอย่าง
                sample_users = supabase.table("users").select("id, username, email").limit(3).execute()
                for user in sample_users.data:
                    print(f"   - ID: {user.get('id')}, Username: {user.get('username')}, Email: {user.get('email')}")
        except Exception as e:
            print(f"❌ Error checking users table: {e}")
        
        # ตรวจสอบตาราง products
        try:
            products_result = supabase.table("products").select("count").execute()
            products_count = len(products_result.data) if products_result.data else 0
            print(f"📊 Products table: {products_count} records")
            
            if products_count > 0:
                # แสดงข้อมูลตัวอย่าง
                sample_products = supabase.table("products").select("id, name, price, size_category").limit(3).execute()
                for product in sample_products.data:
                    print(f"   - ID: {product.get('id')}, Name: {product.get('name')}, Price: {product.get('price')}, Size: {product.get('size_category')}")
        except Exception as e:
            print(f"❌ Error checking products table: {e}")
        
        # เปรียบเทียบกับ Local Database
        print("\n=== เปรียบเทียบกับ Local Database ===")
        from database import SessionLocal
        from models import User, Product
        
        local_db = SessionLocal()
        local_users = local_db.query(User).count()
        local_products = local_db.query(Product).count()
        
        print(f"📊 Local DB - Users: {local_users}, Products: {local_products}")
        
        if users_count != local_users:
            print(f"⚠️ Users ไม่ตรงกัน: Supabase={users_count}, Local={local_users}")
        
        if products_count != local_products:
            print(f"⚠️ Products ไม่ตรงกัน: Supabase={products_count}, Local={local_products}")
        
        local_db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ ไม่สามารถเชื่อมต่อ Supabase: {e}")
        return False

if __name__ == "__main__":
    test_supabase_connection()
