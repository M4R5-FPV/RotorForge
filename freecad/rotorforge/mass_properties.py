"""Volume-weighted frame estimates. Reference envelopes are never frame mass."""
import math

def mass_properties(p,shapes,roles=None):
 if roles is None:
  from .geometry import carbon_roles
  roles=carbon_roles(p)
 def contribution(role,density):
  solids=[(s.Volume,s.CenterOfMass) for s in shapes[role].Solids]
  volume=math.fsum(v for v,c in solids)
  centre=tuple(math.fsum(v*getattr(c,axis) for v,c in solids)/volume for axis in ('x','y','z')) if volume else (0.,0.,0.)
  return (volume*density/1000,centre)
 def combine(items):
  mass=math.fsum(m for m,c in items)
  centre=tuple(math.fsum(m*c[i] for m,c in items)/mass for i in range(3)) if mass else (0.,0.,0.)
  return mass,tuple(0. if abs(v)<1e-10 else v for v in centre)
 carbon=[contribution(r,p.CarbonDensity) for r in roles]
 carbon_mass,carbon_cg=combine(carbon)
 stands=contribution('Standoffs',p.StandoffDensity)
 pad=contribution('LiPoPad',p.LiPoPadDensity) if p.LiPoPadEnabled else (0.,(0.,0.,0.))
 from .flex import flex_roles
 flexible=[contribution(r,p.FlexDensity) for r in flex_roles(p)]
 frame_mass,frame_cg=combine(carbon+[stands,pad]+flexible)
 result=dict(flexible_mass_g=sum(v[0] for v in flexible),carbon_mass_g=carbon_mass,carbon_cg_mm=carbon_cg,standoff_mass_g=stands[0],pad_mass_g=pad[0],frame_mass_g=frame_mass,frame_cg_mm=frame_cg,
  scope='Carbon parts + modelled standoff tubes + optional LiPo pad and printed protective and camera isolation parts. Screws, straps, adhesive, motors and electronics excluded.',
  densities_g_cm3=dict(carbon=p.CarbonDensity,standoffs=p.StandoffDensity,pad=p.LiPoPadDensity,flexible=p.FlexDensity))
 if p.BatteryReferenceEnabled:
  from .battery import battery_levels
  centre=(p.BatteryX,p.BatteryY,battery_levels(p)['battery_z']+p.BatteryHeight/2)
  mass,cg=combine([(frame_mass,frame_cg),(p.BatteryMass,centre)])
  result.update(frame_plus_battery_mass_g=mass,frame_plus_battery_cg_mm=cg,battery_mass_g=p.BatteryMass,
    battery_scope='Frame estimate + reference battery only; not complete aircraft mass or CG.')
 if p.EstimateComponents:
  from .equipment_mass import equipment_items
  items=equipment_items(p)
  equipment=[(i['mass_g'],i['centre_mm']) for i in items]
  drymass,drycg=combine([(frame_mass,frame_cg)]+equipment)
  result.update(equipment_items=items,equipment_mass_g=sum(i['mass_g'] for i in items),
   equipped_mass_g=drymass,equipped_cg_mm=drycg)
  if p.BatteryReferenceEnabled:
   total,cg=combine([(drymass,drycg),(p.BatteryMass,centre)])
   result.update(loaded_mass_g=total,loaded_cg_mm=cg)
  result['equipment_scope']='Nominal equipment + size-based steel screw estimates. Standoffs counted once in bare frame. Other equipment mass is placed at stack centre. Nuts, spacers, straps, antennas and wiring require allowance in Other equipment. Edit nominal masses for your actual analog or digital parts; these are not measured aircraft values.'
 result['display_cg_mm']=result.get('loaded_cg_mm',result.get('equipped_cg_mm',result['frame_cg_mm']))
 return result
