
#!/usr/bin/env python3
import subprocess
import sys
import time
import os

def start_backend():
    """Start the FastAPI backend server"""
    os.chdir('backend')
    return subprocess.Popen([
        sys.executable, '-m', 'uvicorn', 
        'yolo_fastapi_server:app', 
        '--host', '0.0.0.0', 
        '--port', '8000'
    ])

def start_frontend():
    """Start the frontend proxy server"""
    os.chdir('frontend')
    return subprocess.Popen([sys.executable, 'proxy.py'])

def main():
    print("Starting AI 4 Green application...")
    
    # Start backend
    print("Starting backend server...")
    backend_process = start_backend()
    
    # Wait a moment for backend to start
    time.sleep(2)
    
    # Change back to root directory
    os.chdir('..')
    
    # Start frontend
    print("Starting frontend proxy...")
    frontend_process = start_frontend()
    
    try:
        # Wait for both processes
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    main()
