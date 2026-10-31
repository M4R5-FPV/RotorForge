"""Cut airflow patterns only after checking existing boundaries and fasteners."""
import math
import FreeCAD as App
import Part
from .cutouts import cutouts_for, cutout_polygon
from .fpv import CAMERA_ROLES, camera_mounts, camera_position_y, camera_wall_interior
from .parameters import plate_holes, standoff_layouts, arm_layouts, keystone_retainers


def profile_tool(pattern, z, height):
    from .geometry import cylinder, capsule, rounded_plate
    w,l=pattern['width'],pattern['length']
    if pattern['shape']=='Circle':
        shape=cylinder(0,0,w/2,z,height)
    elif pattern['shape']=='Ellipse':
        if abs(w-l)<1e-9:shape=cylinder(0,0,w/2,z,height)
        else:
            edge=Part.Ellipse(App.Vector(0,0,z),max(w,l)/2,min(w,l)/2).toShape()
            shape=Part.Face(Part.Wire([edge])).extrude(App.Vector(0,0,height))
            if l>w:shape.rotate(App.Vector(),App.Vector(0,0,1),90)
    elif pattern['shape']=='Slot':
        if l>=w: a,b,r=(0,-(l-w)/2),(0,(l-w)/2),w/2
        else: a,b,r=(-(w-l)/2,0),((w-l)/2,0),l/2
        shape=capsule(a,b,r,z,height)
    elif pattern['shape']=='Rounded rectangle':
        shape=rounded_plate(w,l,min(w,l)/4,z,height)
    else:
        points=[App.Vector(x,y,z) for x,y in cutout_polygon(pattern)]
        shape=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,height))
    shape.rotate(App.Vector(),App.Vector(0,0,1),pattern['rotation'])
    shape.translate(App.Vector(pattern['x'],pattern['y'],0))
    return shape


def fastener_keepouts(p, role, z, thickness):
    from .geometry import cylinder
    holes=[]
    if role in ('BottomPlate','MidPlate','TopPlate','ArmClampPlate','ArmLowerClampPlate'):
        holes=[(pt,max(radius,3. if name in ('arm root','stack') else radius))
               for pt,radius,name in plate_holes(p,role)]
        for s in standoff_layouts(p):
            carrier={'Bottom plate':'BottomPlate','Mid plate':'MidPlate','Arm clamp plate':'ArmClampPlate','Arm top':None}[s['mount']]
            if role=='TopPlate' or role==carrier:
                holes.append((s['point'],p.StandoffDiameter/2))
    elif role.startswith('Arm') and role not in ('ArmKeystone','ArmClampPlate','ArmLowerClampPlate'):
        arm=next(a for a in arm_layouts(p) if 'Arm'+a['name']==role)
        holes=[(pt,max(3,p.RootHoleDiameter/2)) for pt in arm['bolts']]
        holes += [(pt,max(3,p.MotorHoleDiameter/2)) for pt in arm['motor_holes']]
    if role in ('ArmKeystone','ArmClampPlate','BottomPlate'):
        holes += [(r['point'],max(r['head_diameter']/2,r['bore'])) for r in keystone_retainers(p)]
    return [cylinder(*pt,r,z-1,thickness+2) for pt,r in holes]


def apply_cutouts(p, role, shape):
    patterns=cutouts_for(p,role)
    if not patterns:
        return shape
    camera=role in CAMERA_ROLES
    bounds=shape.BoundBox
    z=bounds.XMin if camera else bounds.ZMin
    thickness=bounds.XLength if camera else bounds.ZLength
    keepouts=fastener_keepouts(p,role,z,thickness) if not camera else []
    tools=[]
    edges=Part.makeCompound(shape.Edges)
    # Interior wires include service holes, strap slots and camera tab sockets.
    # Keep these protected when the outside boundary is intentionally opened.
    inner=[]
    for face in shape.Faces:
        if face.BoundBox.ZLength<1e-7:
            for wire in face.Wires:
                if not wire.isSame(face.OuterWire):inner.extend(wire.Edges)
    inner_edges=Part.makeCompound(inner) if inner else None
    for index,pattern in enumerate(patterns,1):
        # Shared cap planes preserve analytic ellipse edges through booleans;
        # protruding an elliptic extrusion can produce approximated splines.
        tool=profile_tool(pattern,z if not camera else 0,thickness)
        if camera:
            # Local U = Y offset from camera pivot; V = Z above bottom top.
            tool.rotate(App.Vector(),App.Vector(1,1,1),120)
            tool.translate(App.Vector(z,camera_position_y(p),p.BottomThickness))
            mount=next(m for m in camera_mounts(p) if m['role']==role)
            b=tool.BoundBox
            if min(camera_wall_interior((y,zz),mount) for y in (b.YMin,b.YMax) for zz in (b.ZMin,b.ZMax))<p.MinimumWeb-1e-6:
                raise ValueError(f'{role} airflow cutout {index} is too close to the side-wall edge or captured tabs.')
        # Test the actual outside material instead of subtracting integrated
        # volumes, whose numeric error is noticeable on elliptical surfaces.
        outline=pattern['mode']=='Outline notch'
        if outline:
            if tool.common(shape).Volume<1e-6 or tool.cut(shape).Volume<1e-6:
                raise ValueError(f'{role} outline notch {index} must cross the outside edge; move it onto an edge.')
            if inner_edges is not None and inner_edges.distToShape(tool)[0]<p.MinimumWeb-1e-6:
                raise ValueError(f'{role} outline notch {index} is too close to an existing hole or slot.')
        if not outline and tool.cut(shape).Volume>1e-6:
            raise ValueError(f'{role} airflow cutout {index} crosses an existing edge, hole or slot; move or resize it.')
        if (not outline and edges.distToShape(tool)[0]<p.MinimumWeb-1e-6) or any(k.distToShape(tool)[0]<p.MinimumWeb-1e-6 for k in keepouts):
            raise ValueError(f'{role} airflow cutout {index} leaves less than {p.MinimumWeb:g} mm at a boundary or fastener footprint.')
        tools.append(tool)
    # Union overlapping openings before cutting. Existing holes/edges above
    # remain protected, while a new cutout is free to cross another new one.
    groups=[]
    for tool in tools:
        joined=[];separate=[]
        for group in groups:
            if tool.BoundBox.intersect(group.BoundBox) and tool.common(group).Volume>1e-8:joined.append(group)
            else:separate.append(group)
        if joined:tool=tool.multiFuse(joined).removeSplitter()
        groups=separate+[tool]
    for i,first in enumerate(groups):
        if any(first.distToShape(other)[0]<p.MinimumWeb-1e-6 for other in groups[i+1:]):
            raise ValueError(f'{role}: separate airflow openings need at least {p.MinimumWeb:g} mm of material between them. Overlap them to merge; touching edges alone are insufficient.')
    result=shape.cut(Part.makeCompound(groups)).removeSplitter()
    if not result.isValid() or len(result.Solids)!=1:
        raise ValueError(f'{role}: the combined cutouts disconnect the plate; reduce them or move them.')
    return result
