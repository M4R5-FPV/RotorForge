"""Top-front camera recesses from the same geometry as the live editor."""
from guide_style import *
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,top_bounds
from freecad.rotorforge.bottom_nose import CAMERA_FRONT_SHAPES
from freecad.rotorforge.airflow_gui import finished_part_path
p=Parameters(FPVEnabled=True,StandoffHeight=35.)
rear,front=top_bounds(p);crop=rect(-p.TopWidth/2-1,front-43,p.TopWidth+2,44)
def end(q):return finished_part_path(q,'TopPlate').intersected(crop)
gallery('TopFrontCameraShapes.png',[cell(n.replace('Camera ','').capitalize(),(end(replace(p,TopFrontShape=n)),BLUE)) for n in CAMERA_FRONT_SHAPES],2,rowheight=350)
# All comparison panels share a fixed crop and fit scale; front is upward.
box=QtCore.QRectF(-p.TopWidth/2-1,front-43,p.TopWidth+2,44)
items=[]
for label,shape,setback in [('Straight front','Straight',0.),('Recess + 6 mm setback','Camera U recess',6.)]:
 q=replace(p,TopFrontShape=shape,TopFrontSetback=setback)
 items.append(cell(label,(end(q),BLUE),(rect(-p.TopWidth/2,front-.1,p.TopWidth,.2),TEAL),box=box))
gallery('TopFrontSetback.png',items,2,rowheight=420,cellwidth=800)
