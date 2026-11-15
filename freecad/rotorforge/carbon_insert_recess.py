"""Side-specific axial geometry for optional flush carbon camera inserts.

X is physical frame left/right, not a flat export coordinate. A blind
outside counterbore leaves carbon below the flange to carry its bearing load.
The neck window continues through the whole plate with unchanged opening.
"""

MIN_CARBON_LEDGE = 1.0  # mm: preserve a structural carbon bearing shelf
POCKET_RADIAL_FIT = 0.05  # mm additional cutter/profile clearance


def carbon_flush_enabled(p):
    return bool(getattr(p, 'CameraCarbonFlushInserts', False) and
                p.FPVEnabled and p.CameraCageStyle == 'Carbon side plates' and
                p.FlexCameraMode == 'Captured inserts' and
                p.FlexInsertLipSide in ('Outside only','Both sides'))


def flange_thickness(p):
    # The existing nonflush insert flange already has precisely this thickness.
    return max(.8, float(p.FlexPadThickness) / 2.)


def outer_plate_x(mount, sign):
    a,b = mount['plate_x']
    return a if sign < 0 else b


def recess_span(p, mount, sign):
    """The outermost X interval *inside* carbon removed for the flange."""
    if not carbon_flush_enabled(p):
        return None
    a,b = mount['plate_x']
    depth = flange_thickness(p)
    remaining = b-a-depth
    if remaining < MIN_CARBON_LEDGE-1.e-7:
        raise ValueError('Flush carbon captured inserts need %.2f mm flange depth '
                         'plus at least %.2f mm supporting carbon. Selected side '
                         'plate has %.2f mm thickness. Increase Camera bracket '
                         'thickness or disable Flush carbon-side captured inserts.' %
                         (depth, MIN_CARBON_LEDGE, b-a))
    return (a,a+depth) if sign < 0 else (b-depth,b)


def outside_flange_span(p, mount, sign):
    """Installed outer retaining flange span; independent of neck clearance."""
    if carbon_flush_enabled(p):
        return recess_span(p,mount,sign)
    edge = outer_plate_x(mount,sign)
    depth = flange_thickness(p)
    return (edge-depth,edge) if sign < 0 else (edge,edge+depth)


def bearing_span(p,mount,sign):
    """Unrecessed carbon slab behind flange used for physical support checks."""
    a,b=mount['plate_x']
    rec=recess_span(p,mount,sign)
    if rec is None:return (a,b)
    return (rec[1],b) if sign < 0 else (a,rec[0])
