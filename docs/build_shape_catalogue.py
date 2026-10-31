"""Engineering illustrations generated from the same portable editor paths."""
from pathlib import Path
import sys,json,math
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from freecad.rotorforge.parameters import Parameters,arm_layouts,motor_hole_offsets,plate_holes
from freecad.rotorforge.design_options import ARM_BEAM_SHAPES,MOTOR_PAD_RELIEFS
from freecad.rotorforge.motor_pads import NEW_MOTOR_PAD_SHAPES
from freecad.rotorforge.battery import GRIP_PATTERNS
from freecad.rotorforge.airflow_gui import QtGui,QtCore,QtWidgets,arm_blank_path,motor_pad_path,profile_path,polygon_path
from freecad.rotorforge.part_preview import pad_path,grip_path
app=QtWidgets.QApplication([]);d=ROOT/'docs'
def gallery(name,items,pathfn,cols,cellw=640,cellh=210):
 rows=math.ceil(len(items)/cols);im=QtGui.QImage(cols*cellw,rows*cellh,QtGui.QImage.Format_RGB888);im.fill(QtGui.QColor('white'))
 q=QtGui.QPainter(im);q.setRenderHint(QtGui.QPainter.Antialiasing)
 for i,item in enumerate(items):
  path=pathfn(item);box=path.boundingRect();x=(i%cols)*cellw;y=(i//cols)*cellh;scale=min((cellw-60)/box.width(),(cellh-65)/box.height())
  q.save();q.translate(x+cellw/2,y+(cellh-35)/2);q.scale(scale,-scale);q.translate(-box.center().x(),-box.center().y());q.setPen(QtGui.QPen(QtGui.QColor('#183542'),1.5/scale));q.setBrush(QtGui.QColor('#3b8f9f'));q.drawPath(path);q.restore()
  q.setPen(QtGui.QColor('#183542'));font=q.font();font.setPixelSize(25);q.setFont(font);q.drawText(QtCore.QRectF(x,y+cellh-36,cellw,32),QtCore.Qt.AlignCenter,item)
 q.end();im.save(str(d/name))
def arm(name):
 p=Parameters(ArmBeamShape=name,ArmProfileAmount=65);a=arm_layouts(p)[0];t=QtGui.QTransform();t.rotate(-math.degrees(math.atan2(a['unit'][1],a['unit'][0])))
 return t.map(arm_blank_path(p,a))
gallery('ArmBeamOptions.png',ARM_BEAM_SHAPES,arm,2)
gallery('MotorPadReliefs.png',MOTOR_PAD_RELIEFS,lambda n:motor_pad_path(Parameters(MotorPadShape='Round-shoulder shield',MotorPadRelief=n)),4,500,300)
g=d/'grip_catalogue';g.mkdir(exist_ok=True)
for name in GRIP_PATTERNS:
 p=Parameters(LiPoPadEnabled=True,LiPoPadFollowPlate=False,LiPoPadWidth=32,LiPoPadLength=65,LiPoPadGroovePitch=7,LiPoPadPattern=name)
 path=pad_path(p);grooves=grip_path(p,path)
 im=QtGui.QImage(420,420,QtGui.QImage.Format_RGB888);im.fill(QtGui.QColor('white'));q=QtGui.QPainter(im);q.setRenderHint(QtGui.QPainter.Antialiasing);q.translate(210,210);q.scale(5.8,-5.8)
 q.setPen(QtGui.QPen(QtGui.QColor('#183542'),.35));q.setBrush(QtGui.QColor('#3b8f9f'));q.drawPath(path);q.setPen(QtCore.Qt.NoPen);q.setBrush(QtGui.QColor('#d7e9ee'));q.drawPath(grooves);q.end();im.save(str(g/(name.replace(' ','_')+'.png')))
