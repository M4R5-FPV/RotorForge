"""Kernel-free plan of the front shoe from the finished bottom outline."""
from .airflow_gui import QtGui,QtCore,finished_part_path,polygon_path
from .front_bumper import toe_commands,shoulder_hull

def front_bumper_path(p):
 if not p.FlexFrontBumper:return QtGui.QPainterPath()
 plate=finished_part_path(p,'BottomPlate');polygons=plate.toSubpathPolygons()
 def area(poly):
  points=list(poly);return abs(sum(a.x()*b.y()-b.x()*a.y() for a,b in zip(points,points[1:]+points[:1])))
 if not polygons:return QtGui.QPainterPath()
 outline=QtGui.QPainterPath();outline.addPolygon(max(polygons,key=area));outline.closeSubpath()
 front=outline.boundingRect().bottom();rear=front-p.FlexBumperReach
 scale=QtGui.QTransform();scale.scale(100,100);stroke=QtGui.QPainterPathStroker();stroke.setWidth(200*(p.FlexBumperFit+p.FlexBumperWall));stroke.setJoinStyle(QtCore.Qt.RoundJoin)
 outer=scale.inverted()[0].map(scale.map(outline).united(stroke.createStroke(scale.map(outline))))
 clip=QtGui.QPainterPath();clip.addRect(QtCore.QRectF(-1000,rear,2000,2000));outer=outer.intersected(clip)
 box=outer.boundingRect();half=max(abs(box.left()),abs(box.right()))
 if p.FlexBumperShape!='Follow bottom plate':
  half=p.FlexBumperWidth/2 if p.FlexBumperWidth else half
  hull=shoulder_hull([(v.x(),v.y()) for poly in outer.toSubpathPolygons() for v in poly],half,front+p.FlexBumperFit+p.FlexBumperWall,front-p.FlexBumperWall)
  outer=polygon_path(hull)
 commands=toe_commands(p.FlexBumperShape,half,front,p.FlexBumperFit+p.FlexBumperWall,p.FlexBumperProjection,p.FlexBumperTipWidth,p.FlexBumperRecess)
 if commands:
  toe=QtGui.QPainterPath()
  for item in commands:
   if item[0]=='M':toe.moveTo(*item[1])
   elif item[0]=='L':toe.lineTo(*item[1])
   else:toe.cubicTo(*(v for pt in item[1:] for v in pt))
  toe.closeSubpath();outer=outer.united(toe)
 from .parameters import plate_holes
 for pt,r,label in plate_holes(p,'BottomPlate'):
  tool=QtGui.QPainterPath();tool.addEllipse(QtCore.QPointF(*pt),max(3.,r)+p.FlexBumperFit,max(3.,r)+p.FlexBumperFit);outer=outer.subtracted(tool)
 return outer


def front_bumper_plan(p):
 """Upper wall/lip view: keep the carbon visible inside the shoe."""
 outer=front_bumper_path(p)
 if outer.isEmpty():return outer
 plate=finished_part_path(p,'BottomPlate');polygons=plate.toSubpathPolygons()
 def area(poly):
  points=list(poly);return abs(sum(a.x()*b.y()-b.x()*a.y() for a,b in zip(points,points[1:]+points[:1])))
 outline=QtGui.QPainterPath();outline.addPolygon(max(polygons,key=area));outline.closeSubpath()
 scale=QtGui.QTransform();scale.scale(100,100);large=scale.map(outline)
 stroke=QtGui.QPainterPathStroker();stroke.setWidth(200*p.FlexBumperOverlap);stroke.setJoinStyle(QtCore.Qt.RoundJoin)
 inner=scale.inverted()[0].map(large.subtracted(stroke.createStroke(large)))
 plan=outer.subtracted(inner)
 if p.FlexBumperLipReach:
  rear=outline.boundingRect().bottom()-p.FlexBumperReach
  limit=outline.boundingRect().bottom()-p.FlexBumperLipReach
  if limit>rear:
   # Only the retaining overlap disappears; the outside edge wall remains.
   remove=outline.intersected(polygon_path(((-1000,rear-1),(1000,rear-1),(1000,limit),(-1000,limit))))
   plan=plan.subtracted(remove)
 return plan
