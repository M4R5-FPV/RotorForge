"""Native GUI: colours/restore and editor switches, with JSON result outside GUI console."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge import geometry as g,document as d
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True);checks=[];fail=[]
try:
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
 saved=(g.build_shapes,g.build_for_update)
 def reject(*a,**k):raise AssertionError('CAD construction in editor preview')
 g.build_shapes=g.build_for_update=reject
 p=Parameters(DetailedMotorReferences=True,DetailedPropReferences=True,DetailedStackReference=True,DetailedCameraReference=True,FPVEnabled=True,StandoffHeight=35.,TopFrontShape='Camera U recess',TopFrontDepth=28.,TopFrontRecessWidth=14.,TopFrontSetback=0.,FlexFrontBumper=True,FlexBumperShape='V-recess shoe',FlexBumperTipWidth=45.,FlexBumperRecess=65.,FlexBumperLipReach=8.)
 win=FrameDialog();win.set_values(p);win.refresh();assert win.values()==p
 assert not win.controls['PropReferenceHeight'].isEnabled()
 assert win.controls['FlexBumperTipWidth'].isEnabled() and win.controls['FlexBumperRecess'].isEnabled()
 win.preview.grab();assert win.preview.last_error is None
 win.set_values(replace(p,ShowReferences=False));win.refresh();assert not win.controls['DetailedMotorReferences'].isEnabled()
 win.close();g.build_shapes,g.build_for_update=saved;checks.append('New controls round-trip and live preview does not build CAD')
 doc=App.newDocument();frame=d.create_frame(p,doc);objs=d.component_objects(frame)
 for role in ('MotorEnvelopes','PropellerDiscs','StackEnvelope','CameraEnvelope'):
  obj=objs[role];view=obj.ViewObject
  assert len(view.DiffuseColor)==len(obj.Shape.Faces),(role,len(view.DiffuseColor),len(obj.Shape.Faces))
  assert view.Transparency<=8,role
  if role!='PropellerDiscs':assert len(set(view.DiffuseColor))>=2,role
 checks.append('Per-face reference colours and opaque detailed bodies')
 q=replace(p,DetailedMotorReferences=False,DetailedPropReferences=False,DetailedStackReference=False,DetailedCameraReference=False)
 d.update_frame(frame,q)
 for role,t in (('MotorEnvelopes',50),('PropellerDiscs',86),('StackEnvelope',68),('CameraEnvelope',15)):
  obj=objs[role];assert obj.ViewObject.Transparency==t,role;assert len(obj.ViewObject.DiffuseColor)==1,role
 checks.append('Disabling detail restores simple geometry, colours and transparency')
except Exception:fail.append(traceback.format_exc())
(out/'presentation_gui.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));os._exit(1 if fail else 0)
