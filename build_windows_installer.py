"""
Builds Lazer Shark Kill! Kill! for Windows: the game folder, a portable ZIP and an installer.

Run on Windows, from the project folder, with the build requirements installed:

    pip install -r requirements.txt -r requirements_build.txt
    python build_windows_installer.py [--version 3.0.0]

The installer needs Inno Setup 6 (https://jrsoftware.org/isdl.php). Without it you still
get the game folder and the portable ZIP. Everything lands in dist/. The script exits with
an error code if any step fails, so a CI run fails with it.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import zipfile

GAME_NAME = "LazerSharkKillKill"
PRODUCT_NAME = "Lazer Shark Kill! Kill!"
VERSION = "3.0.0"
PUBLISHER = "wheidal"
DESCRIPTION = "Underwater arcade shooter with a laser-equipped shark"
YEAR = "2026"
APP_FOLDER = os.path.join('dist', GAME_NAME)

README = """Lazer Shark Kill! Kill! v{version}
{dashes}

Run LazerSharkKillKill.exe to play.

Controls (remappable in Settings)
  Arrow keys   Move
  Space        Fire
  P            Pause
  Esc          Quit
  F11          Full screen

On the title screen, S opens Settings and 1-6 jump straight to a boss.
A controller works once it's switched on in Settings.

Settings and high scores are saved in %APPDATA%\\LazerSharkKillKill.

Windows may warn that this app is from an unknown publisher, because the game
isn't digitally signed. Click "More info", then "Run anyway".

https://github.com/wheidal/LazerShark
"""


def step(message):
    print(f"\n== {message}", flush=True)


def fail(message):
    print(f"\nBUILD FAILED: {message}", flush=True)
    sys.exit(1)


def clean():
    for folder in ('build', 'dist'):
        if os.path.exists(folder):
            shutil.rmtree(folder)


def write_version_info(version):
    """The details Windows shows under the exe's Properties."""
    parts = (version.split('.') + ['0', '0', '0', '0'])[:4]
    numbers = ', '.join(str(int(part)) for part in parts)
    text = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({numbers}),
    prodvers=({numbers}),
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
          [StringStruct(u'CompanyName', u'{PUBLISHER}'),
          StringStruct(u'FileDescription', u'{DESCRIPTION}'),
          StringStruct(u'FileVersion', u'{version}'),
          StringStruct(u'InternalName', u'{GAME_NAME}'),
          StringStruct(u'LegalCopyright', u'Copyright (c) {YEAR} {PUBLISHER}'),
          StringStruct(u'OriginalFilename', u'{GAME_NAME}.exe'),
          StringStruct(u'ProductName', u'{PRODUCT_NAME}'),
          StringStruct(u'ProductVersion', u'{version}')])
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    with open('version_info.txt', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(text)


def build_game():
    result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', f'{GAME_NAME}.spec'])
    if result.returncode != 0:
        fail("PyInstaller didn't finish")
    exe = os.path.join(APP_FOLDER, f'{GAME_NAME}.exe')
    if not os.path.exists(exe):
        fail(f"{exe} wasn't made")
    bundled = os.path.join(APP_FOLDER, '_internal')
    for needed in (os.path.join('assets', 'hai_0.png'), os.path.join('sounds', 'laser.wav'),
                   os.path.join('sounds', 'music', 'title.wav')):
        if not os.path.exists(os.path.join(bundled, needed)):
            fail(f"{needed} is missing from the build")


def write_readme(version):
    title = f"{PRODUCT_NAME} v{version}"
    with open(os.path.join(APP_FOLDER, 'README.txt'), 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(README.format(version=version, dashes='=' * len(title)))


def make_zip(version):
    path = os.path.join('dist', f'{GAME_NAME}_v{version}_Portable.zip')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for root, _, files in os.walk(APP_FOLDER):
            for name in files:
                full = os.path.join(root, name)
                archive.write(full, os.path.join(GAME_NAME, os.path.relpath(full, APP_FOLDER)))
    return path


def find_iscc():
    found = shutil.which('iscc')
    if found:
        return found
    for root in (os.environ.get('ProgramFiles(x86)'), os.environ.get('ProgramFiles'),
                 os.environ.get('LOCALAPPDATA') and os.path.join(os.environ['LOCALAPPDATA'], 'Programs')):
        if root:
            candidate = os.path.join(root, 'Inno Setup 6', 'ISCC.exe')
            if os.path.exists(candidate):
                return candidate
    return None


def make_installer(version, required):
    iscc = find_iscc()
    if not iscc:
        message = "Inno Setup 6 isn't installed, so there's no installer. Get it from https://jrsoftware.org/isdl.php"
        if required:
            fail(message)
        print(message)
        return None
    result = subprocess.run([iscc, f'/DMyAppVersion={version}', 'installer_setup.iss'])
    if result.returncode != 0:
        fail("Inno Setup didn't finish")
    path = os.path.join('dist', 'installer', f'{GAME_NAME}_Setup_v{version}.exe')
    if not os.path.exists(path):
        fail(f"{path} wasn't made")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument('--version', default=VERSION, help=f"version number, such as {VERSION}")
    parser.add_argument('--require-installer', action='store_true',
                        help="fail if Inno Setup isn't installed, instead of skipping the installer")
    args = parser.parse_args()
    version = args.version.lstrip('v')
    if not re.fullmatch(r'\d+(\.\d+){0,3}', version):
        fail(f"the version must be numbers and dots, such as {VERSION}, not {args.version}")
    if sys.platform != 'win32':
        fail("this builds a Windows game, so it has to run on Windows")

    step(f"Building {PRODUCT_NAME} v{version}")
    clean()
    write_version_info(version)
    step("Packing the game with PyInstaller")
    build_game()
    write_readme(version)
    step("Making the portable ZIP")
    zip_path = make_zip(version)
    step("Making the installer")
    installer = make_installer(version, args.require_installer)

    step("Done")
    print(f"Game folder:  {APP_FOLDER}")
    print(f"Portable ZIP: {zip_path}")
    if installer:
        print(f"Installer:    {installer}")


if __name__ == '__main__':
    main()
