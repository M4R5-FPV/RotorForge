"""Native shoe profiles, fit, printable mesh, exports and incremental reuse."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,MeshPart
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.front_bumper import BUMPER_SHAPES
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.exporters import export_package
from freecad.rotorforge.flex_geometry import printable_flex
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];fail=[]
try:
 for shape in BUMPER_SHAPES:
  p=Parameters(FlexFrontBumper=True,FlexBumperShape=shape)
  parts=g.build_shapes(p);shoe=parts['FrontBumper']
  assert shoe.isValid() and len(shoe.Solids)==1 and shoe.Volume>0
  assert shoe.common(parts['BottomPlate']).Volume<1e-6
  assert shoe.BoundBox.ZMin<0 and shoe.BoundBox.ZMax>p.BottomThickness
  mesh=MeshPart.meshFromShape(Shape=printable_flex(shoe,'FrontBumper'),LinearDeflection=.08,AngularDeflection=.2,Relative=False)
  assert mesh.isSolid(),shape
  checks.append(shape+' valid shoe, carbon clearance and closed print mesh')
 for nose in ('Rounded nose','V-notch','Twin lobes'):
  p=Parameters(FlexFrontBumper=True,FlexBumperShape='Follow bottom plate',BottomNoseShape=nose)
  parts=g.build_shapes(p);assert parts['FrontBumper'].isValid();checks.append('Finished '+nose+' followed by shoe')
 p=Parameters(FlexFrontBumper=True,FlexBumperReach=45.)
 parts=g.build_shapes(p)
 from freecad.rotorforge.parameters import standoff_holes
 import Part
 for x,y in standoff_holes(p):
  if y>0:
   tool=Part.makeCylinder(3.,20.,App.Vector(x,y,-10.));assert tool.common(parts['FrontBumper']).Volume<1e-7
 from freecad.rotorforge.mass_properties import mass_properties
 metrics=mass_properties(p,parts);assert metrics['flexible_mass_g']>0
 checks.append('Long shoe retains front bolt-head access and contributes to mass/CG')
 for position in ('Above bottom plate','Below bottom plate'):
  p=Parameters(PlateDesign='2 plates',TwoPlateArmPosition=position,ArmBracesEnabled=(position=='Above bottom plate'),FlexFrontBumper=True,FPVEnabled=True,StandoffHeight=35.,TopFrontShape='Camera U recess',TopFrontRecessWidth=14.,TopFrontDepth=28.,TopFrontSetback=0.)
  parts=g.build_shapes(p);assert parts['FrontBumper'].isValid();checks.append('Two plates '+position+' with camera tabs')
 p=Parameters(FlexFrontBumper=True,FPVEnabled=True,StandoffHeight=35.,FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardCloseFront=True,FlexGuardClearance=0.,TopFrontShape='Camera U recess',TopFrontRecessWidth=14.,TopFrontDepth=28.,TopFrontSetback=0.)
 parts=g.build_shapes(p);assert parts['FrontBumper'].isValid();checks.append('Three plates with closed front side guards')
 g.build_for_update(p);q=replace(p,FlexBumperProjection=6.);g.build_for_update(q);report=g.build_report(q)
 assert set(report['rebuilt'])<={'FrontBumper','FrameCGMarker'},report
 checks.append('Toe edit reuses carbon and existing TPU: '+repr(report['rebuilt']))
 doc=App.newDocument();f=d.create_frame(p,doc);folder=export_package(f,out/'export')
 assert (folder/'FlexibleParts/FrontBumper.stl').exists();assert (folder/'FlexibleParts/FrontBumper_assembled.step').exists()
 doc.saveAs(str(out/'FrontBumper.FCStd'));App.closeDocument(doc.Name)
 checks.append('Separate print STL, assembly/print STEP and saved frame')
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'front_bumper.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print(len(checks),fail,flush=True)
