#!/usr/bin/env python3
"""
Fix Corrupted SQLite Database
"""
import os
import shutil
from datetime import datetime

def fix_database():
    print("🔧 กำลังแก้ไข Database ที่เสียหาย...")
    
    # Backup current database (if possible)
    db_file = "brickkit.db"
    backup_file = f"brickkit_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        if os.path.exists(db_file):
            print(f"📦 สำรองข้อมูลเก่า: {backup_file}")
            shutil.copy2(db_file, backup_file)
        
        # Remove corrupted database
        if os.path.exists(db_file):
            print("🗑️ ลบฐานน์ข้อมูลเสียหาย...")
            os.remove(db_file)
        
        print("✅ Database ถูกลบและพร้อมสร้างใหม่")
        print("🔄 รัน llm.py ใหม่เพื่อสร้าง database ใหม่")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    fix_database()
