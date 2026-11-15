"""Single-skin, plate-outline TPU camera cage.

The structural cage cheeks are generated directly from two actual finished carbon
perimeters. This is not a cosmetic envelope joined to legacy camera brackets.
"""
import math
import time
import FreeCAD as App
import Part

from .camera_cages import boss_x
from .fpv import camera_angles, camera_mounts
from .geometry import arc_slot, camera_envelope
from .flex_geometry import camera_window


def _y_bounds(profile, z):
    hits = []
    for (y0,z0),(y1,z1) in zip(profile,profile[1:]+profile[:1]):
        if abs(z1-z0)<1e-9:
            if abs(z-z0)<1e-7: hits.extend((y0,y1))
        elif min(z0,z1)-1e-7 <= z <= max(z0,z1)+1e-7:
            t=(z-z0)/(z1-z0)
            hits.append(y0+(y1-y0)*t)
    if not hits: raise ValueError('Camera cage profile does not cover its mounting height.')
    return min(hits),max(hits)


def _front_sampler(face):
    """Cache a *single* discretization of the finished plate perimeter.

    Previously the builder called OCC face.common(line) at ~80 stations for
    each cage (most of them in the lower floor). Each call repeated a full
    BRep intersection with a profiled plate. Instead, intersect vertical
    lines with the already-discretized perimeter in Python. The original
    OCC intersection remains available for numerical fallback.
    """
    from .cage_extensions import front_at_x
    edges=[]
    for e in face.OuterWire.Edges:
        # Fine enough for the TPU's contact profile, including rounded noses.
        pts=e.discretize(Deflection=.04)
        for a,b in zip(pts,pts[1:]):
            if abs(a.x-b.x)<1.e-9:
                edges.append((a.x,a.y,b.x,b.y))
            else:
                edges.append((a.x,a.y,b.x,b.y))
    if not edges:
        return lambda x:front_at_x(face,x)
    def at(x):
        hits=[]
        for x0,y0,x1,y1 in edges:
            if x<min(x0,x1)-1.e-7 or x>max(x0,x1)+1.e-7:continue
            if abs(x1-x0)<1.e-9:
                if abs(x-x0)<1.e-7:hits.extend((y0,y1))
            else:
                t=(x-x0)/(x1-x0)
                if -1.e-7<=t<=1.+1.e-7:hits.append(y0+t*(y1-y0))
        if hits:return max(hits)
        # This can happen on an unusual, extremely small plate edge.
        return front_at_x(face,x)
    return at


def _intersection_inside_operands(hit, a, b, tolerance=0.08):
    """Reject OCC common() artifacts outside either operand's bounding box.

    The intersection of two solids is necessarily contained in both solids.
    This check is independent of the loft construction and camera tilt.
    """
    if hit.isNull() or hit.Volume <= 1.e-7:
        return True
    hb=hit.BoundBox
    for shape in (a,b):
        bb=shape.BoundBox
        if (hb.XMin < bb.XMin-tolerance or hb.XMax > bb.XMax+tolerance or
            hb.YMin < bb.YMin-tolerance or hb.YMax > bb.YMax+tolerance or
            hb.ZMin < bb.ZMin-tolerance or hb.ZMax > bb.ZMax+tolerance):
            return False
    return True


def _stage(label, started):
    """Print timed checkpoints to FreeCAD's report view for slow builds."""
    elapsed=time.monotonic()-started
    try:App.Console.PrintMessage('[RotorForge TPU cage] %s: %.2fs\n' % (label,elapsed))
    except Exception:pass


def _spline(points):
    curve=Part.BSplineCurve()
    curve.interpolate(points)
    return curve.toShape()


def _boss_support_rear(p, mount, z, normal_rear):
    """The user's straight rear termination is authoritative.

    Do not grow a curved boss-support fin behind the selected cage reach.
    Validate the mounting layout separately before creating the loft.
    """
    return normal_rear


def _side_section(p,mount,bottom_front,top_front,x,rear_contacts):
    """One smooth closed YZ section; top and bottom contact the real plates."""
    z0,z1=mount['z0'],mount['z1']
    lower=bottom_front(x)
    upper=top_front(x)
    rear=[];front=[]
    for i in range(21):
        t=i/20.
        z=z0+(z1-z0)*t
        r,_=_y_bounds(mount['wall_profile'],z)
        # Zero projection at plate interfaces; a soft raised nose between them.
        eased=t*t*(3.-2.*t)
        projection=0.0  # Both carbon contacts are authoritative; no legacy bumper shaping
        y=(1.-eased)*lower+eased*upper+projection*math.sin(math.pi*t)**2
        # The independent upper and lower rear reach controls set the back
        # edge of the *same* side wall. At mounting faces the cage must also
        # contain the original M3 insert boss locations.
        reach=(1.-eased)*p.CameraTPUBottomRearReach + eased*p.CameraTPUTopRearReach
        # The front contact follows the true plate perimeter at this X.
        # The rear contact is a constant Y plane across the width of each
        # wall, not a translated copy of the shaped front plate outline.
        # This gives the requested straight rear termination in top view.
        rear_limit=(1.-eased)*rear_contacts[0]+eased*rear_contacts[1]
        r=_boss_support_rear(p,mount,z,rear_limit)
        # The wall itself now encloses the mounting bosses at both contacts.
        # Avoid manufacturing a disconnected little cylinder and then trying
        # to fuse it to a surface it may only touch tangentially.
        if y-r<1.5:
            raise ValueError('Insufficient room for a continuous TPU camera cage wall near the plate outline.')
        rear.append(App.Vector(x,r,z))
        front.append(App.Vector(x,y,z))
    edges=[_spline(rear), Part.makeLine(rear[-1],front[-1]),
           _spline(list(reversed(front))),Part.makeLine(front[0],rear[0])]
    wire=Part.Wire(edges)
    if not wire.isClosed() or not wire.isValid():
        raise ValueError('TPU cage section cannot follow this plate outline.')
    return wire


def _side_wall(p,mount,bottom_front,top_front):
    xmin,xmax=mount['plate_x']
    # Profile the actual front edge at several stations, including at both
    # sides of the wall, to prevent a loft chord cutting across plate curves.
    # Seven stations constrain both carbon-contact curves. Three stations
    # could bow away from an irregular front plate between the ends and centre.
    positions=[xmin+(xmax-xmin)*i/6. for i in range(7)]
    # Anchor the two straight rear lines to a common centre station. The
    # curved front boundary is sampled independently across the full wall.
    xcentre=(xmin+xmax)*.5
    rear_contacts=(bottom_front(xcentre)-float(p.CameraTPUBottomRearReach),
                   top_front(xcentre)-float(p.CameraTPUTopRearReach))
    sections=[_side_section(p,mount,bottom_front,top_front,x,rear_contacts)
              for x in positions]
    shape=Part.makeLoft(sections,True,False)
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1:
        raise ValueError('Plate-following TPU cage wall could not create one valid smooth solid.')
    return shape



def _hard_wall_sections(p, mount, bottom_front, top_front):
    """A straight, ruled inner cheek for all TPU camera isolation methods.

    The continuous wall is not a stack of moving loft sections. The inner X face is
    the same from the underside of the top plate to the top of the bottom plate.
    Only the plate-derived *front Y contour* and the fixed outside X boundary
    vary between these contacts. There is no inward-outward easing profile,
    attached bearing cylinder or segmented approximation near the plates.

    The straight inner wall can make the TPU too thin around a mounting socket
    for some combinations of camera width and plate width. Such a configuration
    must be rejected by the existing solid/fastener checks; it must never be
    'fixed' by moving the exterior off the user's carbon-plate outline.
    """
    from .flex import tpu_hard_bearing, camera_inner
    camera_x = camera_inner(p)  # same camera-facing X in all TPU modes
    z0, z1 = mount['z0'], mount['z1']
    if z1-z0 <= 1.2:
        raise ValueError('The TPU cage is too short for a continuous hard-mount wall.')
    xmin, xmax = mount['plate_x']
    left = xmax < 0
    outside = xmin if left else xmax
    inside = -camera_x if left else camera_x
    lo, hi = (outside, inside) if left else (inside, outside)
    if hi-lo < 1.2:
        raise ValueError('Hard mount needs at least 1.2 mm TPU between its fixed exterior and straight inner wall.')

    # The bottom and top profiles are the ONLY loft sections. By using a
    # single ruled span there can be no bands/creases from intermediate loft
    # stations and no spline overshoot into the camera or the front nose.
    # Both profiles sample the plate's front edge at its original wall X
    # range; this preserves the shape even when the inner X face is relocated.
    xcentre = (xmin+xmax)*.5
    def contact(z, front_sampler, rear_reach):
        rear = front_sampler(xcentre) - float(rear_reach)
        samples = []
        for i in range(13):
            t = i/12.
            x = lo+(hi-lo)*t
            # Sample at the actual generated X coordinate. Remapping this
            # through the previous (narrower) wall X interval made the nose
            # drift off the finished carbon outline at the plate contacts.
            front_y = front_sampler(x)
            if front_y-rear < 1.5:
                raise ValueError('Insufficient TPU front-to-rear reach for the hard-mount wall.')
            samples.append(App.Vector(x,front_y,z))
        a, b = App.Vector(lo,rear,z), App.Vector(hi,rear,z)
        wire = Part.Wire([Part.makeLine(a,b),Part.makeLine(b,samples[-1]),
                          _spline(list(reversed(samples))),Part.makeLine(samples[0],a)])
        if not wire.isClosed() or not wire.isValid():
            raise ValueError('The TPU hard-mount contact profile is invalid.')
        return wire

    bottom = contact(z0,bottom_front,p.CameraTPUBottomRearReach)
    top = contact(z1,top_front,p.CameraTPUTopRearReach)
    wall = Part.makeLoft([bottom,top],True,True)
    if wall.isNull() or not wall.isValid() or len(wall.Solids)!=1:
        raise ValueError('Straight TPU hard-mount side wall did not form one valid solid.')
    bb = wall.BoundBox
    if bb.XMin < lo-.10 or bb.XMax > hi+.10:
        raise ValueError('Straight TPU hard-mount wall exceeded its fixed outside/inside limits.')
    return wall


def _mount_with_socket_width(p, mount):
    """Never shift the finished plate-following outer face for a socket.

    The portable layout chooses a carbon-supported M3 datum, reserves the
    full socket footprint in the stable wall, and checks camera clearance
    separately. No opportunistic X expansion is permitted here.
    """
    from .tpu_mount_layout import fit_check
    issue=fit_check(p)
    if issue:raise ValueError(issue)
    return mount



def _bosses_and_openings(p,mount):
    """Build mounting material inside the cage's top/bottom contact planes.

    Previously the boss extended 0.08 mm beyond the carbon-contact face at
    both ends. This creates a coincident-end-face Boolean against the plate-
    following loft and can defeat OCC fusion despite real volume overlap.
    The blind pocket keeps its original axis and dimensions.
    """
    from .geometry import cylinder
    xmin,xmax=mount['plate_x']
    centre=boss_x(p,-1 if xmin<0 else 1)
    depth=float(p.CameraTPUInsertDepth)
    rad=float(p.CameraTPUScrewBore)/2
    z0,z1=mount['z0'],mount['z1']
    bosses=[];pockets=[]
    for ys,z,direction in ((mount['tabs_y'],z0,1),
                           (mount['top_tabs_y'],z1,-1)):
        for y in ys:
            # A socket may extend INSIDE the cage by 1 mm, not outside the
            # upper/lower carbon contact. Do not add a sliver across z0/z1.
            start=z if direction>0 else z-depth-1.
            bosses.append(cylinder(centre,y,rad+p.CameraTPUBossWall+.20,
                                    start,depth+1.))
            pockets.append(cylinder(centre,y,rad,
                                    z-.01 if direction>0 else z-depth-.01,
                                    depth+.03))
    return bosses,pockets

def _bounded_bridge_curve(points):
    """A single smooth edge, constrained to its sampled design envelope.

    Segmented polylines eliminate spline overshoot but leave many visible OCC
    edges. A cubic spline is suitable only when it stays inside its samples'
    bounded envelope; otherwise use one smooth approximation with controlled
    fit rather than hundreds of line segments.
    """
    if len(points) < 3:
        return Part.makePolygon(points)
    curve = Part.BSplineCurve()
    curve.interpolate(points)
    edge = curve.toShape()
    ys=[v.y for v in points]
    allowance=.08
    if (edge.BoundBox.YMin < min(ys)-allowance or
            edge.BoundBox.YMax > max(ys)+allowance):
        # Approximating smooths noisy perimeter discretization while avoiding
        # interpolant ringing around a locally clipped contact.
        try:
            approx=Part.BSplineCurve()
            approx.approximate(Points=points, DegMax=3, Tolerance=.045)
            alternate=approx.toShape()
            if (alternate.BoundBox.YMin >= min(ys)-allowance and
                    alternate.BoundBox.YMax <= max(ys)+allowance):
                return alternate
        except Exception:
            pass
        # A straight polyline is an exceptional safety fallback, not the
        # default bridge geometry. Its occurrence is reported for diagnosis.
        try:
            App.Console.PrintWarning('[RotorForge TPU cage] bridge curve exceeded bounded envelope; using polygon fallback\n')
        except Exception:
            pass
        return Part.makePolygon(points)
    return edge


def _lower_bridge(p, mounts, bottom_front, top_front):
    """An integrated, plate-traced lower bridge with no exposed side tongues.

    Only the central opening needs a bridge. Extending the bridge across the
    full *outer* width of both cheeks created coincident/overlapping skins near
    the front corners, which appeared as thin spikes after union. The bridge
    now penetrates each inner cheek by a small controlled amount. The entire
    lower contact follows the actual bottom plate, and the raised front is
    bounded by its adjoining side wall rather than projecting past it.
    """
    left, right = mounts
    z0, z1 = left['z0'], left['z1']
    h = float(p.CameraTPUFrontBridgeHeight)
    if not 0 < h < z1-z0-1.:
        raise ValueError('Lower TPU cage floor is too tall for camera clearance.')
    # All isolation modes use the same straight camera-facing wall scheme.
    from .flex import tpu_hard_bearing, camera_inner
    inner_x = camera_inner(p)  # full-height cheek does not move for isolation
    inner_left, inner_right = -inner_x, inner_x

    # The extra 0.8 mm goes *inside* the side walls, NOT to their exterior.
    # It is enough to produce volumetric union without making any additional
    # exposed front/side lobes. Keep both ends within their structural cheeks.
    overlap=.8
    x0=max(left['plate_x'][0]+.3, inner_left-overlap)
    x1=min(right['plate_x'][1]-.3, inner_right+overlap)
    if not x0 < inner_left < inner_right < x1:
        raise ValueError('TPU lower bridge cannot overlap both cage side walls.')

    # The blend is a transition *length*, not an allowance to push material
    # rearward beyond the two cheek solids. The old `centre_rear-depth`
    # created a backward-pointing tongue at each junction.
    blend = max(0., min(10., float(getattr(p,'CameraTPUFrontBridgeBlend',3.0))))
    transition = max(1.5, blend * 1.5)
    centre_rear = bottom_front(0.)-float(p.CameraTPUFrontBridgeRearReach)

    def smoothstep(v):
        t=max(0.,min(1.,v))
        return t*t*(3.-2.*t)

    def side_front_at(x,z):
        t=max(0.,min(1.,(z-z0)/(z1-z0)))
        # The two-section structural wall has a linear front transition
        # across height for every isolation mode (no soft-only ease bands).
        return (1.-t)*bottom_front(x)+t*top_front(x)

    # The two side cheeks have straight rear termination planes. At the
    # embedded bridge ends, the bridge must stop inside those planes; a
    # bridge-end setback cannot become an exposed horizontal tongue.
    def cheek_rear(mount):
        xc=sum(mount['plate_x'])*.5
        return bottom_front(xc)-float(p.CameraTPUBottomRearReach)
    left_rear, right_rear = cheek_rear(left), cheek_rear(right)

    def perimeter(z):
        upper=z>z0+1.e-7
        rear=[];front=[]
        # The raised top edge is the bottom-plate outline except in the
        # controlled blending strips next to each cheek. Use ONE smoothly
        # tapered correction per side, not a pointwise min() cut: min() used
        # to form sharp spikes where its active branch switched.
        def edge_clearance(x):
            return max(0.,bottom_front(x)-side_front_at(x,z)+.06)
        left_delta=right_delta=0.
        if upper:
            left_delta=max(edge_clearance(x0+(inner_left-x0)*j/4.) for j in range(5))
            right_delta=max(edge_clearance(inner_right+(x1-inner_right)*j/4.) for j in range(5))
        for i in range(49):
            x=x0+(x1-x0)*i/48.
            nose=bottom_front(x)
            if upper:
                wl=smoothstep((inner_left+transition-x)/transition)
                wr=smoothstep((x-inner_right+transition)/transition)
                nose -= max(left_delta*wl,right_delta*wr)

            # Blend the rear termination *toward* a point fully inside the
            # side wall at each end. This preserves the requested center
            # rear reach and eliminates exposed rear fins. The parameter
            # controls how gradually the bridge merges into either cheek.
            rear_y=centre_rear
            if blend>1.e-7:
                wl=smoothstep((inner_left+transition-x)/transition)
                wr=smoothstep((x-inner_right+transition)/transition)
                rear_y += max(0.,left_rear+.25-centre_rear)*wl
                rear_y += max(0.,right_rear+.25-centre_rear)*wr
            else:
                # Even with blend=0, the actual 0.8 mm overlap must be
                # inside the side cheeks, not project behind them.
                if x<inner_left:
                    rear_y=max(rear_y,left_rear+.25)
                if x>inner_right:
                    rear_y=max(rear_y,right_rear+.25)
            if nose-rear_y < .65:
                raise ValueError('Lower TPU bridge has insufficient front-to-rear material at its side-wall connection.')
            rear.append(App.Vector(x,rear_y,z))
            front.append(App.Vector(x,nose,z))
        return Part.Wire([_bounded_bridge_curve(rear),
                          Part.makeLine(rear[-1],front[-1]),
                          _bounded_bridge_curve(list(reversed(front))),
                          Part.makeLine(front[0],rear[0])])

    bottom, top=perimeter(z0),perimeter(z0+h)
    if not all(w.isValid() and w.isClosed() for w in (bottom,top)):
        raise ValueError('The lower TPU cage bridge has an invalid perimeter.')
    shape=Part.makeLoft([bottom,top],True,True)
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1:
        raise ValueError('The lower TPU cage bridge could not form one valid solid.')
    return shape


def tpu_insert_pocket_depths(p,wall_thickness):
    """Neck and retention chamber depths, preserving a 1.2 mm outside skin."""
    from .camera_interface import lip_sides
    outside=lip_sides(p)[1]
    available=max(0.,wall_thickness-1.2)
    lip=min(.8,available*.45) if outside else 0.
    return available-lip,lip


def _attach_insert_bosses(wall, bosses, pockets, p, label):
    """Fuse only boss material that genuinely needs adding to the base loft.

    A profiled cage wall can already contain the entire socket cylinder. In
    that case *no Boolean union is required*: the later pocket subtraction
    creates the exact same functional mounting recess. Trying to fuse a
    redundant cylinder into an OCC loft caused an invalid split BRep on some
    designs. Partially exposed sockets still require a VALID, single-solid
    union and are never silently discarded.
    """
    from .shape_cleanup import guard_refine
    joined=wall
    for index,(boss,pocket) in enumerate(zip(bosses,pockets)):
        common=joined.common(boss)
        overlap=0. if common.isNull() else common.Volume
        if overlap<=1.e-5:
            distance,_,_=joined.distToShape(boss)
            raise ValueError(
                '%s TPU mounting socket %d has no structural overlap '
                '(gap %.3f mm; overlap %.5f mm3). Check plate support '
                'and the contact rear reach.' % (label,index+1,distance,overlap))
        # Redundant additions should not be passed to OCC: they often return
        # a compound with internal splitter faces instead of a single solid.
        remaining=boss.cut(joined)
        exposed=0. if remaining.isNull() else remaining.Volume
        if exposed <= max(1.e-4,boss.Volume*1.e-5):
            try: App.Console.PrintMessage('[RotorForge TPU cage] %s socket %d already inside structural loft\n' % (label,index+1))
            except Exception: pass
            continue
        # An exposed *outer* cylindrical sliver is not evidence of a
        # missing socket. The functional socket is the blind pocket and the
        # load-bearing TPU around it, not the redundant helper cylinder.
        # Loft/surface tolerances can leave sub-mm3 slivers and OCC cannot
        # reliably fuse those near-tangent pieces. Only skip the redundant
        # union when a continuous 1.2 mm minimum material envelope around
        # the full heat-insert pocket is ALREADY in the wall. A larger gap or
        # missing structural material must still fail explicitly.
        if exposed <= min(2.0, boss.Volume * .02):
            try:
                required_radius = float(p.CameraTPUScrewBore)/2. + 1.20
                bb = boss.BoundBox
                # The pocket has the exact insert depth; require material
                # around it through the full boss height (more conservative).
                clearance_core = Part.makeCylinder(
                    required_radius, bb.ZLength,
                    App.Vector((bb.XMin+bb.XMax)/2.,
                               (bb.YMin+bb.YMax)/2., bb.ZMin))
                missing = clearance_core.cut(joined)
                miss_volume = 0. if missing.isNull() else missing.Volume
                if miss_volume <= 1.e-4:
                    App.Console.PrintMessage(
                        '[RotorForge TPU cage] %s socket %d: %.4f mm3 '
                        'redundant outer sliver; existing loft fully '
                        'supports insert pocket with >=1.2 mm TPU. '
                        'No fragile tangent fusion needed.\n'
                        % (label,index+1,exposed))
                    continue
            except Exception:
                # Failure to *prove* the pocket support must not silently
                # drop the cylinder or weaken a printed mounting point.
                pass
        # Try raw and refined Boolean results and both operand orders. This
        # does not permit invalid topology or disconnected printed solids.
        attempts=(lambda: joined.fuse(boss),
                  lambda: boss.fuse(joined),
                  lambda: joined.multiFuse([boss]))
        for fuse in attempts:
            try:
                raw=fuse()
                if not raw.isNull() and raw.isValid() and len(raw.Solids)==1:
                    joined=guard_refine(raw)
                    break
                cleaned=guard_refine(raw)
                if not cleaned.isNull() and cleaned.isValid() and len(cleaned.Solids)==1:
                    joined=cleaned
                    break
            except Exception:
                pass
        else:
            raise ValueError(
                '%s TPU mounting socket %d has %.3f mm3 of wall overlap '
                'and %.3f mm3 outside the loft, but OCC could not fuse the '
                'required extra material into a valid solid. '
                'The socket has not been omitted.'
                % (label,index+1,overlap,exposed))
    return joined

def make_tpu_cage(p,role,inputs):
    from .camera_cages import joined_cage
    from .protection_geometry import outer_face
    if joined_cage(p) and role=='CameraMountRight':return Part.Shape()
    bottom_solid=inputs['BottomPlate']
    top_solid=inputs['TopPlate']
    started=time.monotonic()
    bottom=outer_face(bottom_solid)
    top=outer_face(top_solid)
    bottom_front=_front_sampler(bottom)
    top_front=_front_sampler(top)
    _stage('plate outlines sampled',started)
    # Verify the REAL generated carbon perimeter in FreeCAD. Portable profiles
    # cannot know about every custom fillet or outline cutout; this catches a
    # hole that would leave less than 2 mm of carbon on the manufactured part.
    from .tpu_mount_layout import carbon_rim_centres
    for plate_name,face in (('BottomPlate',bottom),('TopPlate',top)):
        # The perimeter here contains true OCC circle arcs and Beziers. A
        # polygon discretization can underestimate a 3.60 mm circular rim
        # even when the true CAD geometry is exactly 3.60 mm away. Query the
        # exact wire instead; signed distance is negative if the centre lies
        # outside the finished plate.
        for (x,y),needed in carbon_rim_centres(p,plate_name):
            centre=App.Vector(x,y,0)
            clearance=Part.Vertex(centre).distToShape(face.OuterWire)[0]
            if not face.isInside(centre,1.e-6,False):
                clearance=-clearance
            if clearance<needed-1.e-4:
                raise ValueError('%s plate TPU M3 hole at X %.2f / Y %.2f mm has %.2f mm '
                                 'to the finished outside edge; requires %.2f mm measured '
                                 'from centre (M3 radius plus 2 mm carbon). Change the '
                                 'mounting offsets or expand the carbon support.'
                                 % (plate_name.replace('Plate','').title(),x,y,clearance,needed))
    # Mounting positions are computed from finished carbon outlines, while
    # the TPU cage's front/rear contours remain immutable. Check that every
    # insert socket actually fits the selected contact reach; do not warp the
    # cage rear edge to hide a misplaced mounting point.
    mounts=[_mount_with_socket_width(p,m) for m in camera_mounts(p)]
    socket_radius=float(p.CameraTPUScrewBore)/2+float(p.CameraTPUBossWall)+.20
    for m in mounts:
        x=boss_x(p,-1 if m['plate_x'][1]<0 else 1)
        for side,front_sampler,reach,ys in (
            ('bottom',bottom_front,p.CameraTPUBottomRearReach,m['tabs_y']),
            ('top',top_front,p.CameraTPUTopRearReach,m['top_tabs_y'])):
            # The plate silhouette remains fixed; the rear edge is straight.
            # A socket outside this band is a dimensional mismatch, not a
            # reason to add an unrelated curved rear lobe.
            centre_x=sum(m['plate_x'])/2
            rear=front_sampler(centre_x)-float(reach)
            front=front_sampler(x)
            if min(ys)-socket_radius<rear+.15:
                raise ValueError('%s %s TPU mounting socket needs %.2f mm more rear contact reach. '
                                 'Increase that plate contact reach or move the mounting offset forward.'
                                 % (m['role'],side,rear+.15-(min(ys)-socket_radius)))
            if max(ys)+socket_radius>front+.05:
                raise ValueError('%s %s TPU mounting socket extends beyond the carbon front contour. '
                                 'Move the front mounting offset rearward.' % (m['role'],side))
    # The camera-facing side is defined by the rigid plate-mounted cage,
    # independently of the insert choice. Soft parts must fit into that space.
    # The soft camera interface is made independently of the structural cage.
    # Do not refuse a pad merely because its thickness exceeds the old hard-
    # mount clearance: camera_inner() reserves the larger of these spaces.
    selected=mounts  # TPU is always one complete cage
    sides=[];pockets=[];openings=[]
    for mount in selected:
        # Always use the smooth ruled hard-mount cheek, including in both
        # soft camera modes. Only its inner X clearance can differ.
        wall=_hard_wall_sections(p,mount,bottom_front,top_front)
        _stage('side wall created',started)
        bosses,holes=_bosses_and_openings(p,mount)
        for ys, front_at in ((mount['tabs_y'],bottom_front),
                             (mount['top_tabs_y'],top_front)):
            boss_radius=float(p.CameraTPUScrewBore)/2+float(p.CameraTPUBossWall)
            cx=boss_x(p,-1 if mount['plate_x'][0]<0 else 1)
            nose=front_at(cx)
            if max(ys)+boss_radius>nose+0.05:
                raise ValueError('%s TPU mounting boss lies beyond the finished plate front outline by %.2f mm. Move the front mounting offset rearward.' % (mount['role'],max(ys)+boss_radius-nose))
        # Bosses are only structural attachment details on the freshly made
        # cage. The old camera_bracket solid is never built or fused.
        side=_attach_insert_bosses(wall,bosses,holes,p,mount['role'])
        # The same continuous wall is used for all TPU camera attachment modes.
        sides.append(side)
        pockets.extend((mount["role"], hole) for hole in holes)
    sides.append(_lower_bridge(p,mounts,bottom_front,top_front))
    # Preserve the independent original solids for collision cross-validation.
    # A union followed by several OCC cuts/refines can occasionally report a
    # nonsensical common volume even though its three constituent solids never
    # touched the camera. Subtraction cannot add material: comparing against
    # the original solids is a conservative, geometry-based cross-check.
    original_cage_components=tuple(sides)
    _stage('lower floor created',started)
    joined=sides[0].multiFuse(sides[1:]).removeSplitter() if len(sides)>1 else sides[0]
    if joined.isNull() or not joined.isValid() or len(joined.Solids)!=1:
        raise ValueError('The one-piece TPU cage did not form a continuous solid. Check rear reach, floor height and plate outline.')
    _stage('cage fused',started)
    b=joined.BoundBox
    for mount in selected:
        # Compression pads sit against a continuous straight inner wall.
        # Captured inserts replace only their local window cross-section;
        # optional recessed exterior flanges cut shallow matching seats.
        xmin,xmax=mount['plate_x']
        left=xmax<0
        thickness=xmax-xmin
        start=xmin-.15
        through=thickness+.30
        if p.FlexCameraMode=='Hard mount':
            # The new uninterrupted inner surface extends toward the camera
            # in the centre. M2 holes must cut all of that material as well.
            from .flex import tpu_hard_bearing
            camera_x,_=tpu_hard_bearing(p)
            if left:
                through=max(through, camera_x-start+.30)
            else:
                start=min(start,camera_x-.30)
                through=xmax+.30-start
        if p.FlexCameraMode=='Compression pads':
            # The cage retains its hard-mount inner face everywhere except
            # for real pockets behind the two soft contact interfaces.
            # These seats match the axial pad bounds (including preload),
            # leaving at least 1.2 mm of outer structural TPU.
            from .tpu_isolation_layout import compression_pad_x_span,tpu_isolator_datum
            from .cage_extensions import split_o4,o4_tracks,track_solid
            from .flex import insert_rect
            sign=-1 if left else 1
            pa,pb=compression_pad_x_span(p,mount,sign)
            if split_o4(p):
                for track in o4_tracks(mount):
                    openings.append((mount['role'],'O4 compression-pad recess',
                                     track_solid(track,p.O4PadDiameter+.20,
                                                 pa-.05,pb-pa+.10)))
            else:
                from .flex_geometry import interface_blank
                cy,cz,_,_=insert_rect(p)
                datum_y,datum_z=tpu_isolator_datum(p,mount)
                cutter=interface_blank(p,pa-.05,pb-pa+.10,
                                       p.FlexPadWidth,p.FlexPadHeight,.10)
                cutter.translate(App.Vector(0,datum_y-cy,datum_z-cz))
                openings.append((mount['role'],'compression-pad recessed seat',cutter))
        if p.FlexCameraMode=='Captured inserts':
            from .tpu_captured_layout import flush_flange_cutter_span
            from .cage_extensions import split_o4,o4_tracks,track_solid
            sign=-1 if left else 1
            recess=flush_flange_cutter_span(p,mount,sign)
            if split_o4(p):
                for track in o4_tracks(mount):
                    # DJI O4 has TWO independent cassettes per side; never
                    # substitute a single large rectangular through-window.
                    openings.append((mount['role'],'O4 captured insert through-seat',
                                     track_solid(track,p.O4InsertDiameter,
                                                 xmin-.65,thickness+1.30)))
                    if recess:
                        a,b=recess
                        openings.append((mount['role'],'O4 flush outside lip seat',
                                         track_solid(track,p.O4InsertDiameter+2*(p.FlexInsertLip+.08),a,b-a)))
            else:
                from .flex_geometry import interface_blank
                from .tpu_isolation_layout import tpu_isolator_datum
                from .flex import insert_rect
                cy,cz,_,_=insert_rect(p)
                datum_y,datum_z=tpu_isolator_datum(p,mount)
                def located_blank(x,length,extra):
                    cutter=interface_blank(p,x,length,
                                           p.FlexInsertWidth,p.FlexInsertHeight,extra)
                    cutter.translate(App.Vector(0,datum_y-cy,datum_z-cz))
                    return cutter
                openings.append((mount['role'],'captured insert full-wall seat',
                                 located_blank(xmin-.65,thickness+1.30,0.0)))
                if recess:
                    a,b=recess
                    openings.append((mount['role'],'flush outside lip seat',
                                     located_blank(a,b-a,p.FlexInsertLip+.08)))
        # Compression pads are independent soft components against the flat
        # inside of the cage. No full-thickness pocket or side-plate cut.
        # All isolation styles retain camera M2 screw/tilt travel access.
        openings.extend((mount['role'], 'camera screw', Part.makeCylinder(
            p.CameraSideHoleDiameter/2, through,
            App.Vector(start,y,z), App.Vector(1,0,0)))
            for y,z in mount['side_holes'])
        openings.extend((mount['role'], 'camera tilt slot', arc_slot(a,start,through))
            for a in mount['side_arcs'])
    # Apply the different cutter families separately. A single compound of
    # overlapping camera-envelope shapes can produce ambiguous OCC splits and
    # makes it impossible to identify where the load-bearing lower bridge fails.
    def boxes_overlap(a,b):
        return not (a.XMax < b.XMin or b.XMax < a.XMin or
                    a.YMax < b.YMin or b.YMax < a.YMin or
                    a.ZMax < b.ZMin or b.ZMax < a.ZMin)

    def inspect(stage, shape):
        try:
            solids=list(shape.Solids) if not shape.isNull() else []
            volumes=sorted((round(v.Volume,3) for v in solids),reverse=True)
            detail='count=%d volumes=%s valid=%s' % (len(solids), volumes[:8],shape.isValid() if solids else False)
            App.Console.PrintMessage('[RotorForge TPU cage] %s: %s\n' % (stage,detail))
        except Exception as exc:
            App.Console.PrintWarning('[RotorForge TPU cage] diagnostic unavailable at %s: %s\n' %(stage,exc))
        _stage(stage,started)

    inspect('before openings',joined)
    # Do NOT put all heat-insert pockets and camera slots in a single OCC
    # compound cutter. With the curved loft this can return a null shape even
    # though both the original cage and every individual hole are valid.
    # Process each real intersection separately, and inspect the *raw* result
    # before optional refinement so OCC failures cannot be silently hidden.
    cutters = ([(role, 'M3 heat insert pocket', hole) for role,hole in pockets]
               + openings)
    for i,(role, kind, cutter) in enumerate(cutters, 1):
        if cutter.isNull() or not cutter.isValid() or len(cutter.Solids)!=1:
            raise ValueError('%s %s %d is not a valid cutting solid.'
                             % (role,kind,i))
        if not boxes_overlap(joined.BoundBox, cutter.BoundBox):
            continue
        try:
            intersection = joined.common(cutter)
            if intersection.isNull() or intersection.Volume < 1.e-7:
                continue
            candidate = joined.cut(cutter)
        except Exception as exc:
            raise ValueError('%s %s %d Boolean cut failed: %s'
                             % (role,kind,i,exc)) from exc
        if candidate.isNull() or not candidate.isValid() or len(candidate.Solids)!=1:
            # Retain the previous valid solid in this diagnostic rather than
            # replacing it with a null/compound shape. A real disconnection
            # is an error; do not silently discard fragments or a hole.
            try:
                count=len(candidate.Solids) if not candidate.isNull() else 0
                volume=candidate.Volume if not candidate.isNull() else 0.
            except Exception:
                count,volume=-1,0.
            raise ValueError(
                '%s %s %d invalidates the TPU cage (solid count %d, '
                'remaining volume %.3f mm3). See Report view.'
                % (role,kind,i,count,volume))
        # Refining a heavily curved loft occasionally fails even after a
        # successful cut. Only adopt refinement when it remains one solid.
        try:
            refined=candidate.removeSplitter()
            if not refined.isNull() and refined.isValid() and len(refined.Solids)==1:
                candidate=refined
        except Exception:
            pass
        joined=candidate
        try:
            App.Console.PrintMessage(
                '[RotorForge TPU cage] %s %s %d cut: remaining %.3f mm3\n'
                % (role,kind,i,joined.Volume))
        except Exception:
            pass
    inspect('after screw and isolation openings',joined)

    # Validate the camera at its CURRENT installation tilt as a hard safety
    # condition. A variable-tilt range represents possible future angles:
    # report interference there as a clear warning, not as an unconditional
    # refusal to manufacture a cage at the presently selected safe angle.
    # In particular, an unused 0-degree position must not prevent generating
    # a camera mounted at 25 degrees. Never silently accept overlap at the
    # current angle, and never use the camera housing as a cutting tool.
    selected_angle=float(p.CameraTilt)
    angles=[selected_angle]+[a for a in sorted(set(camera_angles(p)))
                             if abs(float(a)-selected_angle)>1.e-6]
    # Broad phase before native BRep creation: the final cage is a subset of
    # the three original walls/bridge, because subsequent features only CUT
    # material. If an enclosing rotated box misses ALL three, an exact camera
    # intersection is mathematically impossible at this angle. This is not a
    # replacement for the existing exact collision checks on plausible hits.
    from .geometry import _camera_envelope_local
    from .fpv import camera_body_centre
    from .camera_clearance_bounds import (as_tuple, rotated_camera_aabb,
                                          aabbs_may_overlap)
    local_camera=_camera_envelope_local(p)
    local_bounds=as_tuple(local_camera.BoundBox)
    component_bounds=tuple(as_tuple(component.BoundBox)
                           for component in original_cage_components)
    tested=0
    broad_rejected=0
    warned=[]
    camera_check_start=time.monotonic()
    for angle in angles:
        conservative=rotated_camera_aabb(local_bounds,angle,
                                         camera_body_centre(p,angle))
        if not any(aabbs_may_overlap(conservative,b)
                   for b in component_bounds):
            broad_rejected+=1
            continue
        envelope=camera_envelope(p,angle,_prototype=local_camera)
        tested+=1
        if envelope is None or envelope.isNull():continue
        if not boxes_overlap(joined.BoundBox,envelope.BoundBox):continue
        intersection=joined.common(envelope)
        if intersection.isNull() or intersection.Volume<=1.e-7:continue
        # OCC can return a nonempty, small-volume overlap with a bounding
        # box larger than the physical camera. This is topologically
        # impossible for a genuine intersection. Check the operands before
        # acting on the reported volume, including all original pieces.
        original_hits=[]
        impossible=[]
        names=('left side wall','right side wall','lower front bridge')
        for name,component in zip(names,original_cage_components):
            if not boxes_overlap(component.BoundBox,envelope.BoundBox):
                continue
            try:
                hit=component.common(envelope)
                volume=0. if hit.isNull() else float(hit.Volume)
            except Exception as exc:
                raise ValueError('Cannot verify camera clearance against %s: %s' % (name,exc)) from exc
            if volume>1.e-5:
                if _intersection_inside_operands(hit,component,envelope):
                    original_hits.append((name,volume))
                else:
                    impossible.append((name,volume))
        if not _intersection_inside_operands(intersection,joined,envelope):
            # Only ignore an impossible combined BRep if the independent
            # structural wall/floor checks also fail to prove a real hit.
            if not original_hits:
                App.Console.PrintWarning(
                    '[RotorForge TPU cage] Invalid OCC common() at %.1f deg: '
                    'intersection bounds %s are not within camera bounds %s. '
                    'Independent structural pieces have no geometrically '
                    'consistent overlap (invalid hits: %s). Ignoring false '
                    'combined collision; inspect assembly before flight.\n'
                    % (angle,str(intersection.BoundBox),str(envelope.BoundBox),str(impossible)))
                continue
            # A credible component overlap is sufficient to stop building.
        elif not original_hits:
            App.Console.PrintWarning(
                '[RotorForge TPU cage] Combined intersection %.3f mm3 at '
                '%.1f deg has no independently verified original wall/floor '
                'intersection; ignoring apparent OCC Boolean artifact.\n'
                % (intersection.Volume,angle))
            continue
        App.Console.PrintMessage(
            '[RotorForge TPU cage] Camera overlap at %.1f deg by original '
            'component: %s\n' % (angle,', '.join('%s %.3f mm3' % hit for hit in original_hits)))
        bb=intersection.BoundBox
        detail=('%.1f deg: %.3f mm3, X=[%.2f,%.2f], '
                'Y=[%.2f,%.2f], Z=[%.2f,%.2f] mm'
                % (angle,intersection.Volume,bb.XMin,bb.XMax,
                   bb.YMin,bb.YMax,bb.ZMin,bb.ZMax))
        if abs(float(angle)-selected_angle)<1.e-6:
            raise ValueError('At the selected camera tilt, the camera housing '
                             'intersects the structural TPU cage (%s). '
                             'Adjust the camera position, cage inner clearance '
                             'or lower front bridge.' % detail)
        warned.append(detail)
    if warned:
        # Deliberately limit verbose warnings without hiding the problematic
        # range. These tilt values may NOT be safely usable after printing.
        App.Console.PrintWarning(
            '[RotorForge TPU cage] Selected tilt %.1f deg clears the cage, '
            'but other adjustable tilt positions collide. The full requested '
            'tilt range is NOT collision-free; do not use these angles until '
            'the geometry is revised. First collision: %s; %d sampled angles '
            'intersect.\n' % (selected_angle,warned[0],len(warned)))
    _stage('camera clearance checks complete (%d angles: %d broad-phase skips, %d exact BRep probes; %.2fs checks)' % (
        len(angles), broad_rejected, tested, time.monotonic()-camera_check_start),started)

    # Plate-to-cage contact faces are deliberately coincident; cutting them
    # merely to remove zero-volume contact can fragment the BRep. Only do a
    # carbon-plate Boolean if there is genuine three-dimensional overlap.
    for plate_name,plate in (('bottom',bottom_solid),('top',top_solid)):
        if plate.isNull() or not boxes_overlap(joined.BoundBox,plate.BoundBox):continue
        overlap=joined.common(plate)
        if overlap.isNull() or overlap.Volume<=1e-7:
            _stage('%s plate cut skipped (contact only)' % plate_name,started)
            continue
        joined=joined.cut(plate).removeSplitter()
        inspect('after %s plate clearance' % plate_name,joined)
        if joined.isNull() or not joined.isValid() or len(joined.Solids)!=1:
            raise ValueError('The %s carbon plate cuts the TPU cage into %d disconnected solids. Inspect plate-contact height and outline in Report view.' % (plate_name,len(joined.Solids)))
    joined=joined.removeSplitter()
    inspect('final cage validation',joined)
    if joined.isNull() or not joined.isValid() or len(joined.Solids)!=1:
        raise ValueError('The TPU cage has disconnected material after clearance operations; see Report view for the failing stage.')
    return joined
