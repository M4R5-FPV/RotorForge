"""Optional four-screw TPU base with an action-camera three-finger hinge.

The fastener positions are taken from the SAME top cage mounting datums as
TopPlate and the cage's four M3 insert sockets. No new carbon-plate holes,
independent screw spacing or camera-specific dimensions are introduced.

Only the pure layout is evaluated by the editor. The BRep is created during
Create frame / Update frame / manufacturing export.
"""
from math import sqrt, cos, sin, pi


def upper_cage_screw_lift(p):
    """Extra screw-head height for the four upper cage M3 fasteners.

    Their X/Y coordinates and final insertion depth into the existing heat-set
    inserts do not change when the removable action-camera base is fitted.
    """
    if p.FPVEnabled and p.CameraCageStyle == 'TPU cage' and p.ActionCamMountEnabled:
        return float(p.ActionCamMountBaseThickness)
    return 0.0

def mount_layout(p):
    """Portable dimensions in frame XYZ, or None if the feature is inactive."""
    if not (p.FPVEnabled and p.CameraCageStyle == 'TPU cage' and p.ActionCamMountEnabled):
        return None
    from .fpv import camera_mounts
    from .tpu_mount_layout import mounting_x
    from .parameters import plate_levels

    mounts = camera_mounts(p)
    if len(mounts) != 2 or mounts[0]['top_tabs_y'] != mounts[1]['top_tabs_y']:
        raise ValueError('The four top TPU cage screw datums could not be matched.')
    x = mounting_x(p)
    rear_y, front_y = sorted(mounts[0]['top_tabs_y'])
    # Standard GoPro-style pivot: 3 x 3 mm TPU fingers, 2 x 3.4 mm gaps.
    # The ribs must not cover the four screw heads/through-bores.
    fin_width = 3.0
    fin_centres = (-6.4, 0.0, 6.4)
    screw_radius = 1.65  # M3 free-fitting hole, 3.3 mm diameter
    edge_web = 1.5
    if x - (max(abs(v) for v in fin_centres)+fin_width/2) < screw_radius+edge_web-1e-7:
        raise ValueError('The top plate is too narrow for both the four M3 cage screws and '
                         'the standard three-finger action-camera interface. Widen the top plate.')
    hinge_y = (rear_y + front_y)/2 + float(p.ActionCamMountOffsetY)
    halfwidth = x + screw_radius + 3.0
    rear = min(rear_y-screw_radius-3.0, hinge_y-10.0-1.0)
    front = max(front_y+screw_radius+3.0, hinge_y+10.0+1.0)
    z = plate_levels(p)['top_z'] + float(p.TopThickness)
    base_thickness = upper_cage_screw_lift(p)
    # The nut is installed axially from the outside of the positive-X finger.
    # ISO 4032 M5: 8 mm across flats, up to 4.7 mm thick. The allowance
    # here is 0.15 mm per flat and 0.2 mm in depth; test fit printed TPU.
    nut = None
    if p.ActionCamMountNutRecess:
        outer_x = fin_centres[-1] + fin_width/2
        nut = dict(start_x=outer_x, end_x=outer_x+5.9,
                   across_flats=8.3, depth=4.9, radius=6.5)
    return dict(nut=nut,box=(-halfwidth,halfwidth,rear,front),
                corner_radius=3.5,
                screws=tuple((sx*x, y) for sx in (-1,1) for y in (rear_y,front_y)),
                top_z=z,
                base_thickness=base_thickness,
                hinge_y=hinge_y,
                hinge_z=z+base_thickness+float(p.ActionCamMountHingeHeight),
                fin_centres=fin_centres,fin_width=fin_width,
                hinge_bore_radius=2.6,  # 5.2 mm clearance for an M5 action-cam bolt
                crown_radius=7.0)


def _rounded_plate(Part, App, d):
    """One exact arc-based footprint, avoiding a 3D vertical-edge fillet."""
    x0,x1,y0,y1 = d['box']
    z=d['top_z'];r=min(d['corner_radius'],(x1-x0)/3,(y1-y0)/3)
    vec=lambda x,y:App.Vector(x,y,z)
    k=1-1/sqrt(2)
    # Travel counter-clockwise from the bottom straight, using genuine arcs.
    pts=((x0+r,y0),(x1-r,y0),(x1,y0+r),(x1,y1-r),
         (x1-r,y1),(x0+r,y1),(x0,y1-r),(x0,y0+r))
    edges=[]
    for i in range(8):
        a=vec(*pts[i]);b=vec(*pts[(i+1)%8])
        if i==1: mid=vec(x1-r*k,y0+r*k)
        elif i==3:mid=vec(x1-r*k,y1-r*k)
        elif i==5:mid=vec(x0+r*k,y1-r*k)
        elif i==7:mid=vec(x0+r*k,y0+r*k)
        else:mid=None
        edges.append(Part.Arc(a,mid,b).toShape() if mid else Part.makeLine(a,b))
    face=Part.Face(Part.Wire(edges))
    return face.extrude(App.Vector(0,0,d['base_thickness']))


def _hinge_finger(Part,App,d,xcenter):
    """One rising, crowned fin. The transverse bolt passes through all 3."""
    x=xcenter-d['fin_width']/2
    y=d['hinge_y'];z=d['top_z']+d['base_thickness']
    pivot_z=d['hinge_z'];radius=d['crown_radius']
    def v(yy,zz):return App.Vector(x,yy,zz)
    back=v(y-10,z);front=v(y+10,z)
    crown_back=v(y-radius,pivot_z)
    crown_front=v(y+radius,pivot_z)
    tip=v(y,pivot_z+radius)
    edges=[Part.makeLine(back,front),
           Part.makeLine(front,crown_front),
           Part.Arc(crown_front,tip,crown_back).toShape(),
           Part.makeLine(crown_back,back)]
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(d['fin_width'],0,0))


def make_action_camera_mount(p,inputs):
    """Exact separate printable TPU part. Never modifies the carbon/cage solids."""
    import FreeCAD as App
    import Part
    d=mount_layout(p)
    if d is None:return Part.Shape()
    # Document the real carrier dependency to component cache. The screw
    # positions remain fully dictated by the cage layout, not this BRep.
    carrier=inputs.get('TopPlate')
    if carrier is None or carrier.isNull():
        raise ValueError('HD action-camera mount requires the finished top carbon plate.')
    base=_rounded_plate(Part,App,d)
    screw_tools=[Part.makeCylinder(1.65,d['base_thickness']+2,
                   App.Vector(x,y,d['top_z']-1)) for x,y in d['screws']]
    base=base.cut(Part.makeCompound(screw_tools))
    fins=[_hinge_finger(Part,App,d,x) for x in d['fin_centres']]
    # A tiny intentional overlap (0.02 mm) is not needed: each fin has a broad
    # co-planar footprint on the base, allowing OCC to fuse shared faces.
    shape=base.multiFuse(fins).removeSplitter()
    from .screw_heads import apply_countersinks
    shape=apply_countersinks(shape,p,'ActionCameraMount')
    nut=d['nut']
    y,z=d['hinge_y'],d['hinge_z']
    axis=App.Vector(1,0,0)
    if nut:
        # Cylindrical boss overlaps the original outer fin; it never expands
        # inward into the two camera fingers' mating gaps.
        start=nut['start_x']-0.25
        boss=Part.makeCylinder(nut['radius'],nut['end_x']-start,
                               App.Vector(start,y,z),axis)
        shape=shape.fuse(boss).removeSplitter()
        # Blind hex pocket, open to the outside. Keep a solid shoulder behind
        # it, so tightening the bolt does not load a thin unsupported rim.
        x=nut['end_x']-nut['depth']
        r=nut['across_flats']/sqrt(3)
        points=[App.Vector(x,y+r*cos(i*pi/3),z+r*sin(i*pi/3)) for i in range(6)]
        pocket=Part.Face(Part.makePolygon(points+[points[0]])).extrude(
            App.Vector(nut['depth']+0.5,0,0))
        shape=shape.cut(pocket)
    # Extend the through-bore beyond the nut boss when present.
    axle_end=max(12.0,nut['end_x']+1.0) if nut else 12.0
    axle=Part.makeCylinder(d['hinge_bore_radius'],axle_end+12,
                App.Vector(-12,y,z),axis)
    shape=shape.cut(axle).removeSplitter()
    if shape.isNull() or len(shape.Solids)!=1 or not shape.isValid():
        raise ValueError('HD action-camera mount could not produce one valid TPU solid. '
                         'Check the cage width, top screw positions and hinge offset.')
    return shape
