"""Editor-only 2D inspection of complete flat parts, without creating a document."""
from .appearance import CARBON_HEX,CARBON_EDGE,PAD_HEX,PAD_GROOVE,printed_hex,printed_groove,carbon_brush
import math
from time import perf_counter
from functools import lru_cache
from .airflow_gui import (QtCore,QtGui,finished_part_path,capsule_path,ROLE_LABELS)
from .preview_acceleration import LocalPathContains
from .pad_preview_rounding import cleaned_core
from .parameters import three_plate,arm_braces,upper_clamp_active,keystone_active,underside_clamp_active,arm_layouts
from .battery import battery_point,mounting_role,groove_segments,pad_polygon,pad_reach_bounds,pad_standoff_clearance,grip_bounds,grip_point,pad_flush_seats,pad_fastener_clearances,pad_rounding_radii,lip_sides

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
 for x,y,r in pad_fastener_clearances(p):
  bounds=QtCore.QRectF(x-r,y-r,2*r,2*r)
  if not path.boundingRect().intersects(bounds):continue
  tool=QtGui.QPainterPath();tool.addEllipse(bounds);path=path.subtracted(tool)
 return path

def _bridge_preview_seats(p,path):
 probe=LocalPathContains(path,QtGui)
 for s in pad_flush_seats(p):
  x,y=s['point'];r=s['bore']/2+.02
  # Do not bridge a screw hole that is open to another cut or the perimeter.
  if probe.contains(QtCore.QPointF(x,y)):continue
  ring=r+.08
  if not all(probe.contains(QtCore.QPointF(x+ring*math.cos(i*math.pi/32),y+ring*math.sin(i*math.pi/32))) for i in range(64)):continue
  disk=QtGui.QPainterPath();disk.addEllipse(QtCore.QRectF(x-r,y-r,2*r,2*r));path=path.united(disk);probe=LocalPathContains(path,QtGui)
 return path


def pad_carrier_path(p):
 """Fast 2-D LiPo source; keep hardware holes, optionally bridge airflow cuts.

 This is only a preview. The manufactured pad is built from exact OCC solids
 on Create / Update; it need not use the heavyweight 3-D construction here.
 """
 role=mounting_role(p)
 if p.LiPoPadCopyAirflow:return _bridge_preview_seats(p,finished_part_path(p,role))
 from .cutouts import parse_patterns
 all_patterns=parse_patterns(p.CutoutPatterns)
 if not any(v['enabled'] and v['role']==role and v['mode']!='Add material'
            for v in all_patterns):
  return _bridge_preview_seats(p,finished_part_path(p,role))
 # Avoid copying through-cuts, outline notches and pocket projections to the
 # grip pad. Material additions and all non-airflow structural holes remain.
 kept=[v for v in all_patterns if not
       (v['enabled'] and v['role']==role and v['mode']!='Add material')]
 return _bridge_preview_seats(p,finished_part_path(p,role,kept))


def _round_outline_preview(path,radius,timings=None):
 """2D analogue of the CAD rolling disk; operate only on the outer loop."""
 if radius<=1e-8 or not math.isfinite(radius) or path.isEmpty():return path
 scale=QtGui.QTransform();scale.scale(16,16)
 inverse=QtGui.QTransform();inverse.scale(1/16,1/16)
 source=scale.map(path)
 def timed(label,fn,*args):
  start=perf_counter()
  try:return fn(*args)
  finally:
   if timings is not None:timings[label]=timings.get(label,0.)+perf_counter()-start
 loops=timed('outline loops',source.toSubpathPolygons)
 def area(poly):
  pts=list(poly);return abs(sum(a.x()*b.y()-b.x()*a.y() for a,b in zip(pts,pts[1:]+pts[:1])))/2
 loops=[poly for poly in loops if area(poly)>1e-5]
 if not loops:return path
 def loop_path(poly):
  x=QtGui.QPainterPath();x.addPolygon(poly);x.closeSubpath();return x
 outer_poly=max(loops,key=area);outer=loop_path(outer_poly)
 holes=[loop_path(poly) for poly in loops if poly is not outer_poly]
 if not timed('hole classification',lambda:all(outer.contains(h) for h in holes)):return path
 b=path.boundingRect()
 for r in pad_rounding_radii(radius,b.width(),b.height()):
  stroker=QtGui.QPainterPathStroker();stroker.setWidth(32*r);stroker.setJoinStyle(QtCore.Qt.RoundJoin);stroker.setCapStyle(QtCore.Qt.RoundCap)
  core=timed('erosion',lambda:outer.subtracted(stroker.createStroke(outer)))
  if core.isEmpty():continue
  polygons=core.toSubpathPolygons()
  if len(polygons)!=1:continue
  # The dense erosion polygon can create thousands of tiny overlapping
  # round-join curves. Clean only its intermediate, subpixel segments.
  clean=timed('intermediate contour cleanup',cleaned_core,core,polygons,16*r,QtGui)
  candidates=(clean,core) if clean is not core else (core,)
  for work in candidates:
   label='dilation' if work is clean else 'legacy dilation fallback'
   rounded=timed(label,lambda:work.united(stroker.createStroke(work)).intersected(outer))
   if rounded.isEmpty() or not timed('hole preservation',lambda:all(rounded.contains(h) for h in holes)):continue
   result=timed('restore material / holes',source.intersected,rounded)
   if not result.isEmpty() and len(result.toSubpathPolygons())==len(loops):return inverse.map(result)
 return path


def pad_path(p):
 return QtGui.QPainterPath(_pad_path_cached(p))


@lru_cache(maxsize=12)
def _pad_path_cached(p):
 timings={};start=perf_counter()
 try:
  path=_build_pad_path(p,timings)
  if not path.isEmpty():
   from .battery import split_rectangles
   b=path.boundingRect()
   rects=split_rectangles(p,(b.left(),b.top(),b.right(),b.bottom()))
   if rects:
    scale=QtGui.QTransform();scale.scale(100,100);path=scale.map(path)
    for x,y,w,h in rects:
     tool=QtGui.QPainterPath();tool.addRect(QtCore.QRectF(x,y,w,h));path=path.subtracted(scale.map(tool))
    path=scale.inverted()[0].map(path)
  return path
 except ValueError:return QtGui.QPainterPath()
 finally:
  elapsed=perf_counter()-start
  if elapsed>=.15:
   try:
    import FreeCAD as App
    App.Console.PrintMessage('RotorForge LiPo pad detail: '+', '.join(f'{k}: {v:.3f}s' for k,v in timings.items())+f'; total {elapsed:.3f}s\n')
   except (ImportError,AttributeError):pass

def _build_pad_path(p,timings):
 def timed(label,fn,*args):
  start=perf_counter()
  try:return fn(*args)
  finally:timings[label]=timings.get(label,0.)+perf_counter()-start
 path=QtGui.QPainterPath();w,l=p.LiPoPadWidth,p.LiPoPadLength
 if p.LiPoPadShape=='Pocket insert':
  from .battery import pocket_patterns
  from .airflow_gui import cutout_path
  scale=QtGui.QTransform();scale.scale(100,100);inverse=scale.inverted()[0]
  for v in pocket_patterns(p):path=path.united(scale.map(cutout_path(v,p.CNCToolRadius)))
  path=path.intersected(scale.map(finished_part_path(p,'TopPlate')))
  if p.LiPoPadPocketClearance>0:
   stroker=QtGui.QPainterPathStroker();stroker.setWidth(200*p.LiPoPadPocketClearance);stroker.setJoinStyle(QtCore.Qt.RoundJoin);path=path.subtracted(stroker.createStroke(path))
  return pad_clearance_path(p,inverse.map(path))
 if p.LiPoPadShape=='Mounting plate outline':
  carrier=timed('carrier profile and flush seats',pad_carrier_path,p)
  b=carrier.boundingRect()
  rear,front=pad_reach_bounds(p,b.top(),b.bottom());clip=QtGui.QPainterPath()
  if front>rear:clip.addRect(QtCore.QRectF(b.left()-1,rear,b.width()+2,front-rear))
  # No outline rescaling (the normal setting): use the already cached true
  # profile directly. Avoid a hugely tessellated Qt-to-polygons conversion
  # containing every airflow hole and mounting slot on each pad refresh.
  if p.LiPoPadOutlineWidthScale==100:
   cropped=carrier if front>rear and rear==b.top() and front==b.bottom() else timed('reach clipping',carrier.intersected,clip)
   rounded=timed('corner rounding',_round_outline_preview,cropped,p.LiPoPadCornerRadius,timings)
   return timed('fastener clearances',pad_clearance_path,p,rounded)
  # For narrowed pads only, extract the outer loop. Interior holes keep their
  # original positions by intersecting the scaled loop with the real carrier.
  sampling=QtGui.QTransform();sampling.scale(20,20)
  polygons=carrier.toSubpathPolygons(sampling)
  def area(poly):
   pts=list(poly);return abs(sum(a.x()*b.y()-b.x()*a.y() for a,b in zip(pts,pts[1:]+pts[:1])))
  outer=max(polygons,key=area);path=QtGui.QPainterPath();path.addPolygon(outer);path.closeSubpath()
  inverse=QtGui.QTransform();inverse.scale(.05,.05);path=inverse.map(path)
  cx,cy=b.center().x(),b.center().y();t=QtGui.QTransform();t.translate(cx,cy);t.scale(p.LiPoPadOutlineWidthScale/100,1.);t.translate(-cx,-cy)
  cropped=timed('width and reach clipping',lambda:t.map(path).intersected(carrier).intersected(clip))
  rounded=timed('corner rounding',_round_outline_preview,cropped,p.LiPoPadCornerRadius,timings)
  return timed('fastener clearances',pad_clearance_path,p,rounded)
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
 if p.LiPoPadFollowPlate:path=timed('carrier clipping',lambda:path.intersected(pad_carrier_path(p)))
 return timed('fastener clearances',pad_clearance_path,p,path)

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

def _text_preview_layout(p,path):
 from .pad_text import text_layout
 b=path.boundingRect()
 return text_layout(p,(b.left(),b.top(),b.right(),b.bottom()))


def pad_text_path(p,path):
 # Both editor callers use the same untransformed pad profile. Cache only
 # that case, retaining support for arbitrary paths in other callers.
 if path==pad_path(p):return QtGui.QPainterPath(_cached_pad_text(p))
 return _make_pad_text_path(p,path)

@lru_cache(maxsize=12)
def _cached_pad_text(p):
 return _make_pad_text_path(p,pad_path(p))

def _make_pad_text_path(p,path):
 result=QtGui.QPainterPath();result.setFillRule(QtCore.Qt.WindingFill)
 layout=_text_preview_layout(p,path)
 if layout is None:return result
 groups,r,_=layout
 for group in groups:
  for a,b in group:result.addPath(capsule_path(a,b,r))
 # Inspect the actual clipped pad, including mounting and strap holes.
 scale=QtGui.QTransform();scale.scale(40,40);inverse=QtGui.QTransform();inverse.scale(.025,.025)
 enlarged=scale.map(result);material=scale.map(path)
 missing=enlarged.subtracted(material)
 if not missing.isEmpty():
  # Qt path booleans are a preview only; CAD performs exact volume checks.
  b=missing.boundingRect()
  if b.width()>.8 and b.height()>.8:raise ValueError('Text crosses pad edge or opening; move or resize it.')
 return inverse.map(enlarged.intersected(material))


@lru_cache(maxsize=12)
def _cached_lip_path(p):
 from .battery import lip_regions,lip_sides
 result=QtGui.QPainterPath()
 if not p.LiPoPadEnabled or not lip_sides(p):return result
 unsplit=_build_pad_path(p,{})
 if unsplit.isEmpty():return result
 b=unsplit.boundingRect()
 # Work enlarged for clipping, but select the same global extreme straight
 # line segments as CAD. Inspect line elements only, not Bezier controls.
 # A hole cannot have a segment on the global X extrema unless it opens to
 # the exterior. The final pad material clips all clearances and splits.
 scale=QtGui.QTransform();scale.scale(40,40);inverse=scale.inverted()[0]
 edges=[];previous=None
 for i in range(unsplit.elementCount()):
  element=unsplit.elementAt(i);point=(element.x,element.y)
  if element.isLineTo() and previous is not None:edges.append((previous,point))
  previous=point
 regions=lip_regions(p,(b.left(),b.top(),b.right(),b.bottom()),edges)
 for side,(x0,y0,x1,y1) in regions:
  window=QtGui.QPainterPath();window.addRect(QtCore.QRectF(x0*40,y0*40,(x1-x0)*40,(y1-y0)*40))
  result=result.united(window)
 path=pad_path(p);result=result.intersected(scale.map(path))
 layout=_text_preview_layout(p,path)
 if layout:
  x0,y0,x1,y1=layout[2];keep=QtGui.QPainterPath();keep.addRect(QtCore.QRectF(x0*40,y0*40,(x1-x0)*40,(y1-y0)*40));result=result.subtracted(keep)
 return inverse.map(result)


def side_lip_path(p):
 return QtGui.QPainterPath(_cached_lip_path(p))


def grip_preview_colour(p):
 colour=QtGui.QColor(printed_hex(p))
 if p.LiPoPadPatternRelief=='Embossed':return colour.lighter(175 if colour.lightness()<80 else 125)
 return QtGui.QColor(printed_groove(p))


def grip_path(p,path):
 grooves=QtGui.QPainterPath()
 if p.LiPoPadPattern=='Solid':return grooves
 grooves.setFillRule(QtCore.Qt.WindingFill);box=path.boundingRect();bounds=grip_bounds(p,(box.left(),box.top(),box.right(),box.bottom()))
 for a,b in groove_segments(p,bounds):grooves.addPath(capsule_path(grip_point(p,*a),grip_point(p,*b),p.LiPoPadGrooveWidth/2))
 # Qt boolean flattening is screen-scale dependent; enlarge before clipping small dots.
 scale=QtGui.QTransform();scale.scale(40,40);inverse=QtGui.QTransform();inverse.scale(.025,.025)
 enlarged=scale.map(grooves)
 layout=_text_preview_layout(p,path)
 if layout:
  x0,y0,x1,y1=layout[2];keep=QtGui.QPainterPath();keep.addRect(QtCore.QRectF(x0,y0,x1-x0,y1-y0))
  enlarged=enlarged.subtracted(scale.map(keep))
 if lip_sides(p) and p.LiPoPadPatternRelief=='Debossed':enlarged=enlarged.subtracted(scale.map(side_lip_path(p)))
 return inverse.map(enlarged.intersected(scale.map(path)))

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
  short={'CameraMountLeft':'TPU cage L','CameraMountRight':'TPU cage R','CameraPadLeft':'Camera pad L','CameraPadRight':'Camera pad R','ActionCameraMount':'HD action-camera mount'}
  label=(('TPU cage — left elevation' if role=='CameraMountLeft' else 'TPU cage — right elevation') if role in ('CameraMountLeft','CameraMountRight') and p.CameraCageStyle=='TPU cage' else short.get(role,ROLE_LABELS.get(role,role)))+(' (flat)' if role.startswith('Camera') and p.CameraCageStyle!='TPU cage' else '')
  if role=='LiPoPad' and p.BatteryMount=='Bottom plate':label+=' — underside'
  painter.setPen(QtGui.QColor('#294554'));painter.drawText(QtCore.QRectF(cell.x(),cell.y(),cell.width(),25),QtCore.Qt.AlignCenter,label)
  scale=min((cw-24)/max(1,b.width()),(ch-40)/max(1,b.height()))
  painter.save();painter.translate(cell.center().x(),cell.center().y()+9);painter.scale(-scale if role=='LiPoPad' and p.BatteryMount=='Bottom plate' else scale,-scale);painter.translate(-b.center().x(),-b.center().y())
  painter.setPen(QtGui.QPen(QtGui.QColor(CARBON_EDGE),.4));painter.setBrush(QtGui.QColor(printed_hex(p)) if role=='LiPoPad' or role.startswith(('CameraPad','MotorProtector','ElectronicsGuard','FrontBumper','RearAntennaMount','ELRSAntennaMount','ActionCameraMount')) else carbon_brush(p,QtGui,role=role));painter.drawPath(path)
  if role in ('CameraMountLeft','CameraMountRight') and p.CameraCageStyle!='Carbon side plates':
   painter.fillPath(path,QtGui.QColor(printed_hex(p) if p.CameraCageStyle=='TPU cage' else '#adb2ba'))
  if role=='ActionCameraMount':
   from .action_camera_mount import mount_layout
   d=mount_layout(p)
   if d:
    painter.setBrush(QtCore.Qt.NoBrush)
    painter.setPen(QtGui.QPen(QtGui.QColor(CARBON_EDGE),.25))
    for x in d['fin_centres']:
     painter.drawRect(QtCore.QRectF(x-d['fin_width']/2,d['hinge_y']-10,d['fin_width'],20))
    nut=d['nut']
    if nut:
     painter.drawRect(QtCore.QRectF(nut['start_x'],d['hinge_y']-nut['radius'],nut['end_x']-nut['start_x'],2*nut['radius']))
  if role=='LiPoPad':
   try:
    painter.fillPath(grip_path(p,path),grip_preview_colour(p))
    if lip_sides(p):
     painter.setPen(QtGui.QPen(QtGui.QColor(CARBON_EDGE),.18));painter.setBrush(QtGui.QColor(printed_hex(p)).lighter(150));painter.drawPath(side_lip_path(p))
    if p.LiPoPadTextEnabled:painter.fillPath(pad_text_path(p,path),QtGui.QColor(printed_groove(p)))
   except ValueError as exc:
    painter.restore();painter.setPen(QtGui.QColor('#ad3d36'))
    painter.drawText(QtCore.QRectF(cell.x()+6,cell.bottom()-48,cell.width()-12,45),QtCore.Qt.AlignHCenter|QtCore.Qt.TextWordWrap,str(exc))
    continue
  painter.restore()
