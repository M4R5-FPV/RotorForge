"""Portable flexible-part layouts. Never imports CAD or Qt in the live editor."""
import math
from .flex_options import FLEX_ROLES

def soft_camera(p):return p.FPVEnabled and p.FlexCameraMode!='Hard mount'
def camera_inner(p):
 return p.CameraWidth/2+(p.FlexPadThickness-p.FlexPadPreload if soft_camera(p) else p.CameraSideClearance/2)
def flex_roles(p):
 return (FLEX_ROLES[:2] if soft_camera(p) else ())+tuple('MotorProtector'+n for n in ('FrontRight','FrontLeft','RearLeft','RearRight') if p.FlexMotorProtectors)+tuple('ElectronicsGuard'+n for n in ('Left','Right') if p.FlexSideGuards)+(('FrontBumper',) if p.FlexFrontBumper else ())

def insert_rect(p):
 from .fpv import camera_position_y,camera_pivot_height
 return (camera_position_y(p),p.BottomThickness+camera_pivot_height(p),p.FlexInsertWidth,p.FlexInsertHeight)

def validate_flex(p):
 errors=[];warnings=[]
 numeric=[k for k in p.__dataclass_fields__ if k.startswith('Flex') and k not in ('FlexGuardStrapY1','FlexGuardStrapY2','FlexGuardUSBY','FlexGuardWireFrontY','FlexGuardWireRearY','FlexGuardVentBoundaryOffset','FlexGuardVTXY','FlexGuardVTXZ','FlexGuardVTXVentZOffset','FlexGuardFCVentZOffset') and isinstance(getattr(p,k),(float,int)) and not isinstance(getattr(p,k),bool)]
 if any(not math.isfinite(getattr(p,k)) or getattr(p,k)<0 for k in numeric):return ['Flexible-part dimensions must be finite and non-negative.'],[]
 if any(not math.isfinite(getattr(p,k)) for k in ('FlexGuardStrapY1','FlexGuardStrapY2','FlexGuardUSBY','FlexGuardWireFrontY','FlexGuardWireRearY','FlexGuardVentBoundaryOffset','FlexGuardVTXY','FlexGuardVTXZ','FlexGuardVTXVentZOffset','FlexGuardFCVentZOffset')):errors.append('Opening offsets must be finite.')
 if p.FlexFrontBumper:
  from .parameters import bottom_bounds
  rear,front=bottom_bounds(p)
  if not 2<=p.FlexBumperReach<front-rear:errors.append('Bumper reach must be at least 2 mm and shorter than the bottom plate.')
  if min(p.FlexBumperWall,p.FlexBumperSole,p.FlexBumperLip)<.8:errors.append('Bumper wall, sole and lip must be at least 0.8 mm.')
  if not .5<=p.FlexBumperOverlap<=min(p.BodyWidth/4,p.FlexBumperReach/2):errors.append('Bumper lip overlap must fit inside the shoe reach and plate width.')
  if not 0<=p.FlexBumperFit<=1:errors.append('Bumper fit clearance must be between 0 and 1 mm.')
  if p.FlexBumperTipWidth>90 or p.FlexBumperRecess>90:errors.append('Bumper feature width and recess depth must be between 0 and 90 percent.')
  if p.FlexBumperLipReach and not 2<=p.FlexBumperLipReach<=p.FlexBumperReach:errors.append('Bumper lip capture length must be zero or between 2 mm and the shoe reach.')
  if 0<p.FlexBumperWidth<8:errors.append('Bumper toe width must be zero for automatic sizing or at least 8 mm.')
  if p.FlexBumperShape!='Follow bottom plate' and p.FlexBumperProjection<.5:errors.append('Toe projection must be at least 0.5 mm for a shaped bumper.')
 if p.FlexDensity<=0:errors.append('Flexible material density must be positive.')
 if soft_camera(p):
  from .fpv import camera_mounts,camera_wall_interior,camera_angles,camera_centre_offset,camera_screw_offsets
  if p.FlexPadThickness<=p.FlexPadPreload or p.FlexPadThickness<.5:errors.append('Camera pad thickness must exceed compression and be at least 0.5 mm.')
  if p.FlexPadPreload>p.FlexPadThickness*.4:errors.append('Camera pad compression must not exceed 40% of its free thickness.')
  width,height=(p.FlexInsertWidth,p.FlexInsertHeight) if p.FlexCameraMode=='Captured inserts' else (p.FlexPadWidth,p.FlexPadHeight)
  if min(width,height)<p.CameraSideHoleDiameter+2*p.MinimumWeb:errors.append('Camera pad/insert needs more material around its screw pattern.')
  for angle in camera_angles(p):
   dy,dz=camera_centre_offset(p,angle)
   for y,z in camera_screw_offsets(p,angle):
    if abs(y+dy)+p.CameraSideHoleDiameter/2+p.MinimumWeb>width/2 or abs(z+dz)+p.CameraSideHoleDiameter/2+p.MinimumWeb>height/2:
     errors.append('The camera pad/insert must contain the complete existing tilt screw paths; increase its length or height.')
  if p.FlexInterfaceShape=='Side plate outline':
   from .plate_profiles import polygon_interior_distance
   outline=camera_interface_polygon(p,width,height)
   for angle in camera_angles(p):
    dy,dz=camera_centre_offset(p,angle)
    cy,cz,_,_=insert_rect(p)
    for y,z in camera_screw_offsets(p,angle):
     if polygon_interior_distance((cy+y+dy,cz+z+dz),outline)<p.CameraSideHoleDiameter/2+p.MinimumWeb:errors.append('The scaled side-plate interface needs more material around the tilt paths; enlarge its length or height.')
  if p.FlexCameraMode=='Captured inserts' and not .25<=p.FlexInsertCornerRadius<=min(width,height)/2:errors.append('Insert opening corner radius must be at least 0.25 mm and no more than half the smaller opening dimension.')
  cy,cz,_,_=insert_rect(p);margin=p.FlexInsertLip if p.FlexCameraMode=='Captured inserts' else 0.
  for mount in camera_mounts(p):
   if any(camera_wall_interior((cy+y,cz+z),mount)<p.MinimumWeb for y in (-width/2-margin,width/2+margin) for z in (-height/2-margin,height/2+margin)):
    errors.append('Camera pad/insert needs more supporting side-plate area; enlarge the cage or move the camera within it.')
  if p.FlexCameraMode=='Captured inserts' and (p.FlexInsertLip<.5 or p.FlexInsertFit>=min(width,height)/4):errors.append('Insert retaining lip must be at least 0.5 mm and fit clearance smaller than a quarter of the opening.')
 if p.FlexMotorProtectors:
  if min(p.FlexProtectorWall,p.FlexProtectorFloor)<.8:errors.append('Motor protector walls and floor must be at least 0.8 mm.')
  if p.FlexProtectorFit>2:errors.append('Motor protector fit clearance must be at most 2 mm.')
 if p.FlexSideGuards:
  if p.FlexGuardCloseFront and not p.FPVEnabled:errors.append('Close sides to camera plates requires FPV camera side plates.')
  if p.FlexGuardCloseFront and not 1<=p.FlexGuardCameraOverlap<=8:errors.append('Camera plate landing length must be between 1 and 8 mm.')
  if p.FlexGuardWall<1:errors.append('Side guards need at least 1 mm wall thickness.')
  if p.FlexGuardFit>2:errors.append('Side guard post clearance must be at most 2 mm.')

  from .parameters import standoff_layouts
  rows=standoff_layouts(p);length=max(i['point'][1] for i in rows)-min(i['point'][1] for i in rows)
  if p.FlexGuardFrontInset+p.FlexGuardRearInset>=length-4*p.FlexGuardWall:errors.append('Side guard insets leave too little protective wall between the posts.')
 if p.FlexSideGuards:
  from .protection_layout import guard_layout,usb_window,guard_wire_openings,guard_strap_windows,guard_vent_sections,guard_vtx_window,guard_between_plates

  if p.FlexGuardWireEnabled and p.FlexGuardWireHeight<2:errors.append('Motor-wire openings need at least 2 mm height above the carrier.')
  for g in guard_layout(p):
   if p.FlexGuardStyle=='Vented':
    for section in guard_vent_sections(p,g):
     if not section['enabled']:continue
     if section['height']<=0 or not 1<=section['rows']<=6 or section['rows']!=round(section['rows']):errors.append(section['name']+' guard vents need positive height and one to six whole-number rows.')
     if section['web']<1.5 or section['width']<1:errors.append(section['name']+' guard vents need at least 1.5 mm webs and 1 mm width.')
     if section['front']<=section['rear']:warnings.append(section['name']+' vent section has no available length; adjust its boundary/insets or disable it.')
   if g['front']-p.FlexGuardFrontInset<=g['rear']+p.FlexGuardRearInset+4*p.FlexGuardWall:errors.append('Side guard insets leave too little wall between the chosen posts.')
   for opening in guard_wire_openings(p,g):
    y,w,h,bottom=opening['y'],opening['width'],opening['height'],opening['bottom'];margin=p.FlexGuardWall
    if min(opening.get('source_width',w),h)<2:errors.append('Motor-wire openings need at least 2 mm width and height.')
    rear=g['rear']+p.FlexGuardRearInset;front=g['front']-p.FlexGuardFrontInset
    if opening['name']=='Rear':
     # A rear exit may open through the end below a raised bearing sleeve.
     if y+w/2<=rear or y-w/2>=front:errors.append('Rear motor-wire opening must intersect the side-guard wall.')
     if y+w/2>front-margin:errors.append('Rear motor-wire opening must leave material at the forward end.')
    else:
     limit=front
     if p.FlexGuardCloseFront and p.FPVEnabled:
      from .protection_layout import closure_profile
      closure=closure_profile(p,g)
      if closure:limit=min(end for z,end in closure['sections'])
     source_y=opening.get('source_y',y);source_w=opening.get('source_width',w)
     if source_w>limit-rear:errors.append('Front motor-wire opening is wider than the available side guard.')
     if source_y+source_w/2<=rear or source_y-source_w/2>=limit:errors.append('Front motor-wire opening must intersect the side-guard wall.')
    if bottom+h>g['inner_top']-margin:errors.append('Motor-wire opening is too tall for the local side guard; reduce its height.')
    radius=(p.StandoffDiameter+p.FlexGuardFit)/2+margin
    for st,(low,high) in zip(g['stands'],g['bands']):
     reaches_post=abs(y-st['point'][1])<w/2+radius+margin
     reaches_band=bottom+h+margin>low+1e-7 and bottom-2-margin<high-1e-7
     if opening['name']!='Front' and reaches_post and reaches_band:errors.append('Motor-wire opening needs more clearance from the actual standoff grip band; lower, narrow or move it.')
    from .parameters import three_plate,mid_bounds
    if opening['name']=='Rear' and p.FlexGuardCloseFront and y-w/2<g['front']<y+w/2:errors.append('Move the motor-wire opening clear of the forward enclosure start at the foremost standoffs so it has one continuous lower edge.')
    if opening['name']=='Rear' and three_plate(p) and not (p.FlexGuardCloseFront and y-w/2>=g['front']) and y-w/2<mid_bounds(p)[1]<y+w/2:errors.append('Move the motor-wire opening clear of the mid-plate end so it has one continuous lower edge.')
   if p.FlexGuardStraps:
    margin=p.FlexGuardWall
    if p.FlexGuardStrapWidth<2 or p.FlexGuardStrapDepth<1:errors.append('Strap openings need at least 2 mm width and 1 mm depth.')
    windows=guard_strap_windows(p,g)
    if len(windows)==2 and abs(windows[0]['y']-windows[1]['y'])<p.FlexGuardStrapWidth+margin:errors.append('Leave a wall between the two strap openings, or select one strap.')
    for window in windows:
     y,w=window['y'],window['width'];low,high=window['bottom'],window['top']
     if y-w/2<g['rear']+p.FlexGuardRearInset+margin or y+w/2>g['front']-p.FlexGuardFrontInset-margin:errors.append('Strap opening must fit between the side-guard ends; move it or reduce its width.')
     local_bottom=g['z']
     from .parameters import three_plate,mid_bounds
     if three_plate(p) and y+w/2>mid_bounds(p)[1]:
      if p.FlexGuardStrapEdge=='Bottom edge':errors.append('Bottom strap openings must stay on the continuous lower carrier section; move them rearward of the mid-plate end.')
      local_bottom=max(local_bottom,g['inner_top']-10)
     if p.FlexGuardStrapDepth>g['top']-local_bottom-2*margin:errors.append('Strap opening is too deep for the local wall; retain material at the opposite edge.')
     radius=(p.StandoffDiameter+p.FlexGuardFit)/2+p.FlexGuardWall+.5
     for stand,(lo,hi) in zip(g['stands'],g['bands']):
      if abs(y-stand['point'][1])<w/2+radius and high>lo-.5 and low<hi+.5:errors.append('Strap opening must clear the standoff grip; move it or reduce width/depth.')
   window=guard_vtx_window(p,g)
   if window:
    y,z,width,height=window;low,high=z-height/2,z+height/2;margin=p.FlexGuardWall
    if min(width,height)<2:errors.append('VTX opening dimensions must be at least 2 mm.')
    if high>g['inner_top']-margin:errors.append('VTX opening must retain a top web; reduce its height, lower it or increase the plate spacing.')
    if high<=g['inner_bottom']:errors.append('VTX opening is below the usable guard wall; raise it.')
    if y+width/2<=g['rear']+p.FlexGuardRearInset or y-width/2>=g['front']-p.FlexGuardFrontInset:
     warnings.append('VTX opening is outside the side-guard wall; no clearance cut is needed there. Adjust its offset if the actual VTX extends into the guard.')
    radius=(p.StandoffDiameter+p.FlexGuardFit)/2+margin
    for stand,(a,b) in zip(g['stands'],g['bands']):
     if abs(y-stand['point'][1])<width/2+radius and high>a and low<b:
      errors.append('VTX opening intersects a standoff grip; move or resize the opening, or reposition the post.')
   window=usb_window(p,g)
   if window:
    y,z,width,height=window
    if min(width,height)<2:errors.append('USB opening dimensions must be at least 2 mm.')
    if y-width/2<g['rear']+p.FlexGuardRearInset+p.FlexGuardWall or y+width/2>g['front']-p.FlexGuardFrontInset-p.FlexGuardWall:errors.append('USB opening must stay within the extended guard ends.')
    if z-height/2<g['inner_bottom']+p.FlexGuardWall:errors.append('USB opening must leave material below it; raise it or reduce its height.')
    if z-height/2>=g['inner_top']:errors.append('USB opening is above the usable guard wall; lower its centre.')
 return list(dict.fromkeys(errors)),list(dict.fromkeys(warnings))


def camera_interface_polygon(p,width,height):
 """Plain side-wall silhouette scaled around the screw pivot; no tab tongues."""
 if p.FlexInterfaceShape!='Side plate outline':return ()
 from .fpv import camera_mounts
 cy,cz,_,_=insert_rect(p);points=camera_mounts(p)[0]['wall_profile']
 lo=min(y for y,z in points);hi=max(y for y,z in points)
 low=min(z for y,z in points);high=max(z for y,z in points)
 return tuple((cy+(y-(lo+hi)/2)*width/(hi-lo),cz+(z-(low+high)/2)*height/(high-low)) for y,z in points)

