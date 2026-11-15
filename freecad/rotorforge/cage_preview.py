"""Lightweight TPU cage footprint, using the finished bottom plate path."""
def outline(p):
 from .airflow_gui import finished_part_path,QtGui
 path=finished_part_path(p,'BottomPlate');polys=path.toSubpathPolygons()
 def area(poly):
  pts=list(poly);return abs(sum(a.x()*b.y()-b.x()*a.y() for a,b in zip(pts,pts[1:]+pts[:1])))
 poly=max(polys,key=area);result=QtGui.QPainterPath();result.addPolygon(poly);result.closeSubpath();return result,[(v.x(),v.y()) for v in poly]

def front(points,x):
 hits=[]
 for a,b in zip(points,points[1:]+points[:1]):
  if abs(a[0]-b[0])<1e-9:
   if abs(x-a[0])<1e-7:hits.extend((a[1],b[1]))
  elif min(a[0],b[0])<=x<=max(a[0],b[0]):hits.append(a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0]))
 return max(hits) if hits else max(y for x,y in points)

def preview_mount(p,mount):
 from .cage_extensions import follow_target
 _,pts=outline(p);a,b=mount['plate_x'];return follow_target(mount,min(front(pts,a+(b-a)*i/4) for i in range(5)),p)

def front_band_path(p):
 """Bottom-contact footprint matching the native rounded rear bridge.

 The front edge is the actual finished bottom-plate contour. The adjustable
 corner blend only changes the rear edge, never the carbon contact outline.
 """
 from .airflow_gui import QtGui
 from .fpv import camera_mounts
 from .flex import tpu_hard_bearing
 _,pts=outline(p)
 mounts=camera_mounts(p)
 x0=mounts[0]['plate_x'][0]+.3
 x1=mounts[1]['plate_x'][1]-.3
 path=QtGui.QPainterPath()
 if x1<=x0:return path
 rear=front(pts,0.)-float(p.CameraTPUFrontBridgeRearReach)
 blend=max(0.,min(10.,float(getattr(p,'CameraTPUFrontBridgeBlend',3.0))))
 span=max(2.,1.5*blend) if blend else 1.
 from .flex import camera_inner
 inner_x=(tpu_hard_bearing(p)[0] if p.FlexCameraMode=='Hard mount'
          else camera_inner(p))
 inside_left,inside_right=-inner_x,inner_x
 def smooth(t):
  t=max(0.,min(1.,t));return t*t*(3.-2.*t)
 for i in range(49):
  x=x0+(x1-x0)*i/48.
  proximity=max((inside_left+span-x)/span,(x-inside_right+span)/span)
  back=rear-blend*smooth(proximity)
  if front(pts,x)-back<.25:return QtGui.QPainterPath()
  if i==0:path.moveTo(x,back)
  else:path.lineTo(x,back)
 for i in range(48,-1,-1):
  x=x0+(x1-x0)*i/48.
  path.lineTo(x,front(pts,x))
 path.closeSubpath()
 return path


def unified_side_elevation(p, role):
    """Approximate the real TPU cheek loft in the lightweight Qt editor.

    This schematic uses the same finished plate boundaries as the 3D model;
    it does not display the obsolete camera-bracket polygon. It is deliberately
    a 2D elevation, not an exact projection of a FreeCAD BRep solid.
    """
    from .airflow_gui import finished_part_path, QtGui, QtCore, capsule_path
    from .fpv import camera_mounts, camera_position_y
    import math
    mount=next(m for m in camera_mounts(p) if m['role']==role)
    def perimeter(part):
        path=finished_part_path(p,part)
        polys=path.toSubpathPolygons()
        # Qt's QPolygonF is iterable but does not consistently implement
        # Python slice indexing (notably in some FreeCAD PySide builds).
        # Convert to a list before closing the perimeter for shoelace area.
        contours=[list(poly) for poly in polys if len(poly)>=3]
        if not contours:
            raise ValueError('The %s has no usable perimeter for the TPU cage preview' % part)
        def signed_area(points):
            return sum(u.x()*v.y()-v.x()*u.y()
                       for u,v in zip(points,points[1:]+points[:1]))
        poly=max(contours,key=lambda points:abs(signed_area(points)))
        return [(v.x(),v.y()) for v in poly]
    lower=perimeter('BottomPlate');upper=perimeter('TopPlate')
    x=sum(mount['plate_x'])/2
    yf0=front(lower,x);yf1=front(upper,x)
    y0=yf0-float(p.CameraTPUBottomRearReach)
    y1=yf1-float(p.CameraTPUTopRearReach)
    z0,z1=mount['z0'],mount['z1'];cy=camera_position_y(p);zbase=p.BottomThickness
    def pos(y,z):return QtCore.QPointF(y-cy,z-zbase)
    path=QtGui.QPainterPath(pos(y0,z0))
    # The rear/front follow the same two-contact ruled wall as the CAD cage.
    for k in range(1,25):
        t=k/24.;e=t
        path.lineTo(pos(y0*(1-e)+y1*e,z0+(z1-z0)*t))
    path.lineTo(pos(yf1,z1))
    for k in range(23,-1,-1):
        t=k/24.;e=t
        path.lineTo(pos(yf0*(1-e)+yf1*e,z0+(z1-z0)*t))
    path.closeSubpath()
    # Draw the existing attachment landings, not the former side plates.
    for ys,z,direction in ((mount['tabs_y'],z0,1),(mount['top_tabs_y'],z1,-1)):
        for y in ys:
            rad=p.CameraTPUScrewBore/2+p.CameraTPUBossWall
            bottom=z if direction>0 else z-p.CameraTPUInsertDepth-1
            boss=QtGui.QPainterPath()
            boss.addRoundedRect(QtCore.QRectF(y-cy-rad,bottom-zbase,2*rad,p.CameraTPUInsertDepth+1),min(.6,rad/3),min(.6,rad/3))
            path=path.united(boss)
    # A captured insert is a through-wall cassette. Match the exact
    # side-specific Y/Z datum and cutter expansion used by the native builder.
    # Do not reuse the old carbon side-plate opening or leave this wall opaque.
    if p.FlexCameraMode=='Captured inserts':
        from .flex_preview import camera_interface_path
        from .flex import insert_rect
        from .tpu_isolation_layout import tpu_isolator_datum
        dat_y,dat_z=tpu_isolator_datum(p,mount)
        src_y,src_z,_,_=insert_rect(p)
        from .tpu_captured_layout import flush_outside
        extra=(p.FlexInsertLip+.08) if flush_outside(p) else 0.0
        from .cage_extensions import split_o4
        if split_o4(p):
            # Both separate O4 cassettes appear with their true tracks.
            opening=QtGui.QPainterPath()
            for y,z in mount['side_holes']:
                opening.addEllipse(pos(y,z),p.O4InsertDiameter/2+extra,
                                   p.O4InsertDiameter/2+extra)
            for arc in mount['side_arcs']:
                pts=[(arc['centre'][0]+arc['radius']*math.cos(math.radians(
                          arc['start']+(arc['end']-arc['start'])*i/24)),
                      arc['centre'][1]+arc['radius']*math.sin(math.radians(
                          arc['start']+(arc['end']-arc['start'])*i/24))) for i in range(25)]
                for a,b in zip(pts,pts[1:]):
                    opening=opening.united(capsule_path(
                        (a[0]-cy,a[1]-zbase),(b[0]-cy,b[1]-zbase),
                        p.O4InsertDiameter/2+extra))
        else:
            opening=camera_interface_path(p,p.FlexInsertWidth+2*extra,
                                          p.FlexInsertHeight+2*extra)
            shift=QtGui.QTransform()
            shift.translate(dat_y-src_y,dat_z-src_z)
            opening=shift.map(opening)
        # Qt path booleans are less reliable at actual millimetre sizes.
        large=QtGui.QTransform();large.scale(60,60)
        path=large.inverted()[0].map(large.map(path).subtracted(
            large.map(opening)))
    # The view is an OUTSIDE elevation of the TPU wall. Compression pads
    # sit on the inside face; captured inserts occupy the through-window
    # cut above. Camera fastener paths are included in all three modes.
    for y,z in mount['side_holes']:
        hole=QtGui.QPainterPath();r=p.CameraSideHoleDiameter/2
        hole.addEllipse(pos(y,z),r,r);path=path.subtracted(hole)
    for arc in mount['side_arcs']:
        pts=[(arc['centre'][0]-cy+arc['radius']*math.cos(math.radians(arc['start']+(arc['end']-arc['start'])*i/24)),arc['centre'][1]-zbase+arc['radius']*math.sin(math.radians(arc['start']+(arc['end']-arc['start'])*i/24))) for i in range(25)]
        for a,b in zip(pts,pts[1:]):path=path.subtracted(capsule_path(a,b,arc['width']/2))
    return path
