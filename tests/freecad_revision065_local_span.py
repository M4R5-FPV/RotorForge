"""Middle widening is retained without changing the local front cap width."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];failures=[]
for mode in ('Rounded nose','V-notch'):
 try:
  p=Parameters(BottomNoseShape=mode,BottomCentreWidth=80.,MidCentreWidth=80.)
  s=build_shapes(p)['BottomPlate'];assert s.isValid() and len(s.Solids)==1
  assert s.isInside(App.Vector(35,0,1),1e-5,True),'Middle widened stock was trimmed'
  if mode=='Rounded nose':assert not s.isInside(App.Vector(22,80,1),1e-5,True),'Nose incorrectly follows the distant middle width'
  checks.append(mode);print('PASS',mode,flush=True)
 except Exception:failures.append(dict(name=mode,error=traceback.format_exc()));traceback.print_exc()
(out/'span065.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
