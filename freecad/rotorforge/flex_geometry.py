"""Small exact solids for flexible parts; called only on Create/Update/export."""
import math
import FreeCAD as App
import Part
from .flex import soft_camera,insert_rect,camera_interface_polygon
from .flex_options import FLEX_ROLES

def box(x,y,z,w,d,h):return Part.makeBox(w,d,h,App.Vector(x,y,z))
def union(items):
 items=[s for s in items if not s.isNull()]
 return items[0].multiFuse(items[1:]).removeSplitter() if len(items)>1 else items[0] if items else Part.Shape()
def round_window(x,thickness,cy,cz,width,height,radius=2.):
 # Reuse the exact rounded XY primitive then map its axes to the camera YZ plane.
 from .geometry import rounded_plate
 s=rounded_plate(width,height,min(radius,width/4,height/4),0,thickness)
 s.rotate(App.Vector(),App.Vector(1,1,1),120)
 s.translate(App.Vector(x,cy,cz));return s

def interface_blank(p,x,thickness,width,height,offset=0.):
 from .camera_interface import profile_corners
 corners=profile_corners(p,width,height);edges=[]
 def point(v):return App.Vector(*v,0)
 for previous,corner in zip(corners[-1:]+corners[:-1],corners):
  if math.dist(previous['end'],corner['start'])>1e-8:edges.append(Part.makeLine(point(previous['end']),point(corner['start'])))
  if corner['radius']:edges.append(Part.Arc(point(corner['start']),point(corner['mid']),point(corner['end'])).toShape())
 face=Part.Face(Part.Wire(edges))
 if offset:face=face.makeOffset2D(offset,join=0)
 if not face.isValid():raise ValueError('Camera interface radius or fit does not form a valid outline; reduce the radius or clearance.')
 solid=face.extrude(App.Vector(0,0,thickness));solid.rotate(App.Vector(),App.Vector(1,1,1),120);solid.translate(App.Vector(x,0,0));return solid


def camera_window(p,x,thickness):
 cy,cz,w,h=insert_rect(p);return interface_blank(p,x,thickness,w,h)

def camera_pads(p,roles=None):
 if not soft_camera(p):return {}
 from .fpv import camera_mounts
 from .geometry import arc_slot
 result={}
 for role,mount,sign in zip(FLEX_ROLES[:2],camera_mounts(p),(-1,1)):
  if roles is not None and role not in roles:continue
  a,b=mount['plate_x'];cy,cz,w,h=insert_rect(p)
  # The uncompressed free pad protrudes by the specified preload. This is an
  # intentional fit allowance against the reference camera, not a rigid clash.
  face=sign*(p.CameraWidth/2-p.FlexPadPreload)
  inner=b if sign<0 else a
  lo,hi=sorted((face,inner))
  if p.FlexCameraMode=='Compression pads':
   blank=interface_blank(p,lo,hi-lo,p.FlexPadWidth,p.FlexPadHeight)
  else:
   from .camera_interface import insert_layers
   from .shape_cleanup import guard_refine
   layers=[interface_blank(p,layer['x'],layer['thickness'],w,h,layer['offset']) for layer in insert_layers(p,mount,sign)]
   blank=guard_refine(layers[0].multiFuse(layers[1:]))
  start=blank.BoundBox.XMin-1;length=blank.BoundBox.XLength+2
  tools=[Part.makeCylinder(p.CameraSideHoleDiameter/2,length,App.Vector(start,y,z),App.Vector(1,0,0)) for y,z in mount['side_holes']]
  tools += [arc_slot(arc,start,length) for arc in mount['side_arcs']]
  if tools and p.FlexCameraMode=='Captured inserts':
   boundary=Part.makeCompound(blank.Edges)
   if any(boundary.distToShape(tool)[0]<min(.8,p.MinimumWeb)-1e-6 for tool in tools):raise ValueError('Rounded camera insert needs more material around the tilt paths; increase opening size or reduce its corner radius/fit clearance.')
  from .shape_cleanup import guard_refine
  result[role]=guard_refine(blank.cut(Part.makeCompound(tools))) if tools else blank
 return result

def make_flex(p,carbon=None):
 from .protection_geometry import motor_protectors,side_guards
 result=camera_pads(p);result.update(motor_protectors(p,carbon));result.update(side_guards(p,carbon))
 if p.FlexFrontBumper:
  from .bumper_geometry import front_bumper
  result['FrontBumper']=front_bumper(p,dict(carbon or {},**result))
 for role,shape in result.items():
  if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1:raise ValueError(role+' must be one valid connected printable part; review its dimensions.')
 return result

def printable_flex(shape,role):
 flat=shape.copy()
 if role.startswith(('CameraPad','ElectronicsGuard')):flat.rotate(App.Vector(),App.Vector(1,1,1),-120)
 b=flat.BoundBox;flat.translate(App.Vector(-b.XMin,-b.YMin,-b.ZMin));return flat
