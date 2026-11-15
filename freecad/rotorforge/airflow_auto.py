"""Plate-aware, web-first automatic airflow design.

Automatic openings are NOT selected from the manual shape palette.  A seeded
network of continuous carbon ribs is built first; the editor clips the spaces
between those ribs to the finished plate silhouette and protected hardware.
The resulting CNC-rounded contours are saved as editable ``Web cell`` patterns.

This module has no Qt or FreeCAD dependencies, so topology, randomisation and
polygon reduction can be checked without launching the CAD workbench.
"""
import math
import random

from .cutouts import PATTERN_DEFAULTS, check_cnc_shape

INTERIOR_STYLES = ('Frame signature', 'Swept channels', 'Structural lattice',
                   'Tapered relief', 'Geometric accents')
AUTO_ROLES = ('BottomPlate', 'MidPlate', 'TopPlate',
              'ArmClampPlate', 'ArmLowerClampPlate')
AUTO_MIN_WEB_MM = 3.0
AUTO_MAX_WEB_MM = 10.0


def proposal(role, points):
    """Turn one irregular finished opening into an adjustable CNC contour."""
    if len(points) < 3:
        return None
    x0 = min(x for x, _ in points)
    x1 = max(x for x, _ in points)
    y0 = min(y for _, y in points)
    y1 = max(y for _, y in points)
    width, length = x1-x0, y1-y0
    if min(width, length) < 2 or width*length < 18:
        return None
    cx, cy = (x0+x1)*.5, (y0+y1)*.5
    verts = [[round((x-cx)/width, 7), round((y-cy)/length, 7)]
             for x, y in points]
    item = dict(PATTERN_DEFAULTS, role=role, shape='Web cell',
                width=round(width, 5), length=round(length, 5),
                x=round(cx, 5), y=round(cy, 5),
                columns=1, rows=1, rotation=0., vertices=verts, enabled=True)
    try:
        check_cnc_shape(item)
    except (ValueError, TypeError):
        return None
    return item


def mirror_pattern(candidate, axis):
    """Mirror the ENTIRE CNC contour; not just its bounding rectangle."""
    if candidate['shape'] != 'Web cell':
        raise ValueError('Automatic web mirroring requires a Web cell.')
    return dict(candidate, x=round(2*axis-candidate['x'], 5),
                rotation=round(-candidate['rotation'], 5),
                vertices=[[-u, v] for u, v in reversed(candidate['vertices'])])


def structural_web_network(bounds, style, seed, density='Balanced',
                           layout='Mirrored', web_mm=5.0):
    """Create a genuinely randomized connected carbon *skeleton*.

    Returns polylines (in millimetres) that are continuous from the central
    spine to/outside the plate. The editor strokes them at the specified carbon
    width, cuts the stroke out of the safe plate mask, and uses the remaining
    cells as *original* openings (rather than fitting predefined shapes).
    """
    left, bottom, width, height = (float(n) for n in bounds)
    if not 3 <= web_mm <= 50:
        raise ValueError('Effective carbon-web width must be at least 3 mm.')
    if min(width, height) < 18:
        return ()
    rng = random.Random(f'web-first|{style}|{seed}|{width:.3f}|{height:.3f}|{density}|{layout}')
    axis = 0.0 if left <= 0 <= left+width else left+width*.5
    mirrored = layout == 'Mirrored'
    half = min(axis-left, left+width-axis)
    if half < web_mm+4:
        return ()

    # Change the NUMBER of bays as well as junction positions when randomizing.
    step = {'Sparse': 40., 'Balanced': 30., 'Detailed': 23.}.get(density, 30.)
    if style == 'Structural lattice':
        step *= .84
    elif style == 'Swept channels':
        step *= 1.15
    elif style == 'Tapered relief':
        step *= 1.08
    bays = max(2, min(12, round(height / step) + rng.choice((-1, 0, 0, 1))))
    minimum_pitch = max(web_mm*2.3+5, 13.5)
    while bays > 2 and height/bays < minimum_pitch:
        bays -= 1
    pitch = height/bays
    # Spine extends beyond the plate and therefore separates left/right
    # openings, even at the ends of a rounded or notched plate.
    margin = max(10., web_mm*2+4)
    stations = [bottom-margin]
    for i in range(1, bays):
        jitter = pitch*rng.uniform(-.24, .24)
        stations.append(bottom+pitch*i+jitter)
    stations.append(bottom+height+margin)
    # A randomized central window deliberately omits one or sometimes two
    # spine sections. Paired cross-ribs at BOTH ends still connect the web to
    # the plate shoulders. That allows a single centred aperture, not just
    # the forced left/right rows of the former continuous-spine design.
    central_gaps = set()
    if bays >= 3 and half > max(8., web_mm*1.8) and rng.random() < .78:
        candidates = list(range(1, bays-1))
        rng.shuffle(candidates)
        central_gaps.add(candidates[0])
        if bays >= 7 and density == 'Detailed' and rng.random() < .30:
            for candidate in candidates[1:]:
                if all(abs(candidate - other) > 2 for other in central_gaps):
                    central_gaps.add(candidate)
                    break
    spine = []
    for i, y in enumerate(stations):
        # A mirrored layout keeps the spine exactly at its mirror axis;
        # organic layouts have a restrained zigzagging central spine.
        x = axis if mirrored or i in (0,len(stations)-1) else axis+rng.uniform(-.07,.07)*half
        spine.append((x,y))
    lines = []
    segment = [spine[0]]
    for i in range(len(spine)-1):
        if i in central_gaps:
            if len(segment) >= 2:
                lines.append(tuple(segment))
            segment = [spine[i+1]]
        else:
            segment.append(spine[i+1])
    if len(segment) >= 2:
        lines.append(tuple(segment))
    # Cross-ribs at either end of a central gap must not be omitted, or the
    # gap would become an uncontrolled opening at the plate perimeter.
    mandatory_stations = {j for i in central_gaps for j in (i, i+1)}

    # Different styles control the *structural webs*, not cutout shapes.
    bend_scale = {'Frame signature': .27, 'Swept channels': .38,
                  'Structural lattice': .16, 'Tapered relief': .30,
                  'Geometric accents': .42}.get(style, .28)
    for i in range(1, bays):
        y = stations[i]
        # Give every generation a new mix of rising, falling and forked ribs.
        slope = rng.uniform(-.38,.38)*pitch
        if style == 'Swept channels':
            slope *= 1.33
        if style == 'Structural lattice':
            slope *= .77
        # Long bays are intentional: omit selected ribs, exposing connected
        # areas that extend between two stations rather than countless holes.
        if i not in mandatory_stations and bays > 3 and rng.random() < ({'Sparse': .26, 'Balanced': .13,
                                         'Detailed': .055}.get(density,.13)):
            continue
        mirrored_bend=rng.uniform(.08,.38)
        mirrored_kink=(rng.uniform(-1.,1.)*pitch*bend_scale
                       if rng.random()<.17 and style in ('Frame signature','Geometric accents') else 0.)
        mirrored_bend_x=rng.uniform(.35,.73)
        for side in (-1,1):
            side_slope = slope if mirrored else slope+rng.uniform(-.18,.18)*pitch
            xx = (axis+side*(half+margin) if mirrored else
                  (left-margin if side < 0 else left+width+margin))
            bent = axis+side*half*(mirrored_bend_x if mirrored else rng.uniform(.35,.73))
            tip_y = y+side_slope
            # In mirrored mode the Y coordinates MUST be shared between
            # left and right. A random draw inside the side loop was subtly
            # breaking symmetry in earlier generators.
            if mirrored:
                inner_fraction = mirrored_bend
                kink = mirrored_kink
            else:
                inner_fraction = rng.uniform(.08,.38)
                kink = (rng.uniform(-1.,1.)*pitch*bend_scale
                        if rng.random()<.17 and style in ('Frame signature','Geometric accents') else 0.)
            inner_y = y+side_slope*inner_fraction+kink
            lines.append(((spine[i][0],y),(bent,inner_y),(xx,tip_y)))

    # Sparse diagonals tie a central spine to a neighboring bay. These make
    # triangular/diamond-shaped *regions* where enough width is available.
    if half > max(24., web_mm*4.3) and bays >= 3:
        accents = min(4, bays//2) if density != 'Sparse' else 1
        indices = list(range(1,bays-1))
        rng.shuffle(indices)
        for i in indices[:accents]:
            if i in central_gaps or i+1 in central_gaps:
                continue
            if rng.random() > {'Structural lattice':.78,'Geometric accents':.66,
                               'Frame signature':.45,'Swept channels':.32,
                               'Tapered relief':.33}.get(style,.45):
                continue
            side=rng.choice((-1,1))
            y0=stations[i]
            y1=stations[i+1]
            dest=axis+side*half*rng.uniform(.63,.87)
            midpoint=(y0+y1)*.5
            lines.append(((spine[i][0], y0),(dest,midpoint)))
            if mirrored:
                lines.append(((2*axis-spine[i][0],y0),(2*axis-dest,midpoint)))

    return tuple(lines)


def signed_area(points):
    return .5*sum(x*y2-x2*y for (x,y),(x2,y2) in
                    zip(points, points[1:]+points[:1]))


def simplify_contour(points, max_vertices=40, tolerance=.22):
    """Reduce Qt's densely tessellated contours without assuming a shape.

    Short segments and low-deviation vertices are removed first. The caller
    validates that the final analytic rounded opening remains inside the safe
    cutting region; this routine never decides manufacturing clearances.
    """
    pts=[]
    for x,y in points:
        p=(float(x),float(y))
        if not pts or math.dist(p,pts[-1])>.075:
            pts.append(p)
    if len(pts)>1 and math.dist(pts[0],pts[-1])<.075:
        pts.pop()
    if len(pts)<3:
        return []
    # Each priority is the deviation from the chord through the neighbours.
    # Discard only details smaller than the tolerance, or raise the tolerance
    # gradually when Qt tessellation creates excessively many line segments.
    tol=tolerance
    for _ in range(16):
        while len(pts)>3:
            scores=[]
            for i,p in enumerate(pts):
                a,b=pts[i-1],pts[(i+1)%len(pts)]
                dx,dy=b[0]-a[0],b[1]-a[1]
                length=math.hypot(dx,dy)
                d=(abs((p[0]-a[0])*dy-(p[1]-a[1])*dx)/length
                   if length>1e-7 else 0.)
                scores.append(d)
            index=min(range(len(scores)),key=scores.__getitem__)
            if len(pts)<=max_vertices and scores[index]>tol:
                break
            if scores[index]>tol and len(pts)>max_vertices:
                break
            pts.pop(index)
        if len(pts)<=max_vertices:
            break
        tol*=1.48
    return pts if 3<=len(pts)<=max_vertices else []


def symmetric_central_contour(points, axis, tolerance=.25, max_vertices=40):
    """Build one exactly mirrored opening straddling the plate's centre axis.

    Clipping to the right half finds one exterior boundary chain. Simplify
    that chain *once*, then reflect it to produce the left exterior boundary.
    Unlike simplification of the full polygon, this cannot introduce an
    asymmetry at the centre after R0.5 corner construction.

    Complex polygon rings with more than two centre-axis crossings are
    deliberately skipped: there may be disconnected lobes or holes, and
    those require independent treatment to remain machinable.
    """
    points=[(float(x),float(y)) for x,y in points]
    if len(points)<3:
        return []
    # Sutherland-Hodgman clip to x >= axis.
    clipped=[]
    for start,end in zip(points[-1:]+points[:-1],points):
        a=start[0]>=axis-1e-7
        b=end[0]>=axis-1e-7
        if a!=b:
            fraction=(axis-start[0])/(end[0]-start[0])
            clipped.append((axis,start[1]+fraction*(end[1]-start[1])))
        if b:
            clipped.append(end)
    cleaned=[]
    for x,y in clipped:
        p=(axis if abs(x-axis)<1e-6 else x,y)
        if not cleaned or math.dist(cleaned[-1],p)>1e-5:
            cleaned.append(p)
    if len(cleaned)>2 and math.dist(cleaned[0],cleaned[-1])<1e-5:
        cleaned.pop()
    axis_indices=[i for i,p in enumerate(cleaned) if abs(p[0]-axis)<1e-5]
    if len(axis_indices)!=2:
        return []
    i,j=axis_indices
    # Choose the boundary direction that visits the right-hand exterior,
    # rather than the artificial straight edge along the symmetry axis.
    def take_chain(step):
        chain=[]
        at=i
        for _ in range(len(cleaned)+1):
            chain.append(cleaned[at])
            if at==j:
                break
            at=(at+step)%len(cleaned)
        return chain
    chain1=take_chain(1)
    chain2=take_chain(-1)
    chain=max((chain1,chain2),key=lambda chain:max(pt[0] for pt in chain))
    if len(chain)<3 or max(x for x,_ in chain)-axis<1.:
        return []
    # Ramer-Douglas-Peucker on an open edge chain, bounded by its axis points.
    def reduce(seq,eps):
        if len(seq)<=2:return seq
        start,end=seq[0],seq[-1]
        dx,dy=end[0]-start[0],end[1]-start[1]
        norm=max(1e-9,math.hypot(dx,dy))
        deviations=[abs((p[0]-start[0])*dy-(p[1]-start[1])*dx)/norm
                    for p in seq[1:-1]]
        if not deviations or max(deviations)<=eps:return [start,end]
        index=deviations.index(max(deviations))+1
        return reduce(seq[:index+1],eps)[:-1]+reduce(seq[index:],eps)
    eps=tolerance
    reduced=reduce(chain,eps)
    for _ in range(10):
        if len(reduced)*2-2<=max_vertices:
            break
        eps*=1.5
        reduced=reduce(chain,eps)
    if len(reduced)*2-2>max_vertices or len(reduced)<3:
        return []
    result=reduced+[(2*axis-x,y) for x,y in reduced[-2:0:-1]]
    return result if len(result)>=3 else []
