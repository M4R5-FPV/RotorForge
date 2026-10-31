"""Update an older guarded frame and render the corrected editor preview."""
import os, sys, json, traceback
from pathlib import Path
root = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(root))
import freecad
freecad.__path__.insert(0, str(root/'freecad'))
from dataclasses import replace
import FreeCAD as App
from PySide import QtWidgets
from freecad.rotorforge import document as d, geometry as g
from freecad.rotorforge.gui import FrameDialog

out = Path(os.environ['ROTORFORGE_TEST_OUTPUT']); out.mkdir(parents=True, exist_ok=True)
checks, failures = [], []
try:
    doc = App.openDocument(os.environ['ROTORFORGE_LEGACY_FRAME'])
    frame = doc.getObject('FrameParameters'); p = d.read_parameters(frame)
    assert p.FlexSideGuards and p.StrapSlotsEnabled and p.StrapOpeningStyle == 'Outline cutouts'
    objs = d.component_objects(frame)
    before = {role: objs[role].Shape.copy() for role in ('ElectronicsGuardLeft', 'ElectronicsGuardRight')}
    plain = g.build_shapes(replace(p, StrapSlotsEnabled=False))
    d.update_frame(frame, p); objs = d.component_objects(frame)
    opening = plain['TopPlate'].cut(objs['TopPlate'].Shape)
    old_fill = sum(s.common(opening).Volume for s in before.values())
    assert old_fill > .1, 'legacy fixture must reproduce the filled strap cutout'
    for role in before:
        shape = objs[role].Shape
        assert shape.isValid() and len(shape.Solids) == 1 and objs[role].ViewObject.Visibility
        assert shape.common(opening).Volume < 1e-6
    checks.append(dict(check='saved legacy geometry updates to clear strap passages', old_fill_mm3=old_fill))
    win = FrameDialog(); win.set_values(p); win.refresh()
    win.preview.grab().save(str(out/'EditorPreview0872.png'))
    assert win.preview.last_error is None
    win.close(); checks.append('editor preview paints with bridged guard outlines')
    saved = out/'MigratedGuardStraps0872.FCStd'; doc.saveAs(str(saved)); App.closeDocument(doc.Name)
    doc = App.openDocument(str(saved)); objs = d.component_objects(doc.getObject('FrameParameters'))
    for role in before:
        assert objs[role].Shape.common(opening).Volume < 1e-6
    App.closeDocument(doc.Name); checks.append('saved updated guards reopen with clear strap passages')
except Exception:
    failures.append(traceback.format_exc())
(out/'gui_checks.json').write_text(json.dumps(dict(checks=checks, failures=failures), indent=2))
print(failures or checks, flush=True)
os._exit(1 if failures else 0)
