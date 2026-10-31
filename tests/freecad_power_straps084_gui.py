"""Native UI controls, power-reference materials and negative offset persistence."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App
from PySide import QtWidgets
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge import document as d,geometry as g
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True);checks=[];fail=[]
try:
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([]);win=FrameDialog()
 p=Parameters(FPVEnabled=True,StandoffHeight=35.,TopFrontShape='Camera U recess',TopFrontDepth=28.,TopFrontRecessWidth=14.,TopFrontSetback=0.,DetailedVTXReference=True,DetailedBatteryReference=True,DetailedStackReference=True,FlexSideGuards=True,FlexGuardStraps=True,FlexGuardStrapAuto=False,FlexGuardStrapY2=-21.)
 saved=(g.build_shapes,g.build_for_update)
 def reject(*a,**k):raise AssertionError('CAD in live editor')
 g.build_shapes=g.build_for_update=reject
 win.set_values(p);win.refresh();assert win.values()==p
 assert win.controls['FlexGuardStrapY2'].isEnabled() and win.controls['FlexGuardStrapY2'].minimum()<0
 win.preview_mode.setCurrentIndex(win.preview_mode.findData('ElectronicsGuardLeft'));win.preview.grab();assert win.preview.last_error is None
 win.set_values(replace(p,FlexGuardStrapCount='1 strap'));win.refresh();assert not win.controls['FlexGuardStrapY2'].isEnabled()
 win.set_values(replace(p,FPVEnabled=False,BatteryReferenceEnabled=False));win.refresh();assert not win.controls['DetailedVTXReference'].isEnabled() and not win.controls['DetailedBatteryReference'].isEnabled()
 win.close();g.build_shapes,g.build_for_update=saved;checks.append('New controls, previews, signed offsets and enable rules without CAD')
 doc=App.newDocument();frame=d.create_frame(p,doc);objs=d.component_objects(frame)
 for role in ('VTXEnvelope','BatteryEnvelope','StackEnvelope'):
  obj=objs[role];assert obj.Shape.isValid() and not obj.Shape.isNull()
  assert len(obj.ViewObject.DiffuseColor)==len(obj.Shape.Faces)
  assert len(set(obj.ViewObject.DiffuseColor))>1 and obj.ViewObject.Transparency==0
 checks.append('Detailed power and stack reference per-face materials')
 d.update_frame(frame,replace(p,DetailedVTXReference=False,DetailedBatteryReference=False))
 for role,t in (('VTXEnvelope',35),('BatteryEnvelope',65)):
  assert objs[role].ViewObject.Transparency==t and len(objs[role].ViewObject.DiffuseColor)==1
 checks.append('Simple VTX and LiPo references restored on disable')
except Exception:fail.append(traceback.format_exc())
(out/'power_straps_gui.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));os._exit(1 if fail else 0)
