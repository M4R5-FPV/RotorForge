"""Alternating arm orientation and clearance for symmetric and asymmetric frames."""
from pathlib import Path
import sys,os,json,math,traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,arm_layouts
from freecad.rotorforge.geometry import build_shapes,carbon_roles,flat_plate_shape
from freecad.rotorforge.exporters import cutting_profiles
from freecad.rotorforge.cutting_layout import ARM_ROLES
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[]}
def check(ok,label):
 if not ok:raise AssertionError(label)
 report['checks'].append(label)
try:
 for i,p in enumerate([Parameters(),Parameters(Layout='Stretched X'),Parameters(Layout='Deadcat',ArmRootWidth=32,ArmRootFit='Fitted miters',MotorPadShape='Swept shield',StandoffFrontMount='Arm outer hole',StandoffRearMount='Arm outer hole',ArmRootReliefsEnabled=True,TopWidth=60)]):
  shapes=build_shapes(p);folder=out/str(i);plan,faces=cutting_profiles(shapes,folder,carbon_roles(p),p)
  sheet=next(s for s in plan['sheets'] if any(a['role'] in ARM_ROLES for a in s['parts']))
  items=sheet['parts'][:4];check([a['role'] for a in items]==list(ARM_ROLES),'Four arms kept together in stable order')
  arms={'Arm'+a['name']:a for a in arm_layouts(p)}
  for j,item in enumerate(items):
   role=item['role'];r=App.Rotation(App.Vector(0,0,1),item['rotation_deg']);a=arms[role]
   root=r.multVec(App.Vector(*a['root'],0));motor=r.multVec(App.Vector(*a['motor'],0))
   check(abs(root.x-motor.x)<1e-7 and (motor.y-root.y)*(1 if j%2==0 else -1)>0,role+': correct alternating motor end')
   expected=flat_plate_shape(shapes[role],role,p).copy();expected.rotate(App.Vector(),App.Vector(0,0,1),item['rotation_deg']);b=expected.BoundBox
   f=max((f for f in expected.Faces if abs(f.normalAt(0,0).z)>.999999),key=lambda f:f.CenterOfMass.z).copy();f.translate(App.Vector(-b.XMin,-b.YMin,-f.CenterOfMass.z))
   actual=faces[role];check(abs(actual.common(f).Area-f.Area)<1e-5,role+': exact rotated outline and holes, no mirror')
   check(abs(b.XLength-item['width'])<1e-7 and abs(b.YLength-item['height'])<1e-7,role+': true rotated bounds')
   if j:
    previous=items[j-1];check(abs(item['y']-previous['y'])<1e-7 and abs(item['x']-previous['x']-previous['width']-4)<1e-7,'Side by side with 4 mm clearance')
  oldarea=sum(flat_plate_shape(shapes[r],r,p).BoundBox.XLength*flat_plate_shape(shapes[r],r,p).BoundBox.YLength for r in ARM_ROLES)
  rowarea=(items[-1]['x']+items[-1]['width']-items[0]['x'])*max(a['height'] for a in items)
  check(rowarea<oldarea,'Arm stock footprint reduced from original diagonal bounding boxes')
 report['status']='passed'
except Exception:report.update(status='failed',error=traceback.format_exc());print(report['error'],flush=True)
finally:(out/'test_report.json').write_text(json.dumps(report,indent=2));print('ARM LAYOUT',report['status'],len(report['checks']),flush=True)
