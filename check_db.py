from database import SessionLocal
from models import User, Product
import os

db = SessionLocal()
print('=== Local Database Status ===')
print(f'Database file: {os.path.exists("brickkit.db")}')
print(f'Users count: {db.query(User).count()}')
print(f'Products count: {db.query(Product).count()}')

users = db.query(User).all()
if users:
    print('\n=== Users in Local DB ===')
    for user in users:
        print(f'ID: {user.id}, Username: {user.username}, Email: {user.email}')
else:
    print('\n❌ No users found in local database')

db.close()
