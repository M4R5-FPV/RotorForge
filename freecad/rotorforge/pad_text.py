"""Portable, printable blind lettering on the LiPo pad (mm; +Y = front).

Uses RotorForge's original glyph centre lines, independently of CNC limits.
No installed fonts, FreeCAD document objects or Qt are needed for layout.
"""
import math
from functools import lru_cache
from .engraving_text import ENGRAVING_FONTS, _STYLES, _paths, _soften, _capsule

PAD_TEXT_FONTS=tuple(f.removesuffix(' engraving') for f in ENGRAVING_FONTS)
PAD_TEXT_STYLES=('Regular','Bold','Italic','Bold italic')
PAD_TEXT_POSITIONS=('Across front','Across rear','Rear to front','Front to rear','Across centre')
PAD_TEXT_FIELDS=frozenset(('LiPoPadTextEnabled','LiPoPadText','LiPoPadTextFont','LiPoPadTextStyle',
    'LiPoPadTextPosition','LiPoPadTextHeight','LiPoPadTextWidthScale','LiPoPadTextStroke',
    'LiPoPadTextSpacing','LiPoPadTextDepth','LiPoPadTextMarginAlong','LiPoPadTextMarginAcross',
    'LiPoPadTextInset','LiPoPadTextOffsetX','LiPoPadTextOffsetY'))

@lru_cache(maxsize=128)
def local_letters(text,font,style,height,width_scale,stroke,spacing):
    """Return centred stroke groups, effective stroke diameter and actual extents."""
    text=text.strip().upper()
    font=font+' engraving'
    glyphs=_paths(text,font)
    r=stroke*(1.45 if 'bold' in style.lower() else 1)/2
    if height<=2*r+.2:raise ValueError('LiPo lettering height is too small for this stroke/style.')
    slant=_STYLES[font][0]+(.20 if 'italic' in style.lower() else 0)
    sy=(height-2*r)/5
    # Each of the original font styles has its own proportional width.
    sx=sy*width_scale/100*_STYLES[font][1]/2.4
    groups=[];cursor=0.
    for glyph in glyphs:
        if not glyph:
            cursor+=height*.4*width_scale/100+spacing
            continue
        paths=[]
        for raw in glyph:
            points=tuple(((x+slant*y)*sx,y*sy) for x,y in raw)
            if font in ('Rounded engraving','Rounded italic engraving') and len(points)>2:points=_soften(points)
            paths.append(points)
        xmin=min(x for path in paths for x,y in path)
        xmax=max(x for path in paths for x,y in path)
        group=[];seen=set()
        for path in paths:
            pts=tuple((x-xmin+cursor+r,y+r) for x,y in path)
            for a,b in zip(pts,pts[1:] or pts):
                key=tuple(sorted((a,b)))
                if key not in seen:group.append((a,b));seen.add(key)
        groups.append(tuple(group));cursor+=xmax-xmin+2*r+spacing
    xmin=min(x for g in groups for ab in g for x,y in ab)-r
    xmax=max(x for g in groups for ab in g for x,y in ab)+r
    ymin=min(y for g in groups for ab in g for x,y in ab)-r
    ymax=max(y for g in groups for ab in g for x,y in ab)+r
    cx,cy=(xmin+xmax)/2,(ymin+ymax)/2
    return tuple(tuple(((a[0]-cx,a[1]-cy),(b[0]-cx,b[1]-cy)) for a,b in g) for g in groups),r,xmax-xmin,ymax-ymin

def validate_pad_text(p):
    if not (p.LiPoPadEnabled and p.LiPoPadTextEnabled):return []
    for key,lo,hi in (('Height',1,50),('WidthScale',25,200),('Stroke',.2,3),('Spacing',.1,10),
                      ('Depth',.1,10),('MarginAlong',0,50),('MarginAcross',0,50),('Inset',0,100),
                      ('OffsetX',-300,300),('OffsetY',-300,300)):
        v=getattr(p,'LiPoPadText'+key)
        if not math.isfinite(v) or not lo<=v<=hi:return [f'LiPo pad text {key} must be between {lo:g} and {hi:g}.']
    if p.LiPoPadTextDepth>p.LiPoPadThickness-.3+1e-9:
        return ['LiPo pad lettering must leave at least 0.3 mm continuous backing. Reduce text depth or increase pad thickness.']
    try:local_letters(p.LiPoPadText,p.LiPoPadTextFont,p.LiPoPadTextStyle,p.LiPoPadTextHeight,p.LiPoPadTextWidthScale,p.LiPoPadTextStroke,p.LiPoPadTextSpacing)
    except (ValueError,TypeError) as exc:return ['LiPo pad lettering: '+str(exc)]
    return []

def text_layout(p,bounds):
    """Fixed frame-facing anchors, then signed XY adjustment; underside readable."""
    if not (p.LiPoPadEnabled and p.LiPoPadTextEnabled):return None
    issues=validate_pad_text(p)
    if issues:raise ValueError(issues[0])
    groups,r,w,h=local_letters(p.LiPoPadText,p.LiPoPadTextFont,p.LiPoPadTextStyle,p.LiPoPadTextHeight,p.LiPoPadTextWidthScale,p.LiPoPadTextStroke,p.LiPoPadTextSpacing)
    xmin,ymin,xmax,ymax=bounds;cx,cy=(xmin+xmax)/2,(ymin+ymax)/2
    pos=p.LiPoPadTextPosition;longitudinal=pos in ('Rear to front','Front to rear')
    if pos=='Across front':cy=ymax-p.LiPoPadTextInset-h/2
    elif pos=='Across rear':cy=ymin+p.LiPoPadTextInset+h/2
    cx+=p.LiPoPadTextOffsetX;cy+=p.LiPoPadTextOffsetY
    sign=-1 if p.BatteryMount=='Bottom plate' else 1
    def pt(a):
        x,y=a
        if pos=='Rear to front':x,y=-y,x
        elif pos=='Front to rear':x,y=y,-x
        return cx+sign*x,cy+y
    placed=tuple(tuple((pt(a),pt(b)) for a,b in g) for g in groups)
    # The reserved area follows the text orientation, but is always an XY box.
    u=w/2+p.LiPoPadTextMarginAlong;v=h/2+p.LiPoPadTextMarginAcross
    if longitudinal:u,v=v,u
    return placed,r,(cx-u,cy-v,cx+u,cy+v)

def text_cutters(layout,z,height):
    """Exact swept round strokes, fused per character; disjoint letters."""
    import FreeCAD as App
    import Part
    groups,r,_=layout
    solids=[]
    for group in groups:
        strokes=[]
        for a,b in group:
            edges=[]
            for segment in _capsule(a,b,r):
                pts=[App.Vector(x,y,z) for x,y in segment[1:]]
                edges.append(Part.makeLine(*pts) if segment[0]=='line' else Part.Arc(*pts).toShape())
            strokes.append(Part.Face(Part.Wire(edges)).extrude(App.Vector(0,0,height)))
        letter=strokes[0] if len(strokes)==1 else strokes[0].multiFuse(strokes[1:]).removeSplitter()
        if letter.isNull() or not letter.isValid():raise ValueError('LiPo pad text geometry is invalid; increase letter height or reduce stroke.')
        solids.extend(letter.Solids)
    return solids
