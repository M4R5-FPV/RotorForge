"""Current side-view geometry, compared in the shared guide style."""
from dataclasses import replace
from guide_style import *
from freecad.rotorforge.flex_preview import flex_path
from freecad.rotorforge.parameters import Parameters,plate_levels
from freecad.rotorforge.protection_layout import guard_layout
p=Parameters(PlateDesign='2 plates',FPVEnabled=True,FlexSideGuards=True,FlexGuardStyle='Solid',
             FlexGuardWireEnabled=True,StandoffHeight=35.,StandoffLength=150.,
             StandoffWidth=42.,TopWidth=54.,BodyWidth=58.,VTXOffsetY=-50.,
             VTXLength=28.,VTXPattern='20 x 20 mm')
cells=[]
for title,mode,opening in [('Plate-edge wrap / two wire exits','Plate-edge wrap',False),
                         ('Between plates / one wire opening','Between plates',False),
                         ('Between plates / VTX clearance enabled','Between plates',True)]:
 q=replace(p,FlexGuardFitMode=mode,FlexGuardVTXOpening=opening);g=guard_layout(q)[0];lv=plate_levels(q)
 items=[(rect(-80,0,160,q.BottomThickness),LIGHT,LIGHT),
        (rect(-80,lv['top_z'],160,q.TopThickness),LIGHT,LIGHT),
        (flex_path(q,g['role']),TPU,TPU)]
 if opening:items.append((rect(q.VTXOffsetY-q.VTXLength/2,lv['deck_z'],q.VTXLength,q.VTXHeight),None,TEAL))
 cells.append(cell(title,*items,box=QtCore.QRectF(-83,-4,166,47)))
gallery('GuardOptions089.png',cells,cols=1,rowheight=350,cellwidth=1200)
