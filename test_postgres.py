"""
Test PostgreSQL Connection to Supabase
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_postgres_connection():
    """Test PostgreSQL connection to Supabase"""
    try:
        database_url = os.getenv("DATABASE_URL")
        print(f"🔗 Testing PostgreSQL connection...")
        print(f"URL: {database_url}")
        
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL!")
            print(f"📋 Version: {version}")
            
            # Test tables
            tables_result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in tables_result.fetchall()]
            print(f"📊 Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
            
            # Test products table
            if 'products' in tables:
                products_result = conn.execute(text("SELECT COUNT(*) FROM products"))
                count = products_result.fetchone()[0]
                print(f"📦 Products count: {count}")
                
                # Get sample products
                sample_result = conn.execute(text("""
                    SELECT name, price, size_category 
                    FROM products 
                    LIMIT 3
                """))
                
                print("📋 Sample products:")
                for row in sample_result.fetchall():
                    print(f"   - {row[0]} (${row[1]}) - Size {row[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_postgres_connection()
