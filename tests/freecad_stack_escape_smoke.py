"""Run with FreeCADCmd: open inward slots, exact exports and bolt-support guards."""
from pathlib import Path
from dataclasses import replace
import sys,os,json,traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,arm_layouts,stack_holes,plate_levels
from freecad.rotorforge.geometry import build_shapes,carbon_roles,arm_stem,motor_pad,fuse,trim_arm_root,cylinder,capsule
from freecad.rotorforge.stack_reliefs import stack_escape_segment
from freecad.rotorforge.document import create_frame,read_parameters
from freecad.rotorforge.exporters import export_package,profile_entities
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[]}
def check(v,name):
 if not v:raise AssertionError(name)
 report['checks'].append(name)
base=Parameters(ArmRootWidth=32,RootExtension=25,ArmRootFit='Fitted miters',StandoffFrontMount='Arm outer hole',StandoffRearMount='Arm outer hole',TopWidth=60)
try:
 for p in [base,replace(base,StackOffsetY=3),replace(base,PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate',ArmBracesEnabled=True),replace(base,PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True),replace(base,Layout='Deadcat',RearArmExtension=25)]:
  round_shapes=build_shapes(p);slot_p=replace(p,ArmRootReliefShape='Slot toward stack centre');shapes=build_shapes(slot_p)
  arms=arm_layouts(p);z=plate_levels(p)['arm_z'];opened=0
  for arm in arms:
   role='Arm'+arm['name'];s=shapes[role];old=round_shapes[role]
   check(s.isValid() and len(s.Solids)==1,role+': one valid solid')
   check(s.Volume<=old.Volume+1e-6,role+': slot only removes material')
   raw=trim_arm_root(p,arm,arms,fuse([arm_stem(p,arm,z,p.ArmThickness),motor_pad(p,arm,z)]),z,p.ArmThickness)
   b=raw.BoundBox
   for pt in stack_holes(p):
    if raw.common(cylinder(*pt,p.StackAccessDiameter/2,z-1,p.ArmThickness+2)).Volume<1e-8:continue
    a,end,r=stack_escape_segment(p,pt,(b.XMin,b.YMin,b.XMax,b.YMax))
    check(s.common(capsule(a,end,r-.01,z,p.ArmThickness)).Volume<1e-6,role+': full-width escape path stays open')
   if old.Volume-s.Volume>1e-5:
    opened+=1
    face=lambda shape:max((f for f in shape.Faces if abs(f.normalAt(0,0).z)>.999999),key=lambda f:f.CenterOfMass.z)
    check(len(face(s).Wires)<=len(face(old).Wires),role+': slot stays connected to the outer contour')
  check(opened>0,'Fixture contains real opened reliefs')
  for role in carbon_roles(p):
   if role.startswith('Arm') and role in ['Arm'+a['name'] for a in arms]:continue
   check(abs(shapes[role].Volume-round_shapes[role].Volume)<1e-6,role+': unchanged')
 # Export exact native and DXF profiles for the slotted three-plate fixture.
 p=replace(base,ArmRootReliefShape='Slot toward stack centre');settings=create_frame(p);folder=export_package(settings,out)
 check(read_parameters(settings).ArmRootReliefShape==p.ArmRootReliefShape,'Setting stored on native frame')
 info=json.loads((folder/'ExportInfo.json').read_text());check(info['arm_mounting']['arm_root_stack_relief_shape']==p.ArmRootReliefShape,'Export metadata records slot mode')
 root=next(o for o in settings.Document.Objects if 'RotorForgeCuttingLayout' in o.PropertiesList)
 for group in root.Group:
  raw=Path(group.DXFFile).read_text().splitlines();pairs=list(zip(raw[::2],raw[1::2]));entries=[];current={}
  for code,val in pairs:
   if code=='0':
    if current.get('0') in ('LINE','ARC','CIRCLE','ELLIPSE'):entries.append(current)
    current={'0':val}
   else:current[code]=val
  for obj in group.Group:
   if obj.SourceRole not in ['Arm'+a['name'] for a in arm_layouts(p)]:continue
   s=obj.Shape;native=profile_entities(s);records=[r for r in entries if r.get('8')==obj.SourceRole]
   codes={'LINE':('10','20','11','21'),'CIRCLE':('10','20','40'),'ARC':('10','20','40','50','51'),'ELLIPSE':('10','20','11','21','40','41','42')}
   parsed=[(r['0'],*[float(r[k]) for k in codes[r['0']]]) for r in records]
   check(len(native)==len(parsed) and all(a[0]==b[0] and all((min(abs(x-y)%360,360-abs(x-y)%360)<1e-7 if a[0]=='ARC' and i>=3 else abs(x-y)<1e-7) for i,(x,y) in enumerate(zip(a[1:],b[1:]))) for a,b in zip(parsed,native)),obj.SourceRole+': native slotted profile exactly matches DXF')
   check(s.isValid() and len(s.Faces)==1,'Exported planar slot face valid')
 path=out/'SlottedStackArms.FCStd';settings.Document.saveAs(str(path));name=settings.Document.Name;App.closeDocument(name);doc=App.openDocument(str(path))
 check(any('ArmRootReliefShape' in o.PropertiesList and o.ArmRootReliefShape==p.ArmRootReliefShape for o in doc.Objects),'Slot setting survives FCStd reopen');App.closeDocument(doc.Name)
 # A round relief clears this bolt, but its inward slot would cut the bearing ring.
 bad=replace(base,RootBoltLayout='Custom coordinates',RootBolt1X=-7,RootBolt1Y=-22,RootBolt2X=5,RootBolt2Y=5)
 build_shapes(bad)
 try:build_shapes(replace(bad,ArmRootReliefShape='Slot toward stack centre'))
 except ValueError as e:check('arm-bolt supporting material' in str(e),'Slot cutting bolt support is rejected')
 else:raise AssertionError('Slot removed bolt support without rejection')
 report['status']='passed'
except Exception:report.update(status='failed',error=traceback.format_exc());print(report['error'],flush=True)
finally:(out/'test_report.json').write_text(json.dumps(report,indent=2));print('STACK ESCAPE',report['status'],len(report['checks']),flush=True)
