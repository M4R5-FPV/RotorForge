"""Saved frame editing must preserve BReps and never start a solid rebuild."""
import os,sys,time,json,traceback
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge import geometry,document
from freecad.rotorforge.parameters import Parameters
root=Path(__file__).resolve().parents[1];out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
checks=[];failures=[];timings=[];calls=[];original=geometry._build

def forbidden(signature):calls.append(signature);raise ValueError('A saved frame triggered an unsolicited solid build')
geometry._build=forbidden
for path in sorted((root/'examples').glob('*.FCStd'))+sorted((root/'tests/fixtures').glob('*.FCStd')):
 doc=None
 try:
  t=time.perf_counter();doc=App.openDocument(str(path));settings=next(o for o in doc.Objects if 'GeneratorVersion' in o.PropertiesList)
  before={o.Name:(None if o.Shape.isNull() else o.Shape.exportBrepToString(),str(o.Placement)) for o in document.component_objects(settings).values()}
  saved_parameters={n:str(getattr(settings,n)) for n in settings.PropertiesList if n not in ('Proxy','Label2')}
  settings.touch();doc.recompute()
  after={o.Name:(None if o.Shape.isNull() else o.Shape.exportBrepToString(),str(o.Placement)) for o in document.component_objects(settings).values()}
  assert before==after,'Saved component geometry changed';assert not calls,'Restore/recompute called the solid builder'
  assert all(str(getattr(settings,n))==v for n,v in saved_parameters.items()),'Restore changed persisted parameters'
  checks.append('Restore '+path.name);timings.append(dict(file=path.name,seconds=time.perf_counter()-t));print('PASS',path.name,flush=True)
 except Exception:failures.append(dict(name=path.name,error=traceback.format_exc()));traceback.print_exc()
 finally:
  if doc:App.closeDocument(doc.Name)
# Failed geometry must only be attempted once across all dependent parts.
try:
 geometry._FAILED_BUILDS.clear();p=Parameters();calls.clear()
 for role in geometry.ALL_ROLES:
  try:geometry.build_shape(p,role)
  except ValueError as exc:assert 'unsolicited' in str(exc)
 assert len(calls)==1,len(calls)
 q=replace(p,ArmWidth=p.ArmWidth+1)
 try:geometry.build_shapes(q)
 except ValueError:pass
 assert len(calls)==2
 geometry.invalidate_failed_build(p)
 try:geometry.build_shapes(p)
 except ValueError:pass
 assert len(calls)==3
 checks.append('One failed CAD attempt per signature; changed parameters and explicit retry remain possible')
except Exception:failures.append(dict(name='Failed build fan-out',error=traceback.format_exc()));traceback.print_exc()
geometry._build=original;geometry._FAILED_BUILDS.clear()
(out/'restore061.json').write_text(json.dumps(dict(checks=checks,failures=failures,timings=timings),indent=2));print('DONE',len(checks),len(failures),flush=True)
