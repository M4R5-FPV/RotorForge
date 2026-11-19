"""LiPo placement and printable/grip-pad layout; CAD imports remain lazy."""
import math
from .pad_text import PAD_TEXT_FIELDS,validate_pad_text,text_layout,text_cutters
BATTERY_FIELDS={'BatteryReferenceEnabled','BatteryWidth','BatteryLength','BatteryHeight','BatteryMass',
 'BatteryMount','BatteryX','BatteryY','BatteryRotation','LiPoPadEnabled','LiPoPadWidth','LiPoPadLength',
 'LiPoPadFrontReach','LiPoPadRearReach','LiPoPadOutlineWidthScale','LiPoPadOutlineLengthScale','LiPoPadThickness','LiPoPadShape','LiPoPadCornerRadius','LiPoPadFollowPlate','LiPoPadCopyAirflow','LiPoPadCoverCountersunk','LiPoPadPattern',
 'LiPoPadGrooveWidth','LiPoPadGrooveDepth','LiPoPadGroovePitch','LiPoPadDensity'} | PAD_TEXT_FIELDS

def battery_point(p,x,y):
 a=math.radians(p.BatteryRotation);c,s=math.cos(a),math.sin(a)
 return (p.BatteryX+x*c-y*s,p.BatteryY+x*s+y*c)

def mounting_role(p):return 'TopPlate' if p.BatteryMount=='Top plate' else 'BottomPlate'

def battery_levels(p):
 from .parameters import plate_levels
 top=plate_levels(p)['top_z']+p.TopThickness
 t=p.LiPoPadThickness if p.LiPoPadEnabled else 0.
 if p.BatteryMount=='Top plate':return dict(pad_z=top,battery_z=top+t)
 return dict(pad_z=-t,battery_z=-t-p.BatteryHeight)

GRIP_PATTERNS=('Solid','Transverse grooves','Cross grooves','Longitudinal grooves','Diagonal grooves','Diamond grooves','Chevron grooves','Zigzag grooves','Rectangular rings','Dimple grid','Staggered dimples','Dash grid','Basket weave','Hexagon cells','Wavy grooves','Brick joints','Herringbone','Plus grid','X grid','Square islands','Diamond islands','Triangular lattice','Ladder grooves','Interrupted ribs','Fish scale grooves')
MAX_GRIP_SEGMENTS=512

def grip_point(p,x,y):
 return (x,y) if p.LiPoPadShape=='Mounting plate outline' else battery_point(p,x,y)

def grip_bounds(p,bounds):
 """Convert the finished frame-space pad bounds to the pattern coordinate system."""
 if p.LiPoPadShape=='Mounting plate outline':return bounds
 xmin,ymin,xmax,ymax=bounds;a=math.radians(p.BatteryRotation);c,s=math.cos(a),math.sin(a)
 pts=[((x-p.BatteryX)*c+(y-p.BatteryY)*s,-(x-p.BatteryX)*s+(y-p.BatteryY)*c) for x in (xmin,xmax) for y in (ymin,ymax)]
 return min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)

def groove_segments(p,bounds=None):
 if not p.LiPoPadEnabled or p.LiPoPadPattern=='Solid':return ()
 if bounds is None:bounds=(-p.LiPoPadWidth/2,-p.LiPoPadLength/2,p.LiPoPadWidth/2,p.LiPoPadLength/2)
 xmin,ymin,xmax,ymax=bounds;pitch=p.LiPoPadGroovePitch
 if pitch<=0:raise ValueError('Grip spacing must be positive.')
 margin=2*pitch+p.LiPoPadGrooveWidth;lo,hi=xmin-margin,xmax+margin;bottom,top=ymin-margin,ymax+margin
 result=[]
 def add(a,b):
  if len(result)>=MAX_GRIP_SEGMENTS:raise ValueError('Grip pattern is too dense for the finished pad; increase groove spacing (maximum 512 segments).')
  result.append((a,b))
 def grid(low,high):return range(math.floor(low/pitch),math.ceil(high/pitch)+1)
 kind=p.LiPoPadPattern
 if kind in ('Transverse grooves','Cross grooves'):
  for i in grid(bottom,top):add((lo,i*pitch),(hi,i*pitch))
 if kind in ('Longitudinal grooves','Cross grooves'):
  for i in grid(lo,hi):add((i*pitch,bottom),(i*pitch,top))
 if kind in ('Diagonal grooves','Diamond grooves'):
  for sign in ((1,-1) if kind=='Diamond grooves' else (1,)):
   values=[y-sign*x for x in (lo,hi) for y in (bottom,top)]
   for i in grid(min(values),max(values)):add((lo,sign*lo+i*pitch),(hi,sign*hi+i*pitch))
 if kind=='Chevron grooves':
  left,right=min(lo,0),max(hi,0)
  for i in grid(bottom-max(abs(left),abs(right))*.5,top):
   y=i*pitch;add((left,y+abs(left)*.5),(0,y));add((0,y),(right,y+abs(right)*.5))
 if kind=='Zigzag grooves':
  for j in grid(bottom-pitch,top+pitch):
   for i in grid(lo-pitch,hi):add((i*pitch,j*pitch+(-1 if i%2 else 1)*pitch*.35),((i+1)*pitch,j*pitch+(-1 if (i+1)%2 else 1)*pitch*.35))
 if kind=='Rectangular rings':
  cx,cy=(xmin+xmax)/2,(ymin+ymax)/2;w,h=(xmax-xmin)/2+pitch,(ymax-ymin)/2+pitch
  while w>0 and h>0:
   pts=((cx-w,cy-h),(cx+w,cy-h),(cx+w,cy+h),(cx-w,cy+h))
   for a,b in zip(pts,pts[1:]+pts[:1]):add(a,b)
   w-=pitch;h-=pitch
 if kind in ('Dimple grid','Staggered dimples','Dash grid'):
  for j in grid(ymin-pitch/2,ymax+pitch/2):
   shift=pitch/2 if j%2 and kind!='Dimple grid' else 0.
   for i in grid(xmin-pitch,xmax+pitch):
    x,y=i*pitch+shift,j*pitch
    if kind=='Dash grid':add((x-pitch*.3,y),(x+pitch*.3,y))
    else:add((x,y),(x,y))
 if kind=='Basket weave':
  tile=2*pitch
  for j in range(math.floor(ymin/tile)-1,math.ceil(ymax/tile)+1):
   for i in range(math.floor(xmin/tile)-1,math.ceil(xmax/tile)+1):
    x,y=(i+.5)*tile,(j+.5)*tile
    for d in (-pitch*.3,pitch*.3):
     if (i+j)%2:add((x+d,y-pitch*.7),(x+d,y+pitch*.7))
     else:add((x-pitch*.7,y+d),(x+pitch*.7,y+d))
 if kind=='Hexagon cells':
  radius=pitch;dy=math.sqrt(3)*radius;dx=1.5*radius;seen=set()
  for i in range(math.floor((xmin-radius)/dx),math.ceil((xmax+radius)/dx)+1):
   for j in range(math.floor((ymin-radius)/dy)-1,math.ceil((ymax+radius)/dy)+1):
    x,y=i*dx,j*dy+(dy/2 if i%2 else 0)
    pts=tuple((x+radius*math.cos(k*math.pi/3),y+radius*math.sin(k*math.pi/3)) for k in range(6))
    for a,b in zip(pts,pts[1:]+pts[:1]):
     key=tuple(sorted((tuple(round(v,7) for v in a),tuple(round(v,7) for v in b))))
     if key not in seen:seen.add(key);add(a,b)
 if kind=='Wavy grooves':
  step=pitch/2
  for j in grid(ymin-pitch,ymax+pitch):
   for i in range(math.floor((xmin-pitch)/step),math.ceil((xmax+pitch)/step)+1):
    x1,x2=i*step,(i+1)*step
    add((x1,j*pitch+pitch*.3*math.sin(x1*math.pi/(3*pitch))),(x2,j*pitch+pitch*.3*math.sin(x2*math.pi/(3*pitch))))
 if kind=='Brick joints':
  for j in grid(bottom,top):
   y=j*pitch;add((lo,y),(hi,y))
   for i in range(math.floor(lo/(2*pitch))-1,math.ceil(hi/(2*pitch))+1):
    x=(2*i+(j%2))*pitch;add((x,y),(x,y+pitch))
 if kind in ('Herringbone','Plus grid','X grid','Square islands','Diamond islands','Interrupted ribs'):
  tile=2*pitch
  for j in range(math.floor(ymin/tile)-1,math.ceil(ymax/tile)+1):
   for i in range(math.floor(xmin/tile)-1,math.ceil(xmax/tile)+1):
    x,y=i*tile,j*tile;h=.55*pitch
    if kind=='Herringbone':
     sign=1 if (i+j)%2 else -1
     add((x-h,y-sign*h),(x+h,y+sign*h))
    elif kind in ('Plus grid','X grid'):
     if kind=='Plus grid':add((x-h,y),(x+h,y));add((x,y-h),(x,y+h))
     else:add((x-h,y-h),(x+h,y+h));add((x-h,y+h),(x+h,y-h))
    elif kind=='Interrupted ribs':
     shift=pitch/2 if j%2 else 0
     add((x-.8*pitch+shift,y),(x+.8*pitch+shift,y))
    else:
     pts=((x-h,y-h),(x+h,y-h),(x+h,y+h),(x-h,y+h)) if kind=='Square islands' else ((x,y-h),(x+h,y),(x,y+h),(x-h,y))
     for a,b in zip(pts,pts[1:]+pts[:1]):add(a,b)
 if kind=='Triangular lattice':
  for i in grid(bottom,top):add((lo,i*pitch),(hi,i*pitch))
  for sign in (-1,1):
   values=[y-sign*math.sqrt(3)*x for x in (lo,hi) for y in (bottom,top)]
   for i in grid(min(values),max(values)):add((lo,sign*math.sqrt(3)*lo+i*pitch),(hi,sign*math.sqrt(3)*hi+i*pitch))
 if kind=='Ladder grooves':
  tile=3*pitch
  for i in range(math.floor(lo/tile)-1,math.ceil(hi/tile)+1):
   x=i*tile
   for dx in (-.7*pitch,.7*pitch):add((x+dx,bottom),(x+dx,top))
   for j in grid(bottom,top):add((x-.7*pitch,j*pitch),(x+.7*pitch,j*pitch))
 if kind=='Fish scale grooves':
  tile=2*pitch
  for j in range(math.floor(ymin/pitch)-1,math.ceil(ymax/pitch)+1):
   for i in range(math.floor(xmin/tile)-1,math.ceil(xmax/tile)+1):
    x=i*tile+(pitch if j%2 else 0);y=j*pitch
    pts=[(x+pitch*.8*math.cos(k*math.pi/4),y+pitch*.55*math.sin(k*math.pi/4)) for k in range(5)]
    for a,b in zip(pts,pts[1:]):add(a,b)
 return tuple(result)

def clipped_grip_segments(p,segments,bounds):
 """Trim only invisible tool overhang, retaining a full groove-width margin.

 Segment ends stay outside the finished pad, so this preserves the actual cut
 while avoiding long outside tools in native boolean operations.
 """
 pad=p.LiPoPadGrooveWidth;xmin,ymin,xmax,ymax=bounds
 xmin-=pad;ymin-=pad;xmax+=pad;ymax+=pad
 result=[]
 for a,b in segments:
  a,b=grip_point(p,*a),grip_point(p,*b);dx,dy=b[0]-a[0],b[1]-a[1];lo,hi=0.,1.
  for direction,distance in ((-dx,a[0]-xmin),(dx,xmax-a[0]),(-dy,a[1]-ymin),(dy,ymax-a[1])):
   if abs(direction)<1e-12:
    if distance<0:lo=2;break
   elif direction<0:lo=max(lo,distance/direction)
   else:hi=min(hi,distance/direction)
  if lo<=hi:result.append(((a[0]+lo*dx,a[1]+lo*dy),(a[0]+hi*dx,a[1]+hi*dy)))
 return tuple(result)

def validate_battery(p):
 errors=validate_pad_text(p)
 for name in (BATTERY_FIELDS-PAD_TEXT_FIELDS)|{'StandoffDensity'}:
  if name in ('BatteryX','BatteryY','BatteryRotation','BatteryMount','BatteryReferenceEnabled','LiPoPadEnabled','LiPoPadShape','LiPoPadPattern','LiPoPadFollowPlate','LiPoPadCopyAirflow','LiPoPadCoverCountersunk'):continue
  if name.startswith('LiPoPad') and not p.LiPoPadEnabled:continue
  if name in ('LiPoPadFrontReach','LiPoPadRearReach'):
   if p.LiPoPadShape=='Mounting plate outline' and (not math.isfinite(getattr(p,name)) or getattr(p,name)<0):errors.append('Pad front/rear reaches must be finite and non-negative (zero means full plate).')
   continue
  if name.startswith('LiPoPadOutline'):
   if p.LiPoPadShape=='Mounting plate outline' and not 1<=getattr(p,name)<=100:errors.append('Plate-following pad scales must be between 1 and 100 percent.')
   continue
  if name.startswith('LiPoPadGroove') and p.LiPoPadPattern=='Solid':continue
  if name=='LiPoPadCornerRadius':
   if p.LiPoPadShape=='Rounded rectangle' and not 0<=p.LiPoPadCornerRadius<min(p.LiPoPadWidth,p.LiPoPadLength)/2:errors.append('Pad corner radius must be smaller than half the shorter pad dimension.')
   if p.LiPoPadShape=='Mounting plate outline' and (not math.isfinite(p.LiPoPadCornerRadius) or p.LiPoPadCornerRadius<0):errors.append('Plate-following pad corner radius must be finite and non-negative.')
  elif getattr(p,name)<=0:errors.append(name+' must be greater than zero.')
 if not -180<=p.BatteryRotation<=180:errors.append('Battery rotation must be between -180 and 180 degrees.')
 if p.LiPoPadEnabled and p.LiPoPadPattern!='Solid':
  if p.LiPoPadGrooveDepth>=p.LiPoPadThickness:errors.append('Pad grooves must leave a continuous backing: groove depth must be less than pad thickness.')
  if p.LiPoPadGroovePitch<=p.LiPoPadGrooveWidth:errors.append('Pad groove pitch must exceed groove width.')
  if p.LiPoPadGroovePitch>0:
   try:
    if p.LiPoPadShape=='Mounting plate outline':
     from .parameters import top_bounds,bottom_bounds
     rear,front=top_bounds(p) if p.BatteryMount=='Top plate' else bottom_bounds(p);rear,front=pad_reach_bounds(p,rear,front);w=max(p.TopWidth,p.TopCentreWidth) if p.BatteryMount=='Top plate' else max(p.BodyWidth,p.BottomCentreWidth);w*=p.LiPoPadOutlineWidthScale/100
     bounds=(-w/2,rear,w/2,front)
    else:bounds=None
    groove_segments(p,bounds)
   except ValueError as exc:errors.append(str(exc))
 return errors

def pad_polygon(p):
 w,l=p.LiPoPadWidth/2,p.LiPoPadLength/2
 if p.LiPoPadShape=='Chamfered rectangle':
  c=min(w,l)*.35
  return ((-w+c,-l),(w-c,-l),(w,-l+c),(w,l-c),(w-c,l),(-w+c,l),(-w,l-c),(-w,-l+c))
 if p.LiPoPadShape=='Tapered':return ((-w,-l),(w,-l),(w*.65,l),(-w*.65,l))
 if p.LiPoPadShape=='Hourglass':return ((-w,-l),(w,-l),(w*.65,0),(w,l),(-w,l),(-w*.65,0))
 return ()

def pad_blank(p):
 import FreeCAD as App
 import Part
 from .geometry import rounded_plate,capsule,polygon_plate
 w,l,t=p.LiPoPadWidth,p.LiPoPadLength,p.LiPoPadThickness
 if pad_polygon(p):shape=polygon_plate(pad_polygon(p),0,t)
 elif p.LiPoPadShape=='Ellipse':
  e=Part.Ellipse(App.Vector(),max(w,l)/2,min(w,l)/2)
  shape=Part.Face(Part.Wire([e.toShape()])).extrude(App.Vector(0,0,t))
  if l>w:shape.rotate(App.Vector(),App.Vector(0,0,1),90)
 elif p.LiPoPadShape=='Capsule':
  d=max(w,l)-min(w,l);a,b=((0,-d/2),(0,d/2)) if l>=w else ((-d/2,0),(d/2,0))
  shape=capsule(a,b,min(w,l)/2,0,t)
 elif p.LiPoPadShape=='Rectangle':shape=Part.makeBox(w,l,t,App.Vector(-w/2,-l/2,0))
 elif p.LiPoPadCornerRadius>1e-8:shape=rounded_plate(w,l,p.LiPoPadCornerRadius,0,t)
 else:shape=Part.makeBox(w,l,t,App.Vector(-w/2,-l/2,0))
 shape.rotate(App.Vector(),App.Vector(0,0,1),p.BatteryRotation)
 shape.translate(App.Vector(p.BatteryX,p.BatteryY,battery_levels(p)['pad_z']))
 return shape

def pad_parameters_without_airflow(p):
 """Return a pad-only source for a carrier without through air openings.

 The original carbon remains untouched. Preserve additions and disabled
 patterns, and only remove enabled cuts/pockets on the selected mounting
 plate. Do this only during exact CAD creation, never for a 2-D preview.
 None means there is no difference and avoids rebuilding a second plate.
 """
 if p.LiPoPadCopyAirflow or (p.LiPoPadShape!='Mounting plate outline' and not p.LiPoPadFollowPlate):
  return None
 from .cutouts import parse_patterns,encode_patterns
 from .parameters import Parameters
 role=mounting_role(p)
 # The dependent-part cache is already keyed by the actual built carrier
 # solid. Keep-only / metadata changes don't alter that solid and must not
 # force an expensive pad rebuild. Read the JSON without registering a raw
 # string dependency on the TrackedParameters instance.
 patterns=parse_patterns(object.__getattribute__(p,'CutoutPatterns'))
 should_omit=lambda v: v['enabled'] and v['role']==role and v['mode']!='Add material'
 if not any(should_omit(v) for v in patterns):return None
 surviving=[v for v in patterns if not should_omit(v)]
 # Avoid dataclasses.replace(p,...) here: on TrackedParameters it reads ALL
 # hundreds of unrelated fields and defeats component-level caching. The
 # finished carrier's native shape token supplies the geometry dependency.
 values={name:object.__getattribute__(p,name) for name in p.__dataclass_fields__}
 values['CutoutPatterns']=encode_patterns(surviving)
 return Parameters(**values)

def pad_reach_bounds(p,ymin,ymax):
 """Frame Y clipping planes. Zero keeps the corresponding carrier end."""
 rear=max(ymin,p.StackOffsetY-p.LiPoPadRearReach) if p.LiPoPadRearReach else ymin
 front=min(ymax,p.StackOffsetY+p.LiPoPadFrontReach) if p.LiPoPadFrontReach else ymax
 return rear,front

def pad_standoff_clearance(p):
 return max(6.,p.StandoffHoleDiameter/2)

def pad_flush_seats(p):
 """Only flush heads on the actual battery-facing carbon surface."""
 if not p.LiPoPadCoverCountersunk:return ()
 from .screw_heads import countersink_specs
 role=mounting_role(p);axis=-1 if role=='TopPlate' else 1
 return tuple(s for s in countersink_specs(p,role) if s['axis']==axis)


def pad_standoff_points(p):
 from .parameters import standoff_layouts
 covered=tuple(s['point'] for s in pad_flush_seats(p) if s['label']=='Standoff screw')
 return tuple(s['point'] for s in standoff_layouts(p) if not any(math.dist(s['point'],pt)<1e-6 for pt in covered))


def pad_fastener_clearances(p):
 """Standoffs retain their original 6 mm clearance; when flush coverage is
 active, also protect any remaining proud hardware at the battery face.
 """
 clearances=[(*pt,pad_standoff_clearance(p)) for pt in pad_standoff_points(p)]
 if not p.LiPoPadCoverCountersunk:return tuple(clearances)
 from .hardware_layout import hardware_layout,SIZES
 from .parameters import plate_levels
 top=mounting_role(p)=='TopPlate';z=plate_levels(p)['top_z']+p.TopThickness if top else 0.
 axis=-1 if top else 1
 for spec in hardware_layout(p):
  x,y,sz=spec['point'];d=spec['diameter']
  if abs(sz-z)<1e-6 and spec['axis']==(0,0,axis) and spec['head']!='Countersunk':
   clearances.append((x,y,.95*d+.1))
  seat=spec.get('seat')
  if spec['nut'] and seat and abs(seat['z']-z)<1e-6 and seat['axis']==-axis:
   # External nut/flange on this surface cannot be hidden by the pad.
   rr=p.PressNutFlangeDiameter/2 if spec.get('press') else SIZES[d][4]/math.sqrt(3)
   clearances.append((x,y,rr+.1))
 by_point={}
 for x,y,r in clearances:
  key=(x,y);by_point[key]=max(r,by_point.get(key,0.))
 return tuple((*pt,r) for pt,r in by_point.items())


def pad_face_with_flush_holes(p,face,seats):
 """Fill only isolated circular screw openings, never the outer perimeter,
 slots or a combined hole/cutout. Face is already at the pad extrusion datum.
 """
 import Part
 if not seats:return face
 outer=face.OuterWire;remaining=[outer];filled=0
 for wire in face.Wires:
  if wire.isSame(outer):continue
  box=wire.BoundBox;centre=((box.XMin+box.XMax)/2,(box.YMin+box.YMax)/2)
  disk=Part.Face(wire)
  for s in seats:
   d=s['head_diameter']
   if (math.dist(centre,s['point'])<.015 and abs(box.XLength-d)<.015 and abs(box.YLength-d)<.015
       and abs(disk.Area-math.pi*(d/2)**2)<.03):
    filled+=1;break
  else:remaining.append(wire)
 if not filled:return face
 merged=Part.makeFace(remaining,'Part::FaceMakerBullseye')
 if len(merged.Faces)==1 and merged.isValid():return merged.Faces[0]
 raise ValueError('Could not restore the isolated flush screw openings in the LiPo pad.')


def pad_rounding_radii(radius,width,length):
 """Bound the trials by the *actual* cropped pad, not inactive pad dimensions."""
 if not math.isfinite(radius) or radius<=1e-8:return ()
 r=min(radius,.49*min(width,length))
 return tuple(r*.7**i for i in range(12) if i==0 or r*.7**i>=.01) if r>1e-8 else ()


def round_pad_outline(shape,radius):
 """Roll a disk inside the outer perimeter only; never add stock or alter holes.

 Work before the fastener and grip cuts. A convex corner (including a clipped
 reach corner or an existing smaller arc) is rounded by an inward/outward
 round offset. Retain the original solid if the contour cannot support it.
 """
 if not math.isfinite(radius) or radius<=1e-8:return shape
 import FreeCAD as App
 import Part
 from .cnc_perimeter import _as_single_face
 from .cnc_autorepair import _rounded_offset
 if shape.isNull() or len(shape.Solids)!=1:return shape
 box=shape.BoundBox
 cap=max((f for f in shape.Faces if f.BoundBox.ZLength<1e-6 and abs(f.BoundBox.ZMin-box.ZMax)<1e-6),key=lambda f:f.Area)
 outer=Part.Face(cap.OuterWire)
 holes=[Part.Face(w) for w in cap.Wires if not w.isSame(cap.OuterWire)]
 from .geometry_bounds import box_distance
 from time import perf_counter
 hole_bounds=[(h,h.OuterWire,h.BoundBox) for h in holes]
 for r in pad_rounding_radii(radius,box.XLength,box.YLength):
  try:
   tick=perf_counter();rolled=_rounded_offset(outer,r,False);offset_time=perf_counter()-tick;tick=perf_counter()
   # Intersect, not replace: no pad material can extend beyond the old shape.
   outline=_as_single_face(outer.common(rolled).removeSplitter())
   if not outline.isValid():continue
   removed=outer.cut(outline)
   if removed.Area<1e-7:
    if r<radius-1e-6:App.Console.PrintMessage(f'LiPo pad: outline already supports the feasible R{r:.2f} mm corner radius.\n')
    return shape
   # Avoid opening a previously enclosed hole to air (even a very small web).
   clip_time=perf_counter()-tick;tick=perf_counter()
   outline_wire=outline.OuterWire;removed_box=removed.BoundBox
   if any(outline.distToShape(wire)[0]>1e-6 or outline_wire.distToShape(wire)[0]<1e-5 or
          (box_distance(removed_box,hb)<=1e-6 and removed.common(h).Area>1e-7) for h,wire,hb in hole_bounds):continue
   hole_time=perf_counter()-tick;tick=perf_counter()
   outline.translate(App.Vector(0,0,box.ZMin-outline.CenterOfMass.z))
   tool=outline.extrude(App.Vector(0,0,box.ZLength))
   result=shape.common(tool).removeSplitter()
   if result.isNull() or not result.isValid() or len(result.Solids)!=1:continue
   if result.Volume>shape.Volume+1e-6:continue
   final_cap=max((f for f in result.Faces if f.BoundBox.ZLength<1e-6 and abs(f.BoundBox.ZMin-box.ZMax)<1e-6),key=lambda f:f.Area)
   if len(final_cap.Wires)!=len(cap.Wires):continue
   if r<radius-1e-6:App.Console.PrintMessage(f'LiPo pad: requested corner radius {radius:g} mm limited to R{r:.2f} mm by the outline.\n')
   App.Console.PrintMessage(f'RotorForge LiPo rounding detail: offsets: {offset_time:.3f}s, planar clipping: {clip_time:.3f}s, hole checks: {hole_time:.3f}s, solid clipping and validation: {perf_counter()-tick:.3f}s (accepted R{r:g})\n')
   return result
  except Exception:
   continue
 App.Console.PrintWarning('LiPo pad: no safe outer rounding fits this outline; retaining original corners. Reduce the corner radius or adjust pad reaches.\n')
 return shape


def make_pad(p,carrier,grooves=True,carrier_without_airflow=None):
 import FreeCAD as App
 import Part
 import time
 from .geometry_bounds import box_distance
 tick=time.perf_counter();stages=[]
 def mark(label):
  nonlocal tick
  now=time.perf_counter();stages.append((label,now-tick));tick=now
 z=battery_levels(p)['pad_z']
 # The secondary plate is constructed only at Create/Update when the user
 # wants the LiPo pad to bridge carbon airflow openings. All mounting and
 # strap access holes are retained; the finished carbon plate is unchanged.
 if carrier_without_airflow is not None:
  carrier=carrier_without_airflow
 seats=pad_flush_seats(p)
 # The lower plate's actual screw rims are on ZMin, not its inner upper face.
 sign=-1 if seats and p.BatteryMount=='Bottom plate' else 1
 faces=[f for f in carrier.Faces if sign*f.normalAt(0,0).z>.99999]
 if seats:
  surface=seats[0]['z'];faces=[f for f in faces if abs(f.CenterOfMass.z-surface)<1e-6]
  if not faces:raise ValueError('Could not locate the battery-facing screw seating plane.')
 face=max(faces,key=lambda f:f.Area).copy();face.translate(App.Vector(0,0,z-face.CenterOfMass.z))
 if seats:face=pad_face_with_flush_holes(p,face,seats)
 if p.LiPoPadShape=='Mounting plate outline':
  shape=face.extrude(App.Vector(0,0,p.LiPoPadThickness))
  if p.LiPoPadOutlineWidthScale!=100:
   # Scale only the outer boundary; carrier holes remain in their real positions.
   outer=Part.Face(face.OuterWire);box=outer.optimalBoundingBox(False);cx=(box.XMin+box.XMax)/2;cy=(box.YMin+box.YMax)/2
   sx,sy=p.LiPoPadOutlineWidthScale/100,1.
   matrix=App.Matrix();matrix.A11=sx;matrix.A22=sy;matrix.A14=cx*(1-sx);matrix.A24=cy*(1-sy)
   outline=outer.transformGeometry(matrix).extrude(App.Vector(0,0,p.LiPoPadThickness))
   shape=shape.common(outline).removeSplitter()
  box=face.optimalBoundingBox(False);rear,front=pad_reach_bounds(p,box.YMin,box.YMax)
  if front<=rear:raise ValueError('Pad front/rear reaches do not overlap the carrier.')
  # With full reaches and no width scaling, the exact carrier extrusion
  # already lies inside this prism. Refinement is retained, without a
  # coincident full-solid Boolean. All cropped cases use the old operation.
  if p.LiPoPadOutlineWidthScale==100 and rear==box.YMin and front==box.YMax:
   shape=shape.removeSplitter()
  else:
   shape=shape.common(Part.makeBox(box.XLength+2,front-rear,p.LiPoPadThickness,App.Vector(box.XMin-1,rear,z))).removeSplitter()
  mark('carrier and reach clipping')
  shape=round_pad_outline(shape,p.LiPoPadCornerRadius)
  mark('outer rounding')
 else:
  shape=pad_blank(p)
  supported=shape.common(face.extrude(App.Vector(0,0,p.LiPoPadThickness))).removeSplitter()
  if supported.isNull() or supported.Volume<1e-6:raise ValueError('LiPo pad does not contact the mounting plate; move or resize it.')
  if p.LiPoPadFollowPlate:shape=supported
  mark('carrier and reach clipping')
 from .geometry import cylinder
 tools=[cylinder(x,y,r,z-.01,p.LiPoPadThickness+.02) for x,y,r in pad_fastener_clearances(p)]
 shape_bounds=shape.BoundBox
 tools=[tool for tool in tools if box_distance(shape_bounds,tool.BoundBox)<=1e-6]
 if tools:shape=shape.cut(Part.makeCompound(tools)).removeSplitter()
 mark('fastener clearances')
 # The outline-only export deliberately omits all shallow surface machining.
 layout=None
 grip_box=None
 if grooves and p.LiPoPadTextEnabled:
  if shape.isNull() or len(shape.Solids)!=1:raise ValueError('LiPo pad must be connected before lettering; adjust the pad outline or openings.')
  box=grip_box=shape.optimalBoundingBox(False)
  layout=text_layout(p,(box.XMin,box.YMin,box.XMax,box.YMax))
  if layout:
   depth=p.LiPoPadTextDepth
   bottom=z if p.BatteryMount=='Bottom plate' else z+p.LiPoPadThickness-depth
   # Use one set of cutters. Exact overlap must equal the designed depth;
   # the remaining 0.01 mm is deliberately outside the battery-facing surface.
   outside=z-.01 if p.BatteryMount=='Bottom plate' else bottom
   letter_tools=text_cutters(layout,outside,depth+.01)
   for letter in letter_tools:
    expected=letter.Volume*depth/(depth+.01)
    if expected-shape.common(letter).Volume>max(1e-7,expected*1e-6):
     raise ValueError('LiPo pad lettering crosses the pad edge or an opening. Move the text, reduce its size or choose another position.')
 if grooves:
  from .geometry import capsule
  bottom=z-.01 if p.BatteryMount=='Bottom plate' else z+p.LiPoPadThickness-p.LiPoPadGrooveDepth
  box=grip_box if grip_box is not None else shape.optimalBoundingBox(False);bounds=grip_bounds(p,(box.XMin,box.YMin,box.XMax,box.YMax))
  segments=clipped_grip_segments(p,groove_segments(p,bounds),(box.XMin,box.YMin,box.XMax,box.YMax))
  radius=p.LiPoPadGrooveWidth/2
  if layout:
   x0,y0,x1,y1=layout[2]
   # A capsule wholly inside the reserved rectangle is removed by the old
   # cutter subtraction anyway. Skip creating its OCC solid entirely.
   eps=1e-7
   if p.LiPoPadGrooveDepth<p.LiPoPadThickness:
    segments=tuple((a,b) for a,b in segments if not (min(a[0],b[0])-radius>x0+eps and max(a[0],b[0])+radius<x1-eps and min(a[1],b[1])-radius>y0+eps and max(a[1],b[1])+radius<y1-eps))
  tools=[capsule(a,b,radius,bottom,p.LiPoPadGrooveDepth+.01) for a,b in segments]
  if layout:
   x0,y0,x1,y1=layout[2]
   keep=Part.makeBox(x1-x0,y1-y0,p.LiPoPadThickness+.04,App.Vector(x0,y0,z-.02))
   trimmed=[]
   for tool in tools:
    b=tool.BoundBox
    if b.XMax>x0 and b.XMin<x1 and b.YMax>y0 and b.YMin<y1:
     tool=tool.cut(keep)
    if not tool.isNull():trimmed.extend(tool.Solids)
   tools=trimmed
  shape_bounds=shape.BoundBox
  tools=[tool for tool in tools if box_distance(shape_bounds,tool.BoundBox)<=1e-6]
  mark('grip and lettering tools')
  if tools:shape=shape.cut(Part.makeCompound(tools)).removeSplitter()
  if layout:shape=shape.cut(Part.makeCompound(letter_tools)).removeSplitter()
  mark('grip and lettering booleans')
 if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1:
  raise ValueError('LiPo pad must remain one connected part after plate cuts and 6 mm standoff clearances. Adjust its width/reaches or simplify cuts.')
 mark('final validation')
 App.Console.PrintMessage('RotorForge LiPo geometry detail: '+', '.join(f'{k}: {v:.3f}s' for k,v in stages)+'\n')
 return shape

def battery_envelope(p):
 import FreeCAD as App
 import Part
 s=Part.makeBox(p.BatteryWidth,p.BatteryLength,p.BatteryHeight,App.Vector(-p.BatteryWidth/2,-p.BatteryLength/2,0))
 s.rotate(App.Vector(),App.Vector(0,0,1),p.BatteryRotation)
 s.translate(App.Vector(p.BatteryX,p.BatteryY,battery_levels(p)['battery_z']))
 return s

def printable_pad(p,shape):
 import FreeCAD as App
 s=shape.copy()
 if p.BatteryMount=='Bottom plate':s.rotate(App.Vector(),App.Vector(1,0,0),180)
 b=s.BoundBox;s.translate(App.Vector(-b.XMin,-b.YMin,-b.ZMin));return s
