"""Rebuild every technical Help figure from current portable workbench geometry.

White background, orthographic views, shared blue/teal/amber palette, DejaVu Sans.
No screenshots, raster recolouring or generated/decorative drone imagery.
"""
from guide_style import *
from dataclasses import replace,fields
import json,zipfile,xml.etree.ElementTree as ET
from freecad.rotorforge.parameters import Parameters,ENUMERATIONS,arm_layouts,motor_hole_offsets,plate_levels,standoff_layouts,stack_holes
from freecad.rotorforge.airflow_gui import finished_part_path,cutout_path,motor_pad_path,capsule_path
from freecad.rotorforge.part_preview import part_path,pad_path,grip_path
from freecad.rotorforge.flex_preview import flex_path,guard_plan_path
from freecad.rotorforge.protection_layout import guard_layout,guard_vents,vent_polygon
from freecad.rotorforge.fpv import camera_mounts,camera_position_y,camera_screw_offsets,camera_pivot_height
from freecad.rotorforge.flex_options import GUARD_VENT_SHAPES
from freecad.rotorforge.appearance import PRINTED_COLOURS
from freecad.rotorforge.motor_pads import MOTOR_PAD_SHAPES
from freecad.rotorforge.design_options import PLATE_SHAPES,ARM_BEAM_SHAPES,MOTOR_PAD_RELIEFS
from freecad.rotorforge.bottom_nose import NOSE_SHAPES
from freecad.rotorforge.battery import GRIP_PATTERNS
from freecad.rotorforge.cutouts import CUTOUT_TYPES,PATTERN_DEFAULTS,encode_patterns
DOC=ROOT/'docs';made=[]
def emit(name,cells,cols=2,**kwargs):
 gallery(name,cells,cols,**kwargs);made.append(name)
def path(p,role):return finished_part_path(p,role)
def example(name):
 with zipfile.ZipFile(ROOT/'examples'/name) as z:xml=ET.fromstring(z.read('Document.xml'))
 obj=next(o for o in xml.findall('./ObjectData/Object') if o.find("./Properties/Property[@name='Wheelbase']") is not None);data={};base=Parameters()
 for f in fields(base):
  node=obj.find(f"./Properties/Property[@name='{f.name}']")
  if node is None:continue
  child=list(node)[0];value=child.get('value')
  if node.get('type')=='App::PropertyEnumeration':
   choices=node.findall('./CustomEnumList/Enum');value=choices[int(value or '0')].get('value') if choices else None
  if value is None:continue
  default=getattr(base,f.name)
  if isinstance(default,bool):data[f.name]=value in ('true','1','True')
  elif isinstance(default,str):data[f.name]=value
  else:
   try:data[f.name]=float(value)
   except ValueError:pass
 return Parameters.from_dict(data)
def assembly(p,props=False):
 items=[]
 if props:
  for a in arm_layouts(p):items.append((ellipse(*a['motor'],p.PropDiameter/2),PALE,LINE))
 for a in arm_layouts(p):items.append((path(p,'Arm'+a['name']),BLUE))
 for role,colour in [('BottomPlate',LIGHT),('MidPlate',BLUE),('TopPlate',LIGHT)]:
  if role=='MidPlate' and p.PlateDesign!='3 plates':continue
  items.append((path(p,role),colour))
 if p.FPVEnabled:
  for m in camera_mounts(p):
   x0,x1=m['plate_x'];ys=[v[0] for v in m['wall_profile']];items.append((rect(x0,min(ys),x1-x0,max(ys)-min(ys)),BLUE))
  items.append((rect(-p.CameraWidth/2,camera_position_y(p)-p.CameraBodyDepth/2,p.CameraWidth,p.CameraBodyDepth),GREY))
 if p.FlexMotorProtectors:
  for a in arm_layouts(p):items.append((flex_path(p,'MotorProtector'+a['name']),TPU))
 if p.FlexSideGuards:
  for g in guard_layout(p):items.append((guard_plan_path(p,g),TPU))
 if p.LiPoPadEnabled:items.append((pad_path(p),TPU))
 for s in standoff_layouts(p):items.append((ellipse(*s['point'],p.StandoffDiameter/2),GREY))
 return items
p=Parameters();fpv=replace(p,FPVEnabled=True,TopFrontShape='Camera U recess',TopFrontDepth=28.,TopFrontRecessWidth=14.,TopFrontSetback=0.);guard=replace(fpv,FlexSideGuards=True,FlexGuardCloseFront=True,FlexGuardClearance=0.,FlexGuardWireEnabled=True)
hero=replace(guard,FlexMotorProtectors=True,LiPoPadEnabled=True)
emit('GuideCover.png',[cell('Front (+Y)',*assembly(hero,True))],1,rowheight=1000,cellwidth=1600)
emit('Frame.png',[cell(mode,*assembly(replace(p,PlateDesign=mode))) for mode in ('2 plates','3 plates')],2,rowheight=650)
emit('BatteryEditor.png',[cell('Overall layout',*assembly(hero)),cell('Top plate', (path(hero,'TopPlate'),BLUE)),cell('Arms',*[(path(hero,'Arm'+a['name']),BLUE) for a in arm_layouts(hero)]),cell('LiPo pad', (pad_path(hero),TPU),(grip_path(hero,pad_path(hero)),LIGHT))],2)
emit('PrintedColours.png',[cell(name,(rect(0,0,2,1),colour)) for name,colour in PRINTED_COLOURS.items()],5,rowheight=180,cellwidth=320)
emit('PlateOutlineOptions.png',[cell(n,(path(replace(p,TopPlateShape=n),'TopPlate'),BLUE)) for n in PLATE_SHAPES],4,rowheight=530,cellwidth=400)
nosecells=[]
for n in NOSE_SHAPES[:8]:
 q=replace(p,BottomNoseShape=n);outline=path(q,'BottomPlate');b=outline.boundingRect();clip=rect(b.left()-1,b.bottom()-20,b.width()+2,21);nosecells.append(cell(n,(outline.intersected(clip),BLUE)))
emit('BottomNoseShapes.png',nosecells,2,rowheight=310)
pReach=example('Example_ArmMatchedBottom_3_plates.FCStd')
emit('BottomStackReach.png',[cell('Shorter rear reach',(path(replace(pReach,BottomBodyRearReach=20),'BottomPlate'),BLUE)),cell('Longer rear reach',(path(replace(pReach,BottomBodyRearReach=40),'BottomPlate'),BLUE))],2)
pMid=example('Example_ArmMatchedMid_3_plates.FCStd')
emit('ArmMatchedMid.png',[cell('Arm roots / mid-plate tabs',*[(path(pMid,'Arm'+a['name']),LIGHT) for a in arm_layouts(pMid)],(path(pMid,'MidPlate'),BLUE))],1,rowheight=620,cellwidth=1600)
pattern=dict(PATTERN_DEFAULTS,role='TopPlate',shape='Rectangle',x=0,y=-25,width=10,length=12)
fillet=replace(p,TopEdgeFillet=3.,CutoutPatterns=encode_patterns([pattern]))
emit('PlateFillets.png',[cell('External corners',(path(fillet,'TopPlate'),BLUE)),cell('Include internal openings',(path(replace(fillet,TopFilletOpenings=True),'TopPlate'),BLUE))],2)
emit('ArmBeamOptions.png',[cell(n,(path(replace(p,ArmBeamShape=n,ArmProfileAmount=65),'ArmFrontRight'),BLUE)) for n in ARM_BEAM_SHAPES],2,rowheight=310)
pArm=replace(p,ArmRootFit='Fitted miters',ArmRootWidth=22.,ArmBeamShape='Stepped beam',StandoffLength=120.)
emit('ArmFillets.png',[cell('No arm fillet',(path(pArm,'ArmFrontRight'),BLUE)),cell('Fillets beyond the mounting root',(path(replace(pArm,ArmEdgeFillet=3.),'ArmFrontRight'),BLUE))],2,rowheight=430)
pKey=example('Example_CompactKeystone_3_plates.FCStd')
emit('FittedArmRoots.png',[cell('Fitted root joints',*[(path(pKey,'Arm'+a['name']),BLUE) for a in arm_layouts(pKey)],(path(pKey,'ArmKeystone'),LIGHT))],1,rowheight=590,cellwidth=1600)
pLower=example('Example_LowerCapture_RootReliefs_2_plates.FCStd');emit('LowerCapture.png',[cell('Lower capture plate',(path(pLower,'ArmLowerClampPlate'),BLUE))],1,rowheight=470,cellwidth=1600)
emit('KeystoneShapes.png',[cell(n,(path(replace(pKey,KeystoneShape=n),'ArmKeystone'),BLUE)) for n in ENUMERATIONS['KeystoneShape']],4,rowheight=370,cellwidth=400)
# Catalogues: identical scales, filled outlines and true mounting holes.
for n in MOTOR_PAD_SHAPES:
 q=replace(p,MotorPadShape=n,MotorBoltCircle=22.627416997969522,MotorHoleRotation=45.)
 outline=motor_pad_path(q).united(rect(-38,-q.ArmWidth/2,38,q.ArmWidth))
 for pt,r in [(pt,q.MotorHoleDiameter/2) for pt in motor_hole_offsets(q)]+[((0,0),q.MotorCenterDiameter/2)]:outline=outline.subtracted(ellipse(*pt,r))
 emit('motor_catalogue/'+n.replace(' ','_')+'.png',[cell('',(outline,BLUE),box=QtCore.QRectF(-38,-23,72,46))],1,rowheight=500,cellwidth=960,labels=False)
reliefcells=[]
for n in MOTOR_PAD_RELIEFS:
 q=replace(p,MotorPadShape='Round-shoulder shield',MotorPadRelief=n)
 outline=motor_pad_path(q)
 for pt,r in [(pt,q.MotorHoleDiameter/2) for pt in motor_hole_offsets(q)]+[((0,0),q.MotorCenterDiameter/2)]:outline=outline.subtracted(ellipse(*pt,r))
 reliefcells.append(cell(n,(outline,BLUE)))
emit('MotorPadReliefs.png',reliefcells,4,rowheight=400,cellwidth=400)
emit('MotorPadRotation.png',[cell(f'{angle} degree pad rotation',*[(path(replace(p,MotorPadRotation=angle),'Arm'+a['name']),BLUE) for a in arm_layouts(p)]) for angle in (0,25)],2,rowheight=620)
emit('StandoffLayouts.png',[cell(count,*assembly(replace(p,StandoffCount=count,StandoffPair3Y=-15.,StandoffPair4Y=15.))) for count in ('4 (2 pairs)','6 (3 pairs)','8 (4 pairs)')],3,rowheight=530,cellwidth=530)
# Height section, with the same orthographic palette as profile diagrams.
items=[(rect(-65,0,145,2),LIGHT),(rect(-55,2,108,5),BLUE),(rect(-65,7,110,3),BLUE),(rect(-65,35,145,2),LIGHT),(rect(45,2,3,33),GREY),(rect(-45,10,3,25),GREY),(rect(-16,10,32,13),GOLD)]
emit('PlateLevels.png',[cell('Side section: rear (-Y) to front (+Y)',*items)],1,rowheight=500,cellwidth=1600)
emit('LiPoPadShapes.png',[cell(n,(pad_path(replace(p,LiPoPadEnabled=True,LiPoPadShape=n,LiPoPadFollowPlate=False)),TPU)) for n in ENUMERATIONS['LiPoPadShape']],4,rowheight=480,cellwidth=400)
for n in GRIP_PATTERNS:
 q=replace(p,LiPoPadEnabled=True,LiPoPadFollowPlate=False,LiPoPadWidth=32,LiPoPadLength=65,LiPoPadGroovePitch=7,LiPoPadPattern=n);pad=pad_path(q)
 emit('grip_catalogue/'+n.replace(' ','_')+'.png',[cell('',(pad,TPU),(grip_path(q,pad),LIGHT))],1,rowheight=420,cellwidth=420,labels=False)
pCam=example('Example_FPV_SlopedCamera_DualSlots_3_plates.FCStd')
emit('CameraMountPatterns.png',[cell('Single side screw',(path(replace(fpv,CameraSideBoltSpacing=0.,CameraMountMode='Fixed'),'CameraMountLeft'),BLUE)),cell('Vertical 6.5 mm side pitch',(path(replace(fpv,CameraSideBoltSpacing=6.5,CameraMountMode='Fixed'),'CameraMountLeft'),BLUE))],2)
emit('CameraArc.png',[cell(f'Tilt: {a} degrees',(path(replace(pCam,CameraTilt=a),'CameraMountLeft'),BLUE),*[(ellipse(dy,camera_pivot_height(pCam)+dz,.8),GOLD) for dy,dz in camera_screw_offsets(pCam,a)]) for a in (0,25,45)],3,rowheight=480,cellwidth=530)
emit('CameraTravel.png',[cell(f'Camera offset: {a} mm',(path(replace(fpv,FlexCameraMode='Captured inserts',CameraForeAftOffset=a),'CameraMountLeft'),BLUE)) for a in (0,20)],2)
pCamBase=example('Example_FPV_ExtendedCameraBase_3_plates.FCStd');emit('CameraBase.png',[cell(n+' lower contact',(path(replace(pCamBase,CameraBaseMode=n),'CameraMountLeft'),BLUE)) for n in ('Automatic','Custom')],2)
emit('CameraTopRearOffset.png',[cell(f'Upper contact rearward: {a} mm',(path(replace(pCamBase,CameraTopRearOffset=a),'CameraMountLeft'),BLUE)) for a in (0,6)],2)
isol=[]
for n in ('Hard mount','Compression pads','Captured inserts'):
 gap=0.2 if n=='Hard mount' else 1.85;items=[(rect(-9.5,-7,19,14),GREY)]
 for sign in (-1,1):
  wallx=sign*(9.5+gap);x=wallx if sign>0 else wallx-3;items.append((rect(x,-16.5,3,33),BLUE))
  if n=='Compression pads':items.append((rect(9.5 if sign>0 else -9.5-gap,-8,gap,16),TPU))
  if n=='Captured inserts':items.extend([(rect(9.5 if sign>0 else -12.35,-8,2.85,16),TPU),(rect(10.35 if sign>0 else -15.35,-9.5,5,19),TPU)])
 isol.append(cell(n+' / front section',*items))
emit('FlexibleCameraModes.png',isol,3,rowheight=500,cellwidth=530)
emit('FlexibleInterfaceShapes.png',[cell(n,(flex_path(replace(fpv,FlexCameraMode='Captured inserts',FlexInterfaceShape=n),'CameraPadLeft'),TPU)) for n in ('Rounded rectangle','Side plate outline')],2)
protect=replace(p,FlexMotorProtectors=True,MotorPadShape='Scalloped shield')
emit('MotorProtectors.png',[cell('Carbon pad and arm',(path(protect,'ArmFrontRight'),BLUE)),cell('Protector / underside',(flex_path(protect,'MotorProtectorFrontRight'),TPU))],2)
emit('MotorGuardService.png',[cell(n,(flex_path(replace(protect,FlexProtectorRetention=n),'MotorProtectorFrontRight'),TPU)) for n in ('Motor screws','Linked screw access')],2)
baseguard=replace(fpv,FlexSideGuards=True,FlexGuardExtendFront=True,StandoffCount='6 (3 pairs)',StandoffPair3Y=-94.,StandoffPair3Width=28,MidReachMode='Custom',MidRearReach=102.,TopReachMode='Custom',TopRearReach=102.)
emit('ElectronicsGuards.png',[cell('Side view / foremost posts covered',(flex_path(baseguard,'ElectronicsGuardLeft'),TPU))],1,rowheight=430,cellwidth=1600)
g=guard_layout(baseguard)[0];bands=[]
for st,(lo,hi) in zip(g['stands'],g['bands']):bands.append(cell(f'{st["position"]}: {hi-lo:g} mm grip',(rect(-1.5,st['base'],3,st['length']),GREY),(rect(-4,lo,2,hi-lo),TPU),(rect(2,lo,2,hi-lo),TPU)))
emit('GuardGripHeight.png',bands,3,rowheight=500,cellwidth=530)
r=(p.StandoffDiameter+p.FlexGuardFit)/2+p.FlexGuardWall
large=QtGui.QTransform();large.scale(100,100);small=QtGui.QTransform();small.scale(.01,.01)
hole=large.map(ellipse(0,0,(p.StandoffDiameter+p.FlexGuardFit)/2))
ring=small.map(large.map(ellipse(0,0,r)).subtracted(hole))
bridge=small.map(large.map(capsule_path((0,0),(4,0),r)).subtracted(hole))
emit('GuardGripSections.png',[cell('Circular inner bearing',(ring,TPU)),cell('Rounded outward support',(bridge,TPU))],2,rowheight=430)
emit('GuardMatchingWidths.png',[cell('Both side guards / top view',(path(baseguard,'TopPlate'),LIGHT),*[(guard_plan_path(baseguard,g),TPU) for g in guard_layout(baseguard)])],1,rowheight=580,cellwidth=1600)
emit('GuardFrontClosure.png',[cell('Foremost-post forward closure',(flex_path(guard,'ElectronicsGuardLeft'),TPU))],1,rowheight=440,cellwidth=1600)
emit('GuardVentSections.png',[cell('VTX section only',(flex_path(replace(baseguard,FlexGuardFCVents=False),'ElectronicsGuardLeft'),TPU)),cell('Independent VTX and FC vents',(flex_path(replace(baseguard,FlexGuardVentShape='Hexagons',FlexGuardFCVentShape='Rounded slots'),'ElectronicsGuardLeft'),TPU))],1,rowheight=350,cellwidth=1600)
vents=[]
for n in GUARD_VENT_SHAPES:
 block=rect(-12,-5,24,10)
 for y in ((0,) if n=='Horizontal slots' else (-6,6)):
  poly=vent_polygon(dict(shape=n,width=8.,height=5.))
  if poly:tool=polygon_path([(y+x,z) for x,z in poly])
  elif n=='Ellipses':tool=ellipse(y,0,4,2.5)
  elif n=='Rounded slots':tool=capsule_path((y-1.5,0),(y+1.5,0),2.5)
  else:tool=rect(-10,-2.5,20,5)
  block=block.subtracted(tool)
 vents.append(cell(n,(block,TPU)))
emit('GuardVentShapes.png',vents,4,rowheight=260,cellwidth=400)
emit('GuardUSBAccess.png',[cell('Adjustable USB opening',(flex_path(replace(baseguard,FlexGuardUSBEnabled=True,FlexGuardUSBY=-6.),'ElectronicsGuardLeft'),TPU))],1,rowheight=400,cellwidth=1600)
emit('GuardWireOpenings.png',[cell('Wire exits at the local lower edge',(flex_path(replace(baseguard,FlexGuardWireEnabled=True),'ElectronicsGuardLeft'),TPU))],1,rowheight=400,cellwidth=1600)
for n in CUTOUT_TYPES:
 pat=dict(PATTERN_DEFAULTS,shape=n,width=8.,length=12.,x=0.,y=0.);emit('cutout_catalogue/'+n.replace(' ','_')+'.png',[cell('',(cutout_path(pat),BLUE),box=QtCore.QRectF(-5,-7,10,14))],1,rowheight=330,cellwidth=380,labels=False)
comb=[]
for title,patterns in [('Crossed slots',[dict(shape='Slot',width=4,length=15,rotation=a) for a in (0,90)]),('Circle union',[dict(shape='Circle',width=8,length=8,x=x) for x in (-5,0,5)]),('Diamond + ellipse',[dict(shape='Diamond',width=10,length=13),dict(shape='Ellipse',width=12,length=8,x=4)]),('Cross + leaf',[dict(shape='Cross',width=12,length=14),dict(shape='Leaf',width=8,length=13,x=3)])]:
 union=QtGui.QPainterPath()
 for pat in patterns:union=union.united(cutout_path(dict(PATTERN_DEFAULTS,**pat)))
 comb.append(cell(title,(union,BLUE)))
emit('CutoutCombinations.png',comb,4,rowheight=410,cellwidth=400)
pNotch=example('Example_OutlineNotches_3_plates.FCStd');emit('Outline_Notched.png',[cell('Original edge',(path(replace(pNotch,CutoutPatterns='[]'),'TopPlate'),BLUE)),cell('Applied outline cuts',(path(pNotch,'TopPlate'),BLUE))],2)
# VTX: actual carrier profile and a clean section with consistent palette.
vtx=replace(fpv,StandoffHeight=35.,VTXPattern='Both (20 + 25.5 mm)');levels=plate_levels(vtx);deck=levels['deck_z'];top=levels['top_z'];clip=rect(-42,-95,84,100)
emit('VTXCoverage.png',[cell('Rear carrier / top view',(path(vtx,'MidPlate').intersected(clip),BLUE),(rect(-vtx.VTXWidth/2,vtx.VTXOffsetY-vtx.VTXLength/2,vtx.VTXWidth,vtx.VTXLength),GOLD),(path(vtx,'TopPlate').intersected(clip),None)),cell('VTX under the top plate / side section',(rect(-30,deck-vtx.ClampThickness,60,vtx.ClampThickness),BLUE),(rect(-30,top,60,vtx.TopThickness),LIGHT),(rect(-vtx.VTXLength/2,deck,vtx.VTXLength,vtx.VTXHeight),GOLD))],2,rowheight=630)
# Thickness-separated, alternating CNC arrangement uses the actual layout planner.
from freecad.rotorforge.cutting_layout import arrange_profiles,ARM_ROLES
from freecad.rotorforge.part_preview import preview_roles
parts={};spec=[]
for role in preview_roles(p):
 pp=path(p,role)
 if role.startswith('Arm'):
  a=next(a for a in arm_layouts(p) if 'Arm'+a['name']==role);t=QtGui.QTransform();t.rotate(90-math.degrees(math.atan2(a['unit'][1],a['unit'][0]))+(180 if ARM_ROLES.index(role)%2 else 0));pp=t.map(pp)
 b=pp.boundingRect();parts[role]=shifted(pp,-b.left(),-b.top());thick=p.ArmThickness if role.startswith('Arm') else p.TopThickness if role=='TopPlate' else p.ClampThickness if role=='MidPlate' else p.BottomThickness;spec.append(dict(role=role,width=b.width(),height=b.height(),thickness=thick))
layout=arrange_profiles(spec);emit('CuttingSheets.png',[cell(f'Stock: {sheet["thickness"]:g} mm',*[(shifted(parts[item['role']],item['x'],item['y']),BLUE) for item in sheet['parts']]) for sheet in layout['sheets']],len(layout['sheets']),rowheight=620,cellwidth=530)
(DOC/'illustration_manifest.json').write_text(json.dumps(dict(style='Orthographic engineering diagrams; DejaVu Sans; white / carbon grey / darker TPU grey / grey shape catalogues / amber references',files=made),indent=2));print('RENDERED',len(made),'consistent illustrations')
