#!/usr/bin/env python3
"""
BRICKIT Quick Start Script
Automatically starts the application and opens browser
"""
import subprocess
import webbrowser
import time
import os

def main():
    print("🚀 Starting BRICKIT Application...")
    print("=" * 50)
    
    # Check if virtual environment exists
    venv_path = ".venv"
    if os.path.exists(venv_path):
        print("✅ Virtual environment found")
        activate_cmd = f".venv\\Scripts\\activate"
    else:
        print("⚠️  No virtual environment found, using system Python")
        activate_cmd = ""
    
    try:
        # Start the FastAPI server
        print("🔄 Starting FastAPI server...")
        server_process = subprocess.Popen(
            ["python", "llm.py"],
            cwd=os.getcwd(),
            shell=True
        )
        
        # Wait a moment for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Open browser
        print("🌐 Opening browser...")
        webbrowser.open("http://localhost:8000/ai-studio/fixed")
        
        print("✅ BRICKIT is running!")
        print("📱 Mobile AI Studio: http://localhost:8000/ai-studio/fixed")
        print("🏠 Home Page: http://localhost:8000/")
        print("🔐 Login: http://localhost:8000/login")
        print("\n💡 Press Ctrl+C to stop the server")
        
        # Wait for server process
        server_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping BRICKIT server...")
        if 'server_process' in locals():
            server_process.terminate()
        print("✅ Server stopped")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

if __name__ == "__main__":
    main()
