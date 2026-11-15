"""Tabbed camera side plates and rear VTX mounting coordinates (+Y front)."""
from .parameter_memo import parameter_cache
import math
from .flex import camera_inner
from .camera_cages import camera_thickness,shaped_wall,screw_cage

VIDEO_SYSTEMS = ("Analog", "Digital")
VTX_PATTERNS = ("20 x 20 mm", "25.5 x 25.5 mm", "Both (20 + 25.5 mm)")
CAMERA_WIDTHS = (("Nano 14 mm", 14), ("Micro 19 mm", 19), ("HD 20 mm", 20),
                 ("Mini 22 mm", 22), ("Full size 28 mm", 28))
CAMERA_ROLES = ("CameraMountLeft", "CameraMountRight")
CAMERA_PIVOT_MODES = ('Automatic centre', 'Custom height')
CAMERA_TILT_MECHANISMS = ('Dual arc slots', 'Upper pivot + lower arc')
CAMERA_POSITION_MODES = ('Automatic centre', 'Custom position')
CAMERA_BASE_MODES = ('Automatic', 'Custom')
FPV_FIELDS = {'CameraPhysicalProfile','CameraLensProjection','CameraSideScrewRearInset','CameraReferenceStyle','CameraViewProfile','CameraViewAspect','CameraViewFOV','CameraViewPupilOffset', "FPVEnabled", "VideoSystem", "CameraWidth", "CameraHeight", "CameraBodyDepth",
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


def camera_local_screws(p):
    """Exact screw pitch plus the camera-specific screw-line origin."""
    if p.FPVSystemProfile=='DJI O4 Air Unit Pro':
        from .o4_camera import side_screw_points
        return side_screw_points()
    from .camera_housing import screw_line_y
    y=screw_line_y(p.CameraBodyDepth,p.CameraSideScrewRearInset)
    if not p.CameraSideBoltSpacing:return ((y,0.),)
    half=p.CameraSideBoltSpacing/2
    return ((y,-half),(y,half))


def camera_centre_offset(p,tilt):
    """Translation keeping the real *upper* screw stationary in pivot mode."""
    if p.CameraMountMode!='Variable':return (0.,0.)
    # A one-screw camera is a friction pivot regardless of the two-screw
    # arc-slot mechanism selected by a previous camera preset. The camera
    # body must rotate around its actual off-centre screw, NOT its centre.
    if p.CameraSideBoltSpacing>0 and p.CameraTiltMechanism!='Upper pivot + lower arc':
        return (0.,0.)
    upper=camera_local_screws(p)[-1]
    a=math.radians(tilt);ref=math.radians(camera_reference_angle(p))
    def rotate(t):return (upper[0]*math.cos(t)-upper[1]*math.sin(t),
                          upper[0]*math.sin(t)+upper[1]*math.cos(t))
    y0,z0=rotate(ref);y,z=rotate(a)
    return y0-y,z0-z


def camera_screw_offsets(p,tilt):
    """True local Y/Z hole positions rotated around the camera body datum."""
    a=math.radians(tilt);c=math.cos(a);s=math.sin(a)
    return tuple((y*c-z*s,y*s+z*c) for y,z in camera_local_screws(p))


def camera_plate_length(p):
    reach=max(abs(camera_centre_offset(p,a)[0]+dy) for a in camera_angles(p)
              for dy,dz in camera_screw_offsets(p,a))
    length=p.CameraPlateLength
    return max(length,2*reach+p.CameraSideHoleDiameter+2*p.MinimumWeb+2)


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
    from .camera_housing import lens_dimensions,body_side_outline
    lens_r=10. if p.FPVSystemProfile=='DJI O4 Air Unit Pro' else lens_dimensions(p.CameraWidth,p.CameraHeight,p.VideoSystem=='Digital',p.CameraLensProjection,p.CameraPhysicalProfile)[0]
    pivot=camera_local_screws(p)[-1] if p.CameraTiltMechanism=='Upper pivot + lower arc' else (0.,0.)
    terms=[(y-pivot[0],z-pivot[1]) for y,z in
           (body_side_outline(p.CameraHeight,p.CameraBodyDepth,p.VideoSystem=='Digital',p.CameraPhysicalProfile)
            if p.FPVSystemProfile!='DJI O4 Air Unit Pro'
            else ((y,z) for y in (-p.CameraBodyDepth/2,p.CameraBodyDepth/2)
                  for z in (-p.CameraHeight/2,p.CameraHeight/2)))]
    from .camera_housing import lens_dimensions
    lens_length=(6. if p.FPVSystemProfile=='DJI O4 Air Unit Pro'
                 else lens_dimensions(p.CameraWidth,p.CameraHeight,p.VideoSystem=='Digital',p.CameraLensProjection,p.CameraPhysicalProfile)[1])
    terms += [(y-pivot[0],z-pivot[1]) for y in (p.CameraBodyDepth/2,p.CameraBodyDepth/2+lens_length)
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
    offset=camera_centre_offset(p,tilt)[1]
    if p.FPVSystemProfile=='DJI O4 Air Unit Pro':
        from .o4_camera import casing_side_outline, CASE_DEPTH,LENS_PROTRUSION
        body=[y*math.sin(angle)+z*math.cos(angle) for y,z in casing_side_outline()]
        # The lens is a cylinder (not the corner of a rectangular box).
        lens=[y*math.sin(angle)+dz for y in (CASE_DEPTH/2-.1,CASE_DEPTH/2+LENS_PROTRUSION)
              for dz in (-10*math.cos(angle),10*math.cos(angle))]
        return offset+min(body+lens),offset+max(body+lens)
    from .camera_housing import body_side_outline,lens_dimensions
    values=[y*math.sin(angle)+z*math.cos(angle)
            for y,z in body_side_outline(p.CameraHeight,p.CameraBodyDepth,p.VideoSystem=='Digital',p.CameraPhysicalProfile)]
    lens_r,lens_length=lens_dimensions(p.CameraWidth,p.CameraHeight,p.VideoSystem=='Digital',p.CameraLensProjection,p.CameraPhysicalProfile)
    values.extend(y*math.sin(angle)+z*math.cos(angle)
                  for y in (p.CameraBodyDepth/2-.1,p.CameraBodyDepth/2+lens_length)
                  for z in (-lens_r,lens_r))
    return offset+min(values),offset+max(values)


def camera_body_centre(p, tilt=None):
    dy,dz=camera_centre_offset(p,p.CameraTilt if tilt is None else tilt)
    return camera_position_y(p)+dy,p.BottomThickness+camera_pivot_height(p)+dz


@parameter_cache(maxsize=128)
def camera_pivot_height(p):
    """Height of the camera datum above the bottom plate (not a standoff).

    In a three-plate frame the front camera has the *whole* bottom-to-top
    cavity: bottom thickness + arm thickness + mid/clamp thickness + rear
    standoff, minus the bottom plate thickness.  ``camera_cage_height``
    already resolves that physical datum with ``plate_levels``.

    The O4 Pro's screws are close to the *front* of its asymmetric housing.
    Centring only their Z travel, as before v0.91.50, placed the much deeper
    rear half below the bottom plate at moderate tilts (even with a 30 mm
    cavity).  Place the *housing* first, keeping side screws inside their
    available vertical range.  The forward lens may pass a legitimate plate
    cutout; only the exact Part/BRep collision probe can decide that.
    """
    if p.CameraPivotMode != CAMERA_PIVOT_MODES[0]:
        return p.CameraPivotHeight
    height = camera_cage_height(p)
    if p.FPVSystemProfile != 'DJI O4 Air Unit Pro':
        return height/2

    from .o4_camera import casing_side_outline
    outline=casing_side_outline()
    body_low=float('inf');body_high=-float('inf')
    screw_low=float('inf');screw_high=-float('inf')
    for a in camera_angles(p):
        radians=math.radians(a);sin=math.sin(radians);cos=math.cos(radians)
        offset=camera_centre_offset(p,a)[1]
        for y,z in outline:
            value=offset+y*sin+z*cos
            body_low=min(body_low,value);body_high=max(body_high,value)
        for y,z in camera_screw_offsets(p,a):
            value=offset+z
            screw_low=min(screw_low,value);screw_high=max(screw_high,value)

    # Include the lens in the clearance envelope. At a steep tilt the O4
    # body may fit vertically while the lens projects below the lower plate.
    # The lens is a cylinder, so its vertical extremes are its centre +/-
    # radius; use the two axial ends to include the whole cylinder.
    from .o4_camera import CASE_DEPTH, LENS_PROTRUSION
    for a in camera_angles(p):
        theta=math.radians(a)
        offset=camera_centre_offset(p,a)[1]
        for y in (CASE_DEPTH/2-.1, CASE_DEPTH/2+LENS_PROTRUSION):
            centre=offset+y*math.sin(theta)
            radius=10.*abs(math.cos(theta))
            body_low=min(body_low,centre-radius)
            body_high=max(body_high,centre+radius)

    # Never modify carbon-fibre plates to solve a camera intersection.
    # Use the best legal vertical placement and leave the exact solid-to-solid
    # collision check intact if the camera genuinely cannot fit.
    margin=.1
    lower=-body_low+margin
    upper=height-body_high-margin
    radius=p.CameraSideHoleDiameter/2
    screw_lower=radius-screw_low
    screw_upper=height-radius-screw_high
    # Automatic centre refers to the *mounting pattern*, not the off-centre
    # camera housing datum. The screws move vertically as the O4 tilts.
    # Centre the complete screw travel, subject to actual housing clearance.
    screw_centre_target=(height-screw_low-screw_high)/2
    if lower<=upper:
        # Prefer the symmetric screw pattern, without sacrificing a casing
        # that can fit completely inside the real bottom-to-top cavity.
        best=max(lower,min(screw_centre_target,upper))
    else:
        # The camera is taller than the closed cavity at some tilt angles.
        # Prefer clearing the lower plate: the elevated forward lens can be
        # ahead of the top-plate nose, whereas the rear housing must remain
        # supported above the bottom plate. Do not silently machine a cutout.
        best=lower
    # Holes must still be supported inside the plate height. If the screw
    # range itself cannot fit, validation will issue a specific error.
    if screw_lower<=screw_upper:
        best=max(screw_lower,min(best,screw_upper))
    return best


def suggest_o4_soft_fit(p):
    """Return minimal *explicit* O4 insert/pad resize for the real cage.

    Only the editor's Fit camera action applies this suggestion: user-selected
    press-fit dimensions are never silently overwritten on preset load or
    during CAD generation.  Evaluate each candidate against the same true
    camera-side wall polygon used in validation, including screw travel.
    """
    if p.FPVSystemProfile!='DJI O4 Air Unit Pro' or p.FlexCameraMode=='Hard mount':
        return {}
    from dataclasses import replace
    from .cage_extensions import o4_tracks,track_points

    def candidates(value,minimum):
        count=int(math.ceil((value-minimum)/.25))
        return tuple(sorted({float(value),float(minimum)} |
               {round(max(minimum,value-i*.25),4) for i in range(max(0,count)+1)},reverse=True))

    if p.FlexCameraMode=='Captured inserts':
        for diameter in candidates(p.O4InsertDiameter,4.):
            # Respect minimum wall around the M2 fixing before trying shapes.
            if diameter/2-p.FlexInsertFit-p.CameraSideHoleDiameter/2<.8-1e-7:
                continue
            for lip in candidates(p.FlexInsertLip,.5):
                if diameter+2*lip>=p.CameraSideBoltSpacing-1e-7:
                    continue
                q=replace(p,O4InsertDiameter=diameter,FlexInsertLip=lip)
                radius=diameter/2+lip
                if all(min(camera_wall_interior(v,mount)
                           for tr in o4_tracks(mount) for v in track_points(tr))
                       >=radius+q.CameraCageEdgeWeb+.02
                       for mount in camera_mounts(q)):
                    return {'O4InsertDiameter':diameter,'FlexInsertLip':lip}
    else:
        for diameter in candidates(p.O4PadDiameter,4.):
            if diameter/2-p.CameraSideHoleDiameter/2<.8-1e-7:
                continue
            q=replace(p,O4PadDiameter=diameter)
            radius=diameter/2
            if all(min(camera_wall_interior(v,mount)
                       for tr in o4_tracks(mount) for v in track_points(tr))
                   >=radius+q.CameraCageEdgeWeb+.02
                   for mount in camera_mounts(q)):
                return {'O4PadDiameter':diameter}
    return {}


@parameter_cache(maxsize=128)
def camera_base_wall_centres(p):
    """Fit the independent upper/lower attachments inside the actual plates."""
    rear_extension,front_extension=camera_base_extensions(p)
    base_preferred=p.CameraPlateY+(front_extension-rear_extension)/2
    if not p.CameraFollowPlates:return base_preferred,p.CameraPlateY
    from .parameters import bottom_bounds,top_bounds,standoff_holes,strap_slots,stack_holes,arm_layouts,point_segment_distance,segment_distance
    from .plate_profiles import profiled_interior_distance
    bottom_length,top_length=camera_attachment_lengths(p)
    inner=camera_inner(p);x=inner+camera_thickness(p)/2
    if screw_cage(p):
        from .camera_cages import boss_x
        x=boss_x(p,1)
    r=camera_thickness(p)/2+p.CameraTabClearance;half=p.CameraTabLength/2+p.CameraTabClearance
    if screw_cage(p):r=1.6;half=0.
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
                       for xx in (inner,inner+camera_thickness(p))
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
    # TPU plate-contact and screw anchors are structural features. They must
    # remain stationary when a pad/insert changes the camera's X spacing.
    if screw_cage(p) and p.FlexCameraMode!='Hard mount':
        from dataclasses import replace
        base=replace(p,FlexCameraMode='Hard mount')
    else:
        base=p
    bottom,top=camera_base_wall_centres(base)
    return bottom,top-p.CameraTopRearOffset


def camera_position_y(p):
    if p.CameraPositionMode=='Custom position':return p.CameraMountY+p.CameraForeAftOffset
    # Use the *actual* upper and lower wall centres, including the tapered
    # upper rearward offset. The old calculation ignored CameraTopRearOffset.
    bottom,top=camera_wall_centres(p)
    midline=bottom+(top-bottom)*camera_pivot_height(p)/max(1e-9,camera_cage_height(p))
    if p.FPVSystemProfile=='DJI O4 Air Unit Pro':
        # DJI's M2 holes lie 16 mm forward of the rear face, not at the case
        # origin. Centre the real screw travel on the cage centreline rather
        # than centring the casing and leaving the attachment off-centre.
        angles=camera_angles(p)
        locations=[camera_centre_offset(p,a)[0]+dy
                   for a in angles for dy,dz in camera_screw_offsets(p,a)]
        midline-=(min(locations)+max(locations))/2
    return midline+p.CameraForeAftOffset


def camera_wall_interior(point,mount):
    from .plate_profiles import polygon_interior_distance
    return polygon_interior_distance(point,mount['wall_profile'])


def _travel_wall(p,base,cy,cz,holes,arcs):
    """Add a supported middle bearing lobe; keep both captured edges fixed."""
    if not p.CameraAutoExtend:return base
    from .plate_profiles import polygon_interior_distance
    if p.FPVSystemProfile=='DJI O4 Air Unit Pro' and p.FlexCameraMode!='Hard mount':
        r=(p.O4InsertDiameter/2+p.FlexInsertLip if p.FlexCameraMode=='Captured inserts' else p.O4PadDiameter/2)
        from .cage_extensions import o4_tracks,track_points
        centres=[v for track in o4_tracks(dict(side_holes=holes,side_arcs=arcs)) for v in track_points(track)]
        points=[(y+dy,z+dz) for y,z in centres for dy in (-r,r) for dz in (-r,r)]
    elif p.FlexCameraMode!='Hard mount':
        w,h=(p.FlexInsertWidth,p.FlexInsertHeight) if p.FlexCameraMode=='Captured inserts' else (p.FlexPadWidth,p.FlexPadHeight)
        lip=0.
        points=[(cy+dy,cz+dz) for dy in (-w/2-lip,w/2+lip) for dz in (-h/2-lip,h/2+lip)]
    else:
        centres=list(holes)
        for arc in arcs:
            angles=[arc['start'],arc['end']]+[a for a in range(-360,721,90) if arc['start']<a<arc['end']]
            centres.extend((arc['centre'][0]+arc['radius']*math.cos(math.radians(a)),arc['centre'][1]+arc['radius']*math.sin(math.radians(a))) for a in angles)
        r=p.CameraSideHoleDiameter/2
        points=[(y+dy,z+dz) for y,z in centres for dy in (-r,r) for dz in (-r,r)]
    if not points or all(polygon_interior_distance(v,base)>=p.CameraCageEdgeWeb-1e-6 for v in points):return base
    margin=p.CameraCageEdgeWeb+.05
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
    # The TPU cage's M3 positions and OUTER plate contours are independently
    # fixed. Only the inner wall is allowed to move for the selected camera
    # interface, including the compressed-pad thickness or insert seat.
    inner = camera_inner(p)
    length=camera_plate_length(p)
    bottom_length,top_length=camera_attachment_lengths(p)
    bottom_tab_offset=bottom_length/2-p.CameraTabLength/2-p.MinimumWeb-.5
    top_tab_offset=top_length/2-p.CameraTabLength/2-p.MinimumWeb-.5
    cy,cz=camera_position_y(p),p.BottomThickness+camera_pivot_height(p)
    spacing=p.CameraSideBoltSpacing;side_holes=();side_arcs=[]
    if p.CameraMountMode=='Fixed':
        side_holes=tuple((cy+dy,cz+dz) for dy,dz in camera_screw_offsets(p,p.CameraTilt))
    elif not spacing:
        # At the reference angle, the physical off-centre camera screw is
        # located here. Every tilt uses camera_centre_offset to keep it fixed.
        side_holes=tuple((cy+dy,cz+dz) for dy,dz in
                         camera_screw_offsets(p,camera_reference_angle(p)))
    elif p.CameraTiltMechanism=='Dual arc slots':
        # The O4 Pro screw line is ahead of the case centre, so both slot
        # radii are measured from its actual threaded-hole coordinates.
        side_arcs=[dict(centre=(cy,cz),radius=math.hypot(y,z),
                        start=math.degrees(math.atan2(z,y))+p.CameraTiltMin,
                        end=math.degrees(math.atan2(z,y))+p.CameraTiltMax,
                        width=p.CameraSideHoleDiameter) for y,z in camera_local_screws(p)]
    else:
        uy,uz=camera_screw_offsets(p,camera_reference_angle(p))[-1]
        pivot=(cy+uy,cz+uz)
        side_holes=(pivot,)
        side_arcs=[dict(centre=pivot,radius=spacing,start=270+p.CameraTiltMin,
                        end=270+p.CameraTiltMax,width=p.CameraSideHoleDiameter)]
    bottom_y,top_y=camera_wall_centres(p);z0=p.BottomThickness;z1=z0+camera_cage_height(p)
    wall_profile=((bottom_y-bottom_length/2,z0),(bottom_y+bottom_length/2,z0),
                  (top_y+top_length/2,z1),(top_y-top_length/2,z1))
    attachment_profile=wall_profile
    wall_profile=shaped_wall(p,wall_profile)
    # The plate-outline TPU cage has its own full-height surfaces.  Applying
    # the legacy flat-plate tilt-envelope convex hull here made soft modes
    # unexpectedly replace the outer silhouette with a huge rear fin.
    if not screw_cage(p):
        wall_profile=_travel_wall(p,wall_profile,cy,cz,side_holes,side_arcs)
    # TPU fasteners belong to the *finished carbon plates*, not the camera
    # side-profile endpoints.  Derive a stable default from the actual plate
    # front outline.  The four editable offsets then move only these fasteners;
    # changing TPU wall reach cannot drag the screw holes towards a plate edge.
    if screw_cage(p):
        from .parameters import bottom_bounds, top_bounds
        from .tpu_mount_layout import mounting_y
        bottom_anchor=mounting_y(p,'BottomPlate',p.BodyWidth,bottom_bounds(p))
        top_anchor=mounting_y(p,'TopPlate',p.TopWidth,top_bounds(p))
        bottom_screws=(bottom_anchor[0]+p.CameraTabBottomRearOffset,
                       bottom_anchor[1]+p.CameraTabBottomFrontOffset)
        top_screws=(top_anchor[0]+p.CameraTabTopRearOffset,
                    top_anchor[1]+p.CameraTabTopFrontOffset)
    else:
        bottom_screws=(bottom_y-bottom_tab_offset+p.CameraTabBottomRearOffset,
                       bottom_y+bottom_tab_offset+p.CameraTabBottomFrontOffset)
        top_screws=(top_y-top_tab_offset+p.CameraTabTopRearOffset,
                    top_y+top_tab_offset+p.CameraTabTopFrontOffset)
    mounts = []
    for role, sign in zip(CAMERA_ROLES, (-1, 1)):
        if screw_cage(p):
            # Exact plate-derived external wall X is fixed; ONLY the inside
            # camera-facing surface changes with camera clearance. The heat-
            # insert M3 datum is immutable under isolation/dimension edits.
            from .tpu_mount_layout import mounting_x, _socket_radius
            outer=mounting_x(p)+_socket_radius(p)+.35
            from .flex import tpu_structural_inner
            inner_face=tpu_structural_inner(p)
            plate_x=sorted((sign*inner_face,sign*outer))
        else:
            plate_x=sorted((sign*inner, sign*(inner+camera_thickness(p))))
        mounts.append(dict(role=role, plate_x=plate_x, plate_length=length,
                           bottom_length=bottom_length,top_length=top_length,
                           z0=z0,z1=z1,wall_profile=wall_profile,attachment_profile=attachment_profile,bottom_centre_y=bottom_y,top_centre_y=top_y,
                           tabs_y=bottom_screws,
                           top_tabs_y=top_screws,
                           side_holes=side_holes, side_arcs=side_arcs))
    return mounts



def camera_tab_reliefs(p, mount):
    """(Y, Z, radius) cutter circles tangent to, and entirely outside, each tab.
    Centres lie on the bearing edge, one radius away from the tab. Only
    the inboard semicircle removes wall stock; tab and socket sizes stay fixed.
    """
    if screw_cage(p) or not p.CameraTabReliefs:
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
        radius=camera_thickness(p)/2+p.CameraTabClearance
        if screw_cage(p):
            from .camera_cages import boss_x
            x=boss_x(p,-1 if x<0 else 1);half=0.;radius=1.6
        slots.extend(((x,y-half),(x,y+half),radius) for y in mount['top_tabs_y' if role=='TopPlate' else 'tabs_y'])
    return tuple(slots)


def vtx_holes(p):
    if not p.FPVEnabled:
        return ()
    if p.FPVSystemProfile=='DJI O4 Air Unit Pro':return tuple(((x,p.VTXOffsetY+y),1.1,25.5) for x in (-12.75,12.75) for y in (-12.75,12.75))
    patterns = []
    if p.VTXPattern != VTX_PATTERNS[1]:
        patterns.append((20., p.VTX20HoleDiameter))
    if p.VTXPattern != VTX_PATTERNS[0]:
        patterns.append((25.5, p.VTX25HoleDiameter))
    return tuple(((x, p.VTXOffsetY+y), diameter/2, spacing) for spacing, diameter in patterns
                 for x in (-spacing/2, spacing/2) for y in (-spacing/2, spacing/2))


def rear_platform_edge(p):
    """Rear extent required for fixing support, not the VTX housing outline.

    A VTX is allowed to overhang the carrier plate. Automatic deck sizing
    needs to support its mounting holes, including the edge material around
    them, rather than grow with the VTX's external package dimensions.
    """
    holes = vtx_holes(p)
    if not holes:
        return p.VTXOffsetY - p.VTXLength/2 - p.MinimumWeb
    return min(pt[1]-radius-p.MinimumWeb for pt,radius,_ in holes)


def vtx_mount_support_errors(p, distance):
    """Validate the fixing region independent of the electronic enclosure.

    The plate distance is the measured minimum edge clearance of the finished
    carrier (including its local supports). Every hole must have its requested
    web and the centre of the screw pattern must remain on the carrier.
    """
    holes = vtx_holes(p)
    if not holes:
        return []
    required = p.MinimumWeb
    tol = 1e-6
    if any(distance(pt,p) < radius+required-tol for pt,radius,_ in holes):
        return ['VTX mounting holes need full plate support and edge material; increase the mid rear reach (three plates), bottom rear reach (two plates), or carrier width. The VTX housing may extend beyond the plate.']
    cx=sum(pt[0] for pt,_,_ in holes)/len(holes)
    cy=sum(pt[1] for pt,_,_ in holes)/len(holes)
    if distance((cx,cy),p)<-tol:
        return ['The VTX mounting pattern needs a connected carrier beneath its centre; adjust the rear plate outline or mounting position.']
    return []


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
    if camera_thickness(p) < 1.5:
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
    if p.CameraSideScrewRearInset < 0 or p.CameraSideScrewRearInset > p.CameraBodyDepth:
        errors.append('Camera side screw line must lie between the rear and front housing faces.')
    if p.CameraLensProjection < 0 or p.CameraLensProjection > 50:
        errors.append('Camera lens projection must be between 0 and 50 mm.')
    if p.CameraSideBoltSpacing+p.CameraSideHoleDiameter > p.CameraHeight or p.CameraSideHoleDiameter>p.CameraBodyDepth:
        errors.append('The vertical side screw pattern extends outside the camera body; check vertical spacing, screw diameter and body height.')
    if p.FPVSystemProfile!='DJI O4 Air Unit Pro':
        # A full cuboid and a mandatory 0.2 mm margin falsely reject cameras
        # at 0 degrees (e.g. a nominal 22 mm T-Rex in a 22 mm opening) and
        # tilted housings passing through legitimate front plate cutouts.
        # The later exact BRep intersection test checks the *shaped housing*
        # and lens against real top/bottom plates and the camera-cage sides.
        # Do not turn a tight *possible* fit into a claim of impossible tilt.
        pass
    else:
        # The O4 Pro's lens and rounded housing can move through actual
        # carbon-plate cutouts. An axis-aligned rectangular envelope would
        # reject those builds before the exact camera/plate collision test.
        # Keep screw/insert/cage web checks and let the BRep collision tests
        # decide if the installed camera truly touches the carbon or cage.
        limits=[(camera_pivot_height(p)+camera_centre_offset(p,a)[1]+dz)
                for a in camera_angles(p) for dy,dz in camera_screw_offsets(p,a)]
        if min(limits)<p.CameraSideHoleDiameter/2 or max(limits)>camera_cage_height(p)-p.CameraSideHoleDiameter/2:
            errors.append('The O4 Pro camera mounting screw centres are outside the available cage height; raise the mounting position or increase plate spacing.')
    if screw_cage(p):
        from .tpu_mount_layout import fit_check
        issue=fit_check(p)
        if issue:errors.append(issue)
    mounts=camera_mounts(p)
    if any(not math.isfinite(getattr(p,k)) for k in TAB_OFFSET_FIELDS):errors.append('Camera tab offsets must be finite.')
    mount=mounts[0]
    for contact_role,ys,centre,length in (('BottomPlate',mount['tabs_y'],mount['bottom_centre_y'],mount['bottom_length']),('TopPlate',mount['top_tabs_y'],mount['top_centre_y'],mount['top_length'])):
        minimum_separation=(max(3.0+p.CameraTPUScrewClearance+2.15,
                             p.CameraTPUScrewBore+2*p.CameraTPUBossWall+1.4)
                        if screw_cage(p) else p.CameraTabLength+p.MinimumWeb)
        if ys[1]-ys[0]<minimum_separation-1e-7:
            errors.append(('TPU cage front and rear M3 heat-insert bosses overlap; increase their separation to at least %.2f mm or reset the mounting offsets to zero.' % minimum_separation)
                          if screw_cage(p) else 'Camera mounting offsets leave insufficient separation or reverse the front/rear positions.')
        if screw_cage(p):
            # TPU uses a through-plate M3 screw, not a long carbon tab. Allow
            # its front screw to approach within 2 mm of the drilled opening's
            # edge while retaining full carbon support around the screw.
            bore_radius=(3.0+p.CameraTPUScrewClearance)/2
            edge_margin=bore_radius+2.0
            # The finished carbon outline, rather than the obsolete side-plate
            # contact rectangle, determines whether an M3 fastener is supported.
            from .parameters import bottom_bounds, top_bounds
            from .plate_profiles import profiled_interior_distance
            from .camera_cages import boss_x
            is_bottom=contact_role=='BottomPlate'
            role=contact_role
            width=p.BodyWidth if is_bottom else p.TopWidth
            rear,front=(bottom_bounds(p) if is_bottom else top_bounds(p))
            if any(profiled_interior_distance((boss_x(p,1),y),p,role,width,rear,front,p.CornerRadius)<edge_margin-1.e-7 for y in ys):
                errors.append('TPU cage M3 mounting holes require 2 mm of carbon outside the hole on the finished '+('bottom' if is_bottom else 'top')+' plate.')
        elif any(y-p.CameraTabLength/2<centre-length/2-1e-7 or y+p.CameraTabLength/2>centre+length/2+1e-7 for y in ys):
            errors.append('Camera tab offsets must keep each tab within its side-plate contact edge.')
    if p.CameraTabReliefs and not screw_cage(p):
        for ys in (mounts[0]['tabs_y'],mounts[0]['top_tabs_y']):
            if abs(ys[1]-ys[0])-p.CameraTabLength < p.CameraTabCutterDiameter-1e-7:
                errors.append('Camera tab reliefs would reach a neighbouring tab; use a smaller cutter or lengthen the camera attachment edge.')
                break
    if not screw_cage(p) and min(y for y,z in mounts[0]['wall_profile']) <= p.StackOffsetY+p.StackSpacing/2+3+p.MinimumWeb:
        errors.append('Move the camera mounting area ahead of the electronics stack.')
    for y,z in (() if screw_cage(p) else mounts[0]['side_holes']):
        if camera_wall_interior((y,z),mounts[0]) < p.CameraSideHoleDiameter/2+p.CameraCageEdgeWeb-1e-7:
            errors.append('Camera side screw holes need more material above/below; adjust pivot height or plate spacing.')
    for arc in (() if screw_cage(p) else mounts[0]['side_arcs']):
        count=max(1,math.ceil(arc['end']-arc['start']))
        for a in (arc['start']+(arc['end']-arc['start'])*i/count for i in range(count+1)):
            y=arc['centre'][0]+arc['radius']*math.cos(math.radians(a))
            z=arc['centre'][1]+arc['radius']*math.sin(math.radians(a))
            if camera_wall_interior((y,z),mounts[0])<arc['width']/2+p.CameraCageEdgeWeb-1e-7:
                errors.append('The adjustment arc needs more side-plate material around its full range; fit taller standoffs or a longer side plate.')
    if p.CameraSideBoltSpacing and p.CameraMountMode=='Variable' and p.CameraTiltMechanism=='Dual arc slots':
        if p.CameraSideBoltSpacing/2<=p.CameraSideHoleDiameter/2:errors.append('Dual arc slot radius must exceed half the side screw diameter.')
        if p.CameraSideBoltSpacing*math.cos(math.radians(p.CameraTiltMax-p.CameraTiltMin)/2)<p.CameraSideHoleDiameter+p.MinimumWeb-1e-6:
            errors.append('Dual arc slots leave too little material between their ends; increase measured screw spacing or reduce the tilt range.')
    if p.VTXOffsetY+p.VTXLength/2 > min(0, p.StackOffsetY-p.StackSpacing/2-3-p.MinimumWeb):
        errors.append('Move the VTX farther rearward to clear the electronics stack.')
    from .parameters import top_interior_distance, bottom_interior_distance, mid_interior_distance, three_plate, plate_levels
    if any(bottom_interior_distance((x,y),p)<p.MinimumWeb-1e-6
           for mount in mounts for x in (mount['plate_x'] if not screw_cage(p) else (sum(mount['plate_x'])/2,))
           for y,z in (mount['attachment_profile'][:2] if not screw_cage(p) else tuple((y,mount['z0']) for y in mount['tabs_y']))):
        errors.append('The lower camera attachment needs full support on the bottom plate; reduce its extensions, move the preferred side-plate centre, or increase bottom reach/width.')
    if p.CameraTopRearOffset>0 and any(top_interior_distance((x,y),p)<p.MinimumWeb-1e-6 for mount in mounts for x in mount['plate_x'] for y,z in mount['attachment_profile'][2:]):
        errors.append('The shifted upper camera attachment needs full top-plate support; reduce its rearward offset or adjust the top outline.')
    support=mid_interior_distance if three_plate(p) else bottom_interior_distance
    # Only the screw pattern and its bearing material need carbon support.
    # Body overhang across the left/right/rear outline is permitted; the
    # top plate is a cover, not a second VTX mounting surface.
    errors.extend(vtx_mount_support_errors(p,support))
    if vtx_deck_z(p)+p.VTXHeight > plate_levels(p)['top_z']-.2:
        # A tall body entirely beyond the top-plate outline is not trapped
        # under the cover. Sample the overlapping rectangle before rejecting.
        xmin,xmax=-p.VTXWidth/2,p.VTXWidth/2
        ymin,ymax=p.VTXOffsetY-p.VTXLength/2,p.VTXOffsetY+p.VTXLength/2
        samples=[(xmin+(xmax-xmin)*i/8,ymin+(ymax-ymin)*j/8)
                 for i in range(9) for j in range(9)]
        if any(top_interior_distance(pt,p)>0 for pt in samples):
            errors.append('The VTX overlaps the top plate vertically; increase frame height, lower the VTX, or move its housing outside the cover.')
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
