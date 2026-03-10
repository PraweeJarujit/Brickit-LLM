"""
BRICKIT App Launcher
Production-ready app launcher
"""

import subprocess
import sys
import time
import webbrowser
import os

def start_frontend():
    """Start frontend server"""
    print("🌐 Starting Frontend Server...")
    try:
        # Start frontend in background
        subprocess.Popen([
            sys.executable, "-m", "http.server", "8080"
        ], cwd=os.getcwd())
        print("✅ Frontend running on http://localhost:8080")
        return True
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        return False

def start_backend():
    """Start backend server"""
    print("🔧 Starting Backend Server...")
    try:
        # Start backend in background
        subprocess.Popen([
            sys.executable, "llm_supabase.py"
        ], cwd=os.getcwd())
        print("✅ Backend running on http://localhost:8001")
        return True
    except Exception as e:
        print(f"❌ Backend error: {e}")
        return False

def open_browser():
    """Open browser tabs"""
    time.sleep(2)  # Wait for servers to start
    
    print("🌐 Opening browser...")
    webbrowser.open("http://localhost:8080/responsive_frontend.html")
    webbrowser.open("http://localhost:8001/docs")

def main():
    """Main launcher"""
    print("🚀 BRICKIT App Launcher")
    print("=" * 50)
    
    # Check if virtual environment is activated
    if ".venv" not in sys.executable:
        print("⚠️  Please activate virtual environment first:")
        print("   .\\.venv\\Scripts\\activate")
        return
    
    # Start services
    frontend_ok = start_frontend()
    backend_ok = start_backend()
    
    if frontend_ok and backend_ok:
        print("\n🎉 All services started successfully!")
        print("\n📱 Frontend: http://localhost:8080/responsive_frontend.html")
        print("🔧 Backend API: http://localhost:8001/docs")
        print("📊 Health Check: http://localhost:8001/health")
        
        # Open browser
        open_browser()
        
        print("\n💡 Press Ctrl+C to stop servers")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
    
    else:
        print("❌ Failed to start services")

if __name__ == "__main__":
    main()
