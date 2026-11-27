# -*- mode: python ; coding: utf-8 -*-
# PyInstaller recipe for the Windows and Mac builds. Run it through build_windows_installer.py,
# which also writes version_info.txt and makes the installer, or build_mac_app.py, which
# makes the .app and the disk image.
#
# Only the files the game loads are bundled. Never add the whole assets folder: it holds
# art whose licence isn't confirmed.
import os
import sys

MAC = sys.platform == 'darwin'
VERSION = os.environ.get('LAZERSHARK_VERSION', '3.1.0')  # Set by the build scripts

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/hai_0.png', 'assets'),
        ('sounds', 'sounds'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'numpy', 'matplotlib', 'scipy', 'pandas', 'PIL', 'pytest'],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

# A folder build, not one file: it starts faster and upsets antivirus less.
# UPX is off for the same reason.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LazerSharkKillKill',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/shark_icon.icns' if MAC else 'assets/shark_icon.ico',
    version=None if MAC else 'version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='LazerSharkKillKill',
)

if MAC:
    app = BUNDLE(
        coll,
        name='Lazer Shark Kill! Kill!.app',
        icon='assets/shark_icon.icns',
        bundle_identifier='io.github.wheidal.lazershark',
        version=VERSION,
        info_plist={
            'CFBundleName': 'Lazer Shark Kill! Kill!',
            'CFBundleDisplayName': 'Lazer Shark Kill! Kill!',
            'CFBundleShortVersionString': VERSION,
            'CFBundleVersion': VERSION,
            'LSApplicationCategoryType': 'public.app-category.arcade-games',
            'NSHumanReadableCopyright': 'Copyright (c) 2026 wheidal',
        },
    )
