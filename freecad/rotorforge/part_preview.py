"""Editor-only 2D inspection of complete flat parts, without creating a document."""
from .appearance import CARBON_HEX,CARBON_EDGE,PAD_HEX,PAD_GROOVE,printed_hex,printed_groove
import math
from .airflow_gui import (QtCore,QtGui,finished_part_path,capsule_path,ROLE_LABELS)
from .parameters import three_plate,arm_braces,upper_clamp_active,keystone_active,underside_clamp_active,arm_layouts
from .battery import battery_point,mounting_role,groove_segments,pad_polygon,pad_reach_bounds,pad_standoff_clearance,grip_bounds,grip_point

def preview_roles(p):
 roles=['BottomPlate']+(['MidPlate'] if three_plate(p) else [])+['TopPlate']
 roles+=['Arm'+a['name'] for a in arm_layouts(p)]
 if upper_clamp_active(p):roles.append('ArmClampPlate')
 if underside_clamp_active(p):roles.append('ArmLowerClampPlate')
 if keystone_active(p):roles.append('ArmKeystone')
 if p.FPVEnabled:roles+=['CameraMountLeft','CameraMountRight']
 if p.LiPoPadEnabled:roles.append('LiPoPad')
 from .flex import flex_roles
 roles+=list(flex_roles(p))
 return roles

def pad_clearance_path(p,path):
 from .parameters import standoff_layouts
 for stand in standoff_layouts(p):
  x,y=stand['point'];r=pad_standoff_clearance(p);tool=QtGui.QPainterPath();tool.addEllipse(QtCore.QRectF(x-r,y-r,2*r,2*r));path=path.subtracted(tool)
 return path

def pad_path(p):
 path=QtGui.QPainterPath();w,l=p.LiPoPadWidth,p.LiPoPadLength
 if p.LiPoPadShape=='Mounting plate outline':
  carrier=finished_part_path(p,mounting_role(p))
  # Resolve the outer loop at high sampling scale; leave real carrier holes fixed.
  sampling=QtGui.QTransform();sampling.scale(20,20)
  polygons=carrier.toSubpathPolygons(sampling)
  def area(poly):
   pts=list(poly);return abs(sum(a.x()*b.y()-b.x()*a.y() for a,b in zip(pts,pts[1:]+pts[:1])))
  outer=max(polygons,key=area);path=QtGui.QPainterPath();path.addPolygon(outer);path.closeSubpath()
  inverse=QtGui.QTransform();inverse.scale(.05,.05);path=inverse.map(path)
  b=carrier.boundingRect();cx,cy=b.center().x(),b.center().y();t=QtGui.QTransform();t.translate(cx,cy);t.scale(p.LiPoPadOutlineWidthScale/100,1.);t.translate(-cx,-cy)
  rear,front=pad_reach_bounds(p,b.top(),b.bottom());clip=QtGui.QPainterPath()
  if front>rear:clip.addRect(QtCore.QRectF(b.left()-1,rear,b.width()+2,front-rear))
  return pad_clearance_path(p,t.map(path).intersected(carrier).intersected(clip))
 if pad_polygon(p):
  pts=pad_polygon(p);path.moveTo(*pts[0])
  for pt in pts[1:]:path.lineTo(*pt)
  path.closeSubpath()
 elif p.LiPoPadShape=='Ellipse':path.addEllipse(QtCore.QRectF(-w/2,-l/2,w,l))
 elif p.LiPoPadShape=='Capsule':
  d=abs(l-w);a,b=((0,-d/2),(0,d/2)) if l>=w else ((-d/2,0),(d/2,0))
  path=capsule_path(a,b,min(w,l)/2)
 elif p.LiPoPadShape=='Rectangle':path.addRect(QtCore.QRectF(-w/2,-l/2,w,l))
 else:path.addRoundedRect(QtCore.QRectF(-w/2,-l/2,w,l),p.LiPoPadCornerRadius,p.LiPoPadCornerRadius)
 t=QtGui.QTransform();t.translate(p.BatteryX,p.BatteryY);t.rotate(p.BatteryRotation);path=t.map(path)
 if p.LiPoPadFollowPlate:path=path.intersected(finished_part_path(p,mounting_role(p)))
 return pad_clearance_path(p,path)

def part_path(p,role,align=True):
 from .flex_options import FLEX_ROLES
 if role in FLEX_ROLES:
  from .flex_preview import flex_path
  return flex_path(p,role)
 path=pad_path(p) if role=='LiPoPad' else finished_part_path(p,role)
 if align and role.startswith('Arm') and role not in ('ArmClampPlate','ArmLowerClampPlate','ArmKeystone'):
  arm=next(a for a in arm_layouts(p) if 'Arm'+a['name']==role)
  t=QtGui.QTransform();t.rotate(90-math.degrees(math.atan2(arm['unit'][1],arm['unit'][0])));path=t.map(path)
 return path

def grip_path(p,path):
 grooves=QtGui.QPainterPath();grooves.setFillRule(QtCore.Qt.WindingFill);box=path.boundingRect();bounds=grip_bounds(p,(box.left(),box.top(),box.right(),box.bottom()))
 for a,b in groove_segments(p,bounds):grooves.addPath(capsule_path(grip_point(p,*a),grip_point(p,*b),p.LiPoPadGrooveWidth/2))
 # Qt boolean flattening is screen-scale dependent; enlarge before clipping small dots.
 scale=QtGui.QTransform();scale.scale(40,40);inverse=QtGui.QTransform();inverse.scale(.025,.025)
 return inverse.map(scale.map(grooves).intersected(scale.map(path)))

def draw_parts(painter,rect,p,selected):
 roles=preview_roles(p)
 if selected=='Arms':roles=[r for r in roles if r in ('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight')]
 elif selected!='AllParts':roles=[selected] if selected in roles else []
 if not roles:return
 maxcols=max(2,int(rect.width()/140));rows=math.ceil(len(roles)/maxcols);cols=math.ceil(len(roles)/rows) if len(roles)>1 else 1
 cw,ch=rect.width()/cols,rect.height()/rows
 for i,role in enumerate(roles):
  cell=QtCore.QRectF(rect.x()+i%cols*cw,rect.y()+i//cols*ch,cw,ch)
  path=part_path(p,role);b=path.boundingRect()
  short={'CameraMountLeft':'Camera plate L','CameraMountRight':'Camera plate R','CameraPadLeft':'Camera pad L','CameraPadRight':'Camera pad R'}
  label=short.get(role,ROLE_LABELS.get(role,'LiPo pad'))+(' (flat)' if role.startswith('Camera') else '')
  painter.setPen(QtGui.QColor('#294554'));painter.drawText(QtCore.QRectF(cell.x(),cell.y(),cell.width(),25),QtCore.Qt.AlignCenter,label)
  scale=min((cw-24)/max(1,b.width()),(ch-40)/max(1,b.height()))
  painter.save();painter.translate(cell.center().x(),cell.center().y()+9);painter.scale(scale,-scale);painter.translate(-b.center().x(),-b.center().y())
  painter.setPen(QtGui.QPen(QtGui.QColor(CARBON_EDGE),.4));painter.setBrush(QtGui.QColor(printed_hex(p)) if role=='LiPoPad' or role.startswith(('CameraPad','MotorProtector','ElectronicsGuard','FrontBumper')) else QtGui.QColor(CARBON_HEX));painter.drawPath(path)
  if role=='LiPoPad':
   try:painter.fillPath(grip_path(p,path),QtGui.QColor(printed_groove(p)))
   except ValueError:pass
  painter.restore()
