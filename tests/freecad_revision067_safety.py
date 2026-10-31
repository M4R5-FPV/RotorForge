"""Copies, stale native geometry and invalid input must not poison the cache."""
import os,sys,json,traceback
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.dependency_cache import COMPONENTS
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];failures=[]
try:
 p=Parameters();g.clear_build_caches()
 for width in (46.,47.,48.,49.,50.):g.build_shapes(replace(p,TopWidth=width))
 g.build_shapes(p);g.build_shapes(replace(p,TopWidth=51.))
 assert g.component_payload('BottomPlate',p) and g.component_manifest('BottomPlate',p)
 shapes=g.build_shapes(p);box=shapes['BottomPlate'].BoundBox
 expected=(box.XMin,box.YMin,box.ZMin,box.XMax,box.YMax,box.ZMax)
 shapes['BottomPlate'].translate(App.Vector(100,200,300));s=g.build_shape(p,'BottomPlate');b=s.BoundBox
 assert expected==(b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax)
 try:g.build_shapes(replace(p,TopThickness=-1.))
 except ValueError:pass
 else:raise AssertionError('Invalid dimensions accepted')
 assert abs(g.build_shape(p,'BottomPlate').Volume-s.Volume)<1e-8
 doc=App.newDocument('CacheSafety067');settings=d.create_frame(p,doc);objects=d.component_objects(settings)
 g.clear_build_caches();objects['ArmFrontRight'].Shape=Part.makeBox(1,1,1);g.prime_document_cache(settings)
 assert 'ArmFrontRight' not in COMPONENTS.latest
 d.update_frame(settings,p);assert str(settings.Status).startswith('Valid');assert objects['ArmFrontRight'].Shape.Volume>1.
 assert 'ArmFrontRight' in g.build_report(p)['rebuilt']
 objects['ArmFrontRight'].ComponentCache='[]';g.clear_build_caches();d.update_frame(settings,p);assert str(settings.Status).startswith('Valid')
 App.closeDocument(doc.Name)
 checks.append('Native returned-shape transforms and invalid parameters leave cache intact; modified saved geometry is rejected and regenerated')
except Exception:failures.append(traceback.format_exc());traceback.print_exc()
(out/'safety067.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
