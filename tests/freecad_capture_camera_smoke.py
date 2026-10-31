"""Exact CAD checks for underside capture, screw access and sloping cameras."""
from pathlib import Path
from dataclasses import replace
import os,sys,json,math,csv,traceback,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from freecad.rotorforge.parameters import *
from tests.frame_cases import FRAME_CASES, FPV_CASES
from freecad.rotorforge.fpv import *
from freecad.rotorforge.geometry import build_shapes,carbon_roles,physical_roles,cylinder,arc_slot,flat_plate_shape
from freecad.rotorforge.document import create_frame,update_frame,read_parameters,component_objects
from freecad.rotorforge.exporters import export_package,profile_entities
from rotorforge import __version__
output=Path(os.environ.get('ROTORFORGE_TEST_OUTPUT',tempfile.mkdtemp(prefix='rotorforge-capture-')));output.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[],'export_folders':[],'freecad_version':'.'.join(App.Version()[:3])}
def check(v,message):
 if not v:raise AssertionError(message)
 report['checks'].append(message)
def circle(shape,point,r):
 return any(e[0]=='CIRCLE' and math.dist((e[1],e[2]),point)<1e-7 and abs(e[3]-r)<1e-7 for e in profile_entities(shape))
def valid(p,s,tag):
 for role in carbon_roles(p):check(s[role].isValid() and len(s[role].Solids)==1,tag+': connected '+role)
def access(p,s,tag):
 carrier=stack_mounting_role(p);z=s[carrier].BoundBox.ZMin;low=min(s[r].BoundBox.ZMin for r in carbon_roles(p))
 for point in stack_holes(p):
  probe=cylinder(*point,p.StackAccessDiameter/2,low-.1,z-low+.1)
  for role in carbon_roles(p):
   if role!=carrier:check(probe.common(s[role]).Volume<1e-6,tag+': full service diameter through '+role)
  check(circle(s[carrier],point,p.StackHoleDiameter/2),tag+': carrier keeps normal screw bore')
try:
 for name,base in FRAME_CASES.items():
  for pos in TWO_PLATE_ARM_POSITIONS:
   for wide in (False,True):
    p=replace(base,PlateDesign='2 plates',TwoPlateArmPosition=pos,ArmBracesEnabled=True,KeystoneEnabled=True,StandoffHeight=35)
    if wide:p=replace(p,BottomCentreWidth=70,ClampCentreWidth=70,TopCentreWidth=70)
    tag=name+'/'+pos+'/'+str(wide);s=build_shapes(p);valid(p,s,tag);access(p,s,tag)
    check(s['ArmKeystone'].distToShape(s['BottomPlate'])[0]<1e-7,tag+': bottom contacts key')
    if underside_clamp_active(p):
     lower=s['ArmLowerClampPlate'];check(abs(lower.BoundBox.ZMax+p.ArmThickness)<1e-7,tag+': lower plate touches arm underside')
     check(abs(lower.BoundBox.ZLength-p.UndersideClampThickness)<1e-7,tag+': lower thickness')
     for role in ['ArmKeystone']+['Arm'+a['name'] for a in arm_layouts(p)]:
      shifted=s[role].copy();shifted.translate(App.Vector(0,0,-.01))
      check(shifted.common(lower).Volume>1,tag+': lower clamp captures '+role)
      check(s[role].common(lower).Volume<1e-6,tag+': no overlap '+role)
     for point in stack_holes(p):check(circle(lower,point,3),tag+': lower 6 mm service hole')
    else:check(s['ArmLowerClampPlate'].isNull(),tag+': extra plate absent above bottom')
 crossing=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,ArmRootY=24,StandoffHeight=35)
 s=build_shapes(crossing);valid(crossing,s,'crossing roots');access(crossing,s,'crossing roots')
 check(bool(validate(replace(crossing,ArmRootReliefsEnabled=False))[0]),'Blocked access rejected when root reliefs disabled')
 for count in STANDOFF_COUNTS[1:]:
  p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,StandoffCount=count,StandoffHeight=35)
  s=build_shapes(p);valid(p,s,count);access(p,s,count)
  for stand in standoff_layouts(p):
   if stand['mount']=='Arm clamp plate' and not stand['shared_arm']:check(circle(s['ArmLowerClampPlate'],stand['point'],3),count+': lower access to custom standoff screw')
 camera_cases=[]
 for mode in PLATE_DESIGNS:
  for mechanism in CAMERA_TILT_MECHANISMS+('Fixed',):
   p=Parameters(PlateDesign=mode,FPVEnabled=True,StandoffHeight=35,CameraSideBoltSpacing=8,TopReachMode='Custom',TopFrontReach=60,TopRearReach=100)
   p=replace(p,CameraMountMode='Fixed') if mechanism=='Fixed' else replace(p,CameraTiltMechanism=mechanism)
   camera_cases.append(p);tag=mode+'/'+mechanism;s=build_shapes(p);valid(p,s,tag)
   check(abs(s['TopPlate'].BoundBox.YMax-60)<1e-7,tag+': top reach stays exact')
   mount=camera_mounts(p)[0];check(mount['top_centre_y']<mount['bottom_centre_y'],tag+': angled walls')
   check(abs(camera_position_y(p)-(mount['top_centre_y']+mount['bottom_centre_y'])/2)<1e-7,tag+': centred pattern')
   for m in camera_mounts(p):
    xmin,xmax=m['plate_x'];t=xmax-xmin;shape=s[m['role']]
    for key,plate,z,th in [('tabs_y','BottomPlate',0,p.BottomThickness),('top_tabs_y','TopPlate',m['z1'],p.TopThickness)]:
     for y in m[key]:
      tongue=Part.makeBox(t,p.CameraTabLength,th,App.Vector(xmin,y-p.CameraTabLength/2,z))
      check(abs(tongue.common(shape).Volume-tongue.Volume)<1e-6,tag+': tongue retained '+key)
      check(tongue.common(s[plate]).Volume<1e-6,tag+': correct slot '+plate)
      for x in (xmin-p.CameraTabClearance-.15,xmax+p.CameraTabClearance+.15):check(s[plate].isInside(App.Vector(x,y,z+th/2),1e-7,True),tag+': material supports tab')
    for arc in m['side_arcs']:
     tool=arc_slot(arc,xmin-.1,t+.2);expected=math.pi*2*arc['radius']*arc['width']*(arc['end']-arc['start'])/360+math.pi*(arc['width']/2)**2
     check(abs(tool.Volume/(t+.2)-expected)<1e-6,tag+': exact circular slot area')
    for angle in (p.CameraTiltMin,p.CameraTilt,p.CameraTiltMax):
     cy,cz=camera_body_centre(p,angle);a=math.radians(angle)
     if p.CameraMountMode=='Variable' or angle==p.CameraTilt:
      for sign in (-1,1):
       probe=Part.makeCylinder(p.CameraSideHoleDiameter/2,t+.2,App.Vector(xmin-.1,cy-sign*4*math.sin(a),cz+sign*4*math.cos(a)),App.Vector(1,0,0))
       check(probe.common(shape).Volume<1e-6,tag+': screw fits at '+str(angle))
    for other in physical_roles(p):
     if other!=m['role']:check(shape.common(s[other]).Volume<1e-6,tag+': camera plate clears '+other)
   if mechanism=='Dual arc slots':check(camera_body_centre(p,0)==camera_body_centre(p,45),tag+': no camera translation')
   if mechanism=='Upper pivot + lower arc':
    pivot=mount['side_holes'][0]
    for angle in camera_angles(p):
     cy,cz=camera_body_centre(p,angle);a=math.radians(angle)
     check(math.dist((cy-4*math.sin(a),cz+4*math.cos(a)),pivot)<1e-7,tag+': fixed upper screw')
 eight=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,StandoffCount='8 (4 pairs)',StandoffHeight=35)
 for p in (crossing,camera_cases[0],camera_cases[-2],eight):
  settings=create_frame(p);doc=settings.Document;folder=export_package(settings,output/'exports');report['export_folders'].append(str(folder))
  info=json.loads((folder/'ExportInfo.json').read_text());check(info['generator_version']==__version__,'Export current version')
  if underside_clamp_active(p):
   check('ArmLowerClampPlate' in info['cutting_files_include'],'Lower clamp exported')
   check(info['arm_mounting']['clamp_grip_mm']==arm_clamp_grip(p),'Correct complete bolt grip')
   check(not (folder/'MachiningOps.csv').exists(),'No obsolete point-retainer countersinks')
  if p.FPVEnabled:check(info['fpv']['camera_tab_slots']!=info['fpv']['camera_top_tab_slots'],'Independent slot layers in metadata')
  path=output/('roundtrip_'+str(len(report['export_folders']))+'.FCStd');name=settings.Name;doc.saveAs(str(path));App.closeDocument(doc.Name)
  doc=App.openDocument(str(path));settings=doc.getObject(name);doc.recompute();doc.UndoMode=1
  check(read_parameters(settings)==p,'All controls persist through native reopen')
  check(str(settings.Status).startswith('Valid'),'Valid native restore')
  update_frame(settings,replace(p,UndersideClampThickness=3));doc.undo();doc.recompute();check(read_parameters(settings)==p,'Undo restores controls');App.closeDocument(doc.Name)
 doc=App.openDocument(str(Path(__file__).parent/'fixtures/Legacy_0.10.FCStd'));settings=doc.getObject('FrameParameters');update_frame(settings,read_parameters(settings))
 check(settings.GeneratorVersion==__version__,'0.10 native migrates')
 check(not component_objects(settings)['ArmLowerClampPlate'].Shape.isNull(),'Migration adds lower capture plate')
 report['status']='passed'
except Exception:report['status']='failed';report['error']=traceback.format_exc()
finally:
 for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
 (output/'test_report.json').write_text(json.dumps(report,indent=2));print('CAPTURE/CAMERA',report['status'],len(report['checks']))
