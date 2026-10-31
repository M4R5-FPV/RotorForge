"""New upper recesses integrate with captured inserts and forward side guards."""
import os,sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge import geometry as g
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];fail=[]
try:
 for shape in ('Camera U recess','Camera swept recess'):
  p=Parameters(FPVEnabled=True,TopFrontShape=shape,StandoffHeight=35.,CameraTilt=55.,CameraTiltMax=60.,FlexCameraMode='Captured inserts',FlexInsertLipSide='Inside only',FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardCloseFront=True,FlexGuardClearance=0.)
  parts=g.build_shapes(p)
  for n in ('TopPlate','CameraMountLeft','CameraMountRight','CameraPadLeft','CameraPadRight','ElectronicsGuardLeft','ElectronicsGuardRight'):
   assert parts[n].isValid() and len(parts[n].Solids)==1,(shape,n)
  checks.append(shape+' with inside retaining lips and full forward guards')
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'protection_top_front.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print(checks,fail,flush=True)
