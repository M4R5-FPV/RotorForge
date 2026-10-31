"""One source of top-front geometry; retired-property migration and editor cleanup."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge.exporters import export_package
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];fail=[]
try:
 p=Parameters(FPVEnabled=True)
 shapes=g.build_shapes(p);front=g.top_bounds(p)[1];top=g.plate_levels(p)['top_z']
 import Part
 probe=Part.makeBox(1.,1.,p.TopThickness,App.Vector(-.5,front-4.,top))
 assert probe.cut(shapes['TopPlate']).Volume<1e-7
 checks.append('Fresh FPV straight front builds with no hidden centre opening')
 p=Parameters(FPVEnabled=True,TopFrontShape='Camera U recess',TopFrontDepth=28.,TopFrontRecessWidth=14.,TopFrontSetback=0.)
 doc=App.newDocument();frame=d.create_frame(p,doc)
 for key,value in (('CameraCutoutWidth',14.),('CameraCutoutDepth',28.),('CameraCutoutClearance',.5)):
  frame.addProperty('App::PropertyLength',key);setattr(frame,key,value)
 frame.TopFrontShape='Straight'
 migrated=d.read_parameters(frame);assert migrated.TopFrontShape=='Camera U recess' and migrated.TopFrontDepth==28.
 d.update_frame(frame,migrated)
 assert all(key not in frame.PropertiesList for key in ('CameraCutoutWidth','CameraCutoutDepth','CameraCutoutClearance'))
 assert frame.TopFrontShape=='Camera U recess'
 folder=export_package(frame,out/'export');metadata=json.loads((folder/'ExportInfo.json').read_text())
 assert 'top_camera_cutout' not in json.dumps(metadata) and 'top_front_profile' in json.dumps(metadata)
 doc.saveAs(str(out/'Migrated.FCStd'));App.closeDocument(doc.Name)
 checks.append('Legacy properties migrate to the visible U profile and are removed on update; export metadata uses the top profile')
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([]);Gui.getMainWindow=lambda:None
 win=FrameDialog();win.set_values(migrated);win.refresh()
 assert all(k not in win.controls for k in ('CameraCutoutWidth','CameraCutoutDepth','CameraCutoutClearance'))
 assert 'TopFrontClearance' in win.controls and win.values()==migrated
 win.close();checks.append('FPV controls/search are removed; top camera clearance round-trips')
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'single_recess.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));os._exit(1 if fail else 0)
