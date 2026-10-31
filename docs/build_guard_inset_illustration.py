"""Nominal right-wall cross sections using the production placement helpers."""
from dataclasses import replace
from guide_style import *
from freecad.rotorforge.parameters import Parameters,plate_levels
from freecad.rotorforge.protection_layout import guard_layout,guard_wall_inner_x
p=Parameters(FlexSideGuards=True,FlexGuardStyle='Solid',FlexGuardClearance=1.)
cells=[]
for mode in ('Plate-edge wrap','Between plates'):
 q=replace(p,FlexGuardFitMode=mode);g=guard_layout(q)[1];lv=plate_levels(q)
 xb=guard_wall_inner_x(q,q.BodyWidth/2,1);xt=guard_wall_inner_x(q,q.TopWidth/2,1);w=q.FlexGuardWall
 if mode=='Between plates':points=[(xb,g['z']),(xb+w,g['z']),(xt+w,g['top']),(xt,g['top'])]
 else:points=[(xb,g['z']),(xb+w,g['z']),(xb+w,g['inner_bottom']),(xt+w,g['inner_top']),
              (xt+w,g['top']),(xt,g['top']),(xt,g['inner_top']),(xb,g['inner_bottom'])]
 items=[(rect(12,lv['mid_z'],q.BodyWidth/2-12,lv['deck_z']-lv['mid_z']),LIGHT,LIGHT),
        (rect(12,lv['top_z'],q.TopWidth/2-12,q.TopThickness),LIGHT,LIGHT),
        (polygon_path(points),TPU,TPU)]
 cells.append(cell(mode,*items,box=QtCore.QRectF(11,lv['mid_z']-2,20,lv['top_z']+q.TopThickness-lv['mid_z']+4)))
gallery('GuardInset0891.png',cells,cols=2,rowheight=700,cellwidth=650)
