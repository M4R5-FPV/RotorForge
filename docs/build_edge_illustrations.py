"""Shared-math front/rear end profiles and camera-tab controls, in the guide palette."""
from guide_style import *
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.bottom_nose import NOSE_SHAPES,REAR_SHAPES
from freecad.rotorforge.airflow_gui import profile_path,finished_part_path
from freecad.rotorforge.fpv import camera_mounts,camera_position_y
p=Parameters(PlateDesign='2 plates')
def outline(n,end):
 prefix='BottomNose' if end=='Front' else 'TopRear'
 role='BottomPlate' if end=='Front' else 'TopPlate'
 q=replace(p,**{prefix+'Shape':n})
 path=profile_path(q,role,50,-70,70,5)
 crop=rect(-26,50 if end=='Front' else -71,52,21)
 return path.intersected(crop)
for filename,names in [('BottomNoseShapes.png',NOSE_SHAPES[:8]),('BottomNoseMoreShapes.png',NOSE_SHAPES[8:])]:
 gallery(filename,[cell(n,(outline(n,'Front'),BLUE)) for n in names],2,rowheight=260)
gallery('RearEdgeShapes.png',[cell(n,(outline(n,'Rear'),BLUE)) for n in REAR_SHAPES],2,rowheight=220)
p=Parameters(FPVEnabled=True)
q=replace(p,CameraTabBottomRearOffset=1.,CameraTabBottomFrontOffset=-1.,CameraTabTopRearOffset=.75,CameraTabTopFrontOffset=-.75)
cells=[]
for label,r in [('Zero offsets',p),('Independent offsets',q)]:
 m=camera_mounts(r)[0]
 shape=finished_part_path(r,'CameraMountLeft')
 # Flattened side plates use frame Y horizontally and absolute Z vertically.
 items=[(shape,BLUE)]
 for ys,z,h in ((m['tabs_y'],0,r.BottomThickness),(m['top_tabs_y'],m['z1'],r.TopThickness)):
  for y in ys:items.append((rect(y-camera_position_y(r)-r.CameraTabLength/2,z-r.BottomThickness,r.CameraTabLength,h),TEAL))
 cells.append(cell(label,*items))
gallery('CameraTabOffsets.png',cells,2,rowheight=500)
