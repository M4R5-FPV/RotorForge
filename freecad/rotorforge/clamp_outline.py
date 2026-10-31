"""Arm-matched clamp ends, with a continuous stack deck and local post pads."""
from .parameter_memo import parameter_cache

@parameter_cache()
def clamp_outline_layout(p):
    from .parameters import arm_brace_layouts,arm_layouts,standoff_pairs,underside_clamp_active
    from .arm_roots import root_width
    from .plate_profiles import profiled_interior_distance
    c=arm_brace_layouts(p)[0];arms=arm_layouts(p)
    margin=max(p.StackHoleDiameter,p.StackAccessDiameter if underside_clamp_active(p) else 0)/2+p.MinimumWeb
    front=max(p.StackOffsetY+p.StackSpacing/2+margin,
              min(pt[1] for a in arms if a['root'][1]>0 for pt in a['bolts'])-root_width(p)/4)
    rear=min(p.StackOffsetY-p.StackSpacing/2-margin,
             max(pt[1] for a in arms if a['root'][1]<0 for pt in a['bolts'])+root_width(p)/4)
    # Existing clamp-mounted standoffs keep a local bearing pad and bridge,
    # instead of stretching the entire front/rear edge into a rectangle.
    radius=max(p.StandoffDiameter/2,p.StackAccessDiameter/2 if underside_clamp_active(p) else 0)+p.MinimumWeb
    pads=[]
    for pair in standoff_pairs(p):
        for sign in (-1,1):
            pt=(sign*pair['width']/2,pair['y'])
            if profiled_interior_distance(pt,p,'ArmClampPlate',c['width'],c['rear'],c['front'],c['radius'])>=0:
                anchor=(pt[0],max(rear+radius,min(front-radius,pt[1])))
                pads.append((pt,anchor,radius))
    return max(c['rear'],rear),min(c['front'],front),tuple(pads)

def clamp_interior_distance(point,p):
    from .parameters import arm_brace_layouts,arm_layouts,mid_tab_interior_distance,point_segment_distance
    from .plate_profiles import profiled_interior_distance
    c=arm_brace_layouts(p)[0];rear,front,pads=clamp_outline_layout(p);arms=arm_layouts(p)
    main=profiled_interior_distance(point,p,'ArmClampPlate',c['width'],rear,front,c['radius'])
    tabs=[mid_tab_interior_distance(point,p,a,arms) for a in arms]
    stock=max([main]+tabs+[r-point_segment_distance(point,a,b) for a,b,r in pads])
    boundary=profiled_interior_distance(point,p,'ArmClampPlate',c['width'],c['rear'],c['front'],c['radius'])
    return min(stock,boundary)
