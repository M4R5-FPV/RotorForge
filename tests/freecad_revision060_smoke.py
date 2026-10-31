"""Native guard reach/vents/USB, linked service openings and unchanged arm roots."""
import os,sys,json,traceback,itertools
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters,arm_layouts,plate_levels,validate
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.protection_layout import guard_layout,guard_vents,usb_window,motor_service_slots
from freecad.rotorforge.motor_pads import MOTOR_PAD_SHAPES
from freecad.rotorforge.arm_roots import fillet_root_limit,arm_local_point
from freecad.rotorforge.flex_options import FLEX_ROLES
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True);checks=[];failures=[]
p=Parameters(StandoffCount='6 (3 pairs)',StandoffPair3Y=-94,StandoffPair3Width=28,MidReachMode='Custom',MidRearReach=102,TopReachMode='Custom',TopRearReach=102)
def case(name,fn):
 try:fn();checks.append(name);print('PASS',name,flush=True)
 except Exception:failures.append(dict(name=name,error=traceback.format_exc()));traceback.print_exc()
def guards(q):
 assert not validate(q)[0],validate(q)[0]
 shapes=build_shapes(q)
 for g in guard_layout(q):
  s=shapes[g['role']];assert s.isValid() and len(s.Solids)==1
  for st,band in zip(g['stands'],g['bands']):
   x,y=st['point'];r=(q.StandoffDiameter+q.FlexGuardFit)/2
   for z in (band[0]+.1,band[1]-.1):assert s.isInside(App.Vector(x,y+r+q.FlexGuardWall*.5,z),1e-5,True),'Bearing band lost'
  for v in guard_vents(q,g):
   # Centre of each actual opening remains clear all the way through the wall.
   tool=Part.makeCylinder(.03,1000,App.Vector(-500,v['y'],v['z']),App.Vector(1,0,0));assert s.common(tool).Volume<1e-6,'Vent blocked'
  window=usb_window(q,g)
  if window:
   y,z,w,h=window;tool=Part.makeBox(1000,w*.6,h*.6,App.Vector(-500,y-w*.3,z-h*.3));assert s.common(tool).Volume<1e-5,'USB connector path blocked'
mode=os.environ.get('ROTORFORGE_CASES','all')
for design,extend,shape in ([] if mode!='all' else itertools.product(('2 plates','3 plates'),(False,True),('Horizontal slots','Rounded slots','Ellipses','Hexagons','Diamonds','Chevrons'))):
 q=replace(p,PlateDesign=design,BottomReachMode='Custom',BottomFrontReach=82,BottomRearReach=102,FlexSideGuards=True,FlexGuardExtendFront=extend,FlexGuardVentShape=shape,FlexGuardUSBEnabled=extend)
 case(f'Guards {design}/{extend}/{shape}',lambda q=q:guards(q))
for side,offset in ([] if mode!='all' else itertools.product(('Left','Right','Both'),(-10.,10.))):
 q=replace(p,FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardUSBEnabled=True,FlexGuardUSBSide=side,FlexGuardUSBY=offset)
 case('USB '+side+'/'+str(offset),lambda q=q:guards(q))
for shape in (() if mode!='all' else MOTOR_PAD_SHAPES):
 def motor(shape=shape):
  q=replace(p,FlexMotorProtectors=True,FlexProtectorRetention='Linked screw access',MotorPadShape=shape,MotorPadDiameter=40.,MotorPadRotation=20.)
  s=build_shapes(q);z=plate_levels(q)['arm_z']-q.FlexProtectorFloor/2
  for arm in arm_layouts(q):
   cup=s['MotorProtector'+arm['name']];assert cup.isValid() and len(cup.Solids)==1
   for a,b,r in motor_service_slots(q,arm):
    for t in (.15,.4,.65,.9):assert not cup.isInside(App.Vector(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),z),1e-5,True),'Service slot has a bridge'
 case('Linked motor cup '+shape,motor)
for fit,radius in itertools.product(('Independent',) if mode=='independent' else ('Independent','Fitted miters'),(1.,3.,5.)):
 def root(fit=fit,radius=radius):
  q=replace(p,StandoffLength=120.,RootExtension=5. if fit=='Independent' else 8.,ArmRootFit=fit,ArmBeamShape='Stepped beam',ArmRootWidth=20. if fit=='Independent' else 22.,ArmEdgeFillet=radius,ArmFilletOpenings=True)
  source=build_shapes(replace(q,ArmEdgeFillet=0.));finished=build_shapes(q)
  changed=0
  for arm in arm_layouts(q):
   role='Arm'+arm['name'];a=source[role];b=finished[role];assert b.isValid() and len(b.Solids)==1
   v=[App.Vector(*arm_local_point(arm,t,x),-30) for t,x in ((-1000,-1000),(fillet_root_limit(q,arm),-1000),(fillet_root_limit(q,arm),1000),(-1000,1000))];zone=Part.Face(Part.makePolygon(v+[v[0]])).extrude(App.Vector(0,0,100))
   assert a.cut(b).common(zone).Volume+b.cut(a).common(zone).Volume<1e-6,'Root mounting outline changed'
   changed+=a.cut(b).Volume+b.cut(a).Volume
  assert changed>1e-5,'Outboard fillets were not applied'
 case(f'Unchanged root {fit}/{radius}',root)
(out/('revision060_'+mode+'.json' if mode!='all' else 'revision060.json')).write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
