"""Pure lower rear mount layout. No CAD runs during editing."""
import math
from .mount_bands import rear_pair,rear_guard_band

def elrs_bore(p):return p.FlexELRSStandoffBore or p.StandoffDiameter+p.FlexELRSFit

def elrs_seat(p):
 from dataclasses import replace
 if not p.FlexELRSEnabled:p=replace(p,FlexELRSEnabled=True)
 pair=rear_pair(p)
 if len(pair)!=2:raise ValueError('ELRS mount needs two rear standoffs.')
 from .mount_bands import rear_mount_seats
 a=rear_mount_seats(p);low=a['elrs_z'];available=a['elrs_space'];height=a['elrs_height']
 return dict(pair=pair,z0=low,top=low+available,available=available,height=height)

def elrs_layout(p):
 a=elrs_seat(p);pair=a['pair'];rear=pair[0]['point'][1];radius=p.FlexELRSAntennaDiameter/2+p.FlexELRSHookWall
 y=rear-p.FlexELRSReach;z=a['z0']+max(a['height']/2,radius)
 # The backbone attaches to the front of the hooks; the centre coax exits behind it.
 bar_y=y+radius+p.FlexELRSBarWidth/2-.5
 x0,x1=(s['point'][0] for s in pair)
 if p.FlexELRSBarShape=='Curved':points=[(x0+(x1-x0)*i/24,rear-(rear-bar_y)*math.sin(math.pi*i/24)) for i in range(25)]
 elif p.FlexELRSBarShape=='Triangle':points=[(x0,rear),(0,bar_y),(x1,rear),(x0,rear)]
 else:points=[(x0,rear),(x0,bar_y),(x1,bar_y),(x1,rear)]
 y-=p.FlexELRSHookReach
 a['support_size']=min(p.FlexELRSHookWidth,a['height'])
 a.update(rear=rear,y=y,z=z,radius=radius,bar_y=bar_y,points=points,hooks=[(-p.FlexELRSHookSpacing/2,y,z),(p.FlexELRSHookSpacing/2,y,z)])
 return a

def validate_elrs(p):
 errors=[]
 if min(p.FlexELRSHeightOffset,p.FlexELRSGuardGap)<0:errors.append("ELRS mounting gaps must not be negative.")
 for ok,msg in [
  (p.FlexELRSGripHeight>=4,'ELRS grip height must be at least 4 mm.'),
  (p.FlexELRSGripWall>=1.2 and p.FlexELRSHookWall>=1.2,'ELRS grip and hook walls must be at least 1.2 mm.'),
  (4<=p.FlexELRSBarWidth<=20,'ELRS bar width must be between 4 and 20 mm.'),
  (2<=p.FlexELRSHookWidth<=15,'ELRS hook width must be between 2 and 15 mm.'),
  (1.5<=p.FlexELRSAntennaDiameter<=12,'ELRS antenna diameter must be between 1.5 and 12 mm.'),
  (p.FlexELRSHookSpacing>=p.FlexELRSHookWidth+4,'ELRS hooks need at least 4 mm between them for the T junction.'),
  (.15<=p.FlexELRSRetainingLip<=p.FlexELRSAntennaDiameter*.35,'ELRS retaining lip must be 0.15 mm to 35% of antenna diameter.'),
  (0<=p.FlexELRSFit<=1,'ELRS standoff fit allowance must be 0 to 1 mm.'),
  (not p.FlexELRSStandoffBore or p.FlexELRSStandoffBore>=p.StandoffDiameter,'ELRS hole must not be smaller than the standoff.')]:
  if not ok:errors.append(msg)
 try:
  a=elrs_layout(p)
  if not 0<=p.FlexELRSHookReach<=80:errors.append('ELRS hook rearward offset must be between 0 and 80 mm.')
  diameter=p.FlexELRSPassThroughDiameter
  stock=2*min(a['z']-a['z0'],a['z0']+a['height']-a['z'])-2
  if diameter and not 1<=diameter<=stock+1e-6:errors.append('ELRS pass-through must leave at least 1 mm above and below it; reduce its diameter or increase grip height.')
  if a['available']<4:errors.append('Less than 4 mm remains below the guard/VTX grips for the ELRS mount; reduce its height offset or increase standoff height.')
  if not a['radius']+p.FlexELRSBarWidth/2+2<=p.FlexELRSReach<=100:errors.append('ELRS rearward reach must clear the hook and bar radii and be at most 100 mm.')
 except (ValueError,IndexError) as e:errors.append(str(e))
 return errors
