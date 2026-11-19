"""Consistent, cross-platform names for user-facing project exports."""
import re
from pathlib import Path, PureWindowsPath

_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
_RESERVED = re.compile(r'^(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)', re.I)
_GENERIC = re.compile(r'^(?:RotorForge|Untitled|Unnamed)(?:[ _-]?\d+)?$', re.I)


def safe_project_name(value):
    """Preserve ordinary names and spaces, but prevent invalid path segments."""
    name = _INVALID.sub('_', str(value or '')).strip().rstrip('. ')
    if not name or name in ('.', '..'):
        return ''
    # Leave room for export suffixes and keep UTF-8 length portable.
    name = name.encode('utf-8')[:160].decode('utf-8', errors='ignore').rstrip('. ')
    if _RESERVED.match(name):
        name = '_' + name
    return name


def project_name(document=None):
    """Prefer the visible FreeCAD project label, then the saved project stem."""
    if document is not None:
        label = safe_project_name(getattr(document, 'Label', ''))
        filename = getattr(document, 'FileName', '') or ''
        stem = safe_project_name(PureWindowsPath(str(filename)).stem) if filename else ''
        if label and not _GENERIC.fullmatch(label):
            return label
        if stem:
            return stem
        if label and not label.casefold().startswith('rotorforge'):
            return label
    return 'Untitled'


def image_name(document=None, preview=False, look=None):
    name=project_name(document)
    if look:
        name += ' ' + safe_project_name(look)
    return name + ('_preview.png' if preview else '.png')


def available_image_path(path):
    """Keep the base name when free; otherwise allocate the next version."""
    path=Path(path)
    # Compare names case-insensitively for portable exports, including JPEG.
    names={p.name.casefold() for p in path.parent.iterdir()} if path.parent.is_dir() else set()
    if path.name.casefold() not in names:return path
    n=1
    while True:
        candidate=path.with_name(f'{path.stem} v{n}{path.suffix}')
        if candidate.name.casefold() not in names:return candidate
        n+=1


def settings_name(document=None):
    return project_name(document) + '.json'


def pictures_directory(standard_paths):
    """Use Qt's OS-aware Pictures location, including redirected/localized folders.

    Accept the QStandardPaths class so this module stays independent of Qt and
    can be tested without loading the FreeCAD GUI.
    """
    home = Path.home()
    try:
        location = getattr(standard_paths, 'PicturesLocation', None)
        if location is None:
            location = standard_paths.StandardLocation.PicturesLocation
        native = standard_paths.writableLocation(location)
    except (AttributeError, RuntimeError, TypeError):
        native = ''
    folder = Path(native) if native else home / 'Pictures'
    try:
        folder.mkdir(parents=True, exist_ok=True)
        if folder.is_dir():
            return folder
    except OSError:
        pass
    # Keep the save dialog usable if the configured Pictures location is
    # unavailable (for example, a disconnected redirected folder).
    return home
