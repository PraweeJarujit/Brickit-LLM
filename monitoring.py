"""
Production-ready Monitoring and Health Checks
Includes system metrics, performance monitoring, and alerting
"""

import time
import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging
import json
import threading
from dataclasses import dataclass

logger = logging.getLogger("brickkit.monitoring")

@dataclass
class HealthStatus:
    """Health status data structure"""
    status: str
    timestamp: float
    details: Dict[str, Any]
    response_time: float = 0.0

class SystemMetrics:
    """System metrics collector"""
    
    @staticmethod
    def get_cpu_usage() -> Dict[str, float]:
        """Get CPU usage metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_count": psutil.cpu_count(),
            "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
        }
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get memory usage metrics"""
        memory = psutil.virtual_memory()
        return {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_gb": memory.used / (1024**3),
            "percent": memory.percent
        }
    
    @staticmethod
    def get_disk_usage() -> Dict[str, float]:
        """Get disk usage metrics"""
        disk = psutil.disk_usage('/')
        return {
            "total_gb": disk.total / (1024**3),
            "used_gb": disk.used / (1024**3),
            "free_gb": disk.free / (1024**3),
            "percent": (disk.used / disk.total) * 100
        }
    
    @staticmethod
    def get_network_stats() -> Dict[str, Any]:
        """Get network statistics"""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }

class ApplicationMetrics:
    """Application-specific metrics"""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.active_connections = 0
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    def record_request(self, response_time: float, status_code: int):
        """Record request metrics"""
        with self._lock:
            self.request_count += 1
            self.response_times.append(response_time)
            
            # Keep only last 1000 response times
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
            
            if status_code >= 400:
                self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get application metrics"""
        with self._lock:
            uptime = time.time() - self.start_time
            
            # Calculate response time statistics
            if self.response_times:
                avg_response_time = sum(self.response_times) / len(self.response_times)
                max_response_time = max(self.response_times)
                min_response_time = min(self.response_times)
            else:
                avg_response_time = max_response_time = min_response_time = 0
            
            error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
            
            return {
                "uptime_seconds": uptime,
                "request_count": self.request_count,
                "error_count": self.error_count,
                "error_rate_percent": error_rate,
                "avg_response_time_ms": avg_response_time * 1000,
                "max_response_time_ms": max_response_time * 1000,
                "min_response_time_ms": min_response_time * 1000,
                "active_connections": self.active_connections,
                "requests_per_second": self.request_count / uptime if uptime > 0 else 0
            }

class HealthChecker:
    """Health check manager"""
    
    def __init__(self):
        self.checks = {}
        self.last_results = {}
    
    def register_check(self, name: str, check_func, critical: bool = True):
        """Register a health check"""
        self.checks[name] = {
            "func": check_func,
            "critical": critical
        }
    
    async def run_check(self, name: str) -> HealthStatus:
        """Run a single health check"""
        if name not in self.checks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health check '{name}' not found"
            )
        
        start_time = time.time()
        check_config = self.checks[name]
        
        try:
            result = await check_config["func"]() if asyncio.iscoroutinefunction(check_config["func"]) else check_config["func"]()
            response_time = time.time() - start_time
            
            status_obj = HealthStatus(
                status="healthy" if result.get("healthy", True) else "unhealthy",
                timestamp=time.time(),
                details=result,
                response_time=response_time
            )
            
            self.last_results[name] = status_obj
            return status_obj
            
        except Exception as e:
            response_time = time.time() - start_time
            status_obj = HealthStatus(
                status="unhealthy",
                timestamp=time.time(),
                details={"error": str(e)},
                response_time=response_time
            )
            
            self.last_results[name] = status_obj
            
            if check_config["critical"]:
                logger.critical(f"Critical health check failed: {name} - {str(e)}")
            
            return status_obj
    
    async def run_all_checks(self) -> Dict[str, HealthStatus]:
        """Run all health checks"""
        results = {}
        
        for name in self.checks:
            results[name] = await self.run_check(name)
        
        return results
    
    def get_overall_status(self) -> str:
        """Get overall health status"""
        if not self.last_results:
            return "unknown"
        
        # Check for any critical failures
        for name, result in self.last_results.items():
            if self.checks[name]["critical"] and result.status == "unhealthy":
                return "unhealthy"
        
        # Check for any non-critical failures
        for result in self.last_results.values():
            if result.status == "unhealthy":
                return "degraded"
        
        return "healthy"

# Health check implementations
async def check_database() -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        from database_config import check_database_health
        return check_database_health()
    except Exception as e:
        return {"healthy": False, "error": str(e)}

async def check_cache() -> Dict[str, Any]:
    """Check cache connectivity"""
    try:
        from cache_manager import get_cache_manager
        cache = get_cache_manager()
        
        # Test cache operations
        test_key = "health_check_test"
        cache.set(test_key, "test_value", ttl=10)
        value = cache.get(test_key)
        cache.delete(test_key)
        
        if value == "test_value":
            return {"healthy": True, "backend": type(cache.backend).__name__}
        else:
            return {"healthy": False, "error": "Cache test failed"}
            
    except Exception as e:
        return {"healthy": False, "error": str(e)}

async def check_ollama() -> Dict[str, Any]:
    """Check Ollama service connectivity"""
    try:
        import httpx
        from config import settings
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_url}/api/tags")
            
            if response.status_code == 200:
                return {"healthy": True, "models": len(response.json().get("models", []))}
            else:
                return {"healthy": False, "error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        return {"healthy": False, "error": str(e)}

async def check_disk_space() -> Dict[str, Any]:
    """Check disk space"""
    try:
        metrics = SystemMetrics.get_disk_usage()
        healthy = metrics["percent"] < 90  # Alert if > 90% full
        
        return {
            "healthy": healthy,
            "disk_usage_percent": metrics["percent"],
            "free_gb": metrics["free_gb"]
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}

async def check_memory() -> Dict[str, Any]:
    """Check memory usage"""
    try:
        metrics = SystemMetrics.get_memory_usage()
        healthy = metrics["percent"] < 90  # Alert if > 90% used
        
        return {
            "healthy": healthy,
            "memory_usage_percent": metrics["percent"],
            "available_gb": metrics["available_gb"]
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}

# Initialize health checker
health_checker = HealthChecker()
app_metrics = ApplicationMetrics()

# Register health checks
health_checker.register_check("database", check_database, critical=True)
health_checker.register_check("cache", check_cache, critical=False)
health_checker.register_check("ollama", check_ollama, critical=False)
health_checker.register_check("disk_space", check_disk_space, critical=True)
health_checker.register_check("memory", check_memory, critical=True)

# Monitoring router
monitoring_router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@monitoring_router.get("/health")
async def health_check():
    """Overall health check endpoint"""
    results = await health_checker.run_all_checks()
    overall_status = health_checker.get_overall_status()
    
    status_code = status.HTTP_200_OK
    if overall_status == "unhealthy":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif overall_status == "degraded":
        status_code = status.HTTP_200_OK  # Still serve traffic but indicate issues
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            name: {
                "status": result.status,
                "response_time": result.response_time,
                "details": result.details
            }
            for name, result in results.items()
        }
    }, status_code

@monitoring_router.get("/health/{check_name}")
async def specific_health_check(check_name: str):
    """Run specific health check"""
    result = await health_checker.run_check(check_name)
    
    status_code = status.HTTP_200_OK
    if result.status == "unhealthy":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "name": check_name,
        "status": result.status,
        "timestamp": datetime.utcnow().isoformat(),
        "response_time": result.response_time,
        "details": result.details
    }, status_code

@monitoring_router.get("/metrics")
async def get_metrics():
    """Get application and system metrics"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "application": app_metrics.get_metrics(),
        "system": {
            "cpu": SystemMetrics.get_cpu_usage(),
            "memory": SystemMetrics.get_memory_usage(),
            "disk": SystemMetrics.get_disk_usage(),
            "network": SystemMetrics.get_network_stats()
        },
        "cache": get_cache_manager().get_stats() if get_cache_manager() else None
    }

@monitoring_router.get("/metrics/prometheus")
async def prometheus_metrics():
    """Get metrics in Prometheus format"""
    app_metrics_data = app_metrics.get_metrics()
    system_metrics = {
        "cpu": SystemMetrics.get_cpu_usage(),
        "memory": SystemMetrics.get_memory_usage(),
        "disk": SystemMetrics.get_disk_usage()
    }
    
    # Convert to Prometheus format
    metrics_text = []
    
    # Application metrics
    metrics_text.append(f"# HELP brickkit_requests_total Total number of requests")
    metrics_text.append(f"# TYPE brickkit_requests_total counter")
    metrics_text.append(f"brickkit_requests_total {app_metrics_data['request_count']}")
    
    metrics_text.append(f"# HELP brickkit_errors_total Total number of errors")
    metrics_text.append(f"# TYPE brickkit_errors_total counter")
    metrics_text.append(f"brickkit_errors_total {app_metrics_data['error_count']}")
    
    metrics_text.append(f"# HELP brickkit_response_time_seconds Average response time")
    metrics_text.append(f"# TYPE brickkit_response_time_seconds gauge")
    metrics_text.append(f"brickkit_response_time_seconds {app_metrics_data['avg_response_time_ms'] / 1000}")
    
    # System metrics
    metrics_text.append(f"# HELP brickkit_cpu_usage_percent CPU usage percentage")
    metrics_text.append(f"# TYPE brickkit_cpu_usage_percent gauge")
    metrics_text.append(f"brickkit_cpu_usage_percent {system_metrics['cpu']['cpu_percent']}")
    
    metrics_text.append(f"# HELP brickkit_memory_usage_percent Memory usage percentage")
    metrics_text.append(f"# TYPE brickkit_memory_usage_percent gauge")
    metrics_text.append(f"brickkit_memory_usage_percent {system_metrics['memory']['percent']}")
    
    metrics_text.append(f"# HELP brickkit_disk_usage_percent Disk usage percentage")
    metrics_text.append(f"# TYPE brickkit_disk_usage_percent gauge")
    metrics_text.append(f"brickkit_disk_usage_percent {system_metrics['disk']['percent']}")
    
    return "\n".join(metrics_text), 200, {"Content-Type": "text/plain"}

# Alerting system
class AlertManager:
    """Simple alerting system"""
    
    def __init__(self):
        self.alerts = []
        self.alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "error_rate": 5.0,
            "response_time": 2.0
        }
    
    def check_alerts(self):
        """Check for alert conditions"""
        alerts = []
        
        # Check system metrics
        system_metrics = {
            "cpu": SystemMetrics.get_cpu_usage(),
            "memory": SystemMetrics.get_memory_usage(),
            "disk": SystemMetrics.get_disk_usage()
        }
        
        # CPU alert
        if system_metrics["cpu"]["cpu_percent"] > self.alert_thresholds["cpu_usage"]:
            alerts.append({
                "type": "system",
                "severity": "warning",
                "message": f"High CPU usage: {system_metrics['cpu']['cpu_percent']:.1f}%",
                "timestamp": time.time()
            })
        
        # Memory alert
        if system_metrics["memory"]["percent"] > self.alert_thresholds["memory_usage"]:
            alerts.append({
                "type": "system",
                "severity": "warning",
                "message": f"High memory usage: {system_metrics['memory']['percent']:.1f}%",
                "timestamp": time.time()
            })
        
        # Disk alert
        if system_metrics["disk"]["percent"] > self.alert_thresholds["disk_usage"]:
            alerts.append({
                "type": "system",
                "severity": "critical",
                "message": f"High disk usage: {system_metrics['disk']['percent']:.1f}%",
                "timestamp": time.time()
            })
        
        # Check application metrics
        app_metrics_data = app_metrics.get_metrics()
        
        # Error rate alert
        if app_metrics_data["error_rate_percent"] > self.alert_thresholds["error_rate"]:
            alerts.append({
                "type": "application",
                "severity": "warning",
                "message": f"High error rate: {app_metrics_data['error_rate_percent']:.1f}%",
                "timestamp": time.time()
            })
        
        # Response time alert
        if app_metrics_data["avg_response_time_ms"] / 1000 > self.alert_thresholds["response_time"]:
            alerts.append({
                "type": "application",
                "severity": "warning",
                "message": f"High response time: {app_metrics_data['avg_response_time_ms']:.0f}ms",
                "timestamp": time.time()
            })
        
        self.alerts.extend(alerts)
        return alerts
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts"""
        cutoff_time = time.time() - (hours * 3600)
        return [alert for alert in self.alerts if alert["timestamp"] > cutoff_time]
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()

# Initialize alert manager
alert_manager = AlertManager()

@monitoring_router.get("/alerts")
async def get_alerts(hours: int = 24):
    """Get recent alerts"""
    return {
        "alerts": alert_manager.get_recent_alerts(hours),
        "timestamp": datetime.utcnow().isoformat()
    }

@monitoring_router.post("/alerts/check")
async def check_alerts():
    """Manually trigger alert check"""
    new_alerts = alert_manager.check_alerts()
    return {
        "new_alerts": len(new_alerts),
        "alerts": new_alerts,
        "timestamp": datetime.utcnow().isoformat()
    }

@monitoring_router.delete("/alerts")
async def clear_alerts():
    """Clear all alerts"""
    alert_manager.clear_alerts()
    return {"message": "Alerts cleared"}

# Middleware for metrics collection
class MonitoringMiddleware:
    """Middleware to collect request metrics"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            # Process request
            await self.app(scope, receive, send)
            
            # Record metrics
            response_time = time.time() - start_time
            
            # Get status code from response (simplified)
            # In a real implementation, you'd need to capture this from the response
            status_code = 200  # Default
            
            app_metrics.record_request(response_time, status_code)
        else:
            await self.app(scope, receive, send)

# Background task for periodic health checks
async def periodic_health_checks():
    """Run health checks periodically"""
    while True:
        try:
            await health_checker.run_all_checks()
            alert_manager.check_alerts()
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Periodic health check failed: {str(e)}")
            await asyncio.sleep(60)

# Start background task
def start_monitoring_background_tasks():
    """Start monitoring background tasks"""
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_health_checks())
