"""Lightweight top-view schematic, with open hooks indicated."""
from .airflow_gui import QtCore,QtGui,capsule_path
from .elrs_layout import elrs_layout,elrs_bore

def elrs_path(p):
 a=elrs_layout(p);pts=a['points'];w=p.FlexELRSBarWidth
 path=QtGui.QPainterPath()
 if p.FlexELRSBarShape=='Rectangle':path.addRect(QtCore.QRectF(pts[0][0],a['bar_y']-w/2,pts[2][0]-pts[0][0],a['rear']-a['bar_y']+w))
 else:
  centre=QtGui.QPainterPath();centre.moveTo(*pts[0])
  for pt in pts[1:]:centre.lineTo(*pt)
  stroke=QtGui.QPainterPathStroker();stroke.setWidth(w);stroke.setCapStyle(QtCore.Qt.RoundCap);stroke.setJoinStyle(QtCore.Qt.RoundJoin);path=stroke.createStroke(centre)
 path=path.united(capsule_path((-p.FlexELRSHookSpacing/2,a['bar_y']),(p.FlexELRSHookSpacing/2,a['bar_y']),w/2))
 for s in a['pair']:
  c=QtCore.QPointF(*s['point']);r=elrs_bore(p)/2;ring=QtGui.QPainterPath();ring.addEllipse(c,r+p.FlexELRSGripWall,r+p.FlexELRSGripWall);hole=QtGui.QPainterPath();hole.addEllipse(c,r,r);path=path.united(ring).subtracted(hole)
 for x,y,z in a['hooks']:
  if p.FlexELRSHookReach>0:
   size=a['support_size'];rib=QtGui.QPainterPath();radius=min(.6,size*.15)
   rib.addRoundedRect(QtCore.QRectF(x-size/2,y,size,a['bar_y']-y+size/2),radius,radius)
   path=path.united(rib)
  hook=QtGui.QPainterPath();hook.addRect(QtCore.QRectF(x-p.FlexELRSHookWidth/2,y-a['radius'],p.FlexELRSHookWidth,2*a['radius']))
  gap=p.FlexELRSAntennaDiameter-2*p.FlexELRSRetainingLip
  opening=QtGui.QPainterPath();opening.addRect(QtCore.QRectF(x-p.FlexELRSHookWidth/2,y-gap/2,p.FlexELRSHookWidth,gap))
  path=path.united(hook).subtracted(opening)
 return path
