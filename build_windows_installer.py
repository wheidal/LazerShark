"""
Comprehensive build script for creating Windows installer for Lazer Shark Kill! Kill!
This script creates both a standalone executable and an Inno Setup installer.
"""

import os
import sys
import shutil
import subprocess
import zipfile
from datetime import datetime

# Configuration
GAME_NAME = "LazerSharkKillKill"
GAME_VERSION = "2.0.0"
AUTHOR = "Your Name"
DESCRIPTION = "Underwater arcade shooter with laser-equipped shark"

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name}/...")
            shutil.rmtree(dir_name)

def create_icon():
    """Convert PNG to ICO if needed"""
    icon_path = "assets/shark_icon.ico"
    if not os.path.exists(icon_path):
        try:
            from PIL import Image
            png_path = "assets/hai_0.png"
            if os.path.exists(png_path):
                img = Image.open(png_path)
                img.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
                print(f"✅ Created icon: {icon_path}")
        except ImportError:
            print("⚠️ Pillow not installed. Using PNG as icon.")
            icon_path = "assets/hai_0.png"
    return icon_path

def build_executable():
    """Build the Windows executable using PyInstaller"""
    print("\n🚀 Building Windows Executable...")
    
    icon_path = create_icon()
    
    # Create PyInstaller spec file
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('sounds', 'sounds'),
        ('sprites', 'sprites'),
        ('*.py', '.'),
    ],
    hiddenimports=['pygame', 'numpy'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pandas'],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='{GAME_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{icon_path}',
    version='version_info.txt'
)
'''
    
    # Write spec file
    with open(f'{GAME_NAME}.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    # Create version info file
    version_info = f'''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({GAME_VERSION.replace(".", ", ")}, 0),
    prodvers=({GAME_VERSION.replace(".", ", ")}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'{AUTHOR}'),
          StringStruct(u'FileDescription', u'{DESCRIPTION}'),
          StringStruct(u'FileVersion', u'{GAME_VERSION}'),
          StringStruct(u'InternalName', u'{GAME_NAME}'),
          StringStruct(u'LegalCopyright', u'Copyright (c) 2024 {AUTHOR}'),
          StringStruct(u'OriginalFilename', u'{GAME_NAME}.exe'),
          StringStruct(u'ProductName', u'Lazer Shark Kill! Kill!'),
          StringStruct(u'ProductVersion', u'{GAME_VERSION}')])
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    # Run PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        f'{GAME_NAME}.spec'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Executable built successfully!")
        print(f"📁 Location: dist/{GAME_NAME}.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_portable_zip():
    """Create a portable ZIP distribution"""
    print("\n📦 Creating Portable ZIP Distribution...")
    
    dist_name = f"{GAME_NAME}_v{GAME_VERSION}_Portable"
    dist_dir = f"dist/{dist_name}"
    
    # Create distribution directory
    os.makedirs(dist_dir, exist_ok=True)
    
    # Copy executable
    exe_path = f"dist/{GAME_NAME}.exe"
    if os.path.exists(exe_path):
        shutil.copy(exe_path, dist_dir)
    
    # Create README
    readme_content = f"""
# Lazer Shark Kill! Kill! - v{GAME_VERSION}
## Portable Edition

### How to Play
Simply run {GAME_NAME}.exe to start the game!

### System Requirements
- Windows 10 or later
- 256MB RAM
- 50MB free disk space
- DirectX 9.0c or later

### Controls
**Movement:**
- Arrow Keys or Gamepad Left Stick

**Weapons:**
- Space / A Button: Fire Laser
- Left Alt / B Button: Fire Missile  
- Left Ctrl / X Button: Fire Torpedo

**Other:**
- P / Start: Pause
- Escape: Quit

### Features
- Multiple weapon systems
- Shield powerups
- Background music with volume control
- Controller support
- Customizable controls
- Easy mode option

### Troubleshooting
If the game doesn't start:
1. Make sure Windows Defender isn't blocking it
2. Try running as Administrator
3. Install Visual C++ Redistributables if needed:
   https://aka.ms/vs/17/release/vc_redist.x64.exe

### Support
For issues or feedback, visit:
https://github.com/yourusername/lazer-shark-arcade

Enjoy the underwater mayhem! 🦈💥

Version {GAME_VERSION} - Built on {datetime.now().strftime('%Y-%m-%d')}
"""
    
    with open(f"{dist_dir}/README.txt", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Create batch launcher
    batch_content = f"""@echo off
title Lazer Shark Kill! Kill! v{GAME_VERSION}
echo Starting Lazer Shark Kill! Kill!...
start "" "{GAME_NAME}.exe"
exit"""
    
    with open(f"{dist_dir}/Play Game.bat", 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    # Create ZIP file
    zip_name = f"{dist_name}.zip"
    with zipfile.ZipFile(f"dist/{zip_name}", 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(dist_dir))
                zipf.write(file_path, arcname)
    
    print(f"✅ Portable ZIP created: dist/{zip_name}")
    return True

def create_installer():
    """Create Inno Setup installer"""
    print("\n🔧 Creating Inno Setup Installer...")
    
    # Update the existing Inno Setup script
    iss_content = f'''; Inno Setup Script for Lazer Shark Kill! Kill!
; Professional Windows Installer

#define MyAppName "Lazer Shark Kill! Kill!"
#define MyAppVersion "{GAME_VERSION}"
#define MyAppPublisher "{AUTHOR}"
#define MyAppURL "https://github.com/yourusername/lazer-shark-arcade"
#define MyAppExeName "{GAME_NAME}.exe"

[Setup]
AppId={{{{A8B3C4D5-E6F7-4A5B-9C3D-2E1F0A9B8C7D}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppVerName={{#MyAppName}} v{{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\LazerSharkKillKill
DefaultGroupName={{#MyAppName}}
AllowNoIcons=yes
OutputDir=dist\\installer
OutputBaseFilename={GAME_NAME}_Setup_v{GAME_VERSION}
SetupIconFile=assets\\hai_0.png
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={{app}}\\{{#MyAppExeName}}
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"
Name: "quicklaunchicon"; Description: "{{cm:CreateQuickLaunchIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\\{{#MyAppExeName}}"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "dist\\{GAME_NAME}_v{GAME_VERSION}_Portable\\README.txt"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{group}}\\Readme"; Filename: "{{app}}\\README.txt"
Name: "{{group}}\\{{cm:UninstallProgram,{{#MyAppName}}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: quicklaunchicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Any post-installation tasks
  end;
end;
'''
    
    # Write updated Inno Setup script
    with open('installer_setup.iss', 'w', encoding='utf-8') as f:
        f.write(iss_content)
    
    print("✅ Inno Setup script created: installer_setup.iss")
    print("\n📌 Next steps to create installer:")
    print("1. Download Inno Setup from: https://jrsoftware.org/isdl.php")
    print("2. Install Inno Setup")
    print("3. Open installer_setup.iss in Inno Setup Compiler")
    print("4. Click 'Compile' to create the installer")
    print("   OR run: iscc installer_setup.iss")
    
    # Try to compile if Inno Setup is installed
    try:
        result = subprocess.run(['iscc', 'installer_setup.iss'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n✅ Installer created successfully!")
            print(f"📁 Location: dist/installer/{GAME_NAME}_Setup_v{GAME_VERSION}.exe")
        else:
            print("\n⚠️ Inno Setup not found. Please install it and compile manually.")
    except FileNotFoundError:
        print("\n⚠️ Inno Setup compiler (iscc) not found in PATH.")
    
    return True

def main():
    """Main build process"""
    print(f"""
╔══════════════════════════════════════════════════════╗
║     Lazer Shark Kill! Kill! - Windows Build Tool     ║
║                    Version {GAME_VERSION}                     ║
╚══════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Clean
    clean_build_dirs()
    
    # Step 2: Build executable
    if not build_executable():
        print("\n❌ Build failed. Please check the errors above.")
        return 1
    
    # Step 3: Create portable distribution
    create_portable_zip()
    
    # Step 4: Create installer
    create_installer()
    
    print(f"""
╔══════════════════════════════════════════════════════╗
║                  BUILD COMPLETE! 🎉                   ║
╠══════════════════════════════════════════════════════╣
║ Outputs created:                                      ║
║ 1. Executable: dist/{GAME_NAME}.exe{'':18}║
║ 2. Portable ZIP: dist/{GAME_NAME}_v{GAME_VERSION}_Portable.zip{'':2}║
║ 3. Installer script: installer_setup.iss             ║
╚══════════════════════════════════════════════════════╝
    """)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
