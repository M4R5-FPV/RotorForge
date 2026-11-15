"""TPU-only camera isolation datums; keeps rigid cage and M3 plate mounts fixed."""
import math

def screw_envelope(mount):
    """Return actual Y/Z bounds swept by camera fasteners (including variable tilt arcs)."""
    pts=list(mount['side_holes'])
    for arc in mount['side_arcs']:
        a0,a1=arc['start'],arc['end']
        angles=[a0,a1]+[float(k*90) for k in range(math.floor(a0/90),math.ceil(a1/90)+1) if a0<k*90<a1]
        cy,cz=arc['centre'];radius=arc['radius']
        pts.extend((cy+radius*math.cos(math.radians(a)),cz+radius*math.sin(math.radians(a))) for a in angles)
    if not pts:return None
    return min(y for y,z in pts),max(y for y,z in pts),min(z for y,z in pts),max(z for y,z in pts)

def tpu_isolator_datum(p,mount):
    """Centre the insert/pad on its camera screw envelope, not on the cage wall.

    Only this removable isolation part uses this datum. The structural TPU
    perimeter and M3 heat-set insert locations are never translated here.
    """
    from .flex import insert_rect
    cy,cz,_,_=insert_rect(p)
    bounds=screw_envelope(mount)
    if bounds is None:return (cy,cz)
    return ((bounds[0]+bounds[1])/2,(bounds[2]+bounds[3])/2)

def isolator_required_dimensions(p,mount):
    """Minimum soft insert dimensions enclosing every screw/slot with material."""
    b=screw_envelope(mount)
    if b is None:return (0.,0.)
    margin=p.CameraSideHoleDiameter/2+max(.8,p.MinimumWeb)
    return (b[1]-b[0]+2*margin,b[3]-b[2]+2*margin)


# These standalone TPU-only camera interfaces are NOT copies of the carbon
# cheek profile or the outer cage. The cutter, removable insert and editor
# preview must all use these exact normalized points.
TPU_INTERFACE_SHAPES = ('Rounded rectangle', 'Chamfered rectangle', 'Hexagon',
                        'Octagon', 'Tapered rectangle', 'Capsule')
CARBON_INTERFACE_SHAPES = ('Rounded rectangle', 'Side plate outline')

def tpu_interface_polygon(p,width,height):
    """YZ outline for TPU interface shapes other than rounded rectangle.

    Coordinates share the camera-interface datum from insert_rect; no side
    plate geometry, mounting offset, or plate reach enters this calculation.
    Polygon winding is consistent for cutting and constructing inserts.
    """
    from .flex import insert_rect
    cy,cz,_,_=insert_rect(p)
    shape=getattr(p,'FlexInterfaceShape','Rounded rectangle')
    hw=width/2.; hh=height/2.
    if hw<=0 or hh<=0:
        raise ValueError('TPU camera interface dimensions must be positive.')
    if shape=='Chamfered rectangle':
        c=min(hw,hh)*.27
        pts=[(-hw+c,-hh),(hw-c,-hh),(hw,-hh+c),(hw,hh-c),
             (hw-c,hh),(-hw+c,hh),(-hw,hh-c),(-hw,-hh+c)]
    elif shape=='Hexagon':
        pts=[(-hw*.55,-hh),(hw*.55,-hh),(hw,0),
             (hw*.55,hh),(-hw*.55,hh),(-hw,0)]
    elif shape=='Octagon':
        c=min(hw,hh)*.52
        pts=[(-hw+c,-hh),(hw-c,-hh),(hw,-hh+c),(hw,hh-c),
             (hw-c,hh),(-hw+c,hh),(-hw,hh-c),(-hw,-hh+c)]
    elif shape=='Tapered rectangle':
        pts=[(-hw,-hh),(hw,-hh),(hw*.82,hh),(-hw*.82,hh)]
    elif shape=='Capsule':
        # Rounded top/bottom ends, represented identically in previews and
        # native solids. 32 vertices keep it printable without spline offset.
        import math
        pts=[(hw*math.cos(2*math.pi*i/32),hh*math.sin(2*math.pi*i/32))
             for i in range(32)]
    else:
        raise ValueError(f'No TPU polygon is defined for interface shape {shape!r}.')
    return tuple((cy+y,cz+z) for y,z in pts)


def compression_pad_x_span(p,mount,sign):
    """Real uncompressed contact and seated back plane of a TPU soft pad.

    The full-height rigid cage surface remains at the hard-mount datum.
    The pad extends from (camera face - intended preload) INTO a pocket in
    that wall. Its axial thickness is always the configured pad thickness;
    otherwise moving the cage inward would quietly squash the pad to 0.3 mm.
    """
    if sign not in (-1,1):
        raise ValueError('TPU camera side must be left or right.')
    camera_face=float(p.CameraWidth)*.5
    contact=camera_face-float(p.FlexPadPreload)
    back=contact+float(p.FlexPadThickness)
    inner=min(abs(v) for v in mount['plate_x'])
    outer=max(abs(v) for v in mount['plate_x'])
    if contact<=0 or back<=inner+.05:
        raise ValueError('TPU soft pad needs a positive seat inside the cage wall.')
    # A retained wall is essential for both the screw and the floor bridge.
    if back>outer-1.2+1.e-6:
        raise ValueError('TPU compression pad needs %.2f mm of wall depth but only %.2f mm is available; reduce pad thickness or increase outer plate width.' % (back-inner,max(0.,outer-inner-1.2)))
    a,b=sign*contact,sign*back
    return (min(a,b),max(a,b))
