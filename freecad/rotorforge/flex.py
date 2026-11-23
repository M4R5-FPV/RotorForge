"""Portable flexible-part layouts. Never imports CAD or Qt in the live editor."""
import math
from .flex_options import FLEX_ROLES

def soft_camera(p):return p.FPVEnabled and p.FlexCameraMode!='Hard mount'
def camera_inner(p):
 # All TPU mounting modes retain the exact same camera-facing wall plane.
 # Soft pads are locally recessed INTO that wall; captured cassettes only
 # replace stock in their through-openings. Do not move the whole inner wall.
 if getattr(p, 'CameraCageStyle', '') == 'TPU cage':
  return float(p.CameraWidth)/2 + float(p.CameraTPUHardClearance)
 return p.CameraWidth/2+(p.FlexPadThickness-p.FlexPadPreload if soft_camera(p) else p.CameraSideClearance/2)
def tpu_structural_inner(p):
    """Stable TPU structural wall datum, independent of attachment mode.

    The removable soft interface occupies the space inside this wall. For a
    direct screw mount, a local integrated camera bearing land bridges the
    difference to the real camera side, avoiding a full-height wall move.
    """
    if getattr(p, 'CameraCageStyle', '') != 'TPU cage':
        return camera_inner(p)
    return float(p.CameraWidth)/2 + float(p.CameraTPUHardClearance)


def tpu_hard_bearing(p):
    """Camera-side X and supporting shell X (unsigned, millimetres)."""
    camera_face=float(p.CameraWidth)/2+float(p.CameraTPUHardClearance)
    return camera_face,tpu_structural_inner(p)


def flex_roles(p):
 return (FLEX_ROLES[:2] if soft_camera(p) else ())+tuple('MotorProtector'+n for n in ('FrontRight','FrontLeft','RearLeft','RearRight') if p.FlexMotorProtectors)+tuple('ElectronicsGuard'+n for n in ('Left','Right') if p.FlexSideGuards)+(('FrontBumper',) if p.FlexFrontBumper and p.CameraCageStyle!='TPU cage' else ())+(('RearAntennaMount',) if p.FlexRearAntenna else ())+(('ELRSAntennaMount',) if p.FlexELRSEnabled else ())+(('ActionCameraMount',) if p.FPVEnabled and p.CameraCageStyle=='TPU cage' and p.ActionCamMountEnabled else ())

def insert_rect(p):
 from .fpv import camera_position_y,camera_pivot_height
 return (camera_position_y(p),p.BottomThickness+camera_pivot_height(p),p.FlexInsertWidth,p.FlexInsertHeight)

def validate_flex(p):
 errors=[];warnings=[]
 if p.ActionCamMountEnabled and p.FPVEnabled and p.CameraCageStyle=='TPU cage':
  if not 2.0<=p.ActionCamMountBaseThickness<=6.0:
   errors.append('HD action-camera mount base thickness must be 2–6 mm.')
  if not 10.0<=p.ActionCamMountHingeHeight<=30.0:
   errors.append('HD action-camera hinge height must be 10–30 mm above the base.')
  if not -12.0<=p.ActionCamMountOffsetY<=12.0:
   errors.append('HD action-camera hinge offset must be between -12 and +12 mm.')
 if p.FlexELRSEnabled:
  from .elrs_layout import validate_elrs
  errors.extend(validate_elrs(p))
 if p.FlexRearAntenna:
  from .antenna_layout import validate_antenna
  errors.extend(validate_antenna(p))
 numeric=[k for k in p.__dataclass_fields__ if k.startswith('Flex') and k not in ('FlexAntennaHolderOffset','FlexGuardStrapY1','FlexGuardStrapY2','FlexGuardUSBY','FlexGuardWireFrontY','FlexGuardWireRearY','FlexGuardVentBoundaryOffset','FlexGuardVTXY','FlexGuardVTXZ','FlexGuardVTXVentZOffset','FlexGuardFCVentZOffset') and isinstance(getattr(p,k),(float,int)) and not isinstance(getattr(p,k),bool)]
 if any(not math.isfinite(getattr(p,k)) or getattr(p,k)<0 for k in numeric):return ['Flexible-part dimensions must be finite and non-negative.'],[]
 if any(not math.isfinite(getattr(p,k)) for k in ('FlexAntennaHolderOffset','FlexGuardStrapY1','FlexGuardStrapY2','FlexGuardUSBY','FlexGuardWireFrontY','FlexGuardWireRearY','FlexGuardVentBoundaryOffset','FlexGuardVTXY','FlexGuardVTXZ','FlexGuardVTXVentZOffset','FlexGuardFCVentZOffset')):errors.append('Opening offsets must be finite.')
 if p.FlexBumperVariant=='Integrated camera cage bumper' and p.FlexFrontBumper:
  if not p.FPVEnabled:errors.append('Integrated camera cage bumper requires FPV camera enabled.')
  if p.CameraCageStyle=='TPU cage':errors.append('Integrated bumper requires flat camera side plates; disable the separate TPU camera cage.')
 if p.FlexBumperCameraFrontProjection > 8.:errors.append('Camera cage front projection must be between 0 and 8 mm.')
 if p.FlexBumperCameraBlendReach > 20:errors.append('Camera shoulder inward reach must be 0 (full) or between 1 and 20 mm.')
 if 0<p.FlexBumperCameraBlendReach<1:errors.append('Camera shoulder inward reach must be 0 (full) or at least 1 mm.')
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
 if soft_camera(p) and p.FPVSystemProfile!='DJI O4 Air Unit Pro':
  from .fpv import camera_mounts,camera_wall_interior,camera_angles,camera_centre_offset,camera_screw_offsets
  if p.FlexPadThickness<=p.FlexPadPreload or p.FlexPadThickness<.5:errors.append('Camera pad thickness must exceed compression and be at least 0.5 mm.')
  if p.FlexPadPreload>p.FlexPadThickness*.4:errors.append('Camera pad compression must not exceed 40% of its free thickness.')
  width,height=(p.FlexInsertWidth,p.FlexInsertHeight) if p.FlexCameraMode=='Captured inserts' else (p.FlexPadWidth,p.FlexPadHeight)
  if min(width,height)<p.CameraSideHoleDiameter+2*p.MinimumWeb:errors.append('Camera pad/insert needs more material around its screw pattern.')
  points=[(y+dy,z+dz) for angle in camera_angles(p)
          for dy,dz in (camera_centre_offset(p,angle),)
          for y,z in camera_screw_offsets(p,angle)]
  web=p.CameraSideHoleDiameter/2+p.MinimumWeb
  needed_w=2*(max(abs(y) for y,z in points)+web)
  needed_h=2*(max(abs(z) for y,z in points)+web)
  if width+1e-7<needed_w or height+1e-7<needed_h:
   mode='Captured insert' if p.FlexCameraMode=='Captured inserts' else 'Compression pad'
   errors.append(f'{mode} dimensions {width:g} x {height:g} mm cannot surround the measured camera '
                 f'screw pattern across the configured tilt(s). Needs at least '
                 f'{needed_w:.1f} x {needed_h:.1f} mm including screw bore and web. '
                 'Use Fit camera to enlarge the pad/insert or enter the measured screw spacing. '
                 'Changing preview tilt alone does not alter an adjustable mount range.')
  if p.FlexInterfaceShape=='Side plate outline' and p.CameraCageStyle!='TPU cage':
   from .plate_profiles import polygon_interior_distance
   outline=camera_interface_polygon(p,width,height)
   for angle in camera_angles(p):
    dy,dz=camera_centre_offset(p,angle)
    cy,cz,_,_=insert_rect(p)
    for y,z in camera_screw_offsets(p,angle):
     if polygon_interior_distance((cy+y+dy,cz+z+dz),outline)<p.CameraSideHoleDiameter/2+p.MinimumWeb:
      if not any('scaled side-plate interface' in msg for msg in errors):
       errors.append('The scaled side-plate interface needs more material around the tilt paths; enlarge its length or height.')
  if p.FlexCameraMode=='Captured inserts' and not .25<=p.FlexInsertCornerRadius<=min(width,height)/2:errors.append('Insert opening corner radius must be at least 0.25 mm and no more than half the smaller opening dimension.')
  # The TPU cage is lofted from the *finished* top/bottom plate contours,
  # not camera_mounts().wall_profile. That legacy polygon must never be
  # used to reject its isolation pocket before the actual solid is built.
  # The resulting cage solid is still validated after the pocket Boolean.
  if p.CameraCageStyle!='TPU cage':
   cy,cz,_,_=insert_rect(p);margin=0.
   for mount in camera_mounts(p):
    if any(camera_wall_interior((cy+y,cz+z),mount)<p.CameraCageEdgeWeb-1e-7 for y in (-width/2-margin,width/2+margin) for z in (-height/2-margin,height/2+margin)):
     errors.append('Camera pad/insert needs more supporting side-plate area; enlarge the cage or move the camera within it.')
  if p.FlexCameraMode=='Captured inserts' and (p.FlexInsertLip<.5 or not 0<=p.FlexInsertFit<=.25):errors.append('Captured inserts require a retaining lip of at least 0.5 mm and a fit clearance from 0 to 0.25 mm.')
  if p.CameraCageStyle=='Carbon side plates' and p.FlexCameraMode=='Captured inserts':
   from .carbon_insert_recess import recess_span
   for mount,sign in zip(camera_mounts(p),(-1,1)):
    try:recess_span(p,mount,sign)
    except ValueError as exc:errors.append(str(exc))
  if p.CameraCageStyle=='TPU cage' and p.FlexCameraMode=='Captured inserts':
   # The TPU cage uses full-wall removable cassettes. The optional outer
   # flange recess requires a real axial land, not the removed blind pocket.
   from .tpu_captured_layout import insert_x_spans
   for mount,sign in zip(camera_mounts(p),(-1,1)):
    try:insert_x_spans(p,mount,sign)
    except ValueError as exc:errors.append(str(exc))

 if soft_camera(p) and p.FPVSystemProfile=='DJI O4 Air Unit Pro':
  from .fpv import camera_mounts,camera_wall_interior
  if p.FlexPadThickness<=p.FlexPadPreload or p.FlexPadThickness<.5:errors.append('O4 insert contact thickness must exceed preload and be at least 0.5 mm.')
  if (p.O4InsertDiameter/2-p.FlexInsertFit if p.FlexCameraMode=='Captured inserts' else p.O4PadDiameter/2)-p.CameraSideHoleDiameter/2<.8:errors.append('O4 inserts need at least 0.8 mm around each screw bore.')
  if p.FlexCameraMode=='Captured inserts' and (p.FlexInsertLip<.5 or p.O4InsertDiameter+2*p.FlexInsertLip>=16.):errors.append('O4 insert lips must be at least 0.5 mm and leave the two inserts separate.')
  for mount in camera_mounts(p):
   from .cage_extensions import o4_tracks,track_points
   required=(p.O4InsertDiameter/2+p.FlexInsertLip if p.FlexCameraMode=='Captured inserts' else p.O4PadDiameter/2)+p.CameraCageEdgeWeb
   centres=tuple(v for track in o4_tracks(mount) for v in track_points(track))
   actual=min(camera_wall_interior(v,mount) for v in centres)
   if actual<required-1e-7:
    errors.append(f'O4 insert opening needs {required:.2f} mm from screw centre to cage edge; '
                  f'only {actual:.2f} mm is available. Use Fit camera to resize the O4 soft inserts/pads, '
                  f'or switch to a hard mount; retain at least 2 mm of cage edge web.')
 if p.FlexMotorProtectors:
  if min(p.FlexProtectorWall,p.FlexProtectorFloor)<.8:errors.append('Motor protector walls and floor must be at least 0.8 mm.')
  if p.FlexProtectorFit>2:errors.append('Motor protector fit clearance must be at most 2 mm.')
  if p.FlexProtectorLandingStyle not in ('Full perimeter (original)', 'Tip-only inward taper'):
   errors.append('Unknown motor protector landing foot style.')
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
 if p.CameraCageStyle=='TPU cage' and p.FlexInterfaceShape!='Rounded rectangle':
  from .tpu_isolation_layout import tpu_interface_polygon
  return tpu_interface_polygon(p,width,height)
 if p.FlexInterfaceShape!='Side plate outline':return ()
 from .fpv import camera_mounts
 cy,cz,_,_=insert_rect(p);points=camera_mounts(p)[0]['wall_profile']
 lo=min(y for y,z in points);hi=max(y for y,z in points)
 low=min(z for y,z in points);high=max(z for y,z in points)
 return tuple((cy+(y-(lo+hi)/2)*width/(hi-lo),cz+(z-(low+high)/2)*height/(high-low)) for y,z in points)

