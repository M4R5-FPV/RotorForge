"""Bounded-cost schematics from the portable layout; no solid kernel imports."""
import math
from .airflow_gui import QtCore,QtGui,capsule_path
from .flex import insert_rect,camera_interface_polygon
from .fpv import camera_mounts,camera_pivot_height

def camera_interface_path(p,w,h,lip=0.):
 from .camera_interface import profile_corners
 path=QtGui.QPainterPath();cy,cz,_,_=insert_rect(p);corners=profile_corners(p,w,h)
 def local(v):return (v[0]-cy,v[1]-p.BottomThickness)
 path.moveTo(*local(corners[-1]['end']))
 for corner in corners:
  path.lineTo(*local(corner['start']))
  if corner['radius']:path.cubicTo(*local(corner['c1']),*local(corner['c2']),*local(corner['end']))
 path.closeSubpath()
 if lip:
  scale=QtGui.QTransform();scale.scale(100,100);large=scale.map(path)
  stroke=QtGui.QPainterPathStroker();stroke.setWidth(200*lip);stroke.setJoinStyle(QtCore.Qt.RoundJoin)
  path=scale.inverted()[0].map(large.united(stroke.createStroke(large)))
 return path

def flex_path(p,role):
 if role=='FrontBumper':
  from .bumper_preview import front_bumper_path
  return front_bumper_path(p)
 path=QtGui.QPainterPath()
 if role.startswith('CameraPad'):
  _,cz,w,h=insert_rect(p)
  if p.FlexCameraMode=='Captured inserts':path=camera_interface_path(p,w,h,p.FlexInsertLip)
  else:path=camera_interface_path(p,p.FlexPadWidth,p.FlexPadHeight)
  mount=camera_mounts(p)[0];cy=insert_rect(p)[0]
  for y,z in mount['side_holes']:
   hole=QtGui.QPainterPath();hole.addEllipse(QtCore.QPointF(y-cy,z-p.BottomThickness),p.CameraSideHoleDiameter/2,p.CameraSideHoleDiameter/2);path=path.subtracted(hole)
  for arc in mount['side_arcs']:
   pts=[(arc['centre'][0]-cy+arc['radius']*math.cos(math.radians(arc['start']+(arc['end']-arc['start'])*i/24)),arc['centre'][1]-p.BottomThickness+arc['radius']*math.sin(math.radians(arc['start']+(arc['end']-arc['start'])*i/24))) for i in range(25)]
   for a,b in zip(pts,pts[1:]):path=path.subtracted(capsule_path(a,b,arc['width']/2))
  return path
 if role.startswith('MotorProtector'):
  from .parameters import arm_layouts
  from .airflow_gui import motor_pad_path
  from .motor_pads import motor_pad_unit
  arm=next(a for a in arm_layouts(p) if role=='MotorProtector'+a['name']);ux,uy=motor_pad_unit(p,arm)
  t=QtGui.QTransform();t.translate(*arm['motor']);t.rotate(math.degrees(math.atan2(uy,ux)))
  pad=t.map(motor_pad_path(p));stroke=QtGui.QPainterPathStroker();stroke.setWidth(2*(p.FlexProtectorFit+p.FlexProtectorWall));path=pad.united(stroke.createStroke(pad))
  from .protection_layout import motor_service_slots
  for a,b,r in motor_service_slots(p,arm):path=path.subtracted(capsule_path(a,b,r))
  for x,y in arm['motor_holes']:
   hole=QtGui.QPainterPath();radius=p.MotorHoleDiameter/2+.15 if p.FlexProtectorRetention=='Motor screws' else max(3.,p.MotorHoleDiameter/2+.2);hole.addEllipse(QtCore.QPointF(x,y),radius,radius);path=path.subtracted(hole)
  hole=QtGui.QPainterPath();hole.addEllipse(QtCore.QPointF(*arm['motor']),p.MotorCenterDiameter/2+.4,p.MotorCenterDiameter/2+.4);return path.subtracted(hole)
 if role.startswith('ElectronicsGuard'):
  from .protection_layout import guard_layout,guard_vents,usb_window,vent_polygon,guard_wire_openings,guard_strap_windows,guard_vtx_window
  g=next(i for i in guard_layout(p) if i['role']==role);lo=g['rear']+p.FlexGuardRearInset;hi=g['front']-p.FlexGuardFrontInset
  path.addRect(QtCore.QRectF(lo,g['z'],hi-lo,g['top']-g['z']))
  from .parameters import three_plate,mid_bounds
  if three_plate(p):
   end=mid_bounds(p)[1]
   if end<hi:
    absent=QtGui.QPainterPath();absent.addRect(QtCore.QRectF(max(lo,end),g['z'],hi-max(lo,end),max(0.,g['inner_top']-10-g['z'])))
    path=path.subtracted(absent)
  from .protection_layout import closure_profile
  closure=closure_profile(p,g)
  if closure:
   points=[(start,z) for start,(z,end) in zip(closure['starts'],closure['sections'])]+[(end,z) for z,end in reversed(closure['sections'])]
   panel=QtGui.QPainterPath();panel.moveTo(*points[0])
   for point in points[1:]:panel.lineTo(*point)
   panel.closeSubpath();path=path.united(panel)
  radius=(p.StandoffDiameter+p.FlexGuardFit)/2+p.FlexGuardWall
  for stand,(low,high) in zip(g['stands'],g['bands']):
   bearing=QtGui.QPainterPath();bearing.addRect(QtCore.QRectF(stand['point'][1]-radius,low,2*radius,high-low));path=path.united(bearing)
  for vent in guard_vents(p,g):
   tool=QtGui.QPainterPath();y,z,w,h=vent['y'],vent['z'],vent['width'],vent['height'];poly=vent_polygon(vent)
   if poly:
    tool.moveTo(y+poly[0][0],z+poly[0][1])
    for dy,dz in poly[1:]:tool.lineTo(y+dy,z+dz)
    tool.closeSubpath()
   elif vent['shape']=='Ellipses':tool.addEllipse(QtCore.QRectF(y-w/2,z-h/2,w,h))
   elif vent['shape']=='Rounded slots':tool.addRoundedRect(QtCore.QRectF(y-w/2,z-h/2,w,h),min(w,h)/2,min(w,h)/2)
   else:tool.addRect(QtCore.QRectF(y-w/2,z-h/2,w,h))
   path=path.subtracted(tool)
  if closure:
   mount=next(m for m in camera_mounts(p) if m['role'].endswith('Left' if g['sign']<0 else 'Right'))
   for y,z in mount['side_holes']:
    tool=QtGui.QPainterPath();tool.addEllipse(QtCore.QPointF(y,z),p.CameraSideHoleDiameter/2+.2,p.CameraSideHoleDiameter/2+.2);path=path.subtracted(tool)
   for arc in mount['side_arcs']:
    pts=[(arc['centre'][0]+arc['radius']*math.cos(math.radians(arc['start']+(arc['end']-arc['start'])*i/24)),arc['centre'][1]+arc['radius']*math.sin(math.radians(arc['start']+(arc['end']-arc['start'])*i/24))) for i in range(25)]
    for a,b in zip(pts,pts[1:]):path=path.subtracted(capsule_path(a,b,(arc['width']+.4)/2))
  for opening in guard_wire_openings(p,g):
   y,w,h,bottom=opening['y'],opening['width'],opening['height'],opening['bottom'];radius=min(1.,w/4,h/4)
   tool=QtGui.QPainterPath();tool.addRoundedRect(QtCore.QRectF(y-w/2,bottom-2,w,h+2),radius,radius)
   if opening['name']=='Front':
    protected=QtGui.QPainterPath();keep=(p.StandoffDiameter+p.FlexGuardFit)/2+p.FlexGuardWall+.8
    for stand,(low,high) in zip(g['stands'],g['bands']):protected.addRect(QtCore.QRectF(stand['point'][1]-keep,low-.8,2*keep,high-low+1.6))
    tool=tool.subtracted(protected)
   path=path.subtracted(tool)
  for opening in guard_strap_windows(p,g):
   tool=QtGui.QPainterPath();w=opening['width'];h=opening['height'];radius=min(1.,w/4,p.FlexGuardStrapDepth/4)
   tool.addRoundedRect(QtCore.QRectF(opening['y']-w/2,opening['bottom'],w,h),radius,radius);path=path.subtracted(tool)
  for window in (usb_window(p,g),guard_vtx_window(p,g)):
   if not window:continue
   y,z,w,h=window;tool=QtGui.QPainterPath();tool.addRoundedRect(QtCore.QRectF(y-w/2,z-h/2,w,h),1,1);path=path.subtracted(tool)
  return path
 return path

from functools import lru_cache

@lru_cache(maxsize=48)
def _guard_plan_cached(p,role):
 from .airflow_gui import finished_part_path
 from .protection_layout import guard_layout,grip_bridge,outline_side_x,guard_between_plates,guard_wall_inner_x
 g=next(g for g in guard_layout(p) if g['role']==role)
 clip=QtGui.QPainterPath();clip.addRect(QtCore.QRectF(0 if g['sign']>0 else -1000,g['rear'],1000,g['front']-g['rear']))
 result=QtGui.QPainterPath();contours={}
 for carrier in ('TopPlate',g['lower_role']):
  # A side wall follows the outer edge, not every drill/airflow opening. Stroking
  # all inner loops produced false islands and costly repeated path booleans.
  plate=finished_part_path(p,carrier,include_strap_notches=False);scale=QtGui.QTransform();scale.scale(20,20)
  loops=plate.toSubpathPolygons(scale)
  if not loops:continue
  def area(poly):return abs(sum(a.x()*b.y()-b.x()*a.y() for a,b in zip(poly,list(poly)[1:]+[poly[0]])))
  polygon=max(loops,key=area);contours[carrier]=[(v.x()/20,v.y()/20) for v in polygon]
  contour=QtGui.QPainterPath();contour.addPolygon(polygon);contour.closeSubpath();plate=scale.inverted()[0].map(contour)
  if guard_between_plates(p):continue
  stroke=QtGui.QPainterPathStroker();stroke.setWidth(2*(p.FlexGuardClearance+p.FlexGuardWall));outer=plate.united(stroke.createStroke(plate))
  inner=QtGui.QPainterPath(plate)
  # Qt treats a zero stroker width as its default width, not as no offset.
  if p.FlexGuardClearance>0:
   inset=QtGui.QPainterPathStroker();inset.setWidth(2*p.FlexGuardClearance);inner=plate.united(inset.createStroke(plate))
  result=result.united(outer.subtracted(inner))
 if guard_between_plates(p):
  # Project the inset ruled wall, including different upper/lower widths.
  lo=g['rear']+p.FlexGuardRearInset;hi=g['front']-p.FlexGuardFrontInset;sign=g['sign']
  ys={lo,hi};ys.update(lo+(hi-lo)*i/max(1,int((hi-lo)/2)+1) for i in range(1,max(1,int((hi-lo)/2)+1)))
  ys.update(y for points in contours.values() for x,y in points if lo<y<hi)
  inside=[];outside=[]
  for y in sorted(ys):
   xt=outline_side_x(contours.get('TopPlate',[]),y,sign);xb=outline_side_x(contours.get(g['lower_role'],[]),y,sign)
   if xt is None:continue
   if xb is None:xb=xt
   a=sign*guard_wall_inner_x(p,xb,sign);b=sign*guard_wall_inner_x(p,xt,sign)
   inside.append((sign*min(a,b),y));outside.append((sign*(max(a,b)+p.FlexGuardWall),y))
  points=inside+outside[::-1]
  if points:
   result.moveTo(*points[0])
   for point in points[1:]:result.lineTo(*point)
   result.closeSubpath()
 result=result.intersected(clip)
 radius=(p.StandoffDiameter+p.FlexGuardFit)/2+p.FlexGuardWall;sign=g['sign']
 for stand in g['stands']:
  sx,sy=stand['point'];wall_y=max(g['rear']+p.FlexGuardRearInset,min(g['front']-p.FlexGuardFrontInset,sy))
  xt=outline_side_x(contours.get('TopPlate',[]),wall_y,sign);xb=outline_side_x(contours.get(g['lower_role'],[]),wall_y,sign)
  if xt is None:continue
  if xb is None:xb=xt
  a,b,r=grip_bridge(p,g,stand,(wall_y,guard_wall_inner_x(p,xb,sign),guard_wall_inner_x(p,xt,sign),0))
  grip=QtGui.QPainterPath();grip.addEllipse(QtCore.QPointF(sx,sy),radius,radius)
  bridge=capsule_path(a,b,r);half=QtGui.QPainterPath();half.addRect(QtCore.QRectF(sx if sign>0 else sx-1000,-500,1000,1000))
  result=result.united(grip).united(bridge.intersected(half))
 from .protection_layout import closure_profile
 closure=closure_profile(p,g)
 if closure:
  from .parameters import Parameters
  # Bottom silhouette is needed only for the optional full-height front panel.
  plate=finished_part_path(p,'BottomPlate');polys=plate.toSubpathPolygons()
  if polys:
   polygon=max(polys,key=lambda a:abs(sum(u.x()*v.y()-v.x()*u.y() for u,v in zip(a,list(a)[1:]+[a[0]]))))
   contours['BottomPlate']=[(v.x(),v.y()) for v in polygon]
  for start,(z,end) in zip(closure['starts'],closure['sections']):
   low=closure['sections'][0][0];high=closure['sections'][-1][0];t=(z-low)/(high-low);points=[]
   for i in range(13):
    y=start+(end-start)*i/12
    xb=outline_side_x(contours.get('BottomPlate',[]),y,sign);xt=outline_side_x(contours.get('TopPlate',[]),y,sign)
    if xb is None:xb=outline_side_x(contours.get('BottomPlate',[]),min(y,closure['sections'][0][1]),sign)
    if xt is None:xt=outline_side_x(contours.get('TopPlate',[]),min(y,closure['sections'][-1][1]),sign)
    if xb is None or xt is None:continue
    x=guard_wall_inner_x(p,xb*(1-t)+xt*t,sign);b=max(0.,min(1.,(y-(end-14))/14));b=b*b*(3-2*b)
    points.append((x*(1-b)+closure['x']*b,y))
   if len(points)<2:continue
   polygon=points+[(x+sign*p.FlexGuardWall,y) for x,y in points[::-1]]
   panel=QtGui.QPainterPath();panel.moveTo(*polygon[0])
   for point in polygon[1:]:panel.lineTo(*point)
   panel.closeSubpath();result=result.united(panel)
 for stand in g['stands']:
  bore=QtGui.QPainterPath();bore.addEllipse(QtCore.QPointF(*stand['point']),(p.StandoffDiameter+p.FlexGuardFit)/2,(p.StandoffDiameter+p.FlexGuardFit)/2);result=result.subtracted(bore)
 return result

def guard_plan_path(p,g):
 from dataclasses import replace
 from .parameters import Parameters
 defaults=Parameters()
 inactive={name:getattr(defaults,name) for name in p.__dataclass_fields__ if name.startswith(('FlexGuardWire','FlexGuardUSB','FlexGuardVent','FlexGuardSlot','FlexGuardVTX','FlexGuardFC','FlexProtector')) or name in ('FlexGuardStyle','FlexMotorProtectors','PrintedPartColour')}
 return QtGui.QPainterPath(_guard_plan_cached(replace(p,**inactive),g['role']))
