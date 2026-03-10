"""
Production-ready Logging Configuration
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Add color to level name
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        
        return super().format(record)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_rotation: str = "1 day",
    log_retention: str = "30 days"
):
    """Setup production-ready logging"""
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        # Parse rotation time (e.g., "1 day", "1 hour", "1 week")
        when = 'midnight'
        interval = 1
        if 'hour' in log_rotation:
            when = 'H'
            interval = int(log_rotation.split()[0])
        elif 'day' in log_rotation:
            when = 'midnight'
            interval = int(log_rotation.split()[0])
        elif 'week' in log_rotation:
            when = 'W0'  # Monday
            interval = int(log_rotation.split()[0])
        
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_file,
            when=when,
            interval=interval,
            backupCount=30  # Keep 30 backup files
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

class RequestLogger:
    """Custom logger for HTTP requests"""
    
    def __init__(self, logger_name: str = "brickkit.requests"):
        self.logger = logging.getLogger(logger_name)
    
    def log_request(self, method: str, url: str, status_code: int, 
                   response_time: float, client_ip: str, user_agent: str):
        """Log HTTP request details"""
        self.logger.info(
            f"{method} {url} - {status_code} - {response_time:.3f}s - {client_ip} - {user_agent[:50]}"
        )
    
    def log_error(self, method: str, url: str, error: Exception, 
                  client_ip: str, user_agent: str):
        """Log HTTP request error"""
        self.logger.error(
            f"{method} {url} - ERROR: {str(error)} - {client_ip} - {user_agent[:50]}"
        )

class SecurityLogger:
    """Logger for security events"""
    
    def __init__(self, logger_name: str = "brickkit.security"):
        self.logger = logging.getLogger(logger_name)
    
    def log_login_attempt(self, username: str, success: bool, ip: str):
        """Log login attempts"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.warning(f"LOGIN_{status}: {username} from {ip}")
    
    def log_rate_limit(self, ip: str, endpoint: str):
        """Log rate limit violations"""
        self.logger.warning(f"RATE_LIMIT: {ip} exceeded limit on {endpoint}")
    
    def log_suspicious_activity(self, activity: str, details: dict, ip: str):
        """Log suspicious activities"""
        self.logger.critical(f"SUSPICIOUS: {activity} - {details} from {ip}")

class DatabaseLogger:
    """Logger for database operations"""
    
    def __init__(self, logger_name: str = "brickkit.database"):
        self.logger = logging.getLogger(logger_name)
    
    def log_query(self, query_type: str, table: str, duration: float, 
                  affected_rows: int = None):
        """Log database queries"""
        message = f"DB_{query_type}: {table} - {duration:.3f}s"
        if affected_rows is not None:
            message += f" - {affected_rows} rows"
        self.logger.debug(message)
    
    def log_error(self, operation: str, error: Exception):
        """Log database errors"""
        self.logger.error(f"DB_ERROR: {operation} - {str(error)}")

# Performance monitoring
class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, logger_name: str = "brickkit.performance"):
        self.logger = logging.getLogger(logger_name)
    
    def log_slow_query(self, query: str, duration: float, threshold: float = 1.0):
        """Log slow database queries"""
        if duration > threshold:
            self.logger.warning(f"SLOW_QUERY: {duration:.3f}s - {query[:100]}")
    
    def log_memory_usage(self, process_name: str, memory_mb: float):
        """Log memory usage"""
        self.logger.info(f"MEMORY: {process_name} - {memory_mb:.1f}MB")
    
    def log_api_response_time(self, endpoint: str, method: str, 
                             response_time: float, threshold: float = 2.0):
        """Log API response times"""
        if response_time > threshold:
            self.logger.warning(f"SLOW_API: {method} {endpoint} - {response_time:.3f}s")

# Initialize loggers
request_logger = RequestLogger()
security_logger = SecurityLogger()
database_logger = DatabaseLogger()
performance_logger = PerformanceLogger()
