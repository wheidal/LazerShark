"""
Builds Lazer Shark Kill! Kill! for the Mac: the .app and a disk image (.dmg) to drag it from.

Run on a Mac, from the project folder, with the build requirements installed:

    pip install -r requirements.txt -r requirements_build.txt
    python build_mac_app.py [--version 3.1.0] [--smoke-test]

The app is built for the Mac it runs on: Apple Silicon (arm64) or Intel (x86_64).
GitHub Actions builds both. Everything lands in dist/. The script exits with an error
code if any step fails, so a CI run fails with it.

The app isn't signed with an Apple Developer ID, so macOS asks players to allow it the
first time. README.txt in the disk image explains how.
"""
import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time

from build_windows_installer import (CONTROLS, GAME_NAME, PRODUCT_NAME, VERSION, check_version, clean, fail,
                                     run_pyinstaller, step)

APP = os.path.join('dist', f'{PRODUCT_NAME}.app')
EXECUTABLE = os.path.join(APP, 'Contents', 'MacOS', GAME_NAME)
ARCH_NAMES = {'arm64': 'AppleSilicon', 'x86_64': 'Intel'}
SMOKE_SECONDS = 8

README = """{product} v{version} for Mac ({arch})
{dashes}

To install, drag {product} into the Applications folder.

The first time you open it, macOS says it can't check the game for malicious
software, because the game isn't signed with an Apple Developer ID. To allow it:
  1. Open the game once and click Done (or OK) on the warning.
  2. Open System Settings > Privacy & Security.
  3. Scroll down to the message about {product} and click Open Anyway.
  4. Confirm with your password. After that it opens normally.

{controls}

Settings and high scores are saved in ~/Library/Application Support/{folder}.

https://github.com/wheidal/LazerShark
"""


def check_app(arch):
    if not os.path.exists(EXECUTABLE):
        fail(f"{EXECUTABLE} wasn't made")
    bundled = [os.path.join(root, name).replace(os.sep, '/') for root, _, files in os.walk(APP) for name in files]
    for needed in ('assets/hai_0.png', 'sounds/laser.wav', 'sounds/music/title.wav'):
        if not any(path.endswith('/' + needed) for path in bundled):
            fail(f"{needed} is missing from the app")
    archs = subprocess.run(['lipo', '-archs', EXECUTABLE], capture_output=True, text=True).stdout.split()
    if arch not in archs:
        fail(f"the app was built for {' '.join(archs) or 'nothing'}, not {arch}")


def smoke_test():
    """Start the app with no screen or sound and make sure it's still running a few seconds later."""
    with tempfile.TemporaryDirectory() as home:
        env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', HOME=home)
        game = subprocess.Popen([EXECUTABLE], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        time.sleep(SMOKE_SECONDS)
        crashed = game.poll() is not None
        if not crashed:
            game.terminate()
        output = game.communicate(timeout=10)[0]
        if crashed:
            print(output)
            fail(f"the app stopped within {SMOKE_SECONDS} seconds, with exit code {game.returncode}")
        settings = os.path.join(home, 'Library', 'Application Support', GAME_NAME)
        if not os.path.isdir(settings):
            fail(f"the app didn't make its settings folder, {settings}")
    print(f"The app ran for {SMOKE_SECONDS} seconds and made its settings folder")


def make_dmg(version, arch):
    """A compressed disk image holding the app, a shortcut to Applications and the readme."""
    staging = os.path.join('build', 'dmg')
    if os.path.exists(staging):
        shutil.rmtree(staging)
    os.makedirs(staging)
    # ditto keeps the bundle's symlinks and signature intact
    if subprocess.run(['ditto', APP, os.path.join(staging, os.path.basename(APP))]).returncode != 0:
        fail("couldn't copy the app into the disk image folder")
    os.symlink('/Applications', os.path.join(staging, 'Applications'))
    title = f"{PRODUCT_NAME} v{version} for Mac ({ARCH_NAMES[arch]})"
    with open(os.path.join(staging, 'README.txt'), 'w', encoding='utf-8') as f:
        f.write(README.format(product=PRODUCT_NAME, version=version, arch=ARCH_NAMES[arch],
                              dashes='=' * len(title), controls=CONTROLS, folder=GAME_NAME))

    path = os.path.join('dist', f'{GAME_NAME}_v{version}_Mac_{ARCH_NAMES[arch]}.dmg')
    # hdiutil now and then fails with "Resource busy" on a busy machine, so it gets a few tries
    for attempt in range(3):
        result = subprocess.run(['hdiutil', 'create', '-volname', PRODUCT_NAME, '-srcfolder', staging,
                                 '-ov', '-format', 'UDZO', path])
        if result.returncode == 0 and os.path.exists(path):
            return path
        time.sleep(5)
    fail("hdiutil couldn't make the disk image")


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument('--version', default=VERSION, help=f"version number, such as {VERSION}")
    parser.add_argument('--smoke-test', action='store_true',
                        help="start the built app for a few seconds to check it doesn't crash")
    args = parser.parse_args()
    version = check_version(args.version)
    if sys.platform != 'darwin':
        fail("this builds a Mac app, so it has to run on a Mac")
    arch = platform.machine()
    if arch not in ARCH_NAMES:
        fail(f"don't know how to name a build for {arch}")

    step(f"Building {PRODUCT_NAME} v{version} for {ARCH_NAMES[arch]} Macs")
    clean()
    step("Packing the game with PyInstaller")
    run_pyinstaller(version)
    check_app(arch)
    if args.smoke_test:
        step("Starting the app to check it runs")
        smoke_test()
    step("Making the disk image")
    dmg = make_dmg(version, arch)

    step("Done")
    print(f"App:        {APP}")
    print(f"Disk image: {dmg}")


if __name__ == '__main__':
    main()
