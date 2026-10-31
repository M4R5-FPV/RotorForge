"""Editor modes and migration of saved files from before the clamp fix."""
import sys, os, json, traceback
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import freecad
freecad.__path__.insert(0, str(root/'freecad'))
from dataclasses import replace
import FreeCAD as App
from PySide import QtWidgets
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge import document as d, geometry as g
out = Path(os.environ['ROTORFORGE_TEST_OUTPUT'])
out.mkdir(exist_ok=True, parents=True)
checks, failures = [], []
try:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    win = FrameDialog()
    base = Parameters(PlateDesign='2 plates', ArmBracesEnabled=True)
    for position in ('Below bottom plate', 'Above bottom plate'):
        p = replace(base, TwoPlateArmPosition=position)
        upper = position == 'Above bottom plate'
        active = 'ArmClampPlate' if upper else 'ArmLowerClampPlate'
        inactive = 'ArmLowerClampPlate' if upper else 'ArmClampPlate'
        win.set_values(p); win.refresh()
        assert win.values() == p
        assert win.controls['ArmBraceThickness'].isEnabled() == upper
        assert win.controls['UndersideClampThickness'].isEnabled() != upper
        assert win.preview_mode.findData(active) >= 0 and win.preview_mode.findData(inactive) < 0
        win.preview_mode.setCurrentIndex(win.preview_mode.findData(active))
        win.preview.grab(); assert win.preview.last_error is None
    win.set_values(replace(base, ArmBracesEnabled=False)); win.refresh()
    assert not win.controls['ArmBraceThickness'].isEnabled()
    assert not win.controls['UndersideClampThickness'].isEnabled()
    win.close(); checks.append('position-specific thickness controls and one active preview')
    for path in sorted(Path(os.environ['ROTORFORGE_LEGACY_FRAMES']).glob('*.FCStd')):
        doc = App.openDocument(str(path)); frame = doc.getObject('FrameParameters')
        p = d.read_parameters(frame)
        assert p.TwoPlateArmPosition == 'Below bottom plate' and p.ArmBracesEnabled
        d.update_frame(frame, p); objs = d.component_objects(frame)
        assert objs['ArmClampPlate'].Shape.isNull() and not objs['ArmClampPlate'].ViewObject.Visibility
        assert len(objs['ArmLowerClampPlate'].Shape.Solids) == 1 and objs['ArmLowerClampPlate'].ViewObject.Visibility
        assert objs['StackEnvelope'].Shape.BoundBox.ZMin == p.BottomThickness
        assert all(not objs[r].Shape.isNull() for r in g.carbon_roles(p))
        saved = out/('Migrated_'+path.name); doc.saveAs(str(saved)); App.closeDocument(doc.Name)
        doc = App.openDocument(str(saved)); objs = d.component_objects(doc.getObject('FrameParameters'))
        assert objs['ArmClampPlate'].Shape.isNull() and not objs['ArmClampPlate'].ViewObject.Visibility
        assert not objs['ArmLowerClampPlate'].Shape.isNull()
        App.closeDocument(doc.Name); checks.append('legacy migration: '+path.name)
    assert len(checks) == 3
except Exception:
    failures.append(traceback.format_exc())
(out/'gui_checks.json').write_text(json.dumps(dict(checks=checks, failures=failures), indent=2))
print(failures or checks, flush=True)
os._exit(1 if failures else 0)
