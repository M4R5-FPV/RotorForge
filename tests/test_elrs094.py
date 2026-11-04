import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate,plate_levels
from freecad.rotorforge.elrs_layout import elrs_layout,validate_elrs
from freecad.rotorforge.antenna_layout import validate_antenna
from freecad.rotorforge.mount_bands import rear_guard_band
from freecad.rotorforge.flex import flex_roles
class RearMountTests(unittest.TestCase):
 def test_default_preserves_closed_tube_and_no_elrs(self):
  p=Parameters();self.assertEqual(p.FlexAntennaHolderStyle,'Closed tube');self.assertNotIn('ELRSAntennaMount',flex_roles(p))
 def test_seat_below_guards_above_carrier_both_plate_modes(self):
  for plates in ('2 plates','3 plates'):
   p=replace(Parameters(),PlateDesign=plates,FlexSideGuards=True,FlexRearAntenna=True,FlexELRSEnabled=True)
   a=elrs_layout(p);self.assertGreaterEqual(a['z0'],max(s['base'] for s in a['pair']))
   self.assertAlmostEqual(a['z0']+a['height'],rear_guard_band(p)[0]);self.assertFalse(validate_elrs(p))
 def test_reach_and_spacing_do_not_change_seat(self):
  p=replace(Parameters(),FlexELRSEnabled=True,FlexSideGuards=True);a=elrs_layout(p);b=elrs_layout(replace(p,FlexELRSReach=30,FlexELRSHookSpacing=20))
  self.assertEqual(a['z0'],b['z0']);self.assertEqual(a['height'],b['height']);self.assertEqual(a['y']-b['y'],10);self.assertEqual(b['hooks'][1][0]-b['hooks'][0][0],20)
 def test_oversize_offset_rejected_and_grip_height_capped(self):
  p=replace(Parameters(),FlexELRSEnabled=True,FlexSideGuards=True,FlexELRSGripHeight=50)
  a=elrs_layout(p);self.assertEqual(a['height'],a['available']);self.assertTrue(validate_elrs(replace(p,FlexELRSHeightOffset=30)))
 def test_retention_and_spacing_bounds(self):
  p=replace(Parameters(),FlexELRSEnabled=True)
  for q in (replace(p,FlexELRSRetainingLip=2),replace(p,FlexELRSHookSpacing=5),replace(p,FlexELRSAntennaDiameter=0),replace(p,FlexELRSReach=2)):
   self.assertTrue(validate_elrs(q))
  p=replace(p,FlexRearAntenna=True,FlexAntennaHolderStyle='Side-entry clip',FlexAntennaRetainingLip=2)
  self.assertTrue(validate_antenna(p));self.assertFalse(validate_antenna(replace(p,FlexAntennaConnector='SMA')))
 def test_settings_round_trip(self):
  p=replace(Parameters(),FlexELRSEnabled=True,FlexAntennaHolderStyle='Side-entry clip',FlexELRSHookSpacing=19,FlexELRSRetainingLip=.25,FlexAntennaRetainingLip=.3)
  self.assertEqual(Parameters.from_dict(p.to_dict()),p);self.assertIn('ELRSAntennaMount',flex_roles(p))
