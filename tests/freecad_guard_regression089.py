"""Old document migration, independent cuts and cached base-wall reuse."""
import sys,os,json,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.path.insert(0,str(root/'tests'))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
import FreeCAD as App,Part
from dataclasses import replace
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.parameters import Parameters
from test_guard_options089 import vtx_frame
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[]
cache_dir=tempfile.TemporaryDirectory();os.environ['ROTORFORGE_CACHE_DIR']=cache_dir.name
def equal(a,b):
 assert abs(a.Volume-b.Volume)<1e-6
 assert a.cut(b).Volume+b.cut(a).Volume<1e-5
base=Path(os.environ['ROTORFORGE_BASELINE_SHAPES'])
for mode in ('2 plates','3 plates'):
 p=Parameters(PlateDesign=mode,FlexSideGuards=True,FlexGuardStyle='Solid',FlexGuardWireEnabled=True)
 shapes=g.build_for_update(p)
 for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
  old=Part.Shape();old.read(str(base/(mode[0]+role+'.brep')));equal(old,shapes[role])
 doc=App.openDocument(str(base/(mode[0]+'Original088.FCStd')));f=doc.getObject('FrameParameters')
 assert 'FlexGuardFitMode' not in f.PropertiesList
 assert d.read_parameters(f)==p
 d.update_frame(f,p)
 assert f.FlexGuardFitMode=='Plate-edge wrap' and not f.FlexGuardVTXOpening
 for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):equal(d.component_objects(f)[role].Shape,shapes[role])
 App.closeDocument(doc.Name);checks.append('0.88.0 geometry and document migration: '+mode)
p=vtx_frame(VTXWidth=36.,FlexGuardVTXOpening=False,FlexGuardFitMode='Between plates',FlexGuardStyle='Solid')
closed=g.build_for_update(p)
for side in ('Left','Right'):
 q=replace(p,FlexGuardVTXOpening=True,FlexGuardVTXSide=side);s=g.build_for_update(q)
 other='Right' if side=='Left' else 'Left'
 equal(closed['ElectronicsGuard'+other],s['ElectronicsGuard'+other])
 assert s['ElectronicsGuard'+side].Volume<closed['ElectronicsGuard'+side].Volume-1
 checks.append(side+'-only VTX opening preserves the opposite guard')
q=replace(q,FlexGuardVTXY=2.);g.build_for_update(q);report=g.build_report(q)
assert any(e['role']=='_guard_base:ElectronicsGuardRight' and e['action']=='reused' for e in report['events']),report
assert 'TopPlate' in report['reused'] and 'BottomPlate' in report['reused'],report
checks.append('Moving a VTX opening reuses base guards and unchanged carbon')
g.clear_build_caches();g.build_for_update(q);report=g.build_report(q)
assert report['disk_restored']>0 and not report['rebuilt'],report
checks.append('Persistent cache restores the new geometry after clearing memory')
(out/'checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks),flush=True)
