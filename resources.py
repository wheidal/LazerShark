"""
Asset loading and management.
"""
import os
import sys

APP_NAME = "LazerSharkKillKill"
FROZEN = getattr(sys, 'frozen', False)
BASE_DIR = sys._MEIPASS if FROZEN else os.path.dirname(os.path.abspath(__file__))


def resource_path(*parts):
    """Absolute path to a bundled asset, whatever folder the game was started from."""
    return os.path.join(BASE_DIR, *parts)


def settings_path(filename):
    """Absolute path to a writable settings file.

    A packaged build unpacks to a temporary folder and may be installed under
    Program Files, so it saves per user. Running from source keeps the file
    beside the code.
    """
    if not FROZEN:
        return resource_path(filename)
    root = os.environ.get('APPDATA') or os.path.join(os.path.expanduser('~'), '.config')
    folder = os.path.join(root, APP_NAME)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, filename)
