"""True zero plate clearance, small positive fit and unchanged ordinary gap."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.protection_layout import guard_layout,guard_plate_gap
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];failures=[]
for design in ('2 plates','3 plates'):
 for gap in (0.,.05,1.):
  name=design+'/clearance '+str(gap)
  try:
   p=Parameters(PlateDesign=design,FlexSideGuards=True,FlexGuardStyle='Solid',FlexGuardClearance=gap);s=build_shapes(p)
   for g in guard_layout(p):
    guard=s[g['role']];assert guard.isValid() and len(guard.Solids)==1
    for role in ('TopPlate',g['lower_role']):
     distance=guard.distToShape(s[role])[0]
     if gap==0:assert distance<1e-5,(role,distance)
     else:assert distance>1e-4,(role,distance)
     assert guard.common(s[role]).Volume<1e-5,(role,'carbon overlap')
   checks.append(name);print('PASS',name,flush=True)
  except Exception:failures.append(dict(name=name,error=traceback.format_exc()));traceback.print_exc()
(out/'revision0641.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
