"""Camera tab shoulder cutter relief detail in the shared guide palette."""
from guide_style import *
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.airflow_gui import finished_part_path
from freecad.rotorforge.fpv import camera_mounts,camera_position_y,camera_tab_reliefs
cells=[]
for diameter in (1.,2.):
 p=Parameters(FPVEnabled=True,CameraTabCutterDiameter=diameter)
 m=camera_mounts(p)[0];cy=camera_position_y(p);tab=m['tabs_y'][0]-cy
 bounds=QtCore.QRectF(tab-5,-p.BottomThickness,10,7)
 shape=finished_part_path(p,'CameraMountLeft').intersected(rect(bounds.x(),bounds.y(),bounds.width(),bounds.height()))
 items=[(shape,BLUE)]
 for y,z,r in camera_tab_reliefs(p,m)[:2]:items.append((ellipse(y-cy,z-p.BottomThickness,r),None,TEAL))
 cells.append(cell(f'{diameter:g} mm cutter / {diameter/2:g} mm body relief',*items,box=bounds))
gallery('CameraTabReliefs.png',cells,2,rowheight=480,cellwidth=850)
