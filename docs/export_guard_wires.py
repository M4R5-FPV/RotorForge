"""Export actual side-guard wire exits for the guide."""
import sys,os,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.protection_layout import guard_layout,guard_wire_openings
p=Parameters(FlexSideGuards=True,FlexGuardWireEnabled=True,FlexGuardStyle='Solid')
s=build_shapes(p)['ElectronicsGuardRight'];v,f=s.tessellate(.08)
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
(out/'wire_guard.json').write_text(json.dumps(dict(vertices=[list(a) for a in v],faces=f,openings=guard_wire_openings(p,guard_layout(p)[1]))))
print('WIRE FIGURE DONE',flush=True)
