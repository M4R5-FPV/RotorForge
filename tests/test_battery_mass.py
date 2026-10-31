"""Battery pose, pad validation and independently known weighted-mass results."""
from dataclasses import replace
import math,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as N
from freecad.rotorforge.parameters import Parameters,validate,save_parameters,load_parameters
from freecad.rotorforge.battery import battery_levels,battery_point,groove_segments
from freecad.rotorforge.mass_properties import mass_properties

def shape(volume,cg):return N(Solids=[N(Volume=volume,CenterOfMass=N(x=cg[0],y=cg[1],z=cg[2]))])
class BatteryMassTests(unittest.TestCase):
 def test_nominal_reference(self):
  p=Parameters();self.assertEqual((p.BatteryLength,p.BatteryWidth,p.BatteryHeight,p.BatteryMass),(75.,38.,38.,208.));self.assertFalse(p.LiPoPadEnabled)
 def test_bottom_pad_and_battery_are_below_plate(self):
  p=Parameters(BatteryMount='Bottom plate',LiPoPadEnabled=True)
  z=battery_levels(p);self.assertEqual(z['pad_z'],-2);self.assertEqual(z['battery_z'],-40)
  self.assertEqual(battery_levels(replace(p,LiPoPadEnabled=False))['battery_z'],-38)
 def test_top_battery_follows_pad_thickness(self):
  p=Parameters();a=battery_levels(p);b=battery_levels(replace(p,LiPoPadEnabled=True,LiPoPadThickness=3))
  self.assertEqual(b['battery_z']-a['battery_z'],3)
 def test_local_rotation_and_offsets(self):
  p=Parameters(BatteryX=7,BatteryY=-4,BatteryRotation=90)
  x,y=battery_point(p,2,3);self.assertAlmostEqual(x,4);self.assertAlmostEqual(y,-2)
 def test_groove_validation(self):
  p=Parameters(LiPoPadEnabled=True,LiPoPadPattern='Cross grooves')
  for change in ({'LiPoPadGrooveDepth':2},{'LiPoPadGroovePitch':1},{'LiPoPadGroovePitch':.01},{'LiPoPadCornerRadius':18}):self.assertTrue(validate(replace(p,**change))[0])
  self.assertFalse(validate(p)[0]);self.assertGreater(len(groove_segments(p)),0)
  self.assertEqual(groove_segments(replace(p,LiPoPadPattern='Solid')),())
 def test_frame_mass_and_cg_known_solution(self):
  p=Parameters(BatteryReferenceEnabled=False)
  parts={'Carbon':shape(1000,(0,0,0)),'Standoffs':shape(1000,(0,0,10))}
  m=mass_properties(p,parts,roles=['Carbon']);self.assertAlmostEqual(m['frame_mass_g'],4.3)
  self.assertAlmostEqual(m['frame_cg_mm'][2],27/4.3);self.assertEqual(m['pad_mass_g'],0)
  self.assertNotIn('frame_plus_battery_mass_g',m)
 def test_pad_and_battery_have_separate_mass_scope(self):
  p=Parameters(LiPoPadEnabled=True,BatteryX=20,BatteryY=-10)
  parts={'Carbon':shape(1000,(0,0,0)),'Standoffs':shape(1000,(0,0,10)),'LiPoPad':shape(1000,(0,0,30))}
  m=mass_properties(p,parts,roles=['Carbon']);self.assertAlmostEqual(m['frame_mass_g'],5.5);self.assertAlmostEqual(m['frame_plus_battery_mass_g'],213.5)
  self.assertEqual(m['frame_cg_mm'][:2],(0,0));self.assertAlmostEqual(m['frame_plus_battery_cg_mm'][0],208*20/213.5)
 def test_compound_uses_all_solid_centres(self):
  p=Parameters(BatteryReferenceEnabled=False);a=shape(1000,(-10,0,0));a.Solids+=shape(3000,(10,0,0)).Solids
  m=mass_properties(p,{'Carbon':a,'Standoffs':shape(0,(0,0,0))},roles=['Carbon']);self.assertAlmostEqual(m['carbon_cg_mm'][0],5)
 def test_parameters_round_trip(self):
  p=Parameters(LiPoPadEnabled=True,BatteryX=-4,BatteryY=6,BatteryRotation=-25,LiPoPadPattern='Cross grooves')
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'battery.json';save_parameters(f,p);self.assertEqual(load_parameters(f),p)
 def test_old_settings_keep_pad_disabled(self):
  from freecad.rotorforge.battery import BATTERY_FIELDS
  d={k:v for k,v in Parameters().to_dict().items() if k not in BATTERY_FIELDS and k not in ('StandoffDensity','ShowFrameCG')}
  self.assertFalse(Parameters.from_dict(d).LiPoPadEnabled)
