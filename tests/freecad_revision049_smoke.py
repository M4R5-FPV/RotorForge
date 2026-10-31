"""Native coverage of revised platforms, arm sections, grooves and direct VTX."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.geometry import build_shapes,carbon_roles
from freecad.rotorforge.motor_pads import NEW_MOTOR_PAD_SHAPES
from freecad.rotorforge.design_options import ARM_BEAM_SHAPES,MOTOR_PAD_RELIEFS
from freecad.rotorforge.battery import GRIP_PATTERNS
from freecad.rotorforge.fpv import vtx_deck_z
from freecad.rotorforge.document import create_frame
from freecad.rotorforge.exporters import export_package
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[]
def build(p,label):
 e,_=validate(p);assert not e,(label,e)
 shapes=build_shapes(p)
 assert all(shapes[k].isValid() and len(shapes[k].Solids)==1 for k in carbon_roles(p)),label
 checks.append(label);print('PASS',label,flush=True)
 return shapes
try:
 if not os.environ.get('ROTORFORGE_GRIPS_ONLY'):
  for shape in NEW_MOTOR_PAD_SHAPES:
   for relief in MOTOR_PAD_RELIEFS:build(Parameters(MotorPadShape=shape,MotorPadRelief=relief),shape+' / '+relief)
  for shape in ARM_BEAM_SHAPES:build(Parameters(ArmBeamShape=shape),'Arm '+shape)
 if not os.environ.get('ROTORFORGE_SKIP_GRIPS'):
  for name in GRIP_PATTERNS[int(os.environ.get('ROTORFORGE_GRIP_START','15')):]:
   for mount in ('Top plate','Bottom plate'):
    p=Parameters(LiPoPadEnabled=True,LiPoPadPattern=name,BatteryMount=mount)
    s=build(p,'Grip '+name+' / '+mount);assert len(s['LiPoPad'].Solids)==1 and s['LiPoPad'].isValid()
 if not os.environ.get('ROTORFORGE_GRIPS_ONLY'):
  for mode in ('2 plates','3 plates'):
   p=Parameters(FPVEnabled=True,PlateDesign=mode,StandoffHeight=35);s=build(p,'Direct VTX '+mode)
   assert abs(s['VTXEnvelope'].BoundBox.ZMin-vtx_deck_z(p))<1e-6
  p=Parameters(FPVEnabled=True,StandoffHeight=35,MotorPadShape='Round-shoulder shield',MotorPadRelief='Neck slot',MotorPadRotation=25,ArmBeamShape='Broad shoulder',LiPoPadEnabled=True,LiPoPadPattern='Plus grid')
  build(p,'Combined export');d=App.newDocument('Revision049');root=create_frame(p,d);export_package(root,str(out/'export'));d.saveAs(str(out/'Revision049.FCStd'));App.closeDocument(d.Name)
 report=dict(status='passed',checks=checks)
except Exception:report=dict(status='failed',checks=checks,error=traceback.format_exc());traceback.print_exc()
(out/'report.json').write_text(json.dumps(report,indent=2))
