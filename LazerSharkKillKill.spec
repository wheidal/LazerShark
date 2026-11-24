# -*- mode: python ; coding: utf-8 -*-
# PyInstaller recipe for the Windows build. Run it through build_windows_installer.py,
# which also writes version_info.txt and makes the installer.
#
# Only the files the game loads are bundled. Never add the whole assets folder: it holds
# art whose licence isn't confirmed.

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
    icon='assets/shark_icon.ico',
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='LazerSharkKillKill',
)
