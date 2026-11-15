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


# Only a small clearance outside a hardware *bearing face* is needed to
# support that face. MinimumWeb is still kept around the actual through-hole
# (or broaching envelope). Applying it once more outside a solid standoff or
# an unrecessed press-nut flange made unnecessary perimeter lobes.
BEARING_EDGE_LIP_MM = 0.35


def standoff_stock_radius(p):
    """Hole strength OR full standoff foot bearing, whichever needs more stock.

    The outer diameter is not an additional drilled hole: do not add the full
    MinimumWeb to both the screw clearance and the external standoff diameter.
    """
    return max(p.StandoffHoleDiameter/2+p.MinimumWeb,
               p.StandoffDiameter/2+min(BEARING_EDGE_LIP_MM,p.MinimumWeb))


def press_nut_stock_radius(p, recess_depth):
    """Support the insertion bore and flange without double-counting the web.

    A recessed flange *does* remove carbon and must retain MinimumWeb outside
    the pocket. A proud flange merely bears on the existing plate surface.
    """
    core=max(p.PressNutBore,p.PressNutShankDiameter)/2+p.MinimumWeb
    flange=(p.PressNutFlangeDiameter +
            (p.NutRecessClearance if recess_depth else 0.))/2
    return max(core, flange+(p.MinimumWeb if recess_depth else
                             min(BEARING_EDGE_LIP_MM,p.MinimumWeb)))


def arm_bolt_stock_radius(p, standoff_bearing=False, allowance=None):
    """Arm-only reinforcement; optional fixed stock for receiving-plate trims."""
    bolt_radius=(p.RootHoleDiameter/2+p.MinimumWeb+.05+
                 (p.ArmBoltMaterialAllowance if allowance is None else allowance))
    return max(bolt_radius,standoff_stock_radius(p) if standoff_bearing else 0.)


def receiving_arm_bolt_radius(p, hole_radius, nut_seat_radius=0., standoff_bearing=False):
    """Fixed receiving-plate hole/seat stock, independent of arm allowance.

    The receiving plate follows its real arm-overlap tabs. Its nut pads must
    NOT expand just because the user enlarges the material on an arm. The
    previous function incorrectly added ArmBoltMaterialAllowance here, which
    caused mid-plate press-nut pads to chase the arm and never line up.
    """
    bolt_radius=hole_radius+p.MinimumWeb
    return max(bolt_radius,nut_seat_radius,
               standoff_stock_radius(p) if standoff_bearing else 0.)


def bearing_surface_for_standoff(stand,role):
    """A standoff's OD bears only on its actual mounting layer (plus top)."""
    return (role=='TopPlate' or
            (role=='Arm' and stand['mount']=='Arm top') or
            (role=='MidPlate' and stand['mount']=='Mid plate') or
            (role=='BottomPlate' and stand['mount']=='Bottom plate') or
            (role=='ArmClampPlate' and stand['mount']=='Arm clamp plate'))


def standoff_at_point(stands,point):
    return next((s for s in stands if math.dist(s['point'],point)<=1e-6),None)


@parameter_cache(maxsize=256)
def _arm_supports(p,arm_items,allowance=None):
    arm=dict(arm_items)
    from .arm_roots import base_stem_interior_distance
    # Do NOT call standoff_layouts() here: the standoff layout queries the
    # mid-plate base outline, whose tabs query stem_interior_distance(), which
    # must in turn call arm_supports().  That creates an infinite recursion
    # on 6/8-standoff frames (and on other layouts with extra custom pairs).
    # All the information needed here is available from the raw pairs and
    # plate configuration, without querying geometry or computed post mounts.
    from .parameters import (standoff_holes, three_plate,
                             upper_clamp_active, arms_above_bottom)
    a,b=arm['start'],arm.get('beam_end',arm['motor'])
    dx,dy=b[0]-a[0],b[1]-a[1];d2=dx*dx+dy*dy
    posts=standoff_holes(p)
    # A post seated on the arm is possible only in a two-plate frame with
    # the arms above the bottom and no combined upper arm clamp.
    arm_top_bearing=(not three_plate(p) and arms_above_bottom(p)
                     and not upper_clamp_active(p))
    result=[]
    for pt in arm['bolts']:
        shared=any(math.dist(pt,post)<=1e-6 for post in posts)
        r=arm_bolt_stock_radius(p,shared and arm_top_bearing,allowance)
        if base_stem_interior_distance(p,arm,pt)>=r-.05-1e-7:continue
        t=max(0.,min(1.,((pt[0]-a[0])*dx+(pt[1]-a[1])*dy)/max(d2,1e-12)))
        anchor=(a[0]+t*dx,a[1]+t*dy)
        result.append((pt,anchor,r))
    return tuple(result)


def arm_supports(p,arm,allowance=None):
    return _arm_supports(p,tuple(sorted(arm.items())),allowance)


@parameter_cache(maxsize=512)
def base_plate_distance(p,role,point):
    from . import parameters as m
    fn={'BottomPlate':m._base_bottom_interior_distance,'TopPlate':m._base_top_interior_distance,
        'MidPlate':m._base_mid_interior_distance,'ArmClampPlate':m._base_arm_clamp_interior_distance,
        'ArmLowerClampPlate':m._base_arm_clamp_interior_distance}[role]
    return fn(point,p)


@parameter_cache()
def plate_supports(p,role):
    """One reinforcement envelope per physical fixing and carbon layer.

    plate_holes() deliberately exposes both `arm root` and `standoff` tags
    for shared hardware to layer-specific machining.  Reinforcement must NOT
    treat those two tags as separate fixings or apply a standoff OD bearing to
    a layer where the standoff does not stand.
    """
    from .parameters import (plate_holes,bottom_body_bounds,top_bounds,mid_bounds,
                             arm_brace_layouts,standoff_layouts)
    if role=='TopPlate':width=p.TopWidth;rear,front=top_bounds(p)
    elif role=='BottomPlate':width=p.BodyWidth;rear,front=bottom_body_bounds(p)
    elif role=='MidPlate':width=p.BodyWidth;rear,front=mid_bounds(p)
    else:
        c=arm_brace_layouts(p)[0];width=c['width'];rear,front=c['rear'],c['front']
    from .nut_seats import seats
    from .hardware_layout import SIZES,metric_size
    seat_radii={}
    for seat in seats(p,role):
        if seat['mode']=='Recessed hex nut':
            radius=(SIZES[metric_size(seat['bore'])][4]+p.NutRecessClearance)/math.sqrt(3)+p.MinimumWeb+.05
        else:
            radius=press_nut_stock_radius(p,seat['depth'])
        seat_radii[seat['point']]=radius

    stands=standoff_layouts(p)
    # Combine coincident physical fixing centres; don't construct two circles
    # and two bridges for a single shared arm-bolt/standoff screw.
    centres=[]
    for pt,hole,kind in plate_holes(p,role):
        if kind not in ('arm root','standoff','standoff access') and pt not in seat_radii:
            continue
        group=next((entry for entry in centres if math.dist(entry[0],pt)<=1e-6),None)
        if group is None:
            group=(pt,[]);centres.append(group)
        group[1].append((hole,kind))

    supports=[];anchors=None
    for pt,holes in centres:
        stand=standoff_at_point(stands,pt)
        standoff_foot=stand is not None and bearing_surface_for_standoff(stand,role)
        # A coincident bolt and standoff share the same screw axis; the
        # receiving plate has a FIXED requirement. The adjustable arm-only
        # allowance must not feed through to the nut seat or standoff foot.
        radius=max((hole+p.MinimumWeb for hole,kind in holes),default=0.)
        if any(kind=='arm root' for _,kind in holes):
            root_radius=max(hole for hole,kind in holes if kind=='arm root')
            radius=max(radius,receiving_arm_bolt_radius(
                p,root_radius,seat_radii.get(pt,0.),standoff_foot))
        if standoff_foot:
            radius=max(radius,standoff_stock_radius(p))
        radius=max(radius,seat_radii.get(pt,0.))
        # Keep legacy fast preselection for mounts safely inside the base
        # outline.  When the mount is near the edge, actual CAD/Qt boolean
        # overlap, not this analytic distance, decides whether stock is added.
        if base_plate_distance(p,role,pt)>=radius-1e-7:
            continue
        if anchors is None:
            anchors=tuple((x,y) for i in range(17) for j in range(25)
                          for x,y in ((width*(i/16-.5),rear+(front-rear)*j/24),)
                          if base_plate_distance(p,role,(x,y))>=p.MinimumWeb)
        if not anchors:
            raise ValueError(role+': no solid deck remains to anchor mounting extensions.')
        anchor=min(anchors,key=lambda q:math.dist(q,pt))
        if pt[0]<0:
            mirrored=min(anchors,key=lambda q:math.dist(q,(-pt[0],pt[1])))
            anchor=(-mirrored[0],mirrored[1])
        supports.append((pt,anchor,radius))
    return tuple(supports)


def plate_distance(point,p,role):
    return max(base_plate_distance(p,role,point),support_distance(point,plate_supports(p,role)))


def attachment_needs_bridge(overlap_area, minimum_web):
    """Only use an anchor capsule when the round bearing barely contacts deck.

    Otherwise extending the entire bolt-to-anchor capsule introduces bumps
    even though the round bolt bearing is sufficiently attached already.
    This predicate is shared by the CAD and 2D preview implementations.
    """
    return overlap_area < max(.1, .5*minimum_web*minimum_web)
