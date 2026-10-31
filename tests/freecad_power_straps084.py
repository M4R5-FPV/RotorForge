"""Native grommet contact, power reference bounds, strap machining and reuse."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,Part,MeshPart
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.detailed_references import stack_model,stack_dimensions,detailed_reference,lipo_model,vtx_model
from freecad.rotorforge.protection_layout import guard_layout,guard_strap_windows
from freecad.rotorforge.mass_properties import mass_properties
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True);checks=[];fail=[]
try:
 for spacing in (20.,30.5):
  for height in (3.,14.,24.):
   shape,colours=stack_model(spacing,height,3.2);assert shape.isValid() and len(shape.Faces)==len(colours)
   t,cap,low,high,join=stack_dimensions(height)
   for i in range(4):
    esc,fc=shape.Solids[1+i],shape.Solids[6+i]
    assert abs(esc.BoundBox.ZMax-fc.BoundBox.ZMin)<1e-6
    assert len(esc.fuse(fc).Solids)==1
    assert high-fc.BoundBox.ZMin>fc.BoundBox.ZMax-(high+t)
    assert abs(fc.BoundBox.ZMax-height)<1e-6
   assert shape.BoundBox.ZMax<=height-min(1.,height*.1)+3.2+1e-6
   checks.append(['meeting grommets; FC neck points down; nut seat',spacing,height])
 shape,_=stack_model(30.5,14.,3.2)
 radii=sorted({round(f.Surface.Radius,6) for f in shape.Solids[1].Faces if hasattr(f.Surface,'Radius')})
 (out/'grommet_dimensions.json').write_text(json.dumps(dict(dimensions=stack_dimensions(14.),height=14.,bore=radii[0],neck=radii[1],outer=radii[-1])))
 p=Parameters(FPVEnabled=True,StandoffHeight=35.,TopFrontShape='Camera U recess',TopFrontDepth=28.,TopFrontRecessWidth=14.,TopFrontSetback=0.)
 simple=g.build_for_update(p);mass=mass_properties(p,simple)
 for role,flag in (('VTXEnvelope','DetailedVTXReference'),('BatteryEnvelope','DetailedBatteryReference')):
  q=replace(p,**{flag:True});parts=g.build_for_update(q);assert set(g.build_report(q)['rebuilt'])<={role}
  shape,cs=detailed_reference(q,role);assert shape.isValid() and len(shape.Faces)==len(cs)
  assert len(shape.Solids)>1 and mass_properties(q,parts)==mass
  body=Part.makeCompound(shape.Solids[:-3]) if role=='BatteryEnvelope' else shape
  a,b=body.BoundBox,simple[role].BoundBox
  for name in ('XMin','YMin','ZMin'):assert getattr(a,name)>=getattr(b,name)-1e-5,(role,name)
  for name in ('XMax','YMax','ZMax'):assert getattr(a,name)<=getattr(b,name)+1e-5,(role,name)
  checks.append([role,'detailed model, original envelope bounds and unchanged frame/mass'])
 for mount in ('Top plate','Bottom plate'):
  q=replace(p,DetailedBatteryReference=True,BatteryMount=mount,BatteryRotation=28.,BatteryX=3.,BatteryY=-4.)
  shape,cs=detailed_reference(q,'BatteryEnvelope');assert shape.isValid();checks.append(['LiPo pose',mount])
 for design in ('2 plates','3 plates'):
  base=replace(p,PlateDesign=design,FlexSideGuards=True,FlexGuardStyle='Solid')
  before=g.build_for_update(base)
  for count in ('1 strap','2 straps'):
   for edge in ('Top edge','Bottom edge'):
    q=replace(base,FlexGuardStraps=True,FlexGuardStrapCount=count,FlexGuardStrapEdge=edge,FlexGuardStrapAuto=(edge=='Top edge'),FlexGuardStrapY1=10.,FlexGuardStrapY2=-18.,FlexGuardStrapWidth=16.)
    parts=g.build_for_update(q)
    assert set(g.build_report(q)['rebuilt'])<={'ElectronicsGuardLeft','ElectronicsGuardRight','FrameCGMarker'}
    for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
     s=parts[role];assert s.isValid() and len(s.Solids)==1 and s.Volume<before[role].Volume
     mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.08,AngularDeflection=.2,Relative=False)
     from freecad.rotorforge.mesh_cleanup import weld_micro_seams
     mesh=weld_micro_seams(mesh);assert mesh.isSolid(),(design,count,edge,role)
    checks.append(['connected guards and closed STL',design,count,edge])
 q=replace(p,DetailedVTXReference=True,DetailedBatteryReference=True,FlexSideGuards=True,FlexGuardStraps=True,FlexGuardStrapAuto=False,FlexGuardStrapY2=-21.)
 doc=App.newDocument();frame=d.create_frame(q,doc);file=out/'PowerStraps.FCStd';doc.saveAs(str(file));App.closeDocument(doc.Name)
 doc=App.openDocument(str(file));restored=d.read_parameters(doc.getObject('FrameParameters'));assert restored==q
 from freecad.rotorforge.exporters import export_package
 folder=export_package(doc.getObject('FrameParameters'),out/'export')
 assembly=Part.read(str(folder/'FrameAssembly.step'));parts=g.build_shapes(q)
 volume=sum(parts[r].Volume for r in g.physical_roles(q))
 assert abs(assembly.Volume-volume)<max(1e-4,volume*1e-6)
 App.closeDocument(doc.Name);checks.append('New detailed power references excluded from manufacturing STEP')
 checks.append('New settings and negative strap offset survive FCStd restoration')
 # Documentation meshes for the two new reference types.
 scenes=[]
 from freecad.rotorforge.fpv import vtx_holes
 for title,role in (('VTX reference','VTXEnvelope'),('LiPo reference','BatteryEnvelope')):
  shape,cols=detailed_reference(q,role);triangles=[]
  for face,colour in zip(shape.Faces,cols):
   vertices,faces=face.tessellate(.15)
   triangles.extend(dict(points=[[vertices[i].x,vertices[i].y,vertices[i].z] for i in f],colour=colour) for f in faces)
  scenes.append(dict(title=title,triangles=triangles))
 (out/'power_meshes.json').write_text(json.dumps(scenes))
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'power_straps.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print(len(checks),fail,flush=True)
