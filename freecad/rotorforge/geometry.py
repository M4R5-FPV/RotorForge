"""Exact OpenCASCADE solids built with FreeCAD's bundled Part module."""
from functools import lru_cache
from itertools import combinations
import math
import FreeCAD as App
import Part
from .flex_options import FLEX_ROLES
from .flex import flex_roles

from .parameters import (Parameters, arm_layouts, motor_centres, require_valid,
                         stack_holes, standoff_holes, strap_slots, three_plate,
                         bottom_bounds, bottom_body_bounds, bottom_tabs, top_bounds, mid_bounds, mid_tabs, plate_levels, standoff_layouts,
                         arm_braces, upper_clamp_active, arm_brace_layouts, arms_above_bottom, bottom_stack_hole_diameter,
                         stack_reference_z, point_segment_distance, plate_holes, keystone_active, keystone_retainers, underside_clamp_active, underside_clamp_layout)
from .fpv import (CAMERA_ROLES, camera_mounts, camera_slots, camera_pivot_height,
                  camera_angles, camera_body_centre, vtx_holes, vtx_deck_z)
from .motor_pads import motor_pad_primitives, motor_tip_slots, motor_pad_unit
from .stack_reliefs import stack_escape_segment
from .plate_profiles import plate_base_polygon, centre_polygon, polygon_interior_distance
from .arm_roots import (fitted_roots, root_cell_polygon, compact_key_outline, compact_key_centre,
                        nearest_polygon_point, beam_profile_polygon, widened_roots, stem_stations, arm_local_point, stem_interior_distance)

MAIN_CARBON_ROLES = ("BottomPlate", "MidPlate", "TopPlate", "ArmFrontRight", "ArmFrontLeft", "ArmRearLeft", "ArmRearRight")
ARM_LOCK_ROLES = ('ArmKeystone','ArmClampPlate','ArmLowerClampPlate')
LEGACY_ARM_ROLES = ('FrontArmBrace','RearArmBrace')
CARBON_ROLES = MAIN_CARBON_ROLES+CAMERA_ROLES+ARM_LOCK_ROLES
PHYSICAL_ROLES = CARBON_ROLES + ("Standoffs", "LiPoPad")+FLEX_ROLES
REFERENCE_ROLES = ("PropellerDiscs", "MotorEnvelopes", "StackEnvelope", "CameraEnvelope", "VTXEnvelope", "BatteryEnvelope", "FrameCGMarker")
ALL_ROLES = PHYSICAL_ROLES + REFERENCE_ROLES


def carbon_roles(p):
    main=MAIN_CARBON_ROLES if three_plate(p) else tuple(role for role in MAIN_CARBON_ROLES if role != "MidPlate")
    locks=(('ArmKeystone',) if keystone_active(p) else ())+ (('ArmClampPlate',) if upper_clamp_active(p) else ())+ (('ArmLowerClampPlate',) if underside_clamp_active(p) else ())
    return main+(CAMERA_ROLES if p.FPVEnabled else ())+locks


def physical_roles(p):
    return carbon_roles(p) + ("Standoffs",) + (("LiPoPad",) if p.LiPoPadEnabled else ())+flex_roles(p)


def flat_plate_shape(shape,role,p=None):
    flat=shape.copy()
    if p is not None and role=='ArmClampPlate' and keystone_retainers(p):
        # Flat DXF/SVG are through-cut profiles. Countersinks are separate
        # machining operations; the physical STEP/native solid retains them.
        for item,cone in keystone_countersinks(p):
            x,y=item['point'];bore=cylinder(x,y,item['bore']/2,cone.BoundBox.ZMin-1,cone.BoundBox.ZLength+2)
            flat=flat.fuse(cone.cut(bore)).removeSplitter()
    if p is not None:
        from .nut_geometry import restore_pockets
        flat=restore_pockets(flat,p,role)
    if role in CAMERA_ROLES:
        # YZ camera plates become XY cutting profiles; X thickness becomes Z.
        flat.rotate(App.Vector(),App.Vector(1,1,1),-120)
    return flat


def normalise_role(role):
    return "MidPlate" if role == "ClampPlate" else role


def overlap_volume(a,b):
    """Avoid expensive exact intersections when bounding boxes cannot overlap in volume."""
    if a.isNull() or b.isNull():return 0.
    aa,bb=a.BoundBox,b.BoundBox
    if any(min(getattr(aa,k+'Max'),getattr(bb,k+'Max'))-max(getattr(aa,k+'Min'),getattr(bb,k+'Min'))<=0 for k in ('X','Y','Z')):return 0.
    from .dependency_cache import cached_overlap
    return cached_overlap(a,b)


def cylinder(x, y, radius, z, height):
    return Part.makeCylinder(radius, height, App.Vector(x, y, z))


def polygon_plate(points, z, thickness):
    vertices=[App.Vector(x,y,z) for x,y in points]
    return Part.Face(Part.makePolygon(vertices+[vertices[0]])).extrude(App.Vector(0,0,thickness))


def fuse(shapes):
    if len(shapes) == 1:
        return shapes[0]
    return shapes[0].multiFuse(shapes[1:]).removeSplitter()


def capsule(a, b, radius, z, height):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = (dx * dx + dy * dy) ** 0.5
    if length < 1e-8:
        return cylinder(*a, radius, z, height)
    nx, ny = -dy * radius / length, dx * radius / length
    points = [App.Vector(a[0] + nx, a[1] + ny, z), App.Vector(b[0] + nx, b[1] + ny, z),
              App.Vector(b[0] - nx, b[1] - ny, z), App.Vector(a[0] - nx, a[1] - ny, z)]
    middle = Part.Face(Part.makePolygon(points + [points[0]])).extrude(App.Vector(0, 0, height))
    return fuse([middle, cylinder(*a, radius, z, height), cylinder(*b, radius, z, height)])


def _straight_arm_stem(p, arm, z, height, clearance=0.):
    """A constant beam with an independently widened, tapered root."""
    if not widened_roots(p):
        return capsule(arm['start'],arm.get('beam_end',arm['motor']),p.ArmWidth/2+clearance,z,height)
    start, reach, end, motor, rr, rb = stem_stations(p, arm)
    def point(t,s):
        return App.Vector(*arm_local_point(arm,t,s),z)
    points = [(start,rr),(reach,rr),(end,rb),(motor,rb),
              (motor,-rb),(end,-rb),(reach,-rr),(start,-rr)]
    edges = [Part.makeLine(point(*points[i]),point(*points[i+1])) for i in (0,1,2)]
    edges.append(Part.Arc(point(motor,rb),point(motor+rb,0),point(motor,-rb)).toShape())
    edges.extend(Part.makeLine(point(*points[i]),point(*points[i+1])) for i in (4,5,6))
    edges.append(Part.Arc(point(start,-rr),point(start-rr,0),point(start,rr)).toShape())
    face = Part.Face(Part.Wire(edges))
    if clearance:
        face = face.makeOffset2D(clearance,join=0)
    return face.extrude(App.Vector(0,0,height))


def arm_stem(p,arm,z,height,clearance=0.):
    shape=_straight_arm_stem(p,arm,z,height,clearance)
    outline=beam_profile_polygon(p,arm)
    if outline:
        points=[App.Vector(x,y,z) for x,y in outline]
        face=Part.Face(Part.makePolygon(points+[points[0]]))
        if clearance:face=face.makeOffset2D(clearance,join=0)
        shape=fuse([shape,face.extrude(App.Vector(0,0,height))])
    if p.MotorPadRotationPivot=='Pad beginning':
        shape=fuse([shape,capsule(arm['beam_end'],arm['motor'],p.ArmWidth/2+clearance,z,height)])
    return shape


def rounded_plate(width, length, radius, z, thickness, centre_y=0.0):
    shapes = [Part.makeBox(width - 2 * radius, length, thickness, App.Vector(-width / 2 + radius, -length / 2, z)),
              Part.makeBox(width, length - 2 * radius, thickness, App.Vector(-width / 2, -length / 2 + radius, z))]
    shapes.extend(cylinder(x, y, radius, z, thickness)
                  for x in (-width / 2 + radius, width / 2 - radius)
                  for y in (-length / 2 + radius, length / 2 - radius))
    shape = fuse(shapes)
    if centre_y:
        shape.translate(App.Vector(0, centre_y, 0))
    return shape


def profiled_plate(p,role,width,rear,front,radius,z,thickness,wide_override=None,trim_ends=True):
    outline=plate_base_polygon(p,role,width,rear,front,radius)
    base=polygon_plate(outline,z,thickness) if outline else rounded_plate(width,front-rear,radius,z,thickness,(rear+front)/2)
    polygon=centre_polygon(p,role,width,rear,front,wide_override)
    if polygon:
        points=[App.Vector(x,y,z) for x,y in polygon]
        extra=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,thickness))
        base=base.fuse(extra).removeSplitter()
    from .bottom_nose import edge_commands
    for end in ('Front','Rear') if trim_ends else ():
        commands=edge_commands(p,role,end,width,rear,front)
        if not commands:continue
        edges=[];current=None
        for item in commands:
            if item[0]=='M':current=App.Vector(*item[1],z)
            elif item[0]=='L':
                end=App.Vector(*item[1],z)
                if (end-current).Length>1e-8:edges.append(Part.makeLine(current,end))
                current=end
            else:
                curve=Part.BezierCurve();curve.setPoles([current]+[App.Vector(*pt,z) for pt in item[1:]])
                edges.append(curve.toShape());current=App.Vector(*item[-1],z)
        mask=Part.Face(Part.Wire(edges)).extrude(App.Vector(0,0,thickness))
        base=base.common(mask).removeSplitter()
    return base


def keystone_countersinks(p):
    if not keystone_retainers(p):return ()
    clamp=arm_brace_layouts(p)[0];top=clamp['z']+clamp['thickness']
    return tuple((item,Part.makeCone(item['bore']/2,item['head_diameter']/2,item['countersink_depth'],
                                   App.Vector(*item['point'],top-item['countersink_depth'])))
                 for item in keystone_retainers(p))


def trim_arm_root(p,arm,arms,blank,z,height):
    """Shared outer joint and key cuts for arms and mid clamping tabs."""
    if fitted_roots(p):
        blank=blank.common(polygon_plate(root_cell_polygon(p,arm,arms),z-1,height+2)).removeSplitter()
        if keystone_active(p):
            blank=blank.cut(polygon_plate(compact_key_outline(p,arms,True),z-1,height+2)).removeSplitter()
    return blank


def mid_tab_shapes(p,z,height,arms=None):
    arms=arm_layouts(p) if arms is None else arms
    boundary=profiled_plate(p,'BottomPlate',p.BodyWidth,*bottom_bounds(p),p.CornerRadius,z,height)
    result=[]
    for arm,(a,b,radius) in zip((a for a in arms if a['root'][1]>0),mid_tabs(p)):
        root=trim_arm_root(p,arm,arms,arm_stem(p,arm,z,height),z,height)
        result.append(capsule(a,b,radius,z,height).common(root).common(boundary).removeSplitter())
    return tuple(result)


def mid_plate_blank(p,z,height,arms=None):
    main=profiled_plate(p,'MidPlate',p.BodyWidth,*mid_bounds(p),p.CornerRadius,z,height)
    return fuse([main]+[tab for tab in mid_tab_shapes(p,z,height,arms) if not tab.isNull() and tab.Volume>1e-8])


def bottom_tab_shapes(p,z,height,arms=None):
    if not three_plate(p):return ()
    arms=arm_layouts(p) if arms is None else arms
    boundary=profiled_plate(p,'BottomPlate',p.BodyWidth,*bottom_bounds(p),p.CornerRadius,z,height)
    upper=profiled_plate(p,'MidPlate',p.BodyWidth,*mid_bounds(p),p.CornerRadius,z,height)
    tabs=[]
    for arm,(a,b,radius) in zip((a for a in arms if a['root'][1]<0),bottom_tabs(p)):
        root=trim_arm_root(p,arm,arms,arm_stem(p,arm,z,height),z,height)
        tabs.append(capsule(a,b,radius,z,height).common(root).common(boundary).common(upper).removeSplitter())
    return tuple(tabs)


def bottom_plate_blank(p,z,height,arms=None):
    main=profiled_plate(p,'BottomPlate',p.BodyWidth,*bottom_body_bounds(p),p.CornerRadius,z,height)
    return fuse([main]+[tab for tab in bottom_tab_shapes(p,z,height,arms) if not tab.isNull() and tab.Volume>1e-8])


def clamp_plate_blank(p,role,z,height):
    from .arm_roots import root_width
    from .clamp_outline import clamp_outline_layout
    c=arm_brace_layouts(p)[0];rear,front,pads=clamp_outline_layout(p);arms=arm_layouts(p)
    boundary=profiled_plate(p,role,c['width'],c['rear'],c['front'],c['radius'],z,height)
    pieces=[profiled_plate(p,role,c['width'],rear,front,c['radius'],z,height)]
    for arm in arms:
        root=trim_arm_root(p,arm,arms,arm_stem(p,arm,z,height),z,height)
        pieces.append(capsule(*arm['bolts'],root_width(p)/2,z,height).common(root))
    pieces.extend(capsule(a,b,r,z,height) for a,b,r in pads)
    return fuse([shape for shape in pieces if not shape.isNull() and shape.Volume>1e-8]).common(boundary).removeSplitter()


def cut_holes(shape, holes, z, thickness, other_tools=()):
    unique=[]
    for point,radius in holes:
        if not any(math.dist(point,q)<=1e-6 and abs(radius-r)<=1e-6 for q,r in unique):
            unique.append((point,radius))
    tools = [cylinder(x, y, radius, z - 1, thickness + 2) for (x, y), radius in unique]
    tools.extend(other_tools)
    return shape.cut(Part.makeCompound(tools)).removeSplitter() if tools else shape


def camera_bracket(p, mount):
    xmin,xmax=mount['plate_x']
    points=[App.Vector(xmin,y,z) for y,z in mount['wall_profile']]
    wall=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(xmax-xmin,0,0))
    tabs=[]
    for y in mount['tabs_y']:
        tabs.append(Part.makeBox(xmax-xmin,p.CameraTabLength,p.BottomThickness,
                                App.Vector(xmin,y-p.CameraTabLength/2,0)))
    for y in mount['top_tabs_y']:
        tabs.append(Part.makeBox(xmax-xmin,p.CameraTabLength,p.TopThickness,
                                App.Vector(xmin,y-p.CameraTabLength/2,mount['z1'])))
    blank=fuse([wall]+tabs)
    from .fpv import camera_tab_reliefs
    reliefs=[Part.makeCylinder(r,xmax-xmin+2,App.Vector(xmin-1,y,z),App.Vector(1,0,0))
             for y,z,r in camera_tab_reliefs(p,mount)]
    if reliefs:blank=blank.cut(Part.makeCompound(reliefs)).removeSplitter()
    if p.FlexCameraMode=='Captured inserts':
        from .flex_geometry import camera_window
        return blank.cut(camera_window(p,xmin-1,xmax-xmin+2)).removeSplitter()
    side_tools=[Part.makeCylinder(p.CameraSideHoleDiameter/2,xmax-xmin+2,
                                  App.Vector(xmin-1,y,z),App.Vector(1,0,0)) for y,z in mount['side_holes']]
    for arc in mount['side_arcs']:
        tool=arc_slot(arc,xmin-1,xmax-xmin+2)
        side_tools.append(tool)
    boundaries=Part.makeCompound(blank.Edges)
    if any(boundaries.distToShape(tool)[0]<p.MinimumWeb-1e-6 for tool in side_tools):
        raise ValueError('Camera holes or adjustment slots need more edge material; centre the camera or enlarge the side plate.')
    for i,tool in enumerate(side_tools):
        if any(tool.distToShape(other)[0]<p.MinimumWeb-1e-6 for other in side_tools[i+1:]):
            raise ValueError('Camera holes or slots leave insufficient material between them; increase measured screw spacing or reduce the tilt range.')
    return blank.cut(Part.makeCompound(side_tools)).removeSplitter()


def arc_slot(arc, x, thickness):
    """Exact circular adjustment slot with semicircular ends (DXF arcs)."""
    cy,cz=arc['centre'];r=arc['radius'];w=arc['width']/2
    lo,hi=map(math.radians,(arc['start'],arc['end']))
    def pt(radius,a):return App.Vector(x,cy+radius*math.cos(a),cz+radius*math.sin(a))
    outer0,outer1=pt(r+w,lo),pt(r+w,hi)
    inner0,inner1=pt(r-w,lo),pt(r-w,hi)
    endmid=App.Vector(x,cy+r*math.cos(hi)-w*math.sin(hi),cz+r*math.sin(hi)+w*math.cos(hi))
    startmid=App.Vector(x,cy+r*math.cos(lo)+w*math.sin(lo),cz+r*math.sin(lo)-w*math.cos(lo))
    edges=[Part.Arc(outer0,pt(r+w,(lo+hi)/2),outer1).toShape(),Part.Arc(outer1,endmid,inner1).toShape(),
           Part.Arc(inner1,pt(r-w,(lo+hi)/2),inner0).toShape(),Part.Arc(inner0,startmid,outer0).toShape()]
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(thickness,0,0))


def camera_envelope(p, tilt=None):
    body=Part.makeBox(p.CameraWidth,p.CameraBodyDepth,p.CameraHeight,
                      App.Vector(-p.CameraWidth/2,-p.CameraBodyDepth/2,-p.CameraHeight/2))
    lens=Part.makeCylinder(min(6,p.CameraWidth*.35,p.CameraHeight*.35),6.1,
                           App.Vector(0,p.CameraBodyDepth/2-.1,0),App.Vector(0,1,0))
    camera=fuse([body,lens])
    camera.rotate(App.Vector(),App.Vector(1,0,0),p.CameraTilt if tilt is None else tilt)
    centre=camera_body_centre(p,tilt)
    camera.translate(App.Vector(0,*centre))
    return camera


def fpv_envelopes(p, tilt=None):
    camera=camera_envelope(p,tilt)
    z=vtx_deck_z(p)
    vtx=Part.makeBox(p.VTXWidth,p.VTXLength,p.VTXHeight,
                     App.Vector(-p.VTXWidth/2,p.VTXOffsetY-p.VTXLength/2,z))
    vtx=cut_holes(vtx,[(pt,r) for pt,r,_ in vtx_holes(p)],z,p.VTXHeight)
    return camera,vtx


def motor_pad(p, arm, z):
    shapes=[];cuts=[]
    for d in motor_pad_primitives(p):
        if d['kind']=='circle':
            shape=cylinder(*d['centre'],d['radius'],z,p.ArmThickness)
        elif d['kind']=='rounded':
            shape=rounded_plate(d['width'],d['width'],d['radius'],z,p.ArmThickness)
        else:
            points=[App.Vector(x,y,z) for x,y in d['points']]
            shape=Part.Face(Part.makePolygon(points+[points[0]])).extrude(App.Vector(0,0,p.ArmThickness))
        (cuts if d.get('operation')=='cut' else shapes).append(shape)
    shape=fuse(shapes)
    if cuts:shape=shape.cut(Part.makeCompound(cuts)).removeSplitter()
    ux,uy=motor_pad_unit(p,arm)
    shape.rotate(App.Vector(),App.Vector(0,0,1),math.degrees(math.atan2(uy,ux)))
    shape.translate(App.Vector(*arm['motor'],0))
    return shape


@lru_cache(maxsize=5)
def _build(signature):
    import time
    from .dependency_cache import COMPONENTS
    p=Parameters(*signature);require_valid(p);started=time.perf_counter()
    from . import disk_cache
    restored=disk_cache.restore(signature,COMPONENTS);COMPONENTS.begin()
    result={};arms=arm_layouts(p);levels=plate_levels(p);arm_z=levels['arm_z']
    for role in CARBON_ROLES:
        if role=='ArmKeystone':continue
        q=_canonical_component_parameters(p,role)
        result[role]=COMPONENTS.get(role,q,{},lambda t,i,r=role:_component_carbon(t,r,i))
    role='ArmKeystone';q=_canonical_component_parameters(p,role)
    result[role]=COMPONENTS.get(role,q,result,lambda t,i:_component_carbon(t,'ArmKeystone',i))
    for role in LEGACY_ARM_ROLES:result[role]=Part.Shape()
    result['Standoffs']=COMPONENTS.get('Standoffs',p,{},lambda t,i:_component_standoffs(t,'Standoffs',i))
    carbon=dict(result)
    for role in FLEX_ROLES:
        result[role]=COMPONENTS.get(role,p,result if role=='FrontBumper' else carbon,lambda t,i,r=role:_component_flex(t,r,i))
    for role in flex_roles(p):
        for other in physical_roles(p):
            if other!=role and overlap_volume(result[role],result.get(other,Part.Shape()))>1e-6:
                raise ValueError(role+' intersects '+other+'; adjust flexible-part dimensions or placement.')
    from .battery import make_pad,mounting_role,battery_envelope
    result['LiPoPad']=COMPONENTS.get('LiPoPad',p,result,lambda t,i:make_pad(t,i[mounting_role(t)]) if t.LiPoPadEnabled else Part.Shape())
    if p.FPVEnabled and p.FlexCameraMode=='Captured inserts':
        from .flex_geometry import camera_window,round_window,interface_blank
        from .flex import insert_rect
        cy,cz,w,h=insert_rect(p)
        for mount in camera_mounts(p):
            x0,x1=mount['plate_x']
            bearing=interface_blank(p,x0,x1-x0,w,h,p.FlexInsertLip).cut(camera_window(p,x0-1,x1-x0+2))
            if abs(bearing.common(result[mount['role']]).Volume-bearing.Volume)>1e-5:
                raise ValueError('A camera side-plate cut removes captured-insert flange support; move the cut or enlarge the side plate.')
    if three_plate(p) or arm_braces(p):
        from .parameters import stack_mounting_role
        carrier=stack_mounting_role(p)
        z=result[carrier].BoundBox.ZMin;low=min(result[r].BoundBox.ZMin for r in carbon_roles(p))
        for point in stack_holes(p):
            passage=cylinder(*point,p.StackAccessDiameter/2,low-.1,z-low+.1)
            for role in carbon_roles(p):
                if role!=carrier and result[role].common(passage).Volume>1e-6:
                    raise ValueError('Stack screw access is blocked by '+role+'; enable arm-root reliefs or change the mounting positions.')
    for role in carbon_roles(p):
        shape = result[role]
        if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
            raise ValueError(f"{role} did not produce one valid solid. Adjust the dimensions.")
    if p.LiPoPadEnabled:
        for role in physical_roles(p):
            if role not in ('LiPoPad',mounting_role(p)) and result['LiPoPad'].common(result[role]).Volume>1e-6:
                raise ValueError('LiPo pad intersects '+role+'; move/resize it or choose the other battery mounting face.')
    if fitted_roots(p) or widened_roots(p) or p.ArmBeamShape!='Straight':
        for a,b in combinations(arms,2):
            first,second=result['Arm'+a['name']],result['Arm'+b['name']]
            if first.common(second).Volume>1e-6:
                raise ValueError('Arm roots overlap; select Fitted miters or move the roots apart.')
            if not fitted_roots(p) and first.distToShape(second)[0]<.25-1e-6:
                raise ValueError('Independent arm roots need at least 0.25 mm separation; select Fitted miters or move the roots apart.')
        for arm in arms:
            if result['Arm'+arm['name']].common(result['Standoffs']).Volume>1e-6:
                raise ValueError('An arm intersects a standoff; move the support or use an aligned arm-hole mount.')
    for role in ARM_LOCK_ROLES:
        if result[role].isNull():
            continue
        for other in physical_roles(p):
            if other!=role and overlap_volume(result[role],result[other])>1e-6:
                raise ValueError(role+' intersects '+other+'; adjust the arm or standoff mounting positions.')
    if p.FPVEnabled:
        for role in CAMERA_ROLES:
            if not result[role].isValid() or len(result[role].Solids)!=1:
                raise ValueError(role+' did not produce one connected camera side plate.')
            for other in physical_roles(p):
                if other!=role and overlap_volume(result[role],result[other])>1e-6:
                    raise ValueError(role+' intersects '+other+'; adjust the camera position, height, or bracket dimensions.')
        camera=COMPONENTS.get('_camera_probe',p,{},lambda q,i:camera_envelope(q))
        vtx=COMPONENTS.get('_vtx_probe',p,{},lambda q,i:_vtx_probe(q))
        for name,envelope in (('Camera',camera),('VTX',vtx)):
            for role in physical_roles(p):
                if name=='Camera' and role in FLEX_ROLES[:2]:continue
                if overlap_volume(envelope,result[role])>1e-6:
                    raise ValueError(name+' envelope intersects '+role+'; adjust its size, position, height, or tilt.')
        if p.CameraMountMode=='Variable':
            for angle in camera_angles(p):
                if abs(angle-p.CameraTilt)<1e-8:continue
                swept=COMPONENTS.get('_camera_sweep:'+str(angle),p,{},lambda q,i:camera_envelope(q,angle))
                for role in physical_roles(p):
                    if role in FLEX_ROLES[:2]:continue
                    b=result[role].BoundBox
                    if b.XMin>=p.CameraWidth/2 or b.XMax<=-p.CameraWidth/2:continue
                    if overlap_volume(swept,result[role])>1e-6:
                        raise ValueError(f'Camera at {angle:g}° intersects {role}; reduce the adjustment range or increase clearance.')
    stack=COMPONENTS.get('_stack_probe',p,{},lambda q,i:_stack_probe(q))
    if not three_plate(p) and arms_above_bottom(p) and not arm_braces(p):
        if any(stack.common(result['Arm'+a['name']]).Volume>1e-6 for a in arms):
            raise ValueError('The stack on the bottom intersects an arm. Set an explicit stack spacer height, use below-bottom arms, or add the combined clamp.')
    if flex_roles(p):
        probes=[('FC/ESC stack',stack)]
        if p.BatteryReferenceEnabled:probes.append(('LiPo reference',battery_envelope(p)))
        prop_low=p.PropReferenceHeight;prop_thickness=.25
        if p.DetailedPropReferences:
            from .detailed_references import prop_model
            bounds=prop_model(p.PropDiameter)[0].BoundBox
            prop_low=p.MotorReferenceHeight+bounds.ZMin;prop_thickness=bounds.ZLength
        for i,point in enumerate(motor_centres(p)):
            probes.append(('motor '+str(i+1),cylinder(*point,p.MotorReferenceDiameter/2,arm_z+p.ArmThickness,p.MotorReferenceHeight)))
            probes.append(('propeller '+str(i+1),cylinder(*point,p.PropDiameter/2,arm_z+p.ArmThickness+prop_low,prop_thickness)))
        for role in flex_roles(p):
            for name,probe in probes:
                if overlap_volume(result[role],probe)>1e-6:raise ValueError(role+' intersects '+name+'; adjust the module placement/size, antenna layout or reference dimensions.')

    for role in REFERENCE_ROLES:
        result[role]=COMPONENTS.get(role,p,result,lambda t,i,r=role:_component_reference(t,r,i))
    for role in ALL_ROLES:result.setdefault(role,Part.Shape())
    disk_cache.save(signature,COMPONENTS)
    report=dict(seconds=time.perf_counter()-started,disk_restored=restored,rebuilt=[e['role'] for e in COMPONENTS.events if e['action']=='rebuilt' and not e['role'].startswith('_')],reused=[e['role'] for e in COMPONENTS.events if e['action']=='reused' and not e['role'].startswith('_')],events=list(COMPONENTS.events))
    _BUILD_PAYLOADS[signature]={role:entry['payload'] for role in ALL_ROLES if (entry:=COMPONENTS.latest.get(role)) is not None}
    while len(_BUILD_PAYLOADS)>5:_BUILD_PAYLOADS.pop(next(iter(_BUILD_PAYLOADS)))
    _BUILD_MANIFESTS[signature]={role:COMPONENTS.manifest(role) for role in ALL_ROLES}
    while len(_BUILD_MANIFESTS)>8:_BUILD_MANIFESTS.pop(next(iter(_BUILD_MANIFESTS)))
    _BUILD_REPORTS[signature]=report
    while len(_BUILD_REPORTS)>8:_BUILD_REPORTS.pop(next(iter(_BUILD_REPORTS)))
    return result


# OpenCASCADE failures are deterministic for the same parameters. Retain a
# bounded message cache so every dependent feature does not retry the full
# failed model during one recompute. Explicit user build actions can retry.
_FAILED_BUILDS={}

def invalidate_failed_build(p):
    _FAILED_BUILDS.pop(_geometry_signature(p),None)

def _resolved_build(signature):
    if signature in _FAILED_BUILDS:raise ValueError(_FAILED_BUILDS[signature])
    try:
        result=_build(signature)
        for history in (_BUILD_REPORTS,_BUILD_MANIFESTS,_BUILD_PAYLOADS):
            if signature in history:history[signature]=history.pop(signature)
        return result
    except Exception as exc:
        if isinstance(exc,MemoryError):raise
        if len(_FAILED_BUILDS)>=8:_FAILED_BUILDS.pop(next(iter(_FAILED_BUILDS)))
        _FAILED_BUILDS[signature]=str(exc)
        raise

def build_shapes(p):
    """Return copies: transforms or exports must never mutate cached geometry."""
    require_valid(p)
    return {role: shape.copy() for role, shape in _resolved_build(_geometry_signature(p)).items()}


def build_for_update(p):
    import time
    before=_build.cache_info().hits;start=time.perf_counter();shapes=build_shapes(p)
    if _build.cache_info().hits>before:
        _BUILD_REPORTS[_geometry_signature(p)]=dict(seconds=time.perf_counter()-start,rebuilt=[],reused=[r for r in ALL_ROLES if r not in LEGACY_ARM_ROLES],events=[])
    return shapes


def build_shape(p,role):
    """Copy only the requested part during document recompute."""
    require_valid(p)
    return _resolved_build(_geometry_signature(p))[role].copy()


def blend_motor_junction(p,arm,blank,z,height):
    """Planar closing adds rolling-radius fillets at concave pad/beam joints."""
    r=p.MotorPadBlendRadius
    if r<=1e-8 or abs(p.MotorPadRotation)<1e-8:return blank
    faces=[f for f in blank.Faces if abs(f.normalAt(0,0).z-1)<1e-7]
    face=max(faces,key=lambda f:f.Area).copy()
    face.translate(App.Vector(0,0,z-face.CenterOfMass.z))
    try:
        closed=face.makeOffset2D(r,join=0).makeOffset2D(-r,join=0)
        # Restrict additions to the root-facing pad junction, leaving the nose intact.
        from .motor_pads import motor_pad_start
        ux,uy=arm['unit'];mx,my=arm.get('nominal_motor',arm['motor'])
        a=(mx+ux*(motor_pad_start(p)-p.ArmWidth),my+uy*(motor_pad_start(p)-p.ArmWidth))
        b=(mx+ux*p.ArmWidth,my+uy*p.ArmWidth)
        zone=capsule(a,b,p.MotorPadDiameter,z,height)
        addition=closed.extrude(App.Vector(0,0,height)).common(zone)
        result=fuse([blank,addition])
        if not result.isValid() or len(result.Solids)!=1:raise ValueError('invalid blended outline')
        return result
    except Exception as exc:
        raise ValueError('Cannot round this motor-pad junction. Reduce Rotated pad transition radius, or set it to zero.') from exc

def _component_bottom(p,role,inputs):
    result={}
    arms=arm_layouts(p)
    body_holes=[(pt,r) for pt,r,_ in plate_holes(p,'BottomPlate')]
    rear, front = bottom_bounds(p)
    camera_bottom_slots=[capsule(a,b,r,-1,p.BottomThickness+2) for a,b,r in camera_slots(p)]
    result["BottomPlate"] = cut_holes(bottom_plate_blank(p,0,p.BottomThickness,arms),
                                       body_holes, 0, p.BottomThickness,camera_bottom_slots)

    return result["BottomPlate"]

def _component_mid(p,role,inputs):
    if not three_plate(p):return Part.Shape()
    mid_z=p.BottomThickness+p.ArmThickness
    result={}
    arms=arm_layouts(p)
    if three_plate(p):
        blank = mid_plate_blank(p,mid_z,p.ClampThickness,arms)
        mid_holes = [(pt,r) for pt,r,_ in plate_holes(p,'MidPlate')]
        result["MidPlate"] = cut_holes(blank, mid_holes, mid_z, p.ClampThickness)
    else:
        result["MidPlate"] = Part.Shape()

    return result["MidPlate"]

def _component_top(p,role,inputs,include_strap_notches=True):
    levels=plate_levels(p)
    arm_z,mid_z,hardware_z,top_z=(levels[k] for k in ('arm_z','mid_z','deck_z','top_z'))
    result={}
    slots = [capsule(a, b, radius, top_z - 1, p.TopThickness + 2) for a, b, radius in strap_slots(p)+camera_slots(p,'TopPlate')]
    from .strap_openings import notch_polygons
    if include_strap_notches:
        slots += [polygon_plate(poly,top_z-1,p.TopThickness+2) for poly in notch_polygons(p)]
    top_rear,top_front=top_bounds(p)
    result["TopPlate"] = cut_holes(profiled_plate(p,'TopPlate',p.TopWidth,top_rear,top_front,p.CornerRadius,top_z,p.TopThickness),
                                    [(pt, p.StandoffHoleDiameter / 2) for pt in standoff_holes(p)],
                                    top_z, p.TopThickness, slots)

    return result["TopPlate"]

def _component_arm(p,role,inputs):
    arm_z=p.BottomThickness if arms_above_bottom(p) else -p.ArmThickness
    result={}
    arms=arm_layouts(p)
    arm=next(a for a in arms if 'Arm'+a['name']==role)
    blank = fuse([arm_stem(p,arm,arm_z,p.ArmThickness),
                  motor_pad(p,arm,arm_z)])
    blank=blend_motor_junction(p,arm,blank,arm_z,p.ArmThickness)
    blank=trim_arm_root(p,arm,arms,blank,arm_z,p.ArmThickness)
    holes = [(pt, p.RootHoleDiameter / 2) for pt in arm["bolts"]]
    holes += [(pt, p.MotorHoleDiameter / 2) for pt in arm["motor_holes"]]
    holes.append((arm["motor"], p.MotorCenterDiameter / 2))
    access=[]
    if p.ArmRootReliefsEnabled:
        box=blank.BoundBox
        for pt in stack_holes(p):
            tool=cylinder(*pt,p.StackAccessDiameter/2,arm_z-1,p.ArmThickness+2)
            if p.ArmRootReliefShape=='Slot toward stack centre':
                # Only open screw reliefs which actually intersect this
                # trimmed arm, never slots from a different arm's screws.
                if blank.common(tool).Volume<=1e-8:continue
                a,b,r=stack_escape_segment(p,pt,(box.XMin,box.YMin,box.XMax,box.YMax))
                tool=capsule(a,b,r,arm_z-1,p.ArmThickness+2)
            access.append(tool)
    access += [capsule(a,b,r,arm_z-1,p.ArmThickness+2) for a,b,r in motor_tip_slots(p,arm)]
    result["Arm" + arm["name"]] = cut_holes(blank, holes, arm_z, p.ArmThickness,access)
    for bolt in arm['bolts']:
        ring=cylinder(*bolt,p.RootHoleDiameter/2+p.MinimumWeb,arm_z,p.ArmThickness).cut(cylinder(*bolt,p.RootHoleDiameter/2,arm_z-1,p.ArmThickness+2))
        if abs(ring.common(result['Arm'+arm['name']]).Volume-ring.Volume)>1e-6:
            raise ValueError('An arm-root cut removes arm-bolt supporting material; change the root fit, key size, root position or stack pattern.')
    if fitted_roots(p):
        for point,radius in [(pt,p.MotorHoleDiameter/2) for pt in arm['motor_holes']]+[(arm['motor'],p.MotorCenterDiameter/2)]:
            ring=cylinder(*point,radius+p.MinimumWeb,arm_z,p.ArmThickness).cut(cylinder(*point,radius,arm_z-1,p.ArmThickness+2))
            if abs(ring.common(result['Arm'+arm['name']]).Volume-ring.Volume)>1e-6:
                raise ValueError('A fitted root cell cuts into motor-hole support; change the root layout.')

    return result[role]

def _component_clamp(p,role,inputs):
    if not upper_clamp_active(p):return Part.Shape()
    result={}
    for brace in arm_brace_layouts(p):
        blank=clamp_plate_blank(p,'ArmClampPlate',brace['z'],brace['thickness'])
        clamp_holes=[(pt,r) for pt,r,_ in plate_holes(p,'ArmClampPlate')]
        result[brace['role']]=cut_holes(blank,clamp_holes,brace['z'],brace['thickness'],[cone for _,cone in keystone_countersinks(p)])

    return result.get(role,Part.Shape())

def _component_lower(p,role,inputs):
    if not underside_clamp_active(p):return Part.Shape()
    result={}
    lower=underside_clamp_layout(p)
    if lower:
        blank=clamp_plate_blank(p,'ArmLowerClampPlate',lower['z'],lower['thickness'])
        result[lower['role']]=cut_holes(blank,[(pt,r) for pt,r,_ in plate_holes(p,lower['role'])],lower['z'],lower['thickness'])

    return result.get(role,Part.Shape())

def _component_key(p,role,inputs):
    if not keystone_active(p):return Part.Shape()
    arm_z=p.BottomThickness if arms_above_bottom(p) else -p.ArmThickness
    result={}
    arms=arm_layouts(p)
    body_holes=[(pt,r) for pt,r,_ in plate_holes(p,'BottomPlate')]
    if keystone_active(p):
        reliefs=[]
        if fitted_roots(p):
            outline=compact_key_outline(p,arms)
            key=polygon_plate(outline,arm_z,p.ArmThickness)
            centre=App.Vector(*compact_key_centre(arms),arm_z+p.ArmThickness/2)
            for point in stack_holes(p):
                if abs(polygon_interior_distance(point,outline))<p.StackAccessDiameter/2+p.MinimumWeb:
                    reliefs.append(capsule(point,nearest_polygon_point(point,outline),p.StackAccessDiameter/2,arm_z-1,p.ArmThickness+2))
        else:
            width=p.BodyWidth-2*p.MinimumWeb
            length=2*p.ArmRootY
            wide=p.BottomCentreWidth-2*p.MinimumWeb if p.BottomCentreWidth else None
            blank=profiled_plate(p,'BottomPlate',width,-length/2,length/2,min(p.CornerRadius,width/4,length/4),arm_z,p.ArmThickness,wide,trim_ends=False)
            seats=Part.makeCompound([arm_stem(p,a,arm_z-1,p.ArmThickness+2,p.KeystoneClearance) for a in arms])
            pieces=blank.cut(seats).removeSplitter().Solids
            if not pieces:
                raise ValueError('No room remains for an arm keystone; adjust the arm roots or width.')
            centre=App.Vector(0,0,arm_z+p.ArmThickness/2)
            central=[piece for piece in pieces if piece.isInside(centre,1e-7,True)]
            key=max(central or pieces,key=lambda s:s.Volume)
            for point in stack_holes(p):
                arm=min(arms,key=lambda a:-stem_interior_distance(p,a,point))
                gap=-stem_interior_distance(p,arm,point)-p.KeystoneClearance
                if gap<p.StackAccessDiameter/2+p.MinimumWeb:
                    a,b=arm['start'],arm['motor'];dx,dy=b[0]-a[0],b[1]-a[1]
                    t=max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/(dx*dx+dy*dy)))
                    seat=(a[0]+t*dx,a[1]+t*dy)
                    reliefs.append(capsule(point,seat,p.StackAccessDiameter/2,arm_z-1,p.ArmThickness+2))
        key=cut_holes(key,body_holes+[(pt,p.StackAccessDiameter/2) for pt in stack_holes(p)],arm_z,p.ArmThickness,reliefs)
        if fitted_roots(p) and len(key.Solids)!=1:
            raise ValueError('Access cuts disconnect the compact keystone; change its size or the root layout.')
        if key.Solids:
            central=[piece for piece in key.Solids if piece.isInside(centre,1e-7,True)]
            key=max(central or key.Solids,key=lambda s:s.Volume)
        for arm in arms:
            if key.distToShape(inputs['Arm'+arm['name']])[0]>p.KeystoneClearance+1e-5:
                raise ValueError('The keystone does not seat against all four arms; move the roots closer, increase the arm tail extension, or enlarge the compact key.')
        for item in keystone_retainers(p):
            x,y=item['point'];radius=max(item['head_diameter']/2,item['bore'])+p.MinimumWeb
            ring=cylinder(x,y,radius,arm_z,p.ArmThickness).cut(cylinder(x,y,item['bore']/2,arm_z-1,p.ArmThickness+2))
            if abs(ring.common(key).Volume-ring.Volume)>1e-6:
                raise ValueError('A keystone retaining nut needs more supporting material; change retainer spacing or the arm roots.')
        result['ArmKeystone']=key

    return result.get(role,Part.Shape())

def _component_standoffs(p,role,inputs):
    result={}
    result["Standoffs"] = Part.makeCompound([
        cylinder(*stand["point"], p.StandoffDiameter / 2, stand["base"], stand["length"])
        .cut(cylinder(*stand["point"], p.StandoffHoleDiameter / 2, stand["base"] - 1, stand["length"] + 2))
        for stand in standoff_layouts(p)])

    return result["Standoffs"]

def _component_carbon(p,role,inputs,include_strap_notches=True):
    factories={'BottomPlate':_component_bottom,'MidPlate':_component_mid,'TopPlate':_component_top,
               'ArmClampPlate':_component_clamp,'ArmLowerClampPlate':_component_lower,'ArmKeystone':_component_key}
    if role in CAMERA_ROLES:
        shape=camera_bracket(p,next(m for m in camera_mounts(p) if m['role']==role)) if p.FPVEnabled else Part.Shape()
    elif role=='TopPlate':shape=_component_top(p,role,inputs,include_strap_notches)
    else:shape=factories.get(role,_component_arm)(p,role,inputs)
    if not shape.isNull():
        from .airflow_geometry import apply_cutouts
        from .plate_fillets import apply_plate_fillet
        shape=apply_plate_fillet(p,role,apply_cutouts(p,role,shape))
        from .nut_geometry import apply_seats
        shape=apply_seats(shape,p,role)
        if not shape.isValid() or len(shape.Solids)!=1 or shape.Volume<=0:
            raise ValueError(role+' did not produce one valid solid. Adjust the dimensions.')
    return shape

def _component_flex(p,role,inputs):
    from .flex_geometry import camera_pads
    from .protection_geometry import motor_protectors,side_guards
    if role=='FrontBumper':
        from .bumper_geometry import front_bumper
        return front_bumper(p,inputs)
    if role.startswith('CameraPad'):result=camera_pads(p,roles=(role,))
    elif role.startswith('MotorProtector'):result=motor_protectors(p,inputs,roles=(role,))
    else:
        from .dependency_cache import COMPONENTS
        from .parameters import Parameters
        from .protection_geometry import side_guard_openings
        fixed={'FlexGuardStyle':'Solid','FlexGuardWireEnabled':False,'FlexGuardUSBEnabled':False,'FlexGuardStraps':False,'FlexGuardVTXOpening':False}
        values={n:object.__getattribute__(p,n) for n in p.__dataclass_fields__};values.update(fixed)
        base_p=Parameters(**values);key='_guard_base:'+role
        body=COMPONENTS.get(key,base_p,inputs,lambda t,i:side_guards(t,i,roles=(role,),include_strap_passages=False).get(role,Part.Shape()))
        entry=COMPONENTS.latest.get(key) or COMPONENTS.last_entry
        if hasattr(p,'_reads'):p._reads.update(set(entry['parameters'])-set(fixed))
        for upstream in entry['inputs']:inputs.get(upstream)
        if body.isNull():return body
        return side_guard_openings(p,role,body)
    shape=result.get(role,Part.Shape())
    if not shape.isNull() and (not shape.isValid() or len(shape.Solids)!=1):
        raise ValueError(role+' must be one valid connected printable part; review its dimensions.')
    return shape

def _component_reference(p,role,inputs):
    from .battery import battery_envelope
    if not p.ShowReferences:return Part.Shape()
    from .detailed_references import enabled,detailed_reference
    if enabled(p,role) and (role not in ('CameraEnvelope','VTXEnvelope') or p.FPVEnabled) and (role!='BatteryEnvelope' or p.BatteryReferenceEnabled):return detailed_reference(p,role)[0]
    arm_z=p.BottomThickness if arms_above_bottom(p) else -p.ArmThickness
    if role=='PropellerDiscs':return Part.makeCompound([cylinder(*pt,p.PropDiameter/2,arm_z+p.ArmThickness+p.PropReferenceHeight,.25) for pt in motor_centres(p)])
    if role=='MotorEnvelopes':return Part.makeCompound([cylinder(*pt,p.MotorReferenceDiameter/2,arm_z+p.ArmThickness,p.MotorReferenceHeight) for pt in motor_centres(p)])
    if role=='BatteryEnvelope':return battery_envelope(p) if p.BatteryReferenceEnabled else Part.Shape()
    if role=='StackEnvelope':return _stack_probe(p)
    if role=='CameraEnvelope':return camera_envelope(p) if p.FPVEnabled else Part.Shape()
    if role=='VTXEnvelope':return _vtx_probe(p) if p.FPVEnabled else Part.Shape()
    if role=='FrameCGMarker' and p.ShowFrameCG:
        from .mass_properties import mass_properties
        x,y,z=mass_properties(p,inputs)['display_cg_mm']
        return fuse([Part.makeCylinder(.35,6,App.Vector(x-3,y,z),App.Vector(1,0,0)),Part.makeCylinder(.35,6,App.Vector(x,y-3,z),App.Vector(0,1,0)),cylinder(x,y,.35,z-3,6)])
    return Part.Shape()

def _stack_probe(p):
    return Part.makeBox(p.StackSpacing+6,p.StackSpacing+6,p.StackHeight,App.Vector(-(p.StackSpacing+6)/2,p.StackOffsetY-(p.StackSpacing+6)/2,stack_reference_z(p)))

def _vtx_probe(p):
    z=vtx_deck_z(p)
    return cut_holes(Part.makeBox(p.VTXWidth,p.VTXLength,p.VTXHeight,App.Vector(-p.VTXWidth/2,p.VTXOffsetY-p.VTXLength/2,z)),[(pt,r) for pt,r,_ in vtx_holes(p)],z,p.VTXHeight)

def _canonical_component_parameters(p,role):
    # A cut on another plate does not alter this carbon part's geometry.
    from dataclasses import replace
    from .cutouts import parse_patterns
    import json
    patterns=[v for v in parse_patterns(p.CutoutPatterns) if v['role']==role and v['enabled']]
    return replace(p,CutoutPatterns=json.dumps(patterns,sort_keys=True,separators=(',',':')))

_BUILD_REPORTS={}
_BUILD_MANIFESTS={}
_BUILD_PAYLOADS={}
def _geometry_signature(p):
    if p.PrintedPartColour!='Black':
        from dataclasses import replace
        p=replace(p,PrintedPartColour='Black')
    return p.signature()

def build_report(p):return _BUILD_REPORTS.get(_geometry_signature(p),{})

def component_manifest(role,p=None):
    from .dependency_cache import COMPONENTS
    return _BUILD_MANIFESTS.get(_geometry_signature(p),{}).get(role,'') if p is not None else COMPONENTS.manifest(role)

def component_payload(role,p):return _BUILD_PAYLOADS.get(_geometry_signature(p),{}).get(role,'')

def prime_document_cache(settings):
    from .dependency_cache import COMPONENTS
    from .document import component_objects
    for obj in component_objects(settings).values():
        if not all(n in obj.PropertiesList for n in ('ComponentCache','ComponentBRep','ComponentDocumentDigest')):continue
        import hashlib,json
        manifest=str(obj.ComponentCache);payload=str(obj.ComponentBRep);role=normalise_role(obj.FrameRole)
        from .version import __version__
        try:
            if json.loads(manifest).get('version')!=__version__:continue
        except (ValueError,TypeError,AttributeError):continue
        current=hashlib.sha256(obj.Shape.exportBrepToString().encode()).hexdigest()
        if str(obj.ComponentDocumentDigest)==current and COMPONENTS.has_manifest(role,manifest):continue
        raw=Part.Shape()
        try:
            raw.importBrepFromString(payload)
            if not raw.isNull() and not raw.isValid():continue
            same=str(obj.ComponentDocumentDigest)==current
            # OCC reindexes locations on file read. Verify real geometry before
            # accepting a saved BRep whose serialization has changed.
            if not same:
                actual=obj.Shape
                if raw.isNull()!=actual.isNull():continue
                if raw.isNull():same=True
                elif len(raw.Solids)==len(actual.Solids) and abs(raw.Volume-actual.Volume)<1e-6:
                    same=raw.cut(actual).Volume<1e-6 and actual.cut(raw).Volume<1e-6
            if same and COMPONENTS.seed(role,manifest,raw,payload):
                obj.Proxy._verified_document_digest=current
        except MemoryError:raise
        except Exception:continue


def clear_build_caches():
    from .dependency_cache import clear_geometry_caches
    _build.cache_clear();_FAILED_BUILDS.clear();_BUILD_REPORTS.clear();_BUILD_MANIFESTS.clear();_BUILD_PAYLOADS.clear();clear_geometry_caches()
