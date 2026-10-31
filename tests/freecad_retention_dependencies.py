import os
import sys,json,traceback
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge import geometry as g
from freecad.rotorforge.parameters import Parameters
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];fail=[]
try:
 p=Parameters();g.clear_build_caches();g.build_shapes(p);q=replace(p,ArmNutMount='Recessed hex nut');g.build_shapes(q);rebuilt=g.build_report(q)['rebuilt']
 assert set(rebuilt)<=set(('MidPlate','FrameCGMarker')),rebuilt
 checks.append(dict(name='Nut-retention edit rebuilds receiving mid plate and dependent CG only',rebuilt=rebuilt))
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'dependency070.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print(checks,fail)
