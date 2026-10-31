"""Native upper-attachment offset, matching sockets and unchanged camera pose."""
import os,sys,json,traceback
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.fpv import camera_mounts,camera_body_centre,camera_slots
from freecad.rotorforge.document import create_frame,read_parameters
from freecad.rotorforge.exporters import export_package
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[]
def check(ok,msg):
 if not ok:raise AssertionError(msg)
 checks.append(msg)
try:
 for follow in (True,False):
  for mode in ('Fixed','Variable'):
   p=Parameters(FPVEnabled=True,CameraFollowPlates=follow,CameraMountMode=mode);q=replace(p,CameraTopRearOffset=5)
   s,t=build_shapes(p),build_shapes(q);old,new=camera_mounts(p)[0],camera_mounts(q)[0];tag=str((follow,mode))
   check(camera_body_centre(p)==camera_body_centre(q),tag+' camera pose unchanged')
   check(old['wall_profile'][:2]==new['wall_profile'][:2],tag+' lower contact unchanged')
   check(new['top_tabs_y']==tuple(y-5 for y in old['top_tabs_y']),tag+' upper tabs shift exact distance')
   check(camera_slots(p)==camera_slots(q),tag+' bottom sockets unchanged')
   check(t['BottomPlate'].cut(s['BottomPlate']).Volume<1e-6 and s['BottomPlate'].cut(t['BottomPlate']).Volume<1e-6,tag+' bottom geometry unchanged')
   check(s['TopPlate'].cut(t['TopPlate']).Volume>1 and t['TopPlate'].cut(s['TopPlate']).Volume>1,tag+' top sockets move')
   for role in ('CameraMountLeft','CameraMountRight'):
    check(t[role].isValid() and len(t[role].Solids)==1,tag+' connected '+role)
    check(s[role].cut(t[role]).Volume>1 and t[role].cut(s[role]).Volume>1,tag+' side wall slopes '+role)
 check(validate(Parameters(FPVEnabled=True,CameraTopRearOffset=1000))[0],'unsupported offset rejected')
 settings=create_frame(q,App.newDocument('RearUpperMount'));filename=out/'upper.FCStd';settings.Document.saveAs(str(filename.resolve()));App.closeDocument(settings.Document.Name)
 doc=App.openDocument(str(filename.resolve()));settings=next(o for o in doc.Objects if 'Wheelbase' in o.PropertiesList);check(read_parameters(settings)==q,'native save/reopen')
 folder=export_package(settings,out);info=json.loads((folder/'ExportInfo.json').read_text());check(info['fpv']['camera_top_rearward_offset_mm']==5,'offset export metadata');check((folder/'CameraPlates/CameraMountLeft.stl').is_file(),'sloping camera STL export');App.closeDocument(doc.Name)
 report={'status':'passed','checks':checks}
except Exception:report={'status':'failed','checks':checks,'error':traceback.format_exc()}
(out/'report.json').write_text(json.dumps(report,indent=2))
