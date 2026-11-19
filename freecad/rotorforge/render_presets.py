"""Studio lighting defaults and camera fitting, independent of FreeCAD/Blender."""
from math import isfinite, tan

NAMES = ('Dark Studio', 'Light Studio', 'Cinematic', 'Clay Render')
# Light strengths are relative to the subject's size, not absolute wattages.
PRESETS = (
    dict(key=1.0, fill=.36, rim=.95, world=.085, soft=1.12, exposure=-.15, rough=1.0, ground_rough=.72, background=0, floor=True),
    dict(key=1.0, fill=.38, rim=.35, world=.22, soft=1.35, exposure=0., rough=1., ground_rough=.82, background=0, floor=True),
    dict(key=.90, fill=.25, rim=1.05, world=.065, soft=1.0, exposure=-.25, rough=.95, ground_rough=.58, background=0, floor=True),
    dict(key=1.0, fill=.30, rim=.40, world=.15, soft=1.2, exposure=-.15, rough=1.2, ground_rough=.85, background=0, floor=True),
)
# Linear scene colours; lighting directions are relative to the camera.
LOOKS = (
    dict(bg=(.006,.008,.012), floor=(.003,.004,.006), ambient=(.88,.91,.96), key_color=(1,.97,.93), fill_color=(.94,.97,1), rim_color=(.88,.94,1), look='AgX - Medium Low Contrast'),
    dict(bg=(.72,.76,.82), floor=(.57,.61,.67), ambient=(.92,.95,1), key_color=(1,.96,.91), fill_color=(.91,.95,1), rim_color=(1,1,1), look='AgX - Medium High Contrast'),
    dict(bg=(.003,.012,.022), floor=(.002,.006,.010), ambient=(.42,.61,.80), key_color=(.79,.91,1), fill_color=(.54,.31,1), rim_color=(.11,.80,1), look='AgX - Medium High Contrast'),
    dict(bg=(.30,.33,.37), floor=(.26,.29,.33), ambient=(.9,.93,1), key_color=(1,.96,.91), fill_color=(.86,.91,1), rim_color=(1,1,1), look='AgX - Medium High Contrast'),
)


# Radiant power in watts, normalized to a subject of one metre. A 300 mm
# model receives a few watts per light rather than tens of watts. Keep the
# controls relative so scene scale does not alter the apparent exposure.
LIGHT_WATTS = (42., 85., 38., 70.)

def area_power(style, subject_size, intensity):
    return LIGHT_WATTS[style] * subject_size**2 * max(0., intensity)


def hardware_surface(role, properties=()):
    name=role.lower()
    return 'HardwareRole' in properties or name=='standoffs' or 'screw' in name or 'nut' in name


def surface_finish(surface, roughness=1., clay=False):
    """Physical-style non-metallic finish differences; RGB remains unchanged."""
    if clay:return dict(roughness=.68,specular=.40,coat=0.,coat_roughness=.5,bump=0.)
    rough,spec,coat,coat_rough,bump={
        'carbon':(.29,.48,.23,.25,0.),
        'tpu':(.76,.24,0.,.5,.12),
        'prop':(.32,.31,.05,.32,0.),
        'metal':(.28,.40,0.,.5,0.),
        'motor_bell':(.32,.42,.12,.30,0.),
    }.get(surface,(.43,.40,0.,.5,0.))
    return dict(roughness=min(.98,rough*roughness),specular=spec,coat=coat,coat_roughness=coat_rough,bump=bump)


def _rgb(value):
    try:return tuple(max(0.,min(1.,float(value[i]))) for i in range(3))
    except (AttributeError,TypeError,IndexError,ValueError):return None


def source_palette(view, face_count):
    """FreeCAD 1.x appearance and legacy colours; allow singleton palettes."""
    base=_rgb(view.ShapeColor) or (.18,.19,.20)
    legacy=tuple(filter(None,(_rgb(c) for c in (getattr(view,'DiffuseColor',()) or ()))))
    modern=tuple(filter(None,(_rgb(getattr(m,'DiffuseColor',None)) for m in
        (getattr(view,'ShapeAppearance',()) or ()))))
    if not modern:
        one=_rgb(getattr(getattr(view,'ShapeMaterial',None),'DiffuseColor',None))
        if one is not None:modern=(one,)
    # Prefer explicitly varied face colours over a uniform compatibility
    # property array. If both arrays contain distinct colours, prefer modern.
    for palette in (modern,legacy):
        if len(palette)==face_count and len(set(palette))>1:return base,palette
    for palette in (modern,legacy):
        if len(palette) in (1,face_count) and palette and palette[0]!=base:
            # Non-grey ShapeColor can be the only freshly updated property.
            if max(base)-min(base)>.07 and max(palette[0])-min(palette[0])<.025:continue
            return palette[0],()
    return base,()


def fit_camera(points, half_x, half_y, zoom=1., orthographic=False):
    """Fit camera-space (right, up, toward camera) vertices with safe margins.

    half_x/y are the actual camera frame half extents at unit depth/scale.
    Returns right/up camera offsets, distance, ortho scale, and perspective
    slope offsets for symmetric framing. No CAD or renderer dependencies.
    """
    if not points or not all(isfinite(v) and v>0 for v in (half_x,half_y,zoom)):
        raise ValueError('Invalid camera frame or empty scene')
    # 1.0 fills at most 88% of either image dimension; lower zoom adds space.
    fill=.88*min(zoom,1.)
    xs,ys,zs=zip(*points)
    size=max(max(xs)-min(xs),max(ys)-min(ys),max(zs)-min(zs),.01)
    if orthographic:
        cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2
        scale=max((max(xs)-min(xs))/(2*half_x*fill),(max(ys)-min(ys))/(2*half_y*fill),.001)
        return cx,cy,max(zs)+size*3,scale,0.,0.
    # Solve the intersection of all per-vertex camera-position intervals.
    # This accounts for perspective depth and foreground propellers.
    kx,ky=half_x*fill,half_y*fill
    lx=max(x+kx*z for x,z in zip(xs,zs));ux=min(x-kx*z for x,z in zip(xs,zs))
    ly=max(y+ky*z for y,z in zip(ys,zs));uy=min(y-ky*z for y,z in zip(ys,zs))
    d=max((lx-ux)/(2*kx),(ly-uy)/(2*ky),max(zs)+max(.005,size*.03))
    cx=(lx+ux)/2;cy=(ly+uy)/2
    px=[(x-cx)/(d-z) for x,z in zip(xs,zs)];py=[(y-cy)/(d-z) for y,z in zip(ys,zs)]
    # Lens shift centres the actual projected outline, not the 3D bounding box.
    return cx,cy,d,1.,(min(px)+max(px))/2,(min(py)+max(py))/2

# Keep the original four indices stable for existing renderer jobs. Each new
# look inherits the same control schema, so a preset is a complete reset.
NAMES += ('Soft Dark Studio', 'High Contrast Studio', 'White Catalog',
          'Warm Product Shot', 'Technical Gray', 'Showroom')
PRESETS += (
    dict(key=.85, fill=.36, rim=.50, world=.10, soft=1.65, exposure=-.16, rough=1.05, ground_rough=.80, background=0, floor=True),
    dict(key=1.10, fill=.16, rim=1.20, world=.045, soft=.75, exposure=-.26, rough=.95, ground_rough=.70, background=0, floor=True),
    dict(key=.90, fill=.45, rim=.25, world=.28, soft=1.55, exposure=-.08, rough=1., ground_rough=.92, background=0, floor=True),
    dict(key=.95, fill=.38, rim=.45, world=.16, soft=1.35, exposure=-.14, rough=1., ground_rough=.80, background=0, floor=True),
    dict(key=.82, fill=.40, rim=.28, world=.18, soft=1.35, exposure=-.12, rough=1., ground_rough=.90, background=0, floor=True),
    dict(key=.97, fill=.30, rim=.84, world=.10, soft=1.35, exposure=-.20, rough=.94, ground_rough=.30, background=0, floor=True),
)
LOOKS += (
    dict(bg=(.022,.025,.030), floor=(.016,.018,.022), ambient=(.96,.97,1), key_color=(1,.98,.95), fill_color=(.96,.98,1), rim_color=(.94,.97,1), look='AgX - Medium Low Contrast'),
    dict(bg=(.003,.004,.006), floor=(.003,.004,.005), ambient=(.96,.97,1), key_color=(1,.98,.94), fill_color=(.94,.97,1), rim_color=(.94,.98,1), look='AgX - High Contrast'),
    dict(bg=(.94,.94,.94), floor=(.88,.88,.88), ambient=(1,1,1), key_color=(1,1,1), fill_color=(1,1,1), rim_color=(1,1,1), look='AgX - Medium Low Contrast'),
    dict(bg=(.22,.18,.14), floor=(.16,.13,.10), ambient=(1,.91,.80), key_color=(1,.87,.72), fill_color=(.98,.96,1), rim_color=(1,.94,.82), look='AgX - Medium High Contrast'),
    dict(bg=(.18,.18,.18), floor=(.15,.15,.15), ambient=(1,1,1), key_color=(1,1,1), fill_color=(1,1,1), rim_color=(1,1,1), look='AgX - Medium Low Contrast'),
    dict(bg=(.037,.042,.05), floor=(.025,.030,.040), ambient=(.92,.95,1), key_color=(1,.98,.94), fill_color=(.94,.98,1), rim_color=(.87,.95,1), look='AgX - Medium High Contrast'),
)
LIGHT_WATTS += (42., 40., 85., 60., 60., 48.)

# Distinct photographic light rigs. Coordinates are (camera-right,
# camera-front, vertical) in units of the drone size. Width/height are
# relative to the drone size; a missing height denotes a disk softbox.
RIG_NAMES = ('Classic three-point', 'Cross lighting', 'Overhead softbox',
             'Side stripboxes', 'Backlit / rim', 'Front beauty softbox')
LIGHT_RIGS = (
    (((-.95,.9,1.4),1.15,None), ((.75,1.25,.60),1.65,None), ((.65,-1.05,1.25),.65,None), ((-1.05,-.85,.55),.50,None)),
    (((-1.25,.35,.85),.80,1.35), ((1.1,.45,.65),.80,1.20), ((.65,-1.15,.90),.55,1.10), ((-1.1,-.9,.55),.45,1.05)),
    (((-.12,.30,1.7),2.15,1.50), ((.75,1.15,.35),1.35,None), ((0,-1.05,1.25),1.5,.40), ((-1.15,.15,.55),.50,None)),
    (((-1.1,.25,1.05),.24,1.85), ((1.15,.45,.8),.24,1.65), ((.2,-1.15,1.25),1.7,.22), ((-1.05,-.85,.45),.30,1.35)),
    (((-.85,.65,1.15),1.2,None), ((.6,1.25,.45),1.5,None), ((.25,-1.0,.85),1.75,.48), ((-1.1,-.65,.75),.50,1.25)),
    (((-.25,1.25,1.35),2.2,1.6), ((.85,.90,.55),1.5,None), ((.5,-1.2,1.0),1.3,.55), ((-1.1,-.75,.70),.55,None)),
)
# Append rather than reorder: material override and existing look indices
# remain stable. All colours below are linear scene-light values.
_EXTRA_LOOKS = (
    ('Neon Cyberpunk', 42., 1, .65, .38, 1.10, .12, .055, 1.05, -.22, .95, .34,
     (.008,.003,.020), (.006,.003,.015), (.52,.58,.95), (.09,.75,1), (.67,.07,1), (.98,.10,.42), (.07,.95,1), 'AgX - Medium High Contrast'),
    ('Teal & Amber', 46., 1, .95, .32, .95, .38, .075, 1.18, -.12, .95, .45,
     (.008,.022,.025), (.009,.018,.019), (.70,.84,.86), (1,.64,.28), (.18,.85,1), (.11,.82,1), (1,.35,.08), 'AgX - Medium High Contrast'),
    ('Crimson Edge', 43., 4, .85, .23, 1.20, .55, .065, .85, -.18, .95, .38,
     (.024,.003,.006), (.014,.003,.005), (.88,.85,.89), (1,.95,.90), (1,.28,.23), (1,.035,.06), (1,.10,.05), 'AgX - Medium High Contrast'),
    ('Ice Blue', 56., 2, .95, .38, .8, .18, .16, 1.4, -.10, 1., .55,
     (.07,.14,.23), (.045,.10,.18), (.72,.85,1), (.69,.86,1), (.82,.94,1), (.23,.65,1), (.40,.88,1), 'AgX - Medium Low Contrast'),
    ('Violet & Gold', 48., 1, .82, .34, .98, .36, .08, 1.18, -.15, .94, .42,
     (.035,.009,.055), (.022,.008,.037), (.75,.65,.91), (1,.79,.43), (.51,.20,1), (.73,.25,1), (1,.48,.08), 'AgX - Medium High Contrast'),
    ('Overhead Softbox', 72., 2, 1.15, .25, .25, 0., .18, 1.35, -.10, 1., .82,
     (.16,.17,.18), (.12,.13,.14), (.98,.98,1), (1,1,1), (.94,.96,1), (1,1,1), (1,1,1), 'AgX - Medium Low Contrast'),
    ('Striplight Studio', 50., 3, .92, .50, 1.05, .14, .08, .86, -.16, .86, .26,
     (.014,.017,.023), (.009,.012,.016), (.91,.94,1), (1,.98,.95), (.92,.96,1), (1,1,1), (.62,.80,1), 'AgX - Medium High Contrast'),
    ('Rim Silhouette', 46., 4, .23, .13, 1.50, .66, .035, .96, -.14, .9, .64,
     (.004,.008,.014), (.004,.006,.012), (.85,.91,1), (1,.96,.92), (.70,.85,1), (.75,.91,1), (.35,.70,1), 'AgX - High Contrast'),
    ('Pastel Editorial', 78., 5, .95, .46, .3, .0, .27, 1.65, -.08, 1.05, .92,
     (.48,.31,.38), (.40,.24,.32), (1,.94,.97), (1,.95,.94), (.87,.94,1), (1,.82,.90), (1,1,1), 'AgX - Medium Low Contrast'),
)
_RIG_BY_STYLE = [0]*len(NAMES)
_ACCENT_BY_STYLE = [0.]*len(NAMES)
_ACCENT_BY_STYLE[2] = .28*PRESETS[2]['rim']
_ACCENT_COLOURS = [(1.,1.,1.)]*len(NAMES)
_ACCENT_COLOURS[2] = (.38,.16,1.)
for (name, watts, rig, key, fill, rim, accent, world, soft, exposure, rough, ground,
     bg, floor, ambient, kc, fc, rc, ac, contrast) in _EXTRA_LOOKS:
    NAMES += (name,)
    LIGHT_WATTS += (watts,)
    PRESETS += (dict(key=key, fill=fill, rim=rim, world=world, soft=soft, exposure=exposure,
                     rough=rough, ground_rough=ground, background=0, floor=True),)
    LOOKS += (dict(bg=bg, floor=floor, ambient=ambient, key_color=kc, fill_color=fc,
                   rim_color=rc, look=contrast),)
    _RIG_BY_STYLE.append(rig)
    _ACCENT_BY_STYLE.append(accent)
    _ACCENT_COLOURS.append(ac)

LIGHT_COLOUR_KEYS = ('key_color','fill_color','rim_color','accent_color','ambient','bg','floor')
CONTRAST_NAMES = ('AgX - Very Low Contrast','AgX - Low Contrast','AgX - Medium Low Contrast',
                  'AgX - Medium High Contrast','AgX - High Contrast','AgX - Very High Contrast')

FRONT_BALANCE = [0.16]*len(NAMES)
# Preserve moody looks, but avoid a darker nose than tail on presets with
# strong rim/back lighting or cross-lighting.
for i in (2, 5, 9, 10, 12, 14, 16, 17, 18):
    if i < len(FRONT_BALANCE):FRONT_BALANCE[i] = 0.24
for i in (7, 15):
    if i < len(FRONT_BALANCE):FRONT_BALANCE[i] = 0.28


def lighting_settings(style, overrides=None):
    """Complete independent light settings; old render jobs keep their defaults."""
    result=dict(LOOKS[style], rig=_RIG_BY_STYLE[style], accent=_ACCENT_BY_STYLE[style],
                accent_color=_ACCENT_COLOURS[style], front_balance=FRONT_BALANCE[style])
    if overrides:
        for key in LIGHT_COLOUR_KEYS:
            if key in overrides:
                color=_rgb(overrides[key])
                if color is not None:result[key]=color
        if 'rig' in overrides:
            rig=int(overrides['rig'])
            if 0<=rig<len(LIGHT_RIGS):result['rig']=rig
        if 'accent' in overrides:result['accent']=max(0.,min(4.,float(overrides['accent'])))
        if overrides.get('look') in CONTRAST_NAMES:result['look']=overrides['look']
        if 'front_balance' in overrides:result['front_balance']=max(0.,min(1.,float(overrides['front_balance'])))
    return result


def linear_to_srgb(color):
    return tuple(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055 for v in color)


def srgb_to_linear(color):
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in color)


POSE_NAMES = ('Front Isometric','Rear Isometric','Side Profile','Top Perspective',
              'Low Hero','Detail Close-Up','Hover Presentation','In-Flight','Aggressive In-Flight')

def _pose(az, el, lens, zoom=1., pitch=0., roll=0., blur=0., flying=False, bias=0.):
    return dict(az=az, el=el, lens=lens, zoom=zoom, pitch=pitch, roll=roll,
                yaw=0., blur=blur, spinning=blur>0, flying=flying, flight_shadow=True,
                flight_height=.26, flight_bias=bias, projection=0)

POSES = (
    _pose(35, 30, 42), _pose(145, 30, 42), _pose(90, 8, 58), _pose(35, 62, 38),
    _pose(30, 10, 40), _pose(28, 14, 70),
    _pose(34, 14, 40, .94, 0, 2, .30, True),
    _pose(48, 15, 38, .87, 14, 4, .62, True, .035),
    _pose(60, 12, 34, .84, 25, 10, .90, True, .045),
)


def flight_margins(zoom, bias, direction_x, direction_y):
    """Return safe fit zoom and signed fractional full-frame offsets.

    Reserve room for translation before fitting, including portrait images.
    Direction is already projected into camera space and normalized.
    """
    bias = max(0., min(.10, bias))
    length = (direction_x**2 + direction_y**2)**.5
    if length < 1e-8 or not bias:
        return zoom, 0., 0.
    dx,dy = bias*direction_x/length,bias*direction_y/length
    return min(zoom,(.88-2*max(abs(dx),abs(dy)))/.88),dx,dy


def blur_profile(amount):
    """Relative exposure coverage, never an opaque propeller disc."""
    amount=max(0.,min(1.,amount))
    return (.13+.23*amount, .36*(1-amount), .20+.25*amount)


def viewport_half_height(vertical_extent, source_aspect, output_aspect, orthographic, zoom=1.):
    """Preserve the viewport's visible area when the output aspect changes.

    Extent is the Coin camera height in metres or heightAngle in radians.
    The usual FreeCAD ADJUST_CAMERA mapping expands portrait views.
    """
    if not all(isfinite(v) and v>0 for v in (vertical_extent, source_aspect, output_aspect, zoom)):
        raise ValueError('Invalid FreeCAD camera extent or viewport size')
    half=vertical_extent/2 if orthographic else tan(vertical_extent/2)
    if not isfinite(half) or half<=0 or (not orthographic and vertical_extent>=3.141592653589793):
        raise ValueError('Invalid FreeCAD camera field of view')
    half/=min(1.,source_aspect)
    return half*max(1.,source_aspect/output_aspect)/min(1.,zoom)


def viewport_safe_half_height(points, aspect, half_height, orthographic=False):
    """Widen only when geometry would touch the edge; never move the camera.

    Points are camera-relative (right, up, positive depth). Preserve pan and
    perspective; explicitly reject geometry behind the captured camera.
    """
    required=0.
    for x,y,depth in points:
        if depth<=.001:
            raise ValueError('The FreeCAD camera is too close to the model. Zoom out or use an auto-fit camera preset.')
        span=max(abs(x)/aspect,abs(y))
        required=max(required,span if orthographic else span/depth)
    return max(half_height,required/.98)
