#!/usr/bin/env python3
"""
Master startup script for both frontend and backend
"""
import subprocess
import sys
import os
import time
import threading
import signal

def run_backend():
    """Start the backend server"""
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
    os.chdir(backend_dir)
    
    print("Starting Backend Server...")
    try:
        subprocess.run([sys.executable, "run_server.py"], check=True)
    except KeyboardInterrupt:
        print("\nBackend stopped")
    except Exception as e:
        print(f"Backend error: {e}")

def run_frontend():
    """Start the frontend server"""
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend-vue')
    
    print("Starting Frontend Server...")
    print("Note: Frontend will start in a separate window")
    print("If it doesn't start automatically, run manually:")
    print(f"  cd {frontend_dir}")
    print("  npm run dev")
    print()
    
    try:
        # Use shell=True to ensure proper environment
        subprocess.run(["npm", "run", "dev"], cwd=frontend_dir, shell=True, check=True)
    except KeyboardInterrupt:
        print("\nFrontend stopped")
    except Exception as e:
        print(f"Frontend error: {e}")
        print("Please run 'npm run dev' manually in the frontend-vue directory")

def main():
    print("Simple Cloud Photo Gallery - Development Environment")
    print("=" * 60)
    print("Backend API: http://127.0.0.1:8002")
    print("Frontend: http://localhost:3001")
    print("API proxy configured")
    print("Press Ctrl+C to stop all servers")
    print("=" * 60)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to start
    time.sleep(2)
    
    # Start frontend in main thread
    try:
        run_frontend()
    except KeyboardInterrupt:
        print("\nAll servers stopped")

if __name__ == "__main__":
    main()


