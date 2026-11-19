"""Original portable centre-line lettering for blind CNC engraving.

Every stroke is the exact swept disc of a >= 1 mm end mill, not a scaled
polygon outline. Closed letters retain their centres on the pocket floor.
Coordinates below describe centre-line polylines on a 3 x 5 design grid.
"""
import math
from functools import lru_cache

ENGRAVING_FONTS=(
    'Technical engraving','Italic engraving','Block engraving','Compact engraving',
    'Racing engraving','Rounded engraving','Serif engraving',
    'Aerospace engraving','Cyber engraving','Industrial engraving',
    'Extended engraving','Narrow engraving','Reverse italic engraving',
    'Rounded italic engraving','Racing block engraving','Digital engraving',
    'Slab serif engraving',
)
# Each style owns its actual cutter centre lines, not merely its display name.
# Width factors below are minimum centreline widths in cutter diameters.
_STYLES={
    'Technical engraving':(.0,2.4,4.0,.6),
    'Italic engraving':(.16,3.04,4.0,.6),
    'Block engraving':(.0,2.0,4.0,.6),
    'Compact engraving':(.0,2.0,4.0,.6),
    'Racing engraving':(.25,3.4,4.0,.6),
    'Rounded engraving':(.0,2.8,5.0,.6),
    'Serif engraving':(.0,3.0,5.0,.65),
    'Aerospace engraving':(.0,2.8,4.5,.65),
    'Cyber engraving':(.0,2.6,4.5,.65),
    'Industrial engraving':(.0,2.5,4.5,.6),
    'Extended engraving':(.0,4.0,4.0,.7),
    'Narrow engraving':(.0,1.9,4.5,.6),
    'Reverse italic engraving':(-.20,3.2,4.5,.65),
    'Rounded italic engraving':(.18,3.6,5.0,.65),
    'Racing block engraving':(.30,3.8,4.5,.65),
    'Digital engraving':(.0,2.8,5.0,.65),
    'Slab serif engraving':(.0,3.1,5.5,.7),
}
# Each slash separates pen-down paths. A single point represents a dot.
_GLYPHS={
'A':'00 1.5,5 30/0.6,2 2.4,2',
'B':'00 05 25 34 3,3.4 2.3,2.5 0,2.5/2.3,2.5 3,1.6 31 20 00',
'C':'34 25 15 04 01 10 20 31',
'D':'00 05 15 34 31 10 00',
'E':'35 05 00 30/0,2.5 2.4,2.5', 'F':'35 05 00/0,2.5 2.4,2.5',
'G':'34 25 15 04 01 10 20 31 32 1.5,2',
'H':'00 05/30 35/0,2.5 3,2.5', 'I':'05 35/1.5,5 1.5,0/00 30',
'J':'05 35 31 20 10 01', 'K':'00 05/35 0,2.5 30',
'L':'05 00 30', 'M':'00 05 1.5,2 35 30', 'N':'00 05 30 35',
'O':'10 01 04 15 25 34 31 20 10',
'P':'00 05 25 34 3,3.4 2,2.5 0,2.5', 'Q':'10 01 04 15 25 34 31 20 10/1.8,1.4 30',
'R':'00 05 25 34 3,3.4 2,2.5 0,2.5/2,2.5 30',
'S':'34 25 15 04 0,3.4 1,2.5 2,2.5 3,1.6 31 20 10 01',
'T':'05 35/1.5,5 1.5,0', 'U':'05 01 10 20 31 35',
'V':'05 1.5,0 35', 'W':'05 00 1.5,3 30 35',
'X':'05 30/00 35', 'Y':'05 1.5,2.5 35/1.5,2.5 1.5,0', 'Z':'05 35 00 30',
'0':'1,0 0.3,1 0.3,4 1,5 2,5 2.7,4 2.7,1 2,0 1,0', '1':'04 1.5,5 1.5,0/00 30',
'2':'04 15 25 34 3,3.4 00 30', '3':'05 25 34 3,3.4 2,2.5 0.9,2.5/2,2.5 3,1.6 31 20 00',
'4':'05 02 32/2.5,5 2.5,0', '5':'35 05 0,2.5 2,2.5 3,1.6 31 20 10 01',
'6':'34 25 15 04 01 10 20 31 3,1.6 2,2.5 0,2.5', '7':'05 35 1,0',
'8':'1,0 01 0,1.6 1,2.5 0,3.4 04 15 25 34 3,3.4 2,2.5 3,1.6 31 20 1,0/1,2.5 2,2.5',
'9':'3,2.5 1,2.5 0,3.4 04 15 25 34 31 20 10 01',
'-':'0,2.5 3,2.5', '_':'00 30', '.':'1.5,0', ' ':''}


# Squared bowls and terminals. Blind pockets can retain enclosed counters.
_BLOCK={
 'A':'00 04 15 25 34 30/0,2.5 3,2.5',
 'B':'00 05 35 3,2.5 0,2.5/3,2.5 30 00',
 'C':'35 05 00 30','D':'00 05 35 30 00',
 'G':'35 05 00 30 3,2.5 1.5,2.5',
 'J':'05 35 30 00 01','O':'00 05 35 30 00',
 'P':'00 05 35 3,2.5 0,2.5','Q':'00 05 35 30 00/1.6,1.4 30',
 'R':'00 05 35 3,2.5 0,2.5/1.6,2.5 30',
 'S':'35 05 0,2.5 3,2.5 30 00', 'U':'05 00 30 35',
 '0':'0.2,0 0.2,5 2.8,5 2.8,0 0.2,0',
 '2':'05 35 3,2.5 0,2.5 00 30','3':'05 35 30 00/0.8,2.5 3,2.5',
 '5':'35 05 0,2.5 3,2.5 30 00', '6':'35 05 00 30 3,2.5 0,2.5',
 '8':'00 05 35 30 00/0,2.5 3,2.5','9':'3,2.5 0,2.5 05 35 30 00',
}
# Narrow, open-letter signage, without stencil bridges.
_COMPACT={'I':'1.5,0 1.5,5','J':'2.6,5 2.6,0 0.4,0 0.4,1',
          'M':'00 05 1.5,2.5 35 30','W':'05 0.65,0 1.5,2.5 2.35,0 35',
          '1':'0.5,4 1.5,5 1.5,0','7':'05 35 1.3,0'}
# Chamfered motorsport lettering with a forward slant.
_RACING={'A':'00 04 15 25 34 30/0,2 3,2',
         'M':'00 05 1.5,3 35 30','N':'00 05 35 30/05 30',
         'V':'05 02 1,0 2,0 32 35','W':'05 01 10 1.5,2.5 20 31 35',
         'Z':'05 35 32 02 00 30','I':'0.5,5 2.5,5/1.5,5 1.5,0/0.5,0 2.5,0'}
# Stroke terminals for an upright serif style. Short serifs stay within the
# design grid; they are fused into the same engraved letter.
_SERIF={'A':'0.2,0 1.5,5 2.8,0/0,0 0.8,0/2.2,0 3,0/0.7,1.9 2.3,1.9',
 'H':'0.45,0 0.45,5/2.55,0 2.55,5/0.45,2.5 2.55,2.5/00 0.95,0/05 0.95,5/2.05,0 30/2.05,5 35',
 'I':'0.4,5 2.6,5/1.5,5 1.5,0/0.4,0 2.6,0',
 'L':'0.45,5 0.45,0 30 3,0.65/05 1,5',
 'T':'04 05 35 34/1.5,5 1.5,0/0.6,0 2.4,0',
 'N':'0.45,0 0.45,5 2.55,0 2.55,5/00 0.9,0/05 0.9,5/2.1,5 35',
 'E':'0.4,0 0.4,5 35 34/0.4,2.5 2.3,2.5/2.3,2.1 2.3,2.9/0.4,0 30 31',
 'F':'0.4,0 0.4,5 35 34/0.4,2.5 2.3,2.5/2.3,2.1 2.3,2.9/00 1,0',
 'P':'0.4,0 0.4,5 25 34 3,3.4 2,2.5 0.4,2.5/00 1,0',
 'R':'0.4,0 0.4,5 25 34 3,3.4 2,2.5 0.4,2.5/2,2.5 30/00 1,0',
 'M':'0.4,0 0.4,5 1.5,2 2.6,5 2.6,0/00 0.85,0/2.15,0 30',
 'U':'0.45,5 0.45,1 1,0 2,0 2.55,1 2.55,5/05 0.95,5/2.05,5 35',
 'V':'0.3,5 1.5,0 2.7,5/05 0.9,5/2.1,5 35',
 '1':'0.6,4 1.5,5 1.5,0/0.5,0 2.5,0'}

# Chamfered instrument-panel lettering with wide horizontal terminals.
_AEROSPACE={
 'A':'00 04 15 25 34 30/0,2 3,2',
 'B':'00 05 25 34 3,3.3 2.3,2.5 0,2.5/2.3,2.5 3,1.7 31 20 00',
 'C':'35 15 04 01 10 30','D':'00 05 25 34 31 20 00',
 'G':'35 15 04 01 10 30 3,2.5 1.5,2.5',
 'J':'35 31 20 10 01','M':'00 05 1.5,3 35 30',
 'N':'00 05 30 35','O':'10 01 04 15 25 34 31 20 10',
 'P':'00 05 25 34 3,3 2.3,2.5 0,2.5',
 'Q':'10 01 04 15 25 34 31 20 10/1.8,1.4 30',
 'R':'00 05 25 34 3,3 2.3,2.5 0,2.5/1.8,2.5 30',
 'S':'35 15 04 0,3.3 1,2.5 2,2.5 3,1.7 31 20 00',
 'U':'05 01 10 20 31 35','V':'05 02 1.5,0 32 35',
 'W':'05 01 10 1.5,2.5 20 31 35', 'Z':'05 35 0,1 00 30',
 '0':'10 01 04 15 25 34 31 20 10/0.5,1 2.5,4',
 '2':'05 25 34 3,3 00 30','3':'05 25 34 3,3 2,2.5 1,2.5/2,2.5 3,2 31 20 00',
 '7':'05 35 3,4 1,0','8':'10 01 0,1.7 1,2.5 0,3.3 04 15 25 34 3,3.3 2,2.5 3,1.7 31 20 10/1,2.5 2,2.5',
}
# Open, angular glyphs inspired by instrument displays rather than stencils.
_CYBER={
 'A':'00 04 15 35 30/0,2.5 3,2.5','B':'00 05 25 3,3.5 0,2.5/0,2.5 3,1.5 20 00',
 'C':'35 15 03 00 30','D':'00 05 15 33 31 20 00',
 'E':'35 15 04 00 30/0,2.5 2.4,2.5','F':'35 15 04 00/0,2.5 2.4,2.5',
 'G':'35 15 03 00 30 3,2.5 2,2.5','H':'00 05/30 35/0,3 3,2',
 'I':'1.5,5 1.5,0','J':'35 31 20 00','K':'00 05/35 0,2 30',
 'L':'05 01 10 30','M':'00 05 1.5,3 35 30','N':'00 04 15 30 35',
 'O':'00 04 15 35 31 20 00','P':'00 05 35 33 22 02',
 'Q':'00 04 15 35 31 20 00/1.5,1.5 30','R':'00 05 35 33 22 02/22 30',
 'S':'35 15 03 23 32 20 00','T':'05 35/1.5,5 1.5,0',
 'U':'05 00 20 31 35','V':'05 02 1.5,0 35','W':'05 00 1.5,2 30 35',
 'X':'05 30/00 35','Y':'05 1.5,2 35/1.5,2 1.5,0','Z':'05 35 00 30',
 '0':'00 04 15 35 31 20 00','1':'15 10','2':'05 35 33 02 00 30',
 '3':'05 35 30 00/1,2.5 3,2.5','4':'05 03 33/35 30','5':'35 05 03 23 32 20 00',
 '6':'35 15 03 00 30 32 02','7':'05 35 1,0','8':'00 05 35 30 00/0,2.5 3,2.5','9':'30 35 05 03 33',
}
# DIN-like upright signage: vertical strokes and softened-looking corners
# achieved with a small number of cutter segments.
_INDUSTRIAL={
 'A':'00 04 0.7,5 2.3,5 34 30/0,2.4 3,2.4',
 'C':'3,4.4 2.4,5 0.6,5 0,4.2 0,0.8 0.6,0 2.4,0 3,0.6',
 'D':'00 05 2,5 3,4 3,1 2,0 00','G':'3,4.4 2.4,5 0.6,5 0,4.2 0,0.8 0.6,0 30 3,2.4 1.6,2.4',
 'I':'1.5,0 1.5,5','J':'2.7,5 2.7,0.8 2.1,0 0.6,0 01',
 'O':'0.6,0 0,0.8 0,4.2 0.6,5 2.4,5 3,4.2 3,0.8 2.4,0 0.6,0',
 'P':'00 05 2.3,5 3,4.3 3,3.2 2.3,2.5 0,2.5',
 'R':'00 05 2.3,5 3,4.3 3,3.2 2.3,2.5 0,2.5/1.8,2.5 30',
 'S':'3,4.5 2.5,5 0.6,5 0,4.3 0,3.3 0.7,2.5 2.3,2.5 3,1.7 3,0.7 2.4,0 0.5,0 0,0.5',
 'U':'05 0,0.8 0.6,0 2.4,0 3,0.8 35','1':'0.5,4 1.5,5 1.5,0',
 '7':'05 35 1,0/0.9,2.5 2.8,2.5',
}
_EXTENDED={**_BLOCK,'A':'00 2,5 35 30/0.8,2 3,2',
 'I':'05 35/1.5,5 1.5,0/00 30','M':'00 05 1.5,1.8 35 30',
 'O':'0.5,0 00 05 35 30 0.5,0','V':'05 1,0 2,0 35',
 'W':'05 0.8,0 1.5,3.5 2.2,0 35','Y':'05 1.5,2 35/12 10',
 '0':'0.4,0 04 0.4,5 2.6,5 34 31 2.6,0 0.4,0'}
# Narrow signage uses few terminals and slightly flattened bowls.
_NARROW={**_COMPACT,'A':'00 1,5 2,5 30/0.6,2 2.4,2',
 'B':'00 05 25 35 3,2.5 0,2.5/3,2.5 30 00','C':'35 05 00 30',
 'D':'00 05 25 34 31 20 00','O':'00 05 35 30 00',
 'P':'00 05 35 3,2.5 0,2.5','R':'00 05 35 3,2.5 0,2.5/1.4,2.5 30',
 'U':'05 00 30 35','0':'00 05 35 30 00/0.5,1 2.5,4'}
# Square, heavily slanted race numbers and lettering.
_RACE_BLOCK={**_BLOCK,'A':'00 03 25 35 30/0,2 3,2',
 'M':'00 05 1.5,3.5 35 30','N':'00 05 30 35','V':'05 02 2,0 35',
 'W':'05 00 1.5,2.8 30 35','X':'05 30/00 35','Z':'05 35 00 30',
 '1':'05 25 20','4':'05 02 32/35 30','7':'05 35 32 10'}
# Digital numerals have chamfered ends and consistent horizontal mid-bars.
_DIGITAL={**_AEROSPACE,
 'A':'00 04 15 25 34 30/0,2.5 3,2.5','B':'05 01 10 20 31 32 2,2.5 0,2.5/2,2.5 33 34 25 15 05',
 'D':'05 01 10 20 31 34 25 15 05','G':'35 15 04 01 10 20 31 32 1.5,2',
 'I':'05 35/1.5,5 1.5,0/00 30','J':'35 31 20 10 01',
 'M':'00 04 15 1.5,3 25 34 30','N':'00 05 30 35',
 'P':'00 04 15 25 34 33 2.5,2.5 0,2.5','R':'00 04 15 25 34 33 2.5,2.5 0,2.5/1.5,2.5 30',
 '0':'10 01 04 15 25 34 31 20 10','1':'2,5 2,0','2':'15 25 34 33 2.5,2.5 0.5,2.5 02 01 10 30',
 '3':'05 25 34 33 2.5,2.5 0.8,2.5/2.5,2.5 32 31 20 00',
 '4':'05 03 0.5,2.5 3,2.5/35 30','5':'35 15 04 03 0.5,2.5 2.5,2.5 32 31 20 00',
 '6':'35 15 04 01 10 20 31 32 2.5,2.5 0,2.5','7':'05 35 3,4 1.2,0',
 '8':'10 01 04 15 25 34 31 20 10/0,2.5 3,2.5','9':'30 34 25 15 04 03 0.5,2.5 3,2.5',
}
_SLAB={**_SERIF,'A':'0.4,0 1.5,5 2.6,0/00 1.1,0/1.9,0 30/0.8,2 2.2,2',
 'B':'0.45,0 0.45,5 25 34 3,3.3 2.3,2.5 0.45,2.5/2.3,2.5 3,1.7 31 20 0.45,0/05 1,5/00 1,0',
 'C':'35 34/35 15 04 01 10 30 31','D':'0.45,0 0.45,5 25 34 31 20 0.45,0/05 1,5/00 1,0',
 'H':'0.5,0 0.5,5/2.5,0 2.5,5/0.5,2.5 2.5,2.5/00 1,0/05 1,5/20 30/25 35',
 'K':'0.5,0 0.5,5/05 1,5/00 1,0/2.5,5 0.5,2.5 2.5,0/25 35/20 30',
 'S':'35 34/35 15 04 0,3.4 1,2.5 2,2.5 3,1.6 31 20 00 01',
 'W':'0.3,5 0.9,0 1.5,3 2.1,0 2.7,5/05 0.9,5/2.1,5 35',
 'X':'0.4,5 2.6,0/0.4,0 2.6,5/05 0.85,5/00 0.85,0/2.15,5 35/2.15,0 30',
 'Y':'0.4,5 1.5,2.5 2.6,5/1.5,2.5 1.5,0/05 0.85,5/2.15,5 35/0.7,0 2.3,0',
 'Z':'04 05 35 00 30 31'}

_OVERRIDES={'Block engraving':_BLOCK,'Compact engraving':_COMPACT,
            'Racing engraving':_RACING,'Serif engraving':_SERIF,
            'Aerospace engraving':_AEROSPACE,'Cyber engraving':_CYBER,
            'Industrial engraving':_INDUSTRIAL,'Extended engraving':_EXTENDED,
            'Narrow engraving':_NARROW,'Reverse italic engraving':_AEROSPACE,
            'Rounded italic engraving':_INDUSTRIAL,'Racing block engraving':_RACE_BLOCK,
            'Digital engraving':_DIGITAL,'Slab serif engraving':_SLAB}


def _point(value):
    return tuple(map(float,value.split(','))) if ',' in value else (float(value[0]),float(value[1]))


def _paths(text,font):
    if not isinstance(text,str) or not 1<=len(text)<=24 or not text.strip() or any(c not in _GLYPHS for c in text):
        raise ValueError('Text requires 1–24 characters: A–Z, 0–9, spaces, hyphen, underscore or period.')
    overrides=_OVERRIDES.get(font,{})
    return tuple(tuple(tuple(_point(pt) for pt in path.split())
                       for path in overrides.get(c,_GLYPHS[c]).split('/') if path) for c in text)


def dimensions(text,font,stroke):
    _paths(text,font)
    if font not in ENGRAVING_FONTS or not math.isfinite(stroke) or not 1<=stroke<=10:
        raise ValueError('Engraving stroke diameter must be 1–10 mm (R0.5 minimum).')
    _,min_width,min_height,gap=_STYLES[font]
    n=len(text)
    return (n*(min_width+1.)+(n-1)*gap)*stroke,(min_height+1.)*stroke


def _capsule(a,b,r):
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    if length<1e-9:
        x,y=a;u,v=(x+r,y),(x-r,y)
        return (('arc',u,(x,y+r),v),('arc',v,(x,y-r),u))
    ux,uy=dx/length,dy/length;nx,ny=-uy*r,ux*r
    a0=(a[0]-nx,a[1]-ny);b0=(b[0]-nx,b[1]-ny)
    a1=(a[0]+nx,a[1]+ny);b1=(b[0]+nx,b[1]+ny)
    return (('line',a0,b0),('arc',b0,(b[0]+ux*r,b[1]+uy*r),b1),
            ('line',b1,a1),('arc',a1,(a[0]-ux*r,a[1]-uy*r),a0))


def _soften(points):
    """Small quadratic bends in the centreline, still cut by a round tool.

    Closed paths use cyclic neighbours; open strokes retain both terminals.
    Two samples per bend avoid a dense BRep for such small engraving.
    """
    closed=points[0]==points[-1]
    pts=points[:-1] if closed else points
    out=[]
    for i,b in enumerate(pts):
        if not closed and i in (0,len(pts)-1):
            out.append(b);continue
        a,c=pts[i-1],pts[(i+1)%len(pts)]
        u=tuple(b[k]+.24*(a[k]-b[k]) for k in (0,1))
        v=tuple(b[k]+.24*(c[k]-b[k]) for k in (0,1))
        mid=tuple((u[k]+2*b[k]+v[k])*.25 for k in (0,1))
        out.extend((u,mid,v))
    if closed:out.append(out[0])
    return tuple(out)


@lru_cache(maxsize=192)
def engraving_groups(text,font,w,h,stroke):
    minimum_w,minimum_h=dimensions(text,font,stroke)
    if not (math.isfinite(w) and math.isfinite(h)) or w<minimum_w-1e-8 or h<minimum_h-1e-8:
        raise ValueError(f'Engraving requires at least {minimum_w:.2f} × {minimum_h:.2f} mm at this stroke diameter. Use Fit lettering to CNC rules.')
    paths=_paths(text,font);n=len(text);slant,_,_,gap_factor=_STYLES[font]
    span=3.+5*abs(slant);gap=gap_factor*stroke;cell=(w-(n-1)*gap)/n
    sx=(cell-stroke)/span;sy=(h-stroke)/5.;r=stroke/2
    output=[]
    for i,glyph in enumerate(paths):
        x0=-w/2+i*(cell+gap)+r;y0=-h/2+r
        group=[];seen=set()
        for path in glyph:
            points=tuple((x0+(x+slant*y-min(0.,5*slant))*sx,y0+y*sy) for x,y in path)
            if font in ('Rounded engraving','Rounded italic engraving') and len(points)>2:
                points=_soften(points)
            for a,b in zip(points,points[1:] or points):
                key=tuple(sorted((a,b)))
                if key not in seen:group.append(_capsule(a,b,r));seen.add(key)
        if group:output.append(tuple(group))
    return tuple(output)
