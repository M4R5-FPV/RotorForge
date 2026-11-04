"""One printable mount bounded to the upper rear standoff space."""
import math
import FreeCAD as App
import Part
from .antenna_layout import antenna_layout,antenna_standoff_bore

def rear_antenna_mount(p,inputs):
 if not p.FlexRearAntenna:return Part.Shape()
 from .geometry import overlap_volume
 from .antenna_solids import stroke_solid as stroke, capsule, bulkhead_tab
 from .protection_geometry import outer_face
 a=antenna_layout(p);z0=a['z0'];h=a['height'];y=a['pair'][0]['point'][1];limits=[]
 for role in ('BottomPlate','MidPlate','TopPlate'):
  shape=inputs.get(role,Part.Shape())
  if shape.isNull():continue
  face=outer_face(shape);line=Part.makeLine(App.Vector(-1000,y,0),App.Vector(1000,y,0))
  xs=[v.Point.x for v in face.common(line).Vertexes]
  if xs:limits.append((min(xs),max(xs)))
 if not limits:raise ValueError('Cannot find plate width at rear standoffs.')
 left=min(x[0] for x in limits);right=max(x[1] for x in limits)
 if p.FlexSideGuards:
  from .protection_layout import guard_wall_inner_x
  left=guard_wall_inner_x(p,left,-1)-p.FlexGuardWall;right=guard_wall_inner_x(p,right,1)+p.FlexGuardWall
 clip=Part.makeBox(right-left,500,h,App.Vector(left,y-250,z0));points=a['points'];width=a['width']
 if p.FlexAntennaBarShape=='Rectangle':bar=Part.makeBox(points[2][0]-points[0][0],p.FlexAntennaReach+width,h,App.Vector(points[0][0],y-p.FlexAntennaReach-width/2,z0))
 else:
  if p.FlexAntennaBarShape=='Curved':bar=stroke(points,width/2,z0,h)
  else:
   ribs=[capsule(u,v,width/2,z0,h) for u,v in zip(points,points[1:])];bar=ribs[0].multiFuse(ribs[1:])
 parts=[bar.common(clip)];cuts=[];entries=[]
 for stand in a['pair']:
  x,y1=stand['point'];rad=antenna_standoff_bore(p)/2
  parts.append(Part.makeCylinder(rad+p.FlexAntennaGripWall,h,App.Vector(x,y1,z0)))
  cuts.append(Part.makeCylinder(rad,h+2,App.Vector(x,y1,z0-1)))
 for holder in a['holders']:
  c=App.Vector(*holder['centre']);axis=App.Vector(*holder['axis']);length=a['length'];start=App.Vector(*holder['start'])
  anchor=App.Vector(*holder['anchor'])
  if a['bulkhead']:
   parts.append(bulkhead_tab(a['radius']*2,length,start,axis))
   # Free both nut/washer faces from adjacent supports.
   clearance=max(a['bore']/2+.5,5.)
   cuts.extend([Part.makeCylinder(clearance,100,start-axis*100,axis),Part.makeCylinder(clearance,100,start+axis*length,axis)])
  else:parts.append(Part.makeCylinder(a['radius'],length,start,axis))
  apex=(0,y-p.FlexAntennaReach);target=(anchor.x,anchor.y)
  support_radius=max(width/2,a['radius']) if a['bulkhead'] else width/2
  parts.append(capsule(apex,target,support_radius,z0,h).common(clip) if math.dist(apex,target)>.001 else Part.makeCylinder(support_radius,h,App.Vector(*target,z0)))
  cuts.append(Part.makeCylinder(a['bore']/2,length+200,start-axis*100,axis))
  if not a['bulkhead'] and p.FlexAntennaHolderStyle=='Side-entry clip':entries.append((start,axis))
 solid=parts[0].multiFuse(parts[1:])
 # Tilted tube roots must not project below the carrier's flat seating plane.
 # Keep the full upper sleeve; SMA/RP-SMA pigtail tabs retain their geometry.
 if not a['bulkhead'] and solid.BoundBox.ZMin<z0-1e-7:
  b=solid.BoundBox
  solid=solid.common(Part.makeBox(b.XLength+2,b.YLength+2,b.ZMax-z0+1,App.Vector(b.XMin-1,b.YMin-1,z0)))
 from .snap_channels import full_entry_tool
 for start,axis in entries:cuts.append(full_entry_tool(solid,start,axis,a['bore'],a['radius'],p.FlexAntennaRetainingLip))
 solid=solid.cut(Part.makeCompound(cuts)).removeSplitter()
 if not solid.isValid() or len(solid.Solids)!=1:raise ValueError('Rear antenna mount is disconnected. Increase bar width or reduce holder spacing.')
 # Only actual intersections constrain sleeves behind the frame.
 for role in ('BottomPlate','MidPlate','TopPlate','ElectronicsGuardLeft','ElectronicsGuardRight'):
  obstacle=inputs.get(role,Part.Shape())
  if not obstacle.isNull() and overlap_volume(solid,obstacle)>1e-6:
   raise ValueError('Antenna holder intersects '+role+'; move Holder fore/aft offset rearward or adjust tilt/reach.')
 return solid


def antenna_guard_clearance(p):
 """Reserve the mount footprint above the shared seat, preserving bearing below."""
 if not p.FlexRearAntenna:return []
 from .antenna_layout import antenna_seat
 from .mount_bands import rear_pair
 pair=rear_pair(p);seat=antenna_seat(p)[0]-p.FlexAntennaGuardGap;rear=pair[0]['point'][1]
 radius=antenna_standoff_bore(p)/2+p.FlexAntennaGripWall+.2
 tools=[Part.makeCylinder(radius,100,App.Vector(*stand['point'],seat)) for stand in pair]
 tools.append(Part.makeBox(2000,300+p.FlexAntennaBarWidth/2+.2,100,App.Vector(-1000,rear-300,seat)))
 return tools
