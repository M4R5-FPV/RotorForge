"""Bounded Blender discovery and launch configuration; no Qt/FreeCAD imports."""
import os
import re
import shutil
import sys
from pathlib import Path

FLATPAK_ID = 'org.blender.Blender'
FLATPAK_CHOICE = 'Flatpak: ' + FLATPAK_ID


def _glob(root, pattern):
    try:
        return sorted(root.glob(pattern), key=lambda p: tuple(int(s) for s in re.findall(r'\d+', str(p))) or (0,), reverse=True)
    except OSError:
        return []


def _exe(path, platform):
    if not path:
        return None
    p = Path(path)
    try:
        # Windows Store app-execution aliases can be reparse points.
        alias = (platform == 'win32' and p.name.lower() == 'blender.exe'
                 and p.parent.name.lower() == 'windowsapps')
        if (p.is_file() or (alias and os.path.lexists(p))) and (platform == 'win32' or os.access(p, os.X_OK)):
            return str(p.absolute())  # preserve Snap/alias symlinks, don't resolve
    except OSError:
        pass
    return None


def _registry_candidates():
    try:
        import winreg as r
    except ImportError:
        return []
    out = []
    for hive in (r.HKEY_CURRENT_USER, r.HKEY_LOCAL_MACHINE):
        for view in (0, r.KEY_WOW64_64KEY, r.KEY_WOW64_32KEY):
            for key, value, suffix in (
                (r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\blender.exe', '', ''),
                (r'SOFTWARE\Valve\Steam', 'InstallPath', 'steamapps'),
                (r'SOFTWARE\Valve\Steam', 'SteamPath', 'steamapps'),
            ):
                try:
                    with r.OpenKey(hive, key, 0, r.KEY_READ | view) as k:
                        value_text = str(r.QueryValueEx(k, value)[0]).strip('" ')
                    if value_text:
                        out.append((Path(os.path.expandvars(value_text)) / suffix if suffix else Path(os.path.expandvars(value_text)), bool(suffix)))
                except OSError:
                    pass
    return out


def _steam_libraries(steamapps):
    yield steamapps
    try:
        vdf = steamapps / 'libraryfolders.vdf'
        if vdf.stat().st_size > 2_000_000:
            return
        text = vdf.read_text(encoding='utf-8', errors='replace')
        for raw in re.findall(r'"(?:path|\d+)"\s+"([^"\n]+)"', text, re.I):
            p = Path(raw.replace('\\\\', '\\'))
            if p.is_absolute():
                yield p / 'steamapps'
    except OSError:
        pass


def _flatpak_installed(home, env, which):
    if not which('flatpak'):
        return False
    data = Path(env.get('XDG_DATA_HOME') or home / '.local/share')
    roots = [Path(env.get('FLATPAK_USER_DIR') or data / 'flatpak'),
             Path(env.get('FLATPAK_SYSTEM_DIR') or '/var/lib/flatpak')]
    for root in roots:
        try:
            if ((root/'app'/FLATPAK_ID/'current'/'active').is_dir() or
                    any(_glob(root/'app'/FLATPAK_ID, '*/*/active'))):
                return True
        except OSError:
            pass
    return False


def normalize_choice(value, *, platform=None, home=None, env=None, which=None):
    """Validate a remembered/manual path or the one supported package token."""
    platform = platform or sys.platform
    home = Path(home or Path.home())
    env = os.environ if env is None else env
    which = which or shutil.which
    value = str(value or '').strip().strip('"')
    if not value:
        return ''
    if value == FLATPAK_CHOICE:
        return value if platform.startswith('linux') and _flatpak_installed(home, env, which) else ''
    p = Path(os.path.expanduser(os.path.expandvars(value)))
    if platform == 'darwin' and p.suffix.lower() == '.app':
        for binary in ('Blender', 'blender'):
            found = _exe(p/'Contents/MacOS'/binary, platform)
            if found:
                return found
    found = _exe(p, platform) if p.is_absolute() else None
    if found:
        return found
    if p.name == str(p) and p.name.lower() in ('blender', 'blender.exe'):
        return _exe(which(p.name), platform) or ''
    return ''


def find_blender(saved='', *, platform=None, home=None, env=None, which=None, registry=None):
    """Saved selection first; native executables before sandboxed packages.

    Only fixed directories and immediate Blender-named children are inspected.
    No subprocess, recursive disk scan, or executable launch during discovery.
    """
    platform = platform or sys.platform
    home = Path(home or Path.home())
    env = os.environ if env is None else env
    which = which or shutil.which
    norm = lambda v: normalize_choice(v, platform=platform, home=home, env=env, which=which)
    if saved and (result := norm(saved)):
        return result
    candidates = []
    steam = []
    portable = []
    if platform == 'win32':
        # Standard folder, per-user installs, registry App Paths, Steam.
        program = [Path(env[key]) for key in ('ProgramW6432','ProgramFiles','ProgramFiles(x86)') if env.get(key)]
        if not program:
            program = [Path('C:/Program Files'), Path('C:/Program Files (x86)')]
        local = Path(env.get('LOCALAPPDATA') or home/'AppData/Local')
        roots = program + [local/'Programs', local]
        for root in roots:
            folder = root/'Blender Foundation'
            candidates += [p/'blender.exe' for p in _glob(folder, 'Blender*')]
            candidates += [root/'Blender'/'blender.exe']
        for item, is_steam in (registry or _registry_candidates)():
            if is_steam: steam.append(item)
            else: candidates.append(item)
        for root in program:
            steam.append(root/'Steam/steamapps')
        portable = [home/'Blender', home/'Applications', home/'Downloads', home/'Desktop']
        # Prefer a regular installation over the Store PATH alias.
        store_alias = local/'Microsoft/WindowsApps/blender.exe'
        candidates += [which('blender.exe'), which('blender')]
        for root in steam:
            candidates += [lib/'common/Blender/blender.exe' for lib in _steam_libraries(root)]
        for root in portable:
            candidates += [root/'blender.exe']+[p/'blender.exe' for p in _glob(root,'[Bb]lender*')]
        candidates.append(store_alias)
    elif platform == 'darwin':
        for root in (Path('/Applications'), home/'Applications', home/'Downloads'):
            for app in _glob(root,'[Bb]lender*.app'):
                candidates += [app/'Contents/MacOS'/name for name in ('Blender','blender')]
        candidates += [which('blender'), Path('/opt/homebrew/bin/blender'), Path('/usr/local/bin/blender')]
        steam = [home/'Library/Application Support/Steam/steamapps']
        for root in steam:
            for lib in _steam_libraries(root):
                for location in (lib/'common/Blender',lib/'common'):
                    for app in _glob(location,'[Bb]lender*.app'):
                        candidates += [app/'Contents/MacOS'/name for name in ('Blender','blender')]
    else:
        candidates += [which('blender'), '/usr/bin/blender','/usr/local/bin/blender','/snap/bin/blender', '/opt/blender/blender', home/'.local/bin/blender']
        for root in (Path('/opt'),Path('/usr/local'),home/'Applications',home/'Downloads',home/'blender',home/'.local/opt'):
            candidates += [root/'blender']+[p/'blender' for p in _glob(root,'[Bb]lender*')]+_glob(root,'[Bb]lender*.AppImage')+_glob(root,'[Bb]lender*.appimage')
        for root in (home/'.local/share/Steam/steamapps',home/'.steam/steam/steamapps',home/'.var/app/com.valvesoftware.Steam/data/Steam/steamapps'):
            for lib in _steam_libraries(root):
                candidates += [lib/'common/Blender/blender',lib/'common/Blender/Blender']
    for path in candidates:
        if (result := _exe(path, platform)):
            return result
    if platform.startswith('linux') and _flatpak_installed(home, env, which):
        return FLATPAK_CHOICE
    return ''


def launch_command(choice, temp, blender_args, which=None):
    """Argument vector, never a shell command. Flatpak gets only job access."""
    if choice == FLATPAK_CHOICE:
        executable = (which or shutil.which)('flatpak')
        if not executable:
            raise ValueError('Flatpak is unavailable. Detect Blender again.')
        return executable, ['run', '--filesystem='+str(Path(temp).absolute()), FLATPAK_ID, *blender_args]
    return choice, list(blender_args)


def flatpak_temp_parent():
    # Flatpak has a private /tmp. A unique home-based job directory is exposed
    # only to this launch and deleted after the render completes.
    parent = Path.home()/'.cache'/'RotorForge'/'render-jobs'
    parent.mkdir(parents=True, exist_ok=True)
    return parent


def stage_flatpak_job(temp, payload, script):
    """Copy the renderer, its pure-Python dependencies and texture assets."""
    temp, script = Path(temp), Path(script)
    for name in ('render_blender.py','render_presets.py','render_quality.py'):
        shutil.copyfile(script.parent/name,temp/name)
    for key in ('texture','edge_texture'):
        src = Path(payload[key])
        dst = temp / (key + src.suffix)
        shutil.copyfile(src,dst)
        payload[key] = str(dst)
    return temp/script.name
