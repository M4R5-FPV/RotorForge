"""Editor round-trip/enabling and black materials on reused hardware."""
import os,sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge import document as d,hardware_refs as hw
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];fail=[]
try:
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
 Gui.showMainWindow()
 original=Gui.getMainWindow;Gui.getMainWindow=lambda:None
 win=FrameDialog();p=Parameters(PlateDesign='2 plates',FPVEnabled=True,BottomRearShape='Cable channel',CameraTabBottomRearOffset=.5,CameraTabTopFrontOffset=-.5)
 win.set_values(p);win.refresh()
 assert win.values()==p
 assert win.controls['BottomRearShape'].isEnabled() and not win.controls['MidRearShape'].isEnabled()
 assert win.controls['TopRearShape'].count()==18 and win.controls['BottomNoseShape'].count()==14
 assert win.controls['CameraTabTopFrontOffset'].minimum()<0
 win.set_values(replace(p,PlateDesign='3 plates'));win.refresh()
 assert not win.controls['BottomRearShape'].isEnabled() and win.controls['MidRearShape'].isEnabled()
 win.close();Gui.getMainWindow=original
 checks.append('All new controls round-trip, signed offsets and plate-mode enable rules')
 Gui.showMainWindow()
 doc=App.newDocument();f=d.create_frame(Parameters(ArmNutMount='M3 press nut',StackPressNuts=True),doc)
 hw.refresh(f)
 objs=hw.objects(f);assert objs
 for o in objs:
  assert max(o.ViewObject.ShapeColor[:3])<.06
 before={o.Name:(o.Shape.exportBrepToString(),o.HardwareSignature) for o in objs}
 # A stale silver reference is recoloured without changing its current BRep.
 for o in objs:o.ViewObject.ShapeColor=(.6,.62,.65)
 objs[0].ViewObject.Visibility=False
 hw.refresh(f,automatic=True)
 for o in hw.objects(f):
  assert max(o.ViewObject.ShapeColor[:3])<.06
  if 'ShapeAppearance' in o.ViewObject.PropertiesList:assert max(o.ViewObject.ShapeAppearance[0].DiffuseColor[:3])<.06
  assert (o.Shape.exportBrepToString(),o.HardwareSignature)==before[o.Name],(o.HardwareRole,o.HardwareSignature,before[o.Name][1])
 assert not objs[0].ViewObject.Visibility
 doc.saveAs(str(out/'BlackHardware.FCStd'))
 checks.append('Black screws/nuts/press nuts; existing refs recolour with stable BRePs and visibility')
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'gui_edges.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));os._exit(1 if fail else 0)
