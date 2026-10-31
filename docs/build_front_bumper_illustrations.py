"""Bottom shoe plan styles and retaining section in the shared material palette."""
from guide_style import *
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.front_bumper import BUMPER_SHAPES
from freecad.rotorforge.airflow_gui import finished_part_path
from freecad.rotorforge.bumper_preview import front_bumper_path,front_bumper_plan
p=Parameters(FlexFrontBumper=True)
cells=[]
for style in BUMPER_SHAPES:
 q=replace(p,FlexBumperShape=style);outer=front_bumper_path(q);b=outer.boundingRect()
 clip=rect(b.left()-1,b.top(),b.width()+2,b.height()+1)
 carbon=finished_part_path(q,'BottomPlate').intersected(clip)
 cells.append(cell(style,(outer,TPU),(carbon,LIGHT),(front_bumper_plan(q),TPU)))
gallery('FrontBumperShapes.png',cells[:6],2,rowheight=320)
gallery('FrontBumperMoreShapes.png',cells[6:12],2,rowheight=320)
gallery('FrontBumperNewShapes.png',cells[12:],2,rowheight=320)
# Fore/aft section through the shoe centre. Rear is open at the left.
carbon=rect(-20,0,20,p.BottomThickness)
low=-p.FlexBumperFit-p.FlexBumperSole;high=p.BottomThickness+p.FlexBumperFit+p.FlexBumperLip
shoe=rect(-20,low,26.2,high-low)
shoe=shoe.subtracted(rect(-21,-p.FlexBumperFit,21+p.FlexBumperFit,p.BottomThickness+2*p.FlexBumperFit))
shoe=shoe.subtracted(rect(-21,p.BottomThickness+p.FlexBumperFit,21-p.FlexBumperOverlap,5))
gallery('FrontBumperSection.png',[cell('Rear open at left; front wall at right',(shoe,TPU),(carbon,LIGHT))],1,rowheight=340,cellwidth=1600)
# Width changes only the toe; identical carbon/fit in all three examples.
cells=[]
for width,label in ((24.,'24 mm toe'),(0.,'Automatic toe'),(80.,'80 mm toe')):
 q=replace(p,FlexBumperWidth=width,FlexBumperShape='Chamfered shoe')
 outer=front_bumper_path(q);b=outer.boundingRect();carbon=finished_part_path(q,'BottomPlate').intersected(rect(b.left()-1,b.top(),b.width()+2,b.height()+1))
 cells.append(cell(label,(outer,TPU),(carbon,LIGHT),(front_bumper_plan(q),TPU),box=QtCore.QRectF(-42,b.top()-1,84,b.height()+2)))
gallery('FrontBumperWidth.png',cells,3,rowheight=480,cellwidth=650)
