"""Shared frame-coordinate geometry for arm stack-screw escape slots."""
import math


def stack_escape_segment(p, point, bounds):
    """Return a capsule from the screw toward the stack centre and past the arm.

    bounds is (xmin, ymin, xmax, ymax) of the uncut arm. Extending beyond the
    bounding box makes an open slot even with long tails or asymmetric roots.
    Consumers must first check that this screw's round relief crosses the arm.
    """
    centre=(0.,p.StackOffsetY)
    dx,dy=centre[0]-point[0],centre[1]-point[1]
    distance=math.hypot(dx,dy)
    if distance<1e-9:raise ValueError('A stack escape slot needs a screw offset from the stack centre.')
    xmin,ymin,xmax,ymax=bounds
    reach=distance+max(math.hypot(x-centre[0],y-centre[1])
                       for x in (xmin,xmax) for y in (ymin,ymax))+p.StackAccessDiameter/2+1.
    return point,(point[0]+dx/distance*reach,point[1]+dy/distance*reach),p.StackAccessDiameter/2
