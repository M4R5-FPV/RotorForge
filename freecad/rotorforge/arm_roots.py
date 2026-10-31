"""Shared arm-root joint planes and compact key outlines, without CAD imports."""
import math

ARM_ROOT_FITS = ('Independent', 'Fitted miters')
ROOT_BOLT_LAYOUTS = ('Along arm', 'Custom coordinates')
ROOT_PROFILE_FIELDS = {'ArmRootWidth', 'ArmRootLength', 'ArmRootTaperLength', 'RootBoltLayout',
                       'RootBolt1Y', 'RootBolt1X', 'RootBolt2Y', 'RootBolt2X'}
ROOT_BOLT_COORDINATES = {'RootBolt1Y', 'RootBolt1X', 'RootBolt2Y', 'RootBolt2X'}
LEGACY_ROOT_BOLT_COORDINATES = {'RootBolt1Along', 'RootBolt1Across', 'RootBolt2Along', 'RootBolt2Across'}


def root_width(p):
    return p.ArmRootWidth or p.ArmWidth


def widened_roots(p):
    return root_width(p) > p.ArmWidth + 1e-8


def stem_stations(p, arm):
    """Tail centre, wide shoulder, taper end, motor centre, root/beam radii."""
    return (-p.RootExtension, p.ArmRootLength, p.ArmRootLength+p.ArmRootTaperLength,
            math.dist(arm['root'], arm.get('beam_end',arm['motor'])), root_width(p)/2, p.ArmWidth/2)


def arm_local_point(arm, along, across):
    ux, uy = arm['unit']
    return (arm['root'][0]+along*ux-across*uy, arm['root'][1]+along*uy+across*ux)


def _straight_stem_interior_distance(p, arm, point):
    """Signed distance to the uncut stem, including the tapered root shoulder."""
    ux, uy = arm['unit']
    dx, dy = point[0]-arm['root'][0], point[1]-arm['root'][1]
    t, s = dx*ux+dy*uy, -dx*uy+dy*ux
    start, reach, end, motor, rr, rb = stem_stations(p, arm)
    if not widened_roots(p):
        return rb-math.hypot(t-max(start, min(motor, t)), s)
    if t < start:
        inside = math.hypot(t-start, s) <= rr
    elif t <= reach:
        inside = abs(s) <= rr
    elif t < end:
        inside = abs(s) <= rr+(rb-rr)*(t-reach)/(end-reach)
    elif t <= motor:
        inside = abs(s) <= rb
    else:
        inside = math.hypot(t-motor, s) <= rb
    points = ((start, rr), (reach, rr), (end, rb), (motor, rb),
              (motor, -rb), (end, -rb), (reach, -rr), (start, -rr))
    distances = []
    for i in (0, 1, 2, 4, 5, 6):
        a, b = points[i], points[i+1]
        vx, vy = b[0]-a[0], b[1]-a[1]
        q = max(0., min(1., ((t-a[0])*vx+(s-a[1])*vy)/max(1e-20, vx*vx+vy*vy)))
        distances.append(math.hypot(t-a[0]-q*vx, s-a[1]-q*vy))
    distances.append(abs(math.hypot(t-start, s)-rr) if t <= start else
                     min(math.hypot(t-start, s-rr), math.hypot(t-start, s+rr)))
    distances.append(abs(math.hypot(t-motor, s)-rb) if t >= motor else
                     min(math.hypot(t-motor, s-rb), math.hypot(t-motor, s+rb)))
    return min(distances)*(1 if inside else -1)


def stem_interior_distance(p,arm,point):
    distance=_straight_stem_interior_distance(p,arm,point)
    if p.MotorPadRotationPivot=='Pad beginning' and 'beam_end' in arm:
        a,b=arm['beam_end'],arm['motor'];dx,dy=b[0]-a[0],b[1]-a[1]
        t=max(0.,min(1.,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/max(1e-20,dx*dx+dy*dy)))
        distance=max(distance,p.ArmWidth/2-math.dist(point,(a[0]+t*dx,a[1]+t*dy)))
    from .plate_profiles import polygon_interior_distance
    return max(distance,polygon_interior_distance(point,beam_profile_polygon(p,arm)))


def fitted_roots(p):
    return p.ArmRootFit == ARM_ROOT_FITS[1]


def root_joint_planes(p, arm, arms):
    """Unit-normal half-planes n.point <= limit for this arm's root cell.

    Equal-distance planes divide overlapping roots symmetrically. Offsetting
    each side by half the requested gap leaves the full gap across each joint.
    """
    if not fitted_roots(p):
        return ()
    ax, ay = arm['root']
    result = []
    for other in arms:
        if other['name'] == arm['name']:
            continue
        bx, by = other['root']
        distance = math.hypot(bx-ax, by-ay)
        if distance < 1e-9:
            raise ValueError('Fitted arm roots need distinct root reference centres.')
        normal = ((bx-ax)/distance, (by-ay)/distance)
        limit = (bx*bx+by*by-ax*ax-ay*ay)/(2*distance)-p.ArmJointClearance/2
        result.append((normal, limit))
    return tuple(result)


def root_cell_polygon(p, arm, arms):
    extent = max(abs(v) for a in arms for point in (a['start'], a['motor']) for v in point)
    extent += p.MotorPadDiameter+root_width(p)+max(0, p.MotorTipLength)+1
    points = ((-extent, -extent), (extent, -extent), (extent, extent), (-extent, extent))
    for (nx, ny), limit in root_joint_planes(p, arm, arms):
        clipped = []
        for a, b in zip(points, points[1:]+points[:1]):
            da, db = limit-nx*a[0]-ny*a[1], limit-nx*b[0]-ny*b[1]
            if da >= -1e-10:
                clipped.append(a)
            if (da < -1e-10) != (db < -1e-10):
                t = da/(da-db)
                clipped.append((a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1])))
        unique = []
        for point in clipped:
            if not unique or math.dist(unique[-1], point) > 1e-9:
                unique.append(point)
        if len(unique) > 1 and math.dist(unique[0], unique[-1]) < 1e-9:
            unique.pop()
        points = tuple(unique)
        if len(points) < 3:
            raise ValueError('Joint clearance removes an arm root; reduce the gap or reposition the roots.')
    return points


def compact_key_centre(arms):
    """Junction of the four symmetric root cells, including unequal widths."""
    front = next((a['root'] for a in arms if a['root'][0] > 0 and a['root'][1] > 0), None)
    rear = next((a['root'] for a in arms if a['root'][0] > 0 and a['root'][1] < 0), None)
    if front is None or rear is None:
        raise ValueError('The root junction needs distinct front/rear and left/right root centres.')
    return (0., (front[0]**2+front[1]**2-rear[0]**2-rear[1]**2)/(2*(front[1]-rear[1])))


def compact_key_outline(p, arms, pocket=False):
    x, y = compact_key_centre(arms)
    a, b = p.KeystoneWidth/2, p.KeystoneLength/2
    if a <= 0 or b <= 0:
        raise ValueError('Compact keystone width and length must be positive.')
    kind=p.KeystoneShape
    if kind=='Diamond':pts=((a,0),(0,b),(-a,0),(0,-b))
    elif kind=='Chamfered diamond':pts=((a*.8,b*.2),(a*.2,b*.8),(-a*.2,b*.8),(-a*.8,b*.2),(-a*.8,-b*.2),(-a*.2,-b*.8),(a*.2,-b*.8),(a*.8,-b*.2))
    elif kind=='Hexagon':pts=((a,0),(a*.5,b),(-a*.5,b),(-a,0),(-a*.5,-b),(a*.5,-b))
    else:pts=((a,b*.5),(a*.5,b),(-a*.5,b),(-a,b*.5),(-a,-b*.5),(-a*.5,-b),(a*.5,-b),(a,-b*.5))
    if kind=='Chamfered diamond':pts=tuple((u/.8,v/.8) for u,v in pts)
    if pocket and p.KeystoneClearance:
        lines=[]
        for u,v in zip(pts,pts[1:]+pts[:1]):
            dx,dy=v[0]-u[0],v[1]-u[1];length=math.hypot(dx,dy)
            nx,ny=dy/length,-dx/length
            lines.append((nx,ny,nx*u[0]+ny*u[1]+p.KeystoneClearance))
        out=[]
        for prev,cur in zip(lines[-1:]+lines[:-1],lines):
            nx,ny,c=prev;mx,my,d=cur;det=nx*my-ny*mx
            out.append(((c*my-ny*d)/det,(nx*d-c*mx)/det))
        pts=tuple(out)
    return tuple((x+u,y+v) for u,v in pts)



def nearest_polygon_point(point, points):
    candidates = []
    for a, b in zip(points, points[1:]+points[:1]):
        dx, dy = b[0]-a[0], b[1]-a[1]
        t = max(0., min(1., ((point[0]-a[0])*dx+(point[1]-a[1])*dy)/(dx*dx+dy*dy)))
        candidates.append((a[0]+t*dx, a[1]+t*dy))
    return min(candidates, key=lambda q: math.dist(point, q))



def beam_free_span(p,arm):
    _,reach,end,motor,rr,rb=stem_stations(p,arm)
    ux,uy=arm['unit'];rx,ry=arm['root']
    bolt_end=max(((x-rx)*ux+(y-ry)*uy for x,y in arm['bolts']),default=0)
    start=max(end if widened_roots(p) else reach,bolt_end+p.RootHoleDiameter/2+p.MinimumWeb+2)
    stop=motor-max(p.MotorPadDiameter/2,p.ArmWidth)-2
    return start,stop,rb


def beam_profile_polygon(p,arm):
    """Distinct straight-axis tapers, broad shoulders and solid beam profiles."""
    if p.ArmBeamShape=='Straight':return ()
    start,stop,rb=beam_free_span(p,arm)
    if stop-start<2:return ()
    name=p.ArmBeamShape
    knots={
      'Root taper':((0,0),(.12,1),(.35,1),(1,0)),
      'Motor flare':((0,0),(.6,0),(.88,1),(1,0)),
      'Hourglass neck':((0,0),(.12,1),(.28,1),(.45,0),(.65,0),(.85,1),(1,0)),
      'Broad shoulder':((0,0),(.12,1),(.72,1),(.85,.4),(1,0)),
      'Stepped beam':((0,0),(.12,1),(.3,1),(.38,.2),(.68,.2),(.76,.7),(.88,.7),(1,0)),
    }.get(name,((0,0),(.12,1),(.88,1),(1,0)))
    pts=tuple((start+(stop-start)*t,rb*(1+p.ArmProfileAmount/100*v)) for t,v in knots)
    return tuple(arm_local_point(arm,t,w) for t,w in pts)+tuple(arm_local_point(arm,t,-w) for t,w in reversed(pts))


def fillet_root_limit(p,arm):
    """Preserve the entire root and all its mounting stock, in arm coordinates."""
    ux,uy=arm['unit'];rx,ry=arm['root']
    return max(p.ArmRootLength,max((x-rx)*ux+(y-ry)*uy for x,y in arm['bolts'])+p.RootHoleDiameter/2+p.MinimumWeb)
