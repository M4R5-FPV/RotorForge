"""Exact solids, VTX fit, persistent updates and manufacturing exports."""
import sys,os,json,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.path.insert(0,str(root/'tests'))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
import FreeCAD as App,Part,MeshPart
from dataclasses import replace
from freecad.rotorforge import geometry as geo,document as doc
from freecad.rotorforge.parameters import Parameters,plate_levels
from freecad.rotorforge.protection_layout import guard_layout,guard_vtx_window
from freecad.rotorforge.mesh_cleanup import weld_micro_seams
from test_guard_options089 import vtx_frame
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
checks=[]
def passed(name):
 checks.append(name);(out/'checks.json').write_text(json.dumps(checks,indent=2));print('PASS',name,flush=True)
def guard_checks(p,shapes):
 for g in guard_layout(p):
  s=shapes[g['role']]
  assert s.isValid() and len(s.Solids)==1 and s.Volume>0,g['role']
  if p.FlexGuardFitMode=='Between plates':
   low=p.BottomThickness if p.FlexGuardCloseFront else g['z']
   assert s.BoundBox.ZMin>=low-1e-6,(g['role'],s.BoundBox,low)
   assert s.BoundBox.ZMax<=g['top']+1e-6,(g['role'],s.BoundBox,g['top'])
  for r in geo.carbon_roles(p):assert s.common(shapes[r]).Volume<1e-6,(g['role'],r)

base=Parameters(FlexSideGuards=True,FlexGuardFitMode='Between plates',FlexGuardWireEnabled=True,FlexGuardStyle='Solid')
cases=[('2 plates below arms',replace(base,PlateDesign='2 plates')),
       ('2 plates above arms and clamp',replace(base,PlateDesign='2 plates',TwoPlateArmPosition='Above bottom plate',ArmBracesEnabled=True)),
       ('3 plates and outline straps',replace(base,StrapOpeningStyle='Outline cutouts')),
       ('Vents, USB and guard strap',replace(base,FlexGuardStyle='Vented',FlexGuardExtendFront=True,
           FlexGuardUSBEnabled=True,FlexGuardUSBZ=23.,FlexGuardUSBHeight=6.,FlexGuardStraps=True,FlexGuardStrapCount='1 strap')),
       ('Stepped mid front',replace(base,MidReachMode='Custom',MidFrontReach=24.,FlexGuardWireFrontY=32.,FlexGuardWireHeight=3.)),
       ('Camera closure',replace(base,FPVEnabled=True,StandoffHeight=35.,FlexGuardCloseFront=True)),
       ('Zero plate clearance',replace(base,FlexGuardClearance=0.))]
for name,p in cases:
 shapes=geo.build_for_update(p);guard_checks(p,shapes)
 # At the centre of the joined span no divider remains below the roof.
 levels=plate_levels(p);probe=Part.makeBox(200,30,p.FlexGuardWireHeight-1,App.Vector(-100,-18,levels['deck_z']+.2))
 for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
  assert shapes[role].common(probe).Volume<1e-6,(name,role,'wire divider')
 passed(name)
for design in ('2 plates','3 plates'):
 for mode in ('Plate-edge wrap','Between plates'):
  p=vtx_frame(PlateDesign=design,FlexGuardFitMode=mode,FlexGuardStyle='Solid',FlexGuardWireEnabled=True)
  shapes=geo.build_for_update(p);guard_checks(p,shapes)
  envelope=geo._vtx_probe(p)
  for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
   assert shapes[role].common(envelope).Volume<1e-6,(design,mode,'VTX blocked')
  closed=geo.build_for_update(replace(p,VTXWidth=36.,FlexGuardVTXOpening=False))
  assert closed['ElectronicsGuardLeft'].common(envelope).Volume>1.,'test VTX does not reach wall'
  passed('Wide VTX clears '+design+' / '+mode)

# Update a saved frame between modes, preserve settings and reuse unchanged carbon.
p=vtx_frame(FlexGuardFitMode='Between plates',FlexGuardStyle='Solid',FlexGuardWireEnabled=True)
f=doc.create_frame(p,App.newDocument('GuardOptions089'))
for mode in ('Plate-edge wrap','Between plates'):
 p=replace(p,FlexGuardFitMode=mode);doc.update_frame(f,p)
 assert doc.read_parameters(f)==p
 guard_checks(p,{r:o.Shape for r,o in doc.component_objects(f).items()})
path=out/'GuardOptions089.FCStd';f.Document.saveAs(str(path));App.closeDocument(f.Document.Name)
geo.clear_build_caches();opened=App.openDocument(str(path));f=opened.getObject('FrameParameters')
assert doc.read_parameters(f)==p;doc.update_frame(f,p)
passed('Save, reopen and switch fit modes preserves settings and exact geometry')
from freecad.rotorforge.exporters import export_package
folder=export_package(f,out/'export');shapes=geo.build_shapes(p)
assembly=Part.read(str(folder/'FrameAssembly.step'))
assert abs(assembly.Volume-sum(shapes[r].Volume for r in geo.physical_roles(p)))<1e-3
for r in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
 exported=Part.read(str(folder/'FlexibleParts'/(r+'_assembled.step')))
 assert exported.common(geo._vtx_probe(p)).Volume<1e-6
 assert abs(exported.Volume-shapes[r].Volume)<1e-5
 mesh=weld_micro_seams(MeshPart.meshFromShape(Shape=shapes[r],LinearDeflection=.08,AngularDeflection=.2,Relative=False))
 assert mesh.isSolid(),r
App.closeDocument(opened.Name)
passed('Assembly STEP, guard STEP/STL and CNC exports retain clearances')
