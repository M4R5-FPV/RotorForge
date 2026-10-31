"""Exact strap passage, straight guard wall, saved update and print exports."""
import sys, os, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App, Part, MeshPart
from freecad.rotorforge.parameters import Parameters, plate_levels
from freecad.rotorforge import geometry as g, document as d
from freecad.rotorforge.cutouts import PATTERN_DEFAULTS, encode_patterns
from freecad.rotorforge.mesh_cleanup import weld_micro_seams
from freecad.rotorforge.dependency_cache import clear_geometry_caches

out = Path(os.environ['ROTORFORGE_TEST_OUTPUT']); out.mkdir(parents=True, exist_ok=True)
checks = []
base = Parameters(FlexSideGuards=True, FlexGuardExtendFront=True,
                  FlexGuardStyle='Solid', FlexGuardClearance=0.,
                  StrapOpeningStyle='Outline cutouts', StrapSingleY=-4.)
cases = [(design+'/'+count, replace(base, PlateDesign=design, StrapCount=count))
         for design in ('2 plates', '3 plates') for count in ('1 strap', '2 straps')]
cases += [('widened', replace(base, TopCentreWidth=60., CentreSectionLength=60.)),
          ('tapered and filleted', replace(base, TopPlateShape='Tapered front', TopEdgeFillet=1.)),
          ('camera closure', replace(base, FPVEnabled=True, StandoffHeight=35., FlexGuardCloseFront=True)),
          ('clearance and separate guard openings', replace(base, FlexGuardClearance=.5, FlexGuardStraps=True,
                                                          FlexGuardStrapWidth=16., FlexGuardStrapCount='2 straps')),
          ('custom edge notch retained', replace(base, CutoutPatterns=encode_patterns([
              dict(PATTERN_DEFAULTS, role='TopPlate', mode='Outline notch', shape='Circle', x=base.TopWidth/2, y=0., width=6.)])))]
start_case = int(os.environ.get('ROTORFORGE_START_CASE', '0'))
for index, (name, p) in enumerate(cases):
    if index < start_case: continue
    shapes = g.build_for_update(p)
    plain = g.build_for_update(replace(p, StrapSlotsEnabled=False))
    passage = plain['TopPlate'].cut(shapes['TopPlate'])
    assert passage.Volume > 1., name
    for role in ('ElectronicsGuardLeft', 'ElectronicsGuardRight'):
        shape, expected = shapes[role], plain[role]
        assert shape.isValid() and len(shape.Solids) == 1, (name, role)
        assert shape.common(passage).Volume < 1e-6, (name, role, 'strap opening filled')
        assert shape.cut(expected).Volume + expected.cut(shape).Volume < 1e-5, (name, role, 'guard follows notch')
        assert shape.common(shapes['TopPlate']).Volume < 1e-6, (name, role, 'carbon overlap')
        if index in (0, 5, 7):
            mesh = weld_micro_seams(MeshPart.meshFromShape(Shape=shape, LinearDeflection=.08,
                                                         AngularDeflection=.2, Relative=False))
            assert mesh.isSolid(), (name, role, 'open STL')
            mesh.write(str(out/(str(index)+role+'.stl')))
    checks.append(name)
    (out/'checks.json').write_text(json.dumps(checks, indent=2))
    print('PASS', name, flush=True)
# Repositioning and disabling notches rebuilds the affected plate/guards;
# neither a cached guide nor a saved profile may refill an opening.
p = replace(base, StrapCount='1 strap')
doc = App.newDocument('GuardStrapBridge0872'); frame = d.create_frame(p, doc)
for changes in ({'StrapNotchDepth':5., 'StrapSlotLength':16., 'StrapSingleY':6.},
                {'StrapSlotsEnabled':False}, {'StrapSlotsEnabled':True}):
    p = replace(p, **changes); d.update_frame(frame, p)
    shapes = g.build_shapes(p); plain = g.build_shapes(replace(p, StrapSlotsEnabled=False))
    for role in ('ElectronicsGuardLeft', 'ElectronicsGuardRight'):
        assert shapes[role].common(plain['TopPlate'].cut(shapes['TopPlate'])).Volume < 1e-6
path = out/'GuardStrapBridge0872.FCStd'; doc.saveAs(str(path)); App.closeDocument(doc.Name)
clear_geometry_caches()
doc = App.openDocument(str(path)); frame = doc.getObject('FrameParameters')
assert d.read_parameters(frame) == p
from freecad.rotorforge.exporters import export_package
folder = export_package(frame, out/'export')
assembly = Part.read(str(folder/'FrameAssembly.step')); shapes = g.build_shapes(p)
assert abs(assembly.Volume-sum(shapes[r].Volume for r in g.physical_roles(p))) < 1e-3
for role in ('ElectronicsGuardLeft', 'ElectronicsGuardRight'):
    export = Part.read(str(folder/'FlexibleParts'/(role+'_assembled.step')))
    assert export.common(plain['TopPlate'].cut(shapes['TopPlate'])).Volume < 1e-6
App.closeDocument(doc.Name)
checks.append('moves/toggles, saved frame and assembly STEP preserve open strap passages')
(out/'checks.json').write_text(json.dumps(checks, indent=2)); print('PASS', len(checks), flush=True)
