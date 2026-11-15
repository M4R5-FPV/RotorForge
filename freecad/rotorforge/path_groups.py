"""Fast, Qt-free broad-phase grouping for independent planar preview profiles.

A pair of paths whose axis-aligned bounds are disjoint cannot intersect. Only
potentially touching connected components need Qt's relatively expensive exact
Boolean unions; disconnected components can be appended directly to one path.
"""


def intersecting_rect_groups(rectangles):
    """Stable groups of transitive overlapping/touching (left,top,right,bottom).

    Bounds are conservative. False positives merely leave some extra Qt work;
    false negatives must never occur because such components could overlap.
    Returns indices in original order, grouped by first occurrence.
    """
    n=len(rectangles)
    if n<2:
        return tuple((i,) for i in range(n))
    parent=list(range(n))
    size=[1]*n

    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]
            i=parent[i]
        return i

    def unite(i,j):
        ri,rj=root(i),root(j)
        if ri==rj:return
        if size[ri]<size[rj]:ri,rj=rj,ri
        parent[rj]=ri
        size[ri]+=size[rj]

    # Sweep in X: when an earlier rectangle ends before the current one
    # starts, it can never touch this or any later rectangle.
    active=[]
    for i in sorted(range(n), key=lambda k:rectangles[k][0]):
        left,top,right,bottom=rectangles[i]
        active=[j for j in active if rectangles[j][2]>=left]
        for j in active:
            other=rectangles[j]
            if other[1]<=bottom and top<=other[3]:
                unite(i,j)
        active.append(i)

    groups={}
    for i in range(n):
        groups.setdefault(root(i),[]).append(i)
    return tuple(tuple(g) for g in sorted(groups.values(), key=lambda g:g[0]))
