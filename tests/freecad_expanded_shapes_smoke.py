"""Native coverage for standard stacks and the additional planar outline families."""
import sys,json,os,traceback
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,validate,arm_layouts
from freecad.rotorforge.geometry import build_shapes,carbon_roles,overlap_volume
from freecad.rotorforge.motor_pads import NEW_MOTOR_PAD_SHAPES
from freecad.rotorforge.design_options import PLATE_SHAPES,ARM_BEAM_SHAPES,MOTOR_PAD_RELIEFS
from freecad.rotorforge.cutouts import CUTOUT_TYPES,encode_patterns
from freecad.rotorforge.document import create_frame,read_parameters,update_frame
from freecad.rotorforge.exporters import export_package
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
checks=[]
def check(p,label):
 errors,_=validate(p)
 assert not errors,(label,errors)
 shapes=build_shapes(p)
 assert all(shapes[k].isValid() and len(shapes[k].Solids)==1 for k in carbon_roles(p)),label
 checks.append(label);print('PASS',label,flush=True)
 return shapes
try:
 for size in (() if os.environ.get("ROTORFORGE_SKIP_INITIAL") else (20.,30.5)):
  p=Parameters(StackSpacing=size,StackMountHeight=3)
  check(p,'Stack '+str(size))
  d=App.newDocument('StackTest');root=create_frame(p,d)
  print('ROOT',root,flush=True)
  assert read_parameters(root).StackSpacing==size
  assert root.getTypeIdOfProperty('StackSpacing')=='App::PropertyEnumeration'
  App.closeDocument(d.Name)
 for name in (() if os.environ.get("ROTORFORGE_SKIP_INITIAL") else NEW_MOTOR_PAD_SHAPES):
  for relief in MOTOR_PAD_RELIEFS:
   check(Parameters(MotorPadShape=name,MotorPadRelief=relief),name+' / '+relief)
 for name in (() if os.environ.get("ROTORFORGE_SKIP_INITIAL") else ARM_BEAM_SHAPES):
  check(Parameters(ArmBeamShape=name),'Beam '+name)
 for name in PLATE_SHAPES:
  check(Parameters(BottomPlateShape=name,MidPlateShape=name,TopPlateShape=name,ClampPlateShape=name),'Plates '+name)
 for pivot in ('Motor centre','Pad beginning'):
  for rotation in (-30.,30.,65.):
   check(Parameters(MotorPadShape='Rounded visor',MotorPadRotationPivot=pivot,MotorPadRotation=rotation),f'Blended {pivot} {rotation}')
 for name in CUTOUT_TYPES[12:]:
  p=Parameters(CutoutPatterns=encode_patterns([dict(role='TopPlate',shape=name,width=8,length=12,x=0,y=0)]))
  check(p,'Cut '+name)
 p=Parameters(MotorPadShape='Wide paddle',ArmBeamShape='Barrel beam',MotorPadRotation=25,TopPlateShape='Octagonal')
 check(p,'Combined design')
 d=App.newDocument('ExportExpanded');root=create_frame(p,d)
 export_package(root,str(out/'export'))
 d.saveAs(str(out/'Expanded.FCStd'));App.closeDocument(d.Name)
 (out/'report.json').write_text(json.dumps(dict(status='passed',checks=checks),indent=2))
except Exception:
 (out/'report.json').write_text(json.dumps(dict(status='failed',checks=checks,error=traceback.format_exc()),indent=2));traceback.print_exc()
