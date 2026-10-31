"""Native optional visuals, preserved probes/physical parts, and export boundaries."""
import sys,os,json,traceback,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.detailed_references import detailed_reference,motor_model,prop_model,stack_model,camera_model
from freecad.rotorforge.reference_options import shaft_top
from freecad.rotorforge.mass_properties import mass_properties
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True);checks=[];fail=[]
try:
 p=Parameters(FPVEnabled=True,StandoffHeight=35.,TopFrontShape='Camera U recess',TopFrontDepth=28.,TopFrontRecessWidth=14.,TopFrontSetback=0.)
 old=g.build_for_update(p);oldmass=mass_properties(p,old)
 flags={'MotorEnvelopes':'DetailedMotorReferences','PropellerDiscs':'DetailedPropReferences','StackEnvelope':'DetailedStackReference','CameraEnvelope':'DetailedCameraReference'}
 for role,flag in flags.items():
  q=replace(p,**{flag:True});parts=g.build_for_update(q);report=g.build_report(q)
  assert set(report['rebuilt'])<={role},report
  assert parts[role].isValid() and parts[role].Volume>0 and len(parts[role].Faces)>len(old[role].Faces),role
  shape,colours=detailed_reference(q,role);assert len(colours)==len(shape.Faces),role
  for part in g.CARBON_ROLES:assert parts[part].exportBrepToString()==old[part].exportBrepToString(),part
  assert mass_properties(q,parts)==oldmass
  checks.append([role,'independent visual rebuild, valid detail, unchanged carbon and mass'])
 q=replace(p,**{flag:True for flag in flags.values()});parts=g.build_for_update(q)
 g.build_for_update(replace(q,ShowReferences=False));report=g.build_report(replace(q,ShowReferences=False))
 assert not any(r in g.CARBON_ROLES for r in report['rebuilt']);checks.append(['master reference visibility remains independent of carbon'])
 for diam,height in ((12.,7.),(28.,16.),(40.,22.)):
  s,c=motor_model(diam,height);assert s.isValid();assert s.BoundBox.ZMax<=shaft_top(height)+1e-6;checks.append(['motor size',diam,height])
 for diam in (40.,127.,254.):
  s,c=prop_model(diam);assert s.isValid()
  vs,_=s.tessellate(.1);radius=max(math.hypot(v.x,v.y) for v in vs)
  assert radius<=diam/2+1e-3,(diam,radius);checks.append(['curved three-blade prop within disc',diam])
 for spacing in (20.,30.5):
  for height in (3.,14.,24.):
   s,c=stack_model(spacing,height,3.2);assert s.isValid();assert s.BoundBox.ZMin>=-1e-6 and s.BoundBox.ZMax<=height-min(1.,height*.1)+3.2+1e-6
   checks.append(['two PCB / grommet envelope',spacing,height])
 doc=App.newDocument();frame=d.create_frame(q,doc);file=out/'DetailedReferences.FCStd';doc.saveAs(str(file));App.closeDocument(doc.Name)
 doc=App.openDocument(str(file));restored=d.read_parameters(doc.getObject('FrameParameters'));assert all(getattr(restored,k) for k in flags.values());App.closeDocument(doc.Name)
 checks.append(['detailed switches survive saved-project restoration'])
 from freecad.rotorforge.exporters import export_package
 doc=App.newDocument();frame=d.create_frame(q,doc);folder=export_package(frame,out/'export')
 assembly=Part.read(str(folder/'FrameAssembly.step'))
 physical=sum(parts[role].Volume for role in g.physical_roles(q))
 assert abs(assembly.Volume-physical)<max(1e-4,physical*1e-6),(assembly.Volume,physical)
 App.closeDocument(doc.Name);checks.append(['manufacturing STEP excludes all presentation references'])
 # Exact native face tessellation for documentation, without a graphics driver.
 scenes=[]
 m,mc=motor_model(28.,16.);hub=prop_model(127.)[0].Solids[0].copy();hub.translate(App.Vector(0,0,16.))
 assembly_model=(Part.makeCompound([m.copy(),hub]),mc+tuple((.18,.57,.62) for f in hub.Faces))
 for title,model in (('Motor, hub and M5 locknut',assembly_model),('Three-blade propeller',prop_model(127.)),('FC / ESC stack',stack_model(30.5,14.,3.2)),('FPV camera',camera_model(19.,19.,19.,6.5,2.2))):
  shape,colours=model;triangles=[]
  for face,colour in zip(shape.Faces,colours):
   vertices,faces=face.tessellate(.15)
   triangles.extend({'points':[[vertices[i].x,vertices[i].y,vertices[i].z] for i in f],'colour':colour} for f in faces)
  scenes.append(dict(title=title,triangles=triangles))
 (out/'reference_meshes.json').write_text(json.dumps(scenes))
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'presentation.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print(len(checks),fail,flush=True)
