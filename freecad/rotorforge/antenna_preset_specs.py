"""Nominal display dimensions for commercial-style antenna references (mm).

The quoted product lengths are catalogue figures, normally measured from the
connector end. Mounted antenna reach is only an approximation because the
feed cable may bend or have a different insertion depth. These are NOT tuned
radiators, RF models, fitting jigs or commercial CAD drawings.
"""

# VTX lengths are common retail configurations, not universal standards.
# Head width varies even within Lollipop revisions; custom mode is available.
VTX_PRESETS={
    'Lollipop 60 mm': (60., 11., 13.),
    'Lollipop 85 mm': (85., 11., 13.),
    'Lollipop 95 mm': (95., 11., 13.),
    'Lollipop 100 mm': (100., 11., 13.),
    'Avatar V2 105 mm': (105., 15., 19.),
    'Lollipop 150 mm': (150., 11., 13.),
    'Lollipop 165 mm': (165., 11., 13.),
    'Custom': None,
}
ELRS_SPAN_PRESETS={
    'Compact T 50 mm': 50.,
    'T 51 mm': 51.,
    'Ideal half-wave 62.5 mm': 62.46,
    'Custom': None,
}
ELRS_FEED_PRESETS={
    '40 mm': 40.,
    '70 mm': 70.,
    '85 mm': 85.,
    '95 mm': 95.,
    'Custom': None,
}


def vtx_spec(p):
    preset=VTX_PRESETS[p.VTXAntennaReferencePreset]
    if preset is None:
        length=float(p.VTXAntennaReferenceLength)
        diameter=float(p.VTXAntennaReferenceDiameter)
        head_length=max(6.,min(20.,diameter*1.2))
    else:
        length,diameter,head_length=preset
    return dict(length=length,head_diameter=diameter,head_length=head_length)


def elrs_spec(p):
    span=ELRS_SPAN_PRESETS[p.ELRSTReferencePreset]
    feed=ELRS_FEED_PRESETS[p.ELRSTReferenceFeedPreset]
    return dict(span=float(p.ELRSTReferenceSpan if span is None else span),
                feed_length=float(p.ELRSTReferenceStemLength if feed is None else feed))


def elrs_feed_to_vtx(p, cable_start_y, clearance_mm=3.0):
    """Forward (+Y) straight reference lead: stop short of the VTX rear edge.

    Uses the same VTX board envelope as the detailed/simple VTX reference. An
    already-overlapping or forward-of-board start has no visible lead; negative
    lengths are never created. Historic feed presets remain readable in JSON,
    but do not influence this purely illustrative cable.
    """
    if not p.FPVEnabled:
        return 0.0  # No VTX is present in a non-FPV design.
    vtx_rear_y=p.VTXOffsetY-p.VTXLength/2.0
    return max(0.0,vtx_rear_y-clearance_mm-float(cable_start_y))
