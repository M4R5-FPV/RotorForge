"""Tabbed camera side plates and rear VTX mounting coordinates (+Y front)."""
from .parameter_memo import parameter_cache
import math
from .flex import camera_inner

VIDEO_SYSTEMS = ("Analog", "Digital")
VTX_PATTERNS = ("20 x 20 mm", "25.5 x 25.5 mm", "Both (20 + 25.5 mm)")
CAMERA_WIDTHS = (("Nano 14 mm", 14), ("Micro 19 mm", 19), ("HD 20 mm", 20),
                 ("Mini 22 mm", 22), ("Full size 28 mm", 28))
CAMERA_ROLES = ("CameraMountLeft", "CameraMountRight")
CAMERA_PIVOT_MODES = ('Automatic centre', 'Custom height')
CAMERA_TILT_MECHANISMS = ('Dual arc slots', 'Upper pivot + lower arc')
CAMERA_POSITION_MODES = ('Automatic centre', 'Custom position')
CAMERA_BASE_MODES = ('Automatic', 'Custom')
FPV_FIELDS = {"FPVEnabled", "VideoSystem", "CameraWidth", "CameraHeight", "CameraBodyDepth",
              "CameraSideClearance", "CameraSideHoleDiameter", "CameraSideBoltSpacing",
              "CameraMountY", "CameraPivotHeight", "CameraTilt", "CameraBracketThickness",
              "CameraMountHoleDiameter", "VTXPattern", "VTXOffsetY", "VTX20HoleDiameter",
              "VTX25HoleDiameter", "VTXWidth", "VTXLength", "VTXHeight",
              "CameraPivotMode", "CameraPlateLength", "CameraTabLength", "CameraTabClearance"}
FPV_FIELDS |= {'CameraMountMode', 'CameraTiltMin', 'CameraTiltMax'}
FPV_FIELDS |= {'CameraTiltMechanism', 'CameraPositionMode', 'CameraFollowPlates', 'CameraPlateY'}
FPV_FIELDS |= {'CameraTopRearOffset','CameraForeAftOffset','CameraAutoExtend'}
FPV_FIELDS |= {'CameraTabReliefs','CameraTabCutterDiameter'}
FPV_FIELDS |= {'CameraBaseMode', 'CameraBaseFrontExtension', 'CameraBaseRearExtension'}
TAB_OFFSET_FIELDS=('CameraTabBottomRearOffset', 'CameraTabBottomFrontOffset', 'CameraTabTopRearOffset', 'CameraTabTopFrontOffset')
FPV_FIELDS.update(TAB_OFFSET_FIELDS)


def camera_reference_angle(p):
    return (p.CameraTiltMin+p.CameraTiltMax)/2 if p.CameraMountMode=='Variable' else p.CameraTilt


def camera_centre_offset(p,tilt):
    if p.CameraMountMode!='Variable' or p.CameraTiltMechanism!='Upper pivot + lower arc':return (0.,0.)
    a=math.radians(tilt);ref=math.radians(camera_reference_angle(p));half=p.CameraSideBoltSpacing/2
    return half*(math.sin(a)-math.sin(ref)),half*(math.cos(ref)-math.cos(a))


def camera_screw_offsets(p,tilt):
    """Side screw centres relative to the body centre: vertical at zero tilt."""
    if not p.CameraSideBoltSpacing:return ((0.,0.),)
    a=math.radians(tilt);half=p.CameraSideBoltSpacing/2
    return tuple((-t*math.sin(a),t*math.cos(a)) for t in (-half,half))


def camera_plate_length(p):
    reach=max(abs(camera_centre_offset(p,a)[0]+dy) for a in camera_angles(p)
              for dy,dz in camera_screw_offsets(p,a))
    return max(p.CameraPlateLength,2*reach+p.CameraSideHoleDiameter+2*p.MinimumWeb+2)


def camera_base_extensions(p):
    """Extra lower contact length, ordered rear/front (+Y is front)."""
    if p.CameraBaseMode=='Custom':
        return p.CameraBaseRearExtension,p.CameraBaseFrontExtension
    return 0.,0.


def camera_attachment_lengths(p):
    """Independent lower/upper contact lengths; extensions only widen the base."""
    length=camera_plate_length(p)
    rear,front=camera_base_extensions(p)
    return length+rear+front,length


def camera_angles(p, step=2.):
    if p.CameraMountMode=='Fixed':
        return (p.CameraTilt,)
    lo,hi=p.CameraTiltMin,p.CameraTiltMax
    if not 0<=lo<=hi<=60:
        return (p.CameraTilt,)
    count=max(1,math.ceil((hi-lo)/step))
    # Critical vertical extrema of the cuboid and approximate lens are also
    # checked, rather than relying only on angular sampling for floor/roof.
    lens_r=min(6,p.CameraWidth*.35,p.CameraHeight*.35)
    pivot=p.CameraSideBoltSpacing/2 if p.CameraTiltMechanism=='Upper pivot + lower arc' else 0.
    terms=[(y,z-pivot) for y in (-p.CameraBodyDepth/2,p.CameraBodyDepth/2)
           for z in (-p.CameraHeight/2,p.CameraHeight/2)]
    terms += [(y,z-pivot) for y in (p.CameraBodyDepth/2,p.CameraBodyDepth/2+6)
              for z in (-lens_r,lens_r)]
    extra=[math.degrees(math.atan2(a,b))%180 for a,b in terms]
    return tuple(sorted(set([lo+(hi-lo)*i/count for i in range(count+1)]+[a for a in extra if lo<=a<=hi])))


def camera_cage_height(p):
    from .parameters import plate_levels
    return plate_levels(p)['top_z']-p.BottomThickness



def camera_vertical_limits(p, tilt=None):
    if tilt is None:
        limits=[camera_vertical_limits(p,a) for a in camera_angles(p)]
        return min(v[0] for v in limits),max(v[1] for v in limits)
    angle=math.radians(tilt)
    body=(p.CameraHeight*math.cos(angle)+p.CameraBodyDepth*math.sin(angle))/2
    lens_r=min(6,p.CameraWidth*.35,p.CameraHeight*.35)
    offset=camera_centre_offset(p,tilt)[1]
    return (offset+min(-body,p.CameraBodyDepth/2*math.sin(angle)-lens_r*math.cos(angle)),
            offset+max(body,(p.CameraBodyDepth/2+6)*math.sin(angle)+lens_r*math.cos(angle)))


def camera_body_centre(p, tilt=None):
    dy,dz=camera_centre_offset(p,p.CameraTilt if tilt is None else tilt)
    return camera_position_y(p)+dy,p.BottomThickness+camera_pivot_height(p)+dz


def camera_pivot_height(p):
    return camera_cage_height(p)/2 if p.CameraPivotMode==CAMERA_PIVOT_MODES[0] else p.CameraPivotHeight


@parameter_cache(maxsize=128)
def camera_base_wall_centres(p):
    """Fit the independent upper/lower attachments inside the actual plates."""
    rear_extension,front_extension=camera_base_extensions(p)
    base_preferred=p.CameraPlateY+(front_extension-rear_extension)/2
    if not p.CameraFollowPlates:return base_preferred,p.CameraPlateY
    from .parameters import bottom_bounds,top_bounds,standoff_holes,strap_slots,stack_holes,arm_layouts,point_segment_distance,segment_distance
    from .plate_profiles import profiled_interior_distance
    bottom_length,top_length=camera_attachment_lengths(p)
    inner=camera_inner(p);x=inner+p.CameraBracketThickness/2
    r=p.CameraBracketThickness/2+p.CameraTabClearance;half=p.CameraTabLength/2+p.CameraTabClearance
    stands=standoff_holes(p);result=[]
    for role,bounds,width,length,desired in (
            ('BottomPlate',bottom_bounds(p),p.BodyWidth,bottom_length,base_preferred),
            ('TopPlate',top_bounds(p),p.TopWidth,top_length,p.CameraPlateY)):
        offset=length/2-p.CameraTabLength/2-p.MinimumWeb-.5
        rear,front=bounds;lo=rear+length/2+p.MinimumWeb;hi=front-length/2-p.MinimumWeb
        preferred=min(hi,max(lo,desired))
        def supported(centre):
            if (role=='BottomPlate' and p.BottomNoseShape!='Straight') or (role=='TopPlate' and p.TopFrontShape!='Straight'):
                # Slots alone can fit while a sloping/recessed nose removes the
                # wider side-plate foot. Follow the full contact footprint.
                if any(profiled_interior_distance((xx,yy),p,role,width,rear,front,p.CornerRadius)<p.MinimumWeb-1e-6
                       for xx in (inner,inner+p.CameraBracketThickness)
                       for yy in (centre-length/2,centre+length/2)):return False
            for y in (centre-offset,centre+offset):
                a,b=(x,y-half),(x,y+half)
                if min(profiled_interior_distance(pt,p,role,width,rear,front,p.CornerRadius) for pt in (a,b))<r+p.MinimumWeb-1e-6:return False
                if any(point_segment_distance(pt,a,b)<r+p.StandoffDiameter/2+p.MinimumWeb-1e-6 for pt in stands):return False
                if role=='TopPlate':
                    if any(segment_distance(a,b,c,d)<r+rr+p.MinimumWeb-1e-6 for c,d,rr in strap_slots(p)):return False
                else:
                    holes=[(pt,p.RootHoleDiameter/2) for arm in arm_layouts(p) for pt in arm['bolts']]
                    holes += [(pt,max(p.StackHoleDiameter,p.StackAccessDiameter)/2) for pt in stack_holes(p)]
                    if any(point_segment_distance(pt,a,b)<r+rr+p.MinimumWeb-1e-6 for pt,rr in holes):return False
            return True
        candidates=[preferred]
        for n in range(1,max(1,math.ceil(max(0,hi-lo)*4))+1):
            candidates.extend(c for c in (preferred-n*.25,preferred+n*.25) if lo<=c<=hi)
        result.append(next((c for c in candidates if supported(c)),preferred))
    return tuple(result)


def camera_wall_centres(p):
    bottom,top=camera_base_wall_centres(p)
    return bottom,top-p.CameraTopRearOffset


def camera_position_y(p):
    if p.CameraPositionMode=='Custom position':return p.CameraMountY+p.CameraForeAftOffset
    bottom,top=camera_base_wall_centres(p)
    return bottom+(top-bottom)*camera_pivot_height(p)/max(1e-9,camera_cage_height(p))+p.CameraForeAftOffset


def camera_wall_interior(point,mount):
    from .plate_profiles import polygon_interior_distance
    return polygon_interior_distance(point,mount['wall_profile'])


def _travel_wall(p,base,cy,cz,holes,arcs):
    """Add a supported middle bearing lobe; keep both captured edges fixed."""
    if not p.CameraAutoExtend:return base
    from .plate_profiles import polygon_interior_distance
    if p.FlexCameraMode!='Hard mount':
        w,h=(p.FlexInsertWidth,p.FlexInsertHeight) if p.FlexCameraMode=='Captured inserts' else (p.FlexPadWidth,p.FlexPadHeight)
        lip=p.FlexInsertLip if p.FlexCameraMode=='Captured inserts' else 0.
        points=[(cy+dy,cz+dz) for dy in (-w/2-lip,w/2+lip) for dz in (-h/2-lip,h/2+lip)]
    else:
        centres=list(holes)
        for arc in arcs:
            angles=[arc['start'],arc['end']]+[a for a in range(-360,721,90) if arc['start']<a<arc['end']]
            centres.extend((arc['centre'][0]+arc['radius']*math.cos(math.radians(a)),arc['centre'][1]+arc['radius']*math.sin(math.radians(a))) for a in angles)
        r=p.CameraSideHoleDiameter/2
        points=[(y+dy,z+dz) for y,z in centres for dy in (-r,r) for dz in (-r,r)]
    if not points or all(polygon_interior_distance(v,base)>=p.MinimumWeb-1e-6 for v in points):return base
    margin=p.MinimumWeb+.05
    lo,hi=min(z for y,z in points)-margin,max(z for y,z in points)+margin
    z0,z1=min(z for y,z in base),max(z for y,z in base)
    if lo<=z0+1e-6 or hi>=z1-1e-6:return base
    rear,front=min(y for y,z in points)-margin,max(y for y,z in points)+margin
    pts=sorted(set(base+tuple((y,z) for y in (rear,front) for z in (lo,hi))))
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    low=[];high=[]
    for seq,out in ((pts,low),(list(reversed(pts)),high)):
        for point in seq:
            while len(out)>1 and cross(out[-2],out[-1],point)<=1e-10:out.pop()
            out.append(point)
    return tuple(low[:-1]+high[:-1])


def camera_mounts(p):
    if not p.FPVEnabled:
        return []
    inner = camera_inner(p)
    length=camera_plate_length(p)
    bottom_length,top_length=camera_attachment_lengths(p)
    bottom_tab_offset=bottom_length/2-p.CameraTabLength/2-p.MinimumWeb-.5
    top_tab_offset=top_length/2-p.CameraTabLength/2-p.MinimumWeb-.5
    cy,cz=camera_position_y(p),p.BottomThickness+camera_pivot_height(p)
    spacing=p.CameraSideBoltSpacing;half=spacing/2;side_holes=();side_arcs=[]
    if p.CameraMountMode=='Fixed':
        side_holes=tuple((cy+dy,cz+dz) for dy,dz in camera_screw_offsets(p,p.CameraTilt))
    elif not spacing:side_holes=((cy,cz),)
    elif p.CameraTiltMechanism=='Dual arc slots':
        side_arcs=[dict(centre=(cy,cz),radius=half,start=p.CameraTiltMin+a,end=p.CameraTiltMax+a,width=p.CameraSideHoleDiameter) for a in (90,270)]
    else:
        ref=math.radians(camera_reference_angle(p));pivot=(cy-half*math.sin(ref),cz+half*math.cos(ref))
        side_holes=(pivot,);side_arcs=[dict(centre=pivot,radius=spacing,start=270+p.CameraTiltMin,end=270+p.CameraTiltMax,width=p.CameraSideHoleDiameter)]
    bottom_y,top_y=camera_wall_centres(p);z0=p.BottomThickness;z1=z0+camera_cage_height(p)
    wall_profile=((bottom_y-bottom_length/2,z0),(bottom_y+bottom_length/2,z0),
                  (top_y+top_length/2,z1),(top_y-top_length/2,z1))
    attachment_profile=wall_profile
    wall_profile=_travel_wall(p,wall_profile,cy,cz,side_holes,side_arcs)
    mounts = []
    for role, sign in zip(CAMERA_ROLES, (-1, 1)):
        plate_x = sorted((sign*inner, sign*(inner+p.CameraBracketThickness)))
        mounts.append(dict(role=role, plate_x=plate_x, plate_length=length,
                           bottom_length=bottom_length,top_length=top_length,
                           z0=z0,z1=z1,wall_profile=wall_profile,attachment_profile=attachment_profile,bottom_centre_y=bottom_y,top_centre_y=top_y,
                           tabs_y=(bottom_y-bottom_tab_offset+p.CameraTabBottomRearOffset,bottom_y+bottom_tab_offset+p.CameraTabBottomFrontOffset),
                           top_tabs_y=(top_y-top_tab_offset+p.CameraTabTopRearOffset,top_y+top_tab_offset+p.CameraTabTopFrontOffset),
                           side_holes=side_holes, side_arcs=side_arcs))
    return mounts



def camera_tab_reliefs(p, mount):
    """(Y, Z, radius) cutter circles tangent to, and entirely outside, each tab.
    Centres lie on the bearing edge, one radius away from the tab. Only
    the inboard semicircle removes wall stock; tab and socket sizes stay fixed.
    """
    if not p.CameraTabReliefs:
        return ()
    radius=p.CameraTabCutterDiameter/2
    return tuple((y+sign*(p.CameraTabLength/2+radius),z,radius)
                 for ys,z in ((mount['tabs_y'],mount['z0']),
                              (mount['top_tabs_y'],mount['z1']))
                 for y in ys for sign in (-1,1))


def camera_holes(p):
    # Kept for old integrations; tabbed plates replace the former base screws.
    return ()


def camera_slots(p,role='BottomPlate'):
    slots=[]
    for mount in camera_mounts(p):
        x=sum(mount['plate_x'])/2
        half=p.CameraTabLength/2+p.CameraTabClearance
        radius=p.CameraBracketThickness/2+p.CameraTabClearance
        slots.extend(((x,y-half),(x,y+half),radius) for y in mount['top_tabs_y' if role=='TopPlate' else 'tabs_y'])
    return tuple(slots)


def vtx_holes(p):
    if not p.FPVEnabled:
        return ()
    patterns = []
    if p.VTXPattern != VTX_PATTERNS[1]:
        patterns.append((20., p.VTX20HoleDiameter))
    if p.VTXPattern != VTX_PATTERNS[0]:
        patterns.append((25.5, p.VTX25HoleDiameter))
    return tuple(((x, p.VTXOffsetY+y), diameter/2, spacing) for spacing, diameter in patterns
                 for x in (-spacing/2, spacing/2) for y in (-spacing/2, spacing/2))


def rear_platform_edge(p):
    half_pattern = max(spacing/2 + radius for _, radius, spacing in vtx_holes(p))
    return p.VTXOffsetY - max(p.VTXLength/2, half_pattern) - p.MinimumWeb


def front_platform_edge(p,role='BottomPlate'):
    # Keep automatic reach independent of mounts, which use the final bounds.
    extra=camera_base_extensions(p)[1] if role=='BottomPlate' else 0.
    return p.CameraPlateY+camera_plate_length(p)/2+extra+p.MinimumWeb


def camera_floor(p):
    return camera_pivot_height(p)+camera_vertical_limits(p)[0]


def vtx_deck_z(p):
    from .parameters import plate_levels
    return plate_levels(p)['deck_z']


def rectangle_circle_gap(point, xmin, xmax, ymin, ymax, radius):
    dx=max(xmin-point[0], 0, point[0]-xmax)
    dy=max(ymin-point[1], 0, point[1]-ymax)
    return math.hypot(dx,dy)-radius


def validate_fpv(p, stands):
    if not p.FPVEnabled:
        return []
    errors=[]
    if not math.isfinite(p.CameraTopRearOffset) or p.CameraTopRearOffset<0:errors.append('Upper camera attachment rearward offset must be finite and non-negative.')
    if not 0 <= p.CameraTilt <= 60:
        errors.append('Camera tilt must be between 0 and 60 degrees.')
    if p.CameraMountMode=='Fixed' and p.CameraSideBoltSpacing<=0:
        errors.append('A fixed tilt needs two screws per camera side. Enter the measured side screw spacing, or choose Variable for a single-screw friction pivot.')
    if p.CameraMountMode=='Variable' and not 0<=p.CameraTiltMin<p.CameraTiltMax<=60:
        errors.append('Variable tilt range must satisfy 0 ≤ minimum < maximum ≤ 60 degrees.')
    if p.CameraMountMode=='Variable' and not p.CameraTiltMin<=p.CameraTilt<=p.CameraTiltMax:
        errors.append('Preview camera tilt must lie inside the variable tilt range.')
    if p.CameraSideClearance < 0 or p.CameraSideBoltSpacing < 0:
        errors.append('Camera clearance and side screw spacing cannot be negative.')
    if p.CameraBracketThickness < 1.5:
        errors.append('Camera side plate thickness must be at least 1.5 mm.')
    if p.CameraTabReliefs and (not math.isfinite(p.CameraTabCutterDiameter) or not .2 <= p.CameraTabCutterDiameter <= 6):
        errors.append('Camera tab cutter diameter must be between 0.2 and 6 mm.')
    if p.CameraTabClearance < 0:
        errors.append('Camera tab clearance cannot be negative.')
    if p.CameraBaseMode=='Custom' and min(p.CameraBaseFrontExtension,p.CameraBaseRearExtension)<0:
        errors.append('Camera lower attachment extensions cannot be negative.')
    if p.CameraPlateLength < 2*p.CameraTabLength+3*p.MinimumWeb+1:
        errors.append('Camera side plates are too short for two supported tabs; increase their length.')
    if p.CameraSideBoltSpacing and p.CameraSideBoltSpacing < p.CameraSideHoleDiameter+p.MinimumWeb:
        errors.append('Camera side screw holes are too close together; use zero for a single pivot screw.')
    if p.CameraSideBoltSpacing+p.CameraSideHoleDiameter > p.CameraHeight or p.CameraSideHoleDiameter>p.CameraBodyDepth:
        errors.append('The vertical side screw pattern extends outside the camera body; check vertical spacing, screw diameter and body height.')
    body_upper=max(camera_pivot_height(p)+camera_centre_offset(p,a)[1]+(p.CameraBodyDepth*math.sin(math.radians(a))+p.CameraHeight*math.cos(math.radians(a)))/2 for a in camera_angles(p))
    if camera_floor(p)<.2 or body_upper>camera_cage_height(p)-.2:
        errors.append('The camera does not clear the bottom and top over its tilt range; fit taller standoffs, centre its pivot, or reduce the range/body size. The lens may rise through the front cutout.')
    mounts=camera_mounts(p)
    if any(not math.isfinite(getattr(p,k)) for k in TAB_OFFSET_FIELDS):errors.append('Camera tab offsets must be finite.')
    mount=mounts[0]
    for ys,centre,length in ((mount['tabs_y'],mount['bottom_centre_y'],mount['bottom_length']),(mount['top_tabs_y'],mount['top_centre_y'],mount['top_length'])):
        if ys[1]-ys[0]<p.CameraTabLength+p.MinimumWeb-1e-7:errors.append('Camera tab offsets leave insufficient separation or reverse the front/rear tabs.')
        if any(y-p.CameraTabLength/2<centre-length/2-1e-7 or y+p.CameraTabLength/2>centre+length/2+1e-7 for y in ys):errors.append('Camera tab offsets must keep each tab within its side-plate contact edge.')
    if p.CameraTabReliefs:
        for ys in (mounts[0]['tabs_y'],mounts[0]['top_tabs_y']):
            if abs(ys[1]-ys[0])-p.CameraTabLength < p.CameraTabCutterDiameter-1e-7:
                errors.append('Camera tab reliefs would reach a neighbouring tab; use a smaller cutter or lengthen the camera attachment edge.')
                break
    if min(y for y,z in mounts[0]['wall_profile']) <= p.StackOffsetY+p.StackSpacing/2+3+p.MinimumWeb:
        errors.append('Move the camera mounting area ahead of the electronics stack.')
    for y,z in mounts[0]['side_holes']:
        if camera_wall_interior((y,z),mounts[0]) < p.CameraSideHoleDiameter/2+p.MinimumWeb:
            errors.append('Camera side screw holes need more material above/below; adjust pivot height or plate spacing.')
    for arc in mounts[0]['side_arcs']:
        count=max(1,math.ceil(arc['end']-arc['start']))
        for a in (arc['start']+(arc['end']-arc['start'])*i/count for i in range(count+1)):
            y=arc['centre'][0]+arc['radius']*math.cos(math.radians(a))
            z=arc['centre'][1]+arc['radius']*math.sin(math.radians(a))
            if camera_wall_interior((y,z),mounts[0])<arc['width']/2+p.MinimumWeb:
                errors.append('The adjustment arc needs more side-plate material around its full range; fit taller standoffs or a longer side plate.')
    if p.CameraSideBoltSpacing and p.CameraMountMode=='Variable' and p.CameraTiltMechanism=='Dual arc slots':
        if p.CameraSideBoltSpacing/2<=p.CameraSideHoleDiameter/2:errors.append('Dual arc slot radius must exceed half the side screw diameter.')
        if p.CameraSideBoltSpacing*math.cos(math.radians(p.CameraTiltMax-p.CameraTiltMin)/2)<p.CameraSideHoleDiameter+p.MinimumWeb-1e-6:
            errors.append('Dual arc slots leave too little material between their ends; increase measured screw spacing or reduce the tilt range.')
    if p.VTXOffsetY+p.VTXLength/2 > min(0, p.StackOffsetY-p.StackSpacing/2-3-p.MinimumWeb):
        errors.append('Move the VTX farther rearward to clear the electronics stack.')
    from .parameters import top_interior_distance, bottom_interior_distance, mid_interior_distance, three_plate, plate_levels
    if any(bottom_interior_distance((x,y),p)<p.MinimumWeb-1e-6
           for mount in mounts for x in mount['plate_x'] for y,z in mount['attachment_profile'][:2]):
        errors.append('The lower camera attachment needs full support on the bottom plate; reduce its extensions, move the preferred side-plate centre, or increase bottom reach/width.')
    if p.CameraTopRearOffset>0 and any(top_interior_distance((x,y),p)<p.MinimumWeb-1e-6 for mount in mounts for x in mount['plate_x'] for y,z in mount['attachment_profile'][2:]):
        errors.append('The shifted upper camera attachment needs full top-plate support; reduce its rearward offset or adjust the top outline.')
    support=mid_interior_distance if three_plate(p) else bottom_interior_distance
    # An explicit clearance opening permits lateral VTX overhang. Keep the
    # complete fore/aft deck, screw support and all exact assembly checks.
    from .protection_layout import guard_layout,guard_vtx_window
    overhang=set()
    if p.FlexSideGuards and p.FlexGuardVTXOpening:
        for guard in guard_layout(p):
            window=guard_vtx_window(p,guard)
            if window:
                cy,cz,w,h=window
                if (cy-w/2<=p.VTXOffsetY-p.VTXLength/2 and cy+w/2>=p.VTXOffsetY+p.VTXLength/2
                    and cz-h/2<=vtx_deck_z(p) and cz+h/2>=vtx_deck_z(p)+p.VTXHeight):
                    overhang.add(guard['sign'])
    def uncovered(distance,x,y):
        if distance((x,y),p)>=p.MinimumWeb-1e-6:return False
        return (1 if x>0 else -1) not in overhang or distance((0.,y),p)<p.MinimumWeb-1e-6
    if any(uncovered(support,x,y) for x in (-p.VTXWidth/2,p.VTXWidth/2)
           for y in (p.VTXOffsetY-p.VTXLength/2,p.VTXOffsetY+p.VTXLength/2)):
        errors.append('The VTX needs a complete rear mounting deck; increase the mid rear reach (three plates) or bottom rear reach (two plates).')
    if any(uncovered(top_interior_distance,x,y)
           for x in (-p.VTXWidth/2,p.VTXWidth/2)
           for y in (p.VTXOffsetY-p.VTXLength/2,p.VTXOffsetY+p.VTXLength/2)):
        errors.append('The top plate must cover the rear VTX footprint with edge material; increase top width or length.')
    if vtx_deck_z(p)+p.VTXHeight > plate_levels(p)['top_z']-.2:
        errors.append('The VTX does not clear the covering top plate; increase standoff height or reduce VTX height.')
    holes=vtx_holes(p)
    if p.VTXPattern==VTX_PATTERNS[2] and math.hypot(2.75,2.75)-(p.VTX20HoleDiameter+p.VTX25HoleDiameter)/2 < p.MinimumWeb:
        errors.append('The two VTX patterns leave too little material between adjacent holes; use smaller clearances or choose a single pattern.')
    for point, radius, _ in holes:
        if abs(point[0])+radius+p.MinimumWeb > p.VTXWidth/2 or abs(point[1]-p.VTXOffsetY)+radius+p.MinimumWeb > p.VTXLength/2:
            errors.append('VTX envelope is too small for its selected mounting pattern.')
    for stand in stands:
        point=stand['point']
        zmin=vtx_deck_z(p)
        if stand['base'] < zmin+p.VTXHeight and stand['base']+stand['length'] > zmin:
            if rectangle_circle_gap(point,-p.VTXWidth/2,p.VTXWidth/2,p.VTXOffsetY-p.VTXLength/2,
                                    p.VTXOffsetY+p.VTXLength/2,p.StandoffDiameter/2) < p.MinimumWeb:
                errors.append('The VTX footprint intersects a standoff; move the VTX rearward or reposition that pair.')
    return list(dict.fromkeys(errors))
