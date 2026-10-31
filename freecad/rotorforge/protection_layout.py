"""Portable guard reach, vent profiles, USB opening and motor service slots."""
import math

def guard_between_plates(p):
 return p.FlexGuardFitMode=='Between plates'

def guard_plate_gap(p):
 """Inset walls bear on the plate faces; wrap walls retain assembly relief."""
 if guard_between_plates(p):return 0.
 return min(.15,max(0.,p.FlexGuardClearance))

def guard_wall_inner_x(p,edge,sign):
 """Inner wall face: outside a wrapped edge or fully underneath a clamp edge."""
 offset=-p.FlexGuardClearance-p.FlexGuardWall if guard_between_plates(p) else p.FlexGuardClearance
 return edge+sign*offset

def guard_layout(p):
 if not p.FlexSideGuards:return ()
 from .mount_bands import rear_pair,stack_pair,front_stack_pair,rear_guard_band
 from .parameters import plate_levels,three_plate
 rear=rear_pair(p);fc=stack_pair(p);forward=front_stack_pair(p) if (p.FlexGuardExtendFront or p.FlexGuardCloseFront) else fc
 levels=plate_levels(p);items=[];gap=guard_plate_gap(p);inner_top=levels['top_z']-gap;top=levels['top_z']+p.TopThickness
 bottom=levels['mid_z'] if three_plate(p) else 0.
 if guard_between_plates(p):bottom=levels['deck_z']+gap;top=inner_top
 for index,(sign,name) in enumerate(((-1,'Left'),(1,'Right'))):
  stands={s['point']:s for s in (forward[index],fc[index],rear[index])};stands=tuple(sorted(stands.values(),key=lambda s:-s['point'][1]))
  bands=tuple((s['base']+.15,s['base']+s['length']-.15) if s['point']==forward[index]['point'] else rear_guard_band(p) if s['point']==rear[index]['point'] else (inner_top-10,inner_top) for s in stands)
  if guard_between_plates(p):bands=tuple((max(low,bottom),min(high,top)) for low,high in bands)
  items.append(dict(role='ElectronicsGuard'+name,sign=sign,x=sign*(max(abs(s['point'][0]) for s in stands)+p.StandoffDiameter/2+p.FlexGuardWall),z=bottom,top=top,inner_bottom=levels['deck_z']+gap,inner_top=inner_top,deck_z=levels['deck_z'],grip=6.,stands=stands,bands=bands,rear=rear[index]['point'][1],front=forward[index]['point'][1],lower_role='MidPlate' if three_plate(p) else 'BottomPlate'))
 return tuple(items)

def guard_rotor_windows(p,g):return ()

def usb_window(p,g):
 if not ((p.FlexGuardExtendFront or p.FlexGuardCloseFront) and p.FlexGuardUSBEnabled):return None
 side='Left' if g['sign']<0 else 'Right'
 if p.FlexGuardUSBSide not in (side,'Both'):return None
 z=g['deck_z']+p.FlexGuardUSBZ;h=p.FlexGuardUSBHeight
 low,high=z-h/2,z+h/2
 # Avoid a fragile top sliver: continue the cut through the physical top edge.
 if high>g['top']-p.FlexGuardWall:
  high=max(high,g['top']+2.);z=(low+high)/2;h=high-low
 return (p.StackOffsetY+p.FlexGuardUSBY,z,p.FlexGuardUSBWidth,h)

def guard_vent_sections(p,g):
 """Rear VTX and forward FC regions in frame Y, independent of post spacing."""
 lo=g['rear']+p.FlexGuardRearInset;hi=g['front']-p.FlexGuardFrontInset
 boundary=max(lo,min(hi,p.StackOffsetY-p.StackSpacing/2+p.FlexGuardVentBoundaryOffset))
 return (dict(name='VTX',enabled=p.FlexGuardVTXVents,rear=lo+p.FlexGuardVTXVentRearInset,front=boundary-p.FlexGuardVTXVentFrontInset,shape=p.FlexGuardVentShape,width=p.FlexGuardVentWidth,web=p.FlexGuardVentWeb,height=p.FlexGuardSlotHeight,rows=p.FlexGuardSlotCount,zoffset=p.FlexGuardVTXVentZOffset),dict(name='FC',enabled=p.FlexGuardFCVents,rear=boundary+p.FlexGuardFCVentRearInset,front=hi-p.FlexGuardFCVentFrontInset,shape=p.FlexGuardFCVentShape,width=p.FlexGuardFCVentWidth,web=p.FlexGuardFCVentWeb,height=p.FlexGuardFCSlotHeight,rows=p.FlexGuardFCSlotCount,zoffset=p.FlexGuardFCVentZOffset))

def guard_vents(p,g):
 if p.FlexGuardStyle!='Vented':return ()
 wall=p.FlexGuardWall;radius=(p.StandoffDiameter+p.FlexGuardFit)/2+wall
 rows=sorted({s['point'][1] for s in g['stands']});items=[]
 from .parameters import mid_bounds,three_plate
 for section in guard_vent_sections(p,g):
  if not section['enabled']:continue
  web=max(wall,section['web']);count=max(1,min(6,int(round(section['rows']))))
  for a,b in zip(rows,rows[1:]):
   start=max(a+radius+web,section['rear']+web);end=min(b-radius-web,section['front']-web)
   boundaries=[start,end]
   if three_plate(p) and start<mid_bounds(p)[1]<end:boundaries.insert(1,mid_bounds(p)[1])
   for first,last in zip(boundaries,boundaries[1:]):
    if last<=first:continue
    start1=first+(web if first!=start else 0);end1=last-(web if last!=end else 0)
    if end1<=start1:continue
    z0=g['inner_bottom']
    if three_plate(p) and (first+last)/2>mid_bounds(p)[1]:z0=max(z0,g['inner_top']-10)
    available=g['inner_top']-z0
    nrows=max(1,min(count,int((available-web)/(min(1.5,section['height'])+web))))
    h=min(section['height'],(available-(nrows+1)*web)/nrows)
    if h<=.1:continue
    span=nrows*h+(nrows-1)*web;travel=max(0.,(available-span)/2-web);dz=max(-travel,min(travel,section['zoffset']))
    widths=[((start1+end1)/2,end1-start1)] if section['shape']=='Horizontal slots' else []
    if not widths:
     width=min(section['width'],end1-start1)
     if width<=0:continue
     n=max(1,int((end1-start1+web)/(width+web)));length=n*width+(n-1)*web
     widths=[((start1+end1-length)/2+width/2+i*(width+web),width) for i in range(n)]
    for y,width in widths:
     for i in range(nrows):items.append(dict(section=section['name'],shape=section['shape'],y=y,z=z0+available/2+dz+(i-(nrows-1)/2)*(h+web),width=width,height=h))
 return tuple(items)

def vent_polygon(item):
 w,h=item['width'],item['height'];shape=item['shape']
 if shape=='Circles':
  radius=min(w,h)/2
  return tuple((radius*math.cos(i*math.pi/24),radius*math.sin(i*math.pi/24)) for i in range(48))
 profiles={
 'Triangles':((-1,-1),(1,-1),(0,1)),
 'Inverted triangles':((-1,1),(0,-1),(1,1)),
 'Octagons':((-1,-.42),(-.42,-1),(.42,-1),(1,-.42),(1,.42),(.42,1),(-.42,1),(-1,.42)),
 'Slanted slots':((-1,-1),(.35,-1),(1,1),(-.35,1)),
 'Arrows':((-1,-.5),(.15,-.5),(.15,-1),(1,0),(.15,1),(.15,.5),(-1,.5)),
 'Shields':((-1,1),(1,1),(1,-.15),(.6,-.65),(0,-1),(-.6,-.65),(-1,-.15)),
 'Crosses':((-.35,-1),(.35,-1),(.35,-.35),(1,-.35),(1,.35),(.35,.35),(.35,1),(-.35,1),(-.35,.35),(-1,.35),(-1,-.35),(-.35,-.35)),
 'Hourglasses':((-1,-1),(1,-1),(.45,0),(1,1),(-1,1),(-.45,0))}
 if shape in profiles:return tuple((x*w/2,y*h/2) for x,y in profiles[shape])
 if shape=='Teardrops':
  # Rounded lower bowl and a broad taper; all vertices stay within the vent envelope.
  return tuple((w/2*math.cos(t),h*(-.15+.35*math.sin(t))) for t in (math.pi+i*math.pi/24 for i in range(25)))+((0,h/2),)
 if shape=='Hexagons':return ((-w/2,0),(-w/4,-h/2),(w/4,-h/2),(w/2,0),(w/4,h/2),(-w/4,h/2))
 if shape=='Diamonds':return ((0,-h/2),(w/2,0),(0,h/2),(-w/2,0))
 if shape=='Chevrons':return ((-w/2,-h/2),(0,-h/6),(w/2,-h/2),(w/2,h/6),(0,h/2),(-w/2,h/6))
 return ()

def motor_service_slots(p,arm):
 if p.FlexProtectorRetention!='Linked screw access':return ()
 radius=max(3.,p.MotorHoleDiameter/2+.2)
 return tuple((arm['motor'],point,radius) for point in arm['motor_holes'])

def grip_pad_bounds(p,g,stand,station):
 """Outboard-only bridge: leave the whole inboard sleeve perimeter circular."""
 sx,sy=stand['point'];wall_y,xb,xt,_=station;sign=g['sign'];w=p.FlexGuardWall
 radius=(p.StandoffDiameter+p.FlexGuardFit)/2+w
 outer=sign*max(sign*xb+w+.1,sign*xt+w+.1,sign*sx+.2)
 x0,x1=sorted((sx,outer))
 return x0,x1,min(sy-radius,wall_y-.2),max(sy+radius,wall_y+.2)

def outline_side_x(points,y,sign):
 xs=[]
 for (ax,ay),(bx,by) in zip(points,points[1:]+points[:1]):
  if min(ay,by)-1e-7<=y<=max(ay,by)+1e-7:
   if abs(by-ay)<1e-8:xs.extend((ax,bx))
   else:xs.append(ax+(bx-ax)*(y-ay)/(by-ay))
 xs=[x for x in xs if sign*x>=-1e-6]
 return (max(xs) if sign>0 else min(xs)) if xs else None


def guard_wire_openings(p,g):
 """Bottom-edge wire exits, anchored to stack Y and the local carrier edge."""
 if not p.FlexGuardWireEnabled:return ()
 side='Left' if g['sign']<0 else 'Right'
 if p.FlexGuardWireSide not in (side,'Both'):return ()
 from .parameters import three_plate,mid_bounds
 items=[]
 positions=(('Front',p.FlexGuardWireFrontY,p.FlexGuardWireWidth),('Rear',p.FlexGuardWireRearY,p.FlexGuardWireWidth))
 if guard_between_plates(p):
  positions=(('Combined',(p.FlexGuardWireFrontY+p.FlexGuardWireRearY)/2,abs(p.FlexGuardWireFrontY-p.FlexGuardWireRearY)+p.FlexGuardWireWidth),)
 for name,offset,w in positions:
  if name!='Combined' and p.FlexGuardWirePairs not in (name,'Both'):continue
  y=p.StackOffsetY+offset
  ends=[y-w/2,y+w/2]
  if name in ('Front','Combined'):
   transitions=[]
   if three_plate(p):transitions.append(mid_bounds(p)[1])
   if p.FlexGuardCloseFront and p.FPVEnabled:transitions.append(g['front'])
   ends=sorted(set(ends+[v for v in transitions if ends[0]<v<ends[-1]]))
  for left,right in zip(ends,ends[1:]):
   if right-left<1e-5:continue
   centre=(left+right)/2;bottom=g['z'];original_bottom=g['inner_bottom']
   if three_plate(p) and centre>mid_bounds(p)[1]:bottom=original_bottom=g['inner_top']-10
   if p.FlexGuardCloseFront and p.FPVEnabled and centre>=g['front']:
    original_bottom=p.BottomThickness+guard_plate_gap(p);bottom=original_bottom if guard_between_plates(p) else 0.
   items.append(dict(name=name,y=centre,bottom=bottom,width=right-left,height=p.FlexGuardWireHeight+original_bottom-bottom,source_width=w,source_y=y))
 return tuple(items)


def guard_vtx_window(p,g):
 """A hardware clearance window, separate from decorative ventilation."""
 if not (p.FPVEnabled and p.FlexGuardVTXOpening):return None
 side='Left' if g['sign']<0 else 'Right'
 if p.FlexGuardVTXSide not in (side,'Both'):return None
 from .fpv import vtx_deck_z
 y=p.VTXOffsetY+p.FlexGuardVTXY
 z=vtx_deck_z(p)+p.VTXHeight/2+p.FlexGuardVTXZ
 width=p.FlexGuardVTXLength or p.VTXLength+2*p.FlexGuardVTXClearance
 height=p.FlexGuardVTXHeight or p.VTXHeight+2*p.FlexGuardVTXClearance
 low,high=z-height/2,z+height/2
 if low<g['inner_bottom']+p.FlexGuardWall:low=min(low,g['z']-2.)
 return (y,(low+high)/2,width,high-low)


def grip_bridge(p,g,stand,station):
 """Rounded outboard support; the separate sleeve supplies the inner circle."""
 sx,sy=stand['point'];sign=g['sign'];x0,x1,_,_=grip_pad_bounds(p,g,stand,station)
 radius=(p.StandoffDiameter+p.FlexGuardFit)/2+p.FlexGuardWall;outer=x1 if sign>0 else x0
 return (sx,sy),(sign*max(sign*sx,sign*outer-radius),station[0]),radius


def closure_profile(p,g):
 """Rear edge of the actual camera wall, sampled at changes in its slope."""
 if not (p.FlexGuardCloseFront and p.FPVEnabled):return None
 from .fpv import camera_mounts
 mount=next(m for m in camera_mounts(p) if m['role'].endswith('Left' if g['sign']<0 else 'Right'))
 low=p.BottomThickness+guard_plate_gap(p) if guard_between_plates(p) else 0.;high=g['top'];points=mount['wall_profile']
 wall_low=min(z for y,z in points);wall_high=max(z for y,z in points)
 zs=sorted({low,high,*[z for y,z in points if low<z<high],(low+high)/2})
 def rear(z):
  # Outside the camera wall, continue its contact edge beside plate stock.
  z=max(wall_low,min(wall_high,z))
  hits=[]
  for (y0,z0),(y1,z1) in zip(points,points[1:]+points[:1]):
   if abs(z1-z0)<1e-8:
    if abs(z-z0)<1e-6:hits.extend((y0,y1))
   elif min(z0,z1)-1e-7<=z<=max(z0,z1)+1e-7:hits.append(y0+(y1-y0)*(z-z0)/(z1-z0))
  if not hits:raise ValueError('Camera side plates must span the bottom-to-top guard closure.')
  return min(hits)+p.FlexGuardCameraOverlap
 sections=tuple((z,rear(z)) for z in zs)
 # Keep the lower skirt at the forward posts; taper only an upper contact
 # rearward if a shorter top plate brings the camera wall behind that row.
 starts=tuple(min(g['front'],end-4.) for z,end in sections)
 return dict(start=g['front'],starts=starts,sections=sections,x=max(mount['plate_x']) if g['sign']>0 else min(mount['plate_x']))

def guard_strap_windows(p,g):
 """Full-width edge notches. Y remains in the frame axes, not wall tangent."""
 if not p.FlexGuardStraps:return ()
 from .parameters import strap_positions
 ys=strap_positions(p) if p.FlexGuardStrapAuto else (p.StackOffsetY+p.FlexGuardStrapY1,p.StackOffsetY+p.FlexGuardStrapY2)
 if p.FlexGuardStrapCount=='1 strap':ys=ys[:1]
 depth=p.FlexGuardStrapDepth;top=p.FlexGuardStrapEdge=='Top edge'
 bottom=g['top']-depth if top else g['z']-2
 height=depth+2
 return tuple(dict(y=y,z=bottom+height/2,width=p.FlexGuardStrapWidth,height=height,bottom=bottom,top=bottom+height) for y in ys)
