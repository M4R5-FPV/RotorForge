"""New motor pads: solid connectivity, exact hole support, exports and old profiles."""
from pathlib import Path
from dataclasses import replace
import sys,os,json,traceback,importlib.util,math
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,arm_layouts,plate_levels
from freecad.rotorforge.motor_pads import MOTOR_PAD_SHAPES,motor_pad_primitives
from freecad.rotorforge.geometry import build_shapes,motor_pad,cylinder,carbon_roles,flat_plate_shape
from freecad.rotorforge.document import create_frame,read_parameters
from freecad.rotorforge.exporters import export_package,profile_entities
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[]}
def check(ok,label):
 if not ok:raise AssertionError(label)
 report['checks'].append(label)
try:
 for shape in MOTOR_PAD_SHAPES[21:]:
  for layout,design,size,sx,sy in [('True X','3 plates',30,16,16),('Deadcat','2 plates',30,16,16),('Stretched X','3 plates',36,19,16)]:
   p=Parameters(MotorPadShape=shape,Layout=layout,PlateDesign=design,MotorPadDiameter=size,MotorSpacingX=sx,MotorSpacingY=sy,RearArmExtension=20 if layout=='Deadcat' else 0)
   shapes=build_shapes(p);z=plate_levels(p)['arm_z']
   for arm in arm_layouts(p):
    role='Arm'+arm['name'];s=shapes[role]
    check(s.isValid() and len(s.Solids)==1,shape+'/'+layout+': connected '+role)
    for pt in arm['motor_holes']:
     tool=cylinder(*pt,p.MotorHoleDiameter/2-.01,z,p.ArmThickness)
     check(s.common(tool).Volume<1e-6,shape+': motor bore open')
     ring=cylinder(*pt,p.MotorHoleDiameter/2+p.MinimumWeb,z,p.ArmThickness).cut(cylinder(*pt,p.MotorHoleDiameter/2,z-.1,p.ArmThickness+.2))
     check(abs(s.common(ring).Volume-ring.Volume)<1e-5,shape+': full motor-bolt support')
  settings=create_frame(Parameters(MotorPadShape=shape));folder=export_package(settings,out)
  check(json.loads((folder/'ExportInfo.json').read_text())['motor_pad']['shape']==shape,shape+': metadata')
  root=next(o for o in settings.Document.Objects if 'RotorForgeCuttingLayout' in o.PropertiesList)
  for g in root.Group:
   for obj in g.Group:
    if obj.SourceRole.startswith('Arm') and obj.SourceRole in ['Arm'+a['name'] for a in arm_layouts(Parameters())]:
     check(obj.Shape.isValid() and len(obj.Shape.Faces)==1,shape+': native cutting face')
     for ext in ('dxf','svg'):check((folder/'CuttingProfiles'/(obj.SourceRole+'.'+ext)).stat().st_size>100,shape+': '+ext)
  path=out/(shape.replace(' ','_')+'.FCStd');settings.Document.saveAs(str(path));App.closeDocument(settings.Document.Name);doc=App.openDocument(str(path))
  check(any('MotorPadShape' in o.PropertiesList and str(o.MotorPadShape)==shape for o in doc.Objects),shape+': reopen selected pad');App.closeDocument(doc.Name)
  print('PAD VERIFIED',shape,flush=True)
 # All existing primitive definitions and resulting solids must remain identical.
 source=Path(os.environ['ROTORFORGE_PREVIOUS_SOURCE']);spec=importlib.util.spec_from_file_location('rotorforge_before_pads',source/'__init__.py',submodule_search_locations=[str(source)])
 pkg=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pkg;spec.loader.exec_module(pkg)
 from rotorforge_before_pads.parameters import Parameters as OldParameters,arm_layouts as old_arms
 from rotorforge_before_pads.motor_pads import motor_pad_primitives as old_primitives,MOTOR_PAD_SHAPES as old_choices
 from rotorforge_before_pads.geometry import motor_pad as old_pad
 check(tuple(MOTOR_PAD_SHAPES[:21])==old_choices,'All twenty-one existing choices retained in original order')
 for name in old_choices:
  p=Parameters(MotorPadShape=name);old=OldParameters(MotorPadShape=name)
  check(motor_pad_primitives(p)==old_primitives(old),name+': unchanged primitives')
  a=motor_pad(p,arm_layouts(p)[0],0);b=old_pad(old,old_arms(old)[0],0)
  check(a.cut(b).Volume+b.cut(a).Volume<1e-6,name+': unchanged CAD solid')
 # Additional choices must produce distinct physical outlines.
 for name in MOTOR_PAD_SHAPES[21:]:
  p=Parameters(MotorPadShape=name);a=motor_pad(p,arm_layouts(p)[0],0)
  for other in MOTOR_PAD_SHAPES:
   if other==name:continue
   q=Parameters(MotorPadShape=other);b=motor_pad(q,arm_layouts(q)[0],0)
   check(a.cut(b).Volume+b.cut(a).Volume>1e-5,name+': distinct from '+other)
 report['status']='passed'
except Exception:report.update(status='failed',error=traceback.format_exc());print(report['error'],flush=True)
finally:(out/'test_report.json').write_text(json.dumps(report,indent=2));print('PAD CATALOGUE',report['status'],len(report['checks']),flush=True)
