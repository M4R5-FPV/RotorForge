"""Fast plan schematic; exact boundaries are checked on Create/Update."""
from .airflow_gui import QtCore,QtGui,capsule_path
from .antenna_layout import antenna_layout,antenna_standoff_bore

def antenna_path(p):
 a=antenna_layout(p);path=QtGui.QPainterPath();pts=a['points']
 if p.FlexAntennaBarShape=='Rectangle':path.addRect(QtCore.QRectF(pts[0][0],pts[1][1]-a['width']/2,pts[2][0]-pts[0][0],p.FlexAntennaReach+a['width']))
 else:
  centreline=QtGui.QPainterPath();centreline.moveTo(*pts[0])
  for pt in pts[1:]:centreline.lineTo(*pt)
  stroker=QtGui.QPainterPathStroker();stroker.setWidth(a['width']);stroker.setCapStyle(QtCore.Qt.RoundCap);stroker.setJoinStyle(QtCore.Qt.RoundJoin)
  path=stroker.createStroke(centreline)
 for s in a['pair']:
  x,y=s['point'];r=antenna_standoff_bore(p)/2
  ring=QtGui.QPainterPath();ring.addEllipse(QtCore.QPointF(x,y),r+p.FlexAntennaGripWall,r+p.FlexAntennaGripWall)
  hole=QtGui.QPainterPath();hole.addEllipse(QtCore.QPointF(x,y),r,r);path=path.united(ring).subtracted(hole)
 for item in a['holders']:
  x,y,z=item['centre'];dx,dy,dz=item['axis'];length=a['length'];ax,ay,az=item['anchor'];apex=(0,a['pair'][0]['point'][1]-p.FlexAntennaReach);path=path.united(capsule_path(apex,(ax,ay),a['width']/2))
  if a['bulkhead']:
   # Project the tilted square tab; local horizontal axis is perpendicular to yaw.
   import math
   nx,ny=-dx*dy,1-dy*dy
   norm=math.sqrt(nx*nx+ny*ny+dz*dz*dy*dy)
   if norm>1e-8:nx,ny=nx/norm,ny/norm
   else:nx,ny=0.,0.
   r=a['radius']*.85;cx,cy=x+nx*r,y+ny*r
   gap=max(.2,(a['bore']-2*p.FlexAntennaRetainingLip)/5)
   path=path.subtracted(capsule_path((cx-dx*length/2,cy-dy*length/2),(cx+dx*length/2,cy+dy*length/2),gap/2))
 return path
