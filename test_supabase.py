"""
Test Supabase Connection
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test Supabase connection"""
    try:
        # Get credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        print(f"URL: {supabase_url}")
        print(f"Key: {supabase_key[:20]}...")
        
        # Create client
        supabase = create_client(supabase_url, supabase_key)
        
        # Test connection
        print("🔗 Testing Supabase connection...")
        
        # Test simple query
        result = supabase.table("products").select("count").execute()
        print(f"✅ Connection successful! Products count: {result.data}")
        
        # Test auth service
        print("🔐 Testing auth service...")
        auth_status = supabase.auth.get_user()
        print(f"✅ Auth service working!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_supabase_connection()
