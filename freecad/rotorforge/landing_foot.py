"""Filled, tip-only tapered TPU landing sole below the motor protector.

The landing foot is a filled extension below the existing TPU protector
floor, not a perimeter-only skirt. Its rear cutoff (around the motor
centreline) tilts towards the front of the motor as it descends; its outer
boundary offsets inward. The original floor remains continuous, ensuring
there is no vertical cutoff on the *extended* foot. Decorative carbon-tip
windows do not pass through the support; the assembled protector is drilled
once with the original motor mounting tools.

FreeCAD/Part are imported only in native-CAD construction functions.
"""
import math


def tip_foot_axis(p, arm):
    """Outward axis of this specific arm, including its directional tip bias."""
    from .motor_pads import motor_pad_unit
    ux, uy = motor_pad_unit(p, arm)
    direction = p.ArmTipBumperDirection
    if direction != 'Pad direction' and p.ArmTipBumperStyle != 'Disabled':
        mx, my = arm['motor']
        if direction == 'Front / rear':
            tx, ty = 0.0, math.copysign(1.0, my)
        elif direction == 'Sideways outwards':
            tx, ty = math.copysign(1.0, mx), 0.0
        else:
            tx, ty = ux, uy
        ux, uy = ux + .4 * tx, uy + .4 * ty
        length = math.hypot(ux, uy)
        ux, uy = ux / length, uy / length
    return ux, uy


def tapered_foot_scales(p, forward_extent=None):
    """Return bottom inset scale for a filled cap, about the motor centre."""
    if forward_extent is None:
        forward_extent = max(9., p.MotorPadDiameter / 2 +
                             (.5 * p.ArmTipBumperReach if p.ArmTipBumperStyle != 'Disabled' else 0.))
    forward_extent = max(1., float(forward_extent))
    inward = min(2.5, .65 * max(0., p.FlexProtectorLanding), .18 * forward_extent)
    return max(.82, 1. - inward / forward_extent)


def _ring_area(points):
    return .5 * sum(a[0] * b[1] - b[0] * a[1]
                      for a, b in zip(points, points[1:] + points[:1]))


def _ring_valid(points):
    """Reject inverted, collapsed and self-intersecting inset footprints."""
    if len(points) < 3 or abs(_ring_area(points)) < .01:
        return False

    def crosses(a, b, c, d):
        def orient(p, q, r):
            return (q[0]-p[0]) * (r[1]-p[1]) - (q[1]-p[1]) * (r[0]-p[0])
        t1, t2 = orient(a,b,c), orient(a,b,d)
        t3, t4 = orient(c,d,a), orient(c,d,b)
        return ((t1 > 1.e-7 and t2 < -1.e-7 or t1 < -1.e-7 and t2 > 1.e-7)
                and (t3 > 1.e-7 and t4 < -1.e-7 or t3 < -1.e-7 and t4 > 1.e-7))

    n = len(points)
    for i in range(n):
        a, b = points[i], points[(i + 1) % n]
        if math.hypot(b[0]-a[0], b[1]-a[1]) < 1.e-6:
            return False
        for j in range(i + 2, n):
            if i == 0 and j == n-1:
                continue
            if crosses(a, b, points[j], points[(j+1) % n]):
                return False
    return True


def _inset_vertices(points, amount):
    """Offset *all* boundary edges, including radial/notch edges.

    Uniform scaling about the motor leaves a radial side face vertical.
    Move each edge along its inward normal instead, retaining one vertex
    per upper vertex so OpenCascade can make a stable, ruled solid loft.
    Miter lengths are limited to prevent long wedges at sharp corners.
    """
    sign = 1. if _ring_area(points) > 0 else -1.
    result = []
    count = len(points)
    for i, (x, y) in enumerate(points):
        px, py = points[i-1]
        qx, qy = points[(i+1) % count]
        dx0, dy0 = x-px, y-py
        dx1, dy1 = qx-x, qy-y
        l0, l1 = math.hypot(dx0,dy0), math.hypot(dx1,dy1)
        if min(l0, l1) < 1.e-8:
            return None
        n0 = (-sign*dy0/l0, sign*dx0/l0)
        n1 = (-sign*dy1/l1, sign*dx1/l1)
        den = 1. + n0[0]*n1[0] + n0[1]*n1[1]
        if den < .025:
            return None
        vx = amount * (n0[0] + n1[0]) / den
        vy = amount * (n0[1] + n1[1]) / den
        # Prevent spike-like slivers at acute concave and convex corners.
        miter = math.hypot(vx, vy)
        limit = 2.3 * amount
        if miter > limit:
            vx, vy = vx*limit/miter, vy*limit/miter
        result.append((x+vx, y+vy))
    return result


def _point_in_ring(point, ring):
    x,y=point
    inside=False
    for (x0,y0),(x1,y1) in zip(ring,ring[1:]+ring[:1]):
        if (y0>y)!=(y1>y) and x < (x1-x0)*(y-y0)/(y1-y0)+x0:
            inside=not inside
    return inside


def _inset_ring(points, requested):
    """Use the largest safe normal inset without changing wire topology."""
    area = _ring_area(points)
    for fraction in (1., .8, .65, .5, .35, .25, .15, .08):
        amount = requested * fraction
        lower = _inset_vertices(points, amount)
        if lower is None or _ring_area(lower)*area <= .01 or not _ring_valid(lower):
            continue
        if all(_point_in_ring(((a[0]+b[0])*.5, (a[1]+b[1])*.5), points)
               for a,b in zip(lower, lower[1:]+lower[:1])):
            return lower
    raise ValueError('The arm-tip footprint is too narrow for an inward-tapered landing foot.')


def _profile_points(wire):
    """Use the same sampled high-detail contour at both loft elevations."""
    vertices = wire.discretize(Deflection=.12)
    pts = []
    for v in vertices:
        xy = (v.x, v.y)
        if not pts or math.hypot(xy[0]-pts[-1][0], xy[1]-pts[-1][1]) > .005:
            pts.append(xy)
    if len(pts) > 3 and math.dist(pts[0], pts[-1]) < .005:
        pts.pop()
    # Very short fragments from offset curves can create degenerate OCC faces.
    if len(pts) < 3:
        raise ValueError('Arm-tip landing foot has no usable outline.')
    return pts


def _polygon_wire(points, height):
    import FreeCAD as App
    import Part
    vertices = [App.Vector(x, y, height) for x,y in points]
    return Part.makePolygon(vertices + [vertices[0]])


def _forward_mask(p, arm, rear_overlap=0.):
    """Planar outward half-space; small rear overlap joins the unchanged floor."""
    import FreeCAD as App
    import Part
    ux, uy = tip_foot_axis(p, arm)
    vx, vy = -uy, ux
    mx, my = arm['motor']
    span = max(100., 4. * p.MotorPadDiameter + 4. * p.ArmTipBumperReach)
    stations = ((-rear_overlap, -span), (span, -span), (span, span), (-rear_overlap, span))
    corners = [App.Vector(mx + ux * a + vx * b,
                          my + uy * a + vy * b, 0.) for a, b in stations]
    return Part.Face(Part.makePolygon(corners + [corners[0]]))


def inclined_rear_clip(p, arm, bottom_z, top_z, bottom_station, top_station):
    """Solid positive-outward halfspace with a ruled (not vertical) rear face.

    Stations are millimetres along the selected arm's outward axis measured
    from the motor centre. Used by both the landing sole and tip-side sleeve,
    so the highlighted rear faces are controlled by the same user angle.
    """
    import FreeCAD as App
    import Part
    if top_z <= bottom_z:
        raise ValueError('Rear-face taper requires a positive vertical span.')
    ux, uy = tip_foot_axis(p, arm)
    vx, vy = -uy, ux
    mx, my = arm['motor']
    span = max(120., 5. * p.MotorPadDiameter + 5. * p.ArmTipBumperReach)
    # Extend the cutting tool slightly past both ends while preserving its
    # exact slope inside the actual z interval. This prevents coplanar faces.
    slope = (top_station - bottom_station) / (top_z - bottom_z)
    za, zb = bottom_z - .2, top_z + .2
    sa = bottom_station + slope * (za - bottom_z)
    sb = top_station + slope * (zb - top_z)
    profile = ((sa, za), (span, za), (span, zb), (sb, zb))
    vertices = [App.Vector(mx + ux * station - vx * span,
                           my + uy * station - vy * span, height)
                for station, height in profile]
    section = Part.Face(Part.makePolygon(vertices + [vertices[0]]))
    return section.extrude(App.Vector(2. * span * vx, 2. * span * vy, 0))


def _incline_only_rear_face(upper_pts, lower_pts, motor, axis, upper_station,
                            angle_degrees, foot_height):
    """Incline the motor-centreline face without changing the outer taper.

    Only vertices on the *original rear closing line* move.  All other
    vertices of the lower profile (including the exterior walls, tip apex
    and concave outer sections) are left untouched.

    The angular parameter changes the horizontal position of those lower
    vertices relative to the top vertices by h*tan(angle).  This avoids the
    previous no-op/dead-zone when a second cutter was used after an inset.
    """
    ux, uy = axis
    shift = math.tan(math.radians(float(angle_degrees))) * foot_height
    bottom_station = upper_station + shift
    new_lower = list(lower_pts)
    hits = []
    for i, (x, y) in enumerate(upper_pts):
        station = (x - motor[0])*ux + (y - motor[1])*uy
        if abs(station - upper_station) <= .035:
            hits.append(i)
            lx, ly = new_lower[i]
            actual = (lx-motor[0])*ux + (ly-motor[1])*uy
            delta = bottom_station - actual
            new_lower[i] = (lx + delta*ux, ly + delta*uy)
    if len(hits) < 2:
        raise ValueError('Cannot locate the two centreline face corners on the landing foot.')
    if not _ring_valid(new_lower):
        raise ValueError('The requested inner-face angle folds the landing foot profile. '
                         'Reduce the angle or increase the motor-tip reach.')
    # Angle control may alter only the closing-line vertices.  In particular,
    # not one exterior side or front tip point is allowed to move.
    assert all(a == b for i,(a,b) in enumerate(zip(lower_pts,new_lower)) if i not in hits)
    return new_lower


def tip_tapered_foot(p, arm, outer, inner, top_z, bottom_z, pad_shape=None):
    """Build a SOLID front-half tapered landing sole, not a perimeter rim.

    `outer` is the full unperforated TPU outline. `inner` and `pad_shape`
    are accepted for compatibility but not subtracted. The top of the sole
    overlaps the existing protector underside by 0.08 mm. The rear cutoff
    ramps inwards/forwards to a *different lower station*, eliminating the
    straight side wall at the landing-foot step. Carbon decoration remains
    unperforated underneath; only motor bores are removed after fusion.
    """
    import FreeCAD as App
    import Part

    if not top_z > bottom_z:
        raise ValueError('Tip-only landing foot must extend below the protector floor.')
    motor = arm['motor']

    # The upper back edge runs a little behind the motor centreline and
    # overlaps the original floor. The *lower* back edge moves *forward*;
    # this gives the trailing end face a physical diagonal, instead of the
    # former rectangular 90-degree step from the main protector.
    foot_height=top_z-bottom_z
    rear_overlap=min(1.0,max(.45,foot_height*.20))
    # Build the rear wall vertically as an initial stock shape.  A bevel
    # cutter applied to the FINAL combined protector later constructs the
    # rear incline. Building a sloping face on the sole alone cannot remove
    # the vertical material left by the protector floor and final booleans.
    forward=outer.common(_forward_mask(p,arm,rear_overlap=rear_overlap))
    faces=[f for f in forward.Faces if f.Area > 1.e-5]
    if not faces:
        raise ValueError('Tip-only landing foot has no footprint ahead of the motor.')
    ux,uy=tip_foot_axis(p,arm)

    sections = []
    for face in faces:
        upper_pts = _profile_points(face.OuterWire)
        extent = max((x - motor[0]) * ux + (y - motor[1]) * uy
                     for x,y in upper_pts)
        if extent <= .1:
            continue
        # Boundary-normal offsets taper the outer wall, concave corners and
        # the two inward-facing cut-off walls as one continuous solid.  Keep
        # topology matched across both elevations for a reliable ruled loft.
        radial_scale = tapered_foot_scales(p, extent)
        requested_inset = max(.05, (1. - radial_scale) * extent)
        lower_pts = _inset_ring(upper_pts, requested_inset)
        # Fix the lower closing edge at its ORIGINAL centreline station.
        # Every outer/front vertex stays at the same tapered location.
        # The adjustable rear-wall bevel is cut from the final fused solid,
        # after drilling, so a vertical remnant cannot mask the result.
        lower_pts = _incline_only_rear_face(
            upper_pts, lower_pts, motor, (ux, uy), -rear_overlap,
            0.0, foot_height)
        sole = Part.makeLoft([
            _polygon_wire(upper_pts, top_z),
            _polygon_wire(lower_pts, bottom_z),
        ], True, True)
        if sole.isNull() or sole.Volume <= 1.e-6:
            raise ValueError('Cannot construct the inclined rear face for this arm tip.')
        # No copied pad windows here: they are decorative carbon openings,
        # not holes in the landing sole. The selected screw-retention pattern
        # is cut once on the fused protector + landing foot below.
        sections.append(sole)
    if not sections:
        raise ValueError('Tip-only landing foot has no forward footprint.')
    foot = sections[0] if len(sections) == 1 else Part.makeCompound(sections)

    # No cuts are performed within this helper. The completed protector is
    # drilled once with the selected motor-screw or linked-access retention
    # pattern; decorative carbon tip windows are never copied into this foot.
    if foot.isNull() or not foot.isValid() or foot.Volume <= 1.e-6:
        raise ValueError('Filled tip landing foot has insufficient material. '
                         'Increase the tip width/reach or reduce the screw clearance.')
    return foot


