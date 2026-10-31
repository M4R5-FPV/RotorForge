"""Native end profiles, offset tabs, export and unaffected-component reuse."""
import os,sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.bottom_nose import NOSE_SHAPES,REAR_SHAPES
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.fpv import camera_mounts,camera_slots
from freecad.rotorforge.exporters import export_package
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
checks=[];fail=[]
try:
 for end,names in (('Front',NOSE_SHAPES),('Rear',REAR_SHAPES)):
  for name in names:
   for role in (('BottomPlate',) if end=='Front' else ('BottomPlate','MidPlate','TopPlate')):
    mode='2 plates' if role=='BottomPlate' else '3 plates'
    prefix='BottomNose' if end=='Front' else {'BottomPlate':'BottomRear','MidPlate':'MidRear','TopPlate':'TopRear'}[role]
    p=Parameters(PlateDesign=mode,**{prefix+'Shape':name})
    s=g.profiled_plate(p,role,50,-80,80,5,0,3)
    assert s.isValid() and len(s.Solids)==1,(end,role,name)
    assert s.BoundBox.YMin>=-80-1e-7 and s.BoundBox.YMax<=80+1e-7
    assert s.Volume<=50*160*3+1e-7
    checks.append(end+' '+role+' '+name)
 for mode in ('2 plates','3 plates'):
  p=Parameters(PlateDesign=mode,FPVEnabled=True,StandoffHeight=35.,BottomReachMode='Custom',BottomFrontReach=100.,BottomRearReach=110.,MidReachMode='Custom',MidRearReach=110.,TopReachMode='Custom',TopFrontReach=90.,TopRearReach=110.,BottomNoseShape='Round U recess',BottomRearShape='Dual cable channels',BottomRearDepth=2.,MidRearShape='Cable channel',MidRearDepth=2.,TopRearShape='Split tail',TopRearDepth=2.,CameraTabBottomRearOffset=.5,CameraTabBottomFrontOffset=-.75,CameraTabTopRearOffset=.25,CameraTabTopFrontOffset=-.5)
  assert not validate(p)[0],validate(p)[0]
  doc=App.newDocument();f=d.create_frame(p,doc);parts=d.component_objects(f)
  for role,obj in parts.items():
   if not obj.Shape.isNull():assert obj.Shape.isValid(),role
  for m in camera_mounts(p):
   bracket=parts[m['role']].Shape
   for ys,z,h in ((m['tabs_y'],0,p.BottomThickness),(m['top_tabs_y'],m['z1'],p.TopThickness)):
    for y in ys:
     tab=Part.makeBox(m['plate_x'][1]-m['plate_x'][0],p.CameraTabLength,h,App.Vector(m['plate_x'][0],y-p.CameraTabLength/2,z))
     assert tab.cut(bracket).Volume<1e-7,(mode,m['role'],y,z,tab.cut(bracket).Volume,bracket.BoundBox)
   assert bracket.common(parts['BottomPlate'].Shape).Volume<1e-7
   assert bracket.common(parts['TopPlate'].Shape).Volume<1e-7
  export_package(f,out/mode.replace(' ','_'))
  doc.saveAs(str(out/('Edges_'+mode[0]+'.FCStd')));App.closeDocument(doc.Name)
  checks.append(mode+' complete frame, matching camera sockets, STEP/DXF/SVG export')
 base=Parameters(FPVEnabled=True,StandoffHeight=35.)
 g.build_for_update(base);q=replace(base,CameraTabBottomRearOffset=.5);g.build_for_update(q);r=g.build_report(q)
 assert not any(role.startswith('Arm') for role in r['rebuilt']),r
 checks.append('Tab edit retains all arm BReps: '+repr(r['rebuilt']))
 q=replace(q,TopRearShape='Cable channel',TopRearDepth=2.);g.build_for_update(q);r=g.build_report(q)
 assert not any(role.startswith('Arm') for role in r['rebuilt']),r
 checks.append('Rear edit retains all arm BReps: '+repr(r['rebuilt']))
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'edges.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print('CHECKS',len(checks),'FAIL',fail,flush=True)
