"""Editor-only 2D inspection of complete flat parts, without creating a document."""
from .appearance import CARBON_HEX,CARBON_EDGE,PAD_HEX,PAD_GROOVE,printed_hex,printed_groove,carbon_brush
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

def pad_carrier_path(p):
 """Fast 2-D LiPo source; keep hardware holes, optionally bridge airflow cuts.

 This is only a preview. The manufactured pad is built from exact OCC solids
 on Create / Update; it need not use the heavyweight 3-D construction here.
 """
 role=mounting_role(p)
 if p.LiPoPadCopyAirflow:return finished_part_path(p,role)
 from .cutouts import parse_patterns
 all_patterns=parse_patterns(p.CutoutPatterns)
 if not any(v['enabled'] and v['role']==role and v['mode']!='Add material'
            for v in all_patterns):
  return finished_part_path(p,role)
 # Avoid copying through-cuts, outline notches and pocket projections to the
 # grip pad. Material additions and all non-airflow structural holes remain.
 kept=[v for v in all_patterns if not
       (v['enabled'] and v['role']==role and v['mode']!='Add material')]
 return finished_part_path(p,role,kept)


def pad_path(p):
 path=QtGui.QPainterPath();w,l=p.LiPoPadWidth,p.LiPoPadLength
 if p.LiPoPadShape=='Mounting plate outline':
  carrier=pad_carrier_path(p)
  b=carrier.boundingRect()
  rear,front=pad_reach_bounds(p,b.top(),b.bottom());clip=QtGui.QPainterPath()
  if front>rear:clip.addRect(QtCore.QRectF(b.left()-1,rear,b.width()+2,front-rear))
  # No outline rescaling (the normal setting): use the already cached true
  # profile directly. Avoid a hugely tessellated Qt-to-polygons conversion
  # containing every airflow hole and mounting slot on each pad refresh.
  if p.LiPoPadOutlineWidthScale==100:
   return pad_clearance_path(p,carrier.intersected(clip))
  # For narrowed pads only, extract the outer loop. Interior holes keep their
  # original positions by intersecting the scaled loop with the real carrier.
  sampling=QtGui.QTransform();sampling.scale(20,20)
  polygons=carrier.toSubpathPolygons(sampling)
  def area(poly):
   pts=list(poly);return abs(sum(a.x()*b.y()-b.x()*a.y() for a,b in zip(pts,pts[1:]+pts[:1])))
  outer=max(polygons,key=area);path=QtGui.QPainterPath();path.addPolygon(outer);path.closeSubpath()
  inverse=QtGui.QTransform();inverse.scale(.05,.05);path=inverse.map(path)
  cx,cy=b.center().x(),b.center().y();t=QtGui.QTransform();t.translate(cx,cy);t.scale(p.LiPoPadOutlineWidthScale/100,1.);t.translate(-cx,-cy)
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
 if p.LiPoPadFollowPlate:path=path.intersected(pad_carrier_path(p))
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
 grooves=QtGui.QPainterPath()
 if p.LiPoPadPattern=='Solid':return grooves
 grooves.setFillRule(QtCore.Qt.WindingFill);box=path.boundingRect();bounds=grip_bounds(p,(box.left(),box.top(),box.right(),box.bottom()))
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
  try:
   path=part_path(p,role)
   if path.isEmpty():raise ValueError('Preview profile is empty for the current settings')
  except Exception as exc:
   painter.setPen(QtGui.QColor('#ad3d36'))
   painter.drawText(QtCore.QRectF(cell.x()+8,cell.y()+35,cell.width()-16,80),
                    QtCore.Qt.TextWordWrap,'Cannot draw '+role+': '+str(exc))
   continue
  # Each inspection role must show ONLY the requested manufactured part.
  # The cage side elevation already contains its through-opening; adding the
  # removable insert here concealed that opening and made both views identical.
  # A CameraPad view likewise shows only the removable pad, not the cage.
  b=path.boundingRect()
  short={'CameraMountLeft':'TPU cage L','CameraMountRight':'TPU cage R','CameraPadLeft':'Camera pad L','CameraPadRight':'Camera pad R'}
  label=(('TPU cage — left elevation' if role=='CameraMountLeft' else 'TPU cage — right elevation') if role in ('CameraMountLeft','CameraMountRight') and p.CameraCageStyle=='TPU cage' else short.get(role,ROLE_LABELS.get(role,'LiPo pad')))+(' (flat)' if role.startswith('Camera') and p.CameraCageStyle!='TPU cage' else '')
  painter.setPen(QtGui.QColor('#294554'));painter.drawText(QtCore.QRectF(cell.x(),cell.y(),cell.width(),25),QtCore.Qt.AlignCenter,label)
  scale=min((cw-24)/max(1,b.width()),(ch-40)/max(1,b.height()))
  painter.save();painter.translate(cell.center().x(),cell.center().y()+9);painter.scale(scale,-scale);painter.translate(-b.center().x(),-b.center().y())
  painter.setPen(QtGui.QPen(QtGui.QColor(CARBON_EDGE),.4));painter.setBrush(QtGui.QColor(printed_hex(p)) if role=='LiPoPad' or role.startswith(('CameraPad','MotorProtector','ElectronicsGuard','FrontBumper','RearAntennaMount','ELRSAntennaMount')) else carbon_brush(p,QtGui,role=role));painter.drawPath(path)
  if role in ('CameraMountLeft','CameraMountRight') and p.CameraCageStyle!='Carbon side plates':
   painter.fillPath(path,QtGui.QColor(printed_hex(p) if p.CameraCageStyle=='TPU cage' else '#adb2ba'))
  if role=='LiPoPad':
   try:painter.fillPath(grip_path(p,path),QtGui.QColor(printed_groove(p)))
   except ValueError:pass
  painter.restore()
