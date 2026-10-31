import sys,json,traceback,itertools,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes,carbon_roles
from freecad.rotorforge.flex import flex_roles
from freecad.rotorforge.document import create_frame,read_parameters
from freecad.rotorforge.gui import FrameDialog
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets
Gui.getMainWindow=lambda:None
app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
checks=[];fail=[]
for mode,shape,offset in itertools.product(('Hard mount','Compression pads','Captured inserts'),('Rounded rectangle','Side plate outline'),(-2.,2.)):
 try:
  p=Parameters(FPVEnabled=True,CameraPlateLength=32,CameraMountMode='Variable',FlexCameraMode=mode,FlexInterfaceShape=shape,CameraForeAftOffset=offset)
  s=build_shapes(p)
  for role in carbon_roles(p)+flex_roles(p):assert s[role].isValid() and len(s[role].Solids)==1
  checks.append([mode,shape,offset])
 except Exception:fail.append(traceback.format_exc())
try:
 d=FrameDialog();d.set_values(p);d.refresh();app.processEvents();assert d.values()==p;assert d.controls['CameraForeAftOffset'].minimum()==-100
 d.close();doc=App.newDocument('CameraOffset');obj=create_frame(p,doc);assert read_parameters(obj).CameraForeAftOffset==2.;App.closeDocument(doc.Name)
 checks.append('Editor and native property roundtrip')
except Exception:fail.append(traceback.format_exc())
(Path(os.environ['ROTORFORGE_TEST_OUTPUT'])/'camera_offset_report.json').write_text(json.dumps(dict(status='failed' if fail else 'passed',checks=checks,failures=fail),indent=2));print('RESULT',len(checks),len(fail),flush=True)
