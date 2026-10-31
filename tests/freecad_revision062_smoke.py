"""Full-height foremost sleeves, circular inboard shoulders and fit clearance."""
import sys,os,json,traceback,itertools,time
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters,standoff_layouts
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.protection_layout import guard_layout,usb_window
root=Path(__file__).resolve().parents[1];out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];failures=[]
p=Parameters(FlexSideGuards=True,FlexGuardExtendFront=True,StandoffCount='6 (3 pairs)',StandoffPair3Y=-94,StandoffPair3Width=28,MidReachMode='Custom',MidRearReach=102,TopReachMode='Custom',TopRearReach=102)
def run(q):
 shapes=build_shapes(q);r=(q.StandoffDiameter+q.FlexGuardFit)/2+q.FlexGuardWall;inner=(q.StandoffDiameter+q.FlexGuardFit)/2
 for g in guard_layout(q):
  s=shapes[g['role']];assert s.isValid() and len(s.Solids)==1,g['role'];sign=g['sign']
  first=g['stands'][0];low,high=g['bands'][0];assert abs(low-first['base']-.15)<1e-6;assert abs(first['base']+first['length']-high-.15)<1e-6
  if q.FlexGuardExtendFront:assert first['point'][1]==max(st['point'][1] for st in standoff_layouts(q))
  for st,band in zip(g['stands'],g['bands']):
   sx,sy=st['point'];lo,hi=band
   for z in (lo+.05,(lo+hi)/2,hi-.05):
    assert s.isInside(App.Vector(sx-sign*(inner+q.FlexGuardWall*.5),sy,z),1e-5,True),'Missing inboard grip along bearing height'
    assert not s.isInside(App.Vector(sx,sy,z),1e-5,True),'Post bore obstructed'
    for dy in (-.8*r,.8*r):assert not s.isInside(App.Vector(sx-sign*.8*r,sy+dy,z),1e-5,True),'Inboard shoulder still has square corners'
  for role in ('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight','BottomPlate','MidPlate','TopPlate','Standoffs'):
   if not shapes[role].isNull():assert s.common(shapes[role]).Volume<1e-5,'Grip intersects '+role
  window=usb_window(q,g)
  if window:
   y,z,w,h=window;probe=Part.makeBox(1000,w*.5,h*.5,App.Vector(-500,y-w*.25,z-h*.25));assert s.common(probe).Volume<1e-6,'USB blocked'
for design,extend,style,height in itertools.product(('2 plates','3 plates'),(False,True),('Solid','Vented'),(22.,30.)):
 q=replace(p,PlateDesign=design,FlexGuardExtendFront=extend,FlexGuardStyle=style,StandoffHeight=height,BottomReachMode='Custom',BottomFrontReach=82.,BottomRearReach=102.,FlexGuardUSBEnabled=extend)
 name=f'{design}/{extend}/{style}/{height}'
 try:run(q);checks.append(name);print('PASS',name,flush=True)
 except Exception:failures.append(dict(name=name,error=traceback.format_exc()));traceback.print_exc()
for name,q in [('Eight posts / foremost extra pair',replace(p,StandoffCount='8 (4 pairs)',StandoffPair4Y=60.,StandoffPair4Width=34.,FlexGuardUSBEnabled=True)),('Default four-post frame',Parameters(FlexSideGuards=True)),('Above-bottom arms',replace(p,PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate',StackMountHeight=6.,BottomReachMode='Custom',BottomFrontReach=82.,BottomRearReach=102.,StandoffHeight=30.)),('Front and rear insets',replace(p,FlexGuardFrontInset=3.,FlexGuardRearInset=3.))]:
 try:run(q);checks.append(name);print('PASS',name,flush=True)
 except Exception:failures.append(dict(name=name,error=traceback.format_exc()));traceback.print_exc()
(out/'revision062.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
