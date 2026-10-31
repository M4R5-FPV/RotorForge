import sys,json,traceback,os
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,plate_levels
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.protection_layout import guard_layout
checks=[];fail=[]
p=Parameters(FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardUSBEnabled=True,StandoffCount='6 (3 pairs)',StandoffPair3Y=-94,StandoffPair3Width=28,MidReachMode='Custom',MidRearReach=102,TopReachMode='Custom',TopRearReach=102)
for name,q in [('Solid, forward USB',replace(p,FlexGuardStyle='Solid')),('Above-bottom arms',replace(p,PlateDesign='2 plates',BottomReachMode='Custom',BottomFrontReach=82,BottomRearReach=102,TwoPlateArmPosition='Above bottom plate',StackMountHeight=6.,StandoffHeight=30.)),('Three-hole cup',replace(p,FlexSideGuards=False,FlexMotorProtectors=True,MotorHoleLayout='3-hole bolt circle',MotorPadRotation=-25.,MotorPadRotationPivot='Pad beginning',FlexProtectorRetention='Linked screw access',MotorPadDiameter=40.))]:
 try:
  s=build_shapes(q)
  for k,v in s.items():
   if k.startswith(('MotorProtector','ElectronicsGuard')) and not v.isNull():assert v.isValid() and len(v.Solids)==1
  checks.append(name);print('PASS',name,flush=True)
 except Exception:fail.append(dict(name=name,error=traceback.format_exc()));traceback.print_exc()
(Path(os.environ['ROTORFORGE_TEST_OUTPUT'])/'extra060.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print('DONE',len(checks),len(fail),flush=True)
