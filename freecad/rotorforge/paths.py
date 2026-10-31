"""Runtime assets live inside the namespaced package, including wheel installs."""
from pathlib import Path
RESOURCE_DIR = Path(__file__).resolve().parent / "resources"

def icon_path(name="frame.svg"):
    return str(RESOURCE_DIR / "icons" / name)

def help_path():
    return str(RESOURCE_DIR / "docs" / "RotorForge_Help.pdf")
