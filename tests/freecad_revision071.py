import os
import sys,json,traceback
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge import geometry as g,document as d,hardware_refs as hw
from freecad.rotorforge.parameters import Parameters,stack_reference_z,plate_levels
from freecad.rotorforge.hardware_layout import hardware_layout
from freecad.rotorforge.nut_seats import seats
from freecad.rotorforge.exporters import export_package
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True);checks=[];fail=[]
for name,p in [('two',Parameters(PlateDesign='2 plates',StackPressNuts=True)),('three',Parameters(StackPressNuts=True,FPVEnabled=True)),('clamp',Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,StackPressNuts=True,StandoffHeight=30.)),('recessed',Parameters(StackPressNuts=True,PressNutFlangeRecess=.2))]:
 try:
  doc=App.newDocument();f=d.create_frame(p,doc);parts=d.component_objects(f);hw.refresh(f)
  assert abs(parts['StackEnvelope'].Shape.BoundBox.ZMin-stack_reference_z(p))<1e-6
  assert all(o.Shape.isValid() for o in hw.objects(f))
  for s in hardware_layout(p):
   if s['group']=='Stack hardware':assert s['nut'] and s['press'] and abs(s['point'][2]+s['nut_distance']-stack_reference_z(p)-p.StackHeight)<1e-6
   if s['group']=='VTX hardware':assert not s['nut'] and not s.get('press')
  if name=='three':
   folder=export_package(f,out/'Export');data=json.loads((folder/'ExportInfo.json').read_text());assert data['stack']['press_nuts']
  if name=='clamp':
   fpath=out/'StackPressNuts.FCStd';doc.saveAs(str(fpath));App.closeDocument(doc.Name);doc=App.openDocument(str(fpath));f=doc.getObject('FrameParameters');assert d.read_parameters(f).StackPressNuts
  App.closeDocument(doc.Name);checks.append(name)
 except Exception:fail.append(dict(case=name,error=traceback.format_exc()));traceback.print_exc()
(out/'native071.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print('DONE',checks,fail,flush=True)
