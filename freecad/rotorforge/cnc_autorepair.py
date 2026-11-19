"""Finish unresolved machining corners using the selected rolling cutter radius.

2D closing adds ONLY missing cutter-radius material at concave outer corners.
The opposite opening operation rounds tiny inside corners in non-circular
through cutouts. Each candidate is checked individually against the original
bores, miter cells, topology and bounded-area limits. The hard minimum must
never be bypassed by suppressing validation, nor by altering bolt locations.
"""

TOOL_RADIUS=0.52


def _as_face(shape):
    from .cnc_perimeter import _as_single_face
    return _as_single_face(shape)


def _rounded_offset(face,radius,outward):
    """Morphological closing/opening with exact OCC round joins."""
    first=_as_face(face.makeOffset2D(radius if outward else -radius,join=0))
    return _as_face(first.makeOffset2D(-radius if outward else radius,join=0))


def _holes(face):
    import Part
    outer=face.OuterWire
    return [Part.Face(w) for w in face.Wires if not w.isSame(outer)]


def finish_cnc_face(face,role,arm=None,joint_cell=None,minimum=.5):
    """Attempt exact rolling-cutter repairs, preserving the original bores.

    Do not reject a CAD build because a *single-edge* fillet lacks tangency
    length: the rolling disk often handles neighboring short edges together.
    This operates on the entire cap and is rerun on the actual final profile
    until all allowed corrections have been accepted or progress stops.
    """
    import FreeCAD as App
    import Part
    from .plate_fillets import (_unmachinable_arcs,_unmachinable_corners)
    working=face
    fixed=0
    for radius in (minimum+.02,minimum+.06,minimum+.15):
        bad=_unmachinable_corners(working)
        arcs=_unmachinable_arcs(working,minimum)
        if not bad and not arcs:
            break
        before=working
        # The same rolling-radius operation applies to neighboring sharp
        # corners, undersized arc blends and features too short to fillet.
        # No arbitrary small-patch radius-reduction is permitted.
        try:
            outside=Part.Face(working.OuterWire)
            closed=_rounded_offset(outside,radius,True)
            candidates=closed.cut(outside)
        except Exception as exc:
            App.Console.PrintWarning('%s: CNC outside closing %.2f unavailable (%s).\n' % (role,radius,exc))
            candidates=Part.Shape()
        if not candidates.isNull():
            for patch in candidates.Faces:
                bb=patch.BoundBox
                # A whole slot/intentional miter must never be filled.
                if patch.Area<1e-8 or patch.Area>10.0 or bb.XLength>8.0 or bb.YLength>8.0:
                    continue
                if joint_cell is not None and patch.cut(joint_cell).Area>1e-7:
                    continue
                # The closing was computed on the outline alone. Never let
                # that patch partially fill an existing drilled bore/slot.
                if any(patch.common(hole).Area>1e-7 for hole in _holes(working)):
                    continue
                # Only cutter patches at independently detected defects.
                if not any(patch.distToShape(Part.Vertex(App.Vector(x,y,0)))[0] <= radius+.3
                           for x,y in bad+[(a,b) for a,b,_ in arcs]):
                    continue
                try:
                    trial=working.fuse(patch).removeSplitter()
                    if trial.isNull() or not trial.isValid() or len(trial.Faces)!=1:
                        continue
                    trial=trial.Faces[0]
                    if len(trial.Wires)!=len(working.Wires):
                        continue
                    if working.cut(trial).Area>1e-7:
                        continue
                    working=trial;fixed+=1
                except Exception:
                    continue
        # Cutout corners also need the selected tool radius. The hole is the air
        # region; round its SHARP convex corners by slightly shrinking the
        # hole (never move or shrink circular mounting bores).
        locations=None
        for hole in _holes(working):
            # Inspect ONLY defect coordinates on this inner contour. Normal
            # round M2/M3 mounting bores must remain completely untouched.
            if locations is None:
                locations=_unmachinable_corners(working)
                locations.extend((x,y) for x,y,r in _unmachinable_arcs(working,minimum))
            if not any(hole.distToShape(Part.Vertex(App.Vector(x,y,0)))[0]<1e-5
                       for x,y in locations):
                continue
            try:
                opened=_rounded_offset(hole,radius,False)
                patches=hole.cut(opened)
            except Exception:
                continue
            if patches.isNull() or patches.Area>10.:continue
            for patch in patches.Faces:
                bb=patch.BoundBox
                if patch.Area<1e-8 or bb.XLength>8 or bb.YLength>8:continue
                try:
                    trial=working.fuse(patch).removeSplitter()
                    if not trial.isValid() or len(trial.Faces)!=1:continue
                    trial=trial.Faces[0]
                    if len(trial.Wires)!=len(working.Wires):continue
                    if working.cut(trial).Area>1e-7:continue
                    working=trial;fixed+=1;locations=None
                except Exception:continue
        if (working.cut(before).Area<1e-7):
            # No safe addition at this radius; try the next rolling radius.
            continue
    if fixed:
        App.Console.PrintMessage('%s: automatic R%g cutter rolling repaired %d local transition(s).\n' %(role,minimum,fixed))
    return working
