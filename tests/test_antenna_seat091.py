import math,unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.antenna_layout import antenna_layout,antenna_standoff_bore,validate_antenna
from freecad.rotorforge.mount_bands import rear_guard_band
class AntennaSeatTests(unittest.TestCase):
 def test_seated_all_angles(self):
  for tilt in (0,30,45,60,90):
   p=replace(Parameters(),FlexRearAntenna=True,FlexSideGuards=True,FlexAntennaTilt=tilt)
   a=antenna_layout(p);lo,hi=rear_guard_band(p)
   self.assertAlmostEqual(a['z0'],hi);self.assertGreaterEqual(hi-lo,4-1e-7)
   self.assertAlmostEqual(math.degrees(math.asin(a['holders'][0]['axis'][2])),tilt)
   self.assertAlmostEqual(a['height'],p.FlexAntennaGripHeight)
 def test_direct_bore_overrides_allowance(self):
  p=replace(Parameters(),FlexAntennaStandoffBore=6.5,FlexAntennaFit=.8)
  self.assertEqual(antenna_standoff_bore(p),6.5)
  self.assertEqual(antenna_standoff_bore(replace(p,FlexAntennaStandoffBore=0)),p.StandoffDiameter+.8)
 def test_adjustable_grip_reserves_guard_stock(self):
  p=replace(Parameters(),FlexRearAntenna=True,FlexSideGuards=True,FlexAntennaGripHeight=40)
  self.assertGreaterEqual(rear_guard_band(p)[1]-rear_guard_band(p)[0],4-1e-7)
  self.assertEqual(validate_antenna(p),[])
 def test_bounds_and_persistence(self):
  p=replace(Parameters(),FlexAntennaTilt=78,FlexAntennaStandoffBore=6.3)
  self.assertEqual(Parameters.from_dict(p.to_dict()),p)
  self.assertTrue(validate_antenna(replace(p,FlexAntennaTilt=91)))
 def test_disabled_guard_unchanged(self):
  p=Parameters();lo,hi=rear_guard_band(p);self.assertEqual(hi-lo,6)
