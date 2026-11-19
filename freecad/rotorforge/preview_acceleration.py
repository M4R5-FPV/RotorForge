"""Lossless preview acceleration; never used by the manufacturing pipeline."""
from collections import OrderedDict
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile


class LocalPathContains:
    """Reuse native Qt containment on only contours that can contain a point.

    A closed contour outside its control-point bounds has zero net winding
    about the test point. Dropping those contours preserves both native fill
    rules. Curves and their original coordinates are copied, not flattened.
    Keep an inexpensive fallback for unusual or unsupported path formats.
    """
    def __init__(self, path, QtGui):
        self.path = path
        self.parts = []
        self.cache = OrderedDict()
        self.QtGui = QtGui
        if path.elementCount() < 80:
            return
        try:
            parts = []
            current = None
            i = 0
            while i < path.elementCount():
                e = path.elementAt(i)
                if e.isMoveTo():
                    if current is not None and not current.isEmpty():
                        parts.append(current)
                    current = QtGui.QPainterPath()
                    current.moveTo(e.x, e.y)
                elif current is None:
                    return
                elif e.isLineTo():
                    current.lineTo(e.x, e.y)
                elif e.isCurveTo() and i+2 < path.elementCount():
                    b, c = path.elementAt(i+1), path.elementAt(i+2)
                    current.cubicTo(e.x, e.y, b.x, b.y, c.x, c.y)
                    i += 2
                else:
                    return
                i += 1
            if current is not None and not current.isEmpty():
                parts.append(current)
            if len(parts) < 4:
                return
            for part in parts:
                r = part.controlPointRect()
                self.parts.append((r.left(), r.top(), r.right(), r.bottom(), part))
        except (AttributeError, TypeError, RuntimeError, ValueError):
            self.parts = []

    def contains(self, point):
        if not self.parts:
            return self.path.contains(point)
        x, y = point.x(), point.y()
        if not math.isfinite(x) or not math.isfinite(y):
            return self.path.contains(point)
        eps = 1e-6
        ids = tuple(i for i, (l, t, r, b, _) in enumerate(self.parts)
                    if l-eps <= x <= r+eps and t-eps <= y <= b+eps)
        if not ids:
            return False
        if len(ids) == len(self.parts):
            return self.path.contains(point)
        subset = self.cache.get(ids)
        if subset is None:
            subset = self.QtGui.QPainterPath()
            for i in ids:
                subset.addPath(self.parts[i][4])
            subset.setFillRule(self.path.fillRule())
            self.cache[ids] = subset
            while len(self.cache) > 32:
                self.cache.popitem(last=False)
        else:
            self.cache.move_to_end(ids)
        return subset.contains(point)


# Store only the unmodified, native-DPI Fit-view pixels; the editor still
# uses its exact vector paths for zoom, pan, editing and other view sizes.
MAX_FILES = 24
MAX_BYTES = 64*1024*1024
MAX_PNG = 24*1024*1024


def preview_cache_location(app):
    if os.environ.get('ROTORFORGE_DISABLE_DISK_CACHE') == '1':
        return None
    override = os.environ.get('ROTORFORGE_CACHE_DIR')
    if override:
        return Path(override).parent / (Path(override).name + '_previews')
    getter = getattr(app, 'getUserCachePath', None)
    root = getter() if getter else str(Path(app.getUserAppDataDir()) / 'Cache')
    return Path(root) / 'RotorForge' / 'previews'


def preview_cache_key(key, version, qt_version, texture_stamp):
    raw = json.dumps([1, version, qt_version, sys.platform, texture_stamp, key],
                     ensure_ascii=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def read_preview(directory, digest, QtGui, width, height, dpr):
    if directory is None:
        return None
    try:
        filename = directory / (digest + '.png')
        if filename.stat().st_size > MAX_PNG:
            return None
        reader = QtGui.QImageReader(str(filename), b'PNG')
        dimensions = reader.size()
        if dimensions.width() != width or dimensions.height() != height:
            return None
        image = reader.read()
        if image.isNull():
            return None
        pixmap = QtGui.QPixmap.fromImage(image)
        if pixmap.isNull():
            return None
        pixmap.setDevicePixelRatio(dpr)
        try: os.utime(filename, None)
        except OSError: pass
        return pixmap
    except (OSError, ValueError, RuntimeError, TypeError):
        return None


def write_preview(directory, digest, pixmap):
    if directory is None or pixmap.isNull():
        return
    if pixmap.width()*pixmap.height()*4 > MAX_PNG:
        return
    temporary = None
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=directory, suffix='.tmp', delete=False) as f:
            temporary = Path(f.name)
        if not pixmap.save(str(temporary), 'PNG') or temporary.stat().st_size > MAX_PNG:
            return
        os.replace(temporary, directory / (digest+'.png'))
        temporary = None
        files = [(f.stat().st_mtime, f.stat().st_size, f) for f in directory.glob('*.png')]
        total = 0
        for i, (_, size, f) in enumerate(sorted(files, reverse=True)):
            total += size
            if i >= MAX_FILES or total > MAX_BYTES:
                f.unlink(missing_ok=True)
    except (OSError, ValueError, RuntimeError, TypeError):
        pass
    finally:
        if temporary is not None:
            try: temporary.unlink(missing_ok=True)
            except OSError: pass
