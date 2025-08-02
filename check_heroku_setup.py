#!/usr/bin/env python3
import os
import subprocess

def check_paths():
    """Check what Chrome and ChromeDriver paths are available on Heroku"""
    print("🔍 Checking Heroku Chrome setup...")
    
    # Check if we're on Heroku
    if os.environ.get('DYNO'):
        print("✅ Running on Heroku")
    else:
        print("ℹ️  Running locally")
    
    # Check environment variables
    print(f"\n📋 Environment Variables:")
    print(f"DYNO: {os.environ.get('DYNO', 'Not set')}")
    print(f"GOOGLE_CHROME_BIN: {os.environ.get('GOOGLE_CHROME_BIN', 'Not set')}")
    print(f"CHROMEDRIVER_PATH: {os.environ.get('CHROMEDRIVER_PATH', 'Not set')}")
    
    # Check possible Chrome paths
    possible_chrome_paths = [
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/app/.apt/usr/bin/google-chrome',
        '/app/.apt/usr/bin/google-chrome-stable'
    ]
    
    print(f"\n🔍 Checking Chrome paths:")
    for path in possible_chrome_paths:
        exists = os.path.exists(path)
        print(f"  {path}: {'✅' if exists else '❌'}")
    
    # Check possible ChromeDriver paths
    possible_chromedriver_paths = [
        '/usr/bin/chromedriver',
        '/app/.apt/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver'
    ]
    
    print(f"\n🔍 Checking ChromeDriver paths:")
    for path in possible_chromedriver_paths:
        exists = os.path.exists(path)
        print(f"  {path}: {'✅' if exists else '❌'}")
    
    # Try to find Chrome and ChromeDriver
    print(f"\n🎯 Finding available binaries:")
    
    chrome_binary = None
    for path in possible_chrome_paths:
        if os.path.exists(path):
            chrome_binary = path
            break
    
    chromedriver_path = None
    for path in possible_chromedriver_paths:
        if os.path.exists(path):
            chromedriver_path = path
            break
    
    print(f"Chrome binary: {chrome_binary or '❌ Not found'}")
    print(f"ChromeDriver: {chromedriver_path or '❌ Not found'}")
    
    # Check if we can run Chrome
    if chrome_binary:
        try:
            result = subprocess.run([chrome_binary, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            print(f"Chrome version: {result.stdout.strip()}")
        except Exception as e:
            print(f"Error running Chrome: {e}")
    
    if chromedriver_path:
        try:
            result = subprocess.run([chromedriver_path, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            print(f"ChromeDriver version: {result.stdout.strip()}")
        except Exception as e:
            print(f"Error running ChromeDriver: {e}")

if __name__ == "__main__":
    check_paths() 