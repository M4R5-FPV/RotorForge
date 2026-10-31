"""Refresh side-guard diagrams for full plate-edge height coverage."""
from guide_style import *
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,plate_levels
from freecad.rotorforge.flex_preview import flex_path
p=Parameters(FPVEnabled=True)
base=replace(p,FlexSideGuards=True,FlexGuardExtendFront=True,StandoffCount='6 (3 pairs)',StandoffPair3Y=-94.,StandoffPair3Width=28,MidReachMode='Custom',MidRearReach=102.,TopReachMode='Custom',TopRearReach=102.)
gallery('ElectronicsGuards.png',[cell('Side view / full plate-edge coverage',(flex_path(base,'ElectronicsGuardLeft'),TPU))],1,rowheight=430,cellwidth=1600)
closure=replace(p,FlexSideGuards=True,FlexGuardCloseFront=True,FlexGuardClearance=0.,FlexGuardWireEnabled=True)
gallery('GuardFrontClosure.png',[cell('Foremost-post forward closure',(flex_path(closure,'ElectronicsGuardLeft'),TPU))],1,rowheight=440,cellwidth=1600)
gallery('GuardUSBAccess.png',[cell('Adjustable USB opening',(flex_path(replace(base,FlexGuardUSBEnabled=True,FlexGuardUSBY=-6.),'ElectronicsGuardLeft'),TPU))],1,rowheight=400,cellwidth=1600)
gallery('GuardWireOpenings.png',[cell('Wire exits extend through the lower lip',(flex_path(replace(base,FlexGuardWireEnabled=True),'ElectronicsGuardLeft'),TPU))],1,rowheight=400,cellwidth=1600)
gallery('GuardVentSections.png',[cell('VTX section only',(flex_path(replace(base,FlexGuardFCVents=False),'ElectronicsGuardLeft'),TPU)),cell('Independent VTX and FC vents',(flex_path(replace(base,FlexGuardVentShape='Hexagons',FlexGuardFCVentShape='Rounded slots'),'ElectronicsGuardLeft'),TPU))],1,rowheight=350,cellwidth=1600)
cells=[]
for mode in ('2 plates','3 plates'):
 q=replace(p,PlateDesign=mode);levels=plate_levels(q);low=0. if mode=='2 plates' else levels['mid_z'];deck=levels['deck_z'];roof=levels['top_z'];top=roof+q.TopThickness
 wall=polygon_path(((20,low),(22,low),(22,deck),(20,roof),(20,top),(18,top),(18,roof),(20,deck)))
 lower=rect(-20,low,40,deck-low);upper=rect(-18,roof,36,q.TopThickness)
 cells.append(cell(mode+' / carrier underside to top face',(rect(-.8,deck,1.6,roof-deck),GREY),(lower,BLUE),(upper,BLUE),(wall,TPU),box=QtCore.QRectF(-23,low-2,48,top-low+4)))
gallery('GuardPlateHeight.png',cells,2,rowheight=530,cellwidth=850)
