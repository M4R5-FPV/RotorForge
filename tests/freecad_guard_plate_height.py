import os,sys,json,traceback
import FreeCAD as App
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,plate_levels
from freecad.rotorforge import geometry as g
from freecad.rotorforge.dependency_cache import cached_overlap
from freecad.rotorforge.protection_layout import guard_layout
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];fail=[]
cases=[]
for mode in ('2 plates','3 plates'):
 for clearance in (0.,1.):
  cases.append((mode+str(clearance),Parameters(FlexSideGuards=True,PlateDesign=mode,FlexGuardClearance=clearance)))
 for style in ('Solid','Vented'):
  cases.append((mode+style+' forward',Parameters(FlexSideGuards=True,PlateDesign=mode,FlexGuardStyle=style,FlexGuardExtendFront=True,FlexGuardWireEnabled=True)))
 cases.append((mode+' closure',Parameters(FPVEnabled=True,StandoffHeight=35.,FlexSideGuards=True,PlateDesign=mode,FlexGuardCloseFront=True,FlexGuardClearance=0.,FlexGuardWireEnabled=True)))
cases.append(('two above clamp',Parameters(PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate',ArmBracesEnabled=True,StandoffHeight=35.,FlexSideGuards=True)))
for name,p in cases:
 try:
  shapes=g.build_shapes(p);levels=plate_levels(p)
  for side in ('Left','Right'):
   sh=shapes['ElectronicsGuard'+side];assert sh.isValid() and len(sh.Solids)==1
   assert abs(sh.BoundBox.ZMax-(levels['top_z']+p.TopThickness))<1e-6,(sh.BoundBox,levels)
   target=0. if p.PlateDesign=='2 plates' or p.FlexGuardCloseFront else levels['mid_z']
   assert sh.BoundBox.ZMin<=target+1e-6,(sh.BoundBox.ZMin,target)
   import Part
   layout=guard_layout(p)[0];y=layout['rear']+.25*(layout['front']-layout['rear'])
   # Inspect the lower-height slice across the wall; wire exits can remove
   # an individual sampling position and front grips can extend lower.
   probe=Part.makeBox(1000,1000,.05,App.Vector(-500,-500,target))
   assert sh.common(probe).Volume>1e-6,'Missing lower plate-edge coverage'
   for role,other in shapes.items():
    if role in g.CARBON_ROLES and not other.isNull():assert cached_overlap(sh,other)<1e-6,(side,role)
  checks.append(name);print('PASS',name,flush=True)
 except Exception:fail.append(dict(name=name,error=traceback.format_exc()));print('FAIL',name,fail[-1]['error'],flush=True)
(out/'native.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2))
