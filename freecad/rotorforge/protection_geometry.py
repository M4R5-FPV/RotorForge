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

def motor_protectors(p,carbon=None,roles=None):
 if not p.FlexMotorProtectors:return {}
 from .parameters import arm_layouts,plate_levels
 from .geometry import motor_pad,arm_stem,capsule
 from .motor_pads import motor_pad_start,motor_pad_unit
 result={};z=plate_levels(p)['arm_z'];floor=p.FlexProtectorFloor;foot=p.FlexProtectorLanding
 for arm in arm_layouts(p):
  if roles is not None and 'MotorProtector'+arm['name'] not in roles:continue
  pad=outer_face(motor_pad(p,arm,0));outer=offset_face(pad,p.FlexProtectorFit+p.FlexProtectorWall)
  base=outer.extrude(App.Vector(0,0,floor+p.ArmThickness-.2));base.translate(App.Vector(0,0,z-floor))
  source=carbon.get('Arm'+arm['name']) if carbon else union([motor_pad(p,arm,z),arm_stem(p,arm,z,p.ArmThickness)])
  cavity=offset_face(outer_face(source),p.FlexProtectorFit).extrude(App.Vector(0,0,p.ArmThickness+1));cavity.translate(App.Vector(0,0,z))
  base=base.cut(cavity)
  if foot:
   inner=offset_face(pad,p.FlexProtectorFit+.4)
   ring=outer.cut(inner).extrude(App.Vector(0,0,foot+.05));ring.translate(App.Vector(0,0,z-floor-foot));base=base.fuse(ring)
  low=z-floor-foot-1;height=p.ArmThickness+floor+foot+2
  radius=p.MotorHoleDiameter/2+.15 if p.FlexProtectorRetention=='Motor screws' else max(3.,p.MotorHoleDiameter/2+.2)
  tools=[Part.makeCylinder(radius,height,App.Vector(x,y,low)) for x,y in arm['motor_holes']]
  tools.append(Part.makeCylinder(p.MotorCenterDiameter/2+.4,height,App.Vector(*arm['motor'],low)))
  from .protection_layout import motor_service_slots
  tools.extend(capsule(a,b,r,low,height) for a,b,r in motor_service_slots(p,arm))
  base=base.cut(Part.makeCompound(tools)).removeSplitter()
  if not base.isValid() or len(base.Solids)!=1:raise ValueError('Motor protector '+arm['name']+' is disconnected; enlarge the pad or reduce the floor openings.')
  result['MotorProtector'+arm['name']]=base
 return result



from .shape_cleanup import guard_refine

def guard_union(items):
 items=[shape for shape in items if not shape.isNull()]
 if not items:return Part.Shape()
 return guard_refine(items[0].multiFuse(items[1:])) if len(items)>1 else items[0]


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
 spans={(lo,hi) for tool,lo,hi in footprints if body.common(tool).Volume>1e-7}
 strap_tools=[box(-500,lo,z,1000,hi-lo,height) for lo,hi in sorted(spans)]
 if any(tool.common(collar).Volume>1e-6 for tool in strap_tools for collar in collars):
  raise ValueError('Top-plate strap passage intersects a side-guard bearing sleeve; move the strap or post.')
 return strap_tools


def side_guards(p,carbon=None,roles=None,include_strap_passages=True):
 if not p.FlexSideGuards:return {}
 from .protection_layout import guard_layout,guard_vents,usb_window,vent_polygon,grip_bridge,guard_wire_openings,guard_strap_windows,guard_plate_gap,guard_between_plates,guard_vtx_window,guard_wall_inner_x
 if carbon is None:raise ValueError('Side guards require finished carbon plate outlines.')
 # The guard bridges the top plate's strap recesses along its unnotched
 # perimeter. Use this envelope for both the wall and its plate clearance;
 # the actual carbon part keeps its strap openings and other finishing cuts.
 upper_stock=carbon['TopPlate']
 if p.StrapSlotsEnabled and p.StrapOpeningStyle=='Outline cutouts':
  from .geometry import _component_carbon
  upper_stock=_component_carbon(p,'TopPlate',{},include_strap_notches=False)
 def outline(shape):
  cap=max((f for f in shape.Faces if f.BoundBox.ZLength<1e-5),key=lambda f:f.Area)
  face=Part.Face(cap.OuterWire)
  return face,[(v.x,v.y) for v in face.OuterWire.discretize(Deflection=.06)]
 edge_cache={}
 def edge(face,y,sign):
  key=(face.hashCode(),round(y,8),sign)
  if key in edge_cache:return edge_cache[key]
  # Intersect the actual curve; coarse whole-wire sampling can select the
  # opposite arm tab near a short tip and produce a cross-frame spike.
  z=face.BoundBox.ZMin
  section=face.common(Part.makeLine(App.Vector(-1000,y,z),App.Vector(1000,y,z)))
  xs=[v.Point.x for v in section.Vertexes if sign*v.Point.x>=-1e-6]
  result=(max(xs) if sign>0 else min(xs)) if xs else None
  edge_cache[key]=result
  return result
 result={};w=p.FlexGuardWall;r=(p.StandoffDiameter+p.FlexGuardFit)/2+w
 for g in guard_layout(p):
  if roles is not None and g['role'] not in roles:continue
  upper_face,upper=outline(upper_stock);lower_face,lower=outline(carbon[g['lower_role']]);lo=g['rear']+p.FlexGuardRearInset;hi=g['front']-p.FlexGuardFrontInset;sign=g['sign'];z0=carbon[g['lower_role']].BoundBox.ZMin;z1=g['top']
  if guard_between_plates(p):z0=g['z']
  ys={lo,hi};ys.update(lo+(hi-lo)*i/max(1,int((hi-lo)/3)+1) for i in range(1,max(1,int((hi-lo)/3)+1)))
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
  from .protection_layout import closure_profile
  closure=closure_profile(p,g)
  if closure:
   bottom_face,_=outline(carbon['BottomPlate']);layers=[]
   low=closure['sections'][0][0];high=closure['sections'][-1][0]
   if closure['sections'][0][1]<=closure['start']+2:
    raise ValueError('Camera side plates need at least 2 mm forward of the foremost standoffs for a full side closure.')
   for start,(z,end) in zip(closure['starts'],closure['sections']):
    t=(z-low)/(high-low);inside=[];outside=[]
    for i in range(13):
     s=i/12;y=start+(end-start)*s
     xb=edge(bottom_face,y,sign);xt=edge(upper_face,y,sign)
     if xb is None:xb=edge(bottom_face,min(y,closure['sections'][0][1]),sign)
     if xt is None:xt=edge(upper_face,min(y,closure['sections'][-1][1]),sign)
     if xb is None or xt is None:raise ValueError('Full side closure needs bottom and top plate support up to the camera side plates.')
     x=guard_wall_inner_x(p,xb*(1-t)+xt*t,sign)
     blend=max(0.,min(1.,(y-(end-14))/14));blend=blend*blend*(3-2*blend)
     x=x*(1-blend)+closure['x']*blend
     inside.append(App.Vector(x,y,z));outside.append(App.Vector(x+sign*w,y,z))
    layers.append((inside,outside))
   # Explicit planar faces avoid coincident ruled-loft surface failures at
   # the existing wall. The broad ribbon has no internal partition faces.
   faces=[]
   def quad(a,b,c,d,reverse=False):
    if reverse != (sign<0):a,b,c,d=d,c,b,a
    for triangle in ((a,b,c),(a,c,d)):
     faces.append(Part.Face(Part.makePolygon(list(triangle)+[triangle[0]])))
   for k,(inside,outside) in enumerate(layers):
    if k in (0,len(layers)-1):
     for i in range(12):quad(inside[i],inside[i+1],outside[i+1],outside[i],k>0)
    if k==0:continue
    prev_in,prev_out=layers[k-1]
    for i in range(12):
     quad(prev_in[i],prev_in[i+1],inside[i+1],inside[i],True)
     quad(prev_out[i],prev_out[i+1],outside[i+1],outside[i])
    for i in (0,12):quad(prev_in[i],prev_out[i],outside[i],inside[i],i>0)
   extra=Part.makeSolid(Part.makeShell(faces));extra=guard_refine(extra)
   if not extra.isValid() or len(extra.Solids)!=1 or extra.Volume<=0:raise ValueError('Camera-side closure could not form a continuous panel; review plate and camera positions.')
   # Replace the forward wall rather than fusing two long coincident skins.
   # The join stays at the forward posts; original post supports stay.
   body=body.cut(box(-500,closure['start']+4,-500,1000,1000,1000))
   body=body.fuse(extra)
  body=guard_union([body]+pads);tools=[];hardware=[]
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
    profile=outer_face(stock)
    if relief>0:profile=offset_face(profile,relief)
    tool=profile.extrude(App.Vector(0,0,stock.BoundBox.ZLength+2*relief));tool.translate(App.Vector(0,0,stock.BoundBox.ZMin-relief));hardware.append(tool)
  if closure:
   hardware.extend(stock for role,stock in carbon.items() if role.startswith('CameraMount') and not stock.isNull())
  from .parameters import motor_centres,plate_levels
  prop_z=plate_levels(p)['arm_z']+p.ArmThickness+p.PropReferenceHeight
  tools.extend(Part.makeCylinder(p.PropDiameter/2+1,4.25,App.Vector(mx,my,prop_z-2)) for mx,my in motor_centres(p))
  # Carbon tools overlap at arm/plate interfaces. Subtract separately before
  # the vent union so coincident cutters cannot leave residual islands.
  for tool in hardware:
   if body.BoundBox.intersect(tool.BoundBox):
    body=body.cut(tool)
  if tools:body=body.cut(guard_union(tools))
  if hardware:
   # The full front sleeve can approach the arm beneath it. Relieve only its
   # outer wall locally, retaining a continuous minimum 0.8 mm circular shell.
   for index,(stand,band) in enumerate(zip(g['stands'],g['bands'])):
    sx,sy=stand['point'];low,high=band
    nearby=[tool for tool in hardware if collars[index].BoundBox.intersect(tool.BoundBox)]
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
