"""Runtime workbench assets and bundled Help manual."""
from pathlib import Path

RESOURCE_DIR = Path(__file__).resolve().parent / "resources"
_WORKBENCH_DIR = Path(__file__).resolve().parents[2]
_HELP_FILENAME = "RotorForge_Help.pdf"


def icon_path(name="frame.svg"):
    return str(RESOURCE_DIR / "icons" / name)


def help_path():
    """Find the workbench's bundled PDF manual.

    Normal ZIP / Addon Manager installs keep the PDF in RotorForge's root.
    Package-based installations may place it in the Python resources folder.
    The final fallback supports older installations with an external manual.
    """
    choices = (
        _WORKBENCH_DIR / _HELP_FILENAME,
        RESOURCE_DIR / "docs" / _HELP_FILENAME,
        _WORKBENCH_DIR.parent / _HELP_FILENAME,
    )
    return str(next((path for path in choices if path.is_file()), choices[0]))
