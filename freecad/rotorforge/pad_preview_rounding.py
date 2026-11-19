"""Keep Qt rolling-disc operations fast on dense intermediate pad contours.

Only the temporary eroded outline may be cleaned. The existing carrier,
rounding radius, Qt stroke precision, final intersection, holes and exact
manufacturing solids are all retained. No optional dependencies are used.
"""

# In millimetres; caller works in the established 16x Qt Boolean space.
CORE_TOLERANCE_MM = .005


def _segment_distance_sq(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    d = dx*dx + dy*dy
    t = max(0., min(1., ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/d)) if d else 0.
    return (p[0]-a[0]-t*dx)**2 + (p[1]-a[1]-t*dy)**2


def clean_closed_loop(points, tolerance):
    """Remove only sub-tolerance intermediate vertices; preserve closed loops.

    Split the ring at a well-separated vertex so the two open chains do not
    have a degenerate start/end baseline. Every discarded vertex is within
    the given distance of its replacement segment. Never round coordinates.
    """
    pts=[]
    for point in points:
        if not pts or point!=pts[-1]:pts.append(point)
    if len(pts)>1 and pts[0]==pts[-1]:pts.pop()
    if len(pts)<4:return tuple(points)
    x,y=pts[0]
    split=max(range(1,len(pts)),key=lambda i:(pts[i][0]-x)**2+(pts[i][1]-y)**2)
    pts.append(pts[0]);last=len(pts)-1
    keep={0,split,last};stack=[(0,split),(split,last)];limit=tolerance*tolerance
    while stack:
        start,end=stack.pop()
        if end<=start+1:continue
        best,index=limit,None
        for i in range(start+1,end):
            distance=_segment_distance_sq(pts[i],pts[start],pts[end])
            if distance>best:best,index=distance,i
        if index is not None:
            keep.add(index);stack.extend(((start,index),(index,end)))
    result=tuple(pts[i] for i in sorted(keep))
    return result if len(result)>=4 else tuple(points)


def _area(points):
    return .5*sum(x*v-y*u for (x,y),(u,v) in zip(points,points[1:]+points[:1]))


def cleaned_core(core, polygons, room, QtGui):
    """Return a cleaned single-loop Qt path or the unmodified core.

    Only linear elements from Qt's erosion are eligible. A conservative area
    and bounds check rejects unexpected topology or geometry changes. The
    caller still validates the final hole count and every enclosed hole.
    """
    if core.elementCount()<80 or len(polygons)!=1:return core
    if any(core.elementAt(i).isCurveTo() for i in range(core.elementCount())):return core
    points=tuple((v.x(),v.y()) for v in polygons[0])
    tolerance=min(16*CORE_TOLERANCE_MM,room*.01)
    if tolerance<=0:return core
    clean=clean_closed_loop(points,tolerance)
    if len(clean)>=len(points)*.9:return core
    area=_area(points);new_area=_area(clean)
    if area*new_area<=0:return core
    # A displacement of at most tolerance along the perimeter can only
    # change area by approximately perimeter*tolerance.
    import math
    perimeter=sum(math.hypot(u-x,v-y) for (x,y),(u,v) in zip(points,points[1:]+points[:1]))
    if abs(area-new_area)>perimeter*tolerance:return core
    path=QtGui.QPainterPath();path.moveTo(*clean[0])
    for point in clean[1:]:path.lineTo(*point)
    path.closeSubpath();path.setFillRule(core.fillRule())
    if path.isEmpty():return core
    old,new=core.boundingRect(),path.boundingRect()
    if any(abs(a-b)>tolerance+1e-8 for a,b in zip(
            (old.left(),old.top(),old.right(),old.bottom()),
            (new.left(),new.top(),new.right(),new.bottom()))):return core
    return path
