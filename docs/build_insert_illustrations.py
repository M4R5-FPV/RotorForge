"""Rounded captured openings and mirrored retaining lip faces."""
from guide_style import *
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.camera_interface import insert_layers
from freecad.rotorforge.fpv import camera_mounts
from freecad.rotorforge.flex_preview import camera_interface_path,flex_path
p=Parameters(FPVEnabled=True,FlexCameraMode='Captured inserts',StandoffHeight=35.)
cells=[]
for mode in ('Both sides','Outside only','Inside only'):
 q=replace(p,FlexInsertLipSide=mode);items=[(rect(-q.CameraWidth/2,-q.CameraHeight/2,q.CameraWidth,q.CameraHeight),GREY)]
 h=q.FlexInsertHeight;full=h+2*q.FlexInsertLip+5
 for sign,mount in zip((-1,1),camera_mounts(q)):
  a,b=mount['plate_x'];items.extend([(rect(a,-full/2,b-a,(full-h)/2),BLUE),(rect(a,h/2,b-a,(full-h)/2),BLUE)])
  for layer in insert_layers(q,mount,sign):
   height=h+2*layer['offset'];items.append((rect(layer['x'],-height/2,layer['thickness'],height),TPU))
 cells.append(cell(mode,*items))
gallery('CameraInsertLipFaces.png',cells,3,rowheight=460,cellwidth=550)
cells=[]
for outline in ('Rounded rectangle','Side plate outline'):
 q=replace(p,FlexInterfaceShape=outline,CameraAutoExtend=False,CameraTopRearOffset=4.)
 cells.append(cell(outline,(flex_path(q,'CameraPadLeft'),TPU),(camera_interface_path(q,q.FlexInsertWidth,q.FlexInsertHeight),None,TEAL)))
gallery('FlexibleInterfaceShapes.png',cells,2,rowheight=510,cellwidth=850)
