"""
Production-ready Database Configuration
Includes Connection Pooling, Indexing, and Performance Optimization
"""

from sqlalchemy import create_engine, event, Index
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import Engine
from typing import Generator
import time
import logging
from config import settings

# Performance monitoring
logger = logging.getLogger("brickkit.database")

class DatabaseConfig:
    """Production-ready database configuration"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Setup database engine with production settings"""
        engine_kwargs = {
            "echo": settings.debug,
            "future": True,
        }
        
        # SQLite specific settings
        if "sqlite" in settings.database_url:
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 20,
                    "isolation_level": None
                },
                "pool_pre_ping": True
            })
        else:
            # PostgreSQL/MySQL settings
            engine_kwargs.update({
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
                "pool_pre_ping": True,
                "pool_recycle": 3600,  # Recycle connections every hour
                "pool_timeout": 30
            })
        
        self.engine = create_engine(settings.database_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            future=True
        )
        
        # Add performance monitoring
        if not settings.debug:
            self._add_performance_monitoring()
    
    def _add_performance_monitoring(self):
        """Add query performance monitoring"""
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            
            # Log slow queries (> 1 second)
            if total > 1.0:
                logger.warning(f"Slow query ({total:.3f}s): {statement[:200]}")
            
            # Log all queries in debug mode
            if settings.debug:
                logger.debug(f"Query ({total:.3f}s): {statement[:100]}")
    
    def get_db(self) -> Generator[Session, None, None]:
        """Get database session with proper error handling"""
        db = self.SessionLocal()
        try:
            yield db
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def create_tables(self):
        """Create all database tables with indexes"""
        from models import Base
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        # Create additional indexes for performance
        self._create_performance_indexes()
    
    def _create_performance_indexes(self):
        """Create performance-optimized indexes"""
        from models import User, Product, Order, OrderItem, ChatMessage
        
        # User indexes
        Index('idx_user_email', User.email)
        Index('idx_user_username', User.username)
        
        # Product indexes
        Index('idx_product_category', Product.size_category)
        Index('idx_product_pattern', Product.pattern)
        Index('idx_product_active', Product.is_active)
        Index('idx_product_name', Product.name)
        
        # Order indexes
        Index('idx_order_user', Order.user_id)
        Index('idx_order_timestamp', Order.timestamp)
        
        # OrderItem indexes
        Index('idx_orderitem_order', OrderItem.order_id)
        Index('idx_orderitem_product', OrderItem.product_name)
        
        # ChatMessage indexes
        Index('idx_chat_user', ChatMessage.user_id)
        Index('idx_chat_timestamp', ChatMessage.timestamp)
        
        # Create indexes
        Base.metadata.create_all(bind=self.engine)

# Database connection manager
db_config = DatabaseConfig()

# Health check for database
def check_database_health() -> dict:
    """Check database connectivity and performance"""
    try:
        start_time = time.time()
        
        # Test connection
        with db_config.engine.connect() as conn:
            conn.execute("SELECT 1")
        
        response_time = time.time() - start_time
        
        # Check connection pool
        pool = db_config.engine.pool
        pool_status = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout()
        }
        
        return {
            "status": "healthy",
            "response_time": response_time,
            "pool_status": pool_status,
            "timestamp": time.time()
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# Database backup utilities
class DatabaseBackup:
    """Database backup and restore utilities"""
    
    @staticmethod
    def create_backup(backup_path: str = None) -> str:
        """Create database backup"""
        import shutil
        from datetime import datetime
        
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backups/brickkit_backup_{timestamp}.db"
        
        # Create backups directory
        import os
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Copy database file (SQLite specific)
        if "sqlite" in settings.database_url:
            db_path = settings.database_url.replace("sqlite:///", "")
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        else:
            # For PostgreSQL/MySQL, implement appropriate backup logic
            raise NotImplementedError("Backup not implemented for this database type")
    
    @staticmethod
    def restore_backup(backup_path: str) -> bool:
        """Restore database from backup"""
        import shutil
        
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        if "sqlite" in settings.database_url:
            db_path = settings.database_url.replace("sqlite:///", "")
            shutil.copy2(backup_path, db_path)
            logger.info(f"Database restored from: {backup_path}")
            return True
        else:
            raise NotImplementedError("Restore not implemented for this database type")

# Database migration utilities
class DatabaseMigration:
    """Database migration utilities"""
    
    @staticmethod
    def run_migrations():
        """Run database migrations"""
        # This is a placeholder for proper migration system
        # In production, use Alembic or similar
        logger.info("Running database migrations...")
        db_config.create_tables()
        logger.info("Migrations completed")

# Query optimization utilities
class QueryOptimizer:
    """Query optimization utilities"""
    
    @staticmethod
    def get_paginated_query(query, page: int = 1, per_page: int = 20):
        """Get paginated results"""
        offset = (page - 1) * per_page
        return query.offset(offset).limit(per_page)
    
    @staticmethod
    def get_count_query(query):
        """Get count efficiently"""
        return query.with_entities(query.column_descriptions[0]['type'])
    
    @staticmethod
    def bulk_insert(session: Session, model_class, data_list: list):
        """Bulk insert for better performance"""
        try:
            session.bulk_insert_mappings(model_class, data_list)
            session.commit()
            logger.info(f"Bulk inserted {len(data_list)} records")
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk insert failed: {str(e)}")
            raise

# Connection pool monitoring
def get_pool_status() -> dict:
    """Get connection pool status"""
    pool = db_config.engine.pool
    
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid()
    }

# Initialize database
def init_database():
    """Initialize database with all optimizations"""
    try:
        db_config.create_tables()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
