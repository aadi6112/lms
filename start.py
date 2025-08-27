#!/usr/bin/env python3
"""
Policy Management System - Startup Script
Simple script to check dependencies and start the application
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print(" Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f" Python {sys.version.split()[0]} detected")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn', 
        'pandas',
        'openpyxl',
        'jinja2'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f" {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f" {package} is missing")
    
    return missing_packages

def install_dependencies():
    """Install missing dependencies"""
    print("\ Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print(" Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print(" Failed to install dependencies!")
        return False

def create_directories():
    """Create necessary directories"""
    dirs = ['uploads', 'static', 'templates']
    for directory in dirs:
        Path(directory).mkdir(exist_ok=True)
        print(f"Directory '{directory}' ready")

def check_files():
    """Check if required files exist"""
    required_files = [
        'main.py',
        'database.py', 
        'file_processor.py',
        'templates/index.html'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f" Missing file: {file_path}")
        else:
            print(f" Found: {file_path}")
    
    return missing_files

def main():
    """Main startup function"""
    print("Policy Management System - Startup Check")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    print("\n Checking files...")
    missing_files = check_files()
    if missing_files:
        print(f"\n Missing required files: {missing_files}")
        print("Please ensure all application files are in the current directory.")
        return False
    
    print("\n Checking dependencies...")
    missing_packages = check_dependencies()
    
    if missing_packages:
        print(f"\n Missing packages: {missing_packages}")
        
        if Path('requirements.txt').exists():
            install_choice = input("\n Install missing dependencies? (y/n): ").lower()
            if install_choice == 'y':
                if not install_dependencies():
                    return False
            else:
                print(" Cannot start without required dependencies!")
                return False
        else:
            print(" requirements.txt not found!")
            print("Please install manually: pip install fastapi uvicorn pandas openpyxl jinja2 python-multipart")
            return False
    
    print("\n Creating directories...")
    create_directories()
    
    print("\n" + "=" * 50)
    print(" All checks passed! Starting the application...")
    print("Server will be available at: http://localhost:8000")
    print(" Default login: admin / admin123")
    print(" API documentation: http://localhost:8000/api/docs")
    print("=" * 50)
    print("\n Starting server...")
    
    # Start the application
    try:
        import uvicorn
        from main import app
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError as e:
        print(f" Failed to start: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        return True
    except Exception as e:
        print(f" Server error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure Python 3.8+ is installed")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Ensure all files are in the same directory")
        print("4. Check that no other service is using port 8000")
        sys.exit(1)
