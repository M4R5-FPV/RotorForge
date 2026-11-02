"""Local rounded stock for displaced structural fixings, shared by CAD and UI.

Supports derive from the unextended outline on every edit, never from the
previous solid. Standoff layer selection also uses that outline to avoid a
circular dependency or moving a post to another plate as its pad grows.
"""
import math
from .parameter_memo import parameter_cache


def support_distance(point,supports):
    from .parameters import point_segment_distance
    return max((r-point_segment_distance(point,a,b) for a,b,r in supports),default=-float('inf'))


@parameter_cache(maxsize=256)
def _arm_supports(p,arm_items):
    arm=dict(arm_items)
    from .arm_roots import base_stem_interior_distance
    from .parameters import standoff_holes
    a,b=arm['start'],arm.get('beam_end',arm['motor'])
    dx,dy=b[0]-a[0],b[1]-a[1];d2=dx*dx+dy*dy
    posts=standoff_holes(p)
    result=[]
    for pt in arm['bolts']:
        bearing=p.StandoffDiameter/2 if any(math.dist(pt,q)<1e-6 for q in posts) else 0
        r=max(p.RootHoleDiameter/2,bearing)+p.MinimumWeb+.05
        if base_stem_interior_distance(p,arm,pt)>=r-.05-1e-7:continue
        t=max(0.,min(1.,((pt[0]-a[0])*dx+(pt[1]-a[1])*dy)/max(d2,1e-12)))
        anchor=(a[0]+t*dx,a[1]+t*dy)
        result.append((pt,anchor,r))
    return tuple(result)


def arm_supports(p,arm):
    return _arm_supports(p,tuple(sorted(arm.items())))


def base_plate_distance(p,role,point):
    from . import parameters as m
    fn={'BottomPlate':m._base_bottom_interior_distance,'TopPlate':m._base_top_interior_distance,
        'MidPlate':m._base_mid_interior_distance,'ArmClampPlate':m._base_arm_clamp_interior_distance,
        'ArmLowerClampPlate':m._base_arm_clamp_interior_distance}[role]
    return fn(point,p)


@parameter_cache()
def plate_supports(p,role):
    from .parameters import plate_holes,bottom_body_bounds,top_bounds,mid_bounds,arm_brace_layouts
    if role=='TopPlate':width=p.TopWidth;rear,front=top_bounds(p)
    elif role=='BottomPlate':width=p.BodyWidth;rear,front=bottom_body_bounds(p)
    elif role=='MidPlate':width=p.BodyWidth;rear,front=mid_bounds(p)
    else:
        c=arm_brace_layouts(p)[0];width=c['width'];rear,front=c['rear'],c['front']
    from .nut_seats import seats
    from .hardware_layout import SIZES,metric_size
    seat_radii={}
    for seat in seats(p,role):
        if seat["mode"]=="Recessed hex nut":
            seat_radii[seat["point"]]=(SIZES[metric_size(seat["bore"])][4]+p.NutRecessClearance)/math.sqrt(3)+p.MinimumWeb+.05
        else:
            seat_radii[seat["point"]]=max(p.PressNutBore,p.PressNutShankDiameter,p.PressNutFlangeDiameter+(p.NutRecessClearance if seat["depth"] else 0))/2+max(1.,p.MinimumWeb)+.05
    supports=[];anchors=None
    for pt,hole,kind in plate_holes(p,role):
        if kind not in ('arm root','standoff','standoff access') and pt not in seat_radii:continue
        r=max(hole,p.StandoffDiameter/2 if kind=='standoff' else 0)+p.MinimumWeb+.05
        r=max(r,seat_radii.get(pt,0))
        if base_plate_distance(p,role,pt)>=r-.05-1e-7:continue
        # Prefer the closest part of the original deck with a firm attachment.
        # The small grid is consulted only when stock is actually missing.
        if anchors is None:
            anchors=tuple((x,y) for i in range(17) for j in range(25)
                          for x,y in ((width*(i/16-.5),rear+(front-rear)*j/24),)
                          if base_plate_distance(p,role,(x,y))>=p.MinimumWeb)
        if not anchors:raise ValueError(role+': no solid deck remains to anchor mounting extensions.')
        anchor=min(anchors,key=lambda q:math.dist(q,pt))
        # Symmetric target positions must get symmetric bridges even on ties.
        if pt[0]<0:
            mirrored=min(anchors,key=lambda q:math.dist(q,(-pt[0],pt[1])))
            anchor=(-mirrored[0],mirrored[1])
        supports.append((pt,anchor,r))
    return tuple(supports)


def plate_distance(point,p,role):
    return max(base_plate_distance(p,role,point),support_distance(point,plate_supports(p,role)))
