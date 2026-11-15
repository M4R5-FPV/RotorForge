"""Optional cage-local protection and O4 split isolation geometry."""
def split_o4(p):return p.FPVSystemProfile=='DJI O4 Air Unit Pro' and p.FlexCameraMode!='Hard mount'

def bumper_profile(p,mount):
 """Front strip shares material with the cage, ending at its plate contacts."""
 profile=mount['wall_profile'];z0,z1=mount['z0'],mount['z1'];inner=[];outer=[]
 for i in range(25):
  t=i/24;z=z0+(z1-z0)*t;hits=[]
  for a,b in zip(profile,profile[1:]+profile[:1]):
   if abs(a[1]-b[1])<1e-9:
    if abs(z-a[1])<1e-7:hits.extend((a[0],b[0]))
   elif min(a[1],b[1])-1e-7<=z<=max(a[1],b[1])+1e-7:hits.append(a[0]+(b[0]-a[0])*(z-a[1])/(b[1]-a[1]))
  y=max(hits);inner.append((y-.8,z));outer.append((y+(p.CameraTPUBumperReach+p.CameraTPUBumperToe*(1-t))*__import__('math').sin(__import__('math').pi*t/2),z))
 return tuple(inner+list(reversed(outer)))

def integrated_bumper(p,mount):
 import FreeCAD as App,Part
 a,b=mount['plate_x'];width=p.CameraTPUBumperWidth
 if a<0:a-=width
 else:b+=width
 pts=[App.Vector(a,y,z) for y,z in bumper_profile(p,mount)]
 return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(b-a,0,0))

def o4_tracks(mount):
 return tuple(dict(point=v) for v in mount['side_holes'])+tuple(dict(arc=v) for v in mount['side_arcs'])

def track_points(track,step=2.):
 import math
 if 'point' in track:return (track['point'],)
 arc=track['arc'];n=max(1,math.ceil((arc['end']-arc['start'])/step))
 angles=[arc['start']+(arc['end']-arc['start'])*i/n for i in range(n+1)]
 angles += [a for a in range(-360,721,90) if arc['start']<a<arc['end']]
 return tuple((arc['centre'][0]+arc['radius']*math.cos(math.radians(a)),arc['centre'][1]+arc['radius']*math.sin(math.radians(a))) for a in sorted(set(angles)))

def track_solid(track,width,x,length):
 import FreeCAD as App,Part
 if 'point' in track:return Part.makeCylinder(width/2,length,App.Vector(x,*track['point']),App.Vector(1,0,0))
 from .geometry import arc_slot
 return arc_slot(dict(track['arc'],width=width),x,length)

def o4_window(p,x,length,lip=0.):
 import Part
 from .fpv import camera_mounts
 return Part.makeCompound([track_solid(v,p.O4InsertDiameter+2*lip,x,length) for v in o4_tracks(camera_mounts(p)[0])])

def o4_pads(p,roles=None):
 import Part
 from .fpv import camera_mounts
 from .flex_options import FLEX_ROLES
 from .camera_interface import insert_layers
 from .flex_geometry import union
 result={}
 for role,mount,sign in zip(FLEX_ROLES[:2],camera_mounts(p),(-1,1)):
  if roles is not None and role not in roles:continue
  pads=[]
  for track in o4_tracks(mount):
   if p.FlexCameraMode=='Compression pads':
    a,b=mount['plate_x'];inner=b if sign<0 else a
    face=sign*(p.CameraWidth/2-p.FlexPadPreload);lo,hi=sorted((face,inner))
    layers=[dict(x=lo,thickness=hi-lo,offset=0.)]
   else:layers=insert_layers(p,mount,sign)
   diameter=p.O4InsertDiameter if p.FlexCameraMode=='Captured inserts' else p.O4PadDiameter
   solids=[track_solid(track,diameter+2*v['offset'],v['x'],v['thickness']) for v in layers]
   blank=union(solids);start=blank.BoundBox.XMin-1
   bore=track_solid(track,p.CameraSideHoleDiameter,start,blank.BoundBox.XLength+2)
   pads.append(blank.cut(bore))
  if len(pads)!=2 or pads[0].distToShape(pads[1])[0]<.3:
   raise ValueError('O4 isolation pieces must stay separate; reduce their diameter, lip or adjustable tilt range.')
  result[role]=Part.makeCompound(pads)
 return result

def outline_points(face):
 return [(v.x,v.y) for e in face.OuterWire.Edges for v in e.discretize(Deflection=.05)]

def front_at_x(face,x):
 import FreeCAD as App,Part
 b=face.BoundBox
 line=Part.makeLine(App.Vector(x,b.YMin-1,0),App.Vector(x,b.YMax+1,0))
 hits=face.common(line)
 if not hits.Vertexes:raise ValueError('TPU cage mounting width lies outside the bottom plate; widen the plate or move the cage.')
 return max(v.Point.y for v in hits.Vertexes)

def follow_bottom(p,mount,face):
 # Preserve the rear and upper attachments. Ease only the front boundary
 # into the actual bottom outline across the complete side-wall width.
 # Base sketch shape is intentionally not inferred from a few sampled
 # front-edge positions.  An irregular nose can vary across even the small
 # thickness of a side cheek.  The final 3D part is intersected with the
 # actual finished plate outline at its bottom contact (see tpu_cage).
 return follow_target(mount,front_at_x(face,sum(mount['plate_x'])/2),p)

def follow_target(mount,target,p=None):
 z0,z1=mount['z0'],mount['z1'];profile=mount['wall_profile']
 def bounds(z):
  ys=[]
  for q,v in zip(profile,profile[1:]+profile[:1]):
   if abs(q[1]-v[1])<1e-8:
    if abs(z-q[1])<1e-7:ys.extend((q[0],v[0]))
   elif min(q[1],v[1])-1e-7<=z<=max(q[1],v[1])+1e-7:ys.append(q[0]+(v[0]-q[0])*(z-q[1])/(v[1]-q[1]))
  return min(ys),max(ys)
 base=bounds(z0)[1];front=[];back=[]
 for i in range(25):
  t=i/24;z=z0+(z1-z0)*t;rear,y=bounds(z)
  # The lower end must meet the finished carbon edge. Above that contact,
  # the cage may project forward to shield the lens. A soft shoulder blends
  # that projection back to the unmodified upper mounting boundary.
  smooth=t*t*(3-2*t)
  y=y+(target-base)*(1-smooth)
  if p is not None and p.CameraCageStyle=='TPU cage' and p.CameraTPUBumper:
   # Do not expand the outer left/right footprint: only the front silhouette
   # changes. This is incorporated into the cheek itself, not a protruding box.
   from math import sin,pi
   arch=sin(pi*t)**2
   y+=(p.CameraTPUBumperReach + .25*p.CameraTPUBumperWidth)*arch
   # The lower shoulder sweeps further forward and merges into the plate
   # contact without a hard step or a second projecting rectangular solid.
   y+=.35*p.CameraTPUBumperToe*arch*(1-t)
  front.append((y,z));back.append((rear,z))
 result=dict(mount);result['wall_profile']=tuple(back+list(reversed(front)))
 return result

def cage_front_band(p,face,mount=None):
 import FreeCAD as App,Part
 from .protection_geometry import offset_face
 from .flex_geometry import box
 from .fpv import camera_mounts
 z=p.BottomThickness;wall=p.CameraTPUClampWall if p.CameraTPUClampBottom and p.CameraTPUBumper else p.CameraTPUBridge;fit=p.CameraTPUClampFit
 mounts=camera_mounts(p);depth=max(2.,wall+1.)
 fronts=[front_at_x(face,sum(m['plate_x'])/2) for m in mounts]
 # Follow the finished outer wire rather than a rectangular nose.
 rear=min(fronts)-max(depth,p.CameraTPUBumperToe)
 region=box(-1000,rear,-10,2000,2000,1000)
 if p.CameraTPUClampBottom and p.CameraTPUBumper:
  outer=offset_face(face,fit+wall);inside=offset_face(face,-max(1.,wall))
  ring=outer.cut(inside)
  band=ring.extrude(App.Vector(0,0,z+fit+2*wall));band.translate(App.Vector(0,0,-fit-wall))
  cavity=offset_face(face,fit).extrude(App.Vector(0,0,z+2*fit));cavity.translate(App.Vector(0,0,-fit))
  band=band.cut(cavity)
 else:
  ring=face.cut(offset_face(face,-depth))
  band=ring.extrude(App.Vector(0,0,wall));band.translate(App.Vector(0,0,z))
 band=band.common(region)
 if mount is not None:
  a,b=mount['plate_x'];reach=p.CameraTPUInnerReach
  if a<0:mask=box(-1000,-1000,-10,1000+min(-.3,b+reach),2000,1000)
  else:
   left=max(.3,a-reach);mask=box(left,-1000,-10,1000-left,2000,1000)
  band=band.common(mask)
 return band


def clip_lower_contact_to_plate(shape,face,bottom_z,contact_height=0.8):
 """Trim a TPU camera cage's plate-contact region to the real XY perimeter.

 No carbon cutouts are made. A TPU lip/clamp beneath the plate is preserved;
 the constraint applies only to the cage wall immediately above the plate.
 The outside mask includes *all* plate edges, not just its frontmost Y value.
 """
 import FreeCAD as App,Part
 if shape.isNull():return shape
 bounds=shape.BoundBox
 z0=bottom_z
 z1=min(bounds.ZMax,z0+contact_height)
 if z1<=z0+1e-7:return shape
 # Make the removal tool from a large horizontal XY sheet with a genuine
 # plate-shaped hole, then extrude only through the lower cage contact.
 margin=10.
 sheet=Part.makePlane(bounds.XLength+2*margin,bounds.YLength+2*margin,
                      App.Vector(bounds.XMin-margin,bounds.YMin-margin,0))
 try:
  outside=sheet.cut(face)
  if outside.isNull() or not outside.Faces:return shape
  tool=outside.extrude(App.Vector(0,0,z1-z0))
  tool.translate(App.Vector(0,0,z0))
  trimmed=shape.cut(tool)
  if trimmed.isNull() or not trimmed.isValid():
   raise ValueError('Could not trim TPU camera cage to the bottom-plate perimeter.')
  return trimmed
 except ValueError:raise
 except Exception as exc:
  raise ValueError('Could not use the finished bottom-plate outline for the TPU cage contact: '+str(exc)) from exc

def _perimeter_samples(wire, n=128):
 """Sample a plate outline without depending on specific OCC edge APIs.

 Older saved frames can generate trimmed edges whose arc-length parameter
 lookup is unsupported or numerically unstable. The wire discretizer gives
 an equivalent, uniformly spaced closed loop in those cases.
 """
 import math
 if wire is None or wire.isNull():
  raise ValueError('The camera-cage plate perimeter is empty.')
 try:
  raw=[(p.x,p.y) for p in wire.discretize(Number=n+1)]
 except Exception:
  raw=[(p.x,p.y) for edge in wire.Edges for p in edge.discretize(Deflection=.2)]
 if len(raw)>1 and math.dist(raw[0],raw[-1])<1.e-6:raw.pop()
 # Remove successive duplicate vertices before resampling. These are common
 # at tangent boundaries of profiled carbon plates.
 pts=[]
 for pt in raw:
  if not pts or math.dist(pts[-1],pt)>1.e-7:pts.append(pt)
 if len(pts)>2 and math.dist(pts[0],pts[-1])<1.e-7:pts.pop()
 if len(pts)<3:raise ValueError('Camera cage plate perimeter has too few points.')
 seg=[math.dist(pts[i],pts[(i+1)%len(pts)]) for i in range(len(pts))]
 total=sum(seg)
 if total<1.e-6:raise ValueError('Camera cage plate perimeter has zero length.')
 out=[];j=0;running=0.
 for i in range(n):
  target=i*total/n
  while j<len(seg)-1 and target>running+seg[j]:
   running+=seg[j];j+=1
  fraction=min(1.,max(0.,(target-running)/max(seg[j],1.e-12)))
  x0,y0=pts[j];x1,y1=pts[(j+1)%len(pts)]
  out.append((x0+(x1-x0)*fraction,y0+(y1-y0)*fraction))
 area=sum(x*y2-x2*y for (x,y),(x2,y2) in zip(out,out[1:]+out[:1]))
 if area<0:out.reverse()
 front=max(range(len(out)),key=lambda i:(out[i][1],-abs(out[i][0])))
 return out[front:]+out[:front]


def _section_wire(points,z,smooth=True):
 """Use a smooth closed section when OCC accepts it, otherwise a polygon."""
 import FreeCAD as App, Part
 verts=[App.Vector(x,y,z) for x,y in points]
 if smooth:
  try:
   curve=Part.BSplineCurve()
   curve.interpolate(verts,PeriodicFlag=True)
   edge=curve.toShape()
   if edge.isClosed() and edge.isValid():return Part.Wire([edge])
  except Exception:pass
 return Part.makePolygon(verts+[verts[0]])


def outline_cage_body(p, bottom_face, top_face, mounts, separate=False):
 """Cage with *two independent physical plate outlines* as its end profiles.

 Bottom interface: upper face of BottomPlate. Top interface: underside of
 TopPlate. Each cage perimeter station interpolates between those profiles;
 the contours therefore terminate exactly on the corresponding carbon edge.
 A mid-height nose projection is permitted, but never at either plate end.
 """
 import FreeCAD as App, Part, math
 from .protection_geometry import offset_face
 from .flex_geometry import box
 from .fpv import camera_angles
 from .geometry import camera_envelope
 z0=min(m['z0'] for m in mounts)
 z1=max(m['z1'] for m in mounts)
 height=z1-z0
 if height<5:raise ValueError('Insufficient space between the two plate contact faces for a TPU cage.')
 wall=max(1.2,min(3.,p.CameraTPUBridge))
 bottom_inner=offset_face(bottom_face,-wall)
 top_inner=offset_face(top_face,-wall)
 # Each outline is sampled with exactly the same vertex count and aligned
 # at the forwardmost point. Unlike the former code, the upper contour is
 # NOT a translated copy of the bottom plate.
 outlines=[_perimeter_samples(f.OuterWire) for f in (bottom_face,top_face)]
 interiors=[_perimeter_samples(f.OuterWire) for f in (bottom_inner,top_inner)]
 reach=float(p.CameraTPUBumperReach) if p.CameraTPUBumper else 0.
 front0=max(y for x,y in outlines[0]);front1=max(y for x,y in outlines[1])
 def sections(pair,smooth=True):
  result=[]
  for t in (0.,.125,.25,.375,.5,.625,.75,.875,1.):
   front=(1-t)*front0+t*front1
   points=[]
   for (x0,y0),(x1,y1) in zip(*pair):
    x=x0*(1-t)+x1*t;y=y0*(1-t)+y1*t
    # Forward extension is a rounded nose above the plate surface,
    # restrained laterally and forced to zero at both contacts.
    influence=max(0.,min(1.,(y-(front-12.))/12.))
    y+=reach*math.sin(math.pi*t)**2*influence
    points.append((x,y))
   result.append(_section_wire(points,z0+height*t,smooth))
  return result
 # A full-resolution periodic B-spline can occasionally self-intersect
 # around narrow notches in older saved plate profiles. Retry with matched
 # piecewise-linear sections, which stay close to the same plate silhouette.
 loft_error=None
 for smooth in (True,False):
  try:
   exterior=Part.makeLoft(sections(outlines,smooth),True,False)
   interior=Part.makeLoft(sections(interiors,smooth),True,False)
   if exterior.isNull() or interior.isNull():
    raise ValueError('A loft resulted in an empty shape.')
   shell=exterior.cut(interior)
   if shell.isNull() or not shell.isValid():
    raise ValueError('The wall subtraction produced an invalid solid.')
   break
  except Exception as exc:
   loft_error=exc
 else:
  raise ValueError('Cannot build the TPU camera cage from the saved plate outlines: '+str(loft_error)) from loft_error
 # Retain only the forward camera region of the plate-derived perimeter.
 rear=min(m['wall_profile'][i][0] for m in mounts for i in range(len(m['wall_profile'])))
 rear-=max(2.,wall)
 bounds=exterior.BoundBox
 shell=shell.common(box(bounds.XMin-2,rear,z0-.2,bounds.XLength+4,
                         bounds.YMax-rear+2,height+.4))
 # The central camera aperture is OPEN through the full plate-to-plate
 # height. The previous upper and lower full-width contact bands produced
 # unwanted solid material directly above and below the camera.
 clear_width=float(p.CameraWidth)+2*max(1.5,float(p.CameraSideClearance))
 shell=shell.cut(box(-clear_width/2,rear-1,z0-.5,clear_width,
                     bounds.YMax-rear+7,height+1))
 # Only a one-piece cage has a lower connection. Its rear edge is
 # smoothly swept into both side walls, instead of ending as a rectangular
 # slab. Independent dimensions control its rear reach and physical height.
 if not separate:
  reach_lower=float(p.CameraTPUFrontBridgeRearReach)
  bridge_height=float(p.CameraTPUFrontBridgeHeight)
  if bridge_height>=height-1.:
   raise ValueError('Lower TPU cage connection height leaves insufficient camera space; reduce its height.')
  half=clear_width/2+wall+.8 # overlap the inner edge of both cage cheeks
  central_front=bottom_face.common(box(-half,bottom_face.BoundBox.YMin-1,-1,
       2*half,bottom_face.BoundBox.YLength+2,2))
  if central_front.isNull():
   raise ValueError('The bottom plate does not reach the proposed camera-cage lower connection.')
  nose=central_front.BoundBox.YMax
  # A rounded rear boundary is shallow at centre and eases into the rear
  # of the existing left/right cheeks. Ends have zero derivative (no lips).
  # All stations use matching perimeter points so the loft stays coherent.
  def lower_wire(t):
   z=z0+bridge_height*t
   # The upper edge becomes a little shallower to give a soft rearward
   # slope; the front is finally trimmed by the actual cage exterior.
   depth_scale=1.-.15*(3*t*t-2*t*t*t)
   back=[]
   for i in range(33):
    u=-1.+2.*i/32
    smooth=3*abs(u)**2-2*abs(u)**3
    depth=reach_lower*(.77+.23*smooth)*depth_scale
    back.append(App.Vector(half*u,nose-depth,z))
   # The forward edge is deliberately oversized here and then cropped to
   # the genuine plate-to-plate loft, leaving no projecting front tabs.
   front=[App.Vector(half*u,nose+max(4.,reach+2.),z)
          for u in (1.-2.*i/32 for i in range(33))]
   rear_curve=Part.BSplineCurve()
   rear_curve.interpolate(back)
   return Part.Wire([rear_curve.toShape(),
                     Part.makeLine(back[-1],front[0]),
                     Part.makeLine(front[0],front[-1]),
                     Part.makeLine(front[-1],back[0])])
  try:
   bridge=Part.makeLoft([lower_wire(t) for t in (0.,.33,.67,1.)],True,False)
   bridge=bridge.common(exterior)
   if bridge.isNull() or not bridge.isValid():
    raise ValueError('Curved bridge did not create a valid solid.')
  except Exception:
   # A plate with complex front cut-ins may not support the multi-section
   # bridge loft. Use a rounded 2D footprint instead of failing the frame.
   from .protection_geometry import offset_face
   bridge_start=nose-reach_lower
   footprint=central_front.common(box(-half,bridge_start,-1,2*half,
                                       reach_lower+2,2))
   if footprint.isNull():
    raise ValueError('There is no bottom-plate support beneath the TPU lower connection.')
   bridge=footprint.extrude(App.Vector(0,0,bridge_height))
   bridge.translate(App.Vector(0,0,z0))
   bridge=bridge.common(exterior)
   if bridge.isNull():
    raise ValueError('The TPU lower connection cannot meet the two cage sides.')
  shell=shell.fuse(bridge)
 # The shell's end sections themselves already match the finished upper
 # and lower carbon plate profiles. Never add a solid upper cross-piece.
 # Preserve the camera's full configured sweep, without carving carbon.
 angles=camera_angles(p)
 for angle in sorted(set((angles[0],angles[-1],p.CameraTilt))):
  envelope=camera_envelope(p,angle)
  if envelope is not None and not envelope.isNull():shell=shell.cut(envelope)
 if shell.isNull():raise ValueError('TPU cage has no material after applying the camera clearance.')
 if separate:
  gap=max(.5,p.CameraWidth*.10)
  masks=(box(bounds.XMin-2,rear,z0-1,-gap/2-bounds.XMin+2,bounds.YMax-rear+4,height+2),
         box(gap/2,rear,z0-1,bounds.XMax-gap/2+2,bounds.YMax-rear+4,height+2))
  return tuple(shell.common(mask) for mask in masks)
 return (shell,)



def _join_nearby_cage_solids(shape, p, forbidden=()):
 """Repair small gaps between a TPU cage cheek and its mounting shell.

 The plate-outline wall and the original camera cheek are independently
 constructed. On some saved plate profiles, their surfaces approach without
 actually intersecting, yielding multiple solids. Close *local*, same-side
 gaps with a short TPU web, but never bridge across the camera opening or
 into any camera, screw, insert, or plate clearance volume.

 This deliberately does not connect left and right sides: only the configured
 one-piece lower bridge may do that.
 """
 import FreeCAD as App, Part
 from .geometry import camera_envelope
 from .fpv import camera_angles
 camera_tools=[camera_envelope(p,a) for a in
               sorted(set((*camera_angles(p),p.CameraTilt)))]
 blocked=tuple(tool for tool in (*forbidden,*camera_tools)
               if tool is not None and not tool.isNull())
 current=shape.removeSplitter()
 if current.isNull() or not current.isValid():return current
 # Limit the number of joins and reject distant pieces. A larger gap
 # suggests genuinely missing geometry rather than a tolerance issue.
 for _ in range(min(32,max(0,len(current.Solids)-1))):
  solids=sorted(current.Solids,key=lambda obj:obj.Volume,reverse=True)
  if len(solids)<=1:return current
  best=None
  for i,a in enumerate(solids):
   for j,b in enumerate(solids[i+1:],i+1):
    # Never use an accidental bar across the camera centreline.
    if (a.CenterOfMass.x<-.1 and b.CenterOfMass.x>.1 or
        b.CenterOfMass.x<-.1 and a.CenterOfMass.x>.1):continue
    try:gap,pairs,_=a.distToShape(b)
    except Exception:continue
    if not pairs or gap>4.0:continue
    va,vb=pairs[0]
    if best is None or gap<best[0]:best=(gap,i,j,va,vb)
  if best is None:break
  _,i,j,a,b=best
  delta=b.sub(a)
  if delta.Length<1e-6:
   # Coincident-touching solids can still have only edge contact. Place
   # a small ball around the contact to create a real overlap.
   web=Part.makeSphere(1.2,a)
  else:
   direction=delta.normalize()
   web=Part.makeCylinder(1.2,(b-a).Length+2.4,a-direction*1.2,direction)
  if any(web.common(tool).Volume>1e-7 for tool in blocked):break
  candidate=current.fuse(web).removeSplitter()
  if candidate.isNull() or not candidate.isValid() or len(candidate.Solids)>=len(solids):break
  current=candidate
 return current

def _remove_boolean_cage_scraps(shape,p,mounts):
 """Remove minor orphan solids after clearance cuts, retaining camera mounts.

 A piece is protected if it overlaps one of the original mount brackets;
 otherwise it must be a substantial side wall or the lower cross-bridge.
 """
 import Part
 from .geometry import camera_bracket
 solids=shape.Solids
 if len(solids)<=2:return shape
 brackets=[camera_bracket(p,m) for m in mounts]
 protected=[]
 for part in solids:
  try:
   if any(part.common(bracket).Volume>1.e-4 for bracket in brackets):
    protected.append(part)
  except Exception:pass
 # At most one additional unconnected wall per side, plus the bridge.
 keep=list(protected)
 for sign in (-1,1):
  candidates=[s for s in solids if s not in keep and s.CenterOfMass.x*sign>.05]
  if candidates:
   main=max(candidates,key=lambda s:s.Volume)
   if main.Volume>.5:keep.append(main)
 if p.CameraTPUConstruction=='One-piece cage':
  bridges=[s for s in solids if s not in keep and s.BoundBox.XMin<0<s.BoundBox.XMax]
  if bridges:
   bridge=max(bridges,key=lambda s:s.Volume)
   if bridge.Volume>.5:keep.append(bridge)
 return Part.makeCompound(keep).removeSplitter() if keep else shape


def _retain_cage_structure(shape, p, mounts):
 """Discard Boolean slivers, not real camera attachment geometry.

 The shell is a full-plate perimeter loft clipped down to a camera nose.
 On profiled plates the centre aperture and camera sweep can cut a single
 wall into numerous disconnected chips. Such chips must never be delivered
 as printable solids or used as intermediate links to the mounting cheeks.

 Keep the substantial left/right wall for each camera bracket; for a one-
 piece cage also retain the largest centre-crossing lower bridge. This is a
 selection of *existing* CAD solids, not a visual-only simplification.
 """
 import Part
 solids=[s for s in shape.Solids if not s.isNull() and s.Volume>1.e-5]
 if len(solids)<=1:return shape
 # The original camera brackets are constructed separately and remain
 # untouched. Only the NEW plate-outline shell is filtered here.
 z0=min(m['z0'] for m in mounts)
 z1=max(m['z1'] for m in mounts)
 wall_height=z1-z0
 kept=[]
 for sign in (-1,1):
  candidates=[s for s in solids if s.CenterOfMass.x*sign>.05]
  if not candidates:continue
  # A full-height cheek is preferred over tiny fragments at a curved nose.
  # The size score also avoids retaining an isolated long, threadlike lip.
  best=max(candidates,key=lambda s:s.Volume *
      (0.5+0.5*min(1.,s.BoundBox.ZLength/max(1.,wall_height))))
  if best not in kept:kept.append(best)
 if p.CameraTPUConstruction=='One-piece cage':
  central=[s for s in solids if s.BoundBox.XMin<-.05 and s.BoundBox.XMax>.05]
  if central:
   bridge=max(central,key=lambda s:s.Volume)
   if bridge not in kept:kept.append(bridge)
 if not kept:raise ValueError('The plate outline produced no usable TPU cage side walls.')
 return Part.makeCompound(kept)



def _supported_outline_cage(p, mounts, bottom_face, top_face, inputs):
 """Construct local cage walls anchored to the original screw-bearing cheeks.

 Unlike a full-board annular loft, these bands are generated only over the
 camera mounting X spans. Each front-band overlaps the pre-existing camera
 bracket in Y by at least 1.5 mm. The side strips therefore cannot create
 orphaned plate-perimeter segments near unrelated plate notches or cutouts.
 No plates are modified. This is a conservative fallback for very irregular
 saved plate profiles whose annular loft breaks into disconnected fragments.
 """
 import FreeCAD as App, Part
 from .geometry import camera_bracket, camera_envelope
 from .fpv import camera_angles
 from .flex_geometry import box
 from .protection_geometry import outer_face
 from .camera_cages import boss_x
 import math
 z0=min(m['z0'] for m in mounts);z1=max(m['z1'] for m in mounts)
 height=z1-z0
 components=[]
 cheek_front=[]
 for mount in mounts:
  xmin,xmax=mount['plate_x']
  xm=(xmin+xmax)/2
  base=mount['attachment_profile']
  # Attachment profile is ordered: rear-bottom, front-bottom, front-top, rear-top.
  bottom_y=base[1][0];top_y=base[2][0]
  bplate=front_at_x(bottom_face,xm)
  tplate=front_at_x(top_face,xm)
  # A genuine overlap with the original cage cheek is mandatory. The front
  # follows the finished plate interface without making an unsupported lip.
  depth=1.7
  front=[];rear=[]
  for k in range(17):
   t=k/16.
   smooth=t*t*(3-2*t)
   nominal=bottom_y+(top_y-bottom_y)*smooth
   plate_front=bplate+(tplate-bplate)*smooth
   profile_front=nominal+max(-.5,plate_front-nominal)*(1-0.13*math.sin(math.pi*t)**2)
   # Do not add a nose forward of the physical carbon edges at contact.
   if k==0:profile_front=bplate
   if k==16:profile_front=tplate
   z=z0+height*t
   front.append(App.Vector(xmin,profile_front,z))
   rear.append(App.Vector(xmin,min(nominal-1.7,profile_front-1.2),z))
  polygon=rear+list(reversed(front))
  face=Part.Face(Part.makePolygon(polygon+[polygon[0]]))
  strip=face.extrude(App.Vector(xmax-xmin,0,0))
  bracket=camera_bracket(p,mount)
  combined=bracket.fuse(strip).removeSplitter()
  if combined.isNull() or not combined.isValid() or len(combined.Solids)!=1:
   # Never ship a floating cosmetic skin with a mounting part.
   raise ValueError('Plate-following cage wall cannot connect to '+mount['role']+'; check camera attachment and plate contour.')
  components.append(combined)
  cheek_front.append((xmin,xmax,bplate))
 joined=p.CameraTPUConstruction=='One-piece cage'
 if joined:
  # Lower bridge connects the two side cheeks; it is not a full-height band.
  # It is deliberately inset from the front; the camera-clearance cutter
  # below is applied to the entire assembled cage.
  x0=min(v[0] for v in cheek_front)+.4
  x1=max(v[1] for v in cheek_front)-.4
  front=min(v[2] for v in cheek_front)-.25
  reach=float(p.CameraTPUFrontBridgeRearReach)
  h=min(float(p.CameraTPUFrontBridgeHeight),height-1.)
  bridge=box(x0,front-reach,z0,x1-x0,reach+0.5,h)
  components.append(bridge)
 result=components[0].multiFuse(components[1:]).removeSplitter()
 # Reopen *all* original access paths through any additional TPU material.
 from .geometry import arc_slot
 from .flex_geometry import camera_window
 cuts=[]
 b=result.BoundBox
 for mount in mounts:
  x=b.XMin-1.;length=b.XLength+2.
  if p.FlexCameraMode=='Captured inserts':
   cuts.append(camera_window(p,x,length))
  else:
   cuts.extend(Part.makeCylinder(p.CameraSideHoleDiameter/2,length,
                App.Vector(x,y,z),App.Vector(1,0,0)) for y,z in mount['side_holes'])
   cuts.extend(arc_slot(a,x,length) for a in mount['side_arcs'])
  sign=-1 if mount['plate_x'][0]<0 else 1
  cx=boss_x(p,sign)
  for ys,z,side in ((mount['tabs_y'],z0,1),(mount['top_tabs_y'],z1,-1)):
   cuts.extend(Part.makeCylinder(p.CameraTPUScrewBore/2,p.CameraTPUInsertDepth+.03,
        App.Vector(cx,y,z-.02 if side>0 else z-p.CameraTPUInsertDepth-.01)) for y in ys)
 if cuts:result=result.cut(Part.makeCompound(cuts))
 for a in sorted(set((*camera_angles(p),p.CameraTilt))):
  envelope=camera_envelope(p,a)
  if not envelope.isNull():result=result.cut(envelope)
 for plate in (inputs['BottomPlate'],inputs['TopPlate']):
  if not plate.isNull():result=result.cut(plate)
 result=result.removeSplitter()
 if result.isNull() or not result.isValid() or len(result.Solids)!=1:
  raise ValueError('The camera mounting and plate-following TPU cage cannot form one connected solid at these dimensions. No disconnected fragments were accepted.')
 return result


def tpu_cage(p,role,inputs):
 """Generate the plate-outline cage directly; never fuse legacy camera cheeks."""
 from .tpu_outline_cage import make_tpu_cage
 return make_tpu_cage(p,role,inputs)
