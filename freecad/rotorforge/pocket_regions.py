"""Merge exact pocket regions before applying any fitting clearance."""


def cap_boundary(faces):
    """Reconstruct exterior and hole wires, cancelling shared partition edges."""
    import Part
    if len(faces) == 1:
        return faces[0]
    buckets = {}
    for face in faces:
        for edge in face.Edges:
            bucket = buckets.setdefault(edge.hashCode(), [])
            for item in bucket:
                if edge.isSame(item[0]):
                    item[1] += 1
                    break
            else:
                bucket.append([edge, 1])
    items = [item for bucket in buckets.values() for item in bucket]
    if any(count > 2 for _, count in items):
        raise ValueError('Non-manifold pocket boundary.')
    boundary = [edge for edge, count in items if count == 1]
    if not boundary:
        raise ValueError('Pocket region has no exterior boundary.')
    wires = [Part.Wire(group) for group in Part.sortEdges(boundary)]
    if not wires or any(not wire.isClosed() for wire in wires):
        raise ValueError('Pocket boundary could not be closed.')
    result = Part.makeFace(wires, 'Part::FaceMakerBullseye')
    area = sum(face.Area for face in faces)
    if not result.isValid() or len(result.Faces) != 1 or abs(result.Area-area) > max(1e-6, area*1e-7):
        raise ValueError('Pocket boundary reconstruction changed the region.')
    return result.Faces[0]


def planar_union(faces, z):
    """Fuse thin solid proxies, then recover one clean face per island.

    The solid Boolean gives shared topology to overlapping planar profiles;
    internal edges are dissolved before any per-side fit clearance is applied.
    Preserve actual holes and disconnected regions, without approximating arcs.
    """
    import FreeCAD as App
    import Part
    slab = .1
    solids = []
    for face in faces:
        if face.Area <= 1e-8:
            continue
        face = face.copy()
        face.translate(App.Vector(0, 0, z-face.CenterOfMass.z))
        if face.normalAt(0, 0).z < 0:
            face.reverse()
        solids.append(face.extrude(App.Vector(0, 0, slab)))
    if not solids:
        return None
    fused = solids[0].multiFuse(solids[1:]) if len(solids)>1 else solids[0]
    if fused.isNull() or not fused.isValid() or not fused.Solids:
        raise ValueError('Could not merge selected pocket regions.')
    regions = []
    for solid in fused.Solids:
        solid = solid.removeSplitter()
        caps = [f for f in solid.Faces if f.BoundBox.ZLength < 1e-6
                and abs(f.CenterOfMass.z-(z+slab)) < 1e-6]
        if not caps:
            raise ValueError('Merged pocket region has no upper boundary.')
        face = cap_boundary(caps).copy()
        if abs(face.Area*slab-solid.Volume) > max(1e-7, solid.Volume*1e-6):
            raise ValueError('Merged pocket boundary does not match its solid.')
        face.translate(App.Vector(0, 0, -slab))
        if face.normalAt(0, 0).z < 0:
            face.reverse()
        regions.append(face)
    return regions[0] if len(regions)==1 else Part.makeCompound(regions)
