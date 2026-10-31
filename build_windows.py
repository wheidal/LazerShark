"""
Build script for creating Windows executable using PyInstaller
"""

import os
import sys
import shutil
import subprocess

def build_executable():
    """Build the Windows executable using PyInstaller"""
    
    print("🚀 Building Lazer Shark Kill! Kill! for Windows...")
    
    # PyInstaller command with options
    command = [
        sys.executable, '-m', 'PyInstaller',
        '--name', 'LazerSharkKillKill',
        '--onefile',  # Single executable file
        '--windowed',  # No console window
        '--icon', 'assets/hai_0.png',  # Game icon (if available)
        '--add-data', 'assets;assets',  # Include assets folder
        '--add-data', 'sounds;sounds',  # Include sounds folder
        '--add-data', 'sprites;sprites',  # Include sprites folder
        '--hidden-import', 'pygame',
        '--hidden-import', 'numpy',  # If still needed
        '--collect-all', 'pygame',  # Collect all pygame data
        'main.py'
    ]
    
    # Run PyInstaller
    try:
        subprocess.run(command, check=True)
        print("✅ Build successful!")
        print("📁 Executable located in: dist/LazerSharkKillKill.exe")
        
        # Optional: Create installer with NSIS or Inno Setup
        print("\n📦 Next steps for creating an installer:")
        print("1. Use Inno Setup (https://jrsoftware.org/isinfo.php)")
        print("2. Or NSIS (https://nsis.sourceforge.io/)")
        print("3. Or create a simple ZIP distribution")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False
    
    return True

def create_distribution_folder():
    """Create a distribution folder with all necessary files"""
    
    dist_folder = "LazerSharkKillKill_Windows"
    
    # Create distribution folder
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)
    os.makedirs(dist_folder)
    
    # Copy executable
    if os.path.exists("dist/LazerSharkKillKill.exe"):
        shutil.copy("dist/LazerSharkKillKill.exe", dist_folder)
    
    # Create README for distribution
    readme_content = """
# Lazer Shark Kill! Kill! - Windows Edition

## How to Play
Simply run LazerSharkKillKill.exe to start the game!

## System Requirements
- Windows 10 or later
- DirectX 9.0c or later
- 256MB RAM
- 50MB free disk space

## Controls
- Arrow Keys: Move
- Space: Fire Laser
- Left Alt: Fire Missile
- Left Ctrl: Fire Torpedo
- P: Pause
- Escape: Quit

## Troubleshooting
If the game doesn't start:
1. Make sure Windows Defender isn't blocking it
2. Try running as Administrator
3. Install Visual C++ Redistributables if needed

Enjoy the underwater mayhem! 🦈💥
"""
    
    with open(f"{dist_folder}/README.txt", "w") as f:
        f.write(readme_content)
    
    print(f"✅ Distribution folder created: {dist_folder}/")
    
    # Create a batch file for easy launching
    batch_content = """@echo off
title Lazer Shark Kill! Kill!
start LazerSharkKillKill.exe
exit"""
    
    with open(f"{dist_folder}/Play Game.bat", "w") as f:
        f.write(batch_content)

if __name__ == "__main__":
    # Install PyInstaller if not present
    try:
        import PyInstaller
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    if build_executable():
        create_distribution_folder()
        print("\n🎉 Build complete! Ready for distribution.")
