"""DJI O4 Air Unit Pro camera: shared physical envelope and display parameters.

DJI O4 Air Unit Series user manual (2025), dimension sheet page 6.
Camera module: 25.55 mm fore/aft overall, 20 mm wide, 23.30 mm tall.
Two M2 camera-side threads per side, 16.0 mm vertical pitch, MAX 2.0 mm
thread depth. The side thread line is 16 mm from the housing rear (DJI dimension drawing,
separate from the 16 mm vertical screw pitch). The shoulder radii are
photo-derived approximations rather than manufacturer CAD. The smooth body and lens details
are reference interpretations of photographs, not certified production CAD.
"""
import math

WIDTH=20.0
HEIGHT=23.3
CASE_DEPTH=19.45
LENS_PROTRUSION=6.10
SIDE_SCREW_PITCH=16.0
SIDE_SCREW_DIAMETER=2.0
SIDE_SCREW_REAR_INSET=16.0
SIDE_SCREW_Y=-CASE_DEPTH/2+SIDE_SCREW_REAR_INSET
SIDE_SCREW_Z=0.0
CASE_CORNER_RELIEF=1.0  # legacy marker for compatibility

# Local +Y is lens-front. Every section fits within DJI's stated 20 x 23.3
# case envelope. Broad rear M2 lands are followed by smooth front shoulders.
# Section sizes/radii are photo-derived approximations, not DJI dimensions.
CASE_STATIONS=(
    (-CASE_DEPTH/2, 18.6,22.2,2.3),
    (-8.95,           19.5,22.9,2.5),
    (-7.75,           WIDTH,HEIGHT,2.8),
    (-2.35,           WIDTH,HEIGHT,2.8),
    (1.25,            WIDTH,23.15,3.0),
    (5.3,             WIDTH,21.5,3.5),
    (8.15,            WIDTH,20.25,4.0),
    (CASE_DEPTH/2,    WIDTH,20.0,4.4),
)

def side_screw_points():
    return ((SIDE_SCREW_Y,SIDE_SCREW_Z-SIDE_SCREW_PITCH/2),
            (SIDE_SCREW_Y,SIDE_SCREW_Z+SIDE_SCREW_PITCH/2))

def casing_side_outline():
    """Conservative Y,Z side silhouette of the loft for tilt-extents checks."""
    top=[(y,h/2) for y,w,h,r in CASE_STATIONS]
    low=[(y,-h/2) for y,w,h,r in reversed(CASE_STATIONS)]
    return tuple(top+low)

def _rounded_xz_section(y,width,height,r,steps=7):
    """Matched closed polygon wires for FreeCAD/OCC through-sections loft.

    Planar section is symmetric in X,Z; every loft section uses exactly
    the same number of vertices, so corners align through all stations.
    """
    import FreeCAD as App,Part
    x=width/2.;z=height/2.;r=min(r,x-.05,z-.05)
    outline=[]
    for cx,cz,start in ((x-r,z-r,0),(-x+r,z-r,90),(-x+r,-z+r,180),(x-r,-z+r,270)):
        # Corner order: right-top => left-top => left-bottom => right-bottom.
        # Right/top corner angles 0..90; left/top 90..180, etc.
        for k in range(steps):
            angle=math.radians(start+90*k/(steps-1))
            outline.append(App.Vector(cx+r*math.cos(angle),y,cz+r*math.sin(angle)))
    return Part.makePolygon(outline+[outline[0]])

def casing_solid():
    """Unified, softly shouldered, bounded DJI camera casing BRep.

    This is *also* used by the exact camera collision probe so the physical
    body is no longer a broad cuboid when detailed reference is enabled.
    Side hole coordinates remain fixed and unaffected by the display detail.
    """
    import FreeCAD as App,Part
    sections=[_rounded_xz_section(*station) for station in CASE_STATIONS]
    shape=Part.makeLoft(sections,True,False)
    # OCC's interpolating loft can overshoot the control sections by a few
    # hundredths; bound this presentation/collision solid to exact DJI dims.
    nominal=Part.makeBox(WIDTH,CASE_DEPTH,HEIGHT,
                         App.Vector(-WIDTH/2,-CASE_DEPTH/2,-HEIGHT/2))
    shape=shape.common(nominal)
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1:
        raise ValueError('Could not form the DJI O4 Pro camera housing loft')
    return shape
