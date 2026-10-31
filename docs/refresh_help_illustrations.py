"""Rebuild coloured Help illustrations from the workbench's portable geometry.

Run outside FreeCAD with Qt installed. The user-supplied cover is preserved.
"""
from pathlib import Path
import sys,math,json,zipfile,xml.etree.ElementTree as ET
from dataclasses import fields,replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));DOC=ROOT/'docs'
from freecad.rotorforge.parameters import Parameters,plate_levels,arm_layouts,motor_hole_offsets,standoff_layouts
from freecad.rotorforge.airflow_gui import QtGui,QtCore,QtWidgets,finished_part_path,cutout_path,polygon_path,capsule_path,motor_pad_path
from freecad.rotorforge.cutouts import CUTOUT_TYPES,encode_patterns,PATTERN_DEFAULTS,pattern_instances
from freecad.rotorforge.fpv import camera_mounts,camera_position_y,camera_screw_offsets,camera_pivot_height
from freecad.rotorforge.motor_pads import motor_tip_slots
from freecad.rotorforge.cutting_layout import arrange_profiles,ARM_ROLES
app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
INK='#183542';TEAL='#3b8f9f';BLUE='#4d7fa5';GOLD='#e3ae5d';PALE='#d7e9ee';SLATE='#8da5b4';ORANGE='#c97825'
def image(w,h):
 im=QtGui.QImage(w,h,QtGui.QImage.Format_RGB888);im.fill(QtGui.QColor('white'));q=QtGui.QPainter(im);q.setRenderHint(QtGui.QPainter.Antialiasing);return im,q

def label(q,rect,text,size=27,color=INK,align=None):
 q.save();font=q.font();font.setFamily('DejaVu Sans');font.setPixelSize(size);q.setFont(font);q.setPen(QtGui.QColor(color));q.drawText(QtCore.QRectF(*rect),align or (QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter|QtCore.Qt.TextWordWrap),text);q.restore()

def draw(q,path,rect,color=TEAL,stroke=INK,padding=12,markers=(),viewbox=None):
 b=viewbox if viewbox is not None else path.boundingRect();x,y,w,h=rect;scale=min((w-2*padding)/b.width(),(h-2*padding)/b.height())
 q.save();q.translate(x+w/2,y+h/2);q.scale(scale,-scale);q.translate(-b.center().x(),-b.center().y());q.setPen(QtGui.QPen(QtGui.QColor(stroke),1.6/scale));q.setBrush(QtGui.QColor(color));q.drawPath(path)
 if markers:
  q.setPen(QtGui.QPen(QtGui.QColor(ORANGE),1.2/scale));q.setBrush(QtGui.QColor(GOLD))
  if len(markers)==2:q.drawLine(QtCore.QPointF(*markers[0]),QtCore.QPointF(*markers[1]))
  for pt in markers:q.drawEllipse(QtCore.QPointF(*pt),.75,.75)
 q.restore()
 return scale

def save(im,q,name):q.end();assert im.save(str(DOC/name))

def example(name):
 # Read only the parameter object's portable property values; retain original files.
 with zipfile.ZipFile(ROOT/'examples'/name) as z:r=ET.fromstring(z.read('Document.xml'))
 obj=next(o for o in r.findall('./ObjectData/Object') if o.find("./Properties/Property[@name='Wheelbase']") is not None)
 data={};base=Parameters()
 for f in fields(base):
  node=obj.find(f"./Properties/Property[@name='{f.name}']")
  if node is None:continue
  child=list(node)[0];value=child.get('value')
  if node.get('type')=='App::PropertyEnumeration':
   choices=node.findall('./CustomEnumList/Enum');index=int(value or '0');value=choices[index].get('value') if choices else None
  if value is None:continue
  default=getattr(base,f.name)
  if isinstance(default,bool):data[f.name]=value in ('true','1','True')
  elif isinstance(default,str):data[f.name]=value
  else:
   try:data[f.name]=float(value)
   except ValueError:continue
 return Parameters.from_dict(data)

# One exact catalogue in editor order: filled silhouettes denote removed material.
folder=DOC/'cutout_catalogue';folder.mkdir(exist_ok=True)
for name in CUTOUT_TYPES:
 pat=dict(PATTERN_DEFAULTS,shape=name,width=8.,length=12.,x=0.,y=0.)
 path=cutout_path(pat);im,q=image(380,330);draw(q,path,(20,12,340,290),TEAL,viewbox=QtCore.QRectF(-4.5,-6.5,9,13))
 save(im,q,'cutout_catalogue/'+name.replace(' ','_')+'.png')

# A uniform old/new comparison for interior and edge cuts, using finished profiles.
p=example('Example_OutlineNotches_3_plates.FCStd');base=replace(p,CutoutPatterns='[]');im,q=image(1500,850)
for i,(value,title,color) in enumerate(((base,'Before edge notches',PALE),(p,'After edge notches',TEAL))):
 label(q,(50+i*750,15,650,55),title,32);draw(q,finished_part_path(value,'TopPlate'),(90+i*750,80,570,670),color)
label(q,(80,770,1340,55),'Filled material stays connected; white regions are holes, slots and edge notches.',26)
save(im,q,'Outline_Notched.png')

# Intersections use the exact same union and rotation as the editor.
im,q=image(1600,840)
examples=(('Crossed slots',[dict(shape='Slot',width=4,length=15,rotation=0),dict(shape='Slot',width=4,length=15,rotation=90)]),('Ellipse + diamond',[dict(shape='Ellipse',width=12,length=9),dict(shape='Diamond',width=10,length=13,x=4)]),('Overlapping circles',[dict(shape='Circle',width=8,length=8,x=x) for x in (-5,0,5)]),('Cross + leaf',[dict(shape='Cross',width=12,length=14),dict(shape='Leaf',width=8,length=13,x=3,y=1)]))
for i,(title,patterns) in enumerate(examples):
 paths=[cutout_path(dict(PATTERN_DEFAULTS,**pat)) for pat in patterns];union=QtGui.QPainterPath()
 sampling=QtGui.QTransform();sampling.scale(100,100)
 for path in paths:union=union.united(sampling.map(path))
 union=sampling.inverted()[0].map(union)
 x=i*400;label(q,(x+12,8,376,60),title,28)
 b=union.boundingRect();scale=min(300/b.width(),235/b.height())
 q.save();q.translate(x+200,205);q.scale(scale,-scale);q.translate(-b.center().x(),-b.center().y())
 for j,path in enumerate(paths):q.setPen(QtGui.QPen(QtGui.QColor(ORANGE if j%2 else BLUE),1.5/scale));q.setBrush(QtGui.QColor(227,174,93,90) if j%2 else QtGui.QColor(59,143,159,90));q.drawPath(path)
 q.restore();label(q,(x+120,345,160,55),'Union',25,ORANGE)
 draw(q,union,(x+30,405,340,280),TEAL);label(q,(x+20,725,360,75),'One combined opening',24)
save(im,q,'CutoutCombinations.png')

# Coloured capture plate, using the supported native example's actual finished path.
p=example('Example_LowerCapture_RootReliefs_2_plates.FCStd');im,q=image(900,720);draw(q,finished_part_path(p,'ArmLowerClampPlate'),(100,15,700,620),TEAL)
label(q,(60,645,780,55),'Lower capture plate with stack-service openings',27);save(im,q,'LowerCapture.png')

# Motor reliefs include real fixing holes and shaft openings.
im,q=image(1800,460)
from freecad.rotorforge.design_options import MOTOR_PAD_RELIEFS
for i,name in enumerate(MOTOR_PAD_RELIEFS):
 p=Parameters(MotorPadShape='Round-shoulder shield',MotorPadRelief=name,MotorBoltCircle=22.627416997969522,MotorHoleRotation=45)
 path=motor_pad_path(p)
 for pt,radius in [(pt,p.MotorHoleDiameter/2) for pt in motor_hole_offsets(p)]+[((0,0),p.MotorCenterDiameter/2)]:
  hole=QtGui.QPainterPath();hole.addEllipse(QtCore.QPointF(*pt),radius,radius);path=path.subtracted(hole)
 draw(q,path,(i*450+12,12,426,350));label(q,(i*450+10,373,430,65),name,28)
save(im,q,'MotorPadReliefs.png')

# Camera slot paths, wall contact and sloping upper tabs, all coloured.
p=example('Example_FPV_SlopedCamera_DualSlots_3_plates.FCStd');im,q=image(1500,750)
for i,angle in enumerate((0,25,45)):
 value=replace(p,CameraTilt=angle);path=finished_part_path(value,'CameraMountLeft');draw(q,path,(i*500+70,20,360,580),TEAL,markers=tuple((dy,camera_pivot_height(value)+dz) for dy,dz in camera_screw_offsets(value,angle)))
 label(q,(i*500+35,620,430,80),f'Variable tilt: {angle} degrees',28)
save(im,q,'CameraArc.png')

p=example('Example_FPV_ExtendedCameraBase_3_plates.FCStd');im,q=image(1450,760)
base_box=finished_part_path(replace(p,CameraBaseMode='Automatic'),'CameraMountLeft').boundingRect().united(finished_part_path(replace(p,CameraBaseMode='Custom'),'CameraMountLeft').boundingRect())
for i,(mode,title) in enumerate((('Automatic','Automatic lower contact'),('Custom','Extended lower contact'))):
 value=replace(p,CameraBaseMode=mode);path=finished_part_path(value,'CameraMountLeft');draw(q,path,(i*725+55,80,615,550),TEAL if i else BLUE,viewbox=base_box)
 label(q,(i*725+20,8,685,65),title,31)
label(q,(60,655,1330,65),'Upper tabs follow the top plate; lower tongues follow the chosen bottom contact.',27)
save(im,q,'CameraBase.png')

# A legible side-section drawing; vertical dimensions are deliberately expanded.
im,q=image(1500,700)
label(q,(30,12,1440,65),'Three-plate side section - height relationships',35)
q.save();q.translate(140,555);q.scale(6,-10)
def box(x,y,w,h,color):q.setPen(QtGui.QPen(QtGui.QColor(INK),.25));q.setBrush(QtGui.QColor(color));q.drawRect(QtCore.QRectF(x,y,w,h))
# Horizontal coordinate is frame Y, front at right. Vertical dimension is Z.
box(25,0,145,2,GOLD);box(25,2,110,5,SLATE);box(0,7,105,3,BLUE);box(0,35,170,2,TEAL)
box(15,10,2,25,SLATE);box(151,2,2,33,SLATE)
box(52,10,32,13,'#c2d9e4');box(25,10,24,6,'#f2d29b')
q.restore()
label(q,(290,406,144,40),'VTX',23)
label(q,(452,365,192,50),'FC / ESC',23)
for y,text,color in ((185,'Top plate',TEAL),(460,'Mid plate / stack carrier',BLUE),(510,'Arms between bottom and mid',SLATE),(545,'Bottom plate',GOLD)):
 target={185:185,460:370,510:465,545:560}[y]
 q.setPen(QtGui.QPen(QtGui.QColor(color),3));q.drawLine(QtCore.QPointF({185:1160,460:770,510:950,545:1160}[y],y),QtCore.QPointF(1230,target));label(q,(1240,target-35,250,75),text,25,color,QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter|QtCore.Qt.TextWordWrap)
label(q,(130,605,1030,60),'Rear (-Y)                                  Front (+Y)',28)
label(q,(70,660,1340,35),'Diagram exaggerates thickness for clarity; each colour identifies a separate part.',22)
save(im,q,'PlateLevels.png')

# Colour the actual thickness-separated layout using the same alternating planner.
p=Parameters();parts={};items=[]
from freecad.rotorforge.part_preview import preview_roles
for role in preview_roles(p):
 if role=='LiPoPad':continue
 path=finished_part_path(p,role)
 if role.startswith('Arm'):
  a=next(a for a in arm_layouts(p) if 'Arm'+a['name']==role);t=QtGui.QTransform();t.rotate(90-math.degrees(math.atan2(a['unit'][1],a['unit'][0]))+(180 if ARM_ROLES.index(role)%2 else 0));path=t.map(path)
 b=path.boundingRect();t=QtGui.QTransform();t.translate(-b.left(),-b.top());path=t.map(path);parts[role]=path
 thickness=p.ArmThickness if role.startswith('Arm') else p.TopThickness if role=='TopPlate' else p.ClampThickness if role=='MidPlate' else p.BottomThickness
 items.append(dict(role=role,width=b.width(),height=b.height(),thickness=thickness))
layout=arrange_profiles(items);im,q=image(1600,850)
for i,sheet in enumerate(layout['sheets']):
 cw=1600/len(layout['sheets']);x=i*cw;label(q,(x+10,5,cw-20,60),f'Stock: {sheet["thickness"]:g} mm',32)
 scale=min((cw-70)/sheet['width'],650/sheet['height']);q.save();q.translate(x+(cw-sheet['width']*scale)/2,745);q.scale(scale,-scale)
 q.setBrush(QtGui.QColor('#f0f5f7'));q.setPen(QtGui.QPen(QtGui.QColor('#cfdee5'),1/scale));q.drawRect(QtCore.QRectF(0,0,sheet['width'],sheet['height']))
 for item in sheet['parts']:
  t=QtGui.QTransform();t.translate(item['x'],item['y']);path=t.map(parts[item['role']]);q.setBrush(QtGui.QColor(TEAL if item['role'].startswith('Arm') else BLUE if item['role']=='MidPlate' else GOLD));q.setPen(QtGui.QPen(QtGui.QColor(INK),1.2/scale));q.drawPath(path)
 q.restore()
label(q,(60,775,1480,60),'Colour identifies parts only; DXF/SVG remain exact through-cut contours. Sheets are shown at independent display scales.',24)
save(im,q,'CuttingSheets.png')
print('Refreshed cutout catalogue and eight technical figures')
