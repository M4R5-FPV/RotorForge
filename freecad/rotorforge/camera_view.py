"""Virtual FPV view using first-hit rays against generated FreeCAD geometry.

The optics use an *approximate* equidistant fisheye. Manufacturer maximum
FOVs are not calibrated lens maps and may differ from stabilized live video.
No FreeCAD or Qt imports are necessary for the geometric ray tracer.
"""
import math
from functools import lru_cache

# Nominal manufacturer max diagonal FOV. Analog presets: estimates only.
CAMERA_VIEW_SPECS = {
    'DJI O4 Air Unit Pro': (155., '16:9', 'https://www.dji.com/o4-air-unit/specs'),
    'DJI O4 Air Unit': (117.6, '16:9', 'https://www.dji.com/o4-air-unit/specs'),
    'DJI O3 Air Unit': (155., '16:9', 'https://www.dji.com/support/product/o3-air-unit'),
    'Walksnail Avatar HD Pro': (160., '16:9', 'https://www.caddxfpv.com/products/walksnail-avatar-hd-pro-camera'),
    'Walksnail Avatar HD Nano V3': (160., '4:3', 'https://en.caddxfpv.com.cn/support/hd-nano-kit-v3.html'),
    'HDZero Micro V3': (157., '16:9', 'https://docs.hd-zero.com/camera-micro-v3'),
    'HDZero Nano V3': (155., '4:3', 'https://docs.hd-zero.com/ru/camera-summary'),
    'Digital camera (estimate)': (155., '16:9', 'Generic estimate; select your actual digital camera'),
    'Analog Nano 14 mm (estimate)': (150., '4:3', 'Lens-dependent estimate; enter the real lens FOV'),
    'Analog Micro 19 mm (estimate)': (150., '4:3', 'Lens-dependent estimate; enter the real lens FOV'),
    'Caddx Ratel Pro': (125., '4:3', 'Caddx stated FOV 125 degrees, FOV axis and lens mapping not specified; approximate'),
    'Analog Mini 22 mm (estimate)': (150., '4:3', 'Lens-dependent estimate; enter the real lens FOV'),
    'Analog Full 28 mm (estimate)': (150., '4:3', 'Lens-dependent estimate; enter the real lens FOV'),
}

# Real non-DJI optics come from the same physical camera table that powers the
# 3-D model, so a user never gets a generic analog FOV after selecting Foxeer.
# A few makers report only an unlabelled "FOV"; such figures stay APPROXIMATE.
from .camera_profiles import CAMERAS
for _camera_name,_spec in CAMERAS.items():
    CAMERA_VIEW_SPECS[_camera_name]=(_spec.fov,_spec.aspect,_spec.source + ' — ' + _spec.note)
# Some sensors/lenses expose MORE on 16:9, not a centre crop of 4:3!
# The virtual view follows the selected aspect, but crop overlays remain
# estimates because full optical calibration maps are unavailable.
CAMERA_ASPECT_FOV={
    name:{'4:3':spec.fov,'16:9':spec.fov_16_9}
    for name,spec in CAMERAS.items() if spec.fov_16_9
}

# Known optical horizontal / vertical angles, where explicitly published.
CAMERA_VIEW_AXES = {
    'HDZero Micro V3': (133.,72.),
    'HDZero Nano V3': (126.,94.),
}
# Boundary horizontal FOVs from published vendor lens modes. Estimate the
# vertical boundary from the diagonal under the ray model; this is NOT a
# measured lens distortion map. HDZero H/V data are manufacturer values.
CAMERA_AXIS_BY_MODE={
    ('Foxeer T-Rex Mini','4:3'):(120.,None),
    ('Foxeer T-Rex Mini','16:9'):(155.,None),
    ('Foxeer Predator 5 Nano','4:3'):(125.,None),
    ('Foxeer Razer Nano','4:3'):(125.,None),
    ('Foxeer Razer Nano','16:9'):(125.,None),
}

CAMERA_VIEW_PROFILES = ('Follow selected camera',) + tuple(CAMERA_VIEW_SPECS)
CAMERA_VIEW_ASPECTS = ('Camera default', '16:9', '4:3')
# Optional sanity hints only. Selecting optics MUST NOT resize the actual camera.
CAMERA_BODY_WIDTHS = {
    'DJI O4 Air Unit Pro':20., 'DJI O4 Air Unit':13.44,
    'DJI O3 Air Unit':20., 'Walksnail Avatar HD Pro':19.,
    'Walksnail Avatar HD Nano V3':14.,'HDZero Micro V3':19.,
    'HDZero Nano V3':14.,
    'Analog Nano 14 mm (estimate)':14.,'Analog Micro 19 mm (estimate)':19.,
    'Caddx Ratel Pro':19.,
    'Analog Mini 22 mm (estimate)':22.,'Analog Full 28 mm (estimate)':28.,
}

CAMERA_BODY_WIDTHS.update({name:spec.width for name,spec in CAMERAS.items()})

# Recording aspect/resolution availability, taken from the manufacturers'
# published mode tables. The 2D footprint is ONLY an aspect-based centred
# estimate: equal pixel sizes and frame rates do not establish optical crop.
# key, UI label, nominal aspect, reported resolution, source / caution
RECORDING_MODES = {
    'DJI O4 Air Unit Pro': (
        ('4k43','4K · 4:3 · 3840×2880 (≤60 fps)','4:3',(3840,2880),'DJI modes; sensor/window crop not specified'),
        ('4k169','4K · 16:9 · 3840×2160 (≤120 fps)','16:9',(3840,2160),'High-frame-rate crop may differ'),
        ('27k43','2.7K · 4:3 · 2888×2016 (≤60 fps)','4:3',(2888,2016),'DJI labels this 4:3, although published pixel dimensions have a different ratio'),
        ('27k169','2.7K · 16:9 · 2688×1512 (≤120 fps)','16:9',(2688,1512),'High-frame-rate crop may differ'),
        ('108043','1080p · 4:3 · 1440×1080 (≤120 fps)','4:3',(1440,1080),'High-frame-rate crop may differ'),
        ('1080169','1080p · 16:9 · 1920×1080 (≤120 fps)','16:9',(1920,1080),'High-frame-rate crop may differ'),
    ),
    'DJI O4 Air Unit': (
        ('4k43','4K · 4:3 · 3840×2880 (≤60 fps)','4:3',(3840,2880),'DJI modes; sensor/window crop not specified'),
        ('4k169','4K · 16:9 · 3840×2160 (≤60 fps)','16:9',(3840,2160),'Camera FOV setting can change capture area'),
        ('108043','1080p · 4:3 · 1440×1080 (≤120 fps)','4:3',(1440,1080),'High-frame-rate crop may differ'),
        ('1080169','1080p · 16:9 · 1920×1080 (≤120 fps)','16:9',(1920,1080),'High-frame-rate crop may differ'),
    ),
    'DJI O3 Air Unit': (
        ('4k169','4K · 16:9 (up to 120 fps)','16:9',None,'4K 4:3 is not a supported O3 recording mode; FOV depends on fps'),
        ('27k43','2.7K · 4:3','4:3',None,'155° FOV is mode/fps-dependent'),
        ('27k169','2.7K · 16:9','16:9',None,'155° FOV is mode/fps-dependent'),
        ('108043','1080p · 4:3','4:3',None,'155° FOV is mode/fps-dependent'),
        ('1080169','1080p · 16:9','16:9',None,'155° FOV is mode/fps-dependent'),
    ),
    'Walksnail Avatar HD Pro': (
        ('108043','1080p · 4:3 (mode-dependent)','4:3',None,'Optical crop by recorder/firmware not calibrated'),
        ('1080169','1080p · 16:9 (60 fps)','16:9',(1920,1080),'Optical crop by recorder/firmware not calibrated'),
        ('72043','720p · 4:3 (mode-dependent)','4:3',None,'Optical crop by recorder/firmware not calibrated'),
        ('720169','720p · 16:9 (60/120 fps)','16:9',(1280,720),'Optical crop by recorder/firmware not calibrated'),
    ),
    'Walksnail Avatar HD Nano V3': (
        ('108043','1080p · 4:3 (60 fps)','4:3',None,'Native 4:3 sensor, mode-dependent output'),
        ('1080169','1080p · 16:9 (60 fps)','16:9',(1920,1080),'Native 4:3 sensor; centred ratio estimate'),
        ('72043','720p · 4:3 (60/120 fps)','4:3',None,'Native 4:3 sensor; recording crop is not documented'),
        ('720169','720p · 16:9 (60/120 fps)','16:9',(1280,720),'Native 4:3 sensor; recording crop is not documented'),
    ),
    'HDZero Micro V3': (
        ('1080169','1080p · 16:9 (30 fps)','16:9',(1920,1080),'Native 16:9; goggle DVR may apply its own crop'),
        ('720169','720p · 16:9 (60 fps)','16:9',(1280,720),'Native 16:9; goggle DVR may apply its own crop'),
    ),
    'HDZero Nano V3': (
        ('72043','720p · 4:3 (60 fps)','4:3',None,'Native 4:3 HDZero feed; goggles DVR crop may differ'),
        ('720169cut','720p · 16:9 cut (60 fps)','16:9',None,'Simulated centred crop; HDZero also offers 16:9 full with vignetting'),
        ('720169full','720p · 16:9 full (60 fps)','16:9',None,'Full mode uses a different optic mapping; overlay cannot simulate extra FOV'),
    ),
}

# Generic recordings are aspect-only because analog systems and other digital
# cameras do not share reliable universal camera-side recording capabilities.
GENERIC_RECORDING_MODES = (
    ('43','4:3 output / DVR — estimated','4:3',None,'Generic aspect ratio, not a verified device recording mode'),
    ('169','16:9 output / DVR — estimated','16:9',None,'Generic aspect ratio, not a verified device recording mode'),
)


def recording_modes(profile):
    """Modes for the optical profile, with analog *output* distinguished from DVR."""
    if profile in CAMERA_ASPECT_FOV:
        return (
            ('analog43','Analog 4:3 output (actual lens FOV)','4:3',None,
             'Manufacturer 4:3 FOV; not a built-in digital recording mode'),
            ('analog169','Analog 16:9 output (different lens FOV)','16:9',None,
             'Manufacturer 16:9 FOV; may show more OR less scene than 4:3'),
        )
    return RECORDING_MODES.get(profile, GENERIC_RECORDING_MODES)


def recording_reference_aspect(profile, preview_aspect):
    """Use widest documented uncropped aspect for an illustration canvas."""
    modes=recording_modes(profile)
    aspects={mode[2] for mode in modes}
    if '4:3' in aspects:
        return '4:3'
    return '16:9' if '16:9' in aspects else preview_aspect


def recording_crop_bounds(reference_aspect, mode, extra_crop_pct=0.):
    """Return (left,top,right,bottom) as 0..1 of the full lens canvas.

    Centred aspect-ratio trimming plus a *manual*, non-manufacturer crop. For
    non-calibrated camera modes there is no defensible inferred stabilization
    factor. 0 means no ADDITIONAL assumed crop, not zero actual EIS crop.
    """
    if mode is None:return (0.,0.,1.,1.)
    if not 0.<=extra_crop_pct<=30. or not math.isfinite(extra_crop_pct):
        raise ValueError('Extra recording crop must be 0–30%.')
    if mode[0] in ('analog43','analog169'):
        f=1.-extra_crop_pct/100.
        return ((1.-f)/2.,(1.-f)/2.,(1.+f)/2.,(1.+f)/2.)
    ar={'4:3':4./3.,'16:9':16./9.}
    source=ar[reference_aspect];target=ar[mode[2]]
    # HDZero Nano V3 '16:9 full' retains extra vertical content rather than
    # simply trimming the image as 16:9 cut mode does. Exact lens mapping and
    # vignetting are unknown, so show the whole 4:3 reference, not a fake cut.
    if mode[0]=='720169full':target=source
    if target>=source: width,height=1.,source/target
    else: width,height=target/source,1.
    factor=1.-extra_crop_pct/100.
    width*=factor;height*=factor
    return ((1.-width)/2.,(1.-height)/2.,(1.+width)/2.,(1.+height)/2.)


def recording_obstruction(pixels,bounds):
    """Measure obstruction only inside the selected recording rectangle.

    The crop usually covers a strict subset of the preview. Preselect its
    sample columns once instead of recomputing each X pixel's normalized
    coordinate in every visible row. Exact centre-point inclusion is retained.
    """
    if not pixels or not pixels[0]:return 0.,{}
    height=len(pixels);width=len(pixels[0]);x0,y0,x1,y1=bounds
    columns=tuple(i for i in range(width) if x0 <= (i+.5)/width <= x1)
    count=0;blocked=0;roles={}
    for j,row in enumerate(pixels):
        cy=(j+.5)/height
        if not y0<=cy<=y1:continue
        for i in columns:
            if i>=len(row):continue
            role=row[i]
            count+=1
            if role:
                blocked+=1;roles[role]=roles.get(role,0)+1
        # Preserve behaviour for irregular input rows wider than the first.
        if len(row)>width:
            for i in range(width,len(row)):
                cx=(i+.5)/width
                if x0<=cx<=x1:
                    count+=1
                    role=row[i]
                    if role:
                        blocked+=1;roles[role]=roles.get(role,0)+1
    return blocked*100/max(1,count),roles


def resolved_optics(p):
    name=p.CameraViewProfile
    if name=='Follow selected camera':
        if p.FPVSystemProfile in ('DJI O4 Air Unit Pro','DJI O4 Air Unit','DJI O3 Air Unit'):
            name=p.FPVSystemProfile
        elif p.CameraPhysicalProfile in CAMERA_VIEW_SPECS and p.CameraPhysicalProfile!='Custom measurements':
            name=p.CameraPhysicalProfile
        elif p.FPVSystemProfile in CAMERA_VIEW_SPECS:
            name=p.FPVSystemProfile
        elif p.VideoSystem=='Analog':
            name=('Analog Nano 14 mm (estimate)' if p.CameraWidth<=16 else
                  'Analog Micro 19 mm (estimate)' if p.CameraWidth<=20 else
                  'Analog Mini 22 mm (estimate)' if p.CameraWidth<=24 else
                  'Analog Full 28 mm (estimate)')
        else:
            name='Digital camera (estimate)'
    angle,aspect,source=CAMERA_VIEW_SPECS[name]
    if p.CameraViewAspect!='Camera default':aspect=p.CameraViewAspect
    aspect_angles=CAMERA_ASPECT_FOV.get(name,{})
    if aspect in aspect_angles and aspect_angles[aspect]:
        angle=aspect_angles[aspect]
        source+='; aspect-specific manufacturer lens FOV'
    if p.CameraViewFOV>0:
        angle=p.CameraViewFOV;source='User override; '+source
    return name,angle,aspect,source


def optical_pose(p,tilt):
    """Approximate entrance pupil, rather than the front face of the box.

    A 10–14 mm lens barrel cannot be approximated by a fixed 3 mm offset;
    doing so makes ray casting start behind its real glass and exaggerates
    frame/TPU obstructions. A positive manual override always takes priority.
    DJI retains its independent legacy approximation until DJI calibration.
    """
    from .fpv import camera_body_centre
    from .camera_housing import lens_dimensions
    y,z=camera_body_centre(p,tilt)
    if p.CameraViewPupilOffset>0:
        protrusion=p.CameraViewPupilOffset
    elif p.FPVSystemProfile in ('DJI O4 Air Unit Pro','DJI O4 Air Unit','DJI O3 Air Unit'):
        protrusion=4. if p.FPVSystemProfile=='DJI O4 Air Unit Pro' else 3.
    else:
        _,lens_length=lens_dimensions(p.CameraWidth,p.CameraHeight,
            p.VideoSystem=='Digital',p.CameraLensProjection,p.CameraPhysicalProfile)
        # Entrance pupil is not identical to the glass surface. Approximate
        # it modestly behind the front glass, still far ahead of the casing.
        protrusion=max(.3,lens_length-1.0)
    distance=p.CameraBodyDepth/2+protrusion
    angle=math.radians(tilt)
    return (0.,y+distance*math.cos(angle),z+distance*math.sin(angle))


def ray_direction(u,v,aspect,diagonal_fov,tilt,axes=None):
    """Direction from image coords u,v (-1..1), +Y forward and +Z up.

    The specified diagonal angle reaches the image corners, not the sides.
    """
    w,h=((16.,9.) if aspect=='16:9' else (4.,3.))
    diagonal=math.hypot(w,h)
    if axes is not None:
        # If the manufacturer measured each axis, preserve those boundary
        # angles instead of inferring both from the diagonal/aspect alone.
        x,z=math.radians(axes[0])*u/2,math.radians(axes[1])*v/2
    else:
        x,z=math.radians(diagonal_fov)*u*w/(2*diagonal),math.radians(diagonal_fov)*v*h/(2*diagonal)
    theta=math.hypot(x,z)
    factor=math.sin(theta)/theta if theta>1e-12 else 1.
    dx,dy,dz=x*factor,math.cos(theta),z*factor
    pitch=math.radians(tilt)
    return dx,dy*math.cos(pitch)-dz*math.sin(pitch),dy*math.sin(pitch)+dz*math.cos(pitch)


@lru_cache(maxsize=24)
def _base_ray_directions(width,height,aspect,diagonal_fov,axes):
    """Cache the expensive fisheye projection independently of camera tilt.

    A tilt only rotates these unit vectors: it never changes lens mapping.
    Recording crop overlays also reuse the original sampled rays.
    """
    return tuple(tuple(ray_direction(2*(i+.5)/width-1,1-2*(j+.5)/height,
                                     aspect,diagonal_fov,0.,axes)
                       for i in range(width)) for j in range(height))


def tessellate_physical(shapes,roles,tolerance=0.9,max_triangles=300000):
    """Material solids only. No camera proxy, VTX, or hypothetical props."""
    tris=[]
    for role in roles:
        shape=shapes.get(role)
        if shape is None or shape.isNull():continue
        points,faces=shape.tessellate(tolerance)
        pts=[(p.x,p.y,p.z) for p in points]
        for ia,ib,ic in faces:
            a,b,c=pts[ia],pts[ib],pts[ic]
            e1=tuple(b[k]-a[k] for k in range(3))
            e2=tuple(c[k]-a[k] for k in range(3))
            nx=e1[1]*e2[2]-e1[2]*e2[1]
            ny=e1[2]*e2[0]-e1[0]*e2[2]
            nz=e1[0]*e2[1]-e1[1]*e2[0]
            if nx*nx+ny*ny+nz*nz<1e-16:continue
            bounds=tuple((min(a[k],b[k],c[k]),max(a[k],b[k],c[k])) for k in range(3))
            tris.append((a,e1,e2,role,bounds))
            if len(tris)>max_triangles:
                raise ValueError('Camera-view mesh exceeds 300,000 triangles. Reduce geometry detail and retry; no parts are omitted from the result.')
    return tris


def make_bvh(tris,indices=None,leaf_size=12):
    if indices is None:indices=list(range(len(tris)))
    if not indices:return None
    # A single scan replaces six generator passes per BVH node. This matters
    # with detailed prop and TPU meshes containing tens of thousands of faces.
    b0=tris[indices[0]][4]
    lo=[b0[k][0] for k in range(3)]
    hi=[b0[k][1] for k in range(3)]
    for index in indices[1:]:
        b=tris[index][4]
        for k in range(3):
            if b[k][0]<lo[k]:lo[k]=b[k][0]
            if b[k][1]>hi[k]:hi[k]=b[k][1]
    bounds=tuple(zip(lo,hi))
    if len(indices)<=leaf_size:return (bounds,None,None,indices)
    axis=max(range(3),key=lambda k:hi[k]-lo[k])
    indices.sort(key=lambda i:tris[i][4][axis][0]+tris[i][4][axis][1])
    cut=len(indices)//2
    return (bounds,make_bvh(tris,indices[:cut],leaf_size),make_bvh(tris,indices[cut:],leaf_size),None)



def _bounds_entry(bounds,origin,inverse,limit):
    """Nearest positive ray entry into an AABB, or None if it misses."""
    tmin,tmax=.001,limit
    for k,(lo,hi) in enumerate(bounds):
        inv=inverse[k];o=origin[k]
        if inv is None:
            if o<lo or o>hi:return None
        else:
            t1=(lo-o)*inv;t2=(hi-o)*inv
            if t1>t2:t1,t2=t2,t1
            if t1>tmin:tmin=t1
            if t2<tmax:tmax=t2
            if tmax<tmin:return None
    return tmin


def _hits_bounds(bounds,origin,direction,limit,inverse=None):
    """Compatibility wrapper for callers expecting a boolean AABB test."""
    if inverse is None:inverse=tuple(None if abs(d)<1e-12 else 1./d for d in direction)
    return _bounds_entry(bounds,origin,inverse,limit) is not None


def _hits_triangle(tri,origin,direction,limit):
    a,e1,e2,_,_=tri
    px=direction[1]*e2[2]-direction[2]*e2[1]
    py=direction[2]*e2[0]-direction[0]*e2[2]
    pz=direction[0]*e2[1]-direction[1]*e2[0]
    det=e1[0]*px+e1[1]*py+e1[2]*pz
    if abs(det)<1e-11:return None
    inv=1/det
    tx,ty,tz=origin[0]-a[0],origin[1]-a[1],origin[2]-a[2]
    u=(tx*px+ty*py+tz*pz)*inv
    if u<0 or u>1:return None
    qx=ty*e1[2]-tz*e1[1]
    qy=tz*e1[0]-tx*e1[2]
    qz=tx*e1[1]-ty*e1[0]
    v=(direction[0]*qx+direction[1]*qy+direction[2]*qz)*inv
    if v<0 or u+v>1:return None
    distance=(e2[0]*qx+e2[1]*qy+e2[2]*qz)*inv
    return distance if .001<distance<limit else None


def first_hit(tris,tree,origin,direction,max_distance=500.):
    """Return the closest hit with front-to-back BVH pruning.

    This preserves the existing exact triangle intersection test and result
    format. Only the order and number of bounds/triangle tests change.
    """
    if tree is None:return None
    distance,role=max_distance,None
    inverse=tuple(None if abs(d)<1e-12 else 1./d for d in direction)
    root_entry=_bounds_entry(tree[0],origin,inverse,distance)
    if root_entry is None:return None
    stack=[(root_entry,tree)]
    while stack:
        entry,node=stack.pop()
        if entry>=distance:continue
        bounds,left,right,ids=node
        if ids is not None:
            for i in ids:
                d=_hits_triangle(tris[i],origin,direction,distance)
                if d is not None and d<distance:distance,role=d,tris[i][3]
        else:
            le=_bounds_entry(left[0],origin,inverse,distance) if left is not None else None
            re=_bounds_entry(right[0],origin,inverse,distance) if right is not None else None
            if le is not None and re is not None:
                if le<re:
                    stack.append((re,right));stack.append((le,left))
                else:
                    stack.append((le,left));stack.append((re,right))
            elif le is not None:stack.append((le,left))
            elif re is not None:stack.append((re,right))
    return (role,distance) if role is not None else None


def propeller_sweep_geometry(p):
    """Four approximate rotor swept discs (not physical CAD obstructions).

    Motor positions include any motor-pad rotation/offset. The prop plane
    follows the same simple/detailed reference convention as the viewport;
    no actual blade shape or motion blur is asserted.
    """
    from .parameters import motor_centres,arms_above_bottom
    arm_z=p.BottomThickness if arms_above_bottom(p) else -p.ArmThickness
    if p.ShowReferences and p.DetailedPropReferences:
        from .reference_options import PROP_HUB_HEIGHT
        height=p.MotorReferenceHeight+PROP_HUB_HEIGHT/2.
    else:
        height=p.PropReferenceHeight
    z=arm_z+p.ArmThickness+height
    radius=p.PropDiameter/2.
    names=('Front right','Front left','Rear left','Rear right')
    return tuple((x,y,z,radius,names[i]) for i,(x,y) in enumerate(motor_centres(p)))


def first_visible_propeller(eye,direction,discs,physical_hit=None,max_distance=500.):
    """First swept disc between the lens and the nearest solid (if any).

    A disc is a thin horizontal plane; the result is a visibility indicator,
    NOT a claim that any blade is present at this instant or a solid blockage.
    """
    dz=direction[2]
    if abs(dz)<1.e-10:return None
    limit=min(max_distance,physical_hit[1]) if physical_hit else max_distance
    nearest=limit
    label=None
    for x,y,z,radius,name in discs:
        distance=(z-eye[2])/dz
        if not .001<distance<nearest:continue
        ix=eye[0]+distance*direction[0]
        iy=eye[1]+distance*direction[1]
        if (ix-x)**2+(iy-y)**2 <= radius*radius:
            nearest=distance;label=name
    return label


def render_rays(tris,tree,p,tilt,width=128,height=72,progress=None,aspect_override=None):
    name,fov,aspect,source=resolved_optics(p)
    if aspect_override is not None:
        if aspect_override not in ('4:3','16:9'):raise ValueError('Unsupported virtual view aspect')
        aspect=aspect_override
    if p.CameraViewFOV==0 and CAMERA_ASPECT_FOV.get(name,{}).get(aspect):
        fov=CAMERA_ASPECT_FOV[name][aspect]
    eye=optical_pose(p,tilt)
    axes=None
    if p.CameraViewFOV==0:
        if (name,aspect) in CAMERA_AXIS_BY_MODE:
            horiz,vertical=CAMERA_AXIS_BY_MODE[(name,aspect)]
            if vertical is None:
                # Equidistant approximation using both published diagonal
                # and horizontal angle, with vertical axis inferred.
                vertical=2*math.sqrt(max(.01,(fov/2.)**2-(horiz/2.)**2))
            axes=(horiz,vertical)
        elif name in CAMERA_VIEW_AXES and aspect==CAMERA_VIEW_SPECS[name][1]:
            axes=CAMERA_VIEW_AXES[name]
    # Reuse the same lens samples for repeated tilt checks; avoid sin/cos and
    # fisheye math for every triangle ray. Image coordinates remain unchanged.
    base=_base_ray_directions(width,height,aspect,fov,axes)
    pitch=math.radians(tilt)
    cs,sn=math.cos(pitch),math.sin(pitch)
    central_columns=tuple(abs(2*(i+.5)/width-1)<.65 for i in range(width))
    discs=propeller_sweep_geometry(p)
    pixels=[];prop_pixels=[];hits=0;central_hits=0;central_count=0;role_counts={}
    prop_hits=0;central_prop_hits=0;prop_counts={}
    for j,base_row in enumerate(base):
        v=1-2*(j+.5)/height
        inside_centre=abs(v)<.65
        row=[];prop_row=[]
        for i,(dx,dy,dz) in enumerate(base_row):
            direction=(dx,dy*cs-dz*sn,dy*sn+dz*cs)
            result=first_hit(tris,tree,eye,direction)
            role=result[0] if result else None
            row.append(role)
            prop=first_visible_propeller(eye,direction,discs,result)
            prop_row.append(prop)
            if prop:
                prop_hits+=1;prop_counts[prop]=prop_counts.get(prop,0)+1
            if role:
                hits+=1;role_counts[role]=role_counts.get(role,0)+1
            if inside_centre and central_columns[i]:
                central_count+=1
                if role:central_hits+=1
                if prop:central_prop_hits+=1
        pixels.append(row);prop_pixels.append(prop_row)
        if progress and j%8==0:progress(j+1,height)
    return {'pixels':pixels,'prop_pixels':prop_pixels,
            'prop_visible_pct':prop_hits*100/(width*height),
            'centre_prop_visible_pct':central_prop_hits*100/max(1,central_count),
            'prop_roles':prop_counts,'blocked_pct':hits*100/(width*height),
            'centre_blocked_pct':central_hits*100/max(1,central_count),
            'roles':role_counts,'origin':eye,'tilt':tilt,'fov':fov,
            'aspect':aspect,'profile':name,'source':source}


def tilt_sweep(tris,tree,p,angles=range(0,61,5),include_props=False):
    """Low-resolution tilt sweep, optionally reporting swept prop visibility."""
    results=[]
    for angle in angles:
        sample=render_rays(tris,tree,p,angle,width=24,height=14)
        value=(angle,sample['blocked_pct'],sample['centre_blocked_pct'])
        if include_props:
            value+=(sample['prop_visible_pct'],sample['centre_prop_visible_pct'])
        results.append(value)
    return results
