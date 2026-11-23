"""Cutter-aware construction of the optional additive arm-tip geometry.

The arm tip is manufactured with the same selected *radius* that the final
CNC validator checks.  Inward cutout corners are made by cutter opening;
outer re-entrant corners by cutter closing.  Both use FreeCAD's analytic OCC
round offsets (not a polygonal approximation that leaves micro-corners).

Only used for enabled arm-tip bumper features.  The unmodified motor mounting
holes are drilled after these operations by geometry._component_arm.
"""


def _single_face(shape):
    """An offset can be an OCC wire, face or compound; reject split results."""
    import Part
    if shape.isNull():
        raise ValueError('CNC offset is empty')
    if len(shape.Faces) == 1:
        face = shape.Faces[0]
    elif len(shape.Faces) == 0 and len(shape.Wires) == 1:
        face = Part.Face(shape.Wires[0])
    else:
        raise ValueError('CNC offset splits the outline into separate regions')
    if face.isNull() or not face.isValid() or face.Area <= 1.e-6:
        raise ValueError('CNC offset has no valid milling area')
    return face


def _upper_face(shape):
    """Extract the horizontal cap without changing the source BRep."""
    top = shape.BoundBox.ZMax
    faces = [face for face in shape.Faces
             if face.BoundBox.ZLength < 1.e-5
             and abs(face.BoundBox.ZMax - top) < 1.e-5]
    if not faces:
        raise ValueError('Cannot find arm-tip top contour')
    return max(faces, key=lambda face: face.Area)


def _tool_roll(face, radius, opening):
    """Analytic machining: opening shrinks an air window, closing fills notches.

    Use a positive tolerance reserve to keep the manufactured radii above
    the cutter radius despite OCC join and geometric tolerance noise.
    """
    # Relative to typical drone hardware geometry, this is a sub-0.01 mm
    # reserve. Never make an R0.5 profile with an R0.49 rolling tool.
    tool = radius + 0.012
    first = _single_face(face.makeOffset2D(-tool if opening else tool, join=0))
    second = _single_face(first.makeOffset2D(tool if opening else -tool, join=0))
    return second


def machine_tip_window(cut_solid, cutter_radius):
    """Round a shaped tip window without widening it or reducing screw lands.

    Returns None if the requested cutter physically cannot enter the pocket.
    The caller then omits that optional *decorative* cut, never leaves a
    sub-diameter notch and never changes the drilled mounting holes.
    """
    import FreeCAD as App
    import Part
    cap = _upper_face(cut_solid)
    src = Part.Face(cap.OuterWire)
    try:
        result = _tool_roll(src, cutter_radius, opening=True)
    except Exception:
        return None
    if result.Area < max(0.35, cutter_radius * cutter_radius * .12):
        return None
    # Cutter opening MUST be wholly contained within the proposed air window.
    # A tolerance-spill could otherwise take material out of the motor lands.
    if result.cut(src).Area > 1.e-5:
        return None
    z0 = cut_solid.BoundBox.ZMin
    result.translate(App.Vector(0., 0., z0 - result.BoundBox.ZMin))
    candidate = result.extrude(App.Vector(0., 0., cut_solid.BoundBox.ZLength))
    if candidate.isNull() or not candidate.isValid() or len(candidate.Solids) != 1:
        return None
    return candidate


def machine_tip_perimeter(carbon, cutter_radius, motor=None, maximum_reach=None):
    """Fill tool-inaccessible outside notches using an analytic rolling disk.

    This is performed on the optional motor-tip subassembly, *before* the
    arm-root geometry is fused, so only tip/pad shapes are affected.  The
    drilled motor bores are created unchanged AFTER this step.  All additions
    must remain outside the original outline; a malformed offset never
    subtracts material or compromises the original carbon solid.
    """
    import FreeCAD as App
    import Part
    try:
        cap = _upper_face(carbon)
        exterior = Part.Face(cap.OuterWire)
        # Most corners are already cutter-safe. Avoid two potentially heavy
        # OCC offsets when no concave defect needs correcting. In particular,
        # the full assembled arm should not be re-offset for each tiny edit
        # after its tip has already been repaired in the pad subassembly.
        from .plate_fillets import _unmachinable_corners, _unmachinable_arcs
        defects = list(_unmachinable_corners(exterior))
        defects.extend((x,y) for x,y,_r in _unmachinable_arcs(exterior,cutter_radius))
        if motor is not None and maximum_reach is not None:
            reach2 = maximum_reach * maximum_reach
            defects = [(x,y) for x,y in defects
                       if (x-motor[0])**2+(y-motor[1])**2 <= reach2]
        if not defects:
            return carbon
        closed = _tool_roll(exterior, cutter_radius, opening=False)
        patches = closed.cut(exterior)
        if patches.isNull() or patches.Area <= 1.e-7:
            return carbon
        # Do not fill an existing tip air-window with a perimeter correction.
        cutouts = [Part.Face(w) for w in cap.Wires if not w.isSame(cap.OuterWire)]
        z0 = carbon.BoundBox.ZMin
        height = carbon.BoundBox.ZLength
        result = carbon
        for patch in patches.Faces:
            if patch.Area <= 1.e-7:
                continue
            if motor is not None and maximum_reach is not None:
                # Second finishing pass on the assembled arm: only fill
                # concave corners in the *motor-tip* area, never root joins,
                # arm interlocks, or the independently configured arm stem.
                box=patch.BoundBox
                dx=max(box.XMin-motor[0],0.,motor[0]-box.XMax)
                dy=max(box.YMin-motor[1],0.,motor[1]-box.YMax)
                if dx*dx+dy*dy > maximum_reach*maximum_reach:
                    continue
            if any(patch.common(hole).Area > 1.e-7 for hole in cutouts):
                continue
            stock = patch.copy()
            stock.translate(App.Vector(0., 0., z0 - stock.BoundBox.ZMin))
            added = stock.extrude(App.Vector(0., 0., height))
            candidate = result.fuse(added).removeSplitter()
            if (candidate.isNull() or not candidate.isValid()
                    or len(candidate.Solids) != 1):
                continue
            result = candidate
        return result
    except Exception as err:
        # Later, the mandatory CNC validator will still reject an actually
        # unmachinable result.  Do not hide errors by skipping that check.
        try:
            App.Console.PrintWarning('Arm-tip CNC perimeter pre-shaping could not complete: %s\n' % err)
        except Exception:
            pass
        return carbon
