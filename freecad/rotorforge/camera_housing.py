"""Non-DJI FPV camera geometry, shared by camera fit and detailed references.

The camera is centred on X=0, Y=0, Z=0; +Y is the lens/front.  All
published dimensions are independent of the illustrative housing shape.
Foxeer T-Rex Mini uses its 22 x 22 mm case face,
6.3 mm vertical screw pitch and 7.7 mm rear-to-screw inset.  The ~14 mm
housing-only depth is an estimate from the drawing, NOT a vendor tolerance.
Caddx Ratel Pro uses a 19 x 19 mm casing, 15 mm lens and a SINGLE M2 screw
on each side. Its approximately 14.2 mm housing length and 9 mm screw
inset are estimates from the image, not manufacturer-toleranced CAD dimensions.
"""
import math


def screw_line_y(depth, rear_inset=0.0):
    """Y of camera-side threaded holes; 0 rear inset means legacy centre."""
    return -depth/2 + rear_inset if rear_inset > 0 else 0.0


def lens_dimensions(width, height, digital=False, projection_override=0., profile=None):
    """Approximate physical lens envelope consistent with selected camera.

    Non-published diameters are scaled conservatively, not fake measurements.
    Only Foxeer T-Rex Mini and Caddx Ratel Pro have diameter cues in drawings.
    """
    from .camera_profiles import get_camera_spec
    spec=get_camera_spec(profile)
    short=min(width,height)
    if profile == 'Foxeer T-Rex Mini':
        radius=min(7.5,short*.36)
    elif profile == 'Caddx Ratel Pro':
        radius=min(7.5,short*.40)
    elif short<=16:
        radius=short*(.315 if digital else .32)
    else:
        radius=min(7.4 if digital else 7.0,short*(.36 if digital else .33))
    default=spec.lens_projection if spec else min(6.3 if digital else 6., max(3.6,short*.29))
    return radius,(projection_override if projection_override>0 else default)


def _ease(t):
    t = max(0.,min(1.,t))
    return t*t*(3. - 2.*t)


def body_side_outline(height, depth, digital=False, profile=None):
    """Y,Z outline: shallow rear cap, long sloped roof/chin, small lens face.

    Unlike a cuboid or a 2 mm chamfer, commercial FPV micro housings have
    a large swept transition from the back shell to the front lens mount.
    The contour is sampled with near-tangent smoothstep curves, which avoids
    fragile B-spline dependencies in OCC boolean intersections.
    """
    hh=height/2.;rear=-depth/2.;front=depth/2.
    rear_bevel=min(.75,depth*.055,hh*.075)
    # Front is substantially shorter vertically than the back of the case.
    if profile == 'Caddx Ratel Pro':
        # Short 19-mm rear alloy cube, pronounced but lens-supporting tapered
        # forward shoulders, based on the user's Caddx Ratel Pro side drawing.
        # Avoid chopping into the M2 screw land (near the forward shoulder).
        front_h=max(hh*.80, min(hh*.85, 7.7))
        start=rear+depth*.44
    elif profile in ('Walksnail Avatar HD Pro','HDZero Micro V3','Walksnail Avatar HD Nano V3','HDZero Nano V3'):
        front_h=hh*.80
        start=rear+depth*.40
    elif profile in ('RunCam Phoenix 2','Caddx Ratel 2','Foxeer Predator 5 Nano','Foxeer Razer Nano'):
        front_h=hh*.83
        start=rear+depth*.42
    else:
        front_h=hh*(.73 if profile=='Foxeer T-Rex Mini' else (.79 if digital else .76))
        start=rear+depth*.26
    edge=[]
    edge.extend([(rear,-hh+rear_bevel),(rear,-hh+rear_bevel*.25),
                 (rear+rear_bevel,-hh),(start,-hh)])
    for i in range(1,10):
        t=i/9.;edge.append((start+(front-start)*t,-hh+(hh-front_h)*_ease(t)))
    edge.append((front,front_h))
    for i in range(8,-1,-1):
        t=i/9.;edge.append((start+(front-start)*t,hh-(hh-front_h)*_ease(t)))
    edge.extend([(rear+rear_bevel,hh),(rear,hh-rear_bevel),(rear,-hh+rear_bevel)])
    return tuple(edge[:-1])


def body_top_outline(width,depth,digital=False,profile=None, screw_y=0.):
    """Y,X footprint: full side-screw land, then narrow into optical nose."""
    hw=width/2.;rear=-depth/2.;front=depth/2.
    # Hold full width through the rear-mounted M2 threads, so inserts are
    # genuinely seated on the physical side wall, not free in space.
    start=max(rear+depth*.28,min(front-depth*.12,screw_y+min(1.45,depth*.12)))
    nose=(max(hw*.81,min(hw*.85,7.7)) if profile=='Caddx Ratel Pro' else
          hw*(.82 if profile=='Foxeer T-Rex Mini' else (.84 if digital else .86)))
    side=[(rear,-hw+min(.65,hw*.08)),(rear+min(.65,hw*.08),-hw),(start,-hw)]
    for i in range(1,10):
        t=i/9.;side.append((start+(front-start)*t,-hw+(hw-nose)*_ease(t)))
    side.append((front,nose))
    for i in range(8,-1,-1):
        t=i/9.;side.append((start+(front-start)*t,hw-(hw-nose)*_ease(t)))
    side.extend([(rear+min(.65,hw*.08),hw),(rear,hw-min(.65,hw*.08))])
    return tuple(side)


def body_front_outline(width,height,digital=False):
    """Rounded 22/19/14 mm face in X,Z, suitable for reliable booleans."""
    hw=width/2.;hh=height/2.
    r=min(width*.15,height*.15,3.0 if digital else 2.7)
    # CCW rounded rectangle; four arcs, six segments each.
    corners=((hw-r,hh-r,0,90),(-hw+r,hh-r,90,180),
             (-hw+r,-hh+r,180,270),(hw-r,-hh+r,270,360))
    return tuple((cx+r*math.cos(math.radians(a+(b-a)*i/6)),
                  cz+r*math.sin(math.radians(a+(b-a)*i/6)))
                 for cx,cz,a,b in corners for i in range(7))


def housing_shape(width,depth,height,digital=False,profile=None,rear_inset=0.):
    """Full 3-D rounded, tapered shell; not a rear cuboid plus a lens tube.

    Three intersected orthogonal prisms enforce the published camera face,
    the swept side silhouette and the side-screw landing silhouette.
    Each is a single solid, and there is no visual geometry in this BRep.
    """
    import FreeCAD as App,Part
    side=body_side_outline(height,depth,digital,profile)
    top=body_top_outline(width,depth,digital,profile,screw_line_y(depth,rear_inset))
    face=body_front_outline(width,height,digital)
    def closed(v):return Part.makePolygon(v+[v[0]])
    face_wire=closed([App.Vector(x,-depth/2.,z) for x,z in face])
    side_wire=closed([App.Vector(-width/2.,y,z) for y,z in side])
    top_wire=closed([App.Vector(x,y,-height/2.) for y,x in top])
    a=Part.Face(face_wire).extrude(App.Vector(0,depth,0))
    b=Part.Face(side_wire).extrude(App.Vector(width,0,0))
    c=Part.Face(top_wire).extrude(App.Vector(0,0,height))
    shaped=a.common(b).common(c)
    if shaped.isNull() or not shaped.isValid() or len(shaped.Solids)!=1:
        raise ValueError('Camera dimensions could not create a valid tapered FPV housing.')
    return shaped
