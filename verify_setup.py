#!/usr/bin/env python3
"""
Virtual Environment and Setup Verification Script

This script helps verify that your development environment is properly configured
for the MongoDB Query Optimizer project.

Usage:
    python verify_setup.py

Requirements:
    - Must be run from within an activated virtual environment
    - All project dependencies should be installed
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path


def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_check(description, status, details=None):
    """Print a check result with status."""
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {description}")
    if details:
        print(f"   {details}")


def check_virtual_environment():
    """Check if running in a virtual environment."""
    print_header("Virtual Environment Check")
    
    # Check VIRTUAL_ENV environment variable
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print_check("Virtual environment detected", True, f"Path: {venv_path}")
        return True
    
    # Check if Python is in a venv directory
    python_path = sys.executable
    if 'venv' in python_path or 'virtualenv' in python_path:
        print_check("Virtual environment detected (via Python path)", True, f"Python: {python_path}")
        return True
    
    # Check sys.prefix vs sys.base_prefix (Python 3.3+)
    if hasattr(sys, 'base_prefix') and sys.prefix != sys.base_prefix:
        print_check("Virtual environment detected (via sys.prefix)", True, f"Prefix: {sys.prefix}")
        return True
    
    print_check("Virtual environment", False, "Not running in a virtual environment!")
    print("   Please activate your virtual environment:")
    print("   Linux/macOS: source venv/bin/activate")
    print("   Windows: venv\\Scripts\\activate")
    return False


def check_python_version():
    """Check Python version compatibility."""
    print_header("Python Version Check")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major == 3 and version.minor >= 8:
        print_check(f"Python version {version_str}", True, "Compatible with project requirements")
        return True
    else:
        print_check(f"Python version {version_str}", False, "Requires Python 3.8 or higher")
        return False


def check_required_packages():
    """Check if required packages are installed."""
    print_header("Required Packages Check")
    
    required_packages = [
        ('pymongo', 'MongoDB driver'),
        ('requests', 'HTTP library'),
        ('fastapi', 'Web framework (for mock LLM service)'),
        ('uvicorn', 'ASGI server (for mock LLM service)')
    ]
    
    all_installed = True
    
    for package_name, description in required_packages:
        try:
            spec = importlib.util.find_spec(package_name)
            if spec is not None:
                # Try to import to check if it's actually working
                module = importlib.import_module(package_name)
                version = getattr(module, '__version__', 'unknown')
                print_check(f"{package_name} ({description})", True, f"Version: {version}")
            else:
                print_check(f"{package_name} ({description})", False, "Not installed")
                all_installed = False
        except ImportError as e:
            print_check(f"{package_name} ({description})", False, f"Import error: {e}")
            all_installed = False
    
    if not all_installed:
        print("\n   To install missing packages:")
        print("   pip install -r requirements.txt")
    
    return all_installed


def check_project_files():
    """Check if essential project files exist."""
    print_header("Project Files Check")
    
    essential_files = [
        ('requirements.txt', 'Python dependencies'),
        ('mongo-optimiser-agent.py', 'Main entry point'),
        ('mongo_optimiser/__init__.py', 'Main package'),
        ('mongo_optimiser/main.py', 'Core optimization logic'),
        ('mongo_optimiser/db_utils.py', 'Database utilities'),
        ('mongo_optimiser/llm_utils.py', 'LLM integration'),
        ('seed_data.py', 'Database seeding script'),
        ('llm_stub/main.py', 'Mock LLM service'),
        ('.gitignore', 'Git ignore file')
    ]
    
    all_exist = True
    
    for file_path, description in essential_files:
        if Path(file_path).exists():
            print_check(f"{file_path} ({description})", True)
        else:
            print_check(f"{file_path} ({description})", False, "File not found")
            all_exist = False
    
    return all_exist


def check_git_status():
    """Check Git repository status."""
    print_header("Git Repository Check")
    
    try:
        # Check if we're in a git repository
        result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                              capture_output=True, text=True, check=True)
        print_check("Git repository", True, "Project is under version control")
        
        # Check if venv is properly ignored
        result = subprocess.run(['git', 'check-ignore', 'venv/'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_check("Virtual environment ignored by Git", True, "venv/ is in .gitignore")
        else:
            print_check("Virtual environment ignored by Git", False, 
                       "venv/ should be in .gitignore")
        
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_check("Git repository", False, "Not a Git repository or Git not installed")
        return False


def check_environment_variables():
    """Check for important environment variables."""
    print_header("Environment Variables Check")
    
    env_vars = [
        ('MONGO_URI', 'MongoDB connection string', False),
        ('MONGO_DB_NAME', 'Target database name', False),
        ('OPENROUTER_API_KEY', 'OpenRouter API key', False),
        ('VIRTUAL_ENV', 'Virtual environment path', True)
    ]
    
    for var_name, description, required in env_vars:
        value = os.environ.get(var_name)
        if value:
            # Mask sensitive values
            display_value = value if var_name != 'OPENROUTER_API_KEY' else f"{value[:8]}..."
            print_check(f"{var_name} ({description})", True, f"Set to: {display_value}")
        else:
            status = not required  # If not required, it's OK if not set
            status_text = "Optional - not set" if not required else "Required but not set"
            print_check(f"{var_name} ({description})", status, status_text)


def main():
    """Run all verification checks."""
    print("🔍 MongoDB Query Optimizer - Setup Verification")
    print("This script will verify your development environment setup.")
    
    checks = [
        ("Virtual Environment", check_virtual_environment),
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("Project Files", check_project_files),
        ("Git Repository", check_git_status),
        ("Environment Variables", check_environment_variables)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_check(f"{check_name} check", False, f"Error: {e}")
            results.append((check_name, False))
    
    # Summary
    print_header("Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Checks passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All checks passed! Your environment is ready for development.")
        print("\nNext steps:")
        print("1. Set up your MongoDB connection (MONGO_URI, MONGO_DB_NAME)")
        print("2. Get an OpenRouter API key (OPENROUTER_API_KEY)")
        print("3. Run: python mongo-optimiser-agent.py")
    else:
        print("\n⚠️  Some checks failed. Please address the issues above.")
        print("\nCommon solutions:")
        print("- Activate virtual environment: source venv/bin/activate")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Check file paths and project structure")


if __name__ == "__main__":
    main()
