"""Run with the FreeCAD GUI to check material persistence and reference colors."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets,QtCore
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.document import create_frame,component_objects,ensure_components
from freecad.rotorforge.geometry import CARBON_ROLES
from freecad.rotorforge.appearance import CARBON_COLOR,PAD_COLOR
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
checks=[]
try:
 assert App.GuiUp
 d=App.newDocument('MaterialCheck');p=Parameters(FPVEnabled=True,StandoffHeight=35,LiPoPadEnabled=True,PlateDesign='3 plates')
 o=create_frame(p,d);parts=component_objects(o)
 def close_color(a,b):return max(abs(x-y) for x,y in zip(a[:3],b))<1/255+1e-5
 for role in CARBON_ROLES:
  v=parts[role].ViewObject;assert close_color(v.ShapeColor,CARBON_COLOR),(role,v.ShapeColor)
  assert v.Transparency==0
 v=parts['LiPoPad'].ViewObject;assert close_color(v.ShapeColor,PAD_COLOR);assert v.Transparency==0
 checks.append('All carbon parts including camera sides and locks share opaque graphite; pad is matte near-black')
 refs=('StackEnvelope','BatteryEnvelope','VTXEnvelope','MotorEnvelopes','PropellerDiscs')
 original={r:(tuple(parts[r].ViewObject.ShapeColor),parts[r].ViewObject.Transparency) for r in refs}
 assert close_color(original['StackEnvelope'][0],(.20,.68,.36))
 assert close_color(original['BatteryEnvelope'][0],(.91,.45,.12))
 assert close_color(original['VTXEnvelope'][0],(.58,.27,.68))
 checks.append('New stack, LiPo and VTX reference colors retain their prior defaults')
 for r in refs:parts[r].ViewObject.ShapeColor=(.12,.34,.56)
 parts['CameraMountLeft'].ViewObject.ShapeColor=(.1,.8,.9)
 ensure_components(o)
 assert close_color(parts['CameraMountLeft'].ViewObject.ShapeColor,CARBON_COLOR)
 for r in refs:assert close_color(parts[r].ViewObject.ShapeColor,(.12,.34,.56))
 checks.append('Updating recolors existing carbon/pad parts and preserves customized electronics references')
 d.recompute();d.saveAs(str(out/'MaterialCheck.FCStd'));name=d.Name;App.closeDocument(name)
 d=App.openDocument(str(out/'MaterialCheck.FCStd'));parts=component_objects(d.getObject('FrameParameters'))
 print('RESTORED',parts['CameraMountLeft'].ViewObject.ShapeColor,parts['LiPoPad'].ViewObject.ShapeColor,flush=True)
 assert close_color(parts['CameraMountLeft'].ViewObject.ShapeColor,CARBON_COLOR)
 assert close_color(parts['LiPoPad'].ViewObject.ShapeColor,PAD_COLOR)
 assert close_color(parts['VTXEnvelope'].ViewObject.ShapeColor,(.12,.34,.56))
 assert abs(parts['TopPlate'].ViewObject.ShapeAppearance[0].Shininess-32)<.01
 assert abs(parts['LiPoPad'].ViewObject.ShapeAppearance[0].Shininess-2)<.01
 checks.append('Physical/reference colors and satin/matte shininess persist after saving and reopening')
 from freecad.rotorforge.gui import FrameDialog
 dialog=FrameDialog();dialog.set_values(p);dialog.show();QtWidgets.QApplication.processEvents();dialog.grab().save(str(out/'editor_materials.png'));dialog.close()
 report=dict(status='passed',checks=checks,material_properties={r:{'color':list(parts[r].ViewObject.ShapeColor),'shininess':parts[r].ViewObject.ShapeAppearance[0].Shininess} for r in ('TopPlate','CameraMountLeft','LiPoPad')})
 App.closeDocument(d.Name)
except Exception:report=dict(status='failed',checks=checks,error=traceback.format_exc());traceback.print_exc()
(out/'material_report.json').write_text(json.dumps(report,indent=2))
QtCore.QTimer.singleShot(100,QtWidgets.QApplication.instance().quit)
