"""Native CAD, motor hole support, exact DXF/SVG coordinates and persistence."""
import sys,os,json,math,traceback,xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from freecad.rotorforge.parameters import Parameters,arm_layouts,plate_levels,motor_hole_offsets
from freecad.rotorforge.geometry import build_shapes,cylinder,motor_pad,capsule
from freecad.rotorforge.motor_pads import motor_pad_unit,motor_tip_slots
from freecad.rotorforge.document import create_frame,read_parameters
from freecad.rotorforge.exporters import export_package
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[]
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def dxf_circles(path):
 lines=path.read_text().splitlines();pairs=list(zip(lines[::2],lines[1::2]));parts=[];current=None
 for code,value in pairs:
  code=code.strip();value=value.strip()
  if code=='0':
   if current is not None:parts.append(current)
   current={} if value=='CIRCLE' else None
  elif current is not None:current[code]=value
 if current is not None:parts.append(current)
 return [(float(c['10']),float(c['20']),float(c['40'])) for c in parts]
try:
 for i,(shape_name,pad_angle,pattern,hole_angle,layout,slots) in enumerate([
  ('Arrowhead',25.,'4-hole bolt circle',0.,'True X',True),
  ('Tapered nose',-20.,'4-hole bolt circle',45.,'Stretched X',True),
  ('Vented spear',30.,'3-hole bolt circle',0.,'Deadcat',False),
  ('Rounded square',-35.,'4-hole bolt circle',0.,'Deadcat',False)]):
  p=Parameters(MotorPadShape=shape_name,MotorPadRotation=pad_angle,MotorHoleLayout=pattern,MotorHoleRotation=hole_angle,MotorBoltCircle=20,Layout=layout,MotorTipSlotEnabled=slots)
  shapes=build_shapes(p);arms=arm_layouts(p);z=plate_levels(p)['arm_z']
  for arm in arms:
   role='Arm'+arm['name'];shape=shapes[role]
   check(shape.isValid() and len(shape.Solids)==1,f'{i}: {role} connected')
   for pt in arm['motor_holes']:
    check(shape.common(cylinder(*pt,p.MotorHoleDiameter/2-.01,z,p.ArmThickness)).Volume<1e-6,f'{i}: {role} motor bore open')
    ring=cylinder(*pt,p.MotorHoleDiameter/2+p.MinimumWeb,z,p.ArmThickness).cut(cylinder(*pt,p.MotorHoleDiameter/2,z-.1,p.ArmThickness+.2))
    check(abs(shape.common(ring).Volume-ring.Volume)<1e-5,f'{i}: {role} motor bore supported')
   actual=motor_pad(p,arm,z);reference=motor_pad(replace(p,MotorPadRotation=0),arm,z)
   reference.rotate(App.Vector(*arm['motor'],0),App.Vector(0,0,1),arm['pad_rotation_deg'])
   check(actual.cut(reference).Volume+reference.cut(actual).Volume<1e-6,f'{i}: {role} complete pad rotated around motor')
   for a,b,radius in motor_tip_slots(p,arm):
    check(shape.common(capsule(a,b,radius-.01,z,p.ArmThickness)).Volume<1e-6,f'{i}: {role} rotated tip slot open')
  # Full solids must reflect left/right, including pads, holes and enabled slots.
  for left,right in [('ArmFrontLeft','ArmFrontRight'),('ArmRearLeft','ArmRearRight')]:
   mirror=App.Matrix();mirror.A11=-1
   reflected=shapes[right].transformGeometry(mirror)
   check(reflected.cut(shapes[left]).Volume+shapes[left].cut(reflected).Volume<1e-5,f'{i}: {left}/{right} mirrored CAD')
  settings=create_frame(p,App.newDocument('Rotation'+str(i)));folder=export_package(settings,out)
  info=json.loads((folder/'ExportInfo.json').read_text());check(info['motor_pad']['hole_rotation_deg']==hole_angle,f'{i}: export rotation metadata')
  check(info['motor_pad']['rotation_deg']==pad_angle,f'{i}: pad rotation metadata')
  check(info['motor_pad']['rotation_by_arm_deg']=={a['name']:a['pad_rotation_deg'] for a in arms},f'{i}: mirrored angles metadata')
  check(info['motor_pad']['hole_offsets_mm']==[list(pt) for pt in motor_hole_offsets(p)],f'{i}: export exact offsets')
  for arm in arms:
   role='Arm'+arm['name'];item=next(item for sheet in info['cutting_layout']['sheets'] for item in sheet['parts'] if item['role']==role)
   a=math.radians(item['rotation_deg']);shape=shapes[role].copy();shape.rotate(App.Vector(),App.Vector(0,0,1),item['rotation_deg']);bb=shape.BoundBox
   expected=[(math.cos(a)*x-math.sin(a)*y-bb.XMin,math.sin(a)*x+math.cos(a)*y-bb.YMin) for x,y in arm['motor_holes']]
   dxfs=dxf_circles(folder/'CuttingProfiles'/(role+'.dxf'))
   svg=ET.parse(folder/'CuttingProfiles'/(role+'.svg'));svgs=[(float(e.attrib['cx']),float(e.attrib['cy']),float(e.attrib['r'])) for e in svg.iter() if e.tag.endswith('circle')]
   for label,actual in [('DXF',dxfs),('SVG',svgs)]:
    for x,y in expected:check(any(math.hypot(x-cx,y-cy)<1e-6 and abs(radius-p.MotorHoleDiameter/2)<1e-6 for cx,cy,radius in actual),f'{i}: {role} {label} rotated hole')
  path=out/f'rotation-{i}.FCStd';settings.Document.saveAs(str(path.resolve()));App.closeDocument(settings.Document.Name);doc=App.openDocument(str(path.resolve()));settings=next(o for o in doc.Objects if 'MotorPadRotation' in o.PropertiesList)
  check(settings.getTypeIdOfProperty('MotorPadRotation')=='App::PropertyAngle',f'{i}: angle property type')
  check(read_parameters(settings)==p,f'{i}: saved native angle preserved');App.closeDocument(doc.Name)
 report={'status':'passed','checks':checks}
except Exception:report={'status':'failed','checks':checks,'error':traceback.format_exc()};print(report['error'],flush=True)
(out/'report.json').write_text(json.dumps(report,indent=2))
