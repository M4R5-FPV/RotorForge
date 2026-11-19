"""Kernel-free plan of the front shoe from the finished bottom outline."""
from .airflow_gui import QtGui,QtCore,finished_part_path,polygon_path
from .front_bumper import toe_commands,shoulder_hull

def front_bumper_path(p):
 if not p.FlexFrontBumper or p.CameraCageStyle=='TPU cage':return QtGui.QPainterPath()
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
 shape='Rounded shoe' if p.FlexBumperVariant=='Integrated camera cage bumper' else p.FlexBumperShape
 if shape!='Follow bottom plate':
  half=p.FlexBumperWidth/2 if p.FlexBumperWidth else half
  hull=shoulder_hull([(v.x(),v.y()) for poly in outer.toSubpathPolygons() for v in poly],half,front+p.FlexBumperFit+p.FlexBumperWall,front-p.FlexBumperWall)
  outer=polygon_path(hull)
 commands=toe_commands(shape,half,front,p.FlexBumperFit+p.FlexBumperWall,p.FlexBumperProjection,p.FlexBumperTipWidth,p.FlexBumperRecess)
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
 return outer.united(camera_cover_plan(p,front,outer))


from functools import lru_cache


def front_bumper_plan(p):
 # Cache is GUI-only.
 return QtGui.QPainterPath(_front_bumper_plan_cached(p))


@lru_cache(maxsize=12)
def _front_bumper_plan_cached(p):
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
 return plan.united(camera_cover_plan(p,outline.boundingRect().bottom(),outer))


def camera_cover_plan(p,front,shoe=None):
 from .front_bumper import camera_cover_profiles
 path=QtGui.QPainterPath()
 for rail in camera_cover_profiles(p):
  upper=p.BottomThickness+p.FlexBumperFit+p.FlexBumperLip
  top=max(z for y,z in rail['points'])
  # Zero height reaches the top-plate underside.  No forced clearance gap.
  from .parameters import plate_levels
  blend=min(top,plate_levels(p)['top_z']) if p.FlexBumperCameraHeight==0 else min(top,plate_levels(p)['top_z'])
  ys=[]
  for profile in (rail['cheeks'],rail['points']):
   ys.extend(y for y,z in profile if z>=blend)
   for (ya,za),(yb,zb) in zip(profile,profile[1:]+profile[:1]):
    if (za-blend)*(zb-blend)<0:ys.append(ya+(yb-ya)*(blend-za)/(zb-za))
  if ys:
   # Top-view hint of the extra front TPU skin; the exact loft uses a
   # smooth height-dependent ramp rather than extending the lower shoe.
   rect=QtCore.QRectF(rail['xmin'],min(ys),rail['width'],max(ys)-min(ys)+p.FlexBumperCameraFrontProjection)
   path.addRoundedRect(rect,min(p.FlexBumperWall,rail['width']*.25),min(p.FlexBumperWall,rail['width']*.25))
  if shoe is not None:
   bounds=shoe.boundingRect();inner=rail['xmin']+rail['width'] if rail['xmin']<0 else rail['xmin']
   outside=bounds.left() if inner<0 else bounds.right()
   inward=abs(inner) if p.FlexBumperCameraBlendReach<=0 else p.FlexBumperCameraBlendReach
   inner=min(0.,inner+inward) if inner<0 else max(0.,inner-inward)
   x0=min(inner,outside);x1=max(inner,outside)
   y0=min(front-p.FlexBumperWall,rail['foot_y']-p.FlexBumperFit-p.FlexBumperCameraGripDepth)
   support=QtGui.QPainterPath();support.addRoundedRect(QtCore.QRectF(x0,y0,x1-x0,bounds.bottom()-y0),p.FlexBumperWall*.45,p.FlexBumperWall*.45)
   path=path.united(support.intersected(shoe))
 return path
