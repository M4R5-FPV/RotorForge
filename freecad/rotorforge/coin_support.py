"""Load FreeCAD's bundled Pivy bindings before accessing native scene nodes.

No GUI dependency is imported until a GUI caller asks for Coin3D.
"""
_coin = None
_reported = set()


def _report_once(key, message, warning=False):
    if key in _reported:
        return
    try:
        import FreeCAD as App
        printer = App.Console.PrintWarning if warning else App.Console.PrintMessage
        printer(message + "\n")
    except Exception:
        return
    _reported.add(key)


def initialize_coin():
    """Return the Coin module, or None if this optional GUI binding fails.

    Cache successful imports only, so a later GUI operation can recover if
    the bindings could not be loaded during workbench initialization.
    """
    global _coin
    if _coin is None:
        try:
            from pivy import coin
        except MemoryError:
            raise
        except Exception as exc:
            _report_once("import", f"RotorForge: Pivy/Coin3D initialization failed: {exc}", True)
            return None
        _coin = coin
        _report_once("initialized", "RotorForge: Pivy/Coin3D initialized.")
    return _coin


def scene_root(view):
    """Access an optional texture scene graph only after loading SWIG.

    FreeCAD's RootNode getter can itself throw before any Coin3D method is
    called. Do not let an unavailable scene graph discard a valid CAD solid.
    """
    if initialize_coin() is None:
        return None
    try:
        return getattr(view, "RootNode", None)
    except MemoryError:
        raise
    except Exception as exc:
        _report_once("root", f"RotorForge: texture scene graph unavailable; using base colours: {exc}", True)
        return None
