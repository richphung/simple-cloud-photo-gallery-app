#!/usr/bin/env python3
"""
Startup script for the FastAPI server
"""
import sys
import os
import uvicorn

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Import the app
from app.main import app

if __name__ == "__main__":
    print("Starting Simple Cloud Photo Gallery API Server...")
    print("Server will be available at: http://127.0.0.1:8002")
    print("Health check: http://127.0.0.1:8002/health")
    print("API docs: http://127.0.0.1:8002/docs")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=8002, 
            log_level="info",
            reload=False
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
