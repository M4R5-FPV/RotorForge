"""Front pocket travel across the stepped lower edge and retained grips."""
from guide_style import *
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.flex_preview import flex_path
from freecad.rotorforge.protection_layout import guard_layout
p=Parameters(FPVEnabled=True,StandoffHeight=35.,FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardWireEnabled=True,FlexGuardWirePairs='Front',FlexGuardClearance=0.)
cells=[]
for y in (20.,24.,40.,46.):
 q=replace(p,FlexGuardWireFrontY=y);g=guard_layout(q)[0];items=[(flex_path(q,'ElectronicsGuardLeft'),TPU)]
 r=(q.StandoffDiameter+q.FlexGuardFit)/2+q.FlexGuardWall
 for stand,(lo,hi) in zip(g['stands'],g['bands']):items.append((rect(stand['point'][1]-r,lo,2*r,hi-lo),None,TEAL))
 cells.append(cell('Front offset '+str(int(y))+' mm',*items))
gallery('FrontWireTravel.png',cells,2,rowheight=360)
