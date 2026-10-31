"""One visual language for all RotorForge technical guide illustrations."""
from pathlib import Path
import sys,math
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from freecad.rotorforge.airflow_gui import QtGui,QtCore,QtWidgets,polygon_path
INK='#222529';BLUE='#2e3033';LIGHT='#999c9f';TPU='#17191c';TEAL='#269c9b';GOLD='#e5b05b';GREY='#9eacb7';PALE='#f0f1f2';LINE='#d4d6d8';WHITE='#ffffff'
app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([]);app.setFont(QtGui.QFont('DejaVu Sans',10))
def rect(x,y,w,h):
 p=QtGui.QPainterPath();p.addRect(QtCore.QRectF(x,y,w,h));return p
def ellipse(x,y,rx,ry=None):
 p=QtGui.QPainterPath();p.addEllipse(QtCore.QPointF(x,y),rx,rx if ry is None else ry);return p
def shifted(path,x,y):
 t=QtGui.QTransform();t.translate(x,y);return t.map(path)
def cell(title,*items,box=None):return dict(title=title,items=list(items),box=box)
def gallery(filename,cells,cols=2,rowheight=520,cellwidth=800,labels=True):
 rows=math.ceil(len(cells)/cols);image=QtGui.QImage(cols*cellwidth,rows*rowheight,QtGui.QImage.Format_RGB888);image.fill(QtGui.QColor(WHITE));q=QtGui.QPainter(image);q.setRenderHint(QtGui.QPainter.Antialiasing)
 for i,c in enumerate(cells):
  x=i%cols*cellwidth;y=i//cols*rowheight
  if labels and c['title']:
   font=QtGui.QFont('DejaVu Sans');font.setPixelSize(26);q.setFont(font);q.setPen(QtGui.QColor(INK));q.drawText(QtCore.QRectF(x+16,y+8,cellwidth-32,64),QtCore.Qt.AlignCenter,c['title'])
  items=c['items'];bounds=c.get('box')
  if bounds is None:
   bounds=QtCore.QRectF()
   for path,*_ in items:bounds=bounds.united(path.boundingRect())
  scale=min((cellwidth-95)/max(bounds.width(),1),(rowheight-115)/max(bounds.height(),1))
  q.save();q.translate(x+cellwidth/2,y+(rowheight+60)/2);q.scale(scale,-scale);q.translate(-bounds.center().x(),-bounds.center().y())
  for item in items:
   path,fill,*rest=item;stroke=rest[0] if rest else INK
   q.setPen(QtGui.QPen(QtGui.QColor(stroke),1.6/scale));q.setBrush(QtGui.QColor(fill) if fill else QtCore.Qt.NoBrush);q.drawPath(path)
  q.restore()
 q.end();target=ROOT/'docs'/filename;target.parent.mkdir(parents=True,exist_ok=True);assert image.save(str(target))
 return target
