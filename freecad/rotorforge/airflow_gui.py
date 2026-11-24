"""Per-part pattern editor and local-coordinate cutting preview."""
import math,json
from functools import lru_cache
from .parameter_memo import parameter_cache
try:
    from PySide import QtCore, QtGui, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
    except ImportError:
        from PySide6 import QtCore, QtGui, QtWidgets
from .cutouts import CUTOUT_ROLES, CUTOUT_TYPES, CUTOUT_MODES, MAX_PATTERNS, MAX_ENABLED_CUTOUTS, PATTERN_DEFAULTS, parse_patterns, encode_patterns, pattern_instances, cutout_polygon, CNC_POLYGON_TYPES, cutout_profile_segments, pattern_cut_count
from .stencil_text import TEXT_FONTS, ENGRAVING_FONTS, RUNE_FONT, text_profiles, check_text_web, minimum_text_size
from .parameters import bottom_bounds, mid_bounds, top_bounds, plate_holes, arm_brace_layouts, arm_layouts, strap_slots, stack_holes, upper_clamp_active, underside_clamp_active, keystone_active, mid_tabs
from .parameters import bottom_body_bounds, bottom_tabs
from .fpv import CAMERA_ROLES, camera_mounts, camera_slots, camera_position_y, camera_pivot_height
from .motor_pads import motor_pad_primitives, motor_tip_slots, motor_pad_unit
from .stack_reliefs import stack_escape_segment
from .plate_profiles import plate_base_polygon, centre_polygon
from .arm_roots import fitted_roots, root_cell_polygon, compact_key_outline, beam_profile_polygon, widened_roots, stem_stations, receiving_tab_expansion_discs

ROLE_LABELS={'FrontBumper':'Front bumper','CameraPadLeft':'Camera pad left','CameraPadRight':'Camera pad right','BottomPlate':'Bottom plate','MidPlate':'Mid plate','TopPlate':'Top plate',
             'ArmClampPlate':'Upper arm clamp / FC plate','ArmKeystone':'Arm keystone',
             'ArmLowerClampPlate':'Lower arm clamp plate',
             'CameraMountLeft':'Camera side plate — left','CameraMountRight':'Camera side plate — right',
             'ArmFrontRight':'Front right arm','ArmFrontLeft':'Front left arm',
             'ArmRearLeft':'Rear left arm','ArmRearRight':'Rear right arm',
             'ActionCameraMount':'HD action-camera mount','LiPoPad':'LiPo pad'}


def capsule_path(a,b,r):
    line=QtGui.QPainterPath(QtCore.QPointF(*a));line.lineTo(QtCore.QPointF(*b))
    if math.dist(a,b)<1e-8:
        path=QtGui.QPainterPath();path.addEllipse(QtCore.QPointF(*a),r,r);return path
    stroke=QtGui.QPainterPathStroker();stroke.setWidth(2*r);stroke.setCapStyle(QtCore.Qt.RoundCap)
    return stroke.createStroke(line)


def polygon_path(points):
    path=QtGui.QPainterPath(QtCore.QPointF(*points[0]))
    for point in points[1:]:path.lineTo(*point)
    path.closeSubpath()
    return path


def _straight_arm_stem_path(p,arm,clearance=0.):
    if not widened_roots(p):return capsule_path(arm['start'],arm.get('beam_end',arm['motor']),p.ArmWidth/2+clearance)
    start,reach,end,motor,rr,rb=stem_stations(p,arm)
    path=QtGui.QPainterPath(QtCore.QPointF(start,rr))
    for point in ((reach,rr),(end,rb),(motor,rb)):path.lineTo(*point)
    path.arcTo(QtCore.QRectF(motor-rb,-rb,2*rb,2*rb),270,180)
    for point in ((end,-rb),(reach,-rr),(start,-rr)):path.lineTo(*point)
    path.arcTo(QtCore.QRectF(start-rr,-rr,2*rr,2*rr),90,180)
    path.closeSubpath()
    transform=QtGui.QTransform();transform.translate(*arm['root'])
    transform.rotate(math.degrees(math.atan2(arm['unit'][1],arm['unit'][0])))
    path=transform.map(path)
    if clearance:
        stroke=QtGui.QPainterPathStroker();stroke.setWidth(2*clearance);stroke.setJoinStyle(QtCore.Qt.RoundJoin)
        path=path.united(stroke.createStroke(path))
    return path


def arm_stem_path(p,arm,clearance=0.):
    """Reuse exact carbon stem geometry between the 2-D editors and part views."""
    return QtGui.QPainterPath(_cached_arm_stem_path(p,arm['name'],float(clearance)))


@parameter_cache(maxsize=128)
def _cached_arm_stem_path(p,arm_name,clearance):
    arm=next(a for a in arm_layouts(p) if a['name']==arm_name)
    return _build_arm_stem_path(p,arm,clearance)


def _build_arm_stem_path(p,arm,clearance=0.):
    """Same true reinforced arm-root mask for the arm and receiving tabs."""
    from .mount_support import arm_supports
    path=_straight_arm_stem_path(p,arm,clearance)
    outline=beam_profile_polygon(p,arm)
    if outline:
        extra=polygon_path(outline)
        if clearance:
            stroke=QtGui.QPainterPathStroker();stroke.setWidth(2*clearance);stroke.setJoinStyle(QtCore.Qt.RoundJoin)
            extra=extra.united(stroke.createStroke(extra))
        path=path.united(extra)
    if p.MotorPadRotationPivot=='Pad beginning':
        path=path.united(capsule_path(arm['beam_end'],arm['motor'],p.ArmWidth/2+clearance))
    supports=tuple((a,b,r+clearance) for a,b,r in
                   arm_supports(p,arm))
    if p.ArmBoltMaterialAllowance<=1e-9:
        from .mount_blends import blend_path
        for a,b,r in supports:path=path.united(capsule_path(a,b,r))
        return blend_path(p,path,supports)
    return _path_add_missing_supports(p,path,supports)


def arm_blank_path(p,arm,arms=None):
    # A manually supplied arm group may have special clipping semantics;
    # keep that path uncached. Normal preview arms use the pure stage cache.
    if arms is not None:
        return _build_arm_blank_path(p,arm,arms)
    return QtGui.QPainterPath(_cached_arm_blank_path(p,arm['name']))


@parameter_cache(maxsize=96)
def _cached_arm_blank_path(p,arm_name):
    arms=arm_layouts(p)
    arm=next(a for a in arms if a['name']==arm_name)
    return _build_arm_blank_path(p,arm,arms)


def _build_arm_blank_path(p,arm,arms):
    transform=QtGui.QTransform();transform.translate(*arm['motor'])
    ux,uy=motor_pad_unit(p,arm)
    transform.rotate(math.degrees(math.atan2(uy,ux)))
    path=arm_stem_path(p,arm).united(transform.map(motor_pad_path(p,arm)))
    path=blend_motor_junction_path(p,arm,path)
    for a,b,r in motor_tip_slots(p,arm):path=path.subtracted(capsule_path(a,b,r))
    if fitted_roots(p):
        path=path.intersected(polygon_path(root_cell_polygon(p,arm,arms)))
        if keystone_active(p):path=path.subtracted(polygon_path(compact_key_outline(p,arms,True)))
    return path


def arm_stack_access_path(p,blank):
    """Match the round relief or open slot used by the CAD arm builder."""
    if not p.ArmRootReliefsEnabled:return blank
    box=blank.boundingRect();tools=QtGui.QPainterPath()
    for pt in stack_holes(p):
        circle=QtGui.QPainterPath();circle.addEllipse(QtCore.QPointF(*pt),p.StackAccessDiameter/2,p.StackAccessDiameter/2)
        if p.ArmRootReliefShape=='Slot toward stack centre':
            if blank.intersected(circle).isEmpty():continue
            tool=capsule_path(*stack_escape_segment(p,pt,(box.left(),box.top(),box.right(),box.bottom())))
        else:tool=circle
        tools=tools.united(tool)
    return blank.subtracted(tools)


def keystone_path(p,arms=None):
    arms=arm_layouts(p) if arms is None else arms
    if fitted_roots(p):return polygon_path(compact_key_outline(p,arms))
    path=profile_path(p,'BottomPlate',p.BodyWidth-2*p.MinimumWeb,-p.ArmRootY,p.ArmRootY,p.CornerRadius,
                      p.BottomCentreWidth-2*p.MinimumWeb if p.BottomCentreWidth else None,trim_ends=False)
    for arm in arms:path=path.subtracted(arm_stem_path(p,arm,p.KeystoneClearance))
    return path


@parameter_cache(maxsize=96)
def _profile_path_cached(p,role,width,rear,front,radius,wide_override,trim_ends):
    path=QtGui.QPainterPath();path.addRoundedRect(QtCore.QRectF(-width/2,rear,width,front-rear),radius,radius)
    outline=plate_base_polygon(p,role,width,rear,front,radius)
    if outline:path=polygon_path(outline)
    points=centre_polygon(p,role,width,rear,front,wide_override)
    if points:
        extra=QtGui.QPainterPath();extra.moveTo(*points[0])
        for point in points[1:]:extra.lineTo(*point)
        extra.closeSubpath();path=path.united(extra)
    from .bottom_nose import edge_commands
    for end in ('Front','Rear') if trim_ends else ():
        commands=edge_commands(p,role,end,width,rear,front)
        if not commands:continue
        mask=QtGui.QPainterPath()
        for item in commands:
            if item[0]=='M':mask.moveTo(*item[1])
            elif item[0]=='L':mask.lineTo(*item[1])
            else:mask.cubicTo(*(value for point in item[1:] for value in point))
        mask.closeSubpath();path=path.intersected(mask)
    return supported_path(p,role,path) if role=='TopPlate' else path


def profile_path(p,role,width,rear,front,radius,wide_override=None,trim_ends=True):
    # QPainterPath is mutable; share only the cached backing geometry, never
    # let a caller modify the cache's canonical shape.
    return QtGui.QPainterPath(_profile_path_cached(p,role,width,rear,front,radius,wide_override,trim_ends))


def mid_tab_paths(p,arms=None):
    arms=arm_layouts(p) if arms is None else arms
    boundary=profile_path(p,'BottomPlate',p.BodyWidth,*bottom_bounds(p),p.CornerRadius)
    paths=[]
    for arm,(a,b,r) in zip((a for a in arms if a['root'][1]>0),mid_tabs(p)):
        root=arm_stem_path(p,arm)
        if fitted_roots(p):
            root=root.intersected(polygon_path(root_cell_polygon(p,arm,arms)))
            if keystone_active(p):root=root.subtracted(polygon_path(compact_key_outline(p,arms,True)))
        cap=capsule_path(a,b,r)
        for point,radius in receiving_tab_expansion_discs(p,arm,r):
            cap=cap.united(capsule_path(point,point,radius))
        paths.append(cap.intersected(root).intersected(boundary))
    return tuple(paths)


def _base_mid_plate_path(p,arms=None):
    path=profile_path(p,'MidPlate',p.BodyWidth,*mid_bounds(p),p.CornerRadius)
    for tab in mid_tab_paths(p,arms):path=path.united(tab)
    return path


def _base_bottom_plate_path(p,arms=None):
    arms=arm_layouts(p) if arms is None else arms
    path=profile_path(p,'BottomPlate',p.BodyWidth,*bottom_body_bounds(p),p.CornerRadius)
    boundary=profile_path(p,'BottomPlate',p.BodyWidth,*bottom_bounds(p),p.CornerRadius)
    upper=profile_path(p,'MidPlate',p.BodyWidth,*mid_bounds(p),p.CornerRadius)
    for arm,(a,b,r) in zip((a for a in arms if a['root'][1]<0),bottom_tabs(p)):
        root=arm_stem_path(p,arm)
        if fitted_roots(p):
            root=root.intersected(polygon_path(root_cell_polygon(p,arm,arms)))
            if keystone_active(p):root=root.subtracted(polygon_path(compact_key_outline(p,arms,True)))
        cap=capsule_path(a,b,r)
        for point,radius in receiving_tab_expansion_discs(p,arm,r):
            cap=cap.united(capsule_path(point,point,radius))
        path=path.united(cap.intersected(root).intersected(boundary).intersected(upper))
    return path


def _base_clamp_plate_path(p,role='ArmClampPlate'):
    from .clamp_outline import clamp_outline_layout
    from .arm_roots import root_width
    c=arm_brace_layouts(p)[0];rear,front,pads=clamp_outline_layout(p);arms=arm_layouts(p)
    boundary=profile_path(p,role,c['width'],c['rear'],c['front'],c['radius'])
    path=profile_path(p,role,c['width'],rear,front,c['radius'])
    for arm in arms:
        root=arm_stem_path(p,arm)
        if fitted_roots(p):
            root=root.intersected(polygon_path(root_cell_polygon(p,arm,arms)))
            if keystone_active(p):root=root.subtracted(polygon_path(compact_key_outline(p,arms,True)))
        base_r=root_width(p)/2
        cap=capsule_path(*arm['bolts'],base_r)
        for point,radius in receiving_tab_expansion_discs(p,arm,base_r):
            cap=cap.united(capsule_path(point,point,radius))
        path=path.united(cap.intersected(root))
    for a,b,r in pads:path=path.united(capsule_path(a,b,r))
    return path.intersected(boundary)


def supported_path(p,role,path):
    from .mount_support import plate_supports
    supports=plate_supports(p,role)
    if p.ArmBoltMaterialAllowance<=1e-9 or role=='TopPlate':
        from .mount_blends import blend_path
        for a,b,r in supports:path=path.united(capsule_path(a,b,r))
        path=blend_path(p,path,supports)
    else:
        path=_path_add_missing_supports(p,path,supports)
    path=_path_add_missing_tpu_rims(p,role,path)
    from .cnc_perimeter import clean_blank_path
    return clean_blank_path(p,role,path)


def _path_add_missing_tpu_rims(p,role,path):
    """Same missing-material-only mounting clearance as the CAD builder."""
    from .tpu_mount_layout import carbon_rim_centres
    for point,radius in carbon_rim_centres(p,role):
        disc=capsule_path(point,point,radius)
        exposed=_path_filled_area(disc.subtracted(path))
        if exposed<=.001:continue
        if _path_filled_area(disc.intersected(path))<math.pi*radius*radius*.75:
            raise ValueError('%s TPU M3 hole needs more plate material or a mounting offset change.' % role)
        path=path.united(disc)
    return path


def _path_add_missing_supports(p,path,supports):
    """Match the exact-bearing-first decision used in the FreeCAD solids."""
    from .mount_support import attachment_needs_bridge
    for centre,anchor,radius in supports:
        bearing=capsule_path(centre,centre,radius)
        if _path_filled_area(bearing.subtracted(path))<=.01:
            continue
        use_bridge=attachment_needs_bridge(
            _path_filled_area(bearing.intersected(path)),p.MinimumWeb)
        path=path.united(capsule_path(centre,anchor,radius) if use_bridge else bearing)
    return path


def _path_filled_area(path):
    """Area of Qt's boolean result; unlike isEmpty ignores subpixel slivers."""
    area=0.
    for poly in path.toFillPolygons():
        vertices=[(pt.x(),pt.y()) for pt in poly]
        area+=abs(sum(a[0]*b[1]-b[0]*a[1]
                      for a,b in zip(vertices,vertices[1:]+vertices[:1])))*.5
    return area


@parameter_cache(maxsize=24)
def _bottom_plate_default(p):
    return supported_path(p,'BottomPlate',_base_bottom_plate_path(p,None))


@parameter_cache(maxsize=24)
def _mid_plate_default(p):
    return supported_path(p,'MidPlate',_base_mid_plate_path(p,None))


@parameter_cache(maxsize=24)
def _clamp_plate_default(p,role):
    return supported_path(p,role,_base_clamp_plate_path(p,role))


def bottom_plate_path(p,arms=None):
    if arms is not None:
        return supported_path(p,'BottomPlate',_base_bottom_plate_path(p,arms))
    return QtGui.QPainterPath(_bottom_plate_default(p))


def mid_plate_path(p,arms=None):
    if arms is not None:
        return supported_path(p,'MidPlate',_base_mid_plate_path(p,arms))
    return QtGui.QPainterPath(_mid_plate_default(p))


def clamp_plate_path(p,role='ArmClampPlate'):
    return QtGui.QPainterPath(_clamp_plate_default(p,role))


def motor_pad_path(p,arm=None):
    """Copy a cached local pad outline for preview and protector construction.

    A complete editor refresh can request the same motor pad path repeatedly
    (arm previews, TPU protectors, airflow). Remember the exact Qt booleans
    even if unrelated battery, text, camera or reference settings change.
    Do not expose a mutable cached QPainterPath to callers.
    """
    key=None
    if arm is not None:
        # Only these values of arm are consumed by motor_pad_primitives.
        # The global pad placement/rotation is performed by the caller.
        key=(tuple(arm['unit']),tuple(arm['motor']),
             tuple(arm.get('nominal_motor',arm['motor'])))
    return QtGui.QPainterPath(_motor_pad_path_cached(p,key))


@parameter_cache(maxsize=96)
def _motor_pad_path_cached(p,arm_key):
    arm=None
    if arm_key is not None:
        unit,motor,nominal=arm_key
        arm={'unit':unit,'motor':motor,'nominal_motor':nominal}
    return _motor_pad_path_uncached(p,arm)


def _motor_pad_path_uncached(p,arm=None):
    path=QtGui.QPainterPath();cuts=[];pad=QtGui.QPainterPath();pad_cuts=[];bumper=QtGui.QPainterPath()
    for d in motor_pad_primitives(p,arm):
        part=QtGui.QPainterPath()
        if d['kind']=='circle':part.addEllipse(QtCore.QPointF(*d['centre']),d['radius'],d['radius'])
        elif d['kind']=='rounded':part.addRoundedRect(QtCore.QRectF(-d['width']/2,-d['width']/2,d['width'],d['width']),d['radius'],d['radius'])
        else:
            part.moveTo(*d['points'][0])
            for point in d['points'][1:]:part.lineTo(*point)
            part.closeSubpath()
        if d.get('operation')=='cut':(pad_cuts if d.get('scope')=='pad' else cuts).append(part)
        else:
            path=path.united(part)
            if not d.get('bumper'):pad=pad.united(part)
            else:bumper=bumper.united(part)
    if cuts or pad_cuts:
        # Qt flattens curves during boolean operations. Work at a larger scale
        # so small concave reliefs keep their dimensions in the preview.
        scale=QtGui.QTransform();scale.scale(100,100)
        path=scale.map(path)
        if pad_cuts:
            # These two reference contours are independent of the individual
            # cut, so do not map them again for every protector/vent slot.
            scaled_pad=scale.map(pad)
            scaled_bumper=scale.map(bumper)
            for part in pad_cuts:
                path=path.subtracted(scale.map(part).intersected(scaled_pad).subtracted(scaled_bumper))
        for part in cuts:path=path.subtracted(scale.map(part))
        path=scale.inverted()[0].map(path)
    for a,b,radius in motor_tip_slots(p):path=path.subtracted(capsule_path(a,b,radius))
    return path


def cutout_path(pattern,radius=.5):
    """Immutable per-shape cache; return a private Qt copy to every caller.

    Repeated Keep/Randomize runs and preview repaints draw the same saved
    rounded Web cells hundreds of times. Reuse their exact analytic contours
    without letting any subsequent Qt boolean modify a cached path.
    """
    vertices=(tuple(tuple(v) for v in pattern.get('vertices') or ())
              if pattern['shape']=='Web cell' else ())
    return QtGui.QPainterPath(_cutout_path_cached(
        pattern['shape'],pattern['width'],pattern['length'],
        pattern['x'],pattern['y'],pattern['rotation'],vertices,pattern.get('arc_angle',75.),
        pattern.get('text','FPV'),pattern.get('text_font',TEXT_FONTS[0]),pattern.get('text_dot',1.2),
        pattern.get('mirror_u',False),pattern.get('mirror_v',False),radius))


@lru_cache(maxsize=384)
def _cutout_path_cached(shape,w,l,x,y,rotation,vertices,arc_angle,text='FPV',text_font=TEXT_FONTS[0],text_dot=1.2,mirror_u=False,mirror_v=False,radius=.5):
    pattern={'shape':shape,'width':w,'length':l,
             'x':x,'y':y,'rotation':rotation,'vertices':vertices,'arc_angle':arc_angle,
             'text':text,'text_font':text_font,'text_dot':text_dot,'_cnc_radius':radius}
    from .cutouts import check_cnc_shape
    check_cnc_shape(pattern,radius)
    path=QtGui.QPainterPath()
    if pattern['shape']=='Circle':path.addEllipse(QtCore.QPointF(),w/2,w/2)
    elif pattern['shape']=='Ellipse':path.addEllipse(QtCore.QPointF(),w/2,l/2)
    elif pattern['shape']=='Slot':
        path=(capsule_path((0,-(l-w)/2),(0,(l-w)/2),w/2) if l>=w else
              capsule_path((-(w-l)/2,0),((w-l)/2,0),l/2))
    elif pattern['shape']=='Rounded rectangle':path.addRoundedRect(QtCore.QRectF(-w/2,-l/2,w,l),max(radius,min(w,l)/4),max(radius,min(w,l)/4))
    elif pattern['shape'] in CNC_POLYGON_TYPES or pattern['shape']=='Text':
        profiles=text_profiles(pattern) if pattern['shape']=='Text' else (cutout_profile_segments(pattern),)
        if pattern['shape']=='Text' and pattern['text_font'] in ENGRAVING_FONTS:
            path.setFillRule(QtCore.Qt.WindingFill)
        for segments in profiles:
            path.moveTo(*segments[0][1])
            for segment in segments:
                if segment[0]=='line':path.lineTo(*segment[2])
                else:
                    start,mid,end=segment[1:]
                    # A true circular arc reconstructed from its three points.
                    ax,ay=start; bx,by=mid;cx,cy=end
                    den=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
                    if abs(den)<1e-10:raise ValueError('Degenerate rounded cutout arc.')
                    a2=ax*ax+ay*ay;b2=bx*bx+by*by;c2=cx*cx+cy*cy
                    ux=(a2*(by-cy)+b2*(cy-ay)+c2*(ay-by))/den
                    uy=(a2*(cx-bx)+b2*(ax-cx)+c2*(bx-ax))/den
                    rad=math.hypot(ax-ux,ay-uy)
                    start_angle=math.atan2(ay-uy,ax-ux)
                    mid_angle=math.atan2(by-uy,bx-ux)
                    end_angle=math.atan2(cy-uy,cx-ux)
                    sweep=(end_angle-start_angle)%(2*math.pi)
                    if (mid_angle-start_angle)%(2*math.pi)>sweep+1e-5:sweep-=2*math.pi
                    path.arcTo(QtCore.QRectF(ux-rad,uy-rad,2*rad,2*rad),
                               -math.degrees(start_angle),-math.degrees(sweep))
            path.closeSubpath()
    else:
        points=cutout_polygon(pattern);path.moveTo(*points[0])
        for point in points[1:]:path.lineTo(*point)
        path.closeSubpath()
    transform=QtGui.QTransform();transform.translate(pattern['x'],pattern['y']);transform.rotate(pattern['rotation'])
    transform.scale(-1 if mirror_u else 1,-1 if mirror_v else 1)
    return transform.map(path)


def _balanced_path_union(paths):
    """Unite paths in a balanced tree instead of repeatedly expanding one BRep.

    Repeated ``result = result.united(next)`` makes every new opening run a
    Boolean on all the previous contours. This is especially costly with
    saved Web cells; pairwise unions bound intermediate complexity and return
    the same union without relying on unsafe even/odd path concatenation.
    """
    level=[path for path in paths if not path.isEmpty()]
    if not level:
        return QtGui.QPainterPath()
    while len(level)>1:
        next_level=[]
        for index in range(0,len(level)-1,2):
            next_level.append(level[index].united(level[index+1]))
        if len(level)%2:
            next_level.append(level[-1])
        level=next_level
    return level[0]


def _spatial_path_union(paths):
    """Only run expensive Qt Boolean unions on potentially touching openings.

    Separate bounding-box components can safely be combined with ``addPath``:
    they cannot geometrically intersect. Within each component the original
    exact balanced union is retained. This is a *preview* optimization; the
    FreeCAD/CNC solid construction and its acceptance rules are unchanged.
    """
    paths=[path for path in paths if not path.isEmpty()]
    if not paths:
        return QtGui.QPainterPath()
    if len(paths)==1:
        return paths[0]
    from .path_groups import intersecting_rect_groups
    groups=intersecting_rect_groups(tuple(
        (r.left(),r.top(),r.right(),r.bottom())
        for r in (path.boundingRect() for path in paths)))
    result=QtGui.QPainterPath()
    for indices in groups:
        if len(indices)==1:
            result.addPath(paths[indices[0]])
        else:
            result.addPath(_balanced_path_union(paths[i] for i in indices))
    return result


def combined_cutout_path(patterns,role,additions=False,radius=.5):
    # Keep the original pattern order and exact 100x Qt Boolean precision.
    relevant=[{k:v for k,v in pattern.items() if k not in ('auto_keep','auto_group','pad_insert')}
              for pattern in patterns
              if pattern['enabled'] and pattern['role']==role and
                 (pattern['mode']=='Add material' if additions else pattern['mode'] not in ('Add material','Pocket'))]
    if not relevant:return QtGui.QPainterPath()
    encoded=json.dumps(relevant,sort_keys=True,separators=(',',':'))
    return QtGui.QPainterPath(_combined_cutout_path_cached(encoded,radius))


@lru_cache(maxsize=64)
def _combined_cutout_path_cached(encoded,radius):
    scale=QtGui.QTransform();scale.scale(100,100)
    profiles=(scale.map(cutout_path(instance,radius))
              for pattern in json.loads(encoded)
              for instance in pattern_instances(pattern))
    return scale.inverted()[0].map(_spatial_path_union(profiles))



@lru_cache(maxsize=32)
def _profile_parameters(p):
    # Protection/vent settings do not change any carbon profile. Keep planar
    # caches warm while tuning those controls on an existing complex frame.
    from dataclasses import replace
    from .parameters import Parameters
    defaults=Parameters()
    changes={name:getattr(defaults,name) for name in p.__dataclass_fields__
             if name.startswith(('FlexGuard','FlexProtector','FlexAntenna','FlexELRS','LiPoPad')) or name in ('FlexRearAntenna','FlexSideGuards','FlexMotorProtectors','PrintedPartColour')}
    changes['CutoutPatterns']='[]'
    return replace(p,**changes)

@parameter_cache(maxsize=96)
def _finished_part_path_cached(p,role,pattern_json,include_strap_notches=True):
    return _make_finished_part_path(p,role,parse_patterns(pattern_json),include_strap_notches)

def finished_part_path(p,role,patterns=None,include_strap_notches=True):
    # Keep markers and generated group IDs are editor metadata, not geometry.
    # Strip them from the geometric cache key so checking Keep on dozens of
    # Web cells does not invalidate the expensive complete plate outline.
    from dataclasses import replace
    if patterns is None:
        patterns=parse_patterns(p.CutoutPatterns)
    geometric=[{key:value for key,value in pattern.items()
                if key not in ('auto_keep','auto_group','pad_insert')}
               for pattern in patterns if pattern['role']==role]
    encoded=json.dumps(geometric,sort_keys=True,separators=(',',':'))
    profile=_profile_parameters(p)
    return QtGui.QPainterPath(_finished_part_path_cached(profile,role,encoded,include_strap_notches))

def _make_finished_part_path(p,role,patterns=None,include_strap_notches=True):
    """Shared complete 2D part profile: joints, holes, slots and applied cuts."""
    path=QtGui.QPainterPath();holes=[];slots=[]
    def rect(width,rear,front,radius):
        q=QtGui.QPainterPath();q.addRoundedRect(QtCore.QRectF(-width/2,rear,width,front-rear),radius,radius);return q
    if role in CAMERA_ROLES:
        if not p.FPVEnabled:return path
        if p.CameraCageStyle=='TPU cage':
            from .cage_preview import unified_side_elevation
            return unified_side_elevation(p,role)
        mount=camera_mounts(p)[0]
        if p.CameraCageStyle=='TPU cage':
            from .cage_preview import preview_mount
            mount=preview_mount(p,mount)
        height=mount['z1']-mount['z0']
        cy=camera_position_y(p);points=[(y-cy,z-p.BottomThickness) for y,z in mount['wall_profile']]
        path.moveTo(*points[0])
        for point in points[1:]:path.lineTo(*point)
        path.closeSubpath()
        from .camera_cages import screw_cage
        for y in (() if screw_cage(p) else mount['tabs_y']):
            path.addRect(QtCore.QRectF(y-cy-p.CameraTabLength/2,-p.BottomThickness,p.CameraTabLength,p.BottomThickness))
        for y in (() if screw_cage(p) else mount['top_tabs_y']):
            path.addRect(QtCore.QRectF(y-cy-p.CameraTabLength/2,height,p.CameraTabLength,p.TopThickness))
        if screw_cage(p):
            radius=p.CameraTPUScrewBore/2+p.CameraTPUBossWall
            for ys,z,direction in ((mount['tabs_y'],mount['z0'],1),(mount['top_tabs_y'],mount['z1'],-1)):
                for y in ys:
                    bottom=z if direction>0 else z-p.CameraTPUInsertDepth-1
                    path=path.united(polygon_path(((y-cy-radius,bottom-p.BottomThickness),(y-cy+radius,bottom-p.BottomThickness),(y-cy+radius,bottom+p.CameraTPUInsertDepth+1-p.BottomThickness),(y-cy-radius,bottom+p.CameraTPUInsertDepth+1-p.BottomThickness))))
            if p.CameraTPUBumper:
                from .cage_extensions import bumper_profile
                path=path.united(polygon_path(tuple((y-cy,z-p.BottomThickness) for y,z in bumper_profile(p,mount))))
        from .fpv import camera_tab_reliefs
        reliefs=camera_tab_reliefs(p,mount)
        if reliefs:
            # Qt booleans flatten curves in coordinate units; work at 100x
            # so small cutter arcs remain round in the millimetre preview.
            precision=QtGui.QTransform();precision.scale(100,100)
            path=precision.map(path)
            for y,z,r in reliefs:
                relief=QtGui.QPainterPath();relief.addEllipse(QtCore.QPointF(y-cy,z-p.BottomThickness),r,r)
                path=path.subtracted(precision.map(relief))
            path=precision.inverted()[0].map(path)
        holes=[((y-cy,z-p.BottomThickness),p.CameraSideHoleDiameter/2) for y,z in mount['side_holes']] if p.FlexCameraMode!='Captured inserts' else []
        if p.FlexCameraMode=='Captured inserts':
            from .flex_preview import camera_interface_path
            opening=camera_interface_path(p,p.FlexInsertWidth,p.FlexInsertHeight)
            precision=QtGui.QTransform();precision.scale(100,100)
            path=precision.inverted()[0].map(precision.map(path).subtracted(precision.map(opening)))
        for arc in (mount['side_arcs'] if p.FlexCameraMode!='Captured inserts' else ()):
            points=[(arc['centre'][0]-cy+arc['radius']*math.cos(math.radians(a)),arc['centre'][1]-p.BottomThickness+arc['radius']*math.sin(math.radians(a)))
                    for a in (arc['start']+(arc['end']-arc['start'])*i/40 for i in range(41))]
            for a,b in zip(points,points[1:]):path=path.subtracted(capsule_path(a,b,arc['width']/2))
    elif role in ('BottomPlate','MidPlate','TopPlate'):
        if role=='MidPlate':
            path=mid_plate_path(p)
        elif role=='BottomPlate':
            path=bottom_plate_path(p)
        else:
            rear,front=top_bounds(p)
            path=profile_path(p,role,p.TopWidth,rear,front,p.CornerRadius)
        holes=[(pt,r) for pt,r,_ in plate_holes(p,role)]
        if role in ('BottomPlate','TopPlate'):slots=list(camera_slots(p,role))
        if role=='TopPlate':
            slots+=list(strap_slots(p))
    elif role in ('ArmClampPlate','ArmLowerClampPlate'):
        clamps=arm_brace_layouts(p)
        if not clamps or role=='ArmLowerClampPlate' and not underside_clamp_active(p) or role=='ArmClampPlate' and not upper_clamp_active(p):return path
        c=clamps[0];path=clamp_plate_path(p,role)
        holes=[(pt,r) for pt,r,_ in plate_holes(p,role)]
    elif role=='ArmKeystone':
        path=keystone_path(p)
        holes=[(pt,p.StackAccessDiameter/2) for pt in stack_holes(p)]
    else:
        arm=next(a for a in arm_layouts(p) if 'Arm'+a['name']==role)
        path=arm_stack_access_path(p,arm_blank_path(p,arm))
        slots=list(motor_tip_slots(p,arm))
        holes=[(pt,p.RootHoleDiameter/2) for pt in arm['bolts']]+[(pt,p.MotorHoleDiameter/2) for pt in arm['motor_holes']]+[(arm['motor'],p.MotorCenterDiameter/2)]
    if role=='TopPlate':
        from .strap_openings import notch_polygons
        for poly in notch_polygons(p) if include_strap_notches else ():
            cut=QtGui.QPainterPath();cut.addPolygon(QtGui.QPolygonF([QtCore.QPointF(*pt) for pt in poly]));cut.closeSubpath();path=path.subtracted(cut)
    source_patterns=parse_patterns(p.CutoutPatterns) if patterns is None else patterns
    additions=combined_cutout_path(source_patterns,role,True,p.CNCToolRadius)
    if not additions.isEmpty():
        path=path.united(additions)
    # Remove disjoint fasteners, straps and vents in a single Qt Boolean.
    # Spatially separate cutters are concatenated without a union. Overlapping
    # ones are still united exactly. Only the preview benefits; the CAD and
    # CNC cutters remain unchanged.
    cutters=[]
    for pt,r in holes:
        hole=QtGui.QPainterPath();hole.addEllipse(QtCore.QPointF(*pt),r,r)
        cutters.append(hole)
    cutters.extend(capsule_path(a,b,r) for a,b,r in slots)
    cutout=combined_cutout_path(source_patterns,role,radius=p.CNCToolRadius)
    if not cutout.isEmpty():
        cutters.append(cutout)
    if cutters:
        path=path.subtracted(_spatial_path_union(cutters))
    from .plate_fillets import preview_fillet
    return preview_fillet(p,role,path)

def replace_parameter_cutouts(p, value):
    from dataclasses import replace
    return replace(p,CutoutPatterns=value)


class AirflowPreview(QtWidgets.QWidget):
    """Saved-pattern locator; all picking stays in Qt, without CAD work."""
    def __init__(self,editor):
        super().__init__();self.editor=editor;self.setMinimumHeight(280)
        self.setMouseTracking(True);self.setCursor(QtCore.Qt.PointingHandCursor)
        self._records_key=None;self._records=();self._focus=False;self._last_pick=None;self.last_error=None
        self._hit_strokes_key=None;self._hit_strokes={}
        self._plate_path_key=None;self._plate_path=None;self._plate_bounds=None
        self._visible_cuts_key=None;self._visible_cuts=()
        # The parent editor reads hundreds of live form fields to construct
        # Parameters. Cache the last validated snapshot for hit-testing;
        # Gui.refresh updates it whenever a frame setting changes.
        self._frame_parameters=None
        self._geometry_parameters=None
        self._addition_signature_key=None;self._addition_signature=()
        self.setToolTip('Click a saved cutout to edit it. Click again in the same place to cycle overlapping patterns. Arrays select the whole saved pattern.')
        self._hover_point=None
        self._hover_timer=QtCore.QTimer(self)
        self._hover_timer.setInterval(45)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._update_hover_tooltip)

    def records(self):
        e=self.editor;role=e.role.currentData();selected=e._selected_index
        # Enabled cuts are bounded by MAX_ENABLED_CUTOUTS. Only the selected
        # disabled array is expanded, avoiding 80,000 inactive copies in a view.
        indices=tuple(i for i,p in enumerate(e.patterns) if p['role']==role and not e.pattern_list.item(i).isHidden() and (p['enabled'] or i==selected))
        radius=self._frame_parameters.CNCToolRadius if self._frame_parameters is not None else e.get_parameters().CNCToolRadius
        key=(role,e._patterns_revision,indices,radius)
        if key!=self._records_key:
            records=[]
            for i in indices:
                paths=tuple(cutout_path(v,radius) for v in pattern_instances(e.patterns[i]))
                box=QtCore.QRectF()
                for path in paths:box=box.united(path.boundingRect())
                records.append((i,paths,box))
            self._records_key=key;self._records=tuple(records)
            self._hit_strokes_key=None;self._hit_strokes={}
        return self._records

    def set_frame_parameters(self, p):
        """Receive the parent's validated snapshot without duplicate repaints."""
        previous=self._frame_parameters
        if previous==p:return
        self._frame_parameters=p
        # Edited cutouts are painted separately from the base blank. The base
        # cannot change just because CutoutPatterns was updated, so keep its
        # derived geometry/silhouette instead of recalculating it on repaint.
        if previous is not None and replace_parameter_cutouts(previous,p.CutoutPatterns)==p:
            if self.isVisible():self.update()
            return
        # Mark stale without recalculating hidden previews. The next actual
        # paint or hit-test canonicalizes once, not on every pointer motion.
        self._geometry_parameters=None
        # Hidden Airflow pages must not trigger expensive preview work until
        # the user actually opens the section (Qt paints it on exposure).
        if self.isVisible():self.update()

    def view(self):
        e=self.editor;role=e.role.currentData()
        p=self._frame_parameters
        if p is None:
            p=e.get_parameters()
            self._frame_parameters=p
        # Hit-testing can run on every pointer movement. Reuse the parent
        # snapshot and only recompute if the preview is used stand-alone.
        geometry_p=self._geometry_parameters
        if geometry_p is None:
            from dataclasses import replace
            geometry_p=replace(_profile_parameters(p),CutoutPatterns='[]')
            self._geometry_parameters=geometry_p
        # Changing any through-cut, Keep flag, cutout list ordering, or other
        # part's pattern does NOT change the plate silhouette. Only added
        # material actually changes the blank. Key by those additions rather
        # than the revision counter covering every airflow operation.
        signature_key=(e._patterns_revision,role)
        if self._addition_signature_key!=signature_key:
            added=[v for v in e.patterns if v['enabled'] and v['role']==role
                   and v['mode']=='Add material']
            self._addition_signature=tuple(json.dumps(
                {k:v for k,v in item.items() if k not in ('auto_keep','auto_group','pad_insert')},
                sort_keys=True,separators=(',',':')) for item in added)
            self._addition_patterns=added
            self._addition_signature_key=signature_key
        added_key=self._addition_signature
        key=(geometry_p,role,added_key)
        if key!=self._plate_path_key:
            # Draw through-cuts separately; expensive plate profile Booleans
            # are only needed when its perimeter or material additions change.
            self._plate_path=finished_part_path(p,role,self._addition_patterns)
            self._plate_bounds=self._plate_path.boundingRect()
            self._plate_path_key=key
        path=self._plate_path;box=QtCore.QRectF(self._plate_bounds)
        if box.isEmpty():
            for i,paths,extent in self.records():box=box.united(extent)
        if self._focus:
            record=next((r for r in self.records() if r[0]==e._selected_index),None)
            if record:box=record[2].adjusted(-4,-4,4,4)
        scale=max(.001,min(max(1,self.width()-32)/max(1,box.width()),max(1,self.height()-32)/max(1,box.height())))
        transform=QtGui.QTransform();transform.translate(self.width()/2,self.height()/2);transform.scale(scale,-scale);transform.translate(-box.center().x(),-box.center().y())
        return path,transform,scale

    def visible_through_cuts(self):
        """All enabled cuts, including those hidden by the list filter."""
        e=self.editor;role=e.role.currentData()
        radius=self._frame_parameters.CNCToolRadius if self._frame_parameters is not None else e.get_parameters().CNCToolRadius
        key=(role,e._patterns_revision,radius)
        if self._visible_cuts_key!=key:
            self._visible_cuts=tuple(
                cutout_path(inst,radius)
                for pattern in e.patterns
                if pattern['enabled'] and pattern['role']==role
                and pattern['mode'] not in ('Add material','Pocket')
                for inst in pattern_instances(pattern))
            self._visible_cuts_key=key
        return self._visible_cuts

    def fit_plate(self):self._focus=False;self.update()
    def zoom_selected(self):
        if self.editor._selected_index<0:return
        self._focus=True;self.update()

    def number_label(self,index,box,transform):
        point=transform.map(box.center());font=QtGui.QFont(self.font());font.setPixelSize(11);font.setBold(index==self.editor._selected_index)
        width=QtGui.QFontMetrics(font).horizontalAdvance('#'+str(index+1))+8
        return QtCore.QRectF(point.x()-width/2,point.y()-9,width,18),font

    def hit_indices(self,position):
        path,transform,scale=self.view();point=transform.inverted()[0].map(position)
        stroke_width=8/scale
        key=(self._records_key,stroke_width)
        if key!=self._hit_strokes_key:
            self._hit_strokes_key=key;self._hit_strokes={}
        stroke=None
        hits=[]
        for i,paths,box in reversed(self.records()):
            if not box.adjusted(-4/scale,-4/scale,4/scale,4/scale).contains(point):continue
            tag_visible=self.editor.show_numbers.isChecked() or i==self.editor._selected_index
            if tag_visible and self.number_label(i,box,transform)[0].contains(position):
                hits.append(i);continue
            for j,cut in enumerate(paths):
                if cut.contains(point):
                    hits.append(i);break
                cache_key=(i,j)
                edge=self._hit_strokes.get(cache_key)
                if edge is None:
                    if stroke is None:
                        stroke=QtGui.QPainterPathStroker();stroke.setWidth(stroke_width)
                    edge=stroke.createStroke(cut)
                    self._hit_strokes[cache_key]=edge
                if edge.contains(point):
                    hits.append(i);break
        return hits

    def mousePressEvent(self,event):
        if event.button()!=QtCore.Qt.LeftButton:return super().mousePressEvent(event)
        try:
            pos=event.position() if hasattr(event,'position') else QtCore.QPointF(event.pos())
            hits=self.hit_indices(pos)
            if not hits:return
            previous=self._last_pick
            repeat=previous and (pos-previous[0]).manhattanLength()<=6 and hits==previous[1]
            index=hits[(hits.index(previous[2])+1)%len(hits)] if repeat and previous[2] in hits else hits[0]
            if self.editor.choose_pattern(index):
                self._last_pick=(pos,hits,index)
                if len(hits)>1:self.editor.status.setText('Selected #'+str(index+1)+'. '+str(len(hits))+' overlapping patterns here; click again to cycle. Edit and press Apply to pattern.')
        except (ValueError,RuntimeError):return

    def mouseMoveEvent(self,event):
        # QPainterPath stroke containment is expensive with hundreds of saved
        # openings. Coalesce mouse moves; the latest position is tested using
        # the complete native paths after 45 ms, with no preview downsampling.
        self._hover_point=event.position() if hasattr(event,'position') else QtCore.QPointF(event.pos())
        if not self._hover_timer.isActive():self._hover_timer.start()

    def _update_hover_tooltip(self):
        pos=self._hover_point
        if pos is None or not self.isVisible():return
        try:
            hits=self.hit_indices(pos)
            text='\n'.join(self.editor.pattern_text(i) for i in hits)
            tooltip=text+'\nClick to select; click again to cycle overlaps.' if hits else 'Click a saved cutout to select it. Disabled patterns can be found in the list.'
            if tooltip!=self.toolTip():self.setToolTip(tooltip)
        except (ValueError,RuntimeError):pass

    def leaveEvent(self,event):
        self._hover_point=None
        self._hover_timer.stop()
        return super().leaveEvent(event)

    def paintEvent(self,event):
        painter=QtGui.QPainter(self);painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(),QtGui.QColor('#f3f6f8'));self.last_error=None
        try:
            path,transform,scale=self.view();painter.setTransform(transform)
            painter.setPen(QtGui.QPen(QtGui.QColor('#111315'),.8/scale));painter.setBrush(QtGui.QColor('#2e3033'));painter.drawPath(path)
            # Cheap visual holes, independent of Qt boolean complexity.
            # Their contours come from cutout_path, the same cutter-radius-rounded
            # shape used by the exact manufacturing clearance check.
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QColor('#f3f6f8'))
            for cut in self.visible_through_cuts():
                painter.drawPath(cut)
            for i,paths,box in sorted(self.records(),key=lambda r:r[0]==self.editor._selected_index):
                selected=i==self.editor._selected_index
                pocket=self.editor.patterns[i]['mode']=='Pocket'
                if not selected and not pocket and not self.editor.show_numbers.isChecked():continue
                if selected or pocket:
                    pen=QtGui.QPen(QtGui.QColor('#087fa8') if pocket else QtGui.QColor('#d87809'),2.5/scale)
                    if pocket:pen.setStyle(QtCore.Qt.DashLine)
                    if not self.editor.patterns[i]['enabled']:pen.setStyle(QtCore.Qt.DashLine)
                    painter.setPen(pen);painter.setBrush(QtGui.QColor(32,170,206,85) if pocket else QtGui.QColor(255,178,65,65))
                    for cut in paths:painter.drawPath(cut)
                if self.editor.show_numbers.isChecked() or selected:
                    rect,font=self.number_label(i,box,transform);painter.save();painter.resetTransform()
                    text='#'+str(i+1);painter.setFont(font)
                    painter.setPen(QtGui.QColor('#9a4d00') if selected else QtGui.QColor('#08798a'));painter.setBrush(QtGui.QColor(255,255,255,230));painter.drawRoundedRect(rect,3,3);painter.drawText(rect,QtCore.Qt.AlignCenter,text);painter.restore()
        except Exception as exc:self.last_error=str(exc)
        finally:painter.end()


# Search can index Airflow without constructing its Qt widgets or parsing saved patterns.
_AIRFLOW_SEARCH_CONTROLS = (('Part', 'role'), ('Cutout type', 'shape'), ('Cutting mode / outline notch', 'mode'), ('Enabled', 'enabled'), ('Saved patterns', 'pattern_list'), ('Find saved cutout', 'find_pattern'), ('Filter cutouts by part', 'filter_role'), ('Show pattern numbers', 'show_numbers'), ('Zoom to selected cutout', 'zoom_button'), ('Fit cutout plate preview', 'fit_button'), ('Add pattern', 'add_button'), ('Apply to pattern', 'apply_button'), ('Remove pattern', 'remove_button'), ('Discard unapplied changes', 'discard_button'), ('Copy to other camera side', 'copy_button'), ('Check plate cuts in CAD', 'check_button'))
_AIRFLOW_SEARCH_INPUTS = (('Width', 'width'), ('Length', 'length'), ('Centre U', 'x'), ('Centre V', 'y'), ('Columns', 'columns'), ('Rows', 'rows'), ('Pitch U', 'pitch_x'), ('Pitch V', 'pitch_y'), ('Rotation', 'rotation'), ('Arc angle', 'arc_angle'), ('Pocket depth', 'depth'))
AIRFLOW_SEARCH_FIELDS = tuple(title for title, _ in _AIRFLOW_SEARCH_CONTROLS + _AIRFLOW_SEARCH_INPUTS)


class AirflowEditor(QtWidgets.QWidget):
    changed=QtCore.Signal(str)
    metadataChanged=QtCore.Signal(str)
    def __init__(self,get_parameters):
        super().__init__();self.get_parameters=get_parameters;self.patterns=[];self.inputs={};self._selected_index=-1;self._patterns_revision=0
        layout=QtWidgets.QVBoxLayout(self)
        note=QtWidgets.QLabel('Add a pattern, then select it to edit and press Apply to pattern. Through-cut openings need a minimum carbon web. Blind pockets may overlap holes, slots, cutouts and outer edges to form open-ended cable channels; they retain at least half the plate thickness where the plate is intact. Inactive parts retain their patterns. Use Interior for through vents, Pocket for shallow channels, or Outline notch to remove a full-depth edge section. Crossing mounting holes with pockets can weaken hardware support; inspect the final CAD model.');note.setWordWrap(True);layout.addWidget(note)
        self.copy_to_pad=QtWidgets.QCheckBox('Copy matching airflow openings into the LiPo pad')
        self.copy_to_pad.setToolTip('Copies openings from the top or bottom mounting plate into the printed LiPo pad, when the pad follows the carrier. Turning it off bridges airflow openings in the pad; mounting holes and strap openings are still preserved. The final solid is recalculated only on Create / Update.')
        layout.addWidget(self.copy_to_pad)
        self.capacity=QtWidgets.QLabel();layout.addWidget(self.capacity)
        self.pattern_list=QtWidgets.QListWidget();self.pattern_list.setMinimumHeight(105);self.pattern_list.setMaximumHeight(160)
        filters=QtWidgets.QHBoxLayout();layout.addLayout(filters)
        self.find_pattern=QtWidgets.QLineEdit();self.find_pattern.setPlaceholderText('Find cutout: #number, shape, mode, coordinates...');self.find_pattern.setClearButtonEnabled(True);filters.addWidget(self.find_pattern,2)
        self.filter_role=QtWidgets.QComboBox();self.filter_role.addItem('All parts',None)
        for part in CUTOUT_ROLES:self.filter_role.addItem(ROLE_LABELS[part],part)
        self.filter_role.setToolTip('Filter the saved-pattern list. Selecting a result opens its part in the preview.');filters.addWidget(self.filter_role,1)
        self.filter_count=QtWidgets.QLabel();layout.addWidget(self.filter_count)
        layout.addWidget(self.pattern_list)
        form=QtWidgets.QFormLayout();layout.addLayout(form)
        self.role=QtWidgets.QComboBox()
        for role in CUTOUT_ROLES:self.role.addItem(ROLE_LABELS[role],role)
        self.role.setCurrentIndex(2);form.addRow('Part',self.role)
        self.shape=QtWidgets.QComboBox();self.shape.addItems(CUTOUT_TYPES);self.shape.setCurrentText('Slot');form.addRow('Cutout type',self.shape)
        self.shape.setToolTip('CNC-safe profiles include classic and curved round-ended slots plus cutter-radius-rounded polygon motifs. Arc slot uses the separate signed Arc bend control; length is the end-centre chord. Very narrow dimensions are refused.')
        self.mode=QtWidgets.QComboBox();self.mode.addItems(CUTOUT_MODES);form.addRow('Operation',self.mode)
        self.mode.setToolTip('Interior removes material through the carbon. Pocket makes a shallow blind relief up to half thickness, including across plate edges, holes and other cutouts; machine it separately and check remaining screw support. Outline notch opens an outside edge. Add material extends main/clamp edges.')
        self.enabled=QtWidgets.QCheckBox('Enabled');self.enabled.setChecked(True);form.addRow(self.enabled)
        for keys,title in ((('width','length'),'Width / length'),(('x','y'),'Centre U / V'),(('columns','rows'),'Columns / rows'),(('pitch_x','pitch_y'),'Pitch U / V'),(('rotation',),'Rotation')):
            row=QtWidgets.QWidget();line=QtWidgets.QHBoxLayout(row);line.setContentsMargins(0,0,0,0)
            for key in keys:
                integer=key in ('columns','rows');control=QtWidgets.QSpinBox() if integer else QtWidgets.QDoubleSpinBox()
                if integer:control.setRange(1,20)
                else:
                    control.setDecimals(3 if key in ('x','y') else 2);control.setRange(-700 if key in ('x','y') else -360 if key=='rotation' else .5,700 if key in ('x','y') else 360 if key=='rotation' else 500)
                    if key in ('x','y'):control.setSingleStep(.001)
                    control.setSuffix('°' if key=='rotation' else ' mm')
                control.setValue(PATTERN_DEFAULTS[key]);line.addWidget(control);self.inputs[key]=control
            form.addRow(title,row)
        mirror_row=QtWidgets.QWidget();mirror_layout=QtWidgets.QHBoxLayout(mirror_row);mirror_layout.setContentsMargins(0,0,0,0)
        self.mirror_u=QtWidgets.QCheckBox('Flip U (left/right)');self.mirror_v=QtWidgets.QCheckBox('Flip V (front/rear)')
        for control in (self.mirror_u,self.mirror_v):
            control.setToolTip('Reflect the shape in its local coordinates before rotation; its centre and grid stay unchanged.')
            mirror_layout.addWidget(control)
        form.addRow('Mirror shape',mirror_row)
        self.arc_angle_label=QtWidgets.QLabel('Arc bend')
        self.arc_angle=QtWidgets.QDoubleSpinBox()
        self.arc_angle.setDecimals(1)
        self.arc_angle.setRange(-170.,170.)
        self.arc_angle.setSingleStep(5.)
        self.arc_angle.setSuffix('°')
        self.arc_angle.setValue(PATTERN_DEFAULTS['arc_angle'])
        self.arc_angle.setToolTip('Arc slot only: signed curvature in degrees. Positive curves to local +U, negative curves to -U, and 0° produces a straight capsule. Length is the chord between end-cap centres; Width is the channel thickness. Rotate the entire slot using Rotation.')
        form.addRow(self.arc_angle_label,self.arc_angle)
        self.inputs['arc_angle']=self.arc_angle
        self.text_label=QtWidgets.QLabel('CNC text')
        self.text_input=QtWidgets.QLineEdit('FPV');self.text_input.setMaxLength(24)
        self.text_input.setToolTip('A–Z, 0–9, space, -, _ and period. Lowercase is converted to uppercase. Width / length set the full lettering grid size.')
        form.addRow(self.text_label,self.text_input)
        self.text_font_label=QtWidgets.QLabel('CNC font')
        self.text_font=QtWidgets.QComboBox();self.text_font.addItems(TEXT_FONTS);self.text_font.setCurrentText(ENGRAVING_FONTS[0])
        self.text_font.setToolTip('Runic engraving supports both Interior through-cuts and blind Pocket lettering. All other fonts are blind pockets. Use Fit lettering to CNC rules after choosing a style and operation.')
        form.addRow(self.text_font_label,self.text_font)
        self.text_dot_label=QtWidgets.QLabel('Dot diameter')
        self.text_dot=QtWidgets.QDoubleSpinBox();self.text_dot.setRange(1.,10.);self.text_dot.setDecimals(2);self.text_dot.setSuffix(' mm');self.text_dot.setValue(1.)
        form.addRow(self.text_dot_label,self.text_dot)
        self.text_fit=QtWidgets.QPushButton('Fit lettering to CNC rules');self.text_fit.clicked.connect(self.fit_lettering)
        self.text_fit.setToolTip('Fit the lettering to its selected stroke diameter (at least the selected cutter diameter), preserving the selected cutter-radius rule. Runic through-cuts also respect the minimum material web. Exact placement is checked on Create / Update.')
        form.addRow(self.text_fit)
        self.text_size_hint=QtWidgets.QLabel();self.text_size_hint.setWordWrap(True)
        form.addRow(self.text_size_hint)
        self.text_input.textChanged.connect(self.update_text_size_hint)
        self.text_dot.valueChanged.connect(self.update_text_size_hint)
        for key in ('width','length'):
            self.inputs[key].valueChanged.connect(self.update_text_size_hint)
        self.text_font.currentIndexChanged.connect(self.update_shape_controls)
        self.shape.currentIndexChanged.connect(self.update_shape_controls)
        self.mode.currentIndexChanged.connect(self.update_text_size_hint)
        self.update_shape_controls()
        self.depth=QtWidgets.QDoubleSpinBox()
        self.depth.setDecimals(2);self.depth.setRange(.1,50.);self.depth.setSingleStep(.1)
        self.depth.setSuffix(' mm');self.depth.setValue(PATTERN_DEFAULTS['depth'])
        self.depth.setToolTip('Blind machining depth, from the upper face (or outer side of camera plates). Maximum: half of the carbon thickness. This is not a through-cut.')
        self.depth_label=QtWidgets.QLabel('Pocket depth')
        form.addRow(self.depth_label,self.depth)
        self.inputs['depth']=self.depth
        self.coordinates=QtWidgets.QLabel();self.coordinates.setWordWrap(True);layout.addWidget(self.coordinates)
        buttons=QtWidgets.QHBoxLayout();layout.addLayout(buttons)
        self.add_button=QtWidgets.QPushButton('Add pattern');self.apply_button=QtWidgets.QPushButton('Apply to pattern');self.remove_button=QtWidgets.QPushButton('Remove')
        for b in (self.add_button,self.apply_button,self.remove_button):buttons.addWidget(b)
        self.discard_button=QtWidgets.QPushButton('Discard unapplied changes');layout.addWidget(self.discard_button)
        self.discard_button.clicked.connect(self.discard_changes)
        self.copy_button=QtWidgets.QPushButton('Copy to other camera side');layout.addWidget(self.copy_button)
        locator=QtWidgets.QHBoxLayout();layout.addLayout(locator)
        self.show_numbers=QtWidgets.QCheckBox('Show pattern numbers');self.show_numbers.setChecked(True);locator.addWidget(self.show_numbers)
        self.zoom_button=QtWidgets.QPushButton('Zoom to selected');locator.addWidget(self.zoom_button)
        self.fit_button=QtWidgets.QPushButton('Fit plate');locator.addWidget(self.fit_button)
        self.preview=AirflowPreview(self);layout.addWidget(self.preview)
        self.find_pattern.textChanged.connect(self.filter_patterns);self.filter_role.currentIndexChanged.connect(self.filter_patterns)
        self.show_numbers.toggled.connect(self.preview.update);self.zoom_button.clicked.connect(self.preview.zoom_selected);self.fit_button.clicked.connect(self.preview.fit_plate)
        # Keep locating and visual selection together, ahead of the edit form.
        layout.removeItem(locator);layout.removeWidget(self.preview)
        index=layout.indexOf(self.pattern_list)+1;layout.insertLayout(index,locator);layout.insertWidget(index+1,self.preview)
        self.status=QtWidgets.QLabel('Click a saved opening to select it; click again to cycle overlaps. Orange highlights the selected pattern. CAD checks run on Create / Update.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.check_button=QtWidgets.QPushButton('Check plate cuts in CAD');layout.addWidget(self.check_button)
        self.add_button.clicked.connect(self.add_pattern);self.apply_button.clicked.connect(self.apply_pattern);self.remove_button.clicked.connect(self.remove_pattern);self.copy_button.clicked.connect(self.copy_camera)
        self.pattern_list.currentRowChanged.connect(self.select_pattern)
        self.pattern_list.itemChanged.connect(self._on_keep_check_changed)
        self.role.currentIndexChanged.connect(self.update_coordinates)
        self.check_button.clicked.connect(self.check_cad);self.update_coordinates()
        self.role.currentIndexChanged.connect(self.update_pocket_controls)
        self.mode.currentIndexChanged.connect(self.update_pocket_controls)
        self.update_pocket_controls()

        self._draft_baseline=self.draft()
        for control in (self.role,self.shape,self.mode):control.currentIndexChanged.connect(self.update_pending_status)
        self.enabled.toggled.connect(self.update_pending_status)
        self.mirror_u.toggled.connect(self.update_pending_status);self.mirror_v.toggled.connect(self.update_pending_status)
        self.text_input.textChanged.connect(self.update_pending_status)
        self.text_font.currentIndexChanged.connect(self.update_pending_status)
        self.text_dot.valueChanged.connect(self.update_pending_status)
        for control in self.inputs.values():control.valueChanged.connect(self.update_pending_status)
        self.update_capacity();self.filter_patterns()
        # Full-width cutting workspace: saved patterns, editing, and inspection
        # stay alongside each other instead of forming one long vertical page.
        while layout.count():
            layout.takeAt(0)
        self.workspace = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.workspace.setChildrenCollapsible(False)
        layout.addWidget(self.workspace, 1)
        library = QtWidgets.QWidget(); library_layout = QtWidgets.QVBoxLayout(library)
        library_layout.setContentsMargins(0, 0, 4, 0)
        self.capacity.setWordWrap(True)
        library_layout.addWidget(self.capacity)
        # A vertical filter stack fits the saved-pattern column.
        while filters.count():filters.takeAt(0)
        library_layout.addWidget(self.find_pattern)
        self.filter_role.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.filter_role.setMinimumContentsLength(10)
        library_layout.addWidget(self.filter_role)
        library_layout.addWidget(self.filter_count)
        self.pattern_list.setMinimumHeight(80);self.pattern_list.setMaximumHeight(16777215)
        library_layout.addWidget(self.pattern_list, 1)
        library_layout.addWidget(self.remove_button)
        help_button = QtWidgets.QPushButton('How to use cutouts')
        help_button.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, 'Airflow / outlines', note.text()))
        library_layout.addWidget(help_button)
        note.hide()
        edit = QtWidgets.QWidget(); edit_layout = QtWidgets.QVBoxLayout(edit)
        edit_layout.setContentsMargins(4, 0, 4, 0)
        edit_layout.addLayout(form)
        edit_layout.addWidget(self.coordinates)
        while buttons.count():buttons.takeAt(0)
        edit_actions = QtWidgets.QHBoxLayout()
        edit_actions.addWidget(self.add_button);edit_actions.addWidget(self.apply_button)
        edit_layout.addLayout(edit_actions)
        edit_layout.addWidget(self.discard_button)
        edit_layout.addWidget(self.copy_button)
        edit_layout.addWidget(self.check_button)
        # Plate-aware interior design motifs only.  Manual outline editing
        # remains available; unreliable automatic perimeter sculpting is gone.
        from .airflow_auto import INTERIOR_STYLES, AUTO_ROLES
        auto_box=QtWidgets.QGroupBox('Automatic cutout design')
        auto_form=QtWidgets.QFormLayout(auto_box)
        self.auto_role=QtWidgets.QComboBox()
        for part in AUTO_ROLES:self.auto_role.addItem(ROLE_LABELS[part],part)
        self.auto_role.setCurrentIndex(self.auto_role.findData('TopPlate'))
        auto_form.addRow('Target plate',self.auto_role)
        self.auto_style=QtWidgets.QComboBox();auto_form.addRow('Style',self.auto_style)
        self.auto_layout=QtWidgets.QComboBox()
        self.auto_layout.addItems(('Mirrored','Organic balance'))
        self.auto_layout.setToolTip('Mirrored creates exact left/right partner cutouts as one accepted unit. Organic balance uses structured plate motifs with occasional unequal details.')
        auto_form.addRow('Arrangement',self.auto_layout)
        self.auto_density=QtWidgets.QComboBox()
        self.auto_density.addItems(('Sparse','Balanced','Detailed'))
        self.auto_density.setCurrentText('Balanced')
        auto_form.addRow('Detail',self.auto_density)
        self.auto_web=QtWidgets.QComboBox()
        for mm in range(3,11):self.auto_web.addItem(f'{mm} mm',mm)
        self.auto_web.setCurrentIndex(self.auto_web.findData(5))
        self.auto_web.setToolTip('Minimum carbon thickness between neighboring automatically generated openings, the plate edge, and mounting keepouts. Select 3–10 mm; the global structural Minimum web takes precedence if higher.')
        auto_form.addRow('Carbon between cutouts',self.auto_web)
        self._last_auto_patterns=[]
        self._last_auto_role=None
        self.auto_operation=QtWidgets.QComboBox();self.auto_operation.addItems(('Through cuts','Blind pockets'))
        auto_form.addRow('Airflow operation',self.auto_operation)
        self.auto_depth=QtWidgets.QDoubleSpinBox();self.auto_depth.setDecimals(2)
        self.auto_depth.setRange(.1,50);self.auto_depth.setValue(.5)
        self.auto_depth.setSuffix(' mm');self.auto_depth.setSingleStep(.1)
        self.auto_depth_label=QtWidgets.QLabel('Auto pocket depth')
        auto_form.addRow(self.auto_depth_label,self.auto_depth)
        self.auto_shape_mix=QtWidgets.QComboBox()
        self.auto_shape_mix.addItems(('Mixed shapes','Web cells','Manual shapes'))
        self.auto_shape_mix.setToolTip('Mix irregular web cells with CNC-rounded manual-library cutout shapes, or choose one family. New candidates are always checked against plate edges, mounting hardware and kept openings.')
        auto_form.addRow('Cutout variety',self.auto_shape_mix)
        self.auto_role.currentIndexChanged.connect(self.update_auto_limits)
        self.auto_role.currentIndexChanged.connect(self._update_randomize_button)
        self.auto_operation.currentIndexChanged.connect(self.update_auto_limits)
        self.auto_generate=QtWidgets.QPushButton('Generate plate design')
        self.auto_generate.setToolTip('Quickly arrange small and medium CNC-rounded openings around the existing carbon, mounts and kept shapes. Uses a bounded, local geometric search.')
        self.auto_generate.clicked.connect(self.generate_automatic)
        auto_form.addRow(self.auto_generate)
        self.auto_random=QtWidgets.QPushButton('Randomize design')
        self.auto_random.setToolTip('Replace unlocked generated openings with a new mix of web cells and manual cutout shapes. Kept shapes and user-created cuts remain unchanged.')
        self.auto_random.clicked.connect(lambda checked=False:self.generate_automatic(randomize=True))
        self.auto_random.setEnabled(False)
        auto_form.addRow(self.auto_random)
        self.auto_note=QtWidgets.QLabel('Mixed shapes combines irregular Web cells with CNC-rounded shapes from the manual palette. Small and medium openings are preferred over oversized holes. Keep protects an opening (and its mirrored partner); Randomize searches the remaining free regions without moving it. Minimum carbon web, mounting clearances and R0.5 fillets still apply; run the CAD check before manufacturing.')
        self.auto_note.setWordWrap(True);auto_form.addRow(self.auto_note)
        edit_layout.addWidget(auto_box)
        self.update_auto_styles();self.update_auto_limits()
        edit_layout.addStretch()
        inspect = QtWidgets.QWidget(); inspect_layout = QtWidgets.QVBoxLayout(inspect)
        inspect_layout.setContentsMargins(4, 0, 0, 0)
        # Two compact rows keep preview actions visible in narrower windows.
        while locator.count():locator.takeAt(0)
        inspect_layout.addWidget(self.show_numbers)
        view_actions = QtWidgets.QHBoxLayout()
        view_actions.addWidget(self.zoom_button);view_actions.addWidget(self.fit_button)
        inspect_layout.addLayout(view_actions)
        self.preview.setMinimumHeight(180)
        inspect_layout.addWidget(self.preview, 1)
        inspect_layout.addWidget(self.status)
        for panel in (library, edit, inspect):self.workspace.addWidget(panel)
        self.workspace.setSizes([210, 350, 420])


    def search_controls(self):
        return ([(title,getattr(self,attr)) for title,attr in _AIRFLOW_SEARCH_CONTROLS]
                + [(title,self.inputs[key]) for title,key in _AIRFLOW_SEARCH_INPUTS])

    def update_coordinates(self,*args):
        camera=self.role.currentData() in CAMERA_ROLES
        self.coordinates.setText('U = Y offset from nominal camera centre. V = height above bottom plate upper face. Width is along U; length is along V.' if camera else
                                 'U = frame X (right). V = frame Y (front). The grid is centred here; rotation turns both cuts and grid. Circle uses width as diameter.')
        self.copy_button.setEnabled(camera);self.preview.fit_plate()
        if hasattr(self,'depth_label'):self.update_pocket_controls()

    def _plate_thickness(self,role):
        p=self.get_parameters()
        if role=='TopPlate':return p.TopThickness
        if role=='MidPlate':return p.ClampThickness
        if role=='BottomPlate':return p.BottomThickness
        if role=='ArmClampPlate':return p.ArmBraceThickness
        if role=='ArmLowerClampPlate':return p.UndersideClampThickness
        if role in CAMERA_ROLES:return p.CameraBracketThickness
        return p.ArmThickness

    def update_pocket_controls(self,*args):
        pocket=self.mode.currentText()=='Pocket'
        camera_side=self.role.currentData() in CAMERA_ROLES
        if pocket and camera_side and self.get_parameters().CameraCageStyle!='Carbon side plates':
            self.depth.setToolTip('Blind pockets require Carbon side plates; TPU cage pockets are not supported.')
        self.depth_label.setVisible(pocket);self.depth.setVisible(pocket)
        max_depth=max(.1,self._plate_thickness(self.role.currentData())*.5)
        self.depth.setMaximum(max_depth)
        self.depth.setToolTip(f'Machine from the upper/outside surface, with at least {max_depth:g} mm carbon remaining. Maximum depth: {max_depth:g} mm.')
        if hasattr(self,'auto_role'):self.update_auto_limits()

    def update_auto_styles(self,*args):
        from .airflow_auto import INTERIOR_STYLES
        self.auto_style.clear();self.auto_style.addItems(INTERIOR_STYLES)

    def update_auto_limits(self,*args):
        role=self.auto_role.currentData()
        max_depth=max(.1,self._plate_thickness(role)*.5)
        self.auto_depth.setMaximum(max_depth)
        pockets=self.auto_operation.currentIndex()==1
        self.auto_depth_label.setVisible(pockets);self.auto_depth.setVisible(pockets)
        self.auto_depth.setToolTip(f'Blind recess depth must be at most half the target carbon thickness: {max_depth:g} mm.')

    @staticmethod
    def _qt_path_has_area(path):
        # False is the safe outcome for tiny paths / boolean artefacts.
        return not path.isEmpty() and path.boundingRect().width()*path.boundingRect().height()>1e-4

    @staticmethod
    def _same_generated_pattern(a,b):
        """Changing only the Keep checkbox must not count as a geometry edit."""
        return ({k:v for k,v in a.items() if k not in ('auto_keep','pad_insert')} ==
                {k:v for k,v in b.items() if k not in ('auto_keep','pad_insert')})

    def _active_auto_batch(self):
        """Find this editor's unedited generated suffix, ignoring Keep changes."""
        previous=getattr(self,'_last_auto_patterns',[])
        if (not previous or self.auto_role.currentData()!=getattr(self,'_last_auto_role',None)
                or len(self.patterns)<len(previous)):
            return None
        latest=self.patterns[-len(previous):]
        if all(self._same_generated_pattern(a,b) for a,b in zip(latest,previous)):
            return latest
        return None

    def _can_randomize(self):
        latest=self._active_auto_batch()
        return bool(latest and any(not p.get('auto_keep',False) for p in latest))

    def _update_randomize_button(self):
        if hasattr(self,'auto_random'):
            self.auto_random.setEnabled(self._can_randomize())

    def _on_keep_check_changed(self,item):
        """Persist Keep and lock matching mirror partners as one design unit."""
        index=self.pattern_list.row(item)
        if not 0<=index<len(self.patterns):return
        group=self.patterns[index].get('auto_group','')
        if not group:return
        locked=item.checkState()==QtCore.Qt.Checked
        targets=[i for i,p in enumerate(self.patterns) if p.get('auto_group')==group]
        old=[self.patterns[i].get('auto_keep',False) for i in targets]
        for i in targets:self.patterns[i]['auto_keep']=locked
        try:value=encode_patterns(self.patterns)
        except ValueError as exc:
            for i,state in zip(targets,old):self.patterns[i]['auto_keep']=state
            self.show_error(str(exc))
            return
        self.pattern_list.blockSignals(True)
        try:
            for i in targets:
                self.pattern_list.item(i).setCheckState(
                    QtCore.Qt.Checked if locked else QtCore.Qt.Unchecked)
                self.pattern_list.item(i).setText(self.pattern_text(i))
        finally:self.pattern_list.blockSignals(False)
        # Checkbox edits do not change cutout geometry: do not rebuild the
        # preview records or run complete frame validation on every click.
        self.metadataChanged.emit(value)
        self._update_randomize_button()
        self.status.setText(
            ('Kept' if locked else 'Released')+f' {len(targets)} generated opening(s). '+
            ('Randomize will retain them.' if locked else 'Randomize may replace them.'))

    def generate_automatic(self,*args,randomize=False):
        """Generate varied local cutouts with a bounded, clearance-safe search.

        The former web-first method constructed huge, deeply tessellated Qt
        boolean paths at 40x scale and then repeatedly simplified their
        largest regions.  Once Keep occupied much of the mask, that could
        spend seconds retrying contours that could never pass a clearance
        check.  This routine instead proposes many SMALL independent cells
        in empty bays; exact Qt CNC profiles are validated locally.
        """
        if getattr(self,'_auto_generating',False):
            return
        if randomize and not self._can_randomize():
            self._update_randomize_button()
            self.status.setText('Generate a design before Randomize, or release one of its kept openings.')
            return
        if not self.require_applied():
            return
        import time
        started=time.perf_counter()
        from .airflow_auto import AUTO_ROLES
        from .airflow_fast import iter_design_candidates, mirror_candidate
        from .parameters import plate_holes,standoff_layouts,keystone_retainers
        from .tpu_mount_layout import carbon_rim_centres
        from .cutouts import MAX_PATTERNS,MAX_ENABLED_CUTOUTS
        import secrets
        from dataclasses import replace
        role=self.auto_role.currentData()
        if role not in AUTO_ROLES:
            self.show_error('Choose a main or clamp carbon plate for automatic airflow cutouts.')
            return
        self._auto_generating=True
        self.auto_generate.setEnabled(False)
        self.auto_random.setEnabled(False)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            p=self.get_parameters()
            previous=self._active_auto_batch()
            if previous is not None:
                replace_previous=True
                retained=[dict(v) for v in previous if v.get('auto_keep',False)]
                working=self.patterns[:-len(previous)]+retained
            else:
                # Reloaded FCStd projects do not have an active editor batch.
                # Only automatic cutouts for this role are replaceable.
                prior=[v for v in self.patterns if v['role']==role and v.get('auto_group')]
                replace_previous=bool(prior)
                retained=[dict(v) for v in prior if v.get('auto_keep',False)]
                working=([v for v in self.patterns
                          if v['role']!=role or not v.get('auto_group')]+retained
                         if prior else list(self.patterns))

            remaining_slots=min(
                MAX_PATTERNS-len(working),
                MAX_ENABLED_CUTOUTS-sum(pattern_cut_count(v) for v in working
                                        if v['enabled']))
            if remaining_slots<1:
                raise ValueError('Airflow cutout capacity reached. Remove or disable a pattern.')

            required_web=max(float(self.auto_web.currentData()),p.MinimumWeb)
            mirrored=self.auto_layout.currentText()=='Mirrored'
            # Use only added material when constructing the plate silhouette.
            # Existing cutouts, INCLUDING kept cutouts, are spatial obstacles,
            # not subtractions from this cached baseline.  This distinction
            # prevents a growing number of kept cells from making the outline
            # computation and plate erosion progressively more complex.
            additions=[v for v in working if v['role']==role and v['enabled']
                       and v['mode']=='Add material']
            material_key=json.dumps(
                [{k:v for k,v in item.items() if k not in ('auto_keep','auto_group','pad_insert')}
                 for item in additions],sort_keys=True,separators=(',',':'))
            plate_key=(replace(p,CutoutPatterns='[]'),role,material_key,required_web)
            cached=getattr(self,'_auto_fast_plate_cache',None)
            if cached is not None and cached[0]==plate_key:
                base,usable,bounds=cached[1:]
            else:
                # Qt's boolean tessellation stays accurate at 12x while its
                # operations are dramatically smaller than the old 40x
                # global skeleton/rounding chain.  The *manufacturing*
                # geometry remains analytic R0.5 FreeCAD geometry.
                factor=12.
                transform=QtGui.QTransform();transform.scale(factor,factor)
                base=transform.map(finished_part_path(p,role,additions))
                bounds=base.boundingRect()
                if base.isEmpty() or bounds.isEmpty():
                    raise ValueError('The chosen plate has no usable carbon profile.')
                rim=QtGui.QPainterPathStroker()
                rim.setWidth(2*(required_web+.20)*factor)
                rim.setJoinStyle(QtCore.Qt.RoundJoin)
                rim.setCapStyle(QtCore.Qt.RoundCap)
                usable=base.subtracted(rim.createStroke(base))
                # The editor has at most one cache entry; an updated frame or
                # a different Minimum web releases the previous large path.
                self._auto_fast_plate_cache=(plate_key,base,usable,bounds)
            if usable.isEmpty():
                self.status.setText('No room for cutouts at this carbon-web width; the plate is unchanged.')
                return

            factor=12.
            scale=QtGui.QTransform();scale.scale(factor,factor)
            margin=(required_web+.20)*factor
            cell_size=max(15.,2*required_web+7.)*factor
            # Uniform-grid broad phase: look only at obstacles that could
            # physically touch the candidate.  Its cost is independent of the
            # number of Keep openings on the opposite end of the plate.
            buckets={}
            obstacles=[]
            def grid_cells(rect):
                x0=int(math.floor(rect.left()/cell_size))
                x1=int(math.floor(rect.right()/cell_size))
                y0=int(math.floor(rect.top()/cell_size))
                y1=int(math.floor(rect.bottom()/cell_size))
                for ix in range(x0,x1+1):
                    for iy in range(y0,y1+1):
                        yield (ix,iy)
            def add_obstacle(path):
                if path.isEmpty():return
                rect=path.boundingRect()
                index=len(obstacles)
                obstacles.append((path,rect))
                for cell in grid_cells(rect):
                    buckets.setdefault(cell,[]).append(index)
            def close_obstacles(rect):
                ids=set()
                for cell in grid_cells(rect):
                    ids.update(buckets.get(cell,()))
                return (obstacles[i][0] for i in ids
                        if obstacles[i][1].intersects(rect))

            def keep_disc(point,radius):
                path=QtGui.QPainterPath()
                path.addEllipse(QtCore.QPointF(point[0]*factor,point[1]*factor),
                                radius*factor,radius*factor)
                add_obstacle(path)
            # Protect real mounting footprints, not only their drill holes.
            for point,radius,name in plate_holes(p,role):
                r=max(radius,3.0 if name in ('arm root','stack') else radius)
                if name in ('arm root','stack'):r+=.5
                keep_disc(point,r)
            for stand in standoff_layouts(p):
                carrier={'Bottom plate':'BottomPlate','Mid plate':'MidPlate',
                         'Arm clamp plate':'ArmClampPlate','Arm top':None}.get(stand['mount'])
                if role=='TopPlate' or role==carrier:
                    keep_disc(stand['point'],p.StandoffDiameter*.5)
            if role in ('BottomPlate','ArmClampPlate'):
                for ret in keystone_retainers(p):
                    keep_disc(ret['point'],max(ret['head_diameter']*.5,ret['bore']))
            for point,radius in carbon_rim_centres(p,role):
                keep_disc(point,radius)
            from .screw_heads import countersink_specs
            for seat in countersink_specs(p,role):
                keep_disc(seat['point'],seat['head_diameter']/2)
            for item in working:
                if item['enabled'] and item['role']==role and item['mode']!='Add material':
                    for instance in pattern_instances(item):
                        add_obstacle(scale.map(cutout_path(instance,p.CNCToolRadius)))

            # One pen is reused for the entire batch; no repeated full-plate
            # union, stroke or topology conversion during individual attempts.
            inflator=QtGui.QPainterPathStroker()
            inflator.setWidth(2*margin)
            inflator.setCapStyle(QtCore.Qt.RoundCap)
            inflator.setJoinStyle(QtCore.Qt.RoundJoin)
            usable_box=usable.boundingRect()
            candidate_new=[]
            kept_groups=len({v['auto_group'] for v in retained if v.get('auto_group')})
            plate_height=bounds.height()/factor
            detail=self.auto_density.currentText()
            pitch={'Sparse':32.,'Balanced':22.,'Detailed':15.}.get(detail,22.)
            target_groups=max(1,min(18,round(plate_height/pitch))-kept_groups)
            accepted_groups=0
            trials=0
            # A fixed attempt ceiling avoids hangs when Keep has filled the
            # available area; later passes use progressively smaller shapes.
            for item in iter_design_candidates(
                    (bounds.left()/factor,bounds.top()/factor,
                     bounds.width()/factor,bounds.height()/factor),
                    role,self.auto_style.currentText(),detail,
                    self.auto_layout.currentText(),required_web,
                    secrets.randbits(64),self.auto_shape_mix.currentText(),
                    max_attempts=150):
                trials+=1
                if accepted_groups>=target_groups or len(candidate_new)>=remaining_slots:
                    break
                central=mirrored and abs(item['x'])<1e-3
                # The centre of the plate may differ slightly from zero in a
                # translated CAD design; the generator uses the same rule.
                axis=0. if bounds.left()<=0<=bounds.right() else bounds.center().x()/factor
                central=mirrored and abs(item['x']-axis)<1e-3
                if central:
                    # A solitary centre cell must itself be mirror symmetric.
                    # Zero rotation and only use Y-symmetric manual contours.
                    safe_central=('Slot','Rounded rectangle','Ellipse','Diamond',
                                  'Hexagon','Kite','Shield','Triangle','Trapezoid')
                    if item['shape'] not in safe_central:
                        item=dict(item,shape='Diamond',vertices=[])
                    item['rotation']=0.
                    members=[item]
                elif mirrored:
                    partner=mirror_candidate(item,axis)
                    if partner is None:continue
                    members=[item,partner]
                else:
                    members=[item]
                if len(candidate_new)+len(members)>remaining_slots:
                    continue
                shaped=[]
                group_ok=True
                for part in members:
                    part['auto_web']=float(self.auto_web.currentData())
                    if self.auto_operation.currentIndex()==1:
                        part['mode']='Pocket'
                        part['depth']=min(self.auto_depth.value(),
                                          self._plate_thickness(role)*.5)
                    # The analytic shape fits inside its rotated width/length
                    # box. Reject candidates outside the eroded plate before
                    # constructing any rounded arcs or Qt path topology.
                    radians=math.radians(part['rotation'])
                    dx=(abs(part['width']*math.cos(radians))+
                        abs(part['length']*math.sin(radians)))*factor*.5
                    dy=(abs(part['width']*math.sin(radians))+
                        abs(part['length']*math.cos(radians)))*factor*.5
                    centre_x,centre_y=part['x']*factor,part['y']*factor
                    approx=QtCore.QRectF(centre_x-dx,centre_y-dy,2*dx,2*dy)
                    if not usable_box.contains(approx):
                        group_ok=False;break
                    try:
                        outline=scale.map(cutout_path(part,p.CNCToolRadius))
                    except (ValueError, TypeError, ArithmeticError):
                        group_ok=False;break
                    rect=outline.boundingRect()
                    if (outline.isEmpty() or not usable_box.contains(rect)
                            or rect.width()<factor or rect.height()<factor):
                        group_ok=False;break
                    # Only inflate when something is actually close enough.
                    padded=rect.adjusted(-margin,-margin,margin,margin)
                    neighbours=list(close_obstacles(padded))
                    neighbours.extend(prev for prev,_ in shaped
                                      if prev.boundingRect().intersects(padded))
                    if neighbours:
                        inflated=outline.united(inflator.createStroke(outline))
                        if any(self._qt_path_has_area(inflated.intersected(previous))
                               for previous in neighbours):
                            group_ok=False;break
                    # The complex full-plate Boolean is last; most proposals
                    # rejected by kept cutouts/hardware never reach it.
                    if self._qt_path_has_area(outline.subtracted(usable)):
                        group_ok=False;break
                    shaped.append((outline,rect))
                if not group_ok:
                    continue
                group_id=secrets.token_hex(8)
                for part,(outline,_) in zip(members,shaped):
                    part['auto_group']=group_id
                    part['auto_keep']=False
                    candidate_new.append(part)
                    add_obstacle(outline)
                accepted_groups+=1

            if not candidate_new:
                self.status.setText(
                    f'No free area for additional cutter-radius cutouts after {trials} '
                    f'attempts ({time.perf_counter()-started:.2f} s). '
                    'Kept shapes and the existing design '
                    'were preserved. Try a narrower carbon web, release a '
                    'Keep opening, or choose a different plate.')
                return
            old=list(self.patterns)
            self.patterns=working+candidate_new
            if self.publish(len(self.patterns)-1):
                self._last_auto_patterns=[dict(v) for v in retained+candidate_new]
                self._last_auto_role=role
                self._update_randomize_button()
                detail_text='Replaced unlocked design' if replace_previous else 'Generated new design'
                self.status.setText(
                    f'{detail_text}: {len(candidate_new)} cutouts in '
                    f'{accepted_groups} groups ({trials} local candidates; '
                    f'{time.perf_counter()-started:.2f} s). '
                    f'{kept_groups} previous groups kept; cutter-radius profiles, '
                    f'{required_web:g} mm minimum web. Check plate cuts in CAD before export.')
            else:
                self.patterns=old
        except (ValueError,RuntimeError,TypeError,OverflowError) as exc:
            self.show_error(str(exc))
        except Exception as exc:
            import traceback
            traceback.print_exc()
            self.show_error('Airflow generation failed: '+str(exc))
        finally:
            self._auto_generating=False
            self.auto_generate.setEnabled(True)
            self._update_randomize_button()
            QtWidgets.QApplication.restoreOverrideCursor()

    def update_shape_controls(self, *args):
        arc = self.shape.currentText() == 'Arc slot'
        self.arc_angle_label.setVisible(arc)
        self.arc_angle.setVisible(arc)
        lettering=self.shape.currentText()=='Text'
        for control in (self.text_label,self.text_input,self.text_font_label,self.text_font,self.text_fit):control.setVisible(lettering)
        font=self.text_font.currentText()
        self.text_dot_label.setText('Stroke diameter' if font in ENGRAVING_FONTS else 'Dot diameter')
        for control in (self.text_dot_label,self.text_dot):control.setVisible(lettering and (font in ENGRAVING_FONTS or font=='Dot matrix'))
        runic=lettering and font==RUNE_FONT
        for mode in ('Interior','Outline notch','Add material'):
            item=self.mode.model().item(self.mode.findText(mode))
            if item is not None:item.setEnabled(not lettering or (runic and mode=='Interior'))
        if lettering and (not runic or self.mode.currentText() not in ('Pocket','Interior')):
            self.mode.setCurrentText('Pocket')
        self.mode.setEnabled(not lettering or runic)
        self.update_text_size_hint()

    def update_text_size_hint(self,*args):
        lettering=self.shape.currentText()=='Text'
        self.text_size_hint.setVisible(lettering)
        if not lettering:return
        item=dict(text=self.text_input.text().upper(),text_font=self.text_font.currentText(),text_dot=self.text_dot.value(),width=self.inputs['width'].value(),length=self.inputs['length'].value())
        try:
            web=self._lettering_web(item)
            width,height=minimum_text_size(item,web)
            # Rounded-up fit includes a small numerical allowance. Do not
            # generate cutter profiles while the user is still typing.
            suffix=(' — increase size or press Fit lettering.'
                    if item['width']<width-.021 or item['length']<height-.021 else '')
            self.text_size_hint.setText(f'Fit size: {width:.2f} × {height:.2f} mm{suffix}')
            self.text_size_hint.setStyleSheet('color: #a45b00;' if suffix else '')
        except ValueError as exc:
            self.text_size_hint.setText(str(exc));self.text_size_hint.setStyleSheet('color: #a45b00;')

    def _lettering_web(self,item):
        if item.get('text_font')!=RUNE_FONT or self.mode.currentText()!='Interior':return 0.
        p=self.get_parameters()
        index=getattr(self,'_selected_index',-1)
        stored=self.patterns[index].get('auto_web',0.) if 0<=index<len(self.patterns) else 0.
        return max(p.MinimumWeb,stored)

    def fit_lettering(self,*args):
        try:
            item=self.draft()
            web=self._lettering_web(item)
            diameter=2*self.get_parameters().CNCToolRadius
            if item['text_dot']<diameter:
                self.text_dot.setValue(diameter);item['text_dot']=diameter
            width,height=minimum_text_size(item,web)
            if width>200 or height>300:raise ValueError('Lettering exceeds the permitted cutout size. Shorten the text or use a smaller valid cutter diameter.')
            self.inputs['width'].setValue(width);self.inputs['length'].setValue(height)
        except ValueError as exc:self.show_error(str(exc))

    def draft(self):
        draft=dict(mode=self.mode.currentText(),role=self.role.currentData(),shape=self.shape.currentText(),enabled=self.enabled.isChecked(),mirror_u=self.mirror_u.isChecked(),mirror_v=self.mirror_v.isChecked(),**{k:c.value() for k,c in self.inputs.items()})
        if draft['shape']=='Text':
            draft['text']=self.text_input.text().upper();draft['text_font']=self.text_font.currentText();draft['text_dot']=self.text_dot.value()
            if draft['text_font']!=RUNE_FONT or draft['mode'] not in ('Interior','Pocket'):draft['mode']='Pocket'
        if draft['shape']=='Web cell':
            draft['vertices']=[list(v) for v in getattr(self,'_web_cell_vertices',[])]
        return draft

    def update_capacity(self):
        enabled=sum(pattern_cut_count(p) for p in self.patterns if p['enabled'])
        self.capacity.setText(f'Saved patterns: {len(self.patterns)} / {MAX_PATTERNS}   |   Enabled cuts: {enabled} / {MAX_ENABLED_CUTOUTS}')

    def has_pending_changes(self):
        draft=self.draft()
        return draft!=getattr(self,'_draft_baseline',draft)

    def update_pending_status(self,*args):
        if hasattr(self,'status') and self.has_pending_changes():
            self.status.setStyleSheet('color: #a45b00; font-weight: bold;')
            self.status.setText('Unapplied pattern changes. Press Add pattern to add a new cut, or Apply to pattern to replace the selected cut. Then check or update the frame.')

    def show_error(self,message):
        self.status.setStyleSheet('color: #b43737; font-weight: bold;')
        self.status.setText(message)
        QtWidgets.QMessageBox.warning(self,'Cutout pattern not saved',message)

    def discard_changes(self):
        p=dict(self._draft_baseline)
        self._web_cell_vertices=[list(v) for v in p.get('vertices',[])]
        self.role.setCurrentIndex(CUTOUT_ROLES.index(p['role']))
        self.shape.setCurrentText(p['shape']);self.mode.setCurrentText(p['mode']);self.enabled.setChecked(p['enabled'])
        self.mirror_u.setChecked(p.get('mirror_u',False));self.mirror_v.setChecked(p.get('mirror_v',False))
        self.text_input.setText(p.get('text','FPV'));self.text_font.setCurrentText(p.get('text_font',TEXT_FONTS[0]) if p['shape']=='Text' else ENGRAVING_FONTS[0]);self.text_dot.setValue(p.get('text_dot',1.) if p['shape']=='Text' else 1.)
        self.mode.setCurrentText(p['mode'])
        for k,c in self.inputs.items():c.setValue(p[k])
        self._draft_baseline=self.draft();self.status.setStyleSheet('')
        self.status.setText('Unapplied edits discarded. Saved patterns are unchanged.');self.preview.update()

    def require_applied(self):
        if self.has_pending_changes():
            self.show_error('The pattern controls have unapplied changes. Press Add pattern for a new cut, or Apply to pattern for the selected cut, before checking, saving or building the frame. Use Discard unapplied changes to keep the saved patterns.')
            return False
        return True

    def publish(self,select=-1,loaded_value=None):
        try:
            if loaded_value is None:
                value=encode_patterns(self.patterns)
                self.patterns=parse_patterns(value)
            else:
                # set_json already parsed/validated the saved input. Only
                # canonicalize it, not another round of schema validation.
                value=json.dumps(self.patterns,separators=(',',':'),allow_nan=False)
        except ValueError as exc:self.show_error(str(exc));return False
        self._patterns_revision+=1
        self.pattern_list.setUpdatesEnabled(False);self.pattern_list.blockSignals(True);self.pattern_list.clear()
        for i,p in enumerate(self.patterns):
            description=self.pattern_text(i)
            item=QtWidgets.QListWidgetItem(description)
            item.setToolTip(description+'\nRotation '+str(p['rotation'])+' degrees; grid '+str(p['columns'])+' x '+str(p['rows'])+'; pitch '+str(p['pitch_x'])+' / '+str(p['pitch_y'])+' mm'+
                            ('\nCheck Keep to retain this generated opening during Randomize. Mirrored partners share this setting.' if p.get('auto_group') else ''))
            if p.get('auto_group'):
                item.setFlags(item.flags()|QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Checked if p['auto_keep'] else QtCore.Qt.Unchecked)
            self.pattern_list.addItem(item)
        self._selected_index=-1
        self.pattern_list.setCurrentRow(select);self.pattern_list.blockSignals(False);self.pattern_list.setUpdatesEnabled(True)
        if select>=0:self.select_pattern(select,force=True)
        self.filter_patterns()
        self._draft_baseline=self.draft();self.update_capacity();self.status.setStyleSheet('')
        self.changed.emit(value);self.preview.update();self.status.setText('Pattern saved. Full CAD checks run on Create / Update, or use Check plate cuts in CAD.');self._update_randomize_button();return True

    def set_json(self,value):
        # Loaded designs are NOT assumed to have a rerollable session result.
        self._last_auto_patterns=[]
        self._last_auto_role=None
        self.patterns=parse_patterns(value);self.publish(loaded_value=value)

    def pattern_text(self,index):
        p=self.patterns[index]
        size=f"Ø{p['width']:g} mm" if p['shape']=='Circle' else f"{p['width']:g} × {p['length']:g} mm"
        label=(' · '+p['text']+' ('+p['text_font']+')') if p['shape']=='Text' else ''
        return f"#{index+1} · {ROLE_LABELS[p['role']]} · {p['mode']} · {p['columns']*p['rows']} × {p['shape']} · {size}"+label+(f" · bend {p['arc_angle']:g}°" if p['shape']=='Arc slot' else '')+f" · ({p['x']:g}, {p['y']:g})"+(f" · depth {p['depth']:g} mm" if p['mode']=='Pocket' else '')+(' [off]' if not p['enabled'] else '')+(' · Keep' if p.get('auto_keep') else '')+(' · LiPo insert' if p.get('pad_insert') else '')

    def filter_patterns(self,*args):
        tokens=self.find_pattern.text().casefold().split();role=self.filter_role.currentData();shown=0
        for i,p in enumerate(self.patterns):
            if not role or p['role']==role:
                description=self.pattern_text(i).casefold() if tokens else ''
                compact=description.replace('×','x').replace(' ','') if tokens else ''
                match=all((token=='#'+str(i+1)) if token.startswith('#') and token[1:].isdigit()
                          else (token in description or token.replace('×','x') in compact)
                          for token in tokens)
            else:match=False
            self.pattern_list.item(i).setHidden(not match);shown+=int(match)
        selected=self._selected_index
        suffix=(' · Selected #'+str(selected+1)+(' (hidden by filter)' if self.pattern_list.item(selected).isHidden() else '')) if 0<=selected<len(self.patterns) else ''
        self.filter_count.setText(str(shown)+' of '+str(len(self.patterns))+' patterns shown'+suffix)
        self.zoom_button.setEnabled(selected>=0 and not self.pattern_list.item(selected).isHidden())
        self.apply_button.setText('Apply to #'+str(selected+1) if selected>=0 else 'Apply to pattern')
        self.remove_button.setText('Remove #'+str(selected+1) if selected>=0 else 'Remove')
        self.preview.update()

    def choose_pattern(self,index):
        if index<0 or index>=len(self.patterns):return False
        if index!=self._selected_index and self.has_pending_changes():
            self.status.setText('Apply or discard your unapplied changes before selecting another pattern.');return False
        self.pattern_list.setCurrentRow(index);self.pattern_list.scrollToItem(self.pattern_list.item(index))
        return self._selected_index==index

    def select_pattern(self,index,force=False):
        if index<0 or index>=len(self.patterns):return False
        if not force and index==self._selected_index:return True
        if not force and self.has_pending_changes():
            self.pattern_list.blockSignals(True);self.pattern_list.setCurrentRow(self._selected_index);self.pattern_list.blockSignals(False)
            self.status.setText('Apply or discard your unapplied changes before selecting another pattern.');return False
        self._selected_index=index
        p=self.patterns[index]
        self._web_cell_vertices=[list(v) for v in p.get('vertices',[])]
        self.role.setCurrentIndex(CUTOUT_ROLES.index(p['role']))
        if self.shape.findText(p['shape'])<0:
            # Keep obsolete polygon profiles editable in older saved designs,
            # but never offer these sharp-corner types for new CNC openings.
            self.shape.addItem(p['shape'])
            item=self.shape.model().item(self.shape.findText(p['shape']))
            if item is not None:item.setEnabled(False)
        self.shape.setCurrentText(p['shape']);self.mode.setCurrentText(p['mode']);self.enabled.setChecked(p['enabled'])
        self.mirror_u.setChecked(p.get('mirror_u',False));self.mirror_v.setChecked(p.get('mirror_v',False))
        self.text_input.setText(p.get('text','FPV'));self.text_font.setCurrentText(p.get('text_font',TEXT_FONTS[0]) if p['shape']=='Text' else ENGRAVING_FONTS[0]);self.text_dot.setValue(p.get('text_dot',1.) if p['shape']=='Text' else 1.)
        self.mode.setCurrentText(p['mode'])
        for k,c in self.inputs.items():c.setValue(p[k])
        self._draft_baseline=self.draft();self.status.setStyleSheet('');self.status.setText('Selected #'+str(index+1)+'. Edit and press Apply to pattern, or Add pattern for a new cut.')
        self.filter_patterns();self.preview.update();return True

    def _check_lettering(self,item):
        if not item['enabled']:return True
        try:
            params=self.get_parameters()
            from .cutouts import check_cnc_shape
            check_cnc_shape(item,params.CNCToolRadius)
            if item['shape']!='Text':return True
            if item['role'] in CAMERA_ROLES and params.CameraCageStyle!='Carbon side plates':raise ValueError('CNC text requires carbon camera side plates.')
            check_text_web(item,0. if item['mode']=='Pocket' else max(params.MinimumWeb,item.get('auto_web',0.)))
        except ValueError as exc:self.show_error(str(exc));return False
        return True

    def add_pattern(self,*args):
        item=self.draft()
        if not self._check_lettering(item):return
        old=list(self.patterns);self.patterns.append(item)
        if not self.publish(len(self.patterns)-1):self.patterns=old

    def apply_pattern(self,*args):
        index=self._selected_index
        if index<0:self.status.setText('Select a saved pattern first, or press Add pattern.');return
        old=list(self.patterns);updated=self.draft()
        updated['auto_web']=self.patterns[index].get('auto_web',0.)
        updated['pad_insert']=self.patterns[index].get('pad_insert',False)
        if not self._check_lettering(updated):return
        if updated['shape']=='Web cell':updated['vertices']=[list(v) for v in self.patterns[index].get('vertices',[])]
        self.patterns[index]=updated
        if not self.publish(index):self.patterns=old

    def remove_pattern(self,*args):
        index=self._selected_index
        if index>=0:self.patterns.pop(index);self.publish(min(index,len(self.patterns)-1))

    def copy_camera(self,*args):
        pattern=self.draft();pattern['role']='CameraMountRight' if pattern['role']=='CameraMountLeft' else 'CameraMountLeft'
        if not self._check_lettering(pattern):return
        old=list(self.patterns);self.patterns.append(pattern)
        if not self.publish(len(self.patterns)-1):self.patterns=old

    def check_cad(self,*args):
        if not self.require_applied():return
        from .geometry import build_shapes,invalidate_failed_build
        invalidate_failed_build(self.get_parameters())
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            build_shapes(self.get_parameters());self.status.setText('CAD passed: each active part is connected; interior cuts preserve edge clearance and all cuts preserve fasteners and existing holes.')
        except Exception as exc:self.status.setText(str(exc))
        finally:QtWidgets.QApplication.restoreOverrideCursor()


_BLEND_PATH_CACHE={}

def blend_motor_junction_path(p,arm,path):
    if p.MotorPadBlendRadius<=1e-8 or abs(p.MotorPadRotation)<1e-8:return path
    key=(p.signature(),arm.get('name'),arm['root'],arm['motor'])
    if key in _BLEND_PATH_CACHE:return QtGui.QPainterPath(_BLEND_PATH_CACHE[key])
    # Flatten only the outer contour at 1/4 mm drawing tolerance; round inward
    # polygon junctions directly rather than stroking a large complementary area.
    transform=QtGui.QTransform();transform.scale(4,4)
    polygons=path.toSubpathPolygons(transform)
    def signed_area(poly):return sum(poly[i].x()*poly[(i+1)%len(poly)].y()-poly[(i+1)%len(poly)].x()*poly[i].y() for i in range(len(poly)))/2
    polygon=max(polygons,key=lambda poly:abs(signed_area(poly)))
    points=[(pt.x()/4,pt.y()/4) for pt in polygon]
    if math.dist(points[0],points[-1])<1e-8:points.pop()
    orientation=1 if signed_area(polygon)>0 else -1
    result=QtGui.QPainterPath();corners=[]
    ux,uy=motor_pad_unit(p,arm);mx,my=arm['motor']
    for i,b in enumerate(points):
        a,c=points[i-1],points[(i+1)%len(points)]
        l1,l2=math.dist(a,b),math.dist(b,c)
        if min(l1,l2)<1e-8:corners.append((b,b,None));continue
        u=((b[0]-a[0])/l1,(b[1]-a[1])/l1);v=((c[0]-b[0])/l2,(c[1]-b[1])/l2)
        cross=u[0]*v[1]-u[1]*v[0];angle=math.acos(max(-1.,min(1.,u[0]*v[0]+u[1]*v[1])))
        localx=(b[0]-mx)*ux+(b[1]-my)*uy
        if orientation*cross>=-1e-5 or angle<.12 or localx>p.ArmWidth or math.dist(b,arm['motor'])>p.MotorPadDiameter+p.ArmWidth:
            corners.append((b,b,None));continue
        d=min(p.MotorPadBlendRadius*math.tan(angle/2),.45*l1,.45*l2)
        radius=d/max(1e-10,math.tan(angle/2))
        first=(b[0]-d*u[0],b[1]-d*u[1]);last=(b[0]+d*v[0],b[1]+d*v[1])
        centre=(first[0]+orientation*u[1]*radius,first[1]-orientation*u[0]*radius)
        corners.append((first,last,(centre,radius)))
    result.moveTo(*corners[0][0])
    for first,last,arc in corners:
        result.lineTo(*first)
        if arc:
            centre,radius=arc;a=math.atan2(first[1]-centre[1],first[0]-centre[0]);b=math.atan2(last[1]-centre[1],last[0]-centre[0]);sweep=(b-a)%(2*math.pi)
            if orientation>0:sweep-=2*math.pi
            for j in range(1,9):
                t=a+sweep*j/8;result.lineTo(centre[0]+radius*math.cos(t),centre[1]+radius*math.sin(t))
        else:result.lineTo(*last)
    result.closeSubpath();result=path.united(result)
    if len(_BLEND_PATH_CACHE)>=32:_BLEND_PATH_CACHE.clear()
    _BLEND_PATH_CACHE[key]=QtGui.QPainterPath(result)
    return result

ROLE_LABELS.update({**{'MotorProtector'+name:'Motor protector '+name for name in ('FrontRight','FrontLeft','RearLeft','RearRight')},'ElectronicsGuardLeft':'Electronics guard left','ElectronicsGuardRight':'Electronics guard right'})

ROLE_LABELS['RearAntennaMount']='Rear antenna mount'

ROLE_LABELS['ELRSAntennaMount']='ELRS antenna mount'
