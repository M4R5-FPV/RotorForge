"""Native CAD, motor hole support, exact DXF/SVG coordinates and persistence."""
import sys,os,json,math,traceback,xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,arm_layouts,plate_levels,motor_hole_offsets
from freecad.rotorforge.geometry import build_shapes,cylinder,motor_pad
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
 for i,(pattern,angle,layout) in enumerate([('4-hole bolt circle',45.,'True X'),('3-hole bolt circle',-30.,'Deadcat'),('4-hole bolt circle',22.5,'Stretched X'),('4-hole bolt circle',-45.,'True X')]):
  p=Parameters(MotorHoleLayout=pattern,MotorHoleRotation=angle,MotorBoltCircle=20,Layout=layout)
  shapes=build_shapes(p);arms=arm_layouts(p);z=plate_levels(p)['arm_z']
  for arm in arms:
   role='Arm'+arm['name'];shape=shapes[role]
   check(shape.isValid() and len(shape.Solids)==1,f'{i}: {role} connected')
   for pt in arm['motor_holes']:
    check(shape.common(cylinder(*pt,p.MotorHoleDiameter/2-.01,z,p.ArmThickness)).Volume<1e-6,f'{i}: {role} motor bore open')
    ring=cylinder(*pt,p.MotorHoleDiameter/2+p.MinimumWeb,z,p.ArmThickness).cut(cylinder(*pt,p.MotorHoleDiameter/2,z-.1,p.ArmThickness+.2))
    check(abs(shape.common(ring).Volume-ring.Volume)<1e-5,f'{i}: {role} motor bore supported')
   a=motor_pad(p,arm,z);b=motor_pad(replace(p,MotorHoleRotation=0),arm,z)
   check(a.cut(b).Volume+b.cut(a).Volume<1e-6,f'{i}: {role} pad outline unchanged')
  settings=create_frame(p,App.newDocument('Rotation'+str(i)));folder=export_package(settings,out)
  info=json.loads((folder/'ExportInfo.json').read_text());check(info['motor_pad']['hole_rotation_deg']==angle,f'{i}: export rotation metadata')
  check(info['motor_pad']['hole_offsets_mm']==[list(pt) for pt in motor_hole_offsets(p)],f'{i}: export exact offsets')
  for arm in arms:
   role='Arm'+arm['name'];item=next(item for sheet in info['cutting_layout']['sheets'] for item in sheet['parts'] if item['role']==role)
   a=math.radians(item['rotation_deg']);shape=shapes[role].copy();shape.rotate(App.Vector(),App.Vector(0,0,1),item['rotation_deg']);bb=shape.BoundBox
   expected=[(math.cos(a)*x-math.sin(a)*y-bb.XMin,math.sin(a)*x+math.cos(a)*y-bb.YMin) for x,y in arm['motor_holes']]
   dxfs=dxf_circles(folder/'CuttingProfiles'/(role+'.dxf'))
   svg=ET.parse(folder/'CuttingProfiles'/(role+'.svg'));svgs=[(float(e.attrib['cx']),float(e.attrib['cy']),float(e.attrib['r'])) for e in svg.iter() if e.tag.endswith('circle')]
   for label,actual in [('DXF',dxfs),('SVG',svgs)]:
    for x,y in expected:check(any(math.hypot(x-cx,y-cy)<1e-6 and abs(radius-p.MotorHoleDiameter/2)<1e-6 for cx,cy,radius in actual),f'{i}: {role} {label} rotated hole')
  path=out/f'rotation-{i}.FCStd';settings.Document.saveAs(str(path.resolve()));App.closeDocument(settings.Document.Name);doc=App.openDocument(str(path.resolve()));settings=next(o for o in doc.Objects if 'MotorHoleRotation' in o.PropertiesList)
  check(settings.getTypeIdOfProperty('MotorHoleRotation')=='App::PropertyAngle',f'{i}: angle property type')
  check(read_parameters(settings)==p,f'{i}: saved native angle preserved');App.closeDocument(doc.Name)
 report={'status':'passed','checks':checks}
except Exception:report={'status':'failed','checks':checks,'error':traceback.format_exc()};print(report['error'],flush=True)
(out/'report.json').write_text(json.dumps(report,indent=2))
