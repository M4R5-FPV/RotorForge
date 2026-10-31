"""Receiving-plate nut seats. Stack threads and threaded motor/standoff joints stay unchanged."""
import math
MODES=('External hex nut','Recessed hex nut','M3 press nut')
FIELDS={
'ArmNutMount':('External hex nut','Arm nut retention','Retention for non-shared arm bolts only. Shared arm/standoff bolts keep their threaded standoffs.',MODES),
'StackPressNuts':(False,'FC stack press nuts','Use M3 press nuts in the stack carrier. Places the stack directly on the exposed flange, overriding manual spacer height; upper conventional nuts follow the stack.'),
'NutRecessDepth':(.8,'Hex nut recess depth','Partial hexagonal pocket depth into the receiving face. At least 1 mm of plate thickness must remain.'),
'NutRecessClearance':(.15,'Nut pocket fit allowance','Added to hex nut across-flats width and to circular flange-pocket diameter. Not a radial allowance.'),
'PressNutBore':(4.22,'M3 press-nut mounting bore','Through-hole diameter in the receiving plate. Default KF2/KFS2 M3 mounting hole: 4.22 mm (+0.08 mm). Other FPV inserts may need 4.55 mm; use the purchased insert drawing.'),
'PressNutFlangeDiameter':(5.56,'Press-nut flange diameter','Default KF2/KFS2 M3 E dimension, used for the reference and optional flange pocket.'),
'PressNutFlangeHeight':(1.5,'Press-nut flange height','Default KF2/KFS2 M3 T dimension. The flange remains proud unless recessed.'),
'PressNutShankDiameter':(4.68,'Press-nut shank envelope diameter','Default KF2/KFS2 M3 C dimension. A smooth reference envelope for the broaching teeth; interference with the smaller mounting bore is intentional.'),
'PressNutShankDepth':(1.53,'Press-nut shank depth','Maximum inserted shank length used in the simplified hardware reference; this is not a blind-hole depth.'),
'PressNutFlangeRecess':(0.,'Press-nut flange recess depth','Optional circular flange counterbore. Zero leaves the flange outside. Remaining plate must meet the insert minimum thickness.'),
'PressNutMinThickness':(1.53,'Press-nut minimum plate thickness','Default KF2/KFS2 minimum supporting sheet thickness after flange recess. Change only to match a specific purchased insert.')}

def joint_seat(p,group,point):
 from .parameters import three_plate,arm_braces,upper_clamp_active,arms_above_bottom,plate_levels,arm_brace_layouts
 levels=plate_levels(p)
 if group=='Arm bolts':
  mode=p.ArmNutMount
  if three_plate(p):role='MidPlate';z=levels['mid_z']+p.ClampThickness;thick=p.ClampThickness;axis=1
  elif upper_clamp_active(p):b=arm_brace_layouts(p)[0];role='ArmClampPlate';z=b['z']+b['thickness'];thick=b['thickness'];axis=1
  else:role='BottomPlate';axis=-1 if arms_above_bottom(p) else 1;z=0. if axis<0 else p.BottomThickness;thick=p.BottomThickness
  bore=p.RootHoleDiameter
 else:
  from .parameters import stack_mounting_role
  mode='M3 press nut';role=stack_mounting_role(p);z=levels['stack_deck_z'];thick=p.ClampThickness if role=='MidPlate' else p.ArmBraceThickness if role=='ArmClampPlate' else p.BottomThickness;axis=1;bore=p.StackHoleDiameter
 depth=p.NutRecessDepth if mode=='Recessed hex nut' else p.PressNutFlangeRecess if mode=='M3 press nut' else 0.
 return dict(role=role,point=point,z=z,axis=axis,thickness=thick,bore=bore,mode=mode,depth=depth)

def seats(p,role=None):
 from .parameters import arm_layouts,standoff_layouts,three_plate,arm_braces,upper_clamp_active,stack_mounting_role,stack_holes
 groups=[]
 if role is not None and role not in ('BottomPlate','MidPlate','ArmClampPlate'):return []
 armrole='MidPlate' if three_plate(p) else 'ArmClampPlate' if upper_clamp_active(p) else 'BottomPlate'
 stackrole=stack_mounting_role(p)
 if role is not None and role not in (armrole,stackrole):return []
 if (role is None or role==armrole) and p.ArmNutMount!='External hex nut':
  stands=standoff_layouts(p)
  for arm in arm_layouts(p):
   for pt in arm['bolts']:
    if not any(s['shared_arm'] and math.dist(pt,s['point'])<1e-6 for s in stands):groups.append(joint_seat(p,'Arm bolts',pt))
 if (role is None or role==stackrole) and p.StackPressNuts:groups += [joint_seat(p,'Stack hardware',pt) for pt in stack_holes(p)]
 return [s for s in groups if role is None or s['role']==role]

def validate_seats(p):
 from .hardware_layout import metric_size,SIZES
 errors=[]
 for name in FIELDS:
  v=getattr(p,name)
  if isinstance(v,(str,bool)):continue
  if not math.isfinite(v) or v<0 or v>20:errors.append(name+' must be finite and between 0 and 20 mm.')
 if errors:return errors
 for s in seats(p):
  if s['mode']=='Recessed hex nut' and (s['depth']<=0 or s['thickness']-s['depth']<1):errors.append(s['role']+': hex recess must leave at least 1 mm of carbon.')
  if s['mode']=='M3 press nut':
   if metric_size(s['bore'])!=3.:errors.append('M3 press nuts require an M3 clearance bore at the selected joint.')
   if not 3.5<=p.PressNutBore<=5.:errors.append('M3 press-nut mounting bore must be 3.5–5 mm; match the insert drawing.')
   if not p.PressNutBore<p.PressNutShankDiameter<=p.PressNutFlangeDiameter:errors.append('Press-nut shank envelope must exceed its mounting bore and fit within the flange diameter.')
   if p.PressNutFlangeDiameter<=p.PressNutBore:errors.append('Press-nut flange must be wider than its mounting bore.')
   if s['thickness']-s['depth']<max(p.PressNutMinThickness,p.PressNutShankDepth):errors.append(s['role']+': insufficient thickness for the press-nut shank after flange recess.')
   if s['depth']>p.PressNutFlangeHeight or p.PressNutFlangeHeight<=0:errors.append('Flange recess cannot exceed the press-nut flange height.')
 if p.StackPressNuts:
  from .parameters import stack_reference_z,plate_levels
  if stack_reference_z(p)+p.StackHeight+SIZES[metric_size(p.StackHoleDiameter)][5] > plate_levels(p)['top_z']-.2:errors.append('The raised FC stack and upper nuts need taller standoffs; use Fit stack height.')
 return list(dict.fromkeys(errors))
