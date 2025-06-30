#!/usr/bin/env python3
"""
Setup script for Restaurant Review Scraper Chrome Extension.
This script helps set up the Chrome extension environment.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_header():
    print("🍽️  Restaurant Review Scraper - Chrome Extension Setup")
    print("=" * 60)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    required = ['requests', 'python-dotenv', 'flask', 'flask-cors']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} - missing")
    
    if missing:
        print(f"\n📦 Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists with DOG_KEY"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Create .env file with: DOG_KEY=your_api_key_here")
        return False
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            if 'DOG_KEY=' in content and not content.count('DOG_KEY=your_') > 0:
                print("✅ .env file found with DOG_KEY")
                return True
            else:
                print("⚠️  .env file exists but DOG_KEY may not be set properly")
                return False
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def check_scraper():
    """Check if the main scraper works"""
    try:
        from restaurant_review_scraper import RestaurantReviewScraper
        scraper = RestaurantReviewScraper()
        print("✅ Restaurant scraper initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Scraper initialization failed: {e}")
        return False

def check_extension_files():
    """Check if Chrome extension files exist"""
    ext_dir = Path('chrome-extension')
    required_files = [
        'manifest.json',
        'popup.html',
        'popup.js',
        'content.js',
        'background.js'
    ]
    
    if not ext_dir.exists():
        print("❌ chrome-extension directory not found")
        return False
    
    missing_files = []
    for file in required_files:
        file_path = ext_dir / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            missing_files.append(file)
            print(f"❌ {file} - missing")
    
    # Check for icons
    icons_dir = ext_dir / 'icons'
    icon_files = ['icon16.png', 'icon32.png', 'icon48.png', 'icon128.png']
    
    if icons_dir.exists():
        missing_icons = []
        for icon in icon_files:
            icon_path = icons_dir / icon
            if icon_path.exists():
                print(f"✅ icons/{icon}")
            else:
                missing_icons.append(icon)
                print(f"⚠️  icons/{icon} - missing")
        
        if missing_icons:
            print(f"\n💡 Create missing icon files or see chrome-extension/icons/README.md")
    else:
        print("⚠️  icons directory missing - create icons for the extension")
    
    return len(missing_files) == 0

def test_server():
    """Test if the extension server can start"""
    try:
        print("\n🧪 Testing server startup...")
        # Import and check server
        import extension_server
        print("✅ Extension server can be imported")
        return True
    except Exception as e:
        print(f"❌ Extension server test failed: {e}")
        return False

def create_quick_icons():
    """Create simple placeholder icons for testing"""
    icons_dir = Path('chrome-extension/icons')
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        sizes = [16, 32, 48, 128]
        for size in sizes:
            # Create a simple colored square with text
            img = Image.new('RGBA', (size, size), (102, 126, 234, 255))  # Blue background
            draw = ImageDraw.Draw(img)
            
            # Add text if size is large enough
            if size >= 32:
                try:
                    font_size = max(8, size // 4)
                    font = ImageFont.load_default()
                    text = "RR" if size >= 48 else "R"
                    
                    # Calculate text position to center it
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (size - text_width) // 2
                    y = (size - text_height) // 2
                    
                    draw.text((x, y), text, fill='white', font=font)
                except:
                    pass  # Skip text if font issues
            
            icon_path = icons_dir / f'icon{size}.png'
            img.save(icon_path)
            print(f"✅ Created {icon_path}")
        
        return True
    except ImportError:
        print("⚠️  PIL not available - create icons manually")
        return False
    except Exception as e:
        print(f"❌ Error creating icons: {e}")
        return False

def print_next_steps():
    """Print instructions for next steps"""
    print("\n🚀 Next Steps:")
    print("=" * 30)
    print("1. 📦 Install any missing dependencies:")
    print("   pip install -r requirements.txt")
    print("\n2. 🔑 Set up your API key (if not done):")
    print("   Create .env file with: DOG_KEY=your_scrapingdog_api_key")
    print("\n3. 🖼️  Create extension icons (if missing):")
    print("   See chrome-extension/icons/README.md")
    print("\n4. 🌐 Start the local server:")
    print("   python extension_server.py")
    print("\n5. 🔧 Install Chrome extension:")
    print("   • Go to chrome://extensions/")
    print("   • Enable Developer Mode")
    print("   • Click 'Load unpacked'")
    print("   • Select 'chrome-extension' folder")
    print("\n6. 🎯 Test the extension:")
    print("   • Go to Google Maps restaurant page")
    print("   • Click extension icon")
    print("   • Click 'Get Random Reviews'")
    print("\n📖 Full instructions: chrome-extension/README.md")

def main():
    print_header()
    
    all_good = True
    
    print("\n🔍 Checking Prerequisites:")
    print("-" * 30)
    
    if not check_python_version():
        all_good = False
    
    if not check_dependencies():
        all_good = False
    
    if not check_env_file():
        all_good = False
    
    if not check_scraper():
        all_good = False
    
    print("\n📁 Checking Extension Files:")
    print("-" * 30)
    
    if not check_extension_files():
        all_good = False
    
    print("\n🧪 Testing Components:")
    print("-" * 30)
    
    if not test_server():
        all_good = False
    
    # Offer to create icons if missing
    icons_dir = Path('chrome-extension/icons')
    if not icons_dir.exists() or len(list(icons_dir.glob('*.png'))) < 4:
        print("\n🖼️  Missing icons detected. Create simple placeholder icons? (y/n): ", end="")
        try:
            choice = input().lower().strip()
            if choice in ['y', 'yes']:
                create_quick_icons()
        except KeyboardInterrupt:
            print("\nSetup cancelled.")
            return
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("🎉 Setup Complete! Everything looks good.")
        print("\n✅ You're ready to:")
        print("   1. Start the server: python extension_server.py")
        print("   2. Install the Chrome extension")
        print("   3. Start scraping reviews!")
    else:
        print("⚠️  Setup Issues Found")
        print("   Please fix the issues above before proceeding.")
    
    print_next_steps()

if __name__ == '__main__':
    main() 