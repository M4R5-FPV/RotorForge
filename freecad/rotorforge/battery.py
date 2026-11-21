"""LiPo placement and printable/grip-pad layout; CAD imports remain lazy."""
import math
from .pad_text import PAD_TEXT_FIELDS,validate_pad_text,text_layout,text_cutters
# (saved checkbox, lateral half, longitudinal half); 0 spans both halves.
# Frame coordinates: negative X is left, positive Y is front.
LIP_PAD_OPTIONS={
 'Single':(),
 'Left / right':(('LiPoPadLipLeft',-1,0),('LiPoPadLipRight',1,0)),
 'Front / rear':(('LiPoPadLipFront',0,1),('LiPoPadLipRear',0,-1)),
 'Four parts':(('LiPoPadLipFrontLeft',-1,1),('LiPoPadLipFrontRight',1,1),
               ('LiPoPadLipRearLeft',-1,-1),('LiPoPadLipRearRight',1,-1)),
}
LIP_PAD_FIELDS=frozenset(name for options in LIP_PAD_OPTIONS.values() for name,_,_ in options)
BATTERY_FIELDS={'BatteryReferenceEnabled','BatteryWidth','BatteryLength','BatteryHeight','BatteryMass',
 'BatteryMount','BatteryX','BatteryY','BatteryRotation','LiPoPadEnabled','LiPoPadWidth','LiPoPadLength',
 'LiPoPadFrontReach','LiPoPadRearReach','LiPoPadOutlineWidthScale','LiPoPadOutlineLengthScale','LiPoPadThickness','LiPoPadShape','LiPoPadCornerRadius','LiPoPadFollowPlate','LiPoPadCopyAirflow','LiPoPadCoverCountersunk','LiPoPadPattern',
 'LiPoPadPatternRelief','LiPoPadSideLips','LiPoPadLipHeight','LiPoPadLipWidth','LiPoPadLipEndInset','LiPoPadGrooveWidth','LiPoPadGrooveDepth','LiPoPadGroovePitch','LiPoPadDensity','LiPoPadLayout','LiPoPadSplitGap','LiPoPadPocketNumber','LiPoPadPocketClearance'} | PAD_TEXT_FIELDS | LIP_PAD_FIELDS

def battery_point(p,x,y):
 a=math.radians(p.BatteryRotation);c,s=math.cos(a),math.sin(a)
 return (p.BatteryX+x*c-y*s,p.BatteryY+x*s+y*c)

def mounting_role(p):return 'TopPlate' if p.BatteryMount=='Top plate' else 'BottomPlate'

def battery_levels(p):
 from .parameters import plate_levels
 top=plate_levels(p)['top_z']+p.TopThickness
 t=pad_projection(p) if p.LiPoPadEnabled else 0.
 rise=grip_rise(p) if p.LiPoPadEnabled else 0.
 if p.BatteryMount=='Top plate':return dict(pad_z=top,battery_z=top+t+rise)
 return dict(pad_z=-t,battery_z=-t-rise-p.BatteryHeight)

GRIP_PATTERNS=('Solid','Transverse grooves','Cross grooves','Longitudinal grooves','Diagonal grooves','Diamond grooves','Chevron grooves','Zigzag grooves','Rectangular rings','Dimple grid','Staggered dimples','Dash grid','Basket weave','Hexagon cells','Honeycomb','Wavy grooves','Brick joints','Herringbone','Plus grid','X grid','Square islands','Diamond islands','Triangular lattice','Ladder grooves','Interrupted ribs','Fish scale grooves')
MAX_GRIP_SEGMENTS=512

def grip_rise(p):
 return p.LiPoPadGrooveDepth if p.LiPoPadPattern!='Solid' and p.LiPoPadPatternRelief=='Embossed' else 0.

def requested_lip_sides(p):
 return {'Off':(), 'Both sides':(-1,1), 'Left side':(-1,), 'Right side':(1,)}.get(p.LiPoPadSideLips,())

def _lip_sections(p,side):
 """Selected Y halves on this outer side; 0 means the whole length."""
 if p.LiPoPadLayout=='Single':return (0,)
 return tuple(y for name,x,y in LIP_PAD_OPTIONS.get(p.LiPoPadLayout,())
              if x in (0,side) and getattr(p,name))

def lip_sides(p):
 return tuple(side for side in requested_lip_sides(p) if _lip_sections(p,side))

def lip_regions(p,bounds,edges,split_bounds=None):
 """Rectangular wall footprints on the straight, global X extrema only.

 Edges are endpoint pairs of straight exterior segments in frame coordinates.
 The unsplit battery-facing outline defines the left/right limits; a recessed
 parallel edge or a diagonal/rounded transition can never seed a wall.
 The preview and the exact CAD use the same selection and split rules.
 """
 x0,y0,x1,y1=bounds;w=x1-x0;inset=p.LiPoPadLipEndInset
 sides=lip_sides(p)
 if not sides:return ()
 if y1-y0<=2*inset or w<=0:raise ValueError('Side lip end inset consumes the pad length.')
 width=p.LiPoPadLipWidth
 if width>w/3:raise ValueError('Side lip width must not exceed one third of the finished pad width.')
 # Numerical tolerance only, independent of wall thickness. Do not treat
 # a near-maximum or sloped edge as an outermost straight segment.
 eps=1e-5;segments=tuple(edges);result=[]
 sb=split_bounds if split_bounds is not None else bounds;cy=(sb[1]+sb[3])/2
 for side in sides:
  x=x0 if side<0 else x1
  sections=_lip_sections(p,side);lo,hi=y0+inset,y1-inset
  if 0 not in sections and len(sections)==1:
   if sections[0]>0:lo=max(lo,cy+p.LiPoPadSplitGap/2)
   else:hi=min(hi,cy-p.LiPoPadSplitGap/2)
  if hi<=lo:continue
  spans=[]
  for (ax,ay),(bx,by) in segments:
   if abs(ax-x)>eps or abs(bx-x)>eps or abs(bx-ax)>eps:continue
   start=max(lo,min(ay,by));end=min(hi,max(ay,by))
   if end-start>eps:spans.append((start,end))
  # Merge adjacent collinear fragments, but never bridge a physical notch.
  merged=[]
  for start,end in sorted(spans):
   if merged and start<=merged[-1][1]+eps:
    merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
   else:merged.append((start,end))
  a,b=(x,x+width) if side<0 else (x-width,x)
  result.extend((side,(a,start,b,end)) for start,end in merged)
 return tuple(result)


def grip_point(p,x,y):
 return (x,y) if p.LiPoPadShape in ('Mounting plate outline','Pocket insert') else battery_point(p,x,y)

def grip_bounds(p,bounds):
 """Convert the finished frame-space pad bounds to the pattern coordinate system."""
 if p.LiPoPadShape in ('Mounting plate outline','Pocket insert'):return bounds
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
 if kind in ('Hexagon cells','Honeycomb'):
  # Legacy hexagons use radius; Honeycomb specifies the distance across flats.
  radius=pitch if kind=='Hexagon cells' else pitch/math.sqrt(3);dy=math.sqrt(3)*radius;dx=1.5*radius;seen=set()
  for i in range(math.floor((xmin-radius)/dx),math.ceil((xmax+radius)/dx)+1):
   for j in range(math.floor((ymin-radius)/dy)-1,math.ceil((ymax+radius)/dy)+1):
    x,y=i*dx,j*dy+(dy/2 if i%2 else 0)
    pts=tuple((x+radius*math.cos(k*math.pi/3),y+radius*math.sin(k*math.pi/3)) for k in range(6))
    for a,b in zip(pts,pts[1:]+pts[:1]):
     key=tuple(sorted((tuple(round(v,7) for v in a),tuple(round(v,7) for v in b))))
     if key not in seen:
      seen.add(key)
      # Keep the denser honeycomb bounded by the actual padded rectangle.
      if kind=='Honeycomb':
       r=p.LiPoPadGrooveWidth/2
       if max(a[0],b[0])+r<xmin or min(a[0],b[0])-r>xmax or max(a[1],b[1])+r<ymin or min(a[1],b[1])-r>ymax:continue
      add(a,b)
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
  if name in LIP_PAD_FIELDS:continue
  if name in ('BatteryX','BatteryY','BatteryRotation','BatteryMount','BatteryReferenceEnabled','LiPoPadEnabled','LiPoPadShape','LiPoPadPattern','LiPoPadFollowPlate','LiPoPadCopyAirflow','LiPoPadCoverCountersunk','LiPoPadLayout','LiPoPadSplitGap','LiPoPadPocketNumber','LiPoPadPocketClearance','LiPoPadPatternRelief','LiPoPadSideLips','LiPoPadLipHeight','LiPoPadLipWidth','LiPoPadLipEndInset'):continue
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
 if p.LiPoPadEnabled:
  if p.LiPoPadPatternRelief not in ('Debossed','Embossed'):errors.append('Unknown LiPo grip relief.')
  if p.LiPoPadSideLips not in ('Off','Both sides','Left side','Right side'):errors.append('Unknown LiPo side lip setting.')
  elif lip_sides(p):
   for name,low,high in (('LiPoPadLipHeight',.2,20),('LiPoPadLipWidth',.3,12),('LiPoPadLipEndInset',0,100)):
    value=getattr(p,name)
    if not math.isfinite(value) or not low<=value<=high:errors.append(f'{name} must be {low:g}–{high:g} mm.')
  if p.LiPoPadLayout not in ('Single','Left / right','Front / rear','Four parts'):errors.append('Unknown LiPo pad layout.')
  if p.LiPoPadLayout!='Single' and not .1<=p.LiPoPadSplitGap<=50:errors.append('LiPo pad split gap must be 0.1–50 mm.')
  if p.LiPoPadShape=='Pocket insert':
   if not 0<=p.LiPoPadPocketClearance<=5:errors.append('Pocket fit clearance must be 0–5 mm per side.')
   try:
    depth=pocket_depth(p)
    if p.LiPoPadThickness+1e-8<2*depth:errors.append(f'Pocket insert total thickness must be at least {2*depth:g} mm (twice the deepest selected pocket, {depth:g} mm).')
   except ValueError as exc:errors.append(str(exc))
 if not -180<=p.BatteryRotation<=180:errors.append('Battery rotation must be between -180 and 180 degrees.')
 if p.LiPoPadEnabled and p.LiPoPadPattern!='Solid':
  if p.LiPoPadPatternRelief=='Debossed' and p.LiPoPadGrooveDepth>=pad_projection(p):errors.append('Pad grooves must leave a continuous backing: groove depth must be less than the pad height above carbon.')
  if p.LiPoPadGroovePitch<=p.LiPoPadGrooveWidth:errors.append('Pad groove pitch must exceed groove width.')
  if p.LiPoPadGroovePitch>0:
   try:
    if p.LiPoPadShape=='Pocket insert':
     # Exact pocket bounds and grip density are validated at CAD generation.
     bounds=None
    elif p.LiPoPadShape=='Mounting plate outline':
     from .parameters import top_bounds,bottom_bounds
     rear,front=top_bounds(p) if p.BatteryMount=='Top plate' else bottom_bounds(p);rear,front=pad_reach_bounds(p,rear,front);w=max(p.TopWidth,p.TopCentreWidth) if p.BatteryMount=='Top plate' else max(p.BodyWidth,p.BottomCentreWidth);w*=p.LiPoPadOutlineWidthScale/100
     bounds=(-w/2,rear,w/2,front)
    else:bounds=None
    if p.LiPoPadShape!='Pocket insert':groove_segments(p,bounds)
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
 if p.LiPoPadShape=='Pocket insert' or p.LiPoPadCopyAirflow or (p.LiPoPadShape!='Mounting plate outline' and not p.LiPoPadFollowPlate):
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
 if p.LiPoPadShape=='Pocket insert' or not p.LiPoPadCoverCountersunk:return ()
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
 if p.LiPoPadShape!='Pocket insert' and not p.LiPoPadCoverCountersunk:return tuple(clearances)
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


def layout_count(p):
 return {'Single':1,'Left / right':2,'Front / rear':2,'Four parts':4}[p.LiPoPadLayout]


def split_rectangles(p,bounds):
 """Frame-aligned gap rectangles, centred on the finished pad bounds."""
 if p.LiPoPadLayout=='Single':return ()
 x0,y0,x1,y1=bounds;cx,cy=(x0+x1)/2,(y0+y1)/2;g=p.LiPoPadSplitGap;out=[]
 if p.LiPoPadLayout in ('Left / right','Four parts'):
  if g>=x1-x0:raise ValueError('LiPo pad split gap consumes its width.')
  out.append((cx-g/2,y0-1,g,y1-y0+2))
 if p.LiPoPadLayout in ('Front / rear','Four parts'):
  if g>=y1-y0:raise ValueError('LiPo pad split gap consumes its length.')
  out.append((x0-1,cy-g/2,x1-x0+2,g))
 return tuple(out)


def split_pad(p,shape):
 import FreeCAD as App
 import Part
 b=shape.BoundBox
 for x,y,w,h in split_rectangles(p,(b.XMin,b.YMin,b.XMax,b.YMax)):
  shape=shape.cut(Part.makeBox(w,h,b.ZLength+.04,App.Vector(x,y,b.ZMin-.02))).removeSplitter()
 return shape


def pocket_choices(p):
 """Saved pattern rows; the selection travels with the pattern, not its number."""
 from .cutouts import parse_patterns
 n=p.LiPoPadPocketNumber
 if not math.isfinite(n) or n< -1 or n!=int(n):raise ValueError('Invalid pocket selector.')
 return tuple((i,v, bool(v['pad_insert']) if n==-1 else n in (0,i))
              for i,v in enumerate(parse_patterns(p.CutoutPatterns),1)
              if v['role']=='TopPlate' and v['mode']=='Pocket')


def pocket_patterns(p):
 from .cutouts import pattern_instances
 if p.BatteryMount!='Top plate':raise ValueError('Pocket inserts require a top-mounted battery: bottom plate pockets are machined from the inner face.')
 selected=[v for _,v,checked in pocket_choices(p) if checked and v['enabled']]
 if not selected:raise ValueError('Select one or more enabled top-plate pockets using Choose pockets in the LiPo pad settings.')
 return tuple(dict(v,_cnc_radius=p.CNCToolRadius) for pattern in selected for v in pattern_instances(pattern))


def pocket_depth(p):
 return max(v['depth'] for v in pocket_patterns(p))


def pad_projection(p):
 """Thickness is total at the deepest selected floor; all tops are level.
 Invalid/incomplete selections remain editable in the preview.
 """
 if p.LiPoPadShape=='Pocket insert':
  try:return max(0.,p.LiPoPadThickness-pocket_depth(p))
  except ValueError:return max(0.,p.LiPoPadThickness)
 return p.LiPoPadThickness


def pocket_pad(p,carrier,surface):
 """Build a common, level top and stepped underside from actual machined floors.
 The clearance is applied to the union outline, then to each deeper step.
 """
 import FreeCAD as App
 import Part
 from .airflow_geometry import profile_tool
 from .cutouts import parse_patterns
 from .pocket_regions import planar_union
 patterns=pocket_patterns(p);depth=max(v['depth'] for v in patterns);top=surface+p.LiPoPadThickness-depth;eps=1e-6
 if p.LiPoPadThickness+1e-8<2*depth:raise ValueError('Pocket insert must be at least twice the deepest selected pocket depth.')
 def merge(faces):return planar_union(faces,surface)
 def intersect(first,second):
  # Common can leave coplanar fragments. Merge before offsetting, or
  # fit clearance becomes an unintended gap along each source contour.
  return merge(first.common(second).Faces)
 def inset(region):
  out=[];clearance=p.LiPoPadPocketClearance
  for face in region.Faces:
   if face.Area<=eps:continue
   if clearance<=1e-9:out.append(face);continue
   try:
    offset=face.makeOffset2D(-clearance,join=0)
    if not offset.Faces and offset.Wires:offset=Part.makeFace(offset.Wires,'Part::FaceMakerBullseye')
    fitted=intersect(offset,face)
    if fitted is None or fitted.Area>=face.Area-1e-7 or not fitted.isValid():raise ValueError('Invalid offset.')
    if min(a.distToShape(b)[0] for a in fitted.Wires for b in face.Wires)<clearance-1e-5:raise ValueError('Insufficient clearance.')
    out.extend(fitted.Faces)
   except Exception as exc:raise ValueError('Pocket fit offset failed; reduce clearance or enlarge the selected pocket/step.') from exc
  return merge(out)
 # Project cutter footprints onto one plane. Only selected cuts define
 # the desired underside depth; an unrelated deeper crossing may leave
 # a gap below the insert, never silently become part of its design.
 profiles_by_depth={}
 for v in patterns:
  tool=profile_tool(v,surface,.02)
  profiles_by_depth.setdefault(v['depth'],[]).extend(f for f in tool.Faces if f.BoundBox.ZLength<eps and abs(f.CenterOfMass.z-surface)<eps)
 selection=merge([f for faces in profiles_by_depth.values() for f in faces])
 if selection is None:raise ValueError('Selected pockets have no planar profile.')
 # Clip to projected actual machined floors, preserving through-holes,
 # plate edges and unrelated material above the selected recesses.
 depths={v['depth'] for v in parse_patterns(p.CutoutPatterns) if v['enabled'] and v['role']=='TopPlate' and v['mode']=='Pocket'}
 floor_faces=[]
 for f in carrier.Faces:
  if f.BoundBox.ZLength<eps and f.normalAt(0,0).z>.99999 and any(abs(f.CenterOfMass.z-(surface-d))<eps for d in depths):
   floor_faces.append(f)
 floors=merge(floor_faces)
 if floors is None:raise ValueError('No usable machined pocket floor found for the chosen pockets.')
 usable=intersect(floors,selection)
 if usable is None:raise ValueError('No usable machined pocket floor found for the chosen pockets.')
 footprint=inset(usable)
 if footprint is None or not footprint.Faces:raise ValueError('Pocket fit leaves no printable pad area.')
 # Extrude each complete footprint from its shallowest floor to the
 # finished top. Deeper extensions overlap only below the upper surface.
 selected_depths=sorted(profiles_by_depth);shallow=selected_depths[0]
 solids=[]
 for f in footprint.Faces:
  face=f.copy();face.translate(App.Vector(0,0,-shallow))
  solids.append(face.extrude(App.Vector(0,0,top-surface+shallow)))
 for i,d in enumerate(selected_depths[1:],1):
  cumulative=merge([f for dd in selected_depths[i:] for f in profiles_by_depth[dd]])
  if cumulative is None:raise ValueError('Selected pocket step has no planar profile.')
  step=intersect(cumulative,usable)
  if step is None:raise ValueError('Selected pocket step has no usable floor.')
  lower=inset(step)
  if lower is None:raise ValueError('Pocket step leaves no printable pad area.')
  region=intersect(lower,footprint)
  if region is None:raise ValueError('Pocket step leaves no printable pad area.')
  for f in region.Faces:
   face=f.copy();face.translate(App.Vector(0,0,-d))
   solids.append(face.extrude(App.Vector(0,0,d+min(.02,(top-surface)/2))))
 shape=solids[0].multiFuse(solids[1:]) if len(solids)>1 else solids[0]
 if shape.isNull() or not shape.isValid() or not shape.Solids:raise ValueError('Cannot fuse the selected pocket inserts. Adjust the pocket layout or clearance.')
 pieces=[s.removeSplitter() for s in shape.Solids]
 for piece in pieces:
  caps=[f for f in piece.Faces if f.BoundBox.ZLength<eps and abs(f.CenterOfMass.z-top)<eps]
  if not piece.isValid() or len(caps)!=1:raise ValueError('Pocket insert could not form a seamless top surface; adjust the pocket layout.')
 return pieces[0] if len(pieces)==1 else Part.makeCompound(pieces)


def _surface_faces(shape,level):
 """Exact flat battery-facing caps, independent of face orientation."""
 return [f for f in shape.Faces if f.BoundBox.ZLength<1e-6 and abs(f.BoundBox.ZMin-level)<1e-6 and f.Area>1e-8]


def side_lip_faces(p,unsplit,level):
 """Seed straight walls from exact exterior line edges of the unsplit cap.
 No directional outline offset: that would also raise notches and shoulders.
 The final material and split masks retain holes and separate pad pieces.
 """
 import FreeCAD as App
 import Part
 if not lip_sides(p):return ()
 caps=_surface_faces(unsplit,level)
 if not caps:raise ValueError('Cannot find the pad surface for retaining lips.')
 boxes=[f.optimalBoundingBox(False) for f in caps]
 bounds=(min(b.XMin for b in boxes),min(b.YMin for b in boxes),max(b.XMax for b in boxes),max(b.YMax for b in boxes))
 edges=[]
 line_types=(Part.Line,Part.LineSegment)
 for cap in caps:
  for edge in cap.OuterWire.Edges:
   if not isinstance(edge.Curve,line_types) or len(edge.Vertexes)!=2:continue
   a,b=(v.Point for v in edge.Vertexes)
   edges.append(((a.x,a.y),(b.x,b.y)))
 b=unsplit.BoundBox
 regions=lip_regions(p,bounds,edges,(b.XMin,b.YMin,b.XMax,b.YMax))
 result=[];found=set()
 for side,(x0,y0,x1,y1) in regions:
  pts=[App.Vector(x,y,level) for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0))]
  window=Part.Face(Part.makePolygon(pts))
  for cap in caps:
   band=cap.common(window).removeSplitter()
   faces=[f for f in band.Faces if f.Area>1e-7]
   if faces:result.extend(faces);found.add(side)
 for side in lip_sides(p):
  if side not in found:
   App.Console.PrintWarning('RotorForge LiPo pad: no straight outermost '+('left' if side<0 else 'right')+' edge in the selected pad section; no retaining lip added on that side.\n')
 return tuple(result)


def _surface_prism(piece,level,sign,inside,outside):
 import FreeCAD as App
 import Part
 caps=_surface_faces(piece,level)
 solids=[]
 for cap in caps:
  f=cap.copy();f.translate(App.Vector(0,0,-sign*inside))
  solids.append(f.extrude(App.Vector(0,0,sign*(inside+outside))))
 if not solids:raise ValueError('Cannot locate the battery-facing pad surface for raised features.')
 return solids[0] if len(solids)==1 else Part.makeCompound(solids)


def _add_pad_relief(p,base,level,sign,grip_tools,lip_faces,layout,projection):
 """Fuse real raised geometry onto each original pad solid separately.
 Mask everything by the original cap including holes and split gaps.
 """
 import FreeCAD as App
 import Part
 from .geometry_bounds import box_distance
 rise=grip_rise(p)
 lip_height=rise+p.LiPoPadLipHeight if lip_faces else 0.
 # Lip bases extend beneath recesses so a cross-groove cannot detach a wall.
 inset=min(projection,.02+(p.LiPoPadGrooveDepth if p.LiPoPadPattern!='Solid' and not rise else 0.))
 lip_tools=[]
 for face in lip_faces:
  f=face.copy();f.translate(App.Vector(0,0,-sign*inset))
  lip_tools.append(f.extrude(App.Vector(0,0,sign*(inset+lip_height))))
 keep=None
 if layout:
  x0,y0,x1,y1=layout[2];h=max(rise,lip_height)+inset+2
  keep=Part.makeBox(x1-x0,y1-y0,2*h,App.Vector(x0,y0,level-h))
 result=[];added_grip=False;added_lips=False
 for piece in base.Solids:
  additions=[]
  for tools,inside,outside,is_lip in ((grip_tools,.02,rise,False),(lip_tools,inset,lip_height,True)):
   if not tools:continue
   mask=_surface_prism(piece,level,sign,inside,outside);mb=mask.BoundBox
   for tool in tools:
    if box_distance(mb,tool.BoundBox)>1e-7:continue
    clipped=tool.common(mask)
    if clipped.Solids and keep is not None and box_distance(clipped.BoundBox,keep.BoundBox)<=1e-7:clipped=clipped.cut(keep)
    valid=[a for a in clipped.Solids if a.Volume>1e-8]
    if valid:
     additions.extend(valid)
     if is_lip:added_lips=True
     else:added_grip=True
  if additions:
   merged=piece.multiFuse(additions).removeSplitter()
   if not merged.isValid() or len(merged.Solids)!=1:raise ValueError('Raised pad features did not fuse into one printable piece. Adjust the pattern or lips.')
   result.append(merged)
  else:result.append(piece)
 if grip_tools and not added_grip:raise ValueError('No embossed pattern fits the finished pad. Adjust spacing or lettering.')
 if lip_faces and not added_lips:raise ValueError('No retaining lip fits the finished pad. Adjust the lip or lettering dimensions.')
 return result[0] if len(result)==1 else Part.makeCompound(result)


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
 projection=pad_projection(p)
 pocket=p.LiPoPadShape=='Pocket insert'
 if pocket:
  shape=pocket_pad(p,carrier,z)
  mark('pocket floor and fit')
 # The secondary plate is constructed only at Create/Update when the user
 # wants the LiPo pad to bridge carbon airflow openings. All mounting and
 # strap access holes are retained; the finished carbon plate is unchanged.
 if carrier_without_airflow is not None:
  carrier=carrier_without_airflow
 seats=pad_flush_seats(p) if not pocket else ()
 # The lower plate's actual screw rims are on ZMin, not its inner upper face.
 sign=-1 if seats and p.BatteryMount=='Bottom plate' else 1
 faces=[f for f in carrier.Faces if sign*f.normalAt(0,0).z>.99999] if not pocket else []
 if seats:
  surface=seats[0]['z'];faces=[f for f in faces if abs(f.CenterOfMass.z-surface)<1e-6]
  if not faces:raise ValueError('Could not locate the battery-facing screw seating plane.')
 if not pocket:
  face=max(faces,key=lambda f:f.Area).copy();face.translate(App.Vector(0,0,z-face.CenterOfMass.z))
  if seats:face=pad_face_with_flush_holes(p,face,seats)
 if pocket:pass
 elif p.LiPoPadShape=='Mounting plate outline':
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
 low=shape.BoundBox.ZMin
 tools=[cylinder(x,y,r,low-.01,z+projection-low+.02) for x,y,r in pad_fastener_clearances(p)]
 shape_bounds=shape.BoundBox
 tools=[tool for tool in tools if box_distance(shape_bounds,tool.BoundBox)<=1e-6]
 if tools:shape=shape.cut(Part.makeCompound(tools)).removeSplitter()
 mark('fastener clearances')
 if shape.isNull() or not shape.Solids:raise ValueError('LiPo pad has no material after clearances.')
 surface_sign=-1 if p.BatteryMount=='Bottom plate' else 1
 surface=z if surface_sign<0 else z+projection
 lips=side_lip_faces(p,shape,surface) if grooves and lip_sides(p) else ()
 shape=split_pad(p,shape)
 pieces=len(shape.Solids)
 if pieces==0:raise ValueError('Split gap leaves no printable pad material.')
 if not pocket and pieces!=layout_count(p):raise ValueError('LiPo pad layout did not produce the requested number of connected pieces. Adjust gap, outline or openings.')
 mark('pad splits')
 # The outline-only export deliberately omits all shallow surface machining.
 layout=None
 grip_box=None
 if grooves and p.LiPoPadTextEnabled:
  if shape.isNull():raise ValueError('LiPo pad is empty before lettering.')
  box=grip_box=shape.optimalBoundingBox(False)
  layout=text_layout(p,(box.XMin,box.YMin,box.XMax,box.YMax))
  if layout:
   depth=p.LiPoPadTextDepth
   bottom=z if p.BatteryMount=='Bottom plate' else z+projection-depth
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
  rise=grip_rise(p)
  bottom=(surface-rise if surface_sign<0 else surface-.02) if rise else (z-.01 if surface_sign<0 else surface-p.LiPoPadGrooveDepth)
  tool_height=rise+.02 if rise else p.LiPoPadGrooveDepth+.01
  box=grip_box if grip_box is not None else shape.optimalBoundingBox(False);bounds=grip_bounds(p,(box.XMin,box.YMin,box.XMax,box.YMax))
  segments=clipped_grip_segments(p,groove_segments(p,bounds),(box.XMin,box.YMin,box.XMax,box.YMax))
  radius=p.LiPoPadGrooveWidth/2
  if layout:
   x0,y0,x1,y1=layout[2]
   # A capsule wholly inside the reserved rectangle is removed by the old
   # cutter subtraction anyway. Skip creating its OCC solid entirely.
   eps=1e-7
   if p.LiPoPadGrooveDepth<projection:
    segments=tuple((a,b) for a,b in segments if not (min(a[0],b[0])-radius>x0+eps and max(a[0],b[0])+radius<x1-eps and min(a[1],b[1])-radius>y0+eps and max(a[1],b[1])+radius<y1-eps))
  tools=[capsule(a,b,radius,bottom,tool_height) for a,b in segments]
  if layout:
   x0,y0,x1,y1=layout[2]
   keep=Part.makeBox(x1-x0,y1-y0,projection+2*rise+.04,App.Vector(x0,y0,z-rise-.02))
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
  if rise and not tools:raise ValueError('No embossed grip pattern fits the pad. Adjust spacing or lettering.')
  if rise or lips:
   # Raise real ribs/walls on the uncut backing. Protect the wall footprint
   # from recess cutters so cross-grooves cannot undermine the side walls.
   if lips and not rise and tools:
    protected=[]
    for f in lips:
     face=f.copy();face.translate(App.Vector(0,0,-surface_sign*(p.LiPoPadGrooveDepth+.02)))
     protected.append(face.extrude(App.Vector(0,0,surface_sign*(p.LiPoPadGrooveDepth+.04))))
    clipped=[]
    for tool in tools:
     for wall in protected:
      if not tool.Solids:break
      if box_distance(tool.BoundBox,wall.BoundBox)<=1e-7:tool=tool.cut(wall)
      if not tool.Solids:break
     clipped.extend(tool.Solids)
    tools=clipped
   shape=_add_pad_relief(p,shape,surface,surface_sign,tools if rise else (),lips,layout,projection)
  if tools and not rise:
   # Honeycomb has shared vertices; fuse its overlapping capsules into a
   # valid cutter rather than subtracting an overlapping compound.
   cutters=(tools[0].multiFuse(tools[1:]).removeSplitter() if len(tools)>1 else tools[0]) if p.LiPoPadPattern=='Honeycomb' else Part.makeCompound(tools)
   shape=shape.cut(cutters).removeSplitter()
  if layout:shape=shape.cut(Part.makeCompound(letter_tools)).removeSplitter()
  mark('grip and lettering booleans')
 if shape.isNull() or not shape.isValid() or len(shape.Solids)!=pieces or any(s.Volume<=1e-7 for s in shape.Solids):
  raise ValueError('LiPo pad pieces must remain connected after grooves and lettering. Adjust the layout or surface details.')
 if pocket and shape.common(carrier).Volume>1e-6:raise ValueError('Pocket insert intersects the carrier; increase fit clearance or simplify pockets.')
 if lips and p.BatteryReferenceEnabled and shape.common(battery_envelope(p)).Volume>1e-5:
  App.Console.PrintWarning('RotorForge LiPo pad: retaining lips overlap the battery envelope. Review the battery width, pad outline and lip thickness before printing.\n')
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
