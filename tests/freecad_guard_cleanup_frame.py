"""Validate a saved frame's guards, document persistence and print export.
ROTORFORGE_FRAME_SETTINGS points to the settings JSON under test.
"""
import sys,os,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,MeshPart
from freecad.rotorforge.flex_geometry import printable_flex
from freecad.rotorforge.mesh_cleanup import weld_micro_seams
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge import protection_geometry as pg
from freecad.rotorforge.parameters import load_parameters,plate_levels
p=load_parameters(Path(os.environ['ROTORFORGE_FRAME_SETTINGS']))
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
checks=[];kept_valid=[];original=pg.guard_refine
def checked_refine(shape):
 valid_before=shape.isValid()
 candidate=shape.copy().removeSplitter()
 result=original(shape)
 if valid_before and not candidate.isValid():kept_valid.append(True)
 if valid_before:assert shape.isValid() and result.isValid()
 return result
pg.guard_refine=checked_refine
doc=App.newDocument();frame=d.create_frame(p,doc)
assert str(frame.Status).startswith('Valid'),frame.Status
parts=d.component_objects(frame)
for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
 shape=parts[role].Shape
 assert shape.isValid() and len(shape.Solids)==1
 assert abs(shape.BoundBox.ZMax-(plate_levels(p)['top_z']+p.TopThickness))<1e-5
 mesh=MeshPart.meshFromShape(Shape=printable_flex(shape,role),LinearDeflection=.08,AngularDeflection=.2,Relative=False)
 mesh=weld_micro_seams(mesh)
 assert mesh.isSolid(),role+' print mesh is not watertight'
 mesh.write(str(out/(role+'.stl')))
 checks.append(role+' valid, connected and reaches top face; watertight print STL exported')
checks.append('Failed OCC refinement kept a valid independent source: '+str(len(kept_valid)))
path=out/'GuardCleanupFrame.FCStd';doc.saveAs(str(path));App.closeDocument(doc.Name)
doc=App.openDocument(str(path));frame=doc.getObject('FrameParameters')
assert d.read_parameters(frame)==p
for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):assert d.component_objects(frame)[role].Shape.isValid()
checks.append('Save/reopen retains settings and valid guard solids')
(out/'guard_cleanup.json').write_text(json.dumps(dict(checks=checks,unsafe_refinements_avoided=len(kept_valid),freecad=App.Version()[:3]),indent=2))
App.closeDocument(doc.Name);print(checks,flush=True)
