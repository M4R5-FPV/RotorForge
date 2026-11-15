"""Integrated TPU bumper with one loft from the sole to the camera cage.

The normal slide-on bumper is a separate, unmodified construction path.  This
variant builds the rounded nose and both rising shoulders as one continuous
exterior, then subtracts the camera aperture and carbon mounting cavity.
There is no separately fused mounting shoe or pair of added camera arches.
"""
import math

import FreeCAD as App
import Part

from .bumper_transition import _at_height, _sculpted_outside, _front_edge_function, _smoothstep
from .front_bumper import camera_cover_profiles
from .shape_cleanup import guard_refine


def _fairing_wire(half, rear, front, z, radius, center=0., top_edge=None, top_mix=0., front_projection=0.):
    """A rounded nose section whose sides run tangent into the *same* front.

    Every station has seven matching edges.  Two cubic Beziers make the broad
    rounded tip without introducing a flat rectangular bar below the cage.
    The continuous shell is lofted from the sole all the way to the crown.
    """
    if half < 3. or front-rear < 2.:
        raise ValueError('Integrated bumper has no room for a sculpted shell.')
    rb = min(1.35, half*.10, (front-rear)*.25)
    # Nose-to-side rounding: a tangent starts along the side wall and
    # becomes horizontal at the centre of the nose.
    rt = min(radius*1.2, (front-rear)*.66)
    side_front = front-rt
    q = 1./math.sqrt(2.)
    def v(x,y,front_factor=0.):
        if top_edge is not None and top_mix>0 and front_factor>0:
            boundary=top_edge(x+center)
            if boundary is not None:
                # Allow a user-selected exterior brow projection beyond the
                # nominal top-plate contour. The *inside* camera cut stays fixed.
                target=max(rear+2.1,boundary-.18)+front_projection
                y+=top_mix*front_factor*(target-front)
        return App.Vector(x+center,y,z)
    def line(a,b): return Part.makeLine(v(*a),v(*b))
    def arc(a,b,c):return Part.Arc(v(*a),v(*b),v(*c)).toShape()
    def bezier(pts,factors):
        curve=Part.BezierCurve()
        curve.setPoles([v(x,y,k) for (x,y),k in zip(pts,factors)])
        return curve.toShape()
    return Part.Wire([
        line((-half+rb,rear),(half-rb,rear)),
        arc((half-rb,rear),(half-rb+rb*q,rear+rb-rb*q),(half,rear+rb)),
        line((half,rear+rb),(half,side_front)),
        bezier([(half,side_front),(half,side_front+.73*rt),
                (.57*half,front),(0.,front)], [0.,.5,1.,1.]),
        bezier([(0.,front),(-.57*half,front),
                (-half,side_front+.73*rt),(-half,side_front)], [1.,1.,.5,0.]),
        line((-half,side_front),(-half,rear+rb)),
        arc((-half,rear+rb),(-half+rb-rb*q,rear+rb-rb*q),(-half+rb,rear)),
    ])


def _camera_aperture(half, zbottom, ztop, ystart, depth, center=0., reach=0.):
    """Round-bottom, open-top lens space cut completely through the front.

    An elliptic lower boundary produces the two broad, continuous shoulders
    rising from the same nose.  There is no narrow rectangular root or step.
    """
    if ztop-zbottom < 2.0 or half < 2.0:
        raise ValueError('Integrated camera aperture does not have enough room.')
    # Inward reach must change the ACTUAL camera-window footprint, not its
    # height.  0 retains the previous full-radius U (the fullest shoulders).
    # 1..20 mm selects the real inward projection on EACH side of the lower
    # opening: short radiused corners and a flat centre between them.
    # The high opening width is unchanged so the camera still has clearance.
    # Even with a 1 mm requested inward reach, retain a structural TPU
    # shoulder next to the open camera aperture. Reach changes the round-over
    # without allowing a nearly zero-width foot in the bottom of the opening.
    structural_radius=max(2.25, min(3.2, half*.35))
    # Map the user's requested reach to an *additional* sweep past the
    # structural minimum. Every millimetre from 1 upwards changes the actual
    # root curvature (unlike v0.91.35, where 1 and 2 could collapse together).
    r=half if reach<=1.e-8 else min(half,max(structural_radius+.3*max(0.,reach-1.),reach))
    # For a shallow/partial-height cage the arc must remain below the crown.
    r=min(r,ztop-zbottom-.65)
    pole=ztop+2.
    y=ystart
    q=1./math.sqrt(2.)
    def v(x,z): return App.Vector(x+center,y,z)
    if r>=half-1.e-7:
        # Keep the original analytic semicircle and its single edge at the
        # maximum/full setting: this avoids a centre seam in the loft cutter.
        edges=[
            Part.makeLine(v(-half,pole),v(-half,zbottom+half)),
            Part.Arc(v(-half,zbottom+half),v(0,zbottom),
                     v(half,zbottom+half)).toShape(),
            Part.makeLine(v(half,zbottom+half),v(half,pole)),
            Part.makeLine(v(half,pole),v(-half,pole)),
        ]
    else:
        left=(-half+r,zbottom)
        right=(half-r,zbottom)
        edges=[
            Part.makeLine(v(-half,pole),v(-half,zbottom+r)),
            Part.Arc(v(-half,zbottom+r),
                     v(-half+r-r*q,zbottom+r-r*q),v(*left)).toShape(),
            Part.makeLine(v(*left),v(*right)),
            Part.Arc(v(*right),v(half-r+r*q,zbottom+r-r*q),
                     v(half,zbottom+r)).toShape(),
            Part.makeLine(v(half,zbottom+r),v(half,pole)),
            Part.makeLine(v(half,pole),v(-half,pole)),
        ]
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(0,depth,0))


def _profile_front_at(profile, z):
    """Forward-facing Y boundary of the carbon camera-side plate.

    The *back* of the carbon side plate can extend 15-25 mm behind the camera
    mount. The integrated bumper grips only the front camera-cage edge; using
    the rearmost edge here created broad solid panels in v0.91.35.
    """
    hits=[]
    for (ya,za),(yb,zb) in zip(profile,profile[1:]+profile[:1]):
        if abs(za-zb)<1.e-8:
            if abs(z-za)<1.e-7:hits.extend((ya,yb))
        elif min(za,zb)-1.e-8<=z<=max(za,zb)+1.e-8:
            t=max(0.,min(1.,(z-za)/(zb-za)))
            hits.append(ya+(yb-ya)*t)
    if not hits:
        raise ValueError('Camera side-plate profile does not cover bumper height.')
    return max(hits)


def _sculpted_shell(p, rails, outer, upper, top_outline):
    from .parameters import plate_levels
    if len(rails)!=2:
        raise ValueError('Integrated camera shell requires both FPV side plates.')
    negative,positive=sorted(rails,key=lambda r:r['xmin'])
    # Both sides should be mirrored about the actual camera centre, allowing
    # small offsets without requiring the rest of the frame to be symmetric.
    cx=(negative['xmin']+negative['width']+positive['xmin'])/2.
    left=negative['xmin']
    right=positive['xmin']+positive['width']
    span=max(abs(left-cx),abs(right-cx))
    inner_half=min(cx-(negative['xmin']+negative['width']),positive['xmin']-cx)
    if inner_half<2.:
        raise ValueError('Camera cage is too narrow for the integrated front opening.')
    top=min(plate_levels(p)['top_z'],max(yz[1] for yz in negative['points']))
    if p.FlexBumperCameraHeight:
        top=min(top,p.BottomThickness+p.FlexBumperCameraHeight)
    # Start the exterior at the actual sole, not atop a second, separately
    # fused mounting shoe.  Its lower perimeter is the same continuous shell.
    from .parameters import plate_levels
    low=-p.FlexBumperFit-p.FlexBumperSole
    if top-upper<4.:
        raise ValueError('Integrated front bumper needs at least 4 mm above its mounting lip.')
    full_height=(p.FlexBumperCameraHeight<=1.e-8)
    nose_half=min(abs(outer.BoundBox.XMin-cx),abs(outer.BoundBox.XMax-cx))-.15
    nose_half=max(span+.15,nose_half)
    foot_rear=outer.BoundBox.YMin+.15
    foot_front=outer.BoundBox.YMax-.15
    ins=negative['points'][:len(negative['points'])//2]
    out=tuple(reversed(negative['points'][len(negative['points'])//2:]))
    top_edge=_front_edge_function(top_outline) if full_height and top_outline else None
    # Below the retaining lip the perimeter stays constant: there is no
    # separate horizontal band or added riser footprint to form a step.
    heights={low,upper,top}
    for i in range(1,8):heights.add(low+(upper-low)*i/8.)
    for i in range(1,26):heights.add(upper+(top-upper)*i/26.)
    for _,z in ins:
        if upper<z<top:heights.add(z)
    # Preserve the successful sculpted outer shape of v0.91.34.  The previous
    # revision instead tracked the REARMOST corner of the entire carbon side
    # plate (47.25 mm on Analog Buster, versus the front rail at 67.25 mm).
    # That turned the rounded cage supports into huge flat panels.
    #
    # The actual TPU camera grip is a local FRONT strip.  Give that strip
    # enough depth for its selected grip without covering the entire plate.
    from .fpv import camera_mounts
    wall_profile=camera_mounts(p)[0]['wall_profile']
    base_top_rear=(_at_height(ins,top)-.60-
                   .35*max(0.,min(8.,p.FlexBumperCameraGripDepth)))
    front_y=_profile_front_at(wall_profile,top)
    required_rear=front_y-max(2.0,p.FlexBumperCameraGripDepth)-p.FlexBumperFit-.35
    # At most 2.5 mm extra behind the original contour; preserve the curved
    # side silhouette rather than allowing an unbounded plate-length sweep.
    top_rear=base_top_rear-min(2.5,max(0.,base_top_rear-required_rear))
    stations=[]
    for z in sorted(heights):
        u=max(0.,min(1.,(z-upper)/(top-upper)))
        taper=_smoothstep(min(1.,u/.90))
        half=nose_half+(span-nose_half)*taper
        outer_y=_sculpted_outside(out,z)
        cage_front=outer_y+min(.48,p.FlexBumperWall*.28)
        # Front TPU thickness is an *external* adjustment. Fade the added
        # material in after the lower mounting shoe so the original nose,
        # carbon plate fit and round camera aperture remain unchanged.
        front_projection=(p.FlexBumperCameraFrontProjection *
                          _smoothstep((u-.15)/.85))
        front=foot_front+(cage_front-foot_front)*taper+front_projection
        # A gently accelerating rear silhouette gives the solid triangular
        # shoulder shown in the full-shell reference.  Unlike a separate web
        # or joined arch, this is part of the SAME loft from sole to crown.
        # The original nose, front profile, and camera aperture are untouched.
        rear=foot_rear+(top_rear-foot_rear)*(u**1.7)
        radius=4.4+(min(2.2,p.FlexBumperWall*1.45)-4.4)*taper
        stations.append(_fairing_wire(half,rear,front,z,radius,cx,top_edge,
                                     _smoothstep((u-.78)/.22),front_projection))
    failures=[]
    for ruled in (False,True):
        try:
            shell=Part.makeLoft(stations,True,ruled)
            if not shell.isNull() and shell.isValid() and len(shell.Solids)==1:
                break
            failures.append('invalid '+str(ruled))
        except Exception as exc:
            failures.append(str(exc))
    else:
        raise ValueError('Could not loft integrated bumper outer shell: '+'; '.join(failures))
    # A round-bottom open camera window splits the shell into two smoothly
    # rising sides, while remaining joined by the thick nose below the lens.
    # The old fixed bottom of the aperture could sit ABOVE the actual camera
    # envelope. The later camera-body Boolean then drilled a separate tiny
    # slit/crescent through the lower nose. Join that clearance into the main
    # round camera mouth instead, retaining at least a small TPU/plate lip.
    from .fpv import camera_angles,camera_body_centre,camera_vertical_limits
    angles=camera_angles(p)
    camera_bottom=min(camera_body_centre(p,a)[1]+camera_vertical_limits(p,a)[0]
                      for a in angles)
    # A low global Z extremum does not establish a collision with the lip:
    # the O4 Pro lens may be entirely FORWARD of the bottom-plate and bumper
    # lip. Previous code rejected such configurations before checking XY.
    # Keep the lower U opening above the plate's retaining lip, and subtract
    # the *actual* rotated camera solids from TPU after making the plate
    # mounting cavity. That operation detects only genuine local contact;
    # carbon plate geometry is never edited to accommodate the camera.
    safe_floor=p.BottomThickness+max(.30,p.FlexBumperFit+.20)
    zbottom=max(safe_floor,min(upper+.65,camera_bottom-max(.25,p.FlexBumperFit+.2)))
    aperture_half=inner_half-min(.22,p.FlexBumperFit+.12)
    cutter=_camera_aperture(aperture_half,zbottom,top,outer.BoundBox.YMin-35.,
                            (outer.BoundBox.YMax-outer.BoundBox.YMin)+70.,cx,
                            p.FlexBumperCameraBlendReach)
    shell=shell.cut(cutter)
    if shell.isNull() or not shell.isValid() or len(shell.Solids)!=1:
        raise ValueError('Integrated camera opening interrupted the continuous TPU shell.')
    return shell



def _adaptive_lower_sole_fillet(p, body):
    """Soft-round the *outside* underside of the integrated shoe only.

    The bottom perimeter comes from the one-piece loft, before any carbon
    pocket is cut. Rounding it at this stage leaves the internal plate fit,
    retaining lip and screw/camera clearances geometrically unchanged.

    The sole and wall supply the material for this fillet. Very thin shoes
    remain sharp instead of attempting an invalid or fragile tiny fillet.
    Failed OCC fillets are retried at smaller radii and never prevent an
    otherwise valid integrated bumper from building.
    """
    sole=max(0., float(p.FlexBumperSole))
    wall=max(0., float(p.FlexBumperWall))
    radius=min(1.35, .60*sole, .60*wall)
    if radius < .40:
        return body
    bottom=-p.FlexBumperFit-sole
    # Only the planar lower OUTER perimeter exists at this stage. No inner
    # gripping-channel edges have been generated yet.
    edges=[e for e in body.Edges
           if abs(e.BoundBox.ZMin-bottom)<1.e-4
           and abs(e.BoundBox.ZMax-bottom)<1.e-4
           and e.Length>1.e-5]
    if len(edges)<3:
        return body
    for scale in (1., .8, .6, .45):
        trial=radius*scale
        if trial<.35:
            break
        try:
            rounded=body.makeFillet(trial,edges)
            if (not rounded.isNull() and rounded.isValid()
                    and len(rounded.Solids)==1 and rounded.Volume>1.e-5):
                return rounded
        except Exception:
            # OCC occasionally rejects a radius near a sharp loft corner.
            # Preserve the body and retry with less material removed.
            pass
    return body


def integrated_camera_bumper(p,parts):
    """Separate from the standard bumper: sculpt, open, and fit ONE full shell."""
    if not p.FPVEnabled:
        raise ValueError('Integrated camera cage bumper requires an FPV camera.')
    from .bumper_geometry import _base_shoe, _finish_bumper
    from .protection_geometry import outer_face
    from .geometry import camera_envelope
    from .fpv import camera_angles
    from dataclasses import replace
    # Use the old shoe only as a 2D footprint reference: none of its solid
    # geometry is fused.  The exterior is one loft from sole to cage top.
    fit_parameters=replace(p,FlexBumperWidth=0.,FlexBumperTipWidth=0.,
                           FlexBumperRecess=0.,FlexBumperLipReach=0.)
    _,outer,upper,low,_=_base_shoe(fit_parameters,parts,'Rounded shoe')
    top_outline=[]
    top_plate=parts.get('TopPlate')
    if not p.FlexBumperCameraHeight and top_plate is not None and not top_plate.isNull():
        top_face=outer_face(top_plate)
        for edge in top_face.OuterWire.Edges:
            samples=edge.discretize(Deflection=.15)
            top_outline.extend((a.x,a.y,b.x,b.y) for a,b in zip(samples,samples[1:]))
    body=_sculpted_shell(p,camera_cover_profiles(p),outer,upper,top_outline)
    # Round only the lowest OUTSIDE edge of the one-piece shell. This adapts
    # to the available sole/wall TPU and is skipped for very thin shoes.
    body=_adaptive_lower_sole_fillet(p,body)
    # Carve the mounting cavity out of the *same* solid rather than joining
    # an independent shoelike collar, which was leaving the visible seam.
    from .protection_geometry import offset_face
    from .protection_geometry import outer_face as plate_outer_face
    plate_face=plate_outer_face(parts['BottomPlate'])
    fit=p.FlexBumperFit
    pocket=offset_face(plate_face,fit).extrude(
        App.Vector(0,0,p.BottomThickness+2*fit))
    pocket.translate(App.Vector(0,0,-fit))
    lip_opening=offset_face(plate_face,-p.FlexBumperOverlap).extrude(
        App.Vector(0,0,p.FlexBumperLip+1.))
    lip_opening.translate(App.Vector(0,0,p.BottomThickness+fit))
    body=body.cut(pocket).cut(lip_opening)
    if p.FlexBumperLipReach:
        face_front=plate_face.BoundBox.YMax
        rear=face_front-p.FlexBumperReach
        limit=face_front-p.FlexBumperLipReach
        if limit>rear:
            body=body.cut(Part.makeBox(2000.,limit-rear+1.,p.FlexBumperLip+1.,
                                      App.Vector(-1000.,rear-1.,p.BottomThickness+fit)))
    if body.isNull() or not body.isValid() or len(body.Solids)!=1:
        raise ValueError('Continuous integrated TPU shell was interrupted by its bottom-plate mounting cavity.')
    angles=tuple(sorted(set(camera_angles(p))|{p.CameraTilt})) if p.CameraMountMode=='Variable' else (p.CameraTilt,)
    for angle in angles:
        lens=camera_envelope(p,angle)
        if not lens.isNull() and body.BoundBox.intersect(lens.BoundBox):
            body=body.cut(lens)
    body=_finish_bumper(p,parts,body,upper,low)
    return guard_refine(body)
