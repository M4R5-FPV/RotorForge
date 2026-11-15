"""TPU cage mounting datums, independent of camera type and isolation method.

The finished carbon-plate outline decides where M3 holes can be drilled.
Camera and insert dimensions may alter ONLY the inside surface of the TPU wall.
No CAD or Qt imports: used by both the editor and the solid builder.
"""
from .parameter_memo import parameter_cache


def _carbon_edge_radius(p):
    return (3.0 + float(p.CameraTPUScrewClearance))/2.0 + 2.0


def _socket_radius(p):
    return float(p.CameraTPUScrewBore)/2.0 + float(p.CameraTPUBossWall) + .2


@parameter_cache(maxsize=128)
def mounting_x(p):
    """Signed right-side M3 datum, fixed by the two carbon plate widths.

    Give the *complete* mounting boss a small lateral landing inside the
    nominal side edge. This coordinate deliberately never uses CameraWidth,
    CameraSideClearance, FlexCameraMode or any side plate dimensions.
    The actual shaped carbon outline is checked separately at each hole.
    """
    edge=min(float(p.BodyWidth), float(p.TopWidth))/2.0
    x=edge-max(_carbon_edge_radius(p), _socket_radius(p)+.55)
    if x <= 0:
        raise ValueError('Carbon plate too narrow to support the TPU cage M3 fasteners.')
    return x


def mounting_y(p, role, width, bounds):
    """Return rear/front fasteners supported by the finished plate outline.

    Search both screw positions as a pair, and keep them independent of cage
    reach, camera width, isolation and TPU material thickness.
    """
    from .plate_profiles import profiled_interior_distance
    x=mounting_x(p)
    rear,front=bounds
    margin=_carbon_edge_radius(p)
    separation=max(3.0+float(p.CameraTPUScrewClearance)+2.15,
                   2*_socket_radius(p)+1.0)
    def supported(y):
        return profiled_interior_distance((x,y),p,role,width,rear,front,p.CornerRadius)>=margin-1.e-6
    # Start at the front, step rearward until BOTH fastening holes fit.
    n=max(0,int((front-rear-separation)/.2))+1
    for i in range(n):
        y=front-i*.2
        if supported(y) and supported(y-separation):
            return (y-separation,y)
    raise ValueError('%s has no room for two M3 TPU cage mounts with 2 mm carbon edge material. '
                     'Increase the plate support area or reduce the mounting boss diameter.' % role)


def fit_check(p):
    """Check the achievable structural side-wall section, not a 2-D socket shadow.

    The M3 inserts are at the lower and upper carbon plate contacts. The
    camera occupies the space between those contacts, often without reaching
    either set of sockets. Comparing their X footprints as if they occupied
    the same Z plane rejected otherwise feasible designs (e.g. 11.60 mm
    required versus 9.20 mm to the mounting socket).

    Retain an honest width check for the actual side wall. Its inner surface
    may move to accommodate the chosen camera, while its outer plate-derived
    edge and screw centre must remain fixed. Exact camera-to-cage BRep
    interference and the individual socket pockets are checked by the solid
    builder, where their real Y/Z extents are available.
    """
    from .flex import camera_inner
    x=mounting_x(p)
    outer=x+_socket_radius(p)+.35
    inner=camera_inner(p)
    # This is the true lateral bound for a continuous cage wall in the
    # camera region; the socket cannot be projected down its entire height.
    min_wall=1.2
    available=outer-min_wall
    if inner>available+1.e-6:
        return ('TPU cage camera clearance needs %.2f mm from the centre, '
                'but the plate-following outer wall allows only %.2f mm '
                'while retaining %.1f mm of TPU. Increase plate width or '
                'reduce camera side clearance.' % (inner,available,min_wall))
    return None


def carbon_rim_centres(p,role):
    """Exact M3 screw centres and required outer carbon radius for the TPU cage.

    These are independent of arm-bolt stock and are NOT the decorative TPU
    socket radius.  Evaluate them in CAD, Qt and fillet protection consistently.
    """
    if role not in ('BottomPlate','TopPlate') or not p.FPVEnabled:
        return ()
    from .camera_cages import screw_cage
    if not screw_cage(p):
        return ()
    from .fpv import camera_mounts
    x=mounting_x(p)
    mount=camera_mounts(p)[0]
    ys=mount['tabs_y' if role=='BottomPlate' else 'top_tabs_y']
    r=_carbon_edge_radius(p)
    return tuple(((sign*x,y),r) for sign in (-1,1) for y in ys)
