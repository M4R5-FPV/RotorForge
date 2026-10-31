"""Portable per-part airflow patterns. Camera coordinates are Y offset / height."""
import json
import math

CUTOUT_ROLES = ('BottomPlate', 'MidPlate', 'TopPlate', 'ArmClampPlate', 'ArmKeystone',
                'CameraMountLeft', 'CameraMountRight', 'ArmFrontRight', 'ArmFrontLeft',
                'ArmRearLeft', 'ArmRearRight', 'ArmLowerClampPlate')
CUTOUT_TYPES = ('Circle', 'Slot', 'Rounded rectangle', 'Hexagon',
                'Ellipse', 'Rectangle', 'Triangle', 'Diamond', 'Trapezoid', 'Pentagon', 'Octagon', 'Chevron', 'Heptagon', 'Dodecagon', 'Parallelogram', 'Kite', 'Hourglass', 'Cross', 'Crescent', 'Leaf')
OUTLINE_ROLES = ('BottomPlate', 'MidPlate', 'TopPlate', 'ArmClampPlate', 'ArmLowerClampPlate')
CUTOUT_MODES = ('Interior', 'Outline notch')
MAX_PATTERNS = 200
MAX_ENABLED_CUTOUTS = 200
PATTERN_DEFAULTS = dict(mode='Interior', role='TopPlate', shape='Slot', width=4., length=12., x=0., y=0.,
                        rotation=0., columns=1, rows=1, pitch_x=10., pitch_y=16., enabled=True)


def cutout_polygon(pattern):
    """Local polygon vertices shared by exact CAD and the editor preview."""
    w,l=pattern['width'],pattern['length'];name=pattern['shape']
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


def parse_patterns(value):
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
        if pattern['role'] not in CUTOUT_ROLES or pattern['shape'] not in CUTOUT_TYPES:
            raise ValueError(f'Airflow pattern {index}: unknown part or cutout type.')
        if pattern['mode'] not in CUTOUT_MODES:
            raise ValueError(f'Cutout pattern {index}: unknown cutting mode.')
        if pattern['mode']=='Outline notch' and pattern['role'] not in OUTLINE_ROLES:
            raise ValueError(f'Cutout pattern {index}: outline notches are available on the main and clamp plates only.')
        if not isinstance(pattern['enabled'], bool):
            raise ValueError(f'Airflow pattern {index}: enabled must be true or false.')
        for key in ('width', 'length', 'x', 'y', 'rotation', 'pitch_x', 'pitch_y', 'columns', 'rows'):
            v = pattern[key]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f'Airflow pattern {index}: {key} must be a finite number.')
        for key in ('columns', 'rows'):
            v = pattern[key]
            if int(v) != v or not 1 <= v <= 20:
                raise ValueError(f'Airflow pattern {index}: {key} must be an integer from 1 to 20.')
            pattern[key] = int(v)
        if not .5 <= pattern['width'] <= 200 or not .5 <= pattern['length'] <= 300:
            raise ValueError(f'Airflow pattern {index}: cutout dimensions are outside 0.5–200/300 mm.')
        if max(abs(pattern['x']), abs(pattern['y'])) > 700 or abs(pattern['rotation']) > 360:
            raise ValueError(f'Airflow pattern {index}: position or rotation is out of range.')
        if not 0 < pattern['pitch_x'] <= 500 or not 0 < pattern['pitch_y'] <= 500:
            raise ValueError(f'Airflow pattern {index}: pitches must be greater than zero and at most 500 mm.')
        count += pattern['columns'] * pattern['rows'] if pattern['enabled'] else 0
        result.append(pattern)
    if count > MAX_ENABLED_CUTOUTS:
        raise ValueError(f'Use at most {MAX_ENABLED_CUTOUTS} enabled cutouts per frame, including grid instances. Disable or remove a pattern, or reduce its rows / columns.')
    return result


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
