import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.antenna_layout import antenna_layout,validate_antenna
from freecad.rotorforge.mount_bands import rear_guard_band
class HolderTests(unittest.TestCase):
 def test_length_keeps_root_and_guard_seat(self):
  p=replace(Parameters(),FlexRearAntenna=True,FlexSideGuards=True)
  q=replace(p,FlexAntennaSocketLength=60.)
  a,b=antenna_layout(p),antenna_layout(q)
  self.assertEqual(a['z0'],b['z0']);self.assertEqual(rear_guard_band(p),rear_guard_band(q));self.assertEqual(a['holders'][0]['start'],b['holders'][0]['start']);self.assertEqual(validate_antenna(q),[])
 def test_offset_independent_of_bar(self):
  p=Parameters();a=antenna_layout(p);b=antenna_layout(replace(p,FlexAntennaHolderOffset=12))
  self.assertEqual(a['points'],b['points']);self.assertAlmostEqual(a['holders'][0]['start'][1]-b['holders'][0]['start'][1],12)
 def test_signed_offset_roundtrip(self):
  p=replace(Parameters(),FlexAntennaHolderOffset=-4)
  self.assertEqual(p,Parameters.from_dict(p.to_dict()));self.assertEqual(validate_antenna(p),[])
