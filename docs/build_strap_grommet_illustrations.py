"""Guide diagrams using actual side-preview paths and native grommet dimensions."""
from guide_style import *
from dataclasses import replace
import json,sys
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.protection_layout import guard_layout,guard_strap_windows
from freecad.rotorforge.flex_preview import flex_path
p=Parameters(FlexSideGuards=True,FlexGuardStyle='Solid',FlexGuardStraps=True)
cells=[]
for count,edge,title in (('1 strap','Top edge','One upper passage'),('2 straps','Top edge','Two upper passages'),('1 strap','Bottom edge','Custom lower passage')):
 q=replace(p,FlexGuardStrapCount=count,FlexGuardStrapEdge=edge,FlexGuardStrapAuto=(edge=='Top edge'),FlexGuardStrapY1=8.)
 g=guard_layout(q)[0];path=flex_path(q,'ElectronicsGuardLeft');items=[(path,TPU)]
 for window in guard_strap_windows(q,g):
  tool=rect(window['y']-window['width']/2,window['bottom'],window['width'],window['height']);items.append((tool,None,TEAL))
 cells.append(cell(title,*items))
gallery('GuardStrapOpenings.png',cells,1,rowheight=290,cellwidth=1400)
v=json.loads(Path(sys.argv[1]).read_text());t,cap,low,high,join=v['dimensions'];height=v['height'];neck,outer,bore=v['neck'],v['outer'],v['bore'];items=[]
# Two opposing necks, with collars above and below their own PCB.
for base,end,z in ((0,join,low),(join,height,high)):
 shape=rect(-neck,base,2*neck,end-base)
 shape=shape.united(rect(-outer,z-cap,2*outer,cap)).united(rect(-outer,z+t,2*outer,cap))
 shape=shape.subtracted(rect(-bore,-1,2*bore,height+4));items.append((shape,TPU))
 for x in (-8,neck):items.append((rect(x,z,8-neck,t),'#14523b'))
# Reference screw and upper nut show the unchanged seating height.
items.insert(0,(rect(-1.5,-1,3,height+4),'#888d94'))
items.append((rect(-2.75,height,5.5,2.4).subtracted(rect(-1.5,height,3,2.4)),TPU))
line=QtGui.QPainterPath();line.moveTo(-outer-.8,join);line.lineTo(outer+.8,join);items.append((line,None,TEAL))
gallery('StackGrommetContact.png',[cell('ESC neck up / FC neck down',*items)],1,rowheight=820,cellwidth=1100)
