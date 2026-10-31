"""Incremental/cold equality, dependency isolation, saved-frame reuse and timings.
Pass ROTORFORGE_BASELINE_SOURCE to an unmodified v0.66.1 geometry.py.
"""
import os,sys,time,json,traceback,importlib.util
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.dependency_cache import COMPONENTS,shape_token
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True);checks=[];failures=[];bench=[]
p=Parameters(FPVEnabled=True,FlexSideGuards=True,FlexGuardCloseFront=True,FlexGuardClearance=0.,FlexMotorProtectors=True,LiPoPadEnabled=True)
try:
 spec=importlib.util.spec_from_file_location('freecad.rotorforge._baseline067',os.environ['ROTORFORGE_BASELINE_SOURCE']);baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
 def equal(a,b):
  assert set(a)==set(b)
  for role in a:
   x,y=a[role],b[role]
   assert x.isNull()==y.isNull(),role
   if x.isNull():continue
   assert len(x.Solids)==len(y.Solids) and abs(x.Volume-y.Volume)<1e-5,(role,x.Volume,y.Volume)
   cx=sum((v.CenterOfMass*v.Volume for v in x.Solids),App.Vector())/x.Volume if x.Volume else App.Vector()
   cy=sum((v.CenterOfMass*v.Volume for v in y.Solids),App.Vector())/y.Volume if y.Volume else App.Vector()
   assert (cx-cy).Length<1e-6,role
   assert x.cut(y).Volume<1e-5 and y.cut(x).Volume<1e-5,role
 cases=[('initial',p),('top thickness',replace(p,TopThickness=2.5)),('FC vent height',replace(p,TopThickness=2.5,FlexGuardFCSlotHeight=4.)),('pad grip',replace(p,LiPoPadGrooveWidth=1.6)),('density estimate',replace(p,CarbonDensity=1.7)),('motor pad',replace(p,MotorPadRotation=10.))]
 for name,q in cases:
  t=time.perf_counter();current=g.build_shapes(q);elapsed=time.perf_counter()-t;report=g.build_report(q)
  t=time.perf_counter();old=baseline.build_shapes(q);cold=time.perf_counter()-t;equal(current,old)
  rebuilt=set(report['rebuilt'])
  if name=='top thickness':assert not rebuilt.intersection(('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight','BottomPlate','MidPlate','Standoffs')),rebuilt
  if name=='FC vent height':assert rebuilt<=set(('ElectronicsGuardLeft','ElectronicsGuardRight','FrameCGMarker')),rebuilt
  if name=='pad grip':assert not rebuilt.intersection(g.CARBON_ROLES+('Standoffs',)),rebuilt
  if name=='density estimate':assert not rebuilt.intersection(g.CARBON_ROLES+g.FLEX_ROLES+('Standoffs','LiPoPad')),rebuilt
  bench.append(dict(edit=name,incremental_seconds=elapsed,full_seconds=cold,rebuilt=report['rebuilt'],reused=report['reused']));print('PASS',name,round(elapsed,3),round(cold,3),report['rebuilt'],flush=True)
 checks.append('Six configurations match the original full builder by validity, solid count, volume, centroid and bidirectional native subtraction; dependency isolation verified')
except Exception:failures.append(dict(name='Geometry/bench',error=traceback.format_exc()));traceback.print_exc()
try:
 g.clear_build_caches();doc=App.newDocument('Incremental067');settings=d.create_frame(p,doc);before={r:(o.Shape.copy(),getattr(o.Proxy,'_shape_writes',0)) for r,o in d.component_objects(settings).items()}
 q=replace(p,FlexGuardFCSlotHeight=4.);d.update_frame(settings,q);rebuilt=set(g.build_report(q)['rebuilt']);assert rebuilt<=set(('ElectronicsGuardLeft','ElectronicsGuardRight','FrameCGMarker')),rebuilt
 for r,o in d.component_objects(settings).items():
  if r not in rebuilt:assert before[r][1]==getattr(o.Proxy,'_shape_writes',0),r
 path=out/'Incremental.FCStd';doc.saveAs(str(path));App.closeDocument(doc.Name);g.clear_build_caches();doc=App.openDocument(str(path));settings=doc.getObject('FrameParameters')
 assert not COMPONENTS.events,'Restore triggered geometry'
 r=replace(q,FlexGuardFCSlotHeight=4.5);d.update_frame(settings,r);rebuilt=set(g.build_report(r)['rebuilt']);assert rebuilt<=set(('ElectronicsGuardLeft','ElectronicsGuardRight','FrameCGMarker')),rebuilt
 assert settings.RebuiltComponents and settings.LastBuildSeconds>=0
 # No-op updates do not replace any component shapes.
 before={r:(o.Shape.copy(),getattr(o.Proxy,'_shape_writes',0)) for r,o in d.component_objects(settings).items()};d.update_frame(settings,r)
 assert all(before[r][1]==getattr(o.Proxy,'_shape_writes',0) for r,o in d.component_objects(settings).items()),[(r,before[r][1],getattr(o.Proxy,'_shape_writes',0)) for r,o in d.component_objects(settings).items() if before[r][1]!=getattr(o.Proxy,'_shape_writes',0)]
 assert not settings.RebuiltComponents
 # Direct FreeCAD property edits use the same dependency engine.
 before={role:getattr(obj.Proxy,'_shape_writes',0) for role,obj in d.component_objects(settings).items()}
 settings.FlexGuardFCSlotHeight=4.6;doc.recompute();assert str(settings.Status).startswith('Valid')
 assert all(before[role]==getattr(obj.Proxy,'_shape_writes',0) for role,obj in d.component_objects(settings).items() if role not in ('ElectronicsGuardLeft','ElectronicsGuardRight','FrameCGMarker'))
 App.closeDocument(doc.Name);checks.append('Native update preserves unchanged Shape identities; save/clear/reopen reuses provenance; no-op update replaces no shapes');print('PASS PERSISTENCE',flush=True)
except Exception:failures.append(dict(name='Document',error=traceback.format_exc()));traceback.print_exc()
(out/'revision067.json').write_text(json.dumps(dict(checks=checks,failures=failures,benchmarks=bench),indent=2));print('DONE',len(checks),len(failures),flush=True)
