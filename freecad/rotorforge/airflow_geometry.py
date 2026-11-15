"""Build through-vent and shallow-pocket machining with depth-aware clearance checks."""
import math
import FreeCAD as App
import Part
from .cutouts import cutouts_for, cutout_polygon, CNC_POLYGON_TYPES, cutout_profile_segments
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
    elif pattern['shape'] in CNC_POLYGON_TYPES:
        edges=[]
        for segment in cutout_profile_segments(pattern):
            if segment[0]=='line':
                edges.append(Part.makeLine(App.Vector(*segment[1],z),App.Vector(*segment[2],z)))
            else:
                edges.append(Part.Arc(App.Vector(*segment[1],z),App.Vector(*segment[2],z),App.Vector(*segment[3],z)).toShape())
        shape=Part.Face(Part.Wire(edges)).extrude(App.Vector(0,0,height))
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


def _xy_boxes_within_margin(first,second,margin):
    """Conservative planar bounding-box reject before expensive OCC distance."""
    a,b=first.BoundBox,second.BoundBox
    dx=max(a.XMin-b.XMax,b.XMin-a.XMax,0.)
    dy=max(a.YMin-b.YMax,b.YMin-a.YMax,0.)
    return dx*dx+dy*dy < margin*margin


def _edge_clearance_too_small(edges, probe, web):
    """Same exact OCC distance check, but only for possibly near edges.

    A 3-D distance smaller than `web` necessarily requires the projected XY
    bounding boxes to be less than `web` apart. The XY broad phase is therefore
    conservative; distant perimeter and mounting edges never need OCC distance
    calculations, even for large automatically generated airflow patterns.
    """
    nearby = [edge for edge in edges
              if _xy_boxes_within_margin(edge, probe, web)]
    if not nearby:
        return False
    source = nearby[0] if len(nearby) == 1 else Part.makeCompound(nearby)
    return source.distToShape(probe)[0] < web - 1e-6


def _boxes_overlap_in_volume(a, b):
    """Cheap, conservative OCC broad-phase before a solid/solid intersection.

    A zero-volume touch cannot contribute to the full-volume union check.
    All shape coordinates use the original CAD geometry, with no tolerance
    enlargement and no modification of the acceptance criteria.
    """
    return (a.XMin < b.XMax and b.XMin < a.XMax and
            a.YMin < b.YMax and b.YMin < a.YMax and
            a.ZMin < b.ZMax and b.ZMin < a.ZMax)


def apply_cutouts(p, role, shape, *, patterns=None):
    # Explicit instances enable separate through-machining / blind-machining
    # passes without paying for a second JSON parse and grid expansion.
    if patterns is None:
        patterns=cutouts_for(p,role)
    if not patterns:
        return shape
    camera=role in CAMERA_ROLES
    if camera and p.CameraCageStyle!='Carbon side plates' and any(item['mode']=='Pocket' for item in patterns):
        raise ValueError(role+': blind CNC pockets are only available for carbon side plates, not TPU camera cages.')
    bounds=shape.BoundBox
    z=bounds.XMin if camera else bounds.ZMin
    thickness=bounds.XLength if camera else bounds.ZLength
    additions=[t for t in patterns if t['mode']=='Add material']
    if additions:
        protected=[]
        for face in shape.Faces:
            if face.BoundBox.ZLength<1e-7:
                for wire in face.Wires:
                    if not wire.isSame(face.OuterWire):
                        pocket=Part.Face(wire).extrude(App.Vector(0,0,thickness+2))
                        pocket.translate(App.Vector(0,0,z-1-face.BoundBox.ZMin));protected.append(pocket)
        for index,pattern in enumerate(additions,1):
            tool=profile_tool(pattern,z,thickness)
            if tool.common(shape).Volume<1e-6 or tool.cut(shape).Volume<1e-6:
                raise ValueError(f'{role} addition {index} must overlap material and extend beyond the outside edge.')
            overlap=tool.common(shape)
            inset=Part.Face(max((f for f in overlap.Faces if f.BoundBox.ZLength<1e-7),key=lambda f:f.Area).OuterWire)
            try: core=inset.makeOffset2D(-p.MinimumWeb/2,join=0)
            except Exception: core=Part.Shape()
            if core.isNull() or not core.Faces or core.Area<1e-6:
                raise ValueError(f'{role} addition {index} needs at least Minimum web of overlap with the plate.')
            if protected:tool=tool.cut(Part.makeCompound(protected))
            shape=shape.fuse(tool).removeSplitter()
            if not shape.isValid() or len(shape.Solids)!=1:raise ValueError(f'{role}: material addition must remain one connected solid.')
        patterns=[t for t in patterns if t['mode']!='Add material']
        if not patterns:return shape
    tools=[]
    # Shallow pockets are surface machining, not through-holes: they may run
    # off the plate perimeter or meet existing holes/slots/through-cuts.
    # Only through operations require the full-depth edge/fastener keepouts.
    through_patterns=any(item['mode']!='Pocket' for item in patterns)
    keepouts=(fastener_keepouts(p,role,z,thickness)
              if through_patterns and not camera else ())
    boundary_edges=tuple(shape.Edges) if through_patterns else ()
    inner=[]
    if any(item['mode']=='Outline notch' for item in patterns):
        for face in shape.Faces:
            if face.BoundBox.ZLength<1e-7:
                for wire in face.Wires:
                    if not wire.isSame(face.OuterWire):inner.extend(wire.Edges)
    for index,pattern in enumerate(patterns,1):
        web=max(p.MinimumWeb,pattern.get('auto_web',0.))
        pocket=pattern['mode']=='Pocket'
        if pocket and pattern['depth']>thickness/2+1e-7:
            raise ValueError(f'{role} pocket {index}: depth {pattern["depth"]:g} mm exceeds half the carbon thickness ({thickness/2:g} mm).')
        # A full-depth footprint probe is still used for through-cut checks
        # and grouping. A shallow pocket uses its true shallow cutter for
        # machining and is allowed to intersect existing edges and openings.
        probe=profile_tool(pattern,z if not camera else 0,thickness)
        if camera:
            probe.rotate(App.Vector(),App.Vector(1,1,1),120)
            probe.translate(App.Vector(z,camera_position_y(p),p.BottomThickness))
            mount=next(m for m in camera_mounts(p) if m['role']==role)
            b=probe.BoundBox
            if not pocket and min(camera_wall_interior((y,zz),mount) for y in (b.YMin,b.YMax) for zz in (b.ZMin,b.ZMax))<web-1e-6:
                raise ValueError(f'{role} airflow cutout {index} is too close to the side-wall edge or captured tabs.')
        outline=pattern['mode']=='Outline notch'
        if outline:
            if probe.common(shape).Volume<1e-6 or probe.cut(shape).Volume<1e-6:
                raise ValueError(f'{role} outline notch {index} must cross the outside edge; move it onto an edge.')
            if inner and _edge_clearance_too_small(inner,probe,web):
                raise ValueError(f'{role} outline notch {index} is too close to an existing hole or slot.')
        if not outline and not pocket and probe.cut(shape).Volume>1e-6:
            raise ValueError(f'{role} airflow cutout {index} crosses an existing edge, hole or slot; move or resize it.')
        if not pocket and ((not outline and _edge_clearance_too_small(boundary_edges,probe,web))
                or any(k.distToShape(probe)[0]<web-1e-6
                       for k in keepouts if _xy_boxes_within_margin(k,probe,web))):
            raise ValueError(f'{role} airflow cutout {index} leaves less than {web:g} mm at a boundary or fastener footprint.')
        if pocket:
            depth=pattern['depth']
            if camera:
                # X = carbon plate thickness; the outer face of each camera
                # side plate is on opposite sides of the X axis.
                x0=bounds.XMin-.02 if role=='CameraMountLeft' else bounds.XMax-depth
                # The left-side start offset must be balanced: it must not
                # travel 0.02 mm deeper into the plate than requested.
                cutter_height=(depth+.02 if role=='CameraMountLeft' else depth+.04)
                cutter=profile_tool(pattern,0,cutter_height)
                cutter.rotate(App.Vector(),App.Vector(1,1,1),120)
                cutter.translate(App.Vector(x0,camera_position_y(p),p.BottomThickness))
            else:
                cutter=profile_tool(pattern,bounds.ZMax-depth,depth+.04)
            # A pocket may overhang the outline or connect to an existing
            # hole, but must actually remove material somewhere on the part.
            # Reject misplaced pockets instead of reporting a successful no-op.
            if not _boxes_overlap_in_volume(cutter.BoundBox,shape.BoundBox) or cutter.common(shape).Volume<=1e-7:
                raise ValueError(f'{role} pocket {index} misses the plate material; move it onto the part.')
        else:cutter=probe
        tools.append((probe,cutter,pattern['mode'],pattern['depth'] if pocket else 0,web))
    # Unite only overlapping identical operations. Pocket cutters can cross
    # through holes, edge notches, or other pockets (including differing
    # depths). Keep those operations separate in 3-D, where the deepest cut
    # wins naturally. Do not merge pockets into full-depth cutters.
    groups=[]
    for probe,cutter,mode,depth,web in tools:
        joined=[];separate=[]
        for group in groups:
            other,other_cutter,other_mode,other_depth,other_web=group
            # Differently machined surfaces may overlap. In particular an
            # open-ended cable channel must cross a through-hole/edge notch.
            # Avoid an expensive OCC intersection for different pocket cuts.
            if (mode=='Pocket' or other_mode=='Pocket') and (mode!=other_mode or abs(depth-other_depth)>1e-7):
                separate.append(group)
                continue
            intersect=(_boxes_overlap_in_volume(probe.BoundBox,other.BoundBox)
                       and probe.common(other).Volume>1e-8)
            if intersect and mode!=other_mode:
                raise ValueError(f'{role}: overlapping through-cut modes require compatible operations.')
            if intersect:joined.append(group)
            else:separate.append(group)
        if joined:
            probe=probe.multiFuse([g[0] for g in joined]).removeSplitter()
            cutter=cutter.multiFuse([g[1] for g in joined]).removeSplitter()
            web=max([web]+[g[4] for g in joined])
        groups=separate+[(probe,cutter,mode,depth,web)]
    for i,(first,_,first_mode,_,first_web) in enumerate(groups):
        if first_mode=='Pocket':
            continue  # A half-depth channel leaves the supporting lower skin.
        for other,_,other_mode,_,other_web in groups[i+1:]:
            if other_mode=='Pocket':
                continue
            web=max(first_web,other_web)
            if _xy_boxes_within_margin(first,other,web) and first.distToShape(other)[0]<web-1e-6:
                raise ValueError(f'{role}: separate through-openings need at least {web:g} mm of carbon between them.')
    result=shape.cut(Part.makeCompound([cutter for _,cutter,_,_,_ in groups])).removeSplitter()
    if not result.isValid() or len(result.Solids)!=1:
        raise ValueError(f'{role}: the combined cuts disconnect the plate; reduce them or move them.')
    return result
