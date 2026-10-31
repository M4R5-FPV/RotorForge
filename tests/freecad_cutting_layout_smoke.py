"""Exact native profiles, stock sheets, repeat export, Undo and persistence."""
from pathlib import Path
from dataclasses import replace
import json,os,sys,traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.cutouts import PATTERN_DEFAULTS,encode_patterns
from freecad.rotorforge.document import create_frame,update_frame,component_objects,find_parameters
from freecad.rotorforge.geometry import build_shapes,flat_plate_shape,carbon_roles
from freecad.rotorforge.exporters import export_package,profile_entities
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[]}
def check(ok,label):
 if not ok:raise AssertionError(label)
 report['checks'].append(label)
def verify(settings,p,folder):
 doc=settings.Document;root=next(o for o in doc.Objects if 'RotorForgeCuttingLayout' in o.PropertiesList and o.SourceFrame==settings)
 shapes=build_shapes(p);layout=json.loads((folder/'CuttingProfiles/Layout.json').read_text());actual=[]
 check(root.Placement.Base.x>max(s.BoundBox.XMax for s in shapes.values() if not s.isNull()), 'Layout beside source assembly')
 for sheet,group in zip(layout['sheets'],root.Group):
  check(abs(group.StockThickness.Value-sheet['thickness'])<1e-7,'Thickness group')
  check(Path(group.DXFFile).is_file() and Path(group.SVGFile).is_file(),'Stock files linked')
  check(find_parameters([group])==settings,'Stock selects its source frame')
  svg=Path(group.SVGFile).read_text();check('<text' not in svg and 'translate(0.0,' in svg,'SVG has no added offset or text')
  raw=Path(group.DXFFile).read_text().splitlines();pairs=list(zip(raw[::2],raw[1::2]));entries=[];current={}
  for code,val in pairs:
   if code=='0':
    if current.get('0') in ('LINE','ARC','CIRCLE','ELLIPSE'):entries.append(current)
    current={'0':val}
   else:current[code]=val

  check(abs(group.Placement.Base.y-sheet['combined_y'])<1e-7,'Separated stock sheets')
  for item,obj in zip(sheet['parts'],group.Group):
   role=item['role'];actual.append(role);shape=obj.Shape;b=shape.BoundBox
   check(abs(b.ZMin)<1e-6 and b.ZLength<1e-6,role+': planar XY')
   check(abs(b.XMin-item['x'])<1e-6 and abs(b.YMin-item['y'])<1e-6,role+': matches file layout')
   source=flat_plate_shape(shapes[role],role,p);face=max((f for f in source.Faces if abs(f.normalAt(0,0).z)>.999999),key=lambda f:f.CenterOfMass.z)
   check(abs(shape.Area-face.Area)<1e-5 and len(shape.Wires)==len(face.Wires),role+': exact holes and area')
   check(shape.isValid() and len(shape.Faces)==1,role+': valid CAM face')
   check(obj.SourcePart==component_objects(settings)[role],role+': links source')
   check(find_parameters([obj])==settings,role+': profile selects source frame')
   records=[r for r in entries if r.get('8')==role];native=profile_entities(shape)
   codes={'LINE':('10','20','11','21'),'CIRCLE':('10','20','40'),'ARC':('10','20','40','50','51'),'ELLIPSE':('10','20','11','21','40','41','42')}
   parsed=[(r['0'],*[float(r[k]) for k in codes[r['0']]]) for r in records]
   check(len(parsed)==len(native) and all(a[0]==b[0] and all((min(abs(x-y)%360,360-abs(x-y)%360)<1e-7 if a[0]=='ARC' and i>=3 else abs(x-y)<1e-7) for i,(x,y) in enumerate(zip(a[1:],b[1:]))) for a,b in zip(parsed,native)),role+': native matches DXF exactly')
   check(len(shape.Edges)==len(face.Edges),role+': no doubled contours')
 check(set(actual)==set(carbon_roles(p)) and len(actual)==len(set(actual)),'Every carbon part once')
 check(not any('Standoff' in name for name in actual),'No hardware profiles')
 check(find_parameters([root])==settings,'Layout root selects source frame')
 return root
try:
 for p in [Parameters(PlateDesign='2 plates'),Parameters(FPVEnabled=True,StandoffHeight=35,CameraTiltMax=45,MotorPadShape='Dogbone'),Parameters(CutoutPatterns=encode_patterns([dict(PATTERN_DEFAULTS,shape='Ellipse',width=8,length=12,y=28,rotation=37),dict(PATTERN_DEFAULTS,shape='Slot',width=4,length=16),dict(PATTERN_DEFAULTS,mode='Outline notch',shape='Circle',width=6,x=23,y=-32)]))]:
  settings=create_frame(p);doc=settings.Document;doc.UndoMode=1
  original={role:o.Shape.copy() for role,o in component_objects(settings).items() if not o.Shape.isNull()}
  folder=export_package(settings,out);root=verify(settings,p,folder)
  for role,shape in original.items():check(shape.cut(component_objects(settings)[role].Shape).Volume+component_objects(settings)[role].Shape.cut(shape).Volume<1e-6,role+': source unchanged')
  count=len(doc.Objects);identities={o.SourceRole:o.ID for g in root.Group for o in g.Group};folder2=export_package(settings,out);check(identities=={o.SourceRole:o.ID for g in root.Group for o in g.Group},'Re-export preserves profile object identities');check(folder!=folder2,'Exports do not overwrite folders')
  check(len(doc.Objects)==count,'Repeated export has no duplicate objects');verify(settings,p,folder2)
  root.Placement.Base=App.Vector(600,0,0);export_package(settings,out);check(root.Placement.Base.x==600,'Keep manually moved layout origin')
  update_frame(settings,replace(p,TopThickness=p.TopThickness+.5));before=root.ExportFolder;newfolder=export_package(settings,out);check(root.ExportFolder!=before,'Refresh snapshot after edit')
  doc.undo();doc.recompute();check(root.ExportFolder==before,'Undo restores prior snapshot')
  path=out/('CNC_'+p.PlateDesign[0]+'.FCStd');doc.saveAs(str(path));App.closeDocument(doc.Name)
  doc=App.openDocument(str(path));root=next(o for o in doc.Objects if 'RotorForgeCuttingLayout' in o.PropertiesList)
  check(all(o.Shape.isValid() and o.Shape.BoundBox.ZLength<1e-7 for g in root.Group for o in g.Group),'Native profile snapshot reopens')
  App.closeDocument(doc.Name)
 # Two frames in one document keep independent snapshots; failed refresh rolls back.
 p=Parameters(PlateDesign='2 plates');first=create_frame(p);doc=first.Document;second=create_frame(p,doc)
 f1=export_package(first,out);f2=export_package(second,out)
 roots=[o for o in doc.Objects if 'RotorForgeCuttingLayout' in o.PropertiesList]
 check(len(roots)==2 and roots[0].SourceFrame!=roots[1].SourceFrame,'Multiple frames have separate snapshots')
 from freecad.rotorforge.cutting_layout import document_layout
 root=next(o for o in roots if o.SourceFrame==first);before=len(doc.Objects);oldfolder=root.ExportFolder
 layout=json.loads((f1/'CuttingProfiles/Layout.json').read_text())
 try:document_layout(first,layout,{},f1/'CuttingProfiles',0)
 except KeyError:pass
 else:raise AssertionError('Injected failure did not occur')
 check(len(doc.Objects)==before and root.ExportFolder==oldfolder and all(o.Shape.isValid() for g in root.Group for o in g.Group),'Failed document refresh rolls back')
 report['status']='passed'
except Exception:report.update(status='failed',error=traceback.format_exc());print(report['error'],flush=True)
finally:(out/'test_report.json').write_text(json.dumps(report,indent=2));print('CNC',report['status'],len(report['checks']),flush=True)
