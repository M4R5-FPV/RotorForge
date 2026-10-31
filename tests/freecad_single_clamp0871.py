"""Only one clamp, correct carrier/fasteners, exact exports and update persistence."""
import sys,os,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from dataclasses import replace
from freecad.rotorforge.parameters import *
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.hardware_layout import hardware_layout
from freecad.rotorforge.nut_seats import joint_seat
from freecad.rotorforge.part_preview import preview_roles
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[]
for position in TWO_PLATE_ARM_POSITIONS:
 for key in (False,True):
  for shared in (False,True):
   p=Parameters(PlateDesign='2 plates',TwoPlateArmPosition=position,ArmBracesEnabled=True,KeystoneEnabled=key,
    StandoffFrontMount='Arm inner hole' if shared else 'Custom position',StrapSlotsEnabled=not shared)
   shapes=g.build_for_update(p);lower=position=='Below bottom plate';role='ArmLowerClampPlate' if lower else 'ArmClampPlate';other='ArmClampPlate' if lower else 'ArmLowerClampPlate'
   assert shapes[other].isNull() and len(shapes[role].Solids)==1 and shapes[role].isValid()
   assert role in g.carbon_roles(p) and other not in g.carbon_roles(p)
   assert role in preview_roles(p) and other not in preview_roles(p)
   if lower:
    assert abs(shapes[role].BoundBox.ZMax+p.ArmThickness)<1e-6
    assert stack_mounting_role(p)=='BottomPlate' and stack_reference_z(p)==p.BottomThickness
    assert all(s['mount']=='Bottom plate' for s in standoff_layouts(p))
   else:
    assert abs(shapes[role].BoundBox.ZMin-p.BottomThickness-p.ArmThickness)<1e-6
   for arm in arm_layouts(p):
    assert shapes[role].distToShape(shapes['Arm'+arm['name']])[0]<1e-6
   assert shapes[role].common(shapes['BottomPlate']).Volume<1e-6
   specs=hardware_layout(p);arm_specs=[s for s in specs if s['group']=='Arm bolts'];stack_specs=[s for s in specs if s['group']=='Stack hardware']
   if lower:
    assert all(abs(s['point'][2]+p.ArmThickness+p.UndersideClampThickness)<1e-6 for s in arm_specs)
    assert all(s['seat']['role']=='BottomPlate' and s['seat']['z']==p.BottomThickness for s in arm_specs)
    assert all(s['owner']=='BottomPlate' and s['point'][2]==0 for s in stack_specs)
   for s in standoff_layouts(p):
    if lower and s['shared_arm']:assert s['grip_length']==p.BottomThickness+p.ArmThickness+p.UndersideClampThickness
   checks.append([position,key,shared,'one clamp, contact, carrier and fasteners'])
# Nut seats receive on the upper face of bottom plate in the lower-clamp case.
for mode in ('Recessed hex nut','M3 press nut'):
 p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,ArmNutMount=mode,StackPressNuts=True,StandoffHeight=35.)
 shapes=g.build_for_update(p);assert shapes['ArmClampPlate'].isNull()
 for a in arm_layouts(p):
  for pt in a['bolts']:assert joint_seat(p,'Arm bolts',pt)['role']=='BottomPlate'
 checks.append([mode,'bottom receiving plate, lower clamp clear'])
# Above/below toggles clear stale shape and update serialized document.
p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,TwoPlateArmPosition='Above bottom plate')
doc=App.newDocument('SingleClamp0871');frame=d.create_frame(p,doc)
for pos in ('Below bottom plate','Above bottom plate','Below bottom plate'):
 p=replace(p,TwoPlateArmPosition=pos);d.update_frame(frame,p);objs=d.component_objects(frame)
 assert objs['ArmClampPlate' if pos=='Below bottom plate' else 'ArmLowerClampPlate'].Shape.isNull()
file=out/'SingleClamp0871.FCStd';doc.saveAs(str(file));App.closeDocument(doc.Name)
doc=App.openDocument(str(file));frame=doc.getObject('FrameParameters');assert d.read_parameters(frame)==p
from freecad.rotorforge.exporters import export_package
folder=export_package(frame,out/'export');assembly=Part.read(str(folder/'FrameAssembly.step'));shapes=g.build_shapes(p)
assert abs(assembly.Volume-sum(shapes[r].Volume for r in g.physical_roles(p)))<1e-3
assert 'ArmClampPlate' not in (folder/'PartsList.csv').read_text()
assert 'ArmLowerClampPlate' in (folder/'PartsList.csv').read_text()
assert 'ArmClampPlate' not in (folder/'CarbonParts.svg').read_text() if (folder/'CarbonParts.svg').exists() else True
App.closeDocument(doc.Name);checks.append('toggle, save/reopen, STEP and parts list contain only lower clamp')
# Disabling clamp and three-plate builds stay clamp-free.
for p in (Parameters(PlateDesign='2 plates'),Parameters(ArmBracesEnabled=True,KeystoneEnabled=True)):
 shapes=g.build_shapes(p);assert shapes['ArmClampPlate'].isNull() and shapes['ArmLowerClampPlate'].isNull()
checks.append('no clamp when disabled or three-plate')
(out/'checks.json').write_text(json.dumps(checks,indent=2));print('PASS',len(checks),flush=True)
