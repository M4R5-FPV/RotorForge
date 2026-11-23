"""Optional printable protectors derived from real pads and actual standoffs."""
import math
import FreeCAD as App
import Part
from .flex_geometry import union,box,round_window

def outer_face(shape):
 cap=max((f for f in shape.Faces if f.BoundBox.ZLength<1e-6),key=lambda f:f.Area)
 face=Part.Face(cap.OuterWire);face.translate(App.Vector(0,0,-cap.BoundBox.ZMin));return face

def offset_face(face,distance):
 result=face.makeOffset2D(distance,join=0)
 if not result.isValid() or not result.Faces:raise ValueError('Protector offset cannot follow this pad at the selected wall/fit size; reduce the offset.')
 return result

def _tapered_sleeve_clip(p, arm, bottom_z, top_z):
 """Angle the upper sleeve's two rear-facing termination edges as well."""
 from .landing_foot import inclined_rear_clip
 # The slider is *only* for the landing-foot centreline face.
 # Keep the existing upper sleeve unchanged when adjusting the foot.
 angle = math.radians(45.0)
 bottom_station = -.24
 top_station = bottom_station + math.tan(angle) * (top_z - bottom_z)
 return inclined_rear_clip(p, arm, bottom_z, top_z, bottom_station, top_station)


def motor_protectors(p,carbon=None,roles=None):
 if not p.FlexMotorProtectors:return {}
 from .parameters import arm_layouts,plate_levels
 from .geometry import motor_pad,arm_stem,capsule
 from .motor_pads import motor_pad_start,motor_pad_unit
 result={};z=plate_levels(p)['arm_z'];floor=p.FlexProtectorFloor;foot=p.FlexProtectorLanding
 for arm in arm_layouts(p):
  if roles is not None and 'MotorProtector'+arm['name'] not in roles:continue
  from dataclasses import replace
  # The carbon arm-tip outline is ALWAYS protected by the TPU side shell.
  # FlexProtectorBumperSleeve controls only the optional material ABOVE the
  # carbon tip; it must never replace the pad/tip footprint with a plain pad.
  pad_shape=motor_pad(p,arm,0);pad=outer_face(pad_shape);outer=offset_face(pad,p.FlexProtectorFit+p.FlexProtectorWall)
  sleeve=p.FlexProtectorBumperSleeve and p.ArmTipBumperStyle!='Disabled'
  shell_height=floor+p.ArmThickness+(p.FlexProtectorFit+.8 if sleeve else -.2)
  base=outer.extrude(App.Vector(0,0,shell_height));base.translate(App.Vector(0,0,z-floor))
  source=carbon.get('Arm'+arm['name']) if carbon else union([motor_pad(p,arm,z),arm_stem(p,arm,z,p.ArmThickness)])
  cavity=offset_face(outer_face(source),p.FlexProtectorFit).extrude(App.Vector(0,0,p.ArmThickness+(p.FlexProtectorFit if sleeve else 1)));cavity.translate(App.Vector(0,0,z))
  base=base.cut(cavity)
  if sleeve:
   # Keep the complete protector envelope, including the pad-to-tip fairing.
   # A mask from the first bumper polygon truncates the sleeve to the cap
   # width and drops the blended shoulders. Motor clearance below and the
   # outward-only limit later define where the upper sleeve is permitted.
   original=outer_face(motor_pad(replace(p,ArmTipBumperStyle='Disabled'),arm,0))
   clearance=offset_face(original,p.FlexProtectorFit).extrude(App.Vector(0,0,3))
   clearance.translate(App.Vector(0,0,z+p.ArmThickness-.2));base=base.cut(clearance)
   motor_clearance=Part.makeCylinder(p.MotorReferenceDiameter/2+p.FlexProtectorFit, shell_height+2, App.Vector(*arm['motor'],z+p.ArmThickness-.2))
   base=base.cut(motor_clearance)
  if foot:
   if p.FlexProtectorLandingStyle=='Tip-only inward taper':
    from .landing_foot import tip_tapered_foot
    # The main protector floor already occupies z-floor and everything above.
    # Form the *filled* front landing extension from its underside rather
    # than cutting a vertical front block and re-fusing another one.  The
    # motor-centreline termination is a sloped rear ramp on this sole.
    # Overlap 0.08 mm upward into the existing floor for a robust fusion.
    ring=tip_tapered_foot(p,arm,outer,None,z-floor+.08,z-floor-foot)
   else:
    # The original perimeter style still uses its independent inner offset.
    inner=offset_face(pad,p.FlexProtectorFit+.4)
    ring=outer.cut(inner).extrude(App.Vector(0,0,foot+.05));ring.translate(App.Vector(0,0,z-floor-foot))
   if not ring.isNull():base=base.fuse(ring)
  if sleeve:
   # Keep the normal protector at the rear; restrict only the upper lip.
   # Cutting the complete shell with a centre-plane tears through the
   # offset side wall on rotated pads. The lower wall and sole stay whole.
   lower_top = z + p.ArmThickness - .2
   # Taper BOTH formerly vertical faces at the termination of the upper
   # sleeve. The lower landing sole already has its own independent loft.
   if foot and p.FlexProtectorLandingStyle == 'Tip-only inward taper':
    outward = _tapered_sleeve_clip(p, arm, lower_top, z-floor+shell_height)
   else:
    mx,my=arm['motor'];ux,uy=motor_pad_unit(p,arm);vx,vy=-uy,ux
    pts=[App.Vector(mx+ux*a+vx*b,my+uy*a+vy*b,lower_top) for a,b in ((0,-500),(500,-500),(500,500),(0,500))]
    outward=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(0,0,shell_height+3))
   lower=Part.makeBox(2000,2000,floor+foot+p.ArmThickness-.2,App.Vector(-1000,-1000,z-floor-foot))
   base=base.common(lower).fuse(base.common(outward))
  low=z-floor-foot-1;height=p.ArmThickness+floor+foot+2
  # Motor screws and Linked screw access are independent of landing-foot
  # style: the filled tapered sole must retain the chosen retention pattern.
  # Carbon arm-tip decorative cutouts are still never transferred into TPU.
  radius=(p.MotorHoleDiameter/2+.15 if p.FlexProtectorRetention=='Motor screws'
          else max(3.,p.MotorHoleDiameter/2+.2))
  tools=[Part.makeCylinder(radius,height,App.Vector(x,y,low)) for x,y in arm['motor_holes']]
  tools.append(Part.makeCylinder(p.MotorCenterDiameter/2+.4,height,App.Vector(*arm['motor'],low)))
  from .protection_layout import motor_service_slots
  # Linked screw access cuts the protector floor/landing foot for either
  # landing style. Only the optional upper sleeve is excluded below.
  slots=[capsule(a,b,r,low,height) for a,b,r in motor_service_slots(p,arm)]
  if sleeve:
   slot_floor=Part.makeBox(2000,2000,floor+foot+1,App.Vector(-1000,-1000,low))
   slots=[tool.common(slot_floor) for tool in slots]
  tools.extend(slots)
  base=base.cut(Part.makeCompound(tools))
  base=base.removeSplitter()
  if not base.isValid() or len(base.Solids)!=1:raise ValueError('Motor protector '+arm['name']+' is disconnected; enlarge the pad or reduce the floor openings.')
  result['MotorProtector'+arm['name']]=base
 return result



from .shape_cleanup import guard_refine

def guard_union(items):
 items=[shape for shape in items if not shape.isNull()]
 if not items:return Part.Shape()
 return guard_refine(items[0].multiFuse(items[1:])) if len(items)>1 else items[0]


def cut_guard_openings(body,tools):
 """Keep exact overlapping-cutter fusion; compound only separated groups."""
 from .geometry_bounds import separated_box_groups
 if not tools:return body
 groups=separated_box_groups([tool.BoundBox for tool in tools])
 if len(groups)<=1:return body.cut(guard_union(tools))
 try:
  merged=[guard_union([tools[i] for i in group]) for group in groups]
  if not all(not s.isNull() and s.isValid() for s in merged):raise ValueError('invalid opening tool')
  result=body.cut(Part.makeCompound(merged))
  if result.isNull() or not result.isValid():raise ValueError('invalid opening cut')
  return result
 except Exception:
  return body.cut(guard_union(tools))


def guard_top_strap_tools(p,collars,body):
 """Open the floor beneath top straps when a wall sits inside the outline."""
 from .protection_layout import guard_between_plates
 if not (guard_between_plates(p) and p.StrapSlotsEnabled):return []
 from .parameters import strap_slots,plate_levels
 from .strap_openings import notch_polygons
 from .geometry import capsule
 depth=2.;z=plate_levels(p)['top_z']-depth;height=p.TopThickness+depth+1
 footprints=[(capsule(a,b,r,z,height),min(a[1],b[1])-r,max(a[1],b[1])+r) for a,b,r in strap_slots(p)]
 for polygon in notch_polygons(p):
  points=[App.Vector(x,y,z) for x,y in polygon]
  footprints.append((Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,height)),min(y for x,y in polygon),max(y for x,y in polygon)))
 # Keep a straight, open ledge under each intersecting passage. Extending
 # through the wall avoids fragile strips at a notch's rounded inner corner.
 from .geometry_bounds import box_distance
 bounds=body.BoundBox
 spans={(lo,hi) for tool,lo,hi in footprints if box_distance(bounds,tool.BoundBox)<=1e-6 and body.common(tool).Volume>1e-7}
 strap_tools=[box(-500,lo,z,1000,hi-lo,height) for lo,hi in sorted(spans)]
 if any(tool.common(collar).Volume>1e-6 for tool in strap_tools for collar in collars):
  raise ValueError('Top-plate strap passage intersects a side-guard bearing sleeve; move the strap or post.')
 return strap_tools


class GuardBuildWork:
 # Scoped to one frame generation. Only exact, read-only native geometry is
 # shared; independent left/right lofts, openings and checks are unchanged.
 def __init__(self):
  from .dependency_cache import NativeStageCache
  self.auxiliary=NativeStageCache(max_entries=2)
  self.outlines={};self.sections={};self.reliefs={}

 def unnotched_top(self,p):
  from .geometry import _component_carbon
  return self.auxiliary.get('unnotched_top',p,lambda t:_component_carbon(t,'TopPlate',{},include_strap_notches=False))

 def outline(self,shape):
  from .dependency_cache import shape_token
  key=shape_token(shape)
  if key not in self.outlines:
   cap=max((f for f in shape.Faces if f.BoundBox.ZLength<1e-5),key=lambda f:f.Area)
   face=Part.Face(cap.OuterWire)
   wire=face.OuterWire
   self.outlines[key]=(wire,face.BoundBox.ZMin,[(v.x,v.y) for v in wire.discretize(Deflection=.06)])
  return key,self.outlines[key][2]

 def edge(self,key,y,sign):
  station=(key,y)
  if station not in self.sections:
   wire,z,_=self.outlines[key]
   section=wire.section(Part.makeLine(App.Vector(-1000,y,z),App.Vector(1000,y,z)))
   self.sections[station]=tuple(v.Point.x for v in section.Vertexes)
  xs=[x for x in self.sections[station] if sign*x>=-1e-6]
  return (max(xs) if sign>0 else min(xs)) if xs else None

 def relief(self,stock,distance):
  from .dependency_cache import shape_token
  key=(shape_token(stock),distance)
  if key not in self.reliefs:
   profile=outer_face(stock)
   if distance>0:profile=offset_face(profile,distance)
   bounds=stock.BoundBox
   tool=profile.extrude(App.Vector(0,0,bounds.ZLength+2*distance))
   tool.translate(App.Vector(0,0,bounds.ZMin-distance));self.reliefs[key]=tool
  return self.reliefs[key]


def side_guards(p,carbon=None,roles=None,include_strap_passages=True,work=None):
 if not p.FlexSideGuards:return {}
 from .protection_layout import guard_layout,guard_vents,usb_window,vent_polygon,grip_bridge,guard_wire_openings,guard_strap_windows,guard_plate_gap,guard_between_plates,guard_vtx_window,guard_wall_inner_x,closure_profile,guard_main_wall_x,guard_closure_wall_bounds,guard_station_at,closure_stations
 if carbon is None:raise ValueError('Side guards require finished carbon plate outlines.')
 # The guard bridges the top plate's strap recesses along its unnotched
 # perimeter. Use this envelope for both the wall and its plate clearance;
 # the actual carbon part keeps its strap openings and other finishing cuts.
 import time
 from .geometry_bounds import box_distance
 work=GuardBuildWork() if work is None else work
 started=time.perf_counter()
 upper_stock=carbon['TopPlate']
 if p.StrapSlotsEnabled and p.StrapOpeningStyle=='Outline cutouts':
  upper_stock=work.unnotched_top(p)
 outline,edge=work.outline,work.edge
 auxiliary_time=time.perf_counter()-started
 result={};w=p.FlexGuardWall;r=(p.StandoffDiameter+p.FlexGuardFit)/2+w
 for g in guard_layout(p):
  if roles is not None and g['role'] not in roles:continue
  tick=time.perf_counter();stages=[('auxiliary carrier',auxiliary_time)]
  def mark(label):
   nonlocal tick
   now=time.perf_counter();stages.append((label,now-tick));tick=now
  upper_face,upper=outline(upper_stock);lower_face,lower=outline(carbon[g['lower_role']]);lo=g['rear']+p.FlexGuardRearInset;hi=g['front']-p.FlexGuardFrontInset;sign=g['sign'];z0=carbon[g['lower_role']].BoundBox.ZMin;z1=g['top']
  if guard_between_plates(p):z0=g['z']
  ys={lo,hi};ys.update(lo+(hi-lo)*i/max(1,int((hi-lo)/3)+1) for i in range(1,max(1,int((hi-lo)/3)+1)))
  closure=closure_profile(p,g)
  if closure:ys.update((closure['start'],closure['join']))
  ys.update(y for x,y in upper+lower if lo<y<hi);ys=sorted({round(y,4) for y in ys});wires=[];stations=[]
  for y in ys:
   xt=edge(upper_face,y,sign);xb=edge(lower_face,y,sign)
   if xt is None:raise ValueError('Top plate must reach both side-guard attachment rows.')
   low=z0
   missing_lower=xb is None
   if missing_lower:xb=xt;low=g['inner_top']-10
   xb=guard_wall_inner_x(p,xb,sign);xt=guard_wall_inner_x(p,xt,sign)
   # Vertical lips follow each plate through its full thickness. The
   # sloping electronics wall connects their inner faces, so a narrower
   # top or lower plate cannot pull the lip diagonally through carbon.
   lower_shoulder=low+.01 if missing_lower else g['inner_bottom']
   upper_shoulder=g['inner_top']
   points=[App.Vector(xb,y,low),App.Vector(xb+sign*w,y,low),
           App.Vector(xb+sign*w,y,lower_shoulder),App.Vector(xt+sign*w,y,upper_shoulder),
           App.Vector(xt+sign*w,y,z1),App.Vector(xt,y,z1),
           App.Vector(xt,y,upper_shoulder),App.Vector(xb,y,lower_shoulder)]
   if guard_between_plates(p):
    points=[App.Vector(xb,y,low),App.Vector(xb+sign*w,y,low),
            App.Vector(xt+sign*w,y,z1),App.Vector(xt,y,z1)]
   wires.append(Part.makePolygon(points+[points[0]]));stations.append((y,xb,xt,low))
  mark("exact plate sections")
  body=Part.makeLoft(wires,True,True);pads=[];collars=[]
  for stand,band in zip(g['stands'],g['bands']):
   sx,sy=stand['point'];low,high=band
   collars.append(Part.makeCylinder(r,high-low,App.Vector(sx,sy,low)))
   station=min(stations,key=lambda v:abs(v[0]-sy))
   from .geometry import capsule
   a,b,rad=grip_bridge(p,g,stand,station)
   bridge=capsule(a,b,rad,low,high-low)
   half=box(sx if sign>0 else sx-1000,-500,low-1,1000,1000,high-low+2)
   pads.append(bridge.common(half))
  if closure:
   bottom_face,bottom_outline=outline(carbon['BottomPlate']);layers=[]
   if min(end for z,end in closure['sections'])<=closure['start']+p.FlexGuardWall:
    raise ValueError('Camera side plates need at least 2 mm forward of the foremost standoffs for a full side closure.')
   sample_ys=closure_stations(closure,(station[0] for station in stations),(bottom_outline,upper))
   count=len(sample_ys)
   for start,(z,end) in zip(closure['starts'],closure['sections']):
    inside=[];outside=[]
    landing_x=closure['x']
    if closure['mode']!='Plate outlines only' and p.CameraCageStyle=='TPU cage':
     from .camera_cages import joined_cage
     stock=carbon.get('CameraMountLeft' if joined_cage(p) or sign<0 else 'CameraMountRight')
     if stock is not None and not stock.isNull():
      probe_z=max(p.BottomThickness+.001,min(z,g['inner_top']-.001))
      section=stock.common(Part.makeLine(App.Vector(-500,end,probe_z),App.Vector(500,end,probe_z)))
      xs=[v.Point.x for v in section.Vertexes if sign*v.Point.x>0]
      if xs:landing_x=max(xs) if sign>0 else min(xs)
    for y in sample_ys:
     main=guard_station_at(stations,min(y,closure['join']))
     main_x=guard_main_wall_x(p,g,main,z)
     if y<=closure['join']:
      x,outer_x=main_x,main_x+sign*w
     else:
      xb=edge(bottom_face,y,sign);xt=edge(upper_face,y,sign)
      # If the new rearward overlap precedes the bottom plate, transition
      # from the actual lower carrier rather than requiring an absent face.
      if xb is None and y<hi:xb=edge(lower_face,y,sign)
      if xb is None and y<hi:xb=xt
      if xb is None or xt is None:raise ValueError('Full side closure needs bottom and top plate support up to the camera side plates.')
      x,outer_x=guard_closure_wall_bounds(p,g,closure,y,z,xb,xt,landing_x,main_x)
     inside.append(App.Vector(x,y,z));outside.append(App.Vector(outer_x,y,z))
    layers.append((inside,outside))
   # Explicit planar faces avoid coincident ruled-loft surface failures at
   # the existing wall. The broad ribbon has no internal partition faces.
   faces=[]
   def quad(a,b,c,d,reverse=False):
    if reverse != (sign<0):a,b,c,d=d,c,b,a
    # Keep genuinely planar patches as quads. Only nonplanar patches need
    # a diagonal, so the finished TPU surface has fewer artificial seams.
    normal=(b-a).cross(c-a)
    if normal.Length>1e-10 and abs(normal.dot(d-a))/normal.Length<=1e-8:
     faces.append(Part.Face(Part.makePolygon([a,b,c,d,a])))
    else:
     for triangle in ((a,b,c),(a,c,d)):
      faces.append(Part.Face(Part.makePolygon(list(triangle)+[triangle[0]])))
   for k,(inside,outside) in enumerate(layers):
    if k in (0,len(layers)-1):
     for i in range(count-1):quad(inside[i],inside[i+1],outside[i+1],outside[i],k>0)
    if k==0:continue
    prev_in,prev_out=layers[k-1]
    for i in range(count-1):
     quad(prev_in[i],prev_in[i+1],inside[i+1],inside[i],True)
     quad(prev_out[i],prev_out[i+1],outside[i+1],outside[i])
    for i in (0,count-1):quad(prev_in[i],prev_out[i],outside[i],inside[i],i>0)
   extra=Part.makeSolid(Part.makeShell(faces));extra=guard_refine(extra)
   if not extra.isValid() or len(extra.Solids)!=1 or extra.Volume<=0:raise ValueError('Camera-side closure could not form a continuous panel; review plate and camera positions.')
   # Replace the forward wall rather than fusing two long coincident skins.
   # The cut is inside the extra panel's short rear overlap; post supports stay.
   body=body.cut(box(-500,closure['join'],-500,1000,1000,1000))
   body=body.fuse(extra)
  body=guard_union([body]+pads);mark("wall loft and supports");tools=[];hardware=[];bearing_hardware=[]
  from .antenna_geometry import antenna_guard_clearance
  tools.extend(antenna_guard_clearance(p))
  from .elrs_geometry import elrs_guard_clearance
  tools.extend(elrs_guard_clearance(p))
  # Integrated mode now sculpts the full one-piece rear housing first and
  # subtracts these finished side guards from the housing itself.  Unlike the
  # older two-band strategy, do not carve any additional material from the
  # side guards here: their original collar and wall geometry is preserved.
  if include_strap_passages:tools.extend(guard_top_strap_tools(p,collars,body))
  for vent in guard_vents(p,g):
   y,z,width,height=vent['y'],vent['z'],vent['width'],vent['height'];poly=vent_polygon(vent)
   if poly:
    points=[App.Vector(-500,y+dy,z+dz) for dy,dz in poly];tools.append(Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(1000,0,0)))
   elif vent['shape']=='Ellipses':
    points=[App.Vector(-500,y+width/2*math.cos(i*math.pi/32),z+height/2*math.sin(i*math.pi/32)) for i in range(64)]
    tools.append(Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(1000,0,0)))
   elif vent['shape']=='Rounded slots':tools.append(round_window(-500,1000,y,z,width,height,min(width,height)/2-.01))
   else:tools.append(box(-500,y-width/2,z-height/2,1000,width,height))
  if closure:
   from .fpv import camera_mounts
   from .geometry import arc_slot
   mount=next(m for m in camera_mounts(p) if m['role'].endswith('Left' if sign<0 else 'Right'))
   tools.extend(Part.makeCylinder(p.CameraSideHoleDiameter/2+.2,1000,App.Vector(-500,y,z),App.Vector(1,0,0)) for y,z in mount['side_holes'])
   tools.extend(arc_slot(dict(arc,width=arc['width']+.4),-500,1000) for arc in mount['side_arcs'])
  for opening in guard_wire_openings(p,g):
   y,opening_width,h,bottom=opening['y'],opening['width'],opening['height'],opening['bottom']
   # Start below the edge: the result is an open notch with rounded shoulders.
   tool=round_window(-500,1000,y,bottom+(h-2)/2,opening_width,h+2,min(1.,opening_width/4,h/4))
   tool=protected_front_wire_tool(p,g,opening,tool,body)
   if opening['name']!='Front' and any(tool.common(collar).Volume>1e-6 for collar in collars):raise ValueError('Motor-wire opening intersects a side-guard bearing sleeve; move or resize it.')
   tools.append(tool)
  for opening in guard_strap_windows(p,g):
   y,z,width,height=opening['y'],opening['z'],opening['width'],opening['height']
   tool=round_window(-500,1000,y,z,width,height,min(1.,width/4,p.FlexGuardStrapDepth/4))
   if any(tool.common(collar).Volume>1e-6 for collar in collars):raise ValueError('Battery strap opening intersects a standoff grip; move it or reduce its width/depth.')
   tools.append(tool)
  for window,label in ((usb_window(p,g),'USB'),(guard_vtx_window(p,g),'VTX')):
   if not window:continue
   y,z,width,height=window;tool=round_window(-500,1000,y,z,width,height,min(1.,width/4,height/4))
   if any(tool.common(collar).Volume>1e-6 for collar in collars):raise ValueError(label+' opening intersects a side-guard bearing sleeve; move or resize it.')
   tools.append(tool)
  # Arms above the bottom plate and clamp stock need local service reliefs.
  # Keep the full post sleeves intact; their final clash check remains strict.
  for role,stock in carbon.items():
   if role in ('ArmFrontRight','ArmFrontLeft','ArmRearLeft','ArmRearRight','ArmClampPlate','ArmLowerClampPlate','BottomPlate','MidPlate','TopPlate') and not stock.isNull():
    if role=='TopPlate':stock=upper_stock
    relief=guard_plate_gap(p) if role in ('BottomPlate','MidPlate','TopPlate') else .15
    tool=work.relief(stock,relief);hardware.append(tool);bearing_hardware.append(stock if role in ('BottomPlate','MidPlate','TopPlate') else tool)
  if closure:
   hardware.extend(stock for role,stock in carbon.items() if role.startswith('CameraMount') and not stock.isNull())
  from .parameters import motor_centres,plate_levels
  prop_z=plate_levels(p)['arm_z']+p.ArmThickness+p.PropReferenceHeight
  tools.extend(Part.makeCylinder(p.PropDiameter/2+1,4.25,App.Vector(mx,my,prop_z-2)) for mx,my in motor_centres(p))
  mark("relief and opening tools")
  # Carbon tools overlap at arm/plate interfaces. Subtract separately before
  # the vent union so coincident cutters cannot leave residual islands.
  for tool in hardware:
   if body.BoundBox.intersect(tool.BoundBox):
    body=body.cut(tool)
  # Do not fuse cutters separated from the remaining wall. Their difference
  # is empty; retain touching/nearby cutters and exact native operations.
  wall_bounds=body.BoundBox
  tools=[tool for tool in tools if not tool.isNull() and box_distance(wall_bounds,tool.BoundBox)<=1e-6]
  if tools:body=cut_guard_openings(body,tools)
  mark("wall relief booleans")
  if hardware:
   # The full front sleeve can approach the arm beneath it. Relieve only its
   # outer wall locally, retaining a continuous minimum 0.8 mm circular shell.
   for index,(stand,band) in enumerate(zip(g['stands'],g['bands'])):
    sx,sy=stand['point'];low,high=band
    rear_flush=(p.FlexRearAntenna or p.FlexELRSEnabled) and abs(sy-g['rear'])<1e-6
    nearby=[tool for tool in (bearing_hardware if rear_flush else hardware) if collars[index].BoundBox.intersect(tool.BoundBox)]
    if not nearby:continue
    clearance=guard_union(nearby)
    if collars[index].common(clearance).Volume<1e-6:continue
    inner=(p.StandoffDiameter+p.FlexGuardFit)/2
    core=Part.makeCylinder(inner+.8,high-low,App.Vector(sx,sy,low)).cut(Part.makeCylinder(inner,high-low,App.Vector(sx,sy,low)))
    if core.common(clearance).Volume>1e-6:raise ValueError('A full-height guard grip needs more space around its standoff; move that post or adjust the adjacent carbon part.')
    collars[index]=collars[index].cut(clearance)
  body=guard_union([body]+collars)
  bores=[Part.makeCylinder((p.StandoffDiameter+p.FlexGuardFit)/2,1000,App.Vector(*stand['point'],-500)) for stand in g['stands']]
  body=guard_refine(body.cut(Part.makeCompound(bores)))
  if not body.isValid() or len(body.Solids)!=1:raise ValueError(g['role']+' cannot connect its actual plate edges and full bearing bands; check plate reach, post positions and prop clearance.')
  if closure and body.BoundBox.YMax<max(y for z,y in closure['sections'])-1e-5:raise ValueError('Camera-side enclosure did not retain its full forward panel; review plate reach and camera landing.')
  mark('bearing sleeves and validation')
  App.Console.PrintMessage('RotorForge guard detail '+g['role']+': '+', '.join(f'{k}: {v:.3f}s' for k,v in stages)+'\n')
  result[g['role']]=body
 return result


def side_guard_openings(p,role,body):
 from .protection_layout import guard_layout,guard_vents,usb_window,vent_polygon,guard_wire_openings,guard_strap_windows,guard_vtx_window
 g=next(g for g in guard_layout(p) if g['role']==role)
 r=(p.StandoffDiameter+p.FlexGuardFit)/2+p.FlexGuardWall
 collars=[Part.makeCylinder(r,high-low,App.Vector(*stand['point'],low)) for stand,(low,high) in zip(g['stands'],g['bands'])]
 tools=guard_top_strap_tools(p,collars,body)
 for vent in guard_vents(p,g):
  y,z,width,height=vent['y'],vent['z'],vent['width'],vent['height'];poly=vent_polygon(vent)
  if poly:
   points=[App.Vector(-500,y+dy,z+dz) for dy,dz in poly];tools.append(Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(1000,0,0)))
  elif vent['shape']=='Ellipses':
   points=[App.Vector(-500,y+width/2*math.cos(i*math.pi/32),z+height/2*math.sin(i*math.pi/32)) for i in range(64)]
   tools.append(Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(1000,0,0)))
  elif vent['shape']=='Rounded slots':tools.append(round_window(-500,1000,y,z,width,height,min(width,height)/2-.01))
  else:tools.append(box(-500,y-width/2,z-height/2,1000,width,height))
 for opening in guard_wire_openings(p,g):
  y,opening_width,h,bottom=opening['y'],opening['width'],opening['height'],opening['bottom']
  # Start below the edge: the result is an open notch with rounded shoulders.
  tool=round_window(-500,1000,y,bottom+(h-2)/2,opening_width,h+2,min(1.,opening_width/4,h/4))
  tool=protected_front_wire_tool(p,g,opening,tool,body)
  if opening['name']!='Front' and any(tool.common(collar).Volume>1e-6 for collar in collars):raise ValueError('Motor-wire opening intersects a side-guard bearing sleeve; move or resize it.')
  tools.append(tool)
 for opening in guard_strap_windows(p,g):
  y,z,width,height=opening['y'],opening['z'],opening['width'],opening['height']
  tool=round_window(-500,1000,y,z,width,height,min(1.,width/4,p.FlexGuardStrapDepth/4))
  if any(tool.common(collar).Volume>1e-6 for collar in collars):raise ValueError('Battery strap opening intersects a standoff grip; move it or reduce its width/depth.')
  tools.append(tool)
 for window,label in ((usb_window(p,g),'USB'),(guard_vtx_window(p,g),'VTX')):
  if not window:continue
  y,z,width,height=window;tool=round_window(-500,1000,y,z,width,height,min(1.,width/4,height/4))
  if any(tool.common(collar).Volume>1e-6 for collar in collars):raise ValueError(label+' opening intersects a side-guard bearing sleeve; move or resize it.')
  tools.append(tool)
 if tools:body=guard_refine(body.cut(guard_union(tools)))
 if not body.isValid() or len(body.Solids)!=1:raise ValueError(role+' openings disconnect the protective panel; reduce their size or move them.')
 return body


def protected_front_wire_tool(p,g,opening,tool,body):
 """Keep full bearing bands and a local 0.8 mm web beside a front exit."""
 if opening['name']!='Front':return tool
 # Localise the cutter to this wall before the sleeve subtraction. This
 # avoids carrying a full-frame-width cutter through each rounded grip.
 b=body.BoundBox;t=tool.BoundBox
 tool=tool.common(box(b.XMin-1,t.YMin-1,t.ZMin-1,b.XLength+2,t.YLength+2,t.ZLength+2))
 radius=(p.StandoffDiameter+p.FlexGuardFit)/2+p.FlexGuardWall+.8
 protected=[Part.makeCylinder(radius,high-low+1.6,App.Vector(*stand['point'],low-.8)) for stand,(low,high) in zip(g['stands'],g['bands']) if stand['point'][1]+radius>=t.YMin and stand['point'][1]-radius<=t.YMax and high+.8>=t.ZMin and low-.8<=t.ZMax]
 return tool.cut(Part.makeCompound(protected)) if protected else tool
