"""Top-plate edge strap reliefs shared by CAD, preview and validation."""
import math
from .parameter_memo import parameter_cache

@parameter_cache()
def notch_polygons(p):
    if not p.StrapSlotsEnabled or p.StrapOpeningStyle!='Outline cutouts':return ()
    from .parameters import top_interior_distance,strap_positions
    half=p.StrapSlotLength/2;depth=p.StrapNotchDepth
    if half<=0 or depth<=0 or not math.isfinite(half+depth):return ()
    extent=max(p.TopWidth,p.TopCentreWidth)/2+2
    result=[]
    for y in strap_positions(p):
        # Locate the actual side edge, including widened centres and tapers.
        lo,hi=0.,extent
        for _ in range(45):
            x=(lo+hi)/2
            if top_interior_distance((x,y),p)>=0:lo=x
            else:hi=x
        inner=lo-depth;r=min(1.5,depth/2,half/2)
        pts=[(extent,y-half)]
        for cx,cy,start in ((inner+r,y-half+r,270),(inner+r,y+half-r,180)):
            pts.extend((cx+r*math.cos(math.radians(start-i*90/8)),cy+r*math.sin(math.radians(start-i*90/8))) for i in range(9))
        pts.append((extent,y+half))
        result.extend(tuple((side*x,yy) for x,yy in pts) for side in (-1,1))
    return tuple(result)

def validate_notches(p):
    if not p.StrapSlotsEnabled or p.StrapOpeningStyle!='Outline cutouts':return []
    from .parameters import top_interior_distance,strap_positions,standoff_holes,segment_distance,camera_slots
    from .plate_profiles import polygon_interior_distance
    if not math.isfinite(p.StrapNotchDepth) or p.StrapNotchDepth<=0:return ['Outline cutout depth must be positive and finite.']
    if p.StrapCount=="2 straps" and p.StrapOffsetY*2 < p.StrapSlotLength+p.MinimumWeb:return ['Strap outline cutouts overlap; increase fore/aft spacing or reduce strap length.']
    errors=[]
    for poly in notch_polygons(p):
        inner=min(abs(x) for x,y in poly)
        if p.StrapNotchDepth>=max(p.TopWidth,p.TopCentreWidth)/2-p.MinimumWeb/2 or inner*2<p.MinimumWeb:errors.append('Strap outline cutouts leave too little material across the top plate.')
        # The whole inward edge must remain inside the plate. This also prevents
        # a notch running off a nose/rear recess or missing a tapered side.
        inside_edge=poly[1:-1]
        if any(top_interior_distance(pt,p)<.05 for pt in inside_edge):errors.append('Strap outline cutout reaches a plate end or misses the side edge; move the straps inward.')
        for pt in standoff_holes(p):
            if polygon_interior_distance(pt,poly)>-p.StandoffDiameter/2-p.MinimumWeb:
                errors.append('A strap outline cutout is too close to a standoff mounting footprint.')
        for a,b,r in camera_slots(p,'TopPlate'):
            if polygon_interior_distance(a,poly)>=0 or polygon_interior_distance(b,poly)>=0 or any(segment_distance(a,b,c,d)<r+p.MinimumWeb for c,d in zip(poly,poly[1:]+poly[:1])):
                errors.append('A strap outline cutout is too close to a camera tab slot.')
    return list(dict.fromkeys(errors))
