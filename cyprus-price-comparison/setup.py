"""Setup script for the price comparison pipeline."""
import subprocess
import sys
from pathlib import Path


def main():
    """Run setup steps."""
    print("="*60)
    print("CYPRUS PRICE COMPARISON PIPELINE - SETUP")
    print("="*60)
    print()
    
    # Install Python dependencies
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("[OK] Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error installing dependencies: {e}")
        return 1
    
    # Install Playwright browsers
    print("\nInstalling Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("[OK] Playwright browsers installed")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error installing Playwright browsers: {e}")
        return 1
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")
    if not env_file.exists() and env_example.exists():
        print("\nCreating .env file from .env.example...")
        env_file.write_text(env_example.read_text())
        print("[OK] .env file created (please review and edit if needed)")
    
    # Create cache directory
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    print(f"\n[OK] Cache directory ready: {cache_dir}")
    
    print("\n" + "="*60)
    print("Setup complete! You can now run: python main.py")
    print("="*60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
