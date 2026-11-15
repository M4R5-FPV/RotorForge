"""Bounded, spatially local automatic airflow candidate planner.

This planner is deliberately independent of Qt/FreeCAD.  It proposes a varied
mixture of small CNC-compatible manual-library profiles and irregular Web cells
without expensive full-plate boolean construction.  The editor's exact Qt
clearance validator decides what may be manufactured.
"""
import math
import random

from .cutouts import PATTERN_DEFAULTS, cutout_polygon, check_cnc_shape

# All these names are available from the normal, R0.5-validated manual palette.
MANUAL_SHAPES = (
    'Circle', 'Slot', 'Arc slot', 'Rounded rectangle', 'Ellipse', 'Triangle', 'Diamond',
    'Trapezoid', 'Hexagon', 'Pentagon', 'Octagon', 'Heptagon', 'Dodecagon',
    'Chevron', 'Parallelogram', 'Kite', 'Hourglass', 'Cross', 'Shield',
    'Swept fin', 'Aero spear', 'Split bridge',
)


def _web_vertices(rng, style):
    """A compact assortment of asymmetric cells, wedges, hexagons and facets.

    Limit the number of corners, and keep them well separated so genuine R0.5
    fillets are possible even in narrow plate channels.
    """
    family = rng.randrange(5)
    jitter = lambda span: rng.uniform(-span, span)
    if family == 0:  # offset trapezium
        verts = [(-.5, -.48), (.23 + jitter(.12), -.5),
                 (.5, .35 + jitter(.09)), (-.27 + jitter(.1), .5)]
    elif family == 1:  # asymmetric, chamfered diamond
        verts = [(-.48, -.12), (-.23, -.5), (.27, -.46),
                 (.5, .12), (.14, .5), (-.4, .35)]
    elif family == 2:  # flowing five-sided bay
        verts = [(-.48, -.43), (.4, -.5), (.5, .06),
                 (.06 + jitter(.12), .5), (-.49, .23)]
    elif family == 3:  # tilted six-sided rib cell
        verts = [(-.48, -.45), (.08, -.49), (.5, -.15),
                 (.48, .43), (-.1, .49), (-.5, .12)]
    else:  # sharp but machinable zigzag channel
        verts = [(-.49, -.48), (.18, -.5), (.5, -.23),
                 (.25, .06), (.49, .44), (-.2, .49), (-.5, .18)]
    if style == 'Structural lattice':
        # Straighter, more regular network with some asymmetry.
        verts = [(x*.94, y*.96) for x, y in verts]
    elif style == 'Swept channels':
        verts = [(max(-.5,min(.5,x+.09*y)), y) for x,y in verts]
    elif style == 'Tapered relief':
        verts = [(x*(.79-.20*y), y) for x,y in verts]
    return [[round(x,5),round(y,5)] for x,y in verts]


def _pick_shape(rng, style, mix):
    if mix == 'Web cells':
        return 'Web cell'
    if mix == 'Manual shapes':
        return rng.choice(MANUAL_SHAPES)
    if rng.random() < {'Structural lattice': .52, 'Geometric accents': .34,
                       'Swept channels': .46, 'Tapered relief': .58}.get(style, .45):
        return 'Web cell'
    if style == 'Swept channels':
        preferred = ('Slot','Arc slot','Ellipse','Swept fin','Aero spear','Trapezoid',
                     'Parallelogram','Shield')
    elif style == 'Structural lattice':
        preferred = ('Hexagon','Diamond','Triangle','Trapezoid','Kite',
                     'Rounded rectangle')
    elif style == 'Geometric accents':
        preferred = ('Diamond','Triangle','Pentagon','Chevron','Kite',
                     'Split bridge','Hexagon')
    elif style == 'Tapered relief':
        preferred = ('Swept fin','Shield','Trapezoid','Kite','Aero spear',
                     'Rounded rectangle')
    else:
        preferred = MANUAL_SHAPES
    return rng.choice(preferred)


def make_candidate(role, x, y, width, length, angle, rng, style, mix):
    """Build a local proposal; invalid tightly rounded polygons are skipped."""
    shape = _pick_shape(rng, style, mix)
    item = dict(PATTERN_DEFAULTS, role=role, mode='Interior', shape=shape,
                width=round(width,2), length=round(length,2),
                x=round(x,3), y=round(y,3), rotation=round(angle,2),
                enabled=True, columns=1,rows=1,vertices=[])
    if shape == 'Circle':
        item['length'] = item['width']
    elif shape == 'Arc slot':
        item['arc_angle'] = rng.choice((-135.,-110.,-85.,-60.,60.,85.,110.,135.))
    elif shape == 'Web cell':
        item['vertices'] = _web_vertices(rng, style)
    try:
        check_cnc_shape(item)
    except (ValueError, TypeError, ZeroDivisionError, OverflowError):
        return None
    return item


def mirror_candidate(item, axis):
    """Mirror *geometry*, not merely the centre of an asymmetric manual cut."""
    mirrored = dict(item, x=round(2*axis-item['x'], 3),
                    rotation=round(-item['rotation'],2))
    # A manual polygon with asymmetric vertices cannot be reflected merely
    # by reversing its rotation. Convert ONLY its mirrored partner to a Web
    # cell, preserving the original manual profile's exact rounded geometry.
    shape = item['shape']
    reflection_safe = ('Circle','Slot','Arc slot','Rounded rectangle','Ellipse','Triangle',
                       'Diamond','Trapezoid','Hexagon','Pentagon','Octagon',
                       'Heptagon','Dodecagon','Chevron','Kite','Hourglass',
                       'Cross','Shield','Aero spear','Split bridge')
    if shape in reflection_safe:
        if shape == 'Arc slot':
            mirrored['arc_angle'] = -item['arc_angle']
        return mirrored
    if shape == 'Web cell':
        vertices = item['vertices']
    else:
        vertices = [[x/item['width'],y/item['length']]
                    for x,y in cutout_polygon(item)]
    mirrored['shape']='Web cell'
    mirrored['vertices']=[[-x,y] for x,y in reversed(vertices)]
    try:
        check_cnc_shape(mirrored)
    except (ValueError, TypeError):
        return None
    return mirrored


def iter_design_candidates(bounds, role, style, density, layout, web_mm,
                           seed, mix='Mixed shapes', max_attempts=160):
    """Yield plausible small-to-medium proposals; stop after a fixed budget.

    Scan multiple randomized stations so locked shapes never cause an
    unbounded retry, and prefer fitting small patterns to oversized cells.
    Exact material / mounting checks are deliberately NOT done here.
    """
    left, bottom, width, height = (float(v) for v in bounds)
    if min(width,height)<10 or web_mm<3:
        return
    rng=random.Random(f'local-airflow-v2|{seed}|{role}|{bounds}|{style}|'
                      f'{density}|{layout}|{web_mm}|{mix}')
    mirrored=layout=='Mirrored'
    axis=0. if left<=0<=left+width else left+width*.5
    right=left+width
    top=bottom+height
    pitch={'Sparse':32.,'Balanced':22.,'Detailed':15.}.get(density,22.)
    bands=max(1, min(35,round(height/pitch)))
    # Stagger lanes / station order, rather than scanning the same handful of
    # big rectangles. Multiple rounds actively search free gaps around Keep.
    attempts=0
    for phase in range(6):
        stations=list(range(bands))*3
        rng.shuffle(stations)
        for row in stations:
            if attempts>=max_attempts:
                return
            attempts+=1
            cell_y=bottom+(row+.5)*height/bands
            y=cell_y+rng.uniform(-.42,.42)*(height/bands)
            y=min(top-2.0,max(bottom+2.0,y))
            central=(rng.random()<(.23 if density=='Detailed' else .16))
            if mirrored and not central:
                lane_start=axis+web_mm*.5+2.
                lane_end=right-web_mm-2.
                if lane_end<=lane_start:continue
                x=rng.uniform(lane_start,lane_end)
                max_w=min(2*(x-axis)-web_mm-1.,
                          2*(right-x-web_mm-1.))
            else:
                # Organic balance switches amongst left, centre and right.
                centre_x=axis if central or mirrored else rng.choice(
                    (axis-width*.22,axis,axis+width*.22))
                x=centre_x+rng.uniform(-min(3,width*.1),min(3,width*.1))
                if mirrored: x=axis  # a single genuinely central aperture
                max_w=2*min(x-left-web_mm-1.,right-x-web_mm-1.)
            if max_w<3.2:
                continue
            # Large cutouts are exceptional; many small pockets/vents produce
            # interesting carbon webs, especially in the Detailed mode.
            small=rng.random()<(.50 if density=='Detailed' else .37)
            width_ceiling={'Sparse':19.,'Balanced':15.,'Detailed':11.}[density]
            width_ceiling=min(width_ceiling,max_w)
            if small:
                w=min(width_ceiling,rng.uniform(4.0,8.0))
                ln=rng.uniform(6.5,13.0)
            else:
                w=min(width_ceiling,rng.uniform(7.0,17.0))
                ln=rng.uniform(11.,{'Sparse':29.,'Balanced':23.,'Detailed':17.}[density])
            # Reduce dimensions on later passes to fit between locked cuts.
            shrink=(1.,.92,.80,.72,.64,.55)[phase]
            w=max(3.2,w*shrink)
            ln=max(5.5,ln*shrink)
            ln=min(ln,2*min(y-bottom-web_mm-1.,top-y-web_mm-1.))
            if ln<5.0:continue
            turn={'Structural lattice':8.,'Swept channels':24.,
                  'Tapered relief':16.,'Geometric accents':28.}.get(style,14.)
            # Narrow plates cannot accommodate large rotated longitudinal cuts.
            if width < 55.:turn=min(turn,9.)
            angle=rng.uniform(-turn,turn)
            candidate=make_candidate(role,x,y,w,ln,angle,rng,style,mix)
            if candidate is not None:
                yield candidate
