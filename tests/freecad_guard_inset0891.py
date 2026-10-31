"""Physical bearing area, inward placement, strap access and old-file update."""
import sys,os,json,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.path.insert(0,str(root/'tests'))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
import FreeCAD as App,Part
from dataclasses import replace
from freecad.rotorforge import geometry as geo,document as doc
from freecad.rotorforge.parameters import Parameters,plate_levels,strap_slots
from freecad.rotorforge.protection_layout import guard_layout
from freecad.rotorforge.strap_openings import notch_polygons
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
baseline=Path(os.environ['ROTORFORGE_BASELINE_SHAPES']);checks=[]
cache=tempfile.TemporaryDirectory();os.environ['ROTORFORGE_CACHE_DIR']=cache.name
def passed(name):
 checks.append(name);(out/'checks.json').write_text(json.dumps(checks,indent=2));print('PASS',name,flush=True)
def bearing(p,shapes):
 lv=plate_levels(p)
 for g in guard_layout(p):
  guard=shapes[g['role']]
  assert guard.isValid() and len(guard.Solids)==1
  # The actual solid must share finite contact area with each actual plate.
  for role in (g['lower_role'],'TopPlate'):
   plate=shapes[role]
   assert guard.common(plate).Volume<1e-6,(g['role'],role,'overlap')
   z=lv['top_z'] if role=='TopPlate' else lv['deck_z']
   def at_plane(face):return face.BoundBox.ZLength<1e-6 and abs(face.BoundBox.ZMin-z)<1e-6
   area=sum(a.common(b).Area for a in guard.Faces if at_plane(a) for b in plate.Faces if at_plane(b))
   assert area>15.,(g['role'],role,'no clamping face',area)
  assert abs(guard.BoundBox.ZMax-lv['top_z'])<1e-6
  assert abs(guard.BoundBox.ZMin-lv['deck_z'])<1e-6
  # At a section away from posts, the whole top contact strip sits inside
  # the plate. Below it, a wall may slope outward toward a wider carrier.
  slab=Part.makePlane(300,2,App.Vector(-150,-1,lv['top_z']))
  def top_face(face):return face.BoundBox.ZLength<1e-6 and abs(face.BoundBox.ZMin-lv['top_z'])<1e-6
  sections=[f.common(slab) for f in guard.Faces if top_face(f)]
  sections=[f for f in sections if not f.isNull()]
  support=[f for f in shapes['TopPlate'].Faces if top_face(f)]
  area=sum(f.Area for f in sections)
  covered=sum(f.common(s).Area for f in sections for s in support)
  assert area>1.
  assert abs(area-covered)<1e-6,(g['role'],'wall outside top footprint',area,covered)
base=Parameters(FlexSideGuards=True,FlexGuardFitMode='Between plates',FlexGuardStyle='Solid')
cases=[('two plates',replace(base,PlateDesign='2 plates')),
       ('three plates',base),
       ('zero inset',replace(base,FlexGuardClearance=0.)),
       ('larger inset',replace(base,FlexGuardClearance=2.)),
       ('tapered filleted top',replace(base,TopPlateShape='Tapered front',TopEdgeFillet=1.))]
for name,p in cases:
 shapes=geo.build_for_update(p);bearing(p,shapes);passed('Clamped contact and inward wall: '+name)
for style,count,clearance in [('Outline cutouts','1 strap',1.),('Outline cutouts','2 straps',0.),('Slots','2 straps',4.)]:
 p=replace(base,StrapOpeningStyle=style,StrapCount=count,StrapSingleY=0.,FlexGuardClearance=clearance,TopWidth=54.,BodyWidth=58.)
 shapes=geo.build_for_update(p);lv=plate_levels(p);z=lv['top_z']-1.99;h=1.98
 tools=[geo.capsule(a,b,r,z,h) for a,b,r in strap_slots(p)]
 for poly in notch_polygons(p):
  pts=[App.Vector(x,y,z) for x,y in poly];tools.append(Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(0,0,h)))
 passage=Part.makeCompound(tools)
 for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
  assert shapes[role].common(passage).Volume<1e-6,(style,count,'strap floor blocked')
  assert shapes[role].isValid() and len(shapes[role].Solids)==1
 passed('Under-plate strap passage: '+style+' / '+count)
for design in ('2 plates','3 plates'):
 p=Parameters(PlateDesign=design,FlexSideGuards=True,FlexGuardStyle='Solid',FlexGuardWireEnabled=True)
 shapes=geo.build_for_update(p)
 for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
  old=Part.Shape();old.read(str(baseline/(design[0]+role+'.brep')))
  assert shapes[role].cut(old).Volume+old.cut(shapes[role]).Volume<1e-5
 passed('Original wrap unchanged: '+design)
d=App.openDocument(str(baseline/'InsetBefore0891.FCStd'));f=d.getObject('FrameParameters');p=doc.read_parameters(f)
old=doc.component_objects(f)['ElectronicsGuardRight'].Shape.copy()
doc.update_frame(f,p);shapes={r:o.Shape for r,o in doc.component_objects(f).items()};bearing(p,shapes)
assert shapes['ElectronicsGuardRight'].cut(old).Volume>1
path=out/'InsetCorrected0891.FCStd';d.saveAs(str(path));App.closeDocument(d.Name)
geo.clear_build_caches();d=App.openDocument(str(path));f=d.getObject('FrameParameters');doc.update_frame(f,p)
bearing(p,{r:o.Shape for r,o in doc.component_objects(f).items()});App.closeDocument(d.Name)
passed('0.89.0 saved frame rebuilds inward and retains contact after reopen')
p=replace(base,FlexGuardClearance=.75);geo.build_for_update(p);geo.clear_build_caches();s=geo.build_for_update(p)
bearing(p,s);report=geo.build_report(p);assert report['disk_restored']>0 and not report['rebuilt'],report
passed('Persistent cache restores clamped geometry')
