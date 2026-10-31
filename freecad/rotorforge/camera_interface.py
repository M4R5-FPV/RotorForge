"""Portable rounded camera-opening geometry and insert retention layers."""
import math

def lip_sides(p):
 """Inside faces the camera; outside faces away from it (mirrored per side)."""
 return (p.FlexInsertLipSide in ('Inside only','Both sides'),
         p.FlexInsertLipSide in ('Outside only','Both sides'))

def profile_corners(p,width,height):
 from .flex import insert_rect,camera_interface_polygon
 cy,cz,_,_=insert_rect(p);points=camera_interface_polygon(p,width,height)
 if not points:points=((cy-width/2,cz-height/2),(cy+width/2,cz-height/2),(cy+width/2,cz+height/2),(cy-width/2,cz+height/2))
 radius=p.FlexInsertCornerRadius if p.FlexCameraMode=='Captured inserts' else (0. if p.FlexInterfaceShape=='Side plate outline' else min(2.,width/4,height/4))
 corners=[]
 for before,vertex,after in zip(points[-1:]+points[:-1],points,points[1:]+points[:1]):
  la=math.dist(before,vertex);lb=math.dist(after,vertex)
  u=tuple((a-b)/la for a,b in zip(before,vertex));v=tuple((a-b)/lb for a,b in zip(after,vertex))
  alpha=math.acos(max(-1.,min(1.,sum(a*b for a,b in zip(u,v)))))
  if radius<=0 or alpha<1e-7 or math.pi-alpha<1e-7:
   corners.append(dict(start=vertex,end=vertex,mid=vertex,c1=vertex,c2=vertex,radius=0.));continue
  r=min(radius,.45*min(la,lb)*math.tan(alpha/2))
  distance=r/math.tan(alpha/2);bisector=tuple(a+b for a,b in zip(u,v));norm=math.hypot(*bisector)
  centre=tuple(a+b/norm*r/math.sin(alpha/2) for a,b in zip(vertex,bisector))
  start=tuple(a+b*distance for a,b in zip(vertex,u));end=tuple(a+b*distance for a,b in zip(vertex,v))
  toward=tuple(a-b for a,b in zip(vertex,centre));length=math.hypot(*toward)
  mid=tuple(a+b/length*r for a,b in zip(centre,toward))
  k=4/3*math.tan((math.pi-alpha)/4)*r
  corners.append(dict(start=start,end=end,mid=mid,c1=tuple(a-b*k for a,b in zip(start,u)),c2=tuple(a-b*k for a,b in zip(end,v)),radius=r))
 return tuple(corners)

def insert_layers(p,mount,sign):
 """X spans plus profile offsets; the central neck always stays in the plate."""
 a,b=mount['plate_x'];inner=b if sign<0 else a
 face=sign*(p.CameraWidth/2-p.FlexPadPreload);lo,hi=sorted((face,inner))
 inside,outside=lip_sides(p);outer_thickness=max(.8,p.FlexPadThickness/2)
 layers=[dict(kind='contact',x=lo,thickness=hi-lo,offset=p.FlexInsertLip if inside else -p.FlexInsertFit),
         dict(kind='neck',x=a,thickness=b-a,offset=-p.FlexInsertFit)]
 if outside:layers.append(dict(kind='outside lip',x=b if sign>0 else a-outer_thickness,thickness=outer_thickness,offset=p.FlexInsertLip))
 return tuple(layers)
