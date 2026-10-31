import sys,json,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from dataclasses import replace
from freecad.rotorforge import document as d,geometry as g
from freecad.rotorforge.parameters import Parameters,plate_levels
p=Parameters(FlexSideGuards=True)
doc=App.newDocument();f=d.create_frame(p,doc);path=(Path(os.environ['ROTORFORGE_TEST_OUTPUT'])/'GuardHeight.FCStd').resolve();doc.saveAs(str(path));App.closeDocument(doc.Name)
doc=App.openDocument(str(path));f=doc.getObject('FrameParameters')
q=replace(p,TopThickness=3.)
d.update_frame(f,q)
parts=d.component_objects(f)
for side in ('Left','Right'):assert abs(parts['ElectronicsGuard'+side].Shape.BoundBox.ZMax-(plate_levels(q)['top_z']+3.))<1e-6
report=g.build_report(q);assert all(role not in report['rebuilt'] for role in ('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight','BottomPlate','MidPlate'))
(Path(os.environ['ROTORFORGE_TEST_OUTPUT'])/'update.json').write_text(json.dumps(dict(rebuilt=report['rebuilt'],save_reopen_update=True),indent=2))
print('PASS',report['rebuilt'],flush=True)
