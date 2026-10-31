"""Connected rotated shields, screw support, and native window-profile migration."""
import os,sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters,arm_layouts,plate_levels,validate
from freecad.rotorforge.geometry import arm_stem,motor_pad,fuse,blend_motor_junction,cut_holes,cylinder
from freecad.rotorforge.motor_pads import NEW_MOTOR_PAD_SHAPES
from freecad.rotorforge.document import create_frame,read_parameters,ensure_parameter_properties
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[]
try:
 for name in NEW_MOTOR_PAD_SHAPES:
  for pivot,layout in (('Motor centre','4-hole bolt circle'),('Pad beginning','3-hole bolt circle')):
   p=Parameters(MotorPadShape=name,MotorPadRotation=30,MotorPadRotationPivot=pivot,MotorHoleLayout=layout)
   assert not validate(p)[0],(name,pivot,validate(p)[0])
   a=arm_layouts(p)[0];z=plate_levels(p)['arm_z']
   blank=fuse([arm_stem(p,a,z,p.ArmThickness),motor_pad(p,a,z)])
   blank=blend_motor_junction(p,a,blank,z,p.ArmThickness)
   holes=[(pt,p.MotorHoleDiameter/2) for pt in a['motor_holes']]+[(a['motor'],p.MotorCenterDiameter/2)]
   shape=cut_holes(blank,holes,z,p.ArmThickness)
   assert shape.isValid() and len(shape.Solids)==1,(name,pivot)
   for (x,y),r in holes:
    ring=cylinder(x,y,r+p.MinimumWeb,z,p.ArmThickness).cut(cylinder(x,y,r,z-1,p.ArmThickness+2))
    assert abs(ring.common(shape).Volume-ring.Volume)<1e-5,(name,pivot,'screw support')
   checks.append(name+' / '+pivot+' / '+layout)
 d=App.newDocument('RetiredBeam');o=create_frame(Parameters(),d)
 o.ArmBeamShape=['Straight','Slot beam','Twin window beam','Bridge beam'];o.ArmBeamShape='Bridge beam'
 o.addProperty('App::PropertyLength','ArmWindowWidth');o.ArmWindowWidth=8
 p=read_parameters(o);assert p.ArmBeamShape=='Broad shoulder'
 ensure_parameter_properties(o,p)
 assert 'ArmWindowWidth' not in o.PropertiesList
 assert 'Bridge beam' not in o.getEnumerationsOfProperty('ArmBeamShape')
 assert read_parameters(o).ArmBeamShape=='Broad shoulder';App.closeDocument(d.Name)
 checks.append('Native old window enumeration migrates and retired property is removed')
 report=dict(status='passed',checks=checks)
except Exception:report=dict(status='failed',checks=checks,error=traceback.format_exc());traceback.print_exc()
(out/'report.json').write_text(json.dumps(report,indent=2));print(report['status'],len(checks),flush=True)
