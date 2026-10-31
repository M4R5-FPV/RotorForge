"""Actual rear plate plan plus an orthographic clearance section and pitch details."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from freecad.rotorforge.parameters import Parameters,plate_levels,standoff_layouts
from freecad.rotorforge.fpv import vtx_deck_z,vtx_holes
from freecad.rotorforge.airflow_gui import QtGui,QtCore,QtWidgets,finished_part_path
app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
INK='#183542';TEAL='#5ba1ac';BLUE='#356eaf';ORANGE='#e5ac62';RUST='#aa542d'
p=Parameters(FPVEnabled=True,PlateDesign='3 plates',StandoffHeight=35,VTXPattern='Both (20 + 25.5 mm)')
# The image uses the same finished profiles and mounting levels as the editor.
levels=plate_levels(p);deck=vtx_deck_z(p);top=levels['top_z']
im=QtGui.QImage(1800,1200,QtGui.QImage.Format_RGB888);im.fill(QtGui.QColor('white'));q=QtGui.QPainter(im);q.setRenderHint(QtGui.QPainter.Antialiasing)
def text(rect,value,size=31,color=INK):
 q.save();font=QtGui.QFont('DejaVu Sans');font.setPixelSize(size);q.setFont(font);q.setPen(QtGui.QColor(color));q.drawText(QtCore.QRectF(*rect),QtCore.Qt.AlignCenter|QtCore.Qt.TextWordWrap,value);q.restore()
def line(a,b,color=INK,width=3,dash=False):
 q.setPen(QtGui.QPen(QtGui.QColor(color),width,QtCore.Qt.DashLine if dash else QtCore.Qt.SolidLine));q.drawLine(QtCore.QPointF(*a),QtCore.QPointF(*b))
def arrow(a,b,color=INK):
 import math
 line(a,b,color);ang=math.atan2(b[1]-a[1],b[0]-a[0]);q.setBrush(QtGui.QColor(color))
 for pt,theta in ((a,ang),(b,ang+math.pi)):
  poly=QtGui.QPolygonF([QtCore.QPointF(*pt)]+[QtCore.QPointF(pt[0]+13*math.cos(theta+d),pt[1]+13*math.sin(theta+d)) for d in (-.4,.4)])
  q.drawPolygon(poly)
text((55,10,740,65),'Rear deck • top view',38)
text((920,10,820,65),'VTX clearance • side section',38)
# Left: actual rear portion of the three-plate frame, not a generic rectangle.
clip=QtGui.QPainterPath();clip.addRect(QtCore.QRectF(-42,-95,84,100))
carrier=finished_part_path(p,'MidPlate').intersected(clip)
roof=finished_part_path(p,'TopPlate').intersected(clip)
q.save();q.translate(440,170);q.scale(7.5,-7.5)
q.setPen(QtGui.QPen(QtGui.QColor(INK),.38));q.setBrush(QtGui.QColor(TEAL));q.drawPath(carrier)
q.setPen(QtGui.QPen(QtGui.QColor(RUST),.4));q.setBrush(QtGui.QColor(ORANGE));q.drawRect(QtCore.QRectF(-p.VTXWidth/2,p.VTXOffsetY-p.VTXLength/2,p.VTXWidth,p.VTXLength))
for (x,y),r,pitch in vtx_holes(p):
 q.setPen(QtGui.QPen(QtGui.QColor(BLUE if pitch==20 else RUST),.36));q.setBrush(QtGui.QColor('white'));q.drawEllipse(QtCore.QPointF(x,y),r,r)
q.setPen(QtGui.QPen(QtGui.QColor(BLUE),.65,QtCore.Qt.DashLine));q.setBrush(QtCore.Qt.NoBrush);q.drawPath(roof)
for st in standoff_layouts(p):
 x,y=st['point']
 if y>5:continue
 q.setPen(QtGui.QPen(QtGui.QColor(INK),.28));q.setBrush(QtGui.QColor('#a8b8c3'));q.drawEllipse(QtCore.QPointF(x,y),p.StandoffDiameter/2,p.StandoffDiameter/2)
q.restore()
text((130,77,620,40),'Toward FC stack / front ↑',30)
text((140,885,610,55),'Rear of frame',30)
# A legend outside the geometry keeps the plate and transmitter identifiable.
for y,color,value,dash in ((985,TEAL,'Mid plate supports the VTX',False),(1040,BLUE,'Top plate coverage (dashed)',True),(1095,RUST,'Orange area: VTX envelope',False)):
 line((110,y+20),(185,y+20),color,7,dash);text((205,y-3,570,50),value,29)
# Right: use actual plate heights and electronic dimensions, with a shortened
# horizontal span focused on the VTX; Z scale is shared for all components.
x0=1000;zbase=455;scale=8;rear=p.VTXOffsetY-p.VTXLength/2-7;front=p.VTXOffsetY+p.VTXLength/2+7
xy=lambda y,z:QtCore.QPointF(x0+(y-rear)*scale,zbase-z*scale)
def block(y0,y1,z0,z1,fill):
 a,b=xy(y0,z1),xy(y1,z0);q.setPen(QtGui.QPen(QtGui.QColor(INK),2));q.setBrush(QtGui.QColor(fill));q.drawRect(QtCore.QRectF(a,b))
block(rear,front,deck-p.ClampThickness,deck,TEAL)
block(rear,front,top,top+p.TopThickness,BLUE)
block(p.VTXOffsetY-p.VTXLength/2,p.VTXOffsetY+p.VTXLength/2,deck,deck+p.VTXHeight,ORANGE)
# End view is deliberately sectioned through the board centre, so standoffs
# outside that section are omitted rather than appearing to intersect the VTX.
text((1460,95,300,60),'Top plate',30,BLUE)
text((1455,345,310,70),'Mid plate',30,INK)
text((1090,310,260,65),'VTX',32,RUST)
clearx=1430;za=xy(front,deck+p.VTXHeight).y();zb=xy(front,top).y()
arrow((clearx,za),(clearx,zb),BLUE)
text((1445,190,300,115),'Free space above VTX',29,BLUE)
text((970,490,780,85),'2 plates: the bottom plate is the VTX carrier.\n3 plates: the mid plate is the carrier.',29)
line((920,605),(1750,605),'#cfdee5',2)
text((930,625,820,60),'Mounting pitches • centre to centre',34)
for i,(pitch,color) in enumerate(((20,BLUE),(25.5,RUST))):
 cx=1120+i*410;cy=890;s=7;half=pitch*s/2
 q.setPen(QtGui.QPen(QtGui.QColor(color),2,QtCore.Qt.DashLine));q.setBrush(QtCore.Qt.NoBrush);q.drawRect(QtCore.QRectF(cx-half,cy-half,2*half,2*half))
 q.setBrush(QtGui.QColor(color));q.setPen(QtCore.Qt.NoPen)
 for dx in (-half,half):
  for dy in (-half,half):q.drawEllipse(QtCore.QPointF(cx+dx,cy+dy),9,9)
 arrow((cx-half,cy+half+40),(cx+half,cy+half+40),color)
 text((cx-155,cy+half+50,310,55),f'{pitch:g} × {pitch:g} mm',30,color)
text((950,1100,790,70),'“Both” provides two alternative sets of four holes.',28)
q.end();assert im.save(str(ROOT/'docs/VTXCoverage.png'))
print('Rendered actual rear profiles, carrier levels and measured pitches')
