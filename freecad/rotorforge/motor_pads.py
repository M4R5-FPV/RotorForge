"""Motor-bearing outlines, neck reliefs and mirrored orientation without CAD imports."""
import math
from functools import lru_cache
from .plate_profiles import polygon_interior_distance
EXTENDED_MOTOR_PAD_SHAPES=('Tapered nose','Arrowhead')
RETAINED_PAD_SHAPES=('Round','Rounded square','Chamfered square','Four-lobe','Tapered nose','Arrowhead','Teardrop','Shouldered','Compact hex','Scalloped shield')
NEW_MOTOR_PAD_SHAPES=('Crown shield', 'Twin-scallop shield', 'Tri-scallop shield', 'Recessed-nose shield', 'Swept-shoulder shield', 'Waist-scallop shield', 'Broad-crown shield', 'Faceted-scallop shield', 'Round-shoulder shield', 'Twin-cheek shield', 'Split-crown shield', 'Compact-scallop shield')
REALISTIC_MOTOR_PAD_SHAPES=RETAINED_PAD_SHAPES[6:]+NEW_MOTOR_PAD_SHAPES
MOTOR_PAD_SHAPES=RETAINED_PAD_SHAPES+NEW_MOTOR_PAD_SHAPES
REPLACED_PAD_SHAPES={'Swept shield': 'Broad-crown shield', 'Wide shoulder': 'Twin-cheek shield', 'Clipped round': 'Recessed-nose shield', 'Dogbone': 'Waist-scallop shield', 'Twin scallop': 'Split-crown shield', 'Long shield': 'Round-shoulder shield', 'Bell': 'Twin-cheek shield', 'Waisted shield': 'Broad-crown shield', 'Diagonal ears': 'Crown shield', 'Hammerhead': 'Waist-scallop shield', 'Flat twin-lobe': 'Recessed-nose shield', 'Recessed cross': 'Twin-scallop shield', 'Vented spear': 'Round-shoulder shield', 'Rounded visor': 'Faceted-scallop shield', 'Blunt arrow': 'Compact-scallop shield', 'Double ear': 'Crown shield', 'Octagonal nose': 'Tri-scallop shield', 'Rounded diamond': 'Tri-scallop shield', 'Winged nose': 'Twin-cheek shield', 'Long oval': 'Swept-shoulder shield', 'Stepped shoulder': 'Round-shoulder shield', 'Fork shoulder': 'Twin-cheek shield', 'Wide paddle': 'Waist-scallop shield', 'Bolt-following round': 'Crown shield', 'Bolt-following facets': 'Twin-scallop shield', 'Compact octagon': 'Tri-scallop shield', 'Flat nose round': 'Recessed-nose shield', 'Long oval platform': 'Swept-shoulder shield', 'Wide oval platform': 'Waist-scallop shield', 'Short shield': 'Broad-crown shield', 'Rounded shield': 'Faceted-scallop shield', 'Reinforced neck': 'Round-shoulder shield', 'Flared neck': 'Twin-cheek shield', 'Side relief round': 'Split-crown shield', 'Clipped shield': 'Compact-scallop shield'}

def motor_pad_rotation(p,arm):
    """Clock front-right/rear-left opposite to the two reflected corners."""
    mx,my=arm.get('nominal_motor',arm['motor'])
    return p.MotorPadRotation*(1 if mx*my>=0 else -1)


def motor_pad_unit(p,arm):
    ux,uy=arm['unit'];a=math.radians(motor_pad_rotation(p,arm))
    return (ux*math.cos(a)-uy*math.sin(a),ux*math.sin(a)+uy*math.cos(a))


def motor_pad_start(p):
    """Root-facing extent of the unrotated additive pad profile."""
    return min(d['centre'][0]-d['radius'] if d['kind']=='circle' else
               -d['width']/2 if d['kind']=='rounded' else min(x for x,y in d['points'])
               for d in _base_motor_pad_primitives(p) if d.get('operation')!='cut')


def motor_pad_pose(p,arm):
    """Return fixed pivot and transformed motor centre in frame coordinates."""
    mx,my=arm.get('nominal_motor',arm['motor']);ux,uy=arm['unit']
    if p.MotorPadRotationPivot=='Motor centre':return (mx,my),(mx,my)
    distance=-motor_pad_start(p)
    pivot=(mx-distance*ux,my-distance*uy)
    pux,puy=motor_pad_unit(p,arm)
    return pivot,(pivot[0]+distance*pux,pivot[1]+distance*puy)


def extended_motor_pad(p):
    return p.MotorPadShape in EXTENDED_MOTOR_PAD_SHAPES


def motor_corner_control(p):
    return p.MotorPadShape in ('Rounded square','Chamfered square','Shouldered','Scalloped shield') or p.MotorPadShape in EXTENDED_MOTOR_PAD_SHAPES+NEW_MOTOR_PAD_SHAPES


def _legacy_motor_pad_primitives(p):
    half=p.MotorPadDiameter/2
    radius=min(p.MotorPadCornerRadius,half-.01)
    if p.MotorPadShape == 'Round':
        return (dict(kind='circle', centre=(0.,0.), radius=half),)
    if p.MotorPadShape == 'Rounded square':
        return (dict(kind='rounded', width=2*half, radius=radius),)
    if p.MotorPadShape == 'Chamfered square':
        points = ((-half+radius,-half),(half-radius,-half),(half,-half+radius),(half,half-radius),
                  (half-radius,half),(-half+radius,half),(-half,half-radius),(-half,-half+radius))
        return (dict(kind='polygon', points=points),)
    if p.MotorPadShape == 'Teardrop':
        back,neck=1.6*half,p.ArmWidth/2
        distance2=back*back+neck*neck
        factor=half*math.sqrt(max(0,distance2-half*half))/distance2
        tx=-back*half*half/distance2+neck*factor
        ty=neck*half*half/distance2+back*factor
        points=((-back,-neck),(tx,-ty),(tx,ty),(-back,neck))
        return (dict(kind='circle',centre=(0.,0.),radius=half),dict(kind='polygon',points=points))
    if p.MotorPadShape == 'Compact hex':
        return (dict(kind='polygon',points=((-half,-.6*half),(0.,-half),(half,-.6*half),
                     (half,.6*half),(0.,half),(-half,.6*half))),)
    if p.MotorPadShape in ('Shouldered','Scalloped shield'):
        points=((-1.6*half,-p.ArmWidth/2),(-.45*half,-half),
                (half-radius,-half),(half,-half+radius),(half,half-radius),
                (half-radius,half),(-.45*half,half),(-1.6*half,p.ArmWidth/2))
        primitives=(dict(kind='polygon',points=points),)
        if p.MotorPadShape=='Scalloped shield':
            primitives+=tuple(dict(kind='circle',centre=c,radius=radius,operation='cut')
                              for c in ((0.,half+1),(0.,-half-1),(half+1,0.)))
        return primitives
    if extended_motor_pad(p):
        shoulder=half*.5
        nose_half=half*(.1 if p.MotorPadShape=='Tapered nose' else .5)
        points=((-half,-half+radius),(-half+radius,-half),(shoulder,-half),
                (half+p.MotorTipLength,-nose_half),(half+p.MotorTipLength,nose_half),
                (shoulder,half),(-half+radius,half),(-half,half-radius))
        return (dict(kind='polygon',points=points),)
    ear_radius = half-max(p.MotorSpacingX,p.MotorSpacingY)/2
    return (dict(kind='circle', centre=(0.,0.), radius=max(p.MotorCenterDiameter/2+p.MinimumWeb,half*.6)),)+tuple(
        dict(kind='circle', centre=(x,y), radius=ear_radius)
        for x in (-p.MotorSpacingX/2,p.MotorSpacingX/2) for y in (-p.MotorSpacingY/2,p.MotorSpacingY/2))



def convex_hull(points):
    pts=sorted(set(points))
    cross=lambda a,b,c:(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    halves=[]
    for seq in (pts,pts[::-1]):
        half=[]
        for pt in seq:
            while len(half)>=2 and cross(half[-2],half[-1],pt)<=0:half.pop()
            half.append(pt)
        halves.append(half[:-1])
    return tuple(halves[0]+halves[1])


def _base_motor_pad_primitives(p):
    if p.MotorPadShape not in NEW_MOTOR_PAD_SHAPES:return _legacy_motor_pad_primitives(p)
    h=p.MotorPadDiameter/2;n=p.MotorPadShape;w=p.ArmWidth/2;back=-h-p.MotorPadNeckLength
    polygon=lambda pts:dict(kind='polygon',points=tuple(pts))
    # Each shield has a solid bearing deck and a continuous tapered neck.
    # (rear shoulder X, nose corner X, nose half-height, corner chamfer)
    specs={
      'Crown shield':(-.55,.68,.70,.22),
      'Twin-scallop shield':(-.35,.72,.65,.25),
      'Tri-scallop shield':(-.50,.70,.70,.24),
      'Recessed-nose shield':(-.65,.80,.80,.18),
      'Swept-shoulder shield':(-.12,.60,.65,.28),
      'Waist-scallop shield':(-.70,.72,.72,.20),
      'Broad-crown shield':(-.45,.82,.82,.16),
      'Faceted-scallop shield':(-.60,.55,.55,.30),
      'Round-shoulder shield':(-.35,.62,.62,.24),
      'Twin-cheek shield':(-.55,.85,.85,.15),
      'Split-crown shield':(-.40,.78,.78,.18),
      'Compact-scallop shield':(-.40,.60,.60,.28),
    }
    rear,nose,tip,clip=specs[n]
    outline=((back,-w),(rear*h,-h),(nose*h,-h),(h,-tip*h),
             (h,tip*h),(nose*h,h),(rear*h,h),(back,w))
    deck=polygon(outline)
    # Round shoulder uses sampled quadratic curves instead of angular shoulders.
    if n=='Round-shoulder shield':
        pts=[(back,-w)]
        for i in range(1,17):
            t=i/16;pts.append(((1-t)**2*back+2*(1-t)*t*(-h)+t*t*.4*h,
                              (1-t)**2*(-w)+2*(1-t)*t*(-h)+t*t*(-h)))
        pts += [(nose*h,-h),(h,-tip*h),(h,tip*h),(nose*h,h),(.4*h,h)]
        pts += [(x,-y) for x,y in reversed(pts[1:17])]
        pts.append((back,w));deck=polygon(pts)
    primitives=[deck]
    # Shallow external scallops leave the motor screw lands intact. The existing
    # corner control sets scallop depth; material validation remains authoritative.
    depth=min(.18*h,p.MotorPadCornerRadius*.32)
    cuts={
      'Crown shield':((1,0,.42),),
      'Twin-scallop shield':((0,1,.36),(0,-1,.36)),
      'Tri-scallop shield':((0,1,.32),(0,-1,.32),(1,0,.36)),
      'Recessed-nose shield':((1,0,.62),),
      'Swept-shoulder shield':((.24,1,.33),(.24,-1,.33)),
      'Waist-scallop shield':((-.36,1,.42),(-.36,-1,.42)),
      'Broad-crown shield':((1,0,.28),(0,1,.22),(0,-1,.22)),
      'Faceted-scallop shield':((0,1,.27),(0,-1,.27),(1,0,.27)),
      'Round-shoulder shield':((1,0,.40),),
      'Twin-cheek shield':((.30,1,.36),(.30,-1,.36)),
      'Split-crown shield':((1,.37,.25),(1,-.37,.25)),
      'Compact-scallop shield':((0,1,.45),(0,-1,.45)),
    }[n]
    for x,y,r in cuts:
        radius=r*h
        cx=x*h+(radius-depth if x==1 else 0)
        cy=y*h+(math.copysign(radius-depth,y) if abs(y)==1 else 0)
        primitives.append(dict(kind='circle',centre=(cx,cy),radius=radius,operation='cut'))
    return tuple(primitives)

def motor_pad_interior(point, p):
    x, y = point
    half = p.MotorPadDiameter/2
    if p.MotorPadShape in REALISTIC_MOTOR_PAD_SHAPES+NEW_MOTOR_PAD_SHAPES:
        positive=[];negative=[]
        for d in _base_motor_pad_primitives(p):
            inside=(d['radius']-math.dist(point,d['centre']) if d['kind']=='circle' else polygon_interior_distance(point,d['points']))
            (negative if d.get('operation')=='cut' else positive).append(inside)
        return min([max(positive)]+[-v for v in negative])
    if p.MotorPadShape == 'Round':
        return half-math.hypot(x,y)
    if p.MotorPadShape == 'Rounded square':
        r = min(p.MotorPadCornerRadius,half-.01)
        qx,qy=abs(x)-(half-r),abs(y)-(half-r)
        return r-math.hypot(max(qx,0),max(qy,0))-min(max(qx,qy),0)
    if p.MotorPadShape == 'Chamfered square':
        r=min(p.MotorPadCornerRadius,half-.01)
        return min(half-abs(x),half-abs(y),(2*half-r-abs(x)-abs(y))/math.sqrt(2))
    if extended_motor_pad(p):
        return polygon_interior_distance(point,_base_motor_pad_primitives(p)[0]['points'])
    return max(d['radius']-math.dist(point,d['centre']) for d in _base_motor_pad_primitives(p))


def motor_pad_bound(p):
    if p.MotorPadShape in REALISTIC_MOTOR_PAD_SHAPES+NEW_MOTOR_PAD_SHAPES:
        return max(math.hypot(*d['centre'])+d['radius'] if d['kind']=='circle' else max(math.hypot(x,y) for x,y in d['points'])
                   for d in _base_motor_pad_primitives(p) if d.get('operation')!='cut')
    if extended_motor_pad(p):
        return max(math.hypot(x,y) for x,y in _base_motor_pad_primitives(p)[0]['points'])
    return p.MotorPadDiameter/2 if p.MotorPadShape=='Round' else p.MotorPadDiameter/math.sqrt(2)


def motor_tip_slots(p,arm=None):
    """Separate reliefs in the neck, or the two retained extended-tip designs."""
    if p.MotorPadShape in NEW_MOTOR_PAD_SHAPES:
        if p.MotorPadRelief=='None':return ()
        radius=p.MotorPadReliefWidth/2
        travel=0 if p.MotorPadRelief=='Twin neck holes' else max(0,(p.MotorPadReliefLength-2*radius)/2)
        centre=-p.MotorPadDiameter/2-p.MotorPadNeckLength/2
        ys=(0.,) if p.MotorPadRelief=='Neck slot' else (-radius-p.MinimumWeb/2,radius+p.MinimumWeb/2)
        slots=tuple(((centre-travel,y),(centre+travel,y),radius) for y in ys)
    else:
        if not extended_motor_pad(p) or not p.MotorTipSlotEnabled:return ()
        radius=p.MotorTipSlotWidth/2;travel=max(0,(p.MotorTipSlotLength-p.MotorTipSlotWidth)/2)
        centre=p.MotorPadDiameter/2+p.MotorTipLength/4
        slots=(((centre-travel,0.),(centre+travel,0.),radius),)
    if arm is None:return slots
    ux,uy=motor_pad_unit(p,arm);mx,my=arm['motor']
    transform=lambda pt:(mx+ux*pt[0]-uy*pt[1],my+uy*pt[0]+ux*pt[1])
    return tuple((transform(a),transform(b),r) for a,b,r in slots)



def _clip_front(points,minimum):
    result=[]
    for a,b in zip(points[-1:]+points[:-1],points):
        ia,ib=a[0]>=minimum,b[0]>=minimum
        if ia!=ib:
            t=(minimum-a[0])/(b[0]-a[0]);result.append((minimum,a[1]+t*(b[1]-a[1])))
        if ib:result.append(b)
    return result


def _inset_polygon(points,wall):
    lines=[];area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]));sign=1 if area>0 else -1
    for a,b in zip(points,points[1:]+points[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if length<1e-8:continue
        lines.append(((a[0]-sign*dy/length*wall,a[1]+sign*dx/length*wall),(dx/length,dy/length)))
    out=[]
    for (a,u),(b,v) in zip(lines[-1:]+lines[:-1],lines):
        cross=u[0]*v[1]-u[1]*v[0]
        if abs(cross)<1e-8:out.append(b);continue
        t=((b[0]-a[0])*v[1]-(b[1]-a[1])*v[0])/cross;out.append((a[0]+t*u[0],a[1]+t*u[1]))
    return out


# These are true additive arm-tip/bumpers, NOT motor pad outline selections.
# Motor-bearing geometry and the motor mounting pattern are never altered.
REFERENCE_ARM_TIP_STYLES=(
    'Seeker arrow', 'Matey swept hook', 'SR-Beast sweep',
    'Podracer spear', 'Master hex', 'Vertex dagger', 'Volador fork',
)
ASYMMETRIC_ARM_TIP_STYLES=frozenset(('Matey swept hook','SR-Beast sweep','Vertex dagger'))
ARM_TIP_STYLES=('Disabled','Round cap','Oval cap','Soft square','Chamfered cap','Tapered cap','Shallow arch')+REFERENCE_ARM_TIP_STYLES
LEGACY_ARM_TIPS={'Round nose':'Round cap','Rounded guard':'Round cap','Rounded paddle':'Oval cap','Elliptic nose':'Oval cap','Wide bow':'Oval cap','Soft shoulders':'Round cap','Flat guard':'Soft square','Hammerhead':'Soft square','Stepped paddle':'Soft square'}
LEGACY_ARM_TIPS.update({name:'Chamfered cap' for name in ('Faceted shield','Forked nose','Spear tip','Swept blade','Beveled nose','Chisel tip','Chevron tip','Twin prong','Flared shield','Chamfered guard')})
def arm_tip_style(style):
    return style if style in ARM_TIP_STYLES else LEGACY_ARM_TIPS.get(style,style)

def _arm_tip_direction_sign(p, arm):
    """Mirror asymmetric bumper silhouettes without changing the motor pad.

    +Y of the frame points toward the FRONT.  Local +Y of a motor pad
    becomes (-pad_unit_y, +pad_unit_x) in world coordinates.  Choose the
    side whose world projection is frontward on a front arm and rearward
    on a rear arm.  On sideways-outward mode, choose the outward edge.
    This also works for Deadcat and rotated motor platforms.
    """
    if arm is None:
        return 1
    ux,uy=motor_pad_unit(p,arm)
    mx,my=arm.get('nominal_motor',arm['motor'])
    if p.ArmTipBumperDirection=='Sideways outwards':
        projection=-uy*(1 if mx>=0 else -1)
    else:
        projection=ux*(1 if my>=0 else -1)
    return -1 if projection < 0 else 1


def _round_inner_corner(points,index,radius):
    """Tangent circular fillet for the Volador fork's concave CNC notch."""
    pts=list(points);v=pts[index];a=pts[index-1];b=pts[(index+1)%len(pts)]
    va=(a[0]-v[0],a[1]-v[1]);vb=(b[0]-v[0],b[1]-v[1])
    la,lb=math.hypot(*va),math.hypot(*vb)
    if min(la,lb)<1e-9:return tuple(pts)
    ua=(va[0]/la,va[1]/la);ub=(vb[0]/lb,vb[1]/lb)
    theta=math.acos(max(-1.,min(1.,ua[0]*ub[0]+ua[1]*ub[1])))
    if theta<.05 or theta>math.pi-.05:return tuple(pts)
    travel=radius/math.tan(theta/2.)
    if travel > .45*min(la,lb):
        # At very short extensions, the fork is below machinable size.
        # The caller uses a simple nose in that case.
        return None
    bis=(ua[0]+ub[0],ua[1]+ub[1]);scale=math.hypot(*bis)
    centre=(v[0]+radius/math.sin(theta/2)*bis[0]/scale,
            v[1]+radius/math.sin(theta/2)*bis[1]/scale)
    t0=(v[0]+ua[0]*travel,v[1]+ua[1]*travel)
    t1=(v[0]+ub[0]*travel,v[1]+ub[1]*travel)
    a0=math.atan2(t0[1]-centre[1],t0[0]-centre[0]);a1=math.atan2(t1[1]-centre[1],t1[0]-centre[0])
    arc_delta=(a1-a0+math.pi)%(2*math.pi)-math.pi
    arc=[(centre[0]+radius*math.cos(a0+arc_delta*i/16),
          centre[1]+radius*math.sin(a0+arc_delta*i/16)) for i in range(17)]
    return tuple(pts[:index]+arc+pts[index+1:])


def _reference_arm_tip_points(p,style,start,end,half,reach):
    """Local additive bumper shell.  Root is inside the unchanged motor pad.

    These silhouettes use only Arm-tip bumper width/reach.  They never touch
    MotorPadShape/MotorTipLength or alter motor centres or screw holes.
    """
    h=half;r=reach
    x0=start
    shoulder=end-min(2.,.18*r)
    profiles={
        'Seeker arrow':[
            (x0,-.78*h),(shoulder,-.88*h),(end+.35*r,-.72*h),
            (end+.76*r,-.40*h),(end+r,0.),
            (end+.76*r,.40*h),(end+.35*r,.72*h),(shoulder,.88*h),(x0,.78*h)],
        'Matey swept hook':[
            (x0,-.74*h),(shoulder,-.84*h),(end+.53*r,-.70*h),
            (end+.84*r,-.40*h),(end+.73*r,.14*h),
            (end+r,.70*h),(end+.66*r,h),(shoulder,.91*h),(x0,.74*h)],
        'SR-Beast sweep':[
            (x0,-.76*h),(shoulder,-.86*h),(end+.41*r,-.76*h),
            (end+.86*r,-.32*h),(end+r,.32*h),
            (end+.62*r,.82*h),(shoulder,h),(x0,.76*h)],
        'Podracer spear':[
            (x0,-.70*h),(shoulder,-.78*h),(end+.27*r,-.48*h),
            (end+.72*r,-.18*h),(end+r,0),
            (end+.72*r,.18*h),(end+.27*r,.48*h),(shoulder,.78*h),(x0,.70*h)],
        'Master hex':[
            (x0,-.82*h),(shoulder,-.93*h),(end+.55*r,-.82*h),
            (end+r,-.34*h),(end+r,.34*h),(end+.55*r,.82*h),
            (shoulder,.93*h),(x0,.82*h)],
        'Vertex dagger':[
            (x0,-.72*h),(shoulder,-.84*h),(end+.47*r,-.70*h),
            (end+r,-.12*h),(end+.84*r,.22*h),
            (end+.39*r,.58*h),(shoulder,.90*h),(x0,.72*h)],
        'Volador fork':[
            (x0,-.82*h),(shoulder,-.90*h),(end+r,-.78*h),
            (end+.66*r,-.23*h),(end+.36*r,0.),
            (end+.66*r,.23*h),(end+r,.78*h),(shoulder,.90*h),(x0,.82*h)],
    }
    pts=profiles[style]
    if style=='Volador fork':
        rounded=_round_inner_corner(pts,4,max(.5,p.CNCToolRadius))
        if rounded is None:
            # Not enough room for a proper R0.5 concave CNC corner:
            # keep a blunt cap until the user increases bumper reach.
            pts=[(x0,-.82*h),(shoulder,-.90*h),(end+r,-.70*h),
                 (end+r,.70*h),(shoulder,.90*h),(x0,.82*h)]
        else:pts=rounded
    return tuple(pts)


def _ray_to_tip_boundary(origin, direction, points):
    """Furthest forward intersection of a ray with an actual asymmetric tip."""
    ox, oy = origin
    dx, dy = direction
    furthest = None
    for a, b in zip(points, points[1:] + points[:1]):
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = dx * ey - dy * ex
        if abs(den) < 1e-12:
            continue
        ax, ay = a[0] - ox, a[1] - oy
        t = (ax * ey - ay * ex) / den
        u = (ax * dy - ay * dx) / den
        if t > 0 and -1e-9 <= u <= 1 + 1e-9:
            furthest = t if furthest is None else max(furthest, t)
    return furthest


def _tip_protected_holes(p):
    """The bores are in local motor-pad coordinates, BEFORE arm orientation."""
    # Local import prevents a module cycle: parameters imports motor_pads.
    from .parameters import motor_hole_offsets
    return tuple((x, y, p.MotorHoleDiameter / 2) for x, y in motor_hole_offsets(p)) + (
        (0., 0., p.MotorCenterDiameter / 2),
    )


def _simplify_tip_chain(points, tolerance=.025):
    """Retain actual bends, discard dense straight/near-straight samples."""
    if len(points) <= 2:
        return list(points)
    a, b = points[0], points[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 1e-12:
        distances = [math.dist(a, point) for point in points[1:-1]]
    else:
        distances = [abs(dx * (point[1] - a[1]) - dy * (point[0] - a[0])) / length
                     for point in points[1:-1]]
    furthest = max(range(len(distances)), key=distances.__getitem__)
    if distances[furthest] <= tolerance:
        return [a, b]
    middle = furthest + 1
    return (_simplify_tip_chain(points[:middle+1], tolerance)[:-1] +
            _simplify_tip_chain(points[middle:], tolerance))


def _segment_point_gap(point, a, b):
    """Exact closest distance from a point to a finite 2-D segment."""
    dx,dy=b[0]-a[0],b[1]-a[1]
    length2=dx*dx+dy*dy
    t=max(0.,min(1.,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/length2)) if length2 else 0.
    return math.hypot(point[0]-a[0]-t*dx,point[1]-a[1]-t*dy)


def _segment_edge_gap(a,b,c,d):
    """Shortest finite segment-to-edge distance, including actual crossings."""
    dx,dy=b[0]-a[0],b[1]-a[1]
    ex,ey=d[0]-c[0],d[1]-c[1]
    den=dx*ey-dy*ex
    if abs(den)>1e-12:
        cx,cy=c[0]-a[0],c[1]-a[1]
        u=(cx*ey-cy*ex)/den
        v=(cx*dy-cy*dx)/den
        if 0<=u<=1 and 0<=v<=1:return 0.
    return min(_segment_point_gap(a,c,d),_segment_point_gap(b,c,d),
               _segment_point_gap(c,a,b),_segment_point_gap(d,a,b))


@lru_cache(maxsize=256)
def _contour_tip_window(points, holes, wall, cutter_radius=.5):
    """Build an actual rim-following motor-tip window for *all* tip styles.

    Trace from the motor centre, not from the foremost motor screw. Tracing
    from the screw made a wedge that could collapse to one straight side when
    the mounting pattern, cap reach, or left/right mirroring changed.

    The outside boundary is an inset of the real (possibly asymmetric) tip
    silhouette. The return boundary curves around the screw/shaft keep-outs.
    End caps curve *into* the available window, with full segment clearance
    and self-intersection checks. This stays independent of FreeCAD and Qt.
    """
    from .plate_profiles import polygon_interior_distance

    safety = .22  # Extra reserve for sampled-curve / CNC discretisation.
    inset_distance = wall + safety
    inner_radius = holes[-1][2] + wall + 2.0  # motor centre bore land
    inset_outline = tuple(_inset_polygon(points, inset_distance))
    # Never propose a slot narrower than the actual CNC cutter diameter.
    # Narrower stretches are removed from the cutout automatically.
    minimum_window_width = max(2.7, 2.0*cutter_radius + .20)
    sample_count = 121
    runs, run = [], []
    for index in range(sample_count + 1):
        if index == sample_count:
            if run:
                runs.append(run)
            break
        angle = -math.pi/2 + math.pi*index/(sample_count-1)
        ux, uy = math.cos(angle), math.sin(angle)
        inner = inner_radius
        # Exact outer intersections of *expanded* screw keepout discs with
        # each ray. These avoid sharp chords/flat cuts through bolt lands.
        for hx, hy, radius in holes:
            along = hx*ux + hy*uy
            perpendicular = hx*uy - hy*ux
            protected = radius + inset_distance + .16
            determinant = protected**2 - perpendicular**2
            if determinant >= 0:
                inner = max(inner, along + math.sqrt(determinant))
        inner += .07
        def coord(distance):
            return (distance*ux, distance*uy)

        # The initial inward offset is cheap and, on convex fairings,
        # accurate. It avoids hundreds of 16-step distance bisections when
        # moving an editor slider. Guard unusual concave/forked contours by
        # falling back to a true-distance search only where needed.
        outer = _ray_to_tip_boundary((0., 0.), (ux,uy), inset_outline)
        if outer is not None and outer > inner + minimum_window_width:
            if polygon_interior_distance(coord(outer), points) < wall + .10:
                outer = None
        if outer is None:
            boundary = _ray_to_tip_boundary((0.,0.), (ux,uy), points)
            if boundary is None or boundary-inner < minimum_window_width + .30 or polygon_interior_distance(coord(inner), points) < inset_distance:
                if run:
                    runs.append(run)
                    run=[]
                continue
            low, high = inner, boundary
            for _ in range(14):
                mid = (low+high)/2
                if polygon_interior_distance(coord(mid), points) >= inset_distance:
                    low=mid
                else:
                    high=mid
            outer=low-.045
        if outer-inner < minimum_window_width or polygon_interior_distance(coord(inner), points) < inset_distance:
            if run:
                runs.append(run)
                run=[]
            continue
        run.append((coord(outer), coord(inner), angle))

    def cap(a,b,theta,toward_middle):
        """Rounded end with tangent returning toward the inside of the slot."""
        mid_radius = (math.hypot(*a) + math.hypot(*b))*.5
        bend = theta + toward_middle*.10
        control = (mid_radius*math.cos(bend),mid_radius*math.sin(bend))
        return [((1-t)**2*a[0]+2*(1-t)*t*control[0]+t*t*b[0],
                 (1-t)**2*a[1]+2*(1-t)*t*control[1]+t*t*b[1])
                for t in (.2,.4,.6,.8)]

    def safe(vertices):
        if len(vertices)<6:return False
        for a,b in zip(vertices, vertices[1:]+vertices[:1]):
            for c,d in zip(points,points[1:]+points[:1]):
                if _segment_edge_gap(a,b,c,d) < wall-.09:return False
            for hx,hy,radius in holes:
                if _segment_point_gap((hx,hy),a,b) < radius+wall-.07:return False
        size=len(vertices)
        # Catch folded offset curves and cap self-intersections, not only
        # crossings with the outer perimeter.
        for i in range(size):
            a,b=vertices[i],vertices[(i+1)%size]
            for j in range(i+2,size):
                if i==0 and j==size-1:continue
                if _segment_edge_gap(a,b,vertices[j],vertices[(j+1)%size])<1e-6:return False
        area=abs(sum(a[0]*b[1]-b[0]*a[1]
                     for a,b in zip(vertices,vertices[1:]+vertices[:1])))/2
        return area>=5.

    candidates=[]
    for run in runs:
        if len(run)<6:continue
        for trim in range(min(7,len(run)//4)):
            part=run[trim:len(run)-trim] if trim else run
            if len(part)<6:break
            outer_chain=_simplify_tip_chain([outer for outer,_,_ in part],.055)
            inner_chain=_simplify_tip_chain([inner for _,inner,_ in reversed(part)],.045)
            end_cap=cap(part[-1][0],part[-1][1],part[-1][2],-1)
            start_cap=cap(part[0][1],part[0][0],part[0][2],+1)
            shape=outer_chain+end_cap+inner_chain+start_cap
            if safe(shape):
                area=abs(sum(a[0]*b[1]-b[0]*a[1]
                             for a,b in zip(shape,shape[1:]+shape[:1])))/2
                candidates.append((area,tuple(shape)))
                break
    if not candidates:
        raise ValueError('No contour-following arm-tip window can retain the selected edge wall and motor screw clearances. Increase tip width/reach or reduce the cutout wall.')
    return max(candidates,key=lambda item:item[0])[1]

def _reference_tip_cutout(p, polygon, end, half, reach):
    """A shaped motor-tip window: outer rim AND motor-hole keep-outs."""
    wall = max(p.MinimumWeb, p.ArmTipBumperCutoutWall)
    try:
        outline = _contour_tip_window(tuple(polygon), _tip_protected_holes(p),
                                      wall, p.CNCToolRadius)
    except ValueError:
        # This cutout is optional. Preserve a machinable solid tip if the
        # cutter cannot fit between the edge and motor-hole safety envelopes.
        return None
    return dict(kind='polygon', points=outline, operation='cut',tip_window=True)


def motor_pad_primitives(p,arm=None):
    # Apply asymmetry at the source. This common path feeds CAD solids, the
    # editing preview, CNC outlines, and TPU protector generation. Importantly
    # the arm-tip guard is generated *after* orientation so a user-selected
    # front/rear guard direction remains in global coordinates.
    base=_base_motor_pad_primitives(p)
    if p.ArmTipBumperStyle=='Disabled':return base
    # Attachment always remains at the outward end of the pad, local +X.
    end=max(d['centre'][0]+d['radius'] if d['kind']=='circle' else d['width']/2 if d['kind']=='rounded' else max(x for x,y in d['points']) for d in base if d.get('operation')!='cut')
    half=min(p.ArmTipBumperWidth,p.MotorPadDiameter*.85)/2
    start=min(p.MotorPadDiameter*.25,end-p.MinimumWeb)
    reach=p.ArmTipBumperReach;style=arm_tip_style(p.ArmTipBumperStyle)
    shoulder=end-max(1.,p.MinimumWeb*.5)
    if style in REFERENCE_ARM_TIP_STYLES:
        pts=list(_reference_arm_tip_points(p,style,start,end,half,reach))
        if style in ASYMMETRIC_ARM_TIP_STYLES and _arm_tip_direction_sign(p,arm)<0:
            pts=[(x,-y) for x,y in reversed(pts)]
    elif style in ('Round cap','Oval cap'):
        nose=min(reach+half*.65,end+reach-start-.1) if style=='Oval cap' else min(half,end+reach-start-.1)
        cap_half=half*.72 if style=='Oval cap' else half
        pts=[(start,-cap_half),(end+reach-nose,-cap_half)]
        pts += [(end+reach-nose+nose*math.cos(a),cap_half*math.sin(a)) for a in [-math.pi/2+i*math.pi/24 for i in range(25)]]
        pts += [(start,cap_half)]
    elif style=='Tapered cap':
        pts=[(start,-half),(end,-half),(end+reach,-half*.5),(end+reach,half*.5),(end,half),(start,half)]
    elif style=='Shallow arch':
        pts=[(start,-half)]+[(end+reach*(1-.25*(t/half)**2),t) for t in [-half+i*half/16 for i in range(33)]]+[(start,half)]
    elif style=='Soft square':
        radius=min(half*.35,reach*.5)
        pts=[(start,-half),(end+reach-radius,-half)]
        pts += [(end+reach-radius+radius*math.cos(a),-half+radius+radius*math.sin(a)) for a in [-math.pi/2+i*math.pi/16 for i in range(9)]]
        pts += [(end+reach,half-radius)]
        pts += [(end+reach-radius+radius*math.cos(a),half-radius+radius*math.sin(a)) for a in [i*math.pi/16 for i in range(9)]]
        pts += [(start,half)]
    else:
        c=min(half*.4,reach*.4)
        pts=[(start,-half),(end+reach-c,-half),(end+reach,-half+c),(end+reach,half-c),(end+reach-c,half),(start,half)]
    pts=[v for i,v in enumerate(pts) if i==0 or math.dist(v,pts[i-1])>1e-8]
    dx,dy=1.,0.
    if arm is not None and p.ArmTipBumperDirection!='Pad direction':
        ux,uy=motor_pad_unit(p,arm)
        gx,gy=((0.,math.copysign(1.,arm['motor'][1])) if p.ArmTipBumperDirection=='Front / rear' else (math.copysign(1.,arm['motor'][0]),0.))
        dx,dy=gx*ux+gy*uy,-gx*uy+gy*ux
    def stretch(poly):
        out=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            # Only directional bending requires intermediate points. The
            # original code inserted a vertex every 1 mm even on straight
            # edges when no deformation was being applied, then made the Qt
            # Boolean/fillet pipelines process them on all four arms.
            # These points are geometrically redundant in Pad direction.
            steps=max(1,math.ceil(abs(b[0]-a[0])/1.))
            for i in range(steps):
                t=i/steps;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
                amount=max(0.,min(1.,(x-shoulder)/(end+reach-shoulder)))
                amount=amount*amount*(3-2*amount)
                extra=0. if p.ArmTipBumperDirection=='Pad direction' else reach*amount
                out.append((x+dx*extra,y+dy*extra))
        return tuple(out)
    # A new-style tip needs interpolation only when the user asks for a
    # directionally warped tip. Without it the eight or nine original corners
    # describe the *exact* outline (no useless vertices on straight lines).
    if style in REFERENCE_ARM_TIP_STYLES and p.ArmTipBumperDirection=='Pad direction':
        transformed=tuple(pts)
    else:
        transformed=stretch(pts)
    if style in REFERENCE_ARM_TIP_STYLES:
        # Retain all actual corners, including the Volador R0.5 concave arc,
        # but remove redundant collinear samples on the interpolated edges.
        # Qt unions/offsets are sensitive to these extra vertices, and the
        # combined finished-arm outline is rebuilt many times by the editor.
        points=list(transformed)
        for _ in range(2):
            if len(points)<4:break
            minimal=[]
            for i,b in enumerate(points):
                a=points[i-1];c=points[(i+1)%len(points)]
                vx=c[0]-a[0];vy=c[1]-a[1]
                squared=vx*vx+vy*vy
                # A zero-length or reversing edge must never be discarded.
                if squared>1e-16:
                    cross=abs(vx*(b[1]-a[1])-vy*(b[0]-a[0]))
                    projection=(b[0]-a[0])*vx+(b[1]-a[1])*vy
                    if cross*cross<=1e-14*squared and 0<projection<squared:
                        continue
                minimal.append(b)
            if len(minimal)==len(points):break
            points=minimal
        transformed=tuple(points)
    base=tuple(dict(d,scope='pad') if d.get('operation')=='cut' else d for d in base)
    if style in REFERENCE_ARM_TIP_STYLES:
        # Do not convex-hull the NEW shapes: doing so erases the swept hook,
        # dagger asymmetry and the Volador's open V. The bumper polygon starts
        # well INSIDE the real motor bearing area and fuses with it.
        result=base+(dict(kind='polygon',points=transformed,bumper=True),)
        if p.ArmTipBumperCutout:
            cutout=_reference_tip_cutout(p,transformed,end,half,reach)
            if cutout is not None:result+=(cutout,)
        return result
    # Reshape the pad's outward shoulder into a tangent outer envelope with
    # the cap. Fill the junction instead of leaving a narrow neck, re-entrant
    # steps or a stretched S-shaped seam. Rear pad/arm attachment is retained.
    samples=[]
    for primitive in base:
        if primitive.get('operation')=='cut':continue
        if primitive['kind']=='circle':
            cx,cy=primitive['centre'];radius=primitive['radius']
            pts0=[(cx+radius*math.cos(i*math.pi/48),cy+radius*math.sin(i*math.pi/48)) for i in range(96)]
        elif primitive['kind']=='rounded':
            radius=primitive['radius'];h=primitive['width']/2-radius
            pts0=[(sx*h+radius*math.cos(i*math.pi/48),sy*h+radius*math.sin(i*math.pi/48)) for sx in (-1,1) for sy in (-1,1) for i in range(96)]
        else:pts0=list(primitive['points'])
        samples.extend(pts0)
    pad_front=_clip_front(list(convex_hull(samples)),0.)
    fairing=convex_hull(pad_front+list(transformed))
    result=base+(dict(kind='polygon',points=transformed,bumper=True),dict(kind='polygon',points=fairing,bumper=True))
    if p.ArmTipBumperCutout:
        wall=max(p.MinimumWeb,p.ArmTipBumperCutoutWall)
        try:
            outline=_contour_tip_window(tuple(fairing),_tip_protected_holes(p),
                                        wall,p.CNCToolRadius)
        except ValueError:
            outline=None
        if outline is not None:
            result+=(dict(kind='polygon', points=outline, operation='cut',tip_window=True),)
    return result
