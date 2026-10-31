"""Numbered cutout list and shared-geometry preview in the guide palette."""
from guide_style import *
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.cutouts import PATTERN_DEFAULTS,pattern_instances
from freecad.rotorforge.airflow_gui import finished_part_path,cutout_path
p=Parameters(StrapSlotsEnabled=False)
patterns=[dict(PATTERN_DEFAULTS,shape='Circle',width=6.,x=-8.,y=-14.),dict(PATTERN_DEFAULTS,x=8.,y=-12.),dict(PATTERN_DEFAULTS,shape='Hexagon',width=7.,length=8.,x=-8.,y=10.),dict(PATTERN_DEFAULTS,width=6.,x=8.,y=12.),dict(PATTERN_DEFAULTS,shape='Circle',width=6.,x=10.,y=18.),dict(PATTERN_DEFAULTS,shape='Circle',width=5.,x=0.,y=-28.,columns=2,pitch_x=16.)]
im=QtGui.QImage(1600,620,QtGui.QImage.Format_RGB888);im.fill(QtGui.QColor(WHITE));q=QtGui.QPainter(im);q.setRenderHint(QtGui.QPainter.Antialiasing)
def text(rect,text,size=28,colour=INK):
 f=QtGui.QFont('DejaVu Sans');f.setPixelSize(size);q.setFont(f);q.setPen(QtGui.QColor(colour));q.drawText(QtCore.QRectF(*rect),QtCore.Qt.AlignVCenter,text)
text((35,15,720,45),'Saved patterns - Top plate',32)
q.setPen(QtGui.QColor(LINE));q.setBrush(QtGui.QColor(PALE));q.drawRoundedRect(QtCore.QRectF(35,70,700,58),5,5)
text((52,77,665,44),'Find: #number, shape, coordinates...',25,TEAL)
for i,pat in enumerate(patterns):
 y=148+i*64
 if i==3:
  q.setPen(QtGui.QColor('#d87809'));q.setBrush(QtGui.QColor('#fff0d7'));q.drawRoundedRect(QtCore.QRectF(35,y,700,56),4,4)
 text((50,y+3,680,48),f"#{i+1}   {pat['shape']}   ({pat['x']:g}, {pat['y']:g})"+('   2 copies' if i==5 else ''),28)
text((870,15,660,45),'Click an opening or its number',30)
t=QtGui.QTransform();t.translate(1190,325);t.scale(7.2,-7.2)
q.save();q.setClipRect(QtCore.QRectF(850,70,680,510));q.setTransform(t)
q.setPen(QtGui.QPen(QtGui.QColor(INK),.3));q.setBrush(QtGui.QColor(BLUE));q.drawPath(finished_part_path(p,'TopPlate',patterns))
q.setPen(QtGui.QPen(QtGui.QColor('#d87809'),.8));q.setBrush(QtGui.QColor(255,178,65,65));q.drawPath(cutout_path(patterns[3]));q.restore()
for i in (0,1,2,4,5,3):
 point=t.map(QtCore.QPointF(patterns[i]['x'],patterns[i]['y']));r=QtCore.QRectF(point.x()-28,point.y()-18,56,36)
 q.setPen(QtGui.QColor('#d87809') if i==3 else QtGui.QColor(TEAL));q.setBrush(QtGui.QColor(WHITE));q.drawRoundedRect(r,4,4)
 f=QtGui.QFont('DejaVu Sans');f.setPixelSize(26);q.setFont(f);q.drawText(r,QtCore.Qt.AlignCenter,'#'+str(i+1))
q.end();assert im.save(str(ROOT/'docs/CutoutLocator.png'))
