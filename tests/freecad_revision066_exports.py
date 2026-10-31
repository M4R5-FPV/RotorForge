"""Check print-positioned guard STEP/STL exports from native validation BReps."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part,MeshPart
from freecad.rotorforge.flex_geometry import printable_flex
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];failures=[]
try:
 for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
  s=Part.Shape();s.read(str(out/(role+'.brep')));flat=printable_flex(s,role)
  assert min(flat.BoundBox.XMin,flat.BoundBox.YMin,flat.BoundBox.ZMin)>-1e-5
  step=out/(role+'.step');flat.exportStep(str(step));restored=Part.Shape();restored.read(str(step));assert restored.isValid() and len(restored.Solids)==1 and abs(restored.Volume-flat.Volume)<.01
  mesh=MeshPart.meshFromShape(Shape=flat,LinearDeflection=.12,AngularDeflection=.3,Relative=False);assert mesh.isSolid();mesh.write(str(out/(role+'.stl')))
 checks.append('Both full-height guards export as closed print-positioned STL meshes and roundtrip as single STEP solids')
except Exception:failures.append(traceback.format_exc());traceback.print_exc()
(out/'exports066.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
