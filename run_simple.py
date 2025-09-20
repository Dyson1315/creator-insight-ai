#!/usr/bin/env python3
"""
Simple runner for the Creator-VRidge AI Recommendation API
For environments without pip/venv
"""

import sys
import subprocess
import os

def check_python():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ required")
        sys.exit(1)
    print(f"Python {sys.version} found")

def install_packages():
    """Install required packages"""
    packages = [
        "fastapi[all]==0.104.1",
        "uvicorn[standard]==0.24.0", 
        "pydantic==2.5.0",
        "pydantic-settings==2.1.0",
        "sqlalchemy==2.0.23",
        "python-multipart==0.0.6",
        "python-dotenv==1.0.0"
    ]
    
    print("Installing required packages...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError:
            print(f"Warning: Could not install {package}")
        except FileNotFoundError:
            print("Error: pip not found. Please install pip first.")
            sys.exit(1)

def setup_database():
    """Create database tables"""
    try:
        from app.core.database import init_db
        print("Initializing database...")
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")

def run_server():
    """Run the FastAPI server"""
    try:
        import uvicorn
        print("Starting server...")
        print("API will be available at: http://localhost:8000")
        print("API documentation: http://localhost:8000/docs")
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    except ImportError:
        print("Error: uvicorn not installed")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    print("Creator-VRidge AI Recommendation System Setup")
    print("=" * 50)
    
    check_python()
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("Creating .env file...")
        with open(".env", "w") as f:
            f.write("""DEBUG=True
SECRET_KEY=dev-secret-key
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./creator_insight.db
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
""")
    
    install_packages()
    setup_database()
    run_server()