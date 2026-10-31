"""Motor-bearing outlines, neck reliefs and mirrored orientation without CAD imports."""
import math
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
               for d in motor_pad_primitives(p) if d.get('operation')!='cut')


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


def motor_pad_primitives(p):
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
        for d in motor_pad_primitives(p):
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
        return polygon_interior_distance(point,motor_pad_primitives(p)[0]['points'])
    return max(d['radius']-math.dist(point,d['centre']) for d in motor_pad_primitives(p))


def motor_pad_bound(p):
    if p.MotorPadShape in REALISTIC_MOTOR_PAD_SHAPES+NEW_MOTOR_PAD_SHAPES:
        return max(math.hypot(*d['centre'])+d['radius'] if d['kind']=='circle' else max(math.hypot(x,y) for x,y in d['points'])
                   for d in motor_pad_primitives(p) if d.get('operation')!='cut')
    if extended_motor_pad(p):
        return max(math.hypot(x,y) for x,y in motor_pad_primitives(p)[0]['points'])
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
