"""Conservative native-CAD broad phase. No FreeCAD imports."""
from math import sqrt

def box_distance(a,b):
    """Lower bound on exact shape distance from enclosing axis-aligned boxes."""
    dx=max(0.,a.XMin-b.XMax,b.XMin-a.XMax)
    dy=max(0.,a.YMin-b.YMax,b.YMin-a.YMax)
    dz=max(0.,a.ZMin-b.ZMax,b.ZMin-a.ZMax)
    return sqrt(dx*dx+dy*dy+dz*dz)

def disjoint_groups(first,second,margin=1e-6):
    """True only if ALL solid boxes have a strict gap. Touches still use OCC."""
    return bool(first and second) and all(box_distance(a,b)>margin for a in first for b in second)


class EnclosingBox:
    """Scalar enclosing bounds, also usable with native FreeCAD boxes."""
    __slots__=('XMin','YMin','ZMin','XMax','YMax','ZMax')
    def __init__(self,boxes,points=()):
        boxes=tuple(boxes);points=tuple(points)
        for axis in 'XYZ':
            coords=[getattr(p,axis.lower()) for p in points]
            setattr(self,axis+'Min',min([getattr(b,axis+'Min') for b in boxes]+coords))
            setattr(self,axis+'Max',max([getattr(b,axis+'Max') for b in boxes]+coords))


def separated_box_groups(boxes, margin=1e-5):
    """Connected groups of potentially intersecting boxes; stable item order."""
    remaining=set(range(len(boxes)));groups=[]
    while remaining:
        first=min(remaining);remaining.remove(first);group=[first]
        for i in group:
            nearby=[j for j in sorted(remaining) if box_distance(boxes[i],boxes[j])<=margin]
            remaining.difference_update(nearby);group.extend(nearby)
        groups.append(tuple(sorted(group)))
    return tuple(groups)
