#!/usr/bin/env python3
"""
Database seeding script for BRICKIT
Run this script to populate the database with sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import engine, get_db
import models

def seed_database():
    """Seed the database with sample products and users"""
    
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if data already exists
        if db.query(models.Product).count() > 0:
            print("Database already contains data. Skipping seeding.")
            return
        
        # Sample Products
        products = [
            # Size S Products
            models.Product(
                name="Smart Drawer Kit A",
                description="Modular dividers for shallow drawers",
                price=24.0,
                image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuAzmWSiYRkx2LyFa4inZdc5plnRv0JxmzOPxaLpt6S5sO9AZ70kdl90C7sdegQTBJrv61CTKUXx2iUS6_LXgHNfCBp2-h4PpgNSI7GVZe12d8tSurGYR2gAu_mbtxuHNxrUqdFT4e0XyKLLRvRN0Bp61hkZwD_0d8uwLZGgTgkWNuios4TxSy1h5FLTCwtUQPmcKi008Vm0z9AfdL7SWFEi2AGTwIzefNF2O9XDYtPDpRQHu4oxh6o3PxviPnKJ_HwX9z74Zz1zH6to",
                size_category="S",
                pattern="White"
            ),
            models.Product(
                name="Cable Organizer Set",
                description="Cable management clips and ties",
                price=18.0,
                image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCniCCMpiiFi2vs3iByKV8gYSBbaAWCfzSP3gvMQkFGTio5KAHaH-KkqgmqIEqezvNnbrd3Cqb0TvhgJnnRUXQ81NhjXqoCDmnoYcYXZKm4tVSSQ08RjF0PnK7UAjIUWDBpX7tOcuhXX6yQ23F69sAEst9ppuCbMwB0XfSFWlVqXQNf_sBNfp-OAX_ZTJMaPwx5PTpRb5crGRP0ET2CvovRaXP56rDqS8SI_T7vjxJh8HN611fajvdgcj0kmuQVK5pkimPI_Yl9zE-o",
                size_category="S",
                pattern="White"
            ),
            
            # Size M Products
            models.Product(
                name="Stackable Storage Bins",
                description="Collapsible storage containers with lids",
                price=35.0,
                image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuAYMPl5-1dsuNaf1u1k_T53aQzfbdUbN6awNUN9Ea9a52J4HfaifhPRdb7mJ_7JgwtL2b6MDfYZHyb8RYMY98vntD4A4MzmIJSzdOryX0FMSMMTmbsK0cv93yU_QTaeGS22N0nWCR0LpNRIrtUThe0cTjQxkaJqDKtVYvsvUbTyh7SKhK0vKK6ZbwexMW3mUM_rqKrusE1Ld8t7ubQYOtaNRs6rsuB2VkjJ6oS78pdcLiCFpoHviY5TJ2VssXfdZc87D402g2XExrZ-",
                size_category="M",
                pattern="Gray"
            ),
            models.Product(
                name="Kitchen Drawer Organizer",
                description="Adjustable compartments for utensils",
                price=42.0,
                image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuAIqu0Dkayj30CqIBEytniDYhxdyf4g_fC1W6hnNZT2NfDb2eLF8WOSGBLiv4DIrEHoN8PDipk8Gjo6JaUq0bq24pfVk_6y-IfDMvv9Q17Kc16KGU-kZvXHxybdpzOlne9J3j7zMJKDUbrazjdoG0biEHQrLdmrEbUk8wZzHZZ1ZyODYsYauUr5KsKSF-yXAxMtgkSoOQYTDD5RgTfZnqgL3J_M6X6ZFyCtn1i-0-aVHKs2YxvLhCPoY-W2yj7wykgWo9R6h28rgvbR",
                size_category="M",
                pattern="Bamboo"
            ),
            
            # Size L Products
            models.Product(
                name="Garage Storage System",
                description="Heavy-duty wall-mounted shelves",
                price=89.0,
                image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCniCCMpiiFi2vs3iByKV8gYSBbaAWCfzSP3gvMQkFGTio5KAHaH-KkqgmqIEqezvNnbrd3Cqb0TvhgJnnRUXQ81NhjXqoCDmnoYcYXZKm4tVSSQ08RjF0PnK7UAjIUWDBpX7tOcuhXX6yQ23F69sAEst9ppuCbMwB0XfSFWlVqXQNf_sBNfp-OAX_ZTJMaPwx5PTpRb5crGRP0ET2CvovRaXP56rDqS8SI_T7vjxJh8HN611fajvdgcj0kmuQVK5pkimPI_Yl9zE-o",
                size_category="L",
                pattern="Black"
            ),
            models.Product(
                name="Workbench with Storage",
                description="Industrial workbench with built-in drawers",
                price=125.0,
                image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuAYMPl5-1dsuNaf1u1k_T53aQzfbdUbN6awNUN9Ea9a52J4HfaifhPRdb7mJ_7JgwtL2b6MDfYZHyb8RYMY98vntD4A4MzmIJSzdOryX0FMSMMTmbsK0cv93yU_QTaeGS22N0nWCR0LpNRIrtUThe0cTjQxkaJqDKtVYvsvUbTyh7SKhK0vKK6ZbwexMW3mUM_rqKrusE1Ld8t7ubQYOtaNRs6rsuB2VkjJ6oS78pdcLiCFpoHviY5TJ2VssXfdZc87D402g2XExrZ-",
                size_category="L",
                pattern="Wood"
            )
        ]
        
        # Add products to database
        for product in products:
            db.add(product)
        
        # Sample Users
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        users = [
            models.User(
                username="demo_user",
                email="demo@BRICKIT.com",
                hashed_password=pwd_context.hash("demo123")
            ),
            models.User(
                username="test_user",
                email="test@BRICKIT.com",
                hashed_password=pwd_context.hash("test123")
            )
        ]
        
        # Add users to database
        for user in users:
            db.add(user)
        
        # Commit all changes
        db.commit()
        
        print(f"Successfully seeded database with {len(products)} products and {len(users)} users")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()