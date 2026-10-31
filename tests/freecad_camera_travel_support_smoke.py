import sys,traceback,json,os,itertools
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.fpv import camera_mounts
from freecad.rotorforge.cutouts import encode_patterns
from freecad.rotorforge.plate_fillets import _corners
checks=[];failures=[]
for mode,shape,offset in itertools.product(('Hard mount','Compression pads','Captured inserts'),('Rounded rectangle','Side plate outline'),(10.,20.)):
 label=f'{mode} / {shape} / {offset}'
 try:
  p=Parameters(FPVEnabled=True,FlexCameraMode=mode,FlexInterfaceShape=shape,CameraForeAftOffset=offset)
  s=build_shapes(p)
  for role in ('CameraMountLeft','CameraMountRight')+(() if mode=='Hard mount' else ('CameraPadLeft','CameraPadRight')):assert s[role].isValid() and len(s[role].Solids)==1,role
  checks.append(label);print('PASS',label,flush=True)
 except Exception:failures.append(dict(name=label,error=traceback.format_exc()));print('FAIL',label,failures[-1]['error'],flush=True)
for enabled in (False,True):
 try:
  p=Parameters(TopEdgeFillet=3,TopFilletOpenings=enabled,CutoutPatterns=encode_patterns([dict(role='TopPlate',shape='Rectangle',width=10,length=16)]))
  s=build_shapes(p)['TopPlate'];cap=max((f for f in s.Faces if f.BoundBox.ZLength<1e-5),key=lambda f:f.Area);corners=sum(len(_corners(w)) for w in cap.Wires if not w.isSame(cap.OuterWire));assert corners==(0 if enabled else 4),corners
  checks.append('Native internal corners / '+str(enabled));print('PASS internal',enabled,flush=True)
 except Exception:failures.append(dict(name='Internal '+str(enabled),error=traceback.format_exc()));traceback.print_exc()
Path(os.environ['ROTORFORGE_TEST_OUTPUT'],'camera.json.report').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
