"""Render all motor-pad help illustrations with Qt; no FreeCAD GUI needed."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from freecad.rotorforge.parameters import Parameters,motor_hole_offsets
from freecad.rotorforge.motor_pads import MOTOR_PAD_SHAPES,motor_pad_primitives
from freecad.rotorforge.airflow_gui import QtWidgets,QtGui,QtCore
app=QtWidgets.QApplication([])
out=ROOT/'docs/motor_catalogue';out.mkdir(exist_ok=True)
for name in MOTOR_PAD_SHAPES:
 p=Parameters(MotorBoltCircle=22.627416997969522,MotorHoleRotation=45,MotorPadShape=name,MotorTipSlotEnabled=False)
 scale=QtGui.QTransform();scale.scale(100,100)
 path=QtGui.QPainterPath();cuts=[]
 for primitive in motor_pad_primitives(p):
  part=QtGui.QPainterPath()
  if primitive['kind']=='circle':part.addEllipse(QtCore.QPointF(*primitive['centre']),primitive['radius'],primitive['radius'])
  elif primitive['kind']=='rounded':
   w=primitive['width'];part.addRoundedRect(QtCore.QRectF(-w/2,-w/2,w,w),primitive['radius'],primitive['radius'])
  else:
   part.moveTo(*primitive['points'][0])
   for point in primitive['points'][1:]:part.lineTo(*point)
   part.closeSubpath()
  if primitive.get('operation')=='cut':cuts.append(scale.map(part))
  else:path=path.united(scale.map(part))
 for cut in cuts:path=path.subtracted(cut)
 stem=QtGui.QPainterPath();stem.addRect(QtCore.QRectF(-42,-p.ArmWidth/2,42,p.ArmWidth))
 path=path.united(scale.map(stem))
 crop=QtGui.QPainterPath();crop.addRect(QtCore.QRectF(-36,-22,70,44));path=path.intersected(scale.map(crop))
 for x,y in motor_hole_offsets(p):
  h=QtGui.QPainterPath();h.addEllipse(QtCore.QPointF(x,y),p.MotorHoleDiameter/2,p.MotorHoleDiameter/2);path=path.subtracted(scale.map(h))
 h=QtGui.QPainterPath();h.addEllipse(QtCore.QPointF(0,0),p.MotorCenterDiameter/2,p.MotorCenterDiameter/2);path=path.subtracted(scale.map(h))
 path=scale.inverted()[0].map(path)
 image=QtGui.QImage(960,500,QtGui.QImage.Format_RGB888);image.fill(QtGui.QColor('white'))
 paint=QtGui.QPainter(image);paint.setRenderHint(QtGui.QPainter.Antialiasing);paint.translate(520,250);paint.scale(11,-11)
 paint.setPen(QtGui.QPen(QtGui.QColor('#183542'),.25));paint.setBrush(QtGui.QColor('#3b8f9f'));paint.drawPath(path)
 # A short dashed line marks the continuation into the arm without extra contours.
 paint.setPen(QtGui.QPen(QtGui.QColor('#728995'),.18,QtCore.Qt.DashLine));paint.drawLine(QtCore.QPointF(-36,-10),QtCore.QPointF(-36,10));paint.end()
 assert image.save(str(out/(name.replace(' ','_')+'.png')))
print('Rendered',len(MOTOR_PAD_SHAPES),'matching coloured motor pads')
