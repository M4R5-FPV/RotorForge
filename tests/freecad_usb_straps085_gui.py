import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import freecad
freecad.__path__.insert(0,str(Path(__file__).resolve().parents[1]/'freecad'))
from dataclasses import replace
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge import document as d,geometry as g
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);fail=[]
try:
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
 win=FrameDialog();p=Parameters(DetailedStackReference=True,StackUSBOffsetY=-2.,StrapOpeningStyle='Outline cutouts')
 saved=(g.build_shapes,g.build_for_update)
 def reject(*a,**kw):raise AssertionError('CAD called from live editor')
 g.build_shapes=g.build_for_update=reject
 win.set_values(p);win.refresh();assert win.values()==p
 assert win.controls['StrapNotchDepth'].isEnabled() and not win.controls['StrapSlotWidth'].isEnabled()
 assert win.controls['StackUSBOffsetY'].minimum()<0
 assert 'guard centre Y offset -2' in win.summary.text()
 win.preview_mode.setCurrentIndex(win.preview_mode.findData('TopPlate'));win.preview.grab();assert win.preview.last_error is None
 win.set_values(replace(p,StrapOpeningStyle='Slots',DetailedStackReference=False));win.refresh()
 assert win.controls['StrapSlotWidth'].isEnabled() and not win.controls['StrapNotchDepth'].isEnabled() and not win.controls['StackUSBOffsetY'].isEnabled()
 win.set_values(replace(p,StrapSlotsEnabled=False));win.refresh();assert not win.controls['StrapSlotLength'].isEnabled()
 win.close();g.build_shapes,g.build_for_update=saved
 doc=App.newDocument();frame=d.create_frame(p,doc);obj=d.component_objects(frame)['StackEnvelope']
 assert obj.Shape.isValid() and len(obj.ViewObject.DiffuseColor)==len(obj.Shape.Faces)
 d.update_frame(frame,replace(p,StackUSBFace='Right',StackUSBOffsetY=2.))
 assert set(g.build_report(replace(p,StackUSBFace='Right',StackUSBOffsetY=2.))['rebuilt'])<={'StackEnvelope'}
 App.closeDocument(doc.Name)
except Exception:fail.append(traceback.format_exc())
(out/'gui_checks.json').write_text(json.dumps({'failures':fail},indent=2));print(fail,flush=True);os._exit(1 if fail else 0)
