"""Round-ended cage grips with full-width, shoe-blended U-section roots.

The cage rails follow the actual camera-profile edges. Their base remains an
open, rounded U rather than collapsing to a narrow rectangular pedestal.
Only the shoe-contact section is clipped to the finished bumper footprint;
the upper transition retains its full camera-cage width.
"""
import math


def _at_height(profile, z):
    """Y on the front/cage profile, ordered by ascending Z."""
    for (ay, az), (by, bz) in zip(profile, profile[1:]):
        if az - 1e-8 <= z <= bz + 1e-8:
            return ay + (by - ay) * (z - az) / max(1e-10, bz - az)
    return profile[0][0] if z < profile[0][1] else profile[-1][0]


def _sculpted_outside(profile, z):
    """Broad, tangent-continuous outer fairing over sharp cage kinks.

    The hard camera-plate profile stays exact at the channel; only the OUTER
    TPU nose is rounded outward.  Use a smooth Hermite crown which cannot
    fall inside the minimum wall thickness at a kink.
    """
    y=_at_height(profile,z)
    for j in range(1,len(profile)-1):
        (ya,za),(yb,zb),(yc,zc)=profile[j-1:j+2]
        if not (za+1e-8<zb<zc-1e-8):continue
        ml=(yb-ya)/(zb-za); mr=(yc-yb)/(zc-zb)
        if ml-mr<.18 or abs(z-zb)>=2.7: continue
        r=2.7
        def base(q):
            t=(q-(zb-r))/(2*r)
            return ((2*t**3-3*t*t+1)*(yb-r*ml)
                    +(t**3-2*t*t+t)*2*r*ml
                    +(-2*t**3+3*t*t)*(yb+r*mr)
                    +(t**3-t*t)*2*r*mr)
        # The Hermite bridge's negative sag at a convex corner is compensated
        # by a smooth positive dome, with zero slope/height at both ends.
        amplitude=0.
        for i in range(1,32):
            q=zb-r+2*r*i/32
            u=(q-zb)/r
            dome=(1-u*u)**2
            linear=yb+(ml if q<zb else mr)*(q-zb)
            amplitude=max(amplitude,(linear-base(q))/dome)
        u=(z-zb)/r
        return base(z)+(amplitude+.07)*(1-u*u)**2
    return y


def _yz_face(points, x):
    import FreeCAD as App, Part
    vertices = [App.Vector(x, y, z) for y, z in points]
    return Part.Face(Part.makePolygon(vertices + [vertices[0]]))


def _rounded_u_wire(x0, x1, rear, inside, outside, z, wall, outline_y=None, outline_mix=0.):
    """True rounded U-section with radiused nose AND round-ended side grips.

    The previous release computed this wire but accidentally discarded it.
    Keep the camera aperture open at the rear: nothing fills the hollow centre.
    Both sides are symmetric and all loft stations have identical edge topology.
    """
    import FreeCAD as App, Part
    width = x1 - x0
    if width <= 2 * wall + 0.15 or outside <= inside + 0.15 or inside <= rear:
        raise ValueError('Not enough room for the rounded camera-cage grip.')

    xi0, xi1 = x0 + wall, x1 - wall
    # Most of the actual curve fits into the TPU wall, not the empty camera slot.
    rear_r = min(.5 * wall, .45 * (inside - rear))
    # A larger radius makes the nose distinctly capsule-like instead of
    # leaving a broad flat face. Keep a short straight cheek ahead of its
    # rounded rear tip, even for unusually shallow grip depths.
    front_r = min(1.70 * wall, .43 * width,
                  outside - rear - rear_r - .25)
    if front_r <= 1e-4 or rear_r <= 1e-4:
        raise ValueError('Rounded camera-cover radius has collapsed.')

    # Only full-height covers use the actual top-carbon front edge.  At the
    # top station the TPU front face follows that edge, not the cage's upper
    # mounting tab.  Gradually sweep toward it over the last several mm.
    # The top face retains a small bearing surface against the plate underside
    # (the carbon itself is still subtracted by bumper_geometry).
    def vec(x, y, front_factor=0.):
        # Leave the *inside* cage mating surface anchored to the real side
        # plate.  Only the outer nose swells toward the top-carbon outline.
        # Translating the entire U (old approach) detached the inside cheek
        # and made a small hole after subtracting the actual camera plate.
        if outline_y is not None and outline_mix > 1.e-7 and front_factor:
            boundary=outline_y(x)
            if boundary is not None:
                # End just behind the top carbon front perimeter, never
                # overshoot the plate by an entire TPU wall thickness.
                shift=max(0.,boundary-.25-outside)
                y += outline_mix*front_factor*shift
        return App.Vector(x, y, z)

    def line(a, b, fa=0., fb=0.):
        return Part.makeLine(vec(*a,fa), vec(*b,fb))

    def arc(a, middle, b, fa=0., fm=0., fb=0.):
        return Part.Arc(vec(*a,fa), vec(*middle,fm), vec(*b,fb)).toShape()

    k = 1. - 1. / math.sqrt(2.)
    # Outer U: two tangent quarter-circle nose corners. The ends of both
    # open rear cheeks are semicircular, so the side rails are not rectangles.
    # Rear_r is half a wall at the default settings; use a quarter + a short
    # rear flat only if constrained by the depth of an unusually shallow grip.
    a = (x0, rear + rear_r)
    b = (x0, outside - front_r)
    c = (x0 + front_r, outside)
    d = (x1 - front_r, outside)
    e = (x1, outside - front_r)
    f = (x1, rear + rear_r)
    g = (xi1, rear + rear_r)
    h = (xi1, inside)
    i = (xi0, inside)
    j = (xi0, rear + rear_r)
    # A curved, gradually widening outer nose forms the top-plate brow.
    # The two inner cheeks remain a close fit to the carbon cage.
    edges = [
        line(a, b, 0., .35),
        arc(b, (x0 + front_r * k, outside - front_r * k), c,
            .35, .72, 1.),
        line(c, d, 1., 1.),
        arc(d, (x1 - front_r * k, outside - front_r * k), e,
            1., .72, .35),
        line(e, f, .35, 0.),
        arc(f, (x1 - wall/2, rear), g),
        line(g, h),
        line(h, i),
        line(i, j),
        arc(j, (x0 + wall/2, rear), a),
    ]
    return Part.Wire(edges)


def _make_rounded_grip(sections):
    """Build the actual curved wire, never silently substitute square rails.

    A ruled loft follows the real cage exactly and avoids overshooting its
    tilt clearance. Smooth loft is an alternate OCC path, not a flat fallback.
    """
    import Part
    errors = []
    for ruled in (False, True):
        try:
            result = Part.makeLoft(sections, True, ruled)
            if (not result.isNull() and result.isValid() and
                    len(result.Solids) == 1 and result.Volume > 1e-5):
                return result
            errors.append(f'ruled={ruled}: invalid or disconnected')
        except Exception as exc:
            errors.append(f'ruled={ruled}: {exc}')
    # Do not pretend the rounding succeeded by returning the old rectangle.
    raise ValueError('Could not build the rounded camera-cage grip: ' + '; '.join(errors))

def _smoothstep(t):
    t=max(0.,min(1.,t))
    return t*t*t*(10.+t*(-15.+6.*t))


def _front_edge_function(segments):
    """Find the actual foremost point on the TOP PLATE perimeter at X.

    The edges are sampled from the plate's outer wire, not the rectangular
    bounding box.  Concave noses and curved plate shoulders are supported.
    Segment format is (x0,y0,x1,y1) to stay independent of the CAD kernel.
    """
    from functools import lru_cache
    segs=tuple(segments)
    @lru_cache(maxsize=128)
    def lookup(x):
        hits=[]
        for ax,ay,bx,by in segs:
            lo=min(ax,bx);hi=max(ax,bx)
            if lo-1.e-6<=x<=hi+1.e-6:
                if abs(ax-bx)<1.e-8:
                    hits.extend((ay,by))
                else:
                    f=max(0.,min(1.,(x-ax)/(bx-ax)))
                    hits.append(ay+(by-ay)*f)
        return max(hits) if hits else None
    return lookup


def camera_cover(p, outer, rail, front, upper, top_outline=None):
    """Continuous rounded camera grip-to-shoe loft without a Boolean junction.

    A single continuous skin, instead of a separate camera grip plus a
    shoulder joined by a Boolean. The lower contact is clipped against the
    exact TPU shoe contour (not its bounding rectangle) and the grip above
    the contact retains its actual dimensions and full cage length.
    """
    import FreeCAD as App, Part
    from .parameters import plate_levels
    wall=p.FlexBumperWall
    count=len(rail['points'])//2
    inner=rail['points'][:count]
    outside=tuple(reversed(rail['points'][count:]))
    rear=rail['cheeks'][:count]
    x0=rail['xmin'];x1=x0+rail['width']
    # Zero means the true *top-plate underside*, without the older mandatory
    # 0.35-mm air gap.  A positive height remains an intentionally partial rail.
    full_height=(p.FlexBumperCameraHeight <= 1.e-8)
    top=min(inner[-1][1],plate_levels(p)['top_z'])
    if not full_height:
        top=min(top,p.BottomThickness+p.FlexBumperCameraHeight)
    low=rail['low']
    outline_y=_front_edge_function(top_outline) if full_height and top_outline else None
    # A gradual sweep to the actual top-front plate contour.
    top_sweep=min(5.7,max(3.5,.19*(top-low)))
    if top-low<=1.0:
        raise ValueError('Camera cage requires more height for a round bumper transition.')
    high=min(upper+7.,top-0.25)
    if high<upper+1.:
        high=upper+.5
    if high>=top:
        high=top-.05
    # Very short covers may have no room for a separate foot-to-grip blend.
    # Keep their ordinary rounded grip instead of creating inverted stations.
    if top<=upper+.05:
        tip_trim=min(.80,.55*wall,.30*p.FlexBumperCameraGripDepth)
        sections=[_rounded_u_wire(x0,x1,_at_height(rear,z)+tip_trim,
                   _at_height(inner,z),_sculpted_outside(outside,z),z,wall,
                   outline_y,_smoothstep((z-(top-top_sweep))/top_sweep))
                  for z in sorted({low,top,*[b[1] for b in inner if low<b[1]<top],
                                   top-.75*top_sweep,top-.5*top_sweep,top-.25*top_sweep}) if low<=z<=top]
        return _make_rounded_grip(sections)

    # Exact shoe footprint, used to find a large embedded landing.
    reach=p.FlexBumperCameraBlendReach
    inside_x=(min(0.,x1+reach) if x0<0 else max(0.,x0-reach))
    shoe_x=outer.BoundBox.XMin if x0<0 else outer.BoundBox.XMax
    bx0,bx1=min(inside_x,shoe_x),max(inside_x,shoe_x)
    by0=rail['foot_y']+.35*wall
    by1=outer.BoundBox.YMax
    region=Part.Face(Part.makePolygon([
        App.Vector(bx0,by0,0),App.Vector(bx1,by0,0),
        App.Vector(bx1,by1,0),App.Vector(bx0,by1,0),
        App.Vector(bx0,by0,0)]))
    foot=outer.common(region)
    faces=[f for f in foot.Faces if f.Area>1e-5]
    if not faces:
        raise ValueError('Camera cage bumper has no usable overlap with the shoe.')
    bb=max(faces,key=lambda f:f.Area).BoundBox
    fx0,fx1=bb.XMin+.08,bb.XMax-.08
    front_y=bb.YMax-.08
    in_y=front_y-max(wall,.32*(bb.YMax-bb.YMin))
    # Keep the U's rear opening shallow where it becomes embedded in the
    # bumper.  A deep open notch at this station produced a triangular void.
    back_y=max(bb.YMin+.08,in_y-.42)
    if (fx1-fx0 < 2*wall+.4 or front_y-in_y < .3
            or in_y-back_y < .3):
        raise ValueError('Camera cage bumper foot is too small for the rounded grip.')
    tip_trim=min(.80,.55*wall,.30*p.FlexBumperCameraGripDepth)
    # Progressively approach the actual cage profile with zero lateral
    # shift at the handover to remove the old grip/shoulder seam.
    span=max(1e-4,high-low)
    heights=set((low,upper,high,top))
    for t in (.07,.15,.25,.37,.50,.64,.78,.90,.97):
        heights.add(low+t*span)
    for a,b in zip(inner,inner[1:]):
        if high<a[1]<top:heights.add(a[1])
    for (ya,za),(yb,zb),(yc,zc) in zip(outside,outside[1:],outside[2:]):
        if not (za<zb<zc):continue
        if (yb-ya)/(zb-za)-(yc-yb)/(zc-zb)<.18:continue
        heights.update(zb+2.7*t for t in (-1.,-.8,-.6,-.4,-.2,0.,.2,.4,.6,.8,1.) if low<zb+2.7*t<top)
    if outline_y is not None:
        heights.update(top-top_sweep*t for t in (0.,.125,.25,.375,.5,.625,.75,.875,1.))
    wires=[]
    for z in sorted(heights):
        t=min(1.,max(0.,(z-low)/span))
        ease=t*t*t*(10.+t*(-15.+6.*t))  # zero-slope quintic at each end
        gx0=fx0*(1-ease)+x0*ease
        gx1=fx1*(1-ease)+x1*ease
        gyrear=back_y*(1-ease)+(_at_height(rear,z)+tip_trim)*ease
        gyinside=in_y*(1-ease)+_at_height(inner,z)*ease
        gyoutside=front_y*(1-ease)+_sculpted_outside(outside,z)*ease
        wires.append(_rounded_u_wire(gx0,gx1,gyrear,gyinside,gyoutside,z,wall,
                     outline_y,_smoothstep((z-(top-top_sweep))/top_sweep)))
    # Build the curved surface with a smooth interpolated loft first.  A
    # ruled loft is retained as a reliable fallback for FreeCAD/OCC versions
    # that reject a particular highly curved spline.  Do not silently fall
    # back to square/rectangular grips.
    #
    # This is an OPEN U section already. The old secondary YZ camera-channel
    # cutter touched the interpolated B-spline surfaces tangentially and in
    # some OCC builds collapsed a valid smooth cover to a null shape. Carbon
    # cage solids and the real camera envelope are subtracted by the parent
    # front_bumper builder after these guards have joined the shoe.
    cutoff=min(high-.3,upper+.05)
    mask=outer.extrude(App.Vector(0,0,cutoff-low+1.))
    mask.translate(App.Vector(0,0,low-.5))
    mask_y0=min(y for y,z in rear)-8.
    mask_y1=max(by1,max(y for y,z in outside))+8.
    wide=Part.makeBox(bx1-bx0+30.,mask_y1-mask_y0,top-cutoff+2.,
                      App.Vector(bx0-15.,mask_y0,cutoff))
    mask=mask.fuse(wide)
    errors=[]
    for ruled in (False, True):
        try:
            cover=Part.makeLoft(wires,True,ruled)
            if (cover.isNull() or not cover.isValid() or
                    len(cover.Solids)!=1 or cover.Volume<=1e-5):
                raise ValueError('loft is null, disconnected or invalid')
            cover=cover.common(mask)
            if (cover.isNull() or not cover.isValid() or
                    len(cover.Solids)!=1 or cover.Volume<=1e-5):
                raise ValueError('shoe outline clipping separated the cover')
            # No planar camera-channel subtraction: the U is already open.
            # Avoid cutting the smooth surface with exactly tangent tools.
            return cover
        except Exception as exc:
            errors.append(f'ruled={ruled}: {exc}')
    raise ValueError('Could not finish the smoothly blended camera guard: '+
                     '; '.join(errors))
