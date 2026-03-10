"""
Supabase Integration for BRICKIT
Real-time database with built-in authentication
"""

import os
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from postgrest import APIError
from gotrue import AuthError
import logging
from datetime import datetime, timezone

logger = logging.getLogger("BRICKIT.supabase")

class SupabaseManager:
    """Production-ready Supabase integration"""
    
    def __init__(self):
        self.supabase: Client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("Supabase credentials not found in environment")
            
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {str(e)}")
            raise
    
    # Authentication Methods
    async def sign_up(self, email: str, password: str, username: str) -> Dict[str, Any]:
        """Sign up new user"""
        try:
            auth_data = {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "username": username
                    }
                }
            }
            
            result = self.supabase.auth.sign_up(auth_data)
            
            # Create user profile in users table
            if result.user:
                await self.create_user_profile(result.user.id, username, email)
            
            return {
                "success": True,
                "user": result.user,
                "session": result.session
            }
            
        except AuthError as e:
            logger.error(f"Signup error: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected signup error: {str(e)}")
            return {"success": False, "error": "Registration failed"}
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in user"""
        try:
            result = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            return {
                "success": True,
                "user": result.user,
                "session": result.session
            }
            
        except AuthError as e:
            logger.error(f"Signin error: {str(e)}")
            return {"success": False, "error": "Invalid credentials"}
        except Exception as e:
            logger.error(f"Unexpected signin error: {str(e)}")
            return {"success": False, "error": "Login failed"}
    
    async def sign_out(self) -> Dict[str, Any]:
        """Sign out user"""
        try:
            self.supabase.auth.sign_out()
            return {"success": True}
        except Exception as e:
            logger.error(f"Signout error: {str(e)}")
            return {"success": False, "error": "Logout failed"}
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        try:
            user = self.supabase.auth.get_user()
            return user.user if user else None
        except Exception as e:
            logger.error(f"Get current user error: {str(e)}")
            return None
    
    # Database Methods
    async def create_user_profile(self, user_id: str, username: str, email: str):
        """Create user profile in users table"""
        try:
            data = {
                "id": user_id,
                "username": username,
                "email": email,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("users").insert(data).execute()
            logger.info(f"User profile created: {user_id}")
            return result
            
        except APIError as e:
            logger.error(f"Create user profile error: {str(e)}")
            raise
    
    async def get_products(self, category: str = None) -> List[Dict[str, Any]]:
        """Get products with optional category filter"""
        try:
            query = self.supabase.table("products").select("*")
            
            if category:
                query = query.eq("size_category", category.upper())
            
            result = query.execute()
            return result.data
            
        except APIError as e:
            logger.error(f"Get products error: {str(e)}")
            return []
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get single product by ID"""
        try:
            result = self.supabase.table("products").select("*").eq("id", product_id).single().execute()
            return result.data
            
        except APIError as e:
            logger.error(f"Get product error: {str(e)}")
            return None
    
    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new order"""
        try:
            # Add timestamp
            order_data["created_at"] = datetime.now(timezone.utc).isoformat()
            order_data["status"] = "pending"
            
            result = self.supabase.table("orders").insert(order_data).execute()
            
            if result.data:
                order_id = result.data[0]["id"]
                logger.info(f"Order created: {order_id}")
                return {"success": True, "order_id": order_id, "data": result.data[0]}
            else:
                return {"success": False, "error": "Failed to create order"}
                
        except APIError as e:
            logger.error(f"Create order error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_user_orders(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's orders"""
        try:
            result = self.supabase.table("orders").select("*").eq("user_id", user_id).execute()
            return result.data
            
        except APIError as e:
            logger.error(f"Get user orders error: {str(e)}")
            return []
    
    async def add_to_wishlist(self, user_id: str, product_id: str) -> Dict[str, Any]:
        """Add product to wishlist"""
        try:
            data = {
                "user_id": user_id,
                "product_id": product_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("wishlists").insert(data).execute()
            return {"success": True, "data": result.data[0]}
            
        except APIError as e:
            if "duplicate" in str(e).lower():
                return {"success": False, "error": "Product already in wishlist"}
            logger.error(f"Add to wishlist error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_user_wishlist(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's wishlist"""
        try:
            result = self.supabase.table("wishlists").select(
                "*, products(*)"
            ).eq("user_id", user_id).execute()
            return result.data
            
        except APIError as e:
            logger.error(f"Get wishlist error: {str(e)}")
            return []
    
    # Real-time subscriptions
    def subscribe_to_orders(self, user_id: str, callback):
        """Subscribe to real-time order updates"""
        try:
            return self.supabase.table("orders").on_update(callback).eq("user_id", user_id).subscribe()
        except Exception as e:
            logger.error(f"Subscribe to orders error: {str(e)}")
            return None
    
    def subscribe_to_products(self, callback):
        """Subscribe to real-time product updates"""
        try:
            return self.supabase.table("products").on_update(callback).subscribe()
        except Exception as e:
            logger.error(f"Subscribe to products error: {str(e)}")
            return None
    
    # File Storage
    async def upload_product_image(self, file_path: str, file_content: bytes) -> Dict[str, Any]:
        """Upload product image to Supabase Storage"""
        try:
            result = self.supabase.storage.from_("product-images").upload(file_path, file_content)
            
            if result.data:
                public_url = self.supabase.storage.from_("product-images").get_public_url(file_path)
                return {"success": True, "url": public_url}
            else:
                return {"success": False, "error": "Upload failed"}
                
        except Exception as e:
            logger.error(f"Upload image error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """Check Supabase connectivity"""
        try:
            # Test database connection
            result = self.supabase.table("products").select("count").execute()
            
            # Test auth service
            user = self.supabase.auth.get_user()
            
            return {
                "status": "healthy",
                "database": "connected",
                "auth": "available",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

# Global Supabase manager instance
supabase_manager = SupabaseManager()

# Database Schema for Supabase
SUPABASE_SCHEMA = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """,
    
    "products": """
        CREATE TABLE IF NOT EXISTS products (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            image_url TEXT,
            size_category VARCHAR(10) NOT NULL CHECK (size_category IN ('S', 'M', 'L')),
            pattern VARCHAR(100),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(size_category);
        CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);
    """,
    
    "orders": """
        CREATE TABLE IF NOT EXISTS orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            full_name VARCHAR(255) NOT NULL,
            address TEXT NOT NULL,
            phone VARCHAR(50),
            total_amount DECIMAL(10,2) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
    """,
    
    "order_items": """
        CREATE TABLE IF NOT EXISTS order_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
            product_name VARCHAR(255) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            quantity INTEGER NOT NULL,
            image_url TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
    """,
    
    "wishlists": """
        CREATE TABLE IF NOT EXISTS wishlists (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            product_id UUID REFERENCES products(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(user_id, product_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_wishlists_user ON wishlists(user_id);
        CREATE INDEX IF NOT EXISTS idx_wishlists_product ON wishlists(product_id);
    """,
    
    "product_reviews": """
        CREATE TABLE IF NOT EXISTS product_reviews (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            product_id UUID REFERENCES products(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            is_verified BOOLEAN DEFAULT false,
            helpful_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_reviews_product ON product_reviews(product_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_user ON product_reviews(user_id);
    """,
    
    "user_activities": """
        CREATE TABLE IF NOT EXISTS user_activities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            activity_type VARCHAR(100) NOT NULL,
            activity_data JSONB,
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_activities_user ON user_activities(user_id);
        CREATE INDEX IF NOT EXISTS idx_activities_type ON user_activities(activity_type);
        CREATE INDEX IF NOT EXISTS idx_activities_created ON user_activities(created_at);
    """
}

# Row Level Security (RLS) Policies
RLS_POLICIES = {
    "users": """
        -- Users can only see their own profile
        CREATE POLICY "Users can view own profile" ON users
            FOR SELECT USING (auth.uid() = id);
        
        -- Users can update their own profile
        CREATE POLICY "Users can update own profile" ON users
            FOR UPDATE USING (auth.uid() = id);
    """,
    
    "orders": """
        -- Users can only see their own orders
        CREATE POLICY "Users can view own orders" ON orders
            FOR SELECT USING (auth.uid() = user_id);
        
        -- Users can create their own orders
        CREATE POLICY "Users can create own orders" ON orders
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    """,
    
    "wishlists": """
        -- Users can only see their own wishlist
        CREATE POLICY "Users can view own wishlist" ON wishlists
            FOR SELECT USING (auth.uid() = user_id);
        
        -- Users can manage their own wishlist
        CREATE POLICY "Users can manage own wishlist" ON wishlists
            FOR ALL USING (auth.uid() = user_id);
    """,
    
    "product_reviews": """
        -- Everyone can view reviews
        CREATE POLICY "Anyone can view reviews" ON product_reviews
            FOR SELECT USING (true);
        
        -- Users can create reviews for products they purchased
        CREATE POLICY "Users can create reviews" ON product_reviews
            FOR INSERT WITH CHECK (auth.uid() = user_id);
        
        -- Users can update their own reviews
        CREATE POLICY "Users can update own reviews" ON product_reviews
            FOR UPDATE USING (auth.uid() = user_id);
    """
}
