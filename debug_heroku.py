#!/usr/bin/env python3
import os
import subprocess
import glob

def debug_heroku():
    """Comprehensive debug of Heroku environment"""
    print("🔍 Comprehensive Heroku Debug")
    print("=" * 50)
    
    # Check if we're on Heroku
    print(f"DYNO: {os.environ.get('DYNO', 'Not set')}")
    print(f"Running on Heroku: {'Yes' if os.environ.get('DYNO') else 'No'}")
    
    # Check environment variables
    print(f"\n📋 Environment Variables:")
    env_vars = ['GOOGLE_CHROME_BIN', 'CHROMEDRIVER_PATH', 'PATH']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"{var}: {value}")
    
    # Check common directories
    print(f"\n📁 Checking common directories:")
    dirs_to_check = [
        '/usr/bin',
        '/usr/local/bin', 
        '/app/.apt/usr/bin',
        '/app/.apt/usr/local/bin',
        '/app/.heroku/vendor/bin'
    ]
    
    for dir_path in dirs_to_check:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path} exists")
            # List some files in the directory
            try:
                files = os.listdir(dir_path)
                chrome_files = [f for f in files if 'chrome' in f.lower()]
                if chrome_files:
                    print(f"   Chrome-related files: {chrome_files}")
            except:
                pass
        else:
            print(f"❌ {dir_path} does not exist")
    
    # Search for Chrome and ChromeDriver
    print(f"\n🔍 Searching for Chrome and ChromeDriver:")
    
    # Search patterns
    search_patterns = [
        '/usr/bin/google-chrome*',
        '/usr/local/bin/google-chrome*',
        '/app/.apt/usr/bin/google-chrome*',
        '/app/.apt/usr/local/bin/google-chrome*',
        '/app/.heroku/vendor/bin/google-chrome*',
        '/usr/bin/chromedriver*',
        '/usr/local/bin/chromedriver*',
        '/app/.apt/usr/bin/chromedriver*',
        '/app/.apt/usr/local/bin/chromedriver*',
        '/app/.heroku/vendor/bin/chromedriver*'
    ]
    
    found_files = []
    for pattern in search_patterns:
        matches = glob.glob(pattern)
        if matches:
            found_files.extend(matches)
            print(f"✅ Found: {matches}")
    
    if not found_files:
        print("❌ No Chrome or ChromeDriver files found")
    
    # Check if we can find them in PATH
    print(f"\n🔍 Checking PATH for Chrome:")
    try:
        result = subprocess.run(['which', 'google-chrome'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ google-chrome found at: {result.stdout.strip()}")
        else:
            print("❌ google-chrome not found in PATH")
    except Exception as e:
        print(f"Error checking PATH: {e}")
    
    try:
        result = subprocess.run(['which', 'chromedriver'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ chromedriver found at: {result.stdout.strip()}")
        else:
            print("❌ chromedriver not found in PATH")
    except Exception as e:
        print(f"Error checking PATH: {e}")
    
    # Check buildpack info
    print(f"\n📦 Buildpack Information:")
    try:
        # Check if buildpack files exist
        buildpack_dirs = [
            '/app/.heroku/buildpacks',
            '/app/.buildpacks'
        ]
        for dir_path in buildpack_dirs:
            if os.path.exists(dir_path):
                print(f"✅ Buildpack directory: {dir_path}")
                try:
                    files = os.listdir(dir_path)
                    print(f"   Files: {files}")
                except:
                    pass
            else:
                print(f"❌ Buildpack directory not found: {dir_path}")
    except Exception as e:
        print(f"Error checking buildpacks: {e}")

if __name__ == "__main__":
    debug_heroku() 