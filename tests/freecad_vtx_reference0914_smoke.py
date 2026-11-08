"""Run with FreeCAD Python (FreeCADCmd), not ordinary CPython.

Checks materials, bounds, and fastener clearance for exposed and enclosed
VTX transmitter references without regenerating the entire frame.
"""
import sys
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App, Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.fpv import vtx_holes
from freecad.rotorforge.detailed_references import vtx_model

checks=[]
for video,style in (('Analog','Automatic'),('Digital','Automatic'),('Analog','Finned enclosure'),('Digital','Exposed PCB'),('Analog','Analog enclosed'),('Digital','Analog enclosed')):
 for pattern in ('20 x 20 mm','25.5 x 25.5 mm','Both (20 + 25.5 mm)'):
  p=Parameters(FPVEnabled=True,VideoSystem=video,VTXPattern=pattern,VTXWidth=36,VTXLength=36,VTXHeight=12)
  holes=tuple((x,y-p.VTXOffsetY,r) for (x,y),r,_ in vtx_holes(p))
  shape,cols=vtx_model(p.VTXWidth,p.VTXLength,p.VTXHeight,holes,video=='Digital',style)
  assert shape.isValid() and len(shape.Faces)==len(cols) and len(set(cols))>=4,(video,style,pattern)
  bb=shape.BoundBox
  assert bb.XMin>=-p.VTXWidth/2-1e-6 and bb.XMax<=p.VTXWidth/2+1e-6
  assert bb.YMin>=-p.VTXLength/2-1e-6 and bb.YMax<=p.VTXLength/2+1e-6
  assert bb.ZMin>=-1e-6 and bb.ZMax<=p.VTXHeight+1e-6
  # Make a tool through the entire VTX body; every modeled element must
  # leave the actual selected screw bore clear.
  for x,y,r in holes:
   probe=Part.makeCylinder(r, p.VTXHeight+.2,App.Vector(x,y,-.1))
   assert shape.common(probe).Volume<1e-5,(video,style,pattern,x,y)
  checks.append((video,style,pattern,len(shape.Faces),len(shape.Solids)))
print('VTX reference geometry passed:',len(checks),'cases')
