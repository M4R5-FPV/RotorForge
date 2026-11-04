"""Separate printable lower rear T-antenna mount and guard relief."""
import FreeCAD as App
import Part
from .elrs_layout import elrs_layout,elrs_seat,elrs_bore

def elrs_guard_clearance(p):
 if not p.FlexELRSEnabled:return []
 a=elrs_seat(p);z=a['z0'];h=a['height']+p.FlexELRSGuardGap;rear=a['pair'][0]['point'][1]
 rad=elrs_bore(p)/2+p.FlexELRSGripWall+.2
 tools=[Part.makeCylinder(rad,h,App.Vector(*s['point'],z)) for s in a['pair']]
 tools.append(Part.makeBox(2000,300+p.FlexELRSBarWidth/2+.2,h,App.Vector(-1000,rear-300,z)))
 return tools

def elrs_mount(p,inputs):
 if not p.FlexELRSEnabled:return Part.Shape()
 from .geometry import overlap_volume
 from .antenna_solids import stroke_solid,capsule
 from .protection_geometry import outer_face
 from .snap_channels import entry_tool
 a=elrs_layout(p);z0=a['z0'];h=a['height'];points=a['points'];w=p.FlexELRSBarWidth;limits=[]
 for role in ('BottomPlate','MidPlate','TopPlate'):
  shape=inputs.get(role,Part.Shape())
  if shape.isNull():continue
  xs=[v.Point.x for v in outer_face(shape).common(Part.makeLine(App.Vector(-1000,a['rear'],0),App.Vector(1000,a['rear'],0))).Vertexes]
  if xs:limits.append((min(xs),max(xs)))
 if not limits:raise ValueError('Cannot find ELRS carrier width at rear standoffs.')
 left=min(v[0] for v in limits);right=max(v[1] for v in limits)
 if p.FlexSideGuards:
  from .protection_layout import guard_wall_inner_x
  left=guard_wall_inner_x(p,left,-1)-p.FlexGuardWall;right=guard_wall_inner_x(p,right,1)+p.FlexGuardWall
 if p.FlexELRSHookSpacing/2+p.FlexELRSHookWidth/2>min(-left,right):raise ValueError('ELRS hooks exceed the rear plate/guard width; reduce hook spacing or width.')
 clip=Part.makeBox(right-left,500,h,App.Vector(left,a['rear']-250,z0))
 if p.FlexELRSBarShape=='Rectangle':bar=Part.makeBox(points[2][0]-points[0][0],a['rear']-a['bar_y']+w,h,App.Vector(points[0][0],a['bar_y']-w/2,z0))
 elif p.FlexELRSBarShape=='Curved':bar=stroke_solid(points,w/2,z0,h)
 else:
  ribs=[capsule(u,v,w/2,z0,h) for u,v in zip(points,points[1:])];bar=ribs[0].multiFuse(ribs[1:])
 parts=[bar.common(clip),capsule((-p.FlexELRSHookSpacing/2,a['bar_y']),(p.FlexELRSHookSpacing/2,a['bar_y']),w/2,z0,h).common(clip)];cuts=[]
 for s in a['pair']:
  rad=elrs_bore(p)/2;pos=App.Vector(*s['point'],z0)
  parts.append(Part.makeCylinder(rad+p.FlexELRSGripWall,h,pos));cuts.append(Part.makeCylinder(rad,h+2,pos-App.Vector(0,0,1)))
 axis=App.Vector(1,0,0)
 for x,y,z in a['hooks']:
  start=App.Vector(x-p.FlexELRSHookWidth/2,y,z);length=p.FlexELRSHookWidth
  if p.FlexELRSHookReach>0:
   size=a['support_size'];bottom=z0+(h-size)/2
   # Bury the end inside the hook; the full-width shank reaches its outer wall.
   # Bore and entry cuts are applied after fusion to keep the antenna path clear.
   support=Part.makeBox(size,a['bar_y']-y+size/2,size,App.Vector(x-size/2,y,bottom))
   support=support.makeFillet(min(.6,size*.15),support.Edges)
   parts.append(support.common(clip))
  parts.append(Part.makeCylinder(a['radius'],length,start,axis))
  cuts.append(Part.makeCylinder(p.FlexELRSAntennaDiameter/2,length+.04,start-axis*.02,axis))
  cuts.append(entry_tool(start,axis,App.Vector(0,0,1),length,p.FlexELRSAntennaDiameter,a['radius'],p.FlexELRSRetainingLip))
 solid=parts[0].multiFuse(parts[1:])
 if p.FlexELRSPassThroughDiameter:
  bounds=solid.BoundBox
  cuts.append(Part.makeCylinder(p.FlexELRSPassThroughDiameter/2,bounds.YLength+2,App.Vector(0,bounds.YMin-1,a['z']),App.Vector(0,1,0)))
 solid=solid.cut(Part.makeCompound(cuts)).removeSplitter()
 if not solid.isValid() or len(solid.Solids)!=1:raise ValueError('ELRS mount must be one connected solid; adjust bar and hook dimensions.')
 for role in ('BottomPlate','MidPlate','TopPlate','ElectronicsGuardLeft','ElectronicsGuardRight','RearAntennaMount'):
  obstacle=inputs.get(role,Part.Shape())
  if overlap_volume(solid,obstacle)>1e-6:raise ValueError('ELRS mount intersects '+role+'; adjust reach, height or hook size.')
 return solid
