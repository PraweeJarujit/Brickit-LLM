"""
Update database schema for new features
"""
from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL

def update_database_schema():
    """อัปเดตโครงสร้างฐานข้อมูลสำหรับฟีเจอร์ใหม่"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        # เพิ่มคอลัมน์ใหม่ในตาราง products
        try:
            conn.execute(text("""
                ALTER TABLE products ADD COLUMN is_active BOOLEAN DEFAULT 1
            """))
            print("✅ Added is_active column to products")
        except Exception as e:
            print(f"⚠️ is_active column may already exist: {e}")
        
        try:
            conn.execute(text("""
                ALTER TABLE products ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            """))
            print("✅ Added created_at column to products")
        except Exception as e:
            print(f"⚠️ created_at column may already exist: {e}")
        
        # สร้างตารางใหม่
        tables = [
            """
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity INTEGER DEFAULT 0,
                reserved INTEGER DEFAULT 0,
                low_stock_threshold INTEGER DEFAULT 5,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS product_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                user_id INTEGER,
                rating INTEGER,
                comment TEXT,
                is_verified BOOLEAN DEFAULT 0,
                helpful_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS wishlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id),
                UNIQUE(user_id, product_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS promotions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                description TEXT,
                discount_type TEXT,
                discount_value REAL,
                min_order_amount REAL DEFAULT 0,
                max_discount REAL,
                usage_limit INTEGER,
                usage_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                starts_at DATETIME,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS promotion_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                promotion_id INTEGER,
                user_id INTEGER,
                order_id INTEGER,
                discount_amount REAL,
                used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (promotion_id) REFERENCES promotions (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sales_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATETIME,
                total_orders INTEGER DEFAULT 0,
                total_revenue REAL DEFAULT 0,
                total_users INTEGER DEFAULT 0,
                top_product_id INTEGER,
                top_product_sales INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                activity_type TEXT,
                activity_data TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        ]
        
        for table_sql in tables:
            try:
                conn.execute(text(table_sql))
                print("✅ Created table successfully")
            except Exception as e:
                print(f"⚠️ Table may already exist: {e}")
        
        # สร้างสต็อกสำหรับสินค้าที่มีอยู่แล้ว
        try:
            conn.execute(text("""
                INSERT INTO stocks (product_id, quantity, low_stock_threshold)
                SELECT id, 50, 10 FROM products
                WHERE id NOT IN (SELECT product_id FROM stocks)
            """))
            conn.commit()
            print("✅ Created stock records for existing products")
        except Exception as e:
            print(f"⚠️ Stock records may already exist: {e}")
        
        # สร้างดัชนี
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_stocks_product_id ON stocks (product_id)",
            "CREATE INDEX IF NOT EXISTS idx_product_reviews_product_id ON product_reviews (product_id)",
            "CREATE INDEX IF NOT EXISTS idx_product_reviews_user_id ON product_reviews (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_wishlists_user_id ON wishlists (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_wishlists_product_id ON wishlists (product_id)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_code ON promotions (code)",
            "CREATE INDEX IF NOT EXISTS idx_user_activities_user_id ON user_activities (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_activities_created_at ON user_activities (created_at)"
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                print("✅ Created index successfully")
            except Exception as e:
                print(f"⚠️ Index may already exist: {e}")
        
        conn.commit()
        print("🎉 Database schema updated successfully!")

if __name__ == "__main__":
    update_database_schema()
