from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# เปลี่ยนมาใช้ SQLite เพื่อให้รันในคอมตัวเองได้เลย
SQLALCHEMY_DATABASE_URL = "sqlite:///./brickkit.db"

# ตั้งค่า Engine สำหรับ SQLite (ต้องมี check_same_thread=False)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()