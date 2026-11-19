"""Portable blind-pocket lettering: swept engraving strokes and exact dot profiles.
No system fonts or third-party packages are required.
"""
import math
from functools import lru_cache

from .engraving_text import ENGRAVING_FONTS, engraving_groups, dimensions as engraving_dimensions
TEXT_FONTS=ENGRAVING_FONTS+('Dot matrix',)
LEGACY_STENCIL_FONTS={'Block stencil':'Block engraving','Compact stencil':'Compact engraving'}
DOT={
'A':'010/101/111/101/101','B':'110/101/110/101/110','C':'111/100/100/100/111','D':'110/101/101/101/110','E':'111/100/110/100/111','F':'111/100/110/100/100','G':'111/100/101/101/111','H':'101/101/111/101/101','I':'111/010/010/010/111','J':'111/001/001/101/111','K':'101/101/110/101/101','L':'100/100/100/100/111','M':'10001/11011/10101/10001/10001','N':'10001/11001/10101/10011/10001','O':'111/101/101/101/111','P':'111/101/111/100/100','Q':'1110/1010/1010/1110/0001','R':'110/101/110/101/101','S':'111/100/111/001/111','T':'111/010/010/010/010','U':'101/101/101/101/111','V':'10001/10001/01010/01010/00100','W':'10001/10001/10101/10101/01010','X':'10001/01010/00100/01010/10001','Y':'10001/01010/00100/00100/00100','Z':'111/001/010/100/111',
'0':'111/101/101/101/111','1':'010/110/010/010/111','2':'111/001/111/100/111','3':'111/001/111/001/111','4':'101/101/111/001/001','5':'111/100/111/001/111','6':'111/100/111/101/111','7':'111/001/010/010/010','8':'111/101/111/101/111','9':'111/101/111/001/111','-':'000/000/111/000/000','_':'000/000/000/000/111','.':'000/000/000/000/010',' ':'000/000/000/000/000'}


def _dot_layout(text,w,h):
    if not isinstance(text,str) or not 1<=len(text)<=24 or not text.strip() or any(c not in DOT for c in text):
        raise ValueError('Text requires 1–24 characters: A–Z, 0–9, spaces, hyphen, underscore or period.')
    glyphs=tuple(tuple(DOT[c].split('/')) for c in text)
    columns=sum(len(g[0]) for g in glyphs)+len(glyphs)-1
    return w/columns,h/5,glyphs,columns


def check_text_web(pattern,web=0.):
    font=pattern['text_font'];dot=pattern.get('text_dot',1.)
    if web>0:raise ValueError('CNC text is available only as blind pockets.')
    if font in ENGRAVING_FONTS:
        engraving_groups(pattern['text'],font,pattern['width'],pattern['length'],dot)
        return
    if font!='Dot matrix':raise ValueError('Select a built-in CNC text font.')
    if not math.isfinite(dot) or not 1.<=dot<=10.:raise ValueError('Dot diameter must be 1–10 mm.')
    dx,dy,_,_=_dot_layout(pattern['text'],pattern['width'],pattern['length'])
    if min(dx,dy)-dot<.1-1e-8:
        raise ValueError('Dot matrix needs 0.1 mm between dots; use Fit lettering to CNC rules or reduce dot diameter.')


@lru_cache(maxsize=192)
def _profiles(text,font,w,h,dot):
    if font in ENGRAVING_FONTS:
        return tuple(profile for group in engraving_groups(text,font,w,h,dot) for profile in group)
    check_text_web(dict(text=text,text_font=font,width=w,length=h,text_dot=dot))
    dx,dy,glyphs,_=_dot_layout(text,w,h);offset=0;result=[];r=dot*.5
    for rows in glyphs:
        for j,row in enumerate(rows):
            for i,c in enumerate(row):
                if c!='1':continue
                x=(offset+i+.5)*dx-w/2;y=(4-j+.5)*dy-h/2
                a,b=(x+r,y),(x-r,y)
                result.append((('arc',a,(x,y+r),b),('arc',b,(x,y-r),a)))
        offset+=len(rows[0])+1
    return tuple(result)


def text_profiles(pattern):
    return _profiles(pattern['text'],pattern['text_font'],pattern['width'],pattern['length'],pattern.get('text_dot',1.))


def minimum_text_size(pattern,web=0.):
    if web>0:raise ValueError('CNC text is available only as blind pockets.')
    font=pattern['text_font'];dot=pattern.get('text_dot',1.)
    if font in ENGRAVING_FONTS:
        w,h=engraving_dimensions(pattern['text'],font,dot)
    elif font=='Dot matrix':
        if not math.isfinite(dot) or not 1.<=dot<=10.:raise ValueError('Dot diameter must be 1–10 mm.')
        _,_,_,columns=_dot_layout(pattern['text'],1.,1.)
        w,h=(dot+.1)*columns,(dot+.1)*5
    else:raise ValueError('Select a built-in CNC text font.')
    return tuple(math.ceil((v+.01)*100-1e-8)/100 for v in (w,h))
