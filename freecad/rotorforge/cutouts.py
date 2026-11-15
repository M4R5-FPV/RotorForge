"""Portable per-part airflow patterns. Camera coordinates are Y offset / height."""
import json
import math
from functools import lru_cache

CUTOUT_ROLES = ('BottomPlate', 'MidPlate', 'TopPlate', 'ArmClampPlate', 'ArmKeystone',
                'CameraMountLeft', 'CameraMountRight', 'ArmFrontRight', 'ArmFrontLeft',
                'ArmRearLeft', 'ArmRearRight', 'ArmLowerClampPlate')
LEGACY_CUTOUT_TYPES = ('Circle', 'Slot', 'Arc slot', 'Rounded rectangle', 'Hexagon',
                'Ellipse', 'Rectangle', 'Triangle', 'Diamond', 'Trapezoid', 'Pentagon', 'Octagon', 'Chevron', 'Heptagon', 'Dodecagon', 'Parallelogram', 'Kite', 'Hourglass', 'Cross', 'Crescent', 'Leaf', 'Shield', 'Swept fin', 'Aero spear', 'Split bridge', 'Web cell')
# New cutouts use only smooth profiles that meet the R0.5 milling rule.
# Legacy polygon profiles remain parseable so older saved frames can be opened.
# Every newly selectable polygon is generated with genuine >= R0.5 circular
# fillets, including at concave corners. Crescent/Leaf remain legacy-only until
# their free-form outlines can be certified to the same curvature requirement.
CUTOUT_TYPES = ('Circle', 'Slot', 'Arc slot', 'Rounded rectangle', 'Ellipse',
                'Triangle', 'Diamond', 'Trapezoid', 'Hexagon', 'Pentagon',
                'Octagon', 'Heptagon', 'Dodecagon', 'Chevron',
                'Parallelogram', 'Kite', 'Hourglass', 'Cross', 'Shield', 'Swept fin',
                'Aero spear', 'Split bridge')
CNC_POLYGON_TYPES = ('Web cell',) + tuple(t for t in CUTOUT_TYPES if t not in
                          ('Circle', 'Slot', 'Rounded rectangle', 'Ellipse'))
MIN_INTERNAL_RADIUS = .5
OUTLINE_ROLES = ('BottomPlate', 'MidPlate', 'TopPlate', 'ArmClampPlate', 'ArmLowerClampPlate')
CUTOUT_MODES = ('Interior', 'Pocket', 'Outline notch', 'Add material')
MAX_PATTERNS = 200
MAX_ENABLED_CUTOUTS = 200
PATTERN_DEFAULTS = dict(mode='Interior', role='TopPlate', shape='Slot', width=4., length=12., x=0., y=0.,
                        rotation=0., columns=1, rows=1, pitch_x=10., pitch_y=16., depth=0.5, arc_angle=75., enabled=True, auto_web=0., auto_keep=False, auto_group='', vertices=[])


def cutout_polygon(pattern):
    """Local polygon vertices shared by exact CAD and the editor preview."""
    w,l=pattern['width'],pattern['length'];name=pattern['shape']
    if name=='Web cell':
        # Local normalized vertices keep fully generated profiles adjustable
        # using the editor's existing Width / Length / Rotation controls.
        vertices=pattern.get('vertices') or ((-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5))
        return tuple((float(u)*w,float(v)*l) for u,v in vertices)
    # Compound *single-opening* profiles: sculpted from several lobes / a
    # central notch into one CNC-compatible outline. The common analytic
    # R0.5 corner routine handles every inward and outward turn in CAD/Qt.
    if name=='Aero spear':
        return ((-w*.30,-l*.50),(w*.30,-l*.50),(w*.45,-l*.27),
                (w*.30,-l*.05),(w*.50,l*.12),(0,l*.50),
                (-w*.50,l*.12),(-w*.30,-l*.05),(-w*.45,-l*.27))
    if name=='Split bridge':
        return ((-w*.50,-l*.50),(-w*.17,-l*.50),(-w*.17,-l*.20),
                (w*.17,-l*.20),(w*.17,-l*.50),(w*.50,-l*.50),
                (w*.39,l*.16),(0,l*.50),(-w*.39,l*.16))
    if name=='Shield':return ((-w*.44,-l/2),(w*.44,-l/2),(w/2,-l*.14),(w*.32,l*.24),(0,l/2),(-w*.32,l*.24),(-w/2,-l*.14))
    if name=='Swept fin':return ((-w/2,-l/2),(w*.32,-l/2),(w/2,-l*.22),(w*.22,l*.34),(-w*.12,l/2),(-w*.42,l*.25))
    if name=='Hexagon':return ((-w/2,0),(-w/4,-l/2),(w/4,-l/2),(w/2,0),(w/4,l/2),(-w/4,l/2))
    if name=='Rectangle':return ((-w/2,-l/2),(w/2,-l/2),(w/2,l/2),(-w/2,l/2))
    if name=='Triangle':return ((-w/2,-l/2),(w/2,-l/2),(0,l/2))
    if name=='Diamond':return ((0,-l/2),(w/2,0),(0,l/2),(-w/2,0))
    if name=='Trapezoid':return ((-w/2,-l/2),(w/2,-l/2),(w/4,l/2),(-w/4,l/2))
    if name=='Chevron':return ((-w/2,-l/2),(0,0),(w/2,-l/2),(w/2,0),(0,l/2),(-w/2,0))
    if name=='Parallelogram':return ((-w/2,-l/2),(w/4,-l/2),(w/2,l/2),(-w/4,l/2))
    if name=='Kite':return ((0,-l/2),(w/2,-l/6),(0,l/2),(-w/2,-l/6))
    if name=='Hourglass':return ((-w/2,-l/2),(w/2,-l/2),(w/5,0),(w/2,l/2),(-w/2,l/2),(-w/5,0))
    if name=='Cross':return ((-w/6,-l/2),(w/6,-l/2),(w/6,-l/6),(w/2,-l/6),(w/2,l/6),(w/6,l/6),(w/6,l/2),(-w/6,l/2),(-w/6,l/6),(-w/2,l/6),(-w/2,-l/6),(-w/6,-l/6))
    if name=='Crescent':
        outer=[(w/2-w*math.sin(i*math.pi/32),l/2*math.cos(i*math.pi/32)) for i in range(33)]
        return tuple(outer+[(w/2-w*.5*math.sin(i*math.pi/32),l/2*math.cos(i*math.pi/32)) for i in range(31,0,-1)])
    if name=='Leaf':return tuple((w/2*math.sin(i*math.pi/32)*abs(math.sin(i*math.pi/32))**.4,l/2*math.cos(i*math.pi/32)) for i in range(64))
    if name in ('Pentagon','Octagon','Heptagon','Dodecagon'):
        n={'Pentagon':5,'Octagon':8,'Heptagon':7,'Dodecagon':12}[name]
        points=[(math.cos(math.pi/2+2*math.pi*i/n+(math.pi/8 if n==8 else 0)),
                 math.sin(math.pi/2+2*math.pi*i/n+(math.pi/8 if n==8 else 0))) for i in range(n)]
        lowx,highx=min(x for x,y in points),max(x for x,y in points)
        lowy,highy=min(y for x,y in points),max(y for x,y in points)
        return tuple((w*((x-lowx)/(highx-lowx)-.5),l*((y-lowy)/(highy-lowy)-.5)) for x,y in points)
    return ()



def rounded_polygon_segments(points, radius=MIN_INTERNAL_RADIUS):
    """Return a closed, analytically filleted outline as line/arc segments.

    Format: list of ('line', start, end) or ('arc', start, middle, end).
    All nonzero internal turns use a circular arc of radius >= radius.
    Raises ValueError if the profile is too narrow for a 1 mm mill.
    Both convex and concave corners are supported; never silently shrink R.
    """
    if radius < MIN_INTERNAL_RADIUS - 1e-9:
        raise ValueError('CNC internal radius must be at least R0.5 mm.')
    pts = list(points)
    if len(pts) < 3:
        raise ValueError('Cutout profile needs at least three corners.')
    # Remove adjacent duplicates and exactly collinear intermediate vertices.
    pruned=[]
    for xy in pts:
        if not pruned or math.dist(xy,pruned[-1])>1e-7:
            pruned.append(xy)
    if len(pruned)>2 and math.dist(pruned[0],pruned[-1])<1e-7:pruned.pop()
    if len(pruned)<3:raise ValueError('Degenerate cutout polygon.')
    pts=pruned
    corners=[]
    for i, p in enumerate(pts):
        prev,nxt=pts[i-1],pts[(i+1)%len(pts)]
        len1=math.dist(prev,p);len2=math.dist(p,nxt)
        if min(len1,len2)<1e-7:raise ValueError('Coincident cutout corners.')
        u=((p[0]-prev[0])/len1,(p[1]-prev[1])/len1)
        v=((nxt[0]-p[0])/len2,(nxt[1]-p[1])/len2)
        turn=math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1])
        if abs(turn)<1e-6:
            corners.append((p,p,None,0.))
            continue
        # Tangency distance measured along each incoming/outgoing segment.
        t=radius*math.tan(abs(turn)/2)
        if not math.isfinite(t) or t<0:
            raise ValueError('Cutout has a degenerate corner.')
        entry=(p[0]-u[0]*t,p[1]-u[1]*t)
        exit=(p[0]+v[0]*t,p[1]+v[1]*t)
        sign=1 if turn>0 else -1
        center=(entry[0]-u[1]*radius*sign,entry[1]+u[0]*radius*sign)
        a=math.atan2(entry[1]-center[1],entry[0]-center[0])
        mid=(center[0]+radius*math.cos(a+turn/2),center[1]+radius*math.sin(a+turn/2))
        corners.append((entry,exit,mid,t))
    for i, (_,_,_,t) in enumerate(corners):
        # Every edge must have nonnegative length between tangent points.
        prev=pts[i-1];cur=pts[i]
        segment=math.dist(prev,cur)
        if t+corners[i-1][3]>segment-1e-5:
            raise ValueError('This profile is too narrow for R0.5. Increase its width/length.')
    segments=[]
    for i,c in enumerate(corners):
        previous=corners[i-1]
        if math.dist(previous[1],c[0])>1e-7:
            segments.append(('line',previous[1],c[0]))
        if c[2] is not None:
            segments.append(('arc',c[0],c[2],c[1]))
    if not segments:raise ValueError('Cutout rounding removed every edge.')
    return segments


def arc_slot_profile_segments(width, length, arc_angle):
    """Analytic, round-ended curved channel, centred on the local Y axis.

    ``length`` is the chord between end-cap *centres* (not the arc length).
    A positive bend bulges toward +X; negative bends toward -X. The centre
    follows a circular arc, its sides are exactly concentric offset arcs,
    and both ends have tangent semicircular caps. No polygonal approximation
    is used in either FreeCAD or the Qt preview.

    Returns four connected line/three-point-arc segments, anticlockwise or
    clockwise depending on handedness. A zero-degree bend is a straight
    round-ended channel and deliberately avoids large-radius arithmetic.
    """
    w, chord, angle = float(width), float(length), float(arc_angle)
    if not all(math.isfinite(v) for v in (w, chord, angle)):
        raise ValueError('Arc slot dimensions and bend must be finite.')
    if w < 1.0 or chord < w + .5:
        raise ValueError('Arc slot requires width ≥1 mm and a chord at least 0.5 mm longer than its width.')
    if abs(angle) > 170.0 + 1e-8:
        raise ValueError('Arc slot bend must be between -170° and +170°.')
    # Tiny nonzero sweeps require very large circle centres and can suffer
    # OpenCASCADE / Qt three-point-arc precision loss.  Use 0° explicitly
    # for a straight channel rather than silently approximating the bend.
    if 1e-7 < abs(angle) < 3.0:
        raise ValueError('Arc slot bend must be 0° or at least 3° in either direction.')
    half_width = w / 2.0
    if abs(angle) < 1e-7:
        # Start and end cap centres: (0,-chord/2) and (0,+chord/2).
        return (
            ('line', (half_width,-chord/2), (half_width,chord/2)),
            ('arc', (half_width,chord/2), (0.,chord/2+half_width), (-half_width,chord/2)),
            ('line', (-half_width,chord/2), (-half_width,-chord/2)),
            ('arc', (-half_width,-chord/2), (0.,-chord/2-half_width), (half_width,-chord/2)),
        )
    sign = 1 if angle > 0 else -1
    half_sweep = math.radians(abs(angle)) / 2.0
    radius = chord / (2.0 * math.sin(half_sweep))
    # The inside curvature is concave for one side of the channel. Never
    # silently violate the R0.5 mm minimum CNC cutter radius.
    if radius-half_width < MIN_INTERNAL_RADIUS - 1e-8:
        raise ValueError('Arc slot inside radius is below R0.5 mm; increase chord or reduce width/bend.')
    cx = -sign * radius * math.cos(half_sweep)
    def polar(r, t):
        alpha = t if sign > 0 else math.pi - t
        return (cx + r*math.cos(alpha), r*math.sin(alpha))
    def tangent(t):
        alpha = t if sign > 0 else math.pi - t
        # d(x,y)/dt always advances from the bottom cap to the top cap.
        return (-sign*math.sin(alpha), sign*math.cos(alpha))
    start, mid, end = -half_sweep, 0.0, half_sweep
    out_radius, in_radius = radius+half_width, radius-half_width
    so, mo, eo = polar(out_radius,start), polar(out_radius,mid), polar(out_radius,end)
    ei, mi, si = polar(in_radius,end), polar(in_radius,mid), polar(in_radius,start)
    ce, cs = polar(radius,end), polar(radius,start)
    te, ts = tangent(end), tangent(start)
    end_cap_mid=(ce[0]+half_width*te[0],ce[1]+half_width*te[1])
    start_cap_mid=(cs[0]-half_width*ts[0],cs[1]-half_width*ts[1])
    return (
        ('arc', so, mo, eo),
        ('arc', eo, end_cap_mid, ei),
        ('arc', ei, mi, si),
        ('arc', si, start_cap_mid, so),
    )


@lru_cache(maxsize=512)
def _cached_profile_segments(shape, width, length, vertices, arc_angle):
    """Immutable local CNC profile shared by validation, Qt and FreeCAD.

    Translation and rotation are deliberately excluded: they are applied by
    the caller, and must not cause a second round of expensive arc geometry.
    Keeping only 512 profiles also bounds memory during repeated Randomize.
    """
    pattern = {'shape': shape, 'width': width, 'length': length}
    if shape == 'Web cell':
        pattern['vertices'] = vertices
    if shape == 'Arc slot':
        return tuple(arc_slot_profile_segments(width, length, arc_angle))
    return tuple(rounded_polygon_segments(cutout_polygon(pattern)))


def cutout_profile_segments(pattern):
    """Return immutable analytic R0.5 line/arc segments for a local cutout."""
    vertices = (tuple(tuple(v) for v in (pattern.get('vertices') or ()))
                if pattern['shape'] == 'Web cell' else ())
    return _cached_profile_segments(pattern['shape'], pattern['width'],
                                    pattern['length'], vertices, pattern.get('arc_angle',75.))


def _check_web_vertices(vertices):
    """Reject malformed, overlapping or self-crossing saved cell polygons."""
    if not isinstance(vertices,(list,tuple)) or not 3<=len(vertices)<=40:
        raise ValueError('Automatic web cell must contain 3–40 profile vertices.')
    points=[]
    for item in vertices:
        if not isinstance(item,(list,tuple)) or len(item)!=2:
            raise ValueError('Invalid web cell vertex.')
        u,v=item
        if (any(isinstance(k,bool) or not isinstance(k,(int,float)) or not math.isfinite(k)
                for k in (u,v)) or max(abs(u),abs(v))>.501):
            raise ValueError('Web cell coordinates must be finite and normalized to ±0.5.')
        points.append((float(u),float(v)))
    area=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1]))*.5
    if abs(area)<.007:raise ValueError('Web cell has insufficient enclosed area.')
    def crossing(a,b,c,d):
        def orient(p,q,r):return ((q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0]))
        return orient(a,b,c)*orient(a,b,d)<-1e-11 and orient(c,d,a)*orient(c,d,b)<-1e-11
    n=len(points)
    for i in range(n):
        for j in range(i+2,n):
            if i==0 and j==n-1:continue
            if crossing(points[i],points[(i+1)%n],points[j],points[(j+1)%n]):
                raise ValueError('Web cell contour intersects itself.')
    return points


def check_cnc_shape(pattern):
    """Validate the machining curvature of a new/editable shape."""
    w,l=pattern['width'],pattern['length']
    name=pattern['shape']
    if name=='Web cell':
        _check_web_vertices(pattern.get('vertices') or [(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)])
    if name in CNC_POLYGON_TYPES:
        cutout_profile_segments(pattern)
    elif name=='Ellipse' and min(w,l)**2 < max(w,l)-1e-8:
        raise ValueError('Ellipse curvature is tighter than R0.5; widen its short axis.')
    elif name=='Circle' and w < 1:
        raise ValueError('Circle diameter must be at least 1 mm.')
    elif name=='Slot' and min(w,l)<1:
        raise ValueError('Slot width must be at least 1 mm.')
    elif name=='Arc slot':
        arc_slot_profile_segments(w,l,pattern.get('arc_angle',75.))
    elif name=='Rounded rectangle' and min(w,l)<2:
        raise ValueError('Rounded rectangle requires at least 2 mm on each axis.')


def _parse_patterns_uncached(value):
    if not isinstance(value, str):
        raise ValueError('CutoutPatterns must be a JSON string; use the Airflow editor.')
    try:
        items = json.loads(value)
    except (ValueError, TypeError) as exc:
        raise ValueError('Invalid airflow pattern JSON.') from exc
    if not isinstance(items, list) or len(items) > MAX_PATTERNS:
        raise ValueError(f'Use a list of at most {MAX_PATTERNS} saved cutout patterns.')
    result, count = [], 0
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict) or set(item)-set(PATTERN_DEFAULTS):
            raise ValueError(f'Airflow pattern {index} has unknown fields or is not an object.')
        pattern = dict(PATTERN_DEFAULTS, **item)
        if pattern['role'] not in CUTOUT_ROLES or pattern['shape'] not in LEGACY_CUTOUT_TYPES:
            raise ValueError(f'Airflow pattern {index}: unknown part or cutout type.')
        if pattern['mode'] not in CUTOUT_MODES:
            raise ValueError(f'Cutout pattern {index}: unknown cutting mode.')
        if pattern['mode'] in ('Outline notch','Add material') and pattern['role'] not in OUTLINE_ROLES:
            raise ValueError(f'Cutout pattern {index}: outline notches and additions are available on the main and clamp plates only.')
        if pattern['shape']=='Web cell':
            _check_web_vertices(pattern['vertices'] or [(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)])
        elif pattern['vertices']:
            raise ValueError(f'Airflow pattern {index}: custom vertices are only valid on web cells.')
        if not isinstance(pattern['enabled'], bool):
            raise ValueError(f'Airflow pattern {index}: enabled must be true or false.')
        if not isinstance(pattern['auto_keep'], bool):
            raise ValueError(f'Airflow pattern {index}: Keep must be true or false.')
        if (not isinstance(pattern['auto_group'], str) or len(pattern['auto_group']) > 32 or
                any(c not in '0123456789abcdef' for c in pattern['auto_group'])):
            raise ValueError(f'Airflow pattern {index}: invalid automatic group reference.')
        if pattern['auto_keep'] and not pattern['auto_group']:
            raise ValueError(f'Airflow pattern {index}: only automatically generated cutouts can be kept.')
        for key in ('width', 'length', 'x', 'y', 'rotation', 'pitch_x', 'pitch_y', 'columns', 'rows', 'depth', 'auto_web', 'arc_angle'):
            v = pattern[key]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f'Airflow pattern {index}: {key} must be a finite number.')
        for key in ('columns', 'rows'):
            v = pattern[key]
            if int(v) != v or not 1 <= v <= 20:
                raise ValueError(f'Airflow pattern {index}: {key} must be an integer from 1 to 20.')
            pattern[key] = int(v)
        if not -170 <= pattern['arc_angle'] <= 170:
            raise ValueError(f'Airflow pattern {index}: arc bend must be between -170° and +170°.')
        if not 0 <= pattern['auto_web'] <= 50:
            raise ValueError(f'Airflow pattern {index}: automatic web must be 0–50 mm.')
        if not .1 <= pattern['depth'] <= 50:
            raise ValueError(f'Airflow pattern {index}: pocket depth must be 0.1–50 mm.')
        if pattern['mode']=='Pocket' and pattern['role'] not in CUTOUT_ROLES:
            raise ValueError(f'Airflow pattern {index}: pockets require a carbon part.')
        if not .5 <= pattern['width'] <= 200 or not .5 <= pattern['length'] <= 300:
            raise ValueError(f'Airflow pattern {index}: cutout dimensions are outside 0.5–200/300 mm.')
        # These profiles use exact R0.5 arcs both in 3D solids and Qt preview.
        # Free-form legacy Crescent/Leaf are not newly selectable.
        if pattern['shape'] in CUTOUT_TYPES or pattern['shape']=='Web cell':
            try:check_cnc_shape(pattern)
            except ValueError as exc:raise ValueError(f'Airflow pattern {index}: {exc}') from exc
        if max(abs(pattern['x']), abs(pattern['y'])) > 700 or abs(pattern['rotation']) > 360:
            raise ValueError(f'Airflow pattern {index}: position or rotation is out of range.')
        if not 0 < pattern['pitch_x'] <= 500 or not 0 < pattern['pitch_y'] <= 500:
            raise ValueError(f'Airflow pattern {index}: pitches must be greater than zero and at most 500 mm.')
        count += pattern['columns'] * pattern['rows'] if pattern['enabled'] else 0
        result.append(pattern)
    if count > MAX_ENABLED_CUTOUTS:
        raise ValueError(f'Use at most {MAX_ENABLED_CUTOUTS} enabled cutouts per frame, including grid instances. Disable or remove a pattern, or reduce its rows / columns.')
    return result


@lru_cache(maxsize=48)
def _parsed_patterns_cached(value):
    # The canonical value is an immutable string. Keep the validated dictionaries
    # private to the cache so no caller can corrupt subsequent parse results.
    return tuple(_parse_patterns_uncached(value))


def parse_patterns(value):
    """Validate once per JSON value; return independent, editable patterns."""
    if not isinstance(value, str):
        raise ValueError('CutoutPatterns must be a JSON string; use the Airflow editor.')
    return [dict(pattern) for pattern in _parsed_patterns_cached(value)]


def encode_patterns(patterns):
    return json.dumps(parse_patterns(json.dumps(patterns, allow_nan=False)), separators=(',', ':'), allow_nan=False)


def pattern_instances(pattern):
    """A centred grid; rotation applies to the grid and every cutout."""
    angle = math.radians(pattern['rotation'])
    c, s = math.cos(angle), math.sin(angle)
    for row in range(pattern['rows']):
        for column in range(pattern['columns']):
            u = (column-(pattern['columns']-1)/2)*pattern['pitch_x']
            v = (row-(pattern['rows']-1)/2)*pattern['pitch_y']
            yield dict(pattern, x=pattern['x']+u*c-v*s, y=pattern['y']+u*s+v*c,
                       columns=1, rows=1)


def cutouts_for(p, role):
    return tuple(instance for pattern in parse_patterns(p.CutoutPatterns)
                 if pattern['enabled'] and pattern['role'] == role for instance in pattern_instances(pattern))
