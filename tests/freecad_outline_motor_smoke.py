"""Validate additional motor profiles and intentional plate outline cuts."""
from pathlib import Path
from dataclasses import replace
import json,os,sys,traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from freecad.rotorforge.parameters import Parameters,LAYOUTS,arm_layouts,plate_levels
from freecad.rotorforge.geometry import build_shapes,carbon_roles,cylinder,motor_pad
from freecad.rotorforge.airflow_geometry import apply_cutouts,profile_tool
from freecad.rotorforge.cutouts import PATTERN_DEFAULTS,CUTOUT_TYPES,encode_patterns,pattern_instances
from freecad.rotorforge.motor_pads import MOTOR_PAD_SHAPES
from freecad.rotorforge.document import create_frame,read_parameters,update_frame,component_objects
from freecad.rotorforge.exporters import export_package,profile_entities,write_svg
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[]}
def check(ok,label):
 if not ok:raise AssertionError(label)
 report['checks'].append(label)
def pattern(**kw):return dict(PATTERN_DEFAULTS,**kw)
def rejected(items,label,plate):
 try:apply_cutouts(Parameters(CutoutPatterns=encode_patterns(items)),'TopPlate',plate)
 except ValueError:check(True,label)
 else:raise AssertionError(label)
try:
 for name in MOTOR_PAD_SHAPES[10:]:
  for layout in LAYOUTS:
   p=Parameters(MotorPadShape=name,Layout=layout,Wheelbase=270);shapes=build_shapes(p);z=plate_levels(p)['arm_z']
   for role in carbon_roles(p):check(shapes[role].isValid() and len(shapes[role].Solids)==1,name+'/'+layout+': connected '+role)
   for arm in arm_layouts(p):
    for point in arm['motor_holes']:
     ring=cylinder(*point,p.MotorHoleDiameter/2+p.MinimumWeb,z,p.ArmThickness).cut(cylinder(*point,p.MotorHoleDiameter/2,z-.1,p.ArmThickness+.2))
     check(abs(ring.common(shapes['Arm'+arm['name']]).Volume-ring.Volume)<1e-5,name+'/'+layout+': motor screw bearing')
   print('MOTOR '+name+'/'+layout,flush=True)
  p=Parameters(MotorPadShape=name,MotorPadDiameter=36,MotorSpacingX=19,MotorSpacingY=16)
  check(all(build_shapes(p)[r].isValid() for r in carbon_roles(p)),name+': rectangular pattern')
 blank=Part.makeBox(80,100,2,App.Vector(-40,-50,0))
 for name in CUTOUT_TYPES:
  for angle in (0,37):
   item=pattern(mode='Outline notch',shape=name,width=12,length=18,x=40,rotation=angle)
   p=Parameters(CutoutPatterns=encode_patterns([item]));actual=apply_cutouts(p,'TopPlate',blank)
   expected=blank.cut(profile_tool(item,0,2)).removeSplitter()
   check(actual.isValid() and len(actual.Solids)==1,name+': connected notch')
   check(actual.cut(expected).Volume+expected.cut(actual).Volume<1e-5,name+': exact edge subtraction')
   check(bool(profile_entities(actual)),name+': cutting profile')
 items=[pattern(mode='Outline notch',shape='Circle',width=14,x=40,y=-2),pattern(mode='Outline notch',shape='Diamond',width=14,length=18,x=40,y=3),pattern(shape='Slot',width=6,length=12,x=32)]
 p=Parameters(CutoutPatterns=encode_patterns(items));actual=apply_cutouts(p,'TopPlate',blank)
 tools=[profile_tool(i,0,2) for i in items];expected=blank.cut(tools[0].multiFuse(tools[1:])).removeSplitter()
 check(actual.cut(expected).Volume+expected.cut(actual).Volume<1e-5,'Mixed outline and interior union')
 reversed_result=apply_cutouts(replace(p,CutoutPatterns=encode_patterns(items[::-1])),'TopPlate',blank)
 check(actual.cut(reversed_result).Volume+reversed_result.cut(actual).Volume<1e-5,'Mixed union order independent')
 rejected([pattern(mode='Outline notch',shape='Circle',width=10)],'Interior-only outline rejected',blank)
 rejected([pattern(mode='Outline notch',shape='Circle',width=10,x=60)],'Outside-only outline rejected',blank)
 rejected([pattern(mode='Outline notch',shape='Rectangle',width=90,length=8)],'Disconnected plate rejected',blank)
 rejected([pattern(shape='Circle',width=12,x=40)],'Interior edge crossing still rejected',blank)
 with_hole=blank.cut(cylinder(34,0,2,-1,4))
 rejected([pattern(mode='Outline notch',shape='Circle',width=10,x=40)],'Existing hole clearance protected',with_hole)
 with_slot=blank.cut(Part.makeBox(3,12,4,App.Vector(34,-6,-1)))
 rejected([pattern(mode='Outline notch',shape='Rectangle',width=12,length=16,x=40)],'Existing socket clearance protected',with_slot)
 rejected([pattern(mode='Outline notch',shape='Circle',width=12,x=17,y=46)],'Standoff bearing protected',Part.makeBox(34,100,2,App.Vector(-17,-50,0)))
 nativeitems=[pattern(mode='Outline notch',shape='Circle',width=8,x=x,y=0) for x in (-Parameters().TopWidth/2,Parameters().TopWidth/2)]
 for design in ('2 plates','3 plates'):
  p=Parameters(PlateDesign=design,MotorPadShape='Swept shield',CutoutPatterns=encode_patterns(nativeitems))
  shapes=build_shapes(p);check(all(shapes[r].isValid() and len(shapes[r].Solids)==1 for r in carbon_roles(p)),design+': real frame cuts')
  settings=create_frame(p);doc=settings.Document;path=out/('Example_OutlineNotches_'+design[0]+'_plates.FCStd');doc.saveAs(str(path));App.closeDocument(doc.Name)
  doc=App.openDocument(str(path));settings=doc.getObject('FrameParameters');doc.recompute();doc.UndoMode=1
  check(read_parameters(settings)==p,design+': native settings restored')
  update_frame(settings,replace(p,CutoutPatterns='[]'));doc.undo();doc.recompute();check(read_parameters(settings)==p,design+': Undo restores notches')
  folder=export_package(settings,out/(design[0]+'_export'))
  check(Part.read(str(folder/'FrameAssembly.step')).isValid(),design+': STEP reimports')
  for ext in ('svg','dxf'):check((folder/'CuttingProfiles'/('TopPlate.'+ext)).stat().st_size>100,design+': '+ext+' exported')
  info=json.loads((folder/'ExportInfo.json').read_text());check('Outline notch' in json.dumps(info),design+': metadata retains mode')
  App.closeDocument(doc.Name)
 for p,roles in [(Parameters(), [('BottomPlate',25,55),('MidPlate',25,-40),('TopPlate',23,0)]),(Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True),[('ArmClampPlate',25,0),('ArmLowerClampPlate',25,0)])]:
  base=build_shapes(p)
  for role,x,y in roles:
   item=pattern(role=role,mode='Outline notch',shape='Circle',width=8,x=x,y=y)
   actual=build_shapes(replace(p,CutoutPatterns=encode_patterns([item])))[role]
   check(actual.isValid() and len(actual.Solids)==1 and actual.Volume<base[role].Volume,role+': actual plate outline cut')
 # Generate local motor pad CAD profiles for the illustrated help.
 for name in MOTOR_PAD_SHAPES[10:]:
  p=Parameters(MotorPadShape=name);arm=dict(motor=(0,0),unit=(1,0))
  pad=motor_pad(p,arm,0)
  write_svg(out/(name.replace(' ','_')+'.svg'),[('MotorPad',profile_entities(pad))],60,60)
 report['status']='passed'
except Exception:
 report['status']='failed';report['error']=traceback.format_exc();print(report['error'],flush=True)
finally:
 (out/'test_report.json').write_text(json.dumps(report,indent=2));print('RESULT '+report['status']+' '+str(len(report['checks'])),flush=True)
