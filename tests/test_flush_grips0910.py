import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,plate_levels
from freecad.rotorforge.mount_bands import rear_mount_seats,rear_guard_band
from freecad.rotorforge.antenna_layout import antenna_layout,validate_antenna
from freecad.rotorforge.elrs_layout import elrs_layout,validate_elrs
class FlushGripsTests(unittest.TestCase):
 def test_flush_stack_both_plate_designs(self):
  for plate in ('2 plates','3 plates'):
   p=replace(Parameters(),PlateDesign=plate,FlexSideGuards=True,FlexRearAntenna=True,FlexELRSEnabled=True)
   a=antenna_layout(p);e=elrs_layout(p);lo,hi=rear_guard_band(p)
   self.assertAlmostEqual(a['top'],plate_levels(p)['top_z']);self.assertAlmostEqual(e['z0'],plate_levels(p)['deck_z'])
   self.assertAlmostEqual(e['z0']+e['height'],lo);self.assertAlmostEqual(a['z0'],hi);self.assertGreaterEqual(hi-lo,4)
 def test_requested_gaps_and_roundtrip(self):
  p=replace(Parameters(),FlexSideGuards=True,FlexRearAntenna=True,FlexELRSEnabled=True,FlexAntennaTopGap=.6,FlexAntennaGuardGap=.3,FlexELRSGuardGap=.4,FlexELRSHeightOffset=.5)
  a=antenna_layout(p);e=elrs_layout(p);lo,hi=rear_guard_band(p)
  self.assertAlmostEqual(plate_levels(p)['top_z']-a['top'],.6);self.assertAlmostEqual(a['z0']-hi,.3)
  self.assertAlmostEqual(lo-e['z0']-e['height'],.4);self.assertAlmostEqual(e['z0']-plate_levels(p)['deck_z'],.5)
  self.assertEqual(Parameters.from_dict(p.to_dict()),p)
 def test_insufficient_height_rejected(self):
  p=replace(Parameters(),FlexSideGuards=True,FlexRearAntenna=True,FlexELRSEnabled=True,FlexAntennaTopGap=100)
  self.assertTrue(validate_antenna(p));self.assertTrue(validate_elrs(p))
 def test_single_mount_guard_reaches_opposite_plate(self):
  p=replace(Parameters(),FlexSideGuards=True,FlexRearAntenna=True);self.assertAlmostEqual(rear_guard_band(p)[0],plate_levels(p)['deck_z'])
  p=replace(p,FlexRearAntenna=False,FlexELRSEnabled=True);self.assertAlmostEqual(rear_guard_band(p)[1],plate_levels(p)['top_z'])
