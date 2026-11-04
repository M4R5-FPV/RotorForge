"""Portable rear layout, fixed elevation and symmetric outward yaw."""
import math
from .mount_bands import rear_pair,rear_guard_band
from .parameters import plate_levels

def antenna_dimensions(p):
 bore=p.FlexAntennaBore or (6.5 if p.FlexAntennaConnector in ('SMA','RP-SMA') else 4. if p.FlexAntennaConnector=='u.FL' else 3.)
 bulkhead=p.FlexAntennaConnector in ('SMA','RP-SMA')
 length=p.FlexAntennaBulkheadThickness if bulkhead else (p.FlexAntennaSocketLength or 6.)
 radius=max(6.,bore/2+p.FlexAntennaSocketWall) if bulkhead else bore/2+p.FlexAntennaSocketWall
 angle=math.radians(p.FlexAntennaTilt)
 return bore,length,radius,length*math.sin(angle)+2*radius*math.cos(angle),angle

def antenna_standoff_bore(p):
 return p.FlexAntennaStandoffBore or p.StandoffDiameter+p.FlexAntennaFit

def antenna_seat(p):
 from dataclasses import replace
 if not p.FlexRearAntenna:p=replace(p,FlexRearAntenna=True)
 from .mount_bands import rear_mount_seats
 a=rear_mount_seats(p)
 return a['vtx_z'],a['vtx_top'],a['vtx_space']

def antenna_layout(p):
 pair=rear_pair(p)
 if len(pair)!=2:raise ValueError('Rear antenna mount needs two rear standoffs.')
 bottom,top,space=antenna_seat(p)
 available=top-bottom;height=min(p.FlexAntennaGripHeight,available)
 bore,length,radius,extent,angle=antenna_dimensions(p)
 z=bottom+height/2;y=pair[0]['point'][1]-p.FlexAntennaReach;holders=[]
 for sign in ((-1,1) if p.FlexAntennaCount=='2 antennas' else (0,)):
  yaw=sign*math.pi/6
  axis=(math.cos(angle)*math.sin(yaw),-math.cos(angle)*math.cos(yaw),math.sin(angle))
  anchor=(sign*p.FlexAntennaSpacing/2,y-p.FlexAntennaHolderOffset,z)
  root_length=length if p.FlexAntennaConnector in ('SMA','RP-SMA') else 6.
  start=tuple(anchor[i]-axis[i]*root_length/2 for i in range(3))
  centre=tuple(start[i]+axis[i]*length/2 for i in range(3))
  holders.append(dict(centre=centre,axis=axis,start=start,anchor=anchor))
 x0,x1=(s['point'][0] for s in pair);rear=pair[0]['point'][1];width=p.FlexAntennaBarWidth
 if p.FlexAntennaBarShape=='Curved':points=[(x0+(x1-x0)*i/24,rear-p.FlexAntennaReach*math.sin(math.pi*i/24)) for i in range(25)]
 elif p.FlexAntennaBarShape=='Triangle':points=[(x0,rear),(0,y),(x1,rear),(x0,rear)]
 else:points=[(x0,rear),(x0,y),(x1,y),(x1,rear)]
 return dict(bulkhead=p.FlexAntennaConnector in ('SMA','RP-SMA'),pair=pair,top=top,bottom=bottom,available=available,height=height,z0=bottom,bore=bore,length=length,radius=radius,extent=extent,holders=holders,points=points,width=width)

def validate_antenna(p):
 errors=[]
 if min(p.FlexAntennaTopGap,p.FlexAntennaGuardGap)<0:errors.append("VTX mounting gaps must not be negative.")
 if p.FlexAntennaConnector in ('SMA','RP-SMA') and not 2<=p.FlexAntennaBulkheadThickness<=5:errors.append('SMA bulkhead tab thickness must be between 2 and 5 mm; match the pigtail thread length.')
 if not -80<=p.FlexAntennaHolderOffset<=100:errors.append("Holder offset must be between -80 and 100 mm.")
 if not 0<=p.FlexAntennaTilt<=90:errors.append("Antenna tilt must be between 0 and 90 degrees.")
 if p.FlexAntennaStandoffBore and p.FlexAntennaStandoffBore<p.StandoffDiameter:errors.append("Antenna standoff hole must not be smaller than the modeled standoff diameter.")
 if min(p.FlexAntennaGripWall,p.FlexAntennaSocketWall)<1.2:errors.append('Antenna grip and socket walls must be at least 1.2 mm.')
 if p.FlexAntennaGripHeight<4:errors.append('Antenna grip height must be at least 4 mm.')
 if not 4<=p.FlexAntennaBarWidth<=20:errors.append('Antenna bar width must be between 4 and 20 mm.')
 if not 8<=p.FlexAntennaReach<=80:errors.append('Antenna rearward reach must be between 8 and 80 mm.')
 if not 0<=p.FlexAntennaFit<=1:errors.append('Antenna standoff fit must be between 0 and 1 mm.')
 try:
  a=antenna_layout(p)
  if not a['bulkhead'] and p.FlexAntennaHolderStyle=='Side-entry clip' and not .15<=p.FlexAntennaRetainingLip<=a['bore']*.35:errors.append('Stem retaining lip must be at least 0.15 mm and no more than 35% of the bore diameter.')
  if a['available']<4:errors.append('Less than 4 mm of upper rear standoff space remains for antenna grips.')
  if a['bore']<1 or a['length']<2:errors.append('Antenna bore must be at least 1 mm and holder length at least 2 mm.')
  if len(a['holders'])==2 and p.FlexAntennaSpacing<2*a['radius']+1:errors.append('Dual antenna spacing must leave at least 1 mm between holders.')
 except (ValueError,IndexError) as e:errors.append(str(e))
 return errors
