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
 # TPU cage has an independent, centred camera interface outline; never
 # import its old carbon side-plate profile.
 # TPU non-rounded interface shapes use their own matching polygon profiles.
 # Expand/shrink its dimensions directly instead of asking OCC to offset a
 # small polygon face (which may self-intersect at small neck sizes).
 # The carbon camera side-plate interface keeps its original offset logic.
 tpu_profile=(getattr(p,'CameraCageStyle','')=='TPU cage' and
              getattr(p,'FlexInterfaceShape','')!='Rounded rectangle')
 if tpu_profile and offset:
  width+=2*offset; height+=2*offset
  if min(width,height)<=1.:
   raise ValueError('TPU insert contact is too small after fit clearance.')
  offset=0.
 profile_p=p
 # Use the same *polygon* on both sides of the TPU captured-insert seat.
 # The former arc fillets produced tiny/self-intersecting faces for chamfered
 # outlines and did not match the polygonal fallback loft.
 if tpu_profile:
  from .tpu_isolation_layout import tpu_interface_polygon
  points=tpu_interface_polygon(p,width,height)
  # Construct in the destination YZ plane. Rotating an already extruded
  # polygon produced avoidable orientation/placement differences from the
  # exact cage aperture, particularly for non-rectangular shapes.
  vertices=[App.Vector(x,y,z) for y,z in points]
  wire=Part.makePolygon(vertices+[vertices[0]])
  if not wire.isClosed() or not wire.isValid():
   raise ValueError('TPU interface polygon is not a closed valid wire.')
  face=Part.Face(wire)
  if face.isNull() or not face.isValid():
   raise ValueError('TPU interface polygon is not a valid planar face.')
  solid=face.extrude(App.Vector(thickness,0,0))
  if solid.isNull() or not solid.isValid() or len(solid.Solids)!=1:
   raise ValueError('TPU interface '+p.FlexInterfaceShape+' could not form one valid solid.')
  return solid
 corners=profile_corners(profile_p,width,height);edges=[]
 def point(v):return App.Vector(*v,0)
 for previous,corner in zip(corners[-1:]+corners[:-1],corners):
  if math.dist(previous['end'],corner['start'])>1e-8:edges.append(Part.makeLine(point(previous['end']),point(corner['start'])))
  if corner['radius']:edges.append(Part.Arc(point(corner['start']),point(corner['mid']),point(corner['end'])).toShape())
 face=Part.Face(Part.Wire(edges))
 if offset:face=face.makeOffset2D(offset,join=0)
 if not face.isValid():raise ValueError('Camera interface radius or fit does not form a valid outline; reduce the radius or clearance.')
 solid=face.extrude(App.Vector(0,0,thickness));solid.rotate(App.Vector(),App.Vector(1,1,1),120);solid.translate(App.Vector(x,0,0));return solid



def _tpu_insert_loft(p,bands,width,height,datum):
 """Single-solid alternate construction for the removable TPU captured insert.

 Each band is (x_begin, x_end, outline_offset). The loft is made from
 ordered eight-edge sections; it cannot yield separate fused layers. Local
 steps between the contact flange, neck and retention flange are represented
 by short transitions (0.03 mm), avoiding coincident OCC faces.
 """
 from .tpu_isolation_layout import tpu_interface_polygon
 if not bands:raise ValueError('Captured insert has no cross-section bands.')
 boundaries=sorted({round(a,7) for a,b,o in bands}|{round(b,7) for a,b,o in bands})
 if len(boundaries)<2:raise ValueError('Captured insert has no axial thickness.')
 def offset_at(x):
  options=[o for a,b,o in bands if a-1.e-6<=x<=b+1.e-6]
  return max(options) if options else None
 sections=[]
 for i,(a,b) in enumerate(zip(boundaries,boundaries[1:])):
  mid=(a+b)*.5;off=offset_at(mid)
  if off is None:continue
  transition=min(.018,(b-a)*.12)
  for x in (a+transition,b-transition):
   if sections and x<=sections[-1][0]+1.e-6:continue
   sections.append((x,off))
 if len(sections)<2:raise ValueError('Captured insert has no connected axial regions.')
 wires=[]
 for x,offset in sections:
  w=width+2*offset;h=height+2*offset
  if min(w,h)<=1.:raise ValueError('Captured insert fit clearance collapses its profile.')
  points=tpu_interface_polygon(p,w,h)
  vertices=[App.Vector(x,y+datum.y,z+datum.z) for y,z in points]
  wires.append(Part.makePolygon(vertices+[vertices[0]]))
 solid=Part.makeLoft(wires,True,True)
 if solid.isNull() or not solid.isValid() or len(solid.Solids)!=1:
  raise ValueError('TPU captured insert loft did not form one solid.')
 return solid

def camera_window(p,x,thickness):
 from .cage_extensions import split_o4,o4_window
 if split_o4(p):return o4_window(p,x,thickness)
 cy,cz,w,h=insert_rect(p);return interface_blank(p,x,thickness,w,h)

def _tpu_camera_pads(p,roles=None):
 """Separate printable TPU camera isolators; NEVER use carbon-plate inserts.

 The load-bearing cage is a continuous solid with its own inner wall and
 dedicated through-wall cassette seat. Pad and insert shapes are generated against that wall,
 without replacing the cage face or changing any carbon mounting hole.
 """
 from .fpv import camera_mounts
 from .tpu_outline_cage import _mount_with_socket_width,tpu_insert_pocket_depths
 from .camera_interface import lip_sides
 from .geometry import arc_slot
 from .cage_extensions import o4_tracks,track_solid
 result={}
 for role,mount,sign in zip(FLEX_ROLES[:2],camera_mounts(p),(-1,1)):
  if roles is not None and role not in roles:continue
  mount=_mount_with_socket_width(p,mount)
  xmin,xmax=mount['plate_x']
  inner=xmax if sign<0 else xmin
  # Compression pads live in local recessed seats, not in a void created
  # by moving the ENTIRE cage wall away from the camera.
  camera_face=sign*(p.CameraWidth/2-p.FlexPadPreload)
  if p.FlexCameraMode=='Compression pads':
   from .tpu_isolation_layout import compression_pad_x_span
   lo,hi=compression_pad_x_span(p,mount,sign)
  else:
   lo,hi=sorted((camera_face,inner))
   if hi-lo<.1:
    raise ValueError('Not enough camera-facing contact for TPU captured inserts.')
  if p.FPVSystemProfile=='DJI O4 Air Unit Pro':
   # O4 has two independent camera screw tracks per side. Those pads must
   # retain their own bodies rather than using a giant rectangular window.
   items=[]
   for track in o4_tracks(mount):
    diameter=p.O4PadDiameter if p.FlexCameraMode=='Compression pads' else p.O4InsertDiameter
    if p.FlexCameraMode=='Compression pads':
     pieces=[track_solid(track,diameter,lo,hi-lo)]
    else:
     from .tpu_captured_layout import insert_x_spans
     spans=insert_x_spans(p,mount,sign)
     inside,outside=lip_sides(p)
     c0,c1=sorted((camera_face,inner))
     pieces=[track_solid(track,diameter-2*p.FlexInsertFit,
                         spans['neck'][0],spans['neck'][1]-spans['neck'][0])]
     if c1-c0>.1:
      pieces.append(track_solid(track,diameter+2*p.FlexInsertLip if inside
                                else diameter-2*p.FlexInsertFit,c0,c1-c0))
     if outside:
      f0,f1=spans['flange']
      pieces.append(track_solid(track,diameter+2*p.FlexInsertLip,f0,f1-f0))
    solid=pieces[0].multiFuse(pieces[1:]) if len(pieces)>1 else pieces[0]
    from .geometry import arc_slot
    bore=track_solid(track,p.CameraSideHoleDiameter,solid.BoundBox.XMin-1,solid.BoundBox.XLength+2)
    solid=solid.cut(bore)
    if solid.isNull() or not solid.isValid() or len(solid.Solids)!=1:
     raise ValueError(role+' DJI O4 TPU isolator is not one valid solid.')
    items.append(solid)
   # Two independent O4 isolators are intentionally separate printable pads.
   if len(items)!=2 or items[0].distToShape(items[1])[0]<.3:
    raise ValueError('DJI O4 TPU isolators overlap; reduce diameter or adjustable tilt range.')
   result[role]=Part.makeCompound(items)
   continue
  from .tpu_isolation_layout import tpu_isolator_datum,isolator_required_dimensions
  from .flex import insert_rect
  cy0,cz0,_,_=insert_rect(p)
  cy1,cz1=tpu_isolator_datum(p,mount)
  delta=App.Vector(0,cy1-cy0,cz1-cz0)
  desired_w,desired_h=isolator_required_dimensions(p,mount)
  width,height=(p.FlexInsertWidth,p.FlexInsertHeight) if p.FlexCameraMode=='Captured inserts' else (p.FlexPadWidth,p.FlexPadHeight)
  if width+1.e-6<desired_w or height+1.e-6<desired_h:
   raise ValueError('%s TPU isolator is too small for the camera screw travel: '
                    'needs at least %.2f x %.2f mm, selected %.2f x %.2f mm. '
                    'Increase the isolator dimensions; the cage outer outline will not move.'
                    % (role,desired_w,desired_h,width,height))
  bands=[]
  if p.FlexCameraMode=='Compression pads':
   # Independent compression pad, not a hole through the structural wall.
   pieces=[interface_blank(p,lo,hi-lo,p.FlexPadWidth,p.FlexPadHeight)]
  else:
   # Through-wall TPU cassette: its neck fills the entire cage thickness,
   # unlike the legacy blind pocket (which left a visible structural skin
   # hiding the insert). A little assembly clearance separates the neck
   # from its matching through-opening. Inner and outer lips remain optional.
   w,h=p.FlexInsertWidth,p.FlexInsertHeight
   inside,outside=lip_sides(p)
   bands=[]
   from .tpu_captured_layout import insert_x_spans
   spans=insert_x_spans(p,mount,sign)
   neck_start,neck_end=spans['neck']
   neck_offset=-p.FlexInsertFit
   neck=interface_blank(p,neck_start,neck_end-neck_start,w,h,neck_offset)
   pieces=[neck]
   bands.append((neck_start,neck_end,neck_offset))
   # Extend the camera-facing contact from the inside of the wall up to the
   # camera housing; it may have a wider face for vibration isolation.
   contact_offset=p.FlexInsertLip if inside else neck_offset
   if sign<0:
    c0=inner+.10
    c1=camera_face
   else:
    c0=camera_face
    c1=inner-.10
   c0,c1=sorted((c0,c1))
   if c1-c0>.1:
    contact=interface_blank(p,c0,c1-c0,w,h,contact_offset)
    pieces.append(contact)
    bands.append((c0,c1,contact_offset))
   if outside:
    # The external lip either projects as before, or occupies a matching
    # cavity *inside* the cage with its exterior exactly flush to the wall.
    # In flush mode the neck also stops at the exterior plane.
    f0,f1=spans['flange']
    if f1-f0>.2:
     flange=interface_blank(p,f0,f1-f0,w,h,p.FlexInsertLip)
     pieces.append(flange)
     bands.append((f0,f1,p.FlexInsertLip))
  # All layers share the actual camera-screw datum. Do not move the cage.
  for piece in pieces:piece.translate(delta)
  from .shape_cleanup import guard_refine
  def single_solid(shape):
   return not shape.isNull() and shape.isValid() and len(shape.Solids)==1
  # IMPORTANT: use discrete, overlapping PRISMATIC layers for every TPU
  # interface shape. The old polygon-only ruled loft interpolated between
  # the larger retaining flange and smaller neck THROUGH the exterior cage
  # face. That taper intruded into uncut cage material, which triggered
  # "CameraPadLeft intersects CameraMountLeft" for Octagon/Hexagon etc.
  # Rounded rectangle already used the correct prismatic construction.
  try:
   blank=guard_refine(pieces[0].multiFuse(pieces[1:])) if len(pieces)>1 else pieces[0]
  except Exception as exc:
   raise ValueError('%s TPU %s insert layers could not be fused without a '
                    'taper into the cage wall: %s' %
                    (role,p.FlexInterfaceShape,exc)) from exc
  if not single_solid(blank):
   raise ValueError('%s TPU %s insert layers did not form one valid solid. '
                    'Check retaining-lip and neck overlap; no tapered '
                    'loft has been substituted.' % (role,p.FlexInterfaceShape))
  start=blank.BoundBox.XMin-1;length=blank.BoundBox.XLength+2
  cutters=[('screw %d'%(i+1),Part.makeCylinder(p.CameraSideHoleDiameter/2,length,App.Vector(start,y,z),App.Vector(1,0,0))) for i,(y,z) in enumerate(mount['side_holes'])]
  cutters += [('tilt path %d'%(i+1),arc_slot(arc,start,length)) for i,arc in enumerate(mount['side_arcs'])]
  for label,cutter in cutters:
   attempt=blank.cut(cutter)
   if not single_solid(attempt):
    # Do not silently remove the screw/tilt opening: a split means the
    # selected removable insert cannot retain sufficient structural web.
    raise ValueError('%s TPU isolator %s splits the removable insert; '
                     'increase its length/height or reduce the tilt range.'%(role,label))
   blank=attempt
  result[role]=blank
 return result

def camera_pads(p,roles=None):
 if not soft_camera(p):return {}
 if p.CameraCageStyle=='TPU cage':
  return _tpu_camera_pads(p,roles)
 from .cage_extensions import split_o4,o4_pads
 if split_o4(p):return o4_pads(p,roles)
 from .fpv import camera_mounts
 from .geometry import arc_slot
 from .cage_extensions import o4_tracks,track_solid
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
   from .camera_interface import insert_layers,lip_sides
   from .shape_cleanup import guard_refine
   if p.CameraCageStyle=='TPU cage':
    # The insert is retained in the TPU wall's shallow, blind pocket;
    # the non-TPU camera plates retain their original through-insert layers.
    from .tpu_outline_cage import tpu_insert_pocket_depths
    neck,lip=tpu_insert_pocket_depths(p,b-a)
    inside,outside=lip_sides(p)
    neck_start=inner-neck if sign<0 else inner
    pieces=[interface_blank(p,lo,hi-lo,w,h,p.FlexInsertLip if inside else -p.FlexInsertFit),
            interface_blank(p,neck_start,neck,w,h,-p.FlexInsertFit)]
    if outside and lip>.1:
     lip_start=inner-neck-lip if sign<0 else inner+neck
     pieces.append(interface_blank(p,lip_start,lip,w,h,p.FlexInsertLip))
    blank=guard_refine(pieces[0].multiFuse(pieces[1:]))
   else:
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
 if p.FlexRearAntenna:
  from .antenna_geometry import rear_antenna_mount
  result['RearAntennaMount']=rear_antenna_mount(p,dict(carbon or {},**result))
 if p.FlexELRSEnabled:
  from .elrs_geometry import elrs_mount
  result['ELRSAntennaMount']=elrs_mount(p,dict(carbon or {},**result))
 for role,shape in result.items():
  if shape.isNull() or not shape.isValid() or len(shape.Solids)!=(2 if role.startswith('CameraPad') and p.FPVSystemProfile=='DJI O4 Air Unit Pro' and p.FlexCameraMode!='Hard mount' else 1):raise ValueError(role+' must be one valid connected printable part; review its dimensions.')
 return result

def printable_flex(shape,role):
 # Preserve the previously working FreeCAD export geometry.  Solid isolation
 # happens only as a non-blocking STEP file optimisation (not for STL).
 flat=shape.copy()
 if role.startswith(('CameraPad','ElectronicsGuard')):flat.rotate(App.Vector(),App.Vector(1,1,1),-120)
 b=flat.BoundBox;flat.translate(App.Vector(-b.XMin,-b.YMin,-b.ZMin));return flat
