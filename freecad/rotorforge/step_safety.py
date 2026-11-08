"""Front-bumper STEP exports based on the already-written printable STL mesh.

The former BRep STEP sometimes contained the wrong geometry although its STL was
correct.  Here STEP is reconstructed from the *same mesh* as that STL.  Such a
STEP has triangular planar faces and is not an editable smooth parametric model.

Failure must be confined to the bumper STEP outputs: never block CNC, STL or
other flexible-part exports, and never quietly replace a failed result with the
known-problematic legacy BRep STEP.
"""
import os
from pathlib import Path


def _bounding_lengths(shape):
    b = shape.BoundBox
    return (float(b.XLength), float(b.YLength), float(b.ZLength))


def _check_matching_dimensions(actual, expected, tolerance=0.35):
    a, b = _bounding_lengths(actual), _bounding_lengths(expected)
    if any(abs(x - y) > tolerance for x, y in zip(a, b)):
        raise ValueError("mesh STEP dimensions differ from STL source: %r versus %r mm" % (a, b))


def faceted_solid_from_mesh(mesh, printable):
    """Build a closed faceted OCC solid from the STL's actual triangle mesh.

    The input ``mesh`` is the same FreeCAD.Mesh object that gets written as
    FrontBumper.stl.  This intentionally never tessellates the old STEP shape
    again, so the two manufacturing outputs describe the same surface.
    """
    import Part

    if not mesh.isSolid():
        # A tiny STL rounding seam can sometimes prevent solid recognition.
        # Make a conservative welded *copy* for STEP only; the working STL
        # file remains untouched. Never attempt aggressive hole filling.
        try:
            from .mesh_cleanup import weld_micro_seams
            repaired = weld_micro_seams(mesh)
            if repaired.isSolid():
                mesh = repaired
        except Exception:
            pass
        if not mesh.isSolid():
            raise ValueError("front bumper STL mesh is not watertight; cannot create a solid STEP")
    triangle_shape = Part.Shape()
    triangle_shape.makeShapeFromMesh(mesh.Topology, 0.005)
    shells = list(triangle_shape.Shells)
    if not shells and triangle_shape.Faces:
        # Standard FreeCAD Mesh-to-Shape examples also construct a Shell
        # explicitly from the triangular faces; support both OCC variants.
        shells = [Part.Shell(triangle_shape.Faces)]
    if len(shells) != 1:
        raise ValueError("bumper STL must form one closed shell (found %d)" % len(shells))
    faceted = Part.makeSolid(shells[0])
    if faceted.Volume < 0:
        faceted.reverse()
    if (faceted.isNull() or not faceted.isValid() or
            len(faceted.Solids) != 1 or faceted.Volume <= 0):
        raise ValueError("STL-to-STEP conversion did not produce one valid solid")
    _check_matching_dimensions(faceted, printable)
    source_volume = float(printable.Volume)
    if source_volume > 0 and abs(faceted.Volume - source_volume) / source_volume > 0.12:
        raise ValueError("STL-to-STEP volume disagrees with the printable bumper by over 12%")
    return faceted


def export_bumper_mesh_steps(assembled, printable, mesh, destination):
    """Atomically write *both* STEP variants from the printable STL's facets.

    If conversion or either write fails, no misleading bumper STEP is left
    behind. The caller catches the error and continues exporting other parts.
    The assembled version is the print mesh translated to its frame position;
    this is valid for the front bumper (which has no print-only rotation).
    """
    folder = Path(destination)
    folder.mkdir(parents=True, exist_ok=True)
    print_step = folder / 'FrontBumper_print.step'
    assembled_step = folder / 'FrontBumper_assembled.step'
    temporary = [(folder / '.FrontBumper_print.pending.step', print_step),
                 (folder / '.FrontBumper_assembled.pending.step', assembled_step)]
    for pending, _ in temporary:
        if pending.exists():
            pending.unlink()
    try:
        print_solid = faceted_solid_from_mesh(mesh, printable)
        assembled_solid = print_solid.copy()
        src = assembled.BoundBox
        faceted = print_solid.BoundBox
        # printable_flex() only translates the FrontBumper, never rotates it.
        import FreeCAD as App
        assembled_solid.translate(App.Vector(src.XMin - faceted.XMin,
                                             src.YMin - faceted.YMin,
                                             src.ZMin - faceted.ZMin))
        _check_matching_dimensions(assembled_solid, assembled)
        for pending, source in ((temporary[0][0], print_solid),
                                (temporary[1][0], assembled_solid)):
            source.exportStep(str(pending))
            if not pending.is_file() or pending.stat().st_size < 256:
                raise ValueError("STEP writer returned an empty or incomplete file: %s" % pending.name)
        for pending, final in temporary:
            os.replace(str(pending), str(final))
        return print_step, assembled_step
    except Exception:
        for pending, final in temporary:
            try:
                pending.unlink(missing_ok=True)
                final.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def export_bumper_step(shape, destination):
    """Compatibility-only legacy helper (not used in package export)."""
    target = Path(destination)
    try:
        solids = shape.Solids
        if len(solids) == 1 and shape.isValid():
            solid = solids[0]
            if len(shape.Faces) > len(solid.Faces) and solid.isValid():
                try:
                    solid.copy().exportStep(str(target))
                    if target.is_file() and target.stat().st_size > 0:
                        return target
                except Exception:
                    pass
    except Exception:
        pass
    shape.exportStep(str(target))
    return target
