"""Exact geometry, cache fallback, document repair and export regression checks."""
import os,sys,json,tempfile,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
import FreeCAD as App,Part
from dataclasses import replace
from freecad.rotorforge import geometry as g,document as d,disk_cache
from freecad.rotorforge.parameters import load_parameters
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
p=load_parameters(os.environ['ROTORFORGE_TEST_SETTINGS']);checks=[]
def passed(text):
 checks.append(text);(out/'checks.json').write_text(json.dumps(checks,indent=2));print('PASS',text,flush=True)
def equal(a,b):
 assert a.isNull()==b.isNull()
 if a.isNull():return
 assert a.isValid() and b.isValid() and len(a.Solids)==len(b.Solids)
 assert abs(a.Volume-b.Volume)<1e-6
 assert a.cut(b).Volume+b.cut(a).Volume<1e-5
with tempfile.TemporaryDirectory() as directory:
 os.environ['ROTORFORGE_CACHE_DIR']=directory;g.clear_build_caches()
 original=g.build_for_update(p);first=g.build_report(p);assert first['rebuilt'] and first['disk_restored']==0
 g.clear_build_caches();restored=g.build_for_update(p);report=g.build_report(p)
 assert report['disk_restored']>0 and not report['rebuilt'],report
 for role in g.physical_roles(p):equal(original[role],restored[role])
 passed('Disk-restored physical parts are exact equivalents; all components reused')
 q=replace(p,TopWidth=p.TopWidth+4);g.build_for_update(q);report=g.build_report(q)
 assert 'TopPlate' in report['rebuilt'] and 'BottomPlate' in report['reused'],report
 passed('Real plate changes invalidate the plate and dependent guards')
 try:g.build_for_update(replace(p,TopThickness=0))
 except ValueError:pass
 else:raise AssertionError('invalid dimensions were accepted')
 passed('Cached geometry never bypasses dimension checks')
 key=disk_cache.identity(g._geometry_signature(p));(Path(directory)/(key+'.zip')).write_bytes(b'broken cache')
 g.clear_build_caches();repaired=g.build_for_update(p)
 assert g.build_report(p)['rebuilt']
 for role in g.physical_roles(p):equal(original[role],repaired[role])
 passed('Corrupt archive falls back to exact regeneration')
 frame=d.create_frame(p,App.newDocument('Performance088'));obj=d.component_objects(frame)['TopPlate']
 obj.Shape=Part.makeBox(1,1,1);d.update_frame(frame,p);equal(original['TopPlate'],obj.Shape)
 passed('Update repairs externally modified native geometry')
 frame.BatteryMass=p.BatteryMass+1;assert d.read_parameters(frame).BatteryMass==p.BatteryMass+1
 d.update_frame(frame,p);assert d.read_parameters(frame).BatteryMass==p.BatteryMass
 passed('Direct property edits remain visible and update correctly')
 saved=out/'Performance088.FCStd';frame.Document.saveAs(str(saved));App.closeDocument(frame.Document.Name)
 doc=App.openDocument(str(saved));frame=doc.getObject('FrameParameters');d.update_frame(frame,p)
 for role in g.physical_roles(p):equal(original[role],d.component_objects(frame)[role].Shape)
 passed('Saved frame reopens and updates with equivalent geometry')
 from freecad.rotorforge.exporters import export_package
 folder=Path(export_package(frame,str(out/'export')))
 assert (folder/'FrameAssembly.step').is_file() and (folder/'FrameParameters.json').is_file()
 assert list((folder/'CuttingProfiles').glob('*.dxf')) and list((folder/'CuttingProfiles').glob('*.svg'))
 passed('STEP, DXF, SVG, settings and flexible-part exports complete')
 App.closeDocument(doc.Name)
