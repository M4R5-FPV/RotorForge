import unittest,math
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.antenna_layout import antenna_layout,validate_antenna
from freecad.rotorforge.flex import flex_roles
class RearAntennaTests(unittest.TestCase):
 def test_roundtrip(self):
  p=replace(Parameters(),FlexRearAntenna=True,FlexAntennaCount='2 antennas',FlexAntennaGripWall=3.5)
  self.assertEqual(p,Parameters.from_dict(p.to_dict()));self.assertIn('RearAntennaMount',flex_roles(p));self.assertNotIn('RearAntennaMount',flex_roles(Parameters()))
 def test_angles(self):
  a=antenna_layout(replace(Parameters(),FlexAntennaCount='2 antennas',FlexAntennaTilt=30));u,v=[h['axis'] for h in a['holders']]
  self.assertAlmostEqual(math.degrees(math.asin(u[2])),30);self.assertAlmostEqual(math.degrees(math.atan2(abs(u[0]),-u[1])),30);self.assertAlmostEqual(u[0],-v[0])
 def test_height_cap(self):
  p=replace(Parameters(),FlexSideGuards=True,FlexAntennaGripHeight=50);a=antenna_layout(p)
  self.assertAlmostEqual(a['height'],a['available']);self.assertGreater(antenna_layout(replace(p,FlexSideGuards=False))['height'],a['height'])
 def test_connectors(self):
  for c in ('SMA','RP-SMA','u.FL','MMCX'):self.assertEqual(validate_antenna(replace(Parameters(),FlexSideGuards=True,FlexAntennaConnector=c)),[])
 def test_invalid(self):
  self.assertTrue(validate_antenna(replace(Parameters(),FlexSideGuards=True,FlexAntennaSocketWall=.5)));self.assertTrue(validate_antenna(replace(Parameters(),FlexAntennaGripHeight=2)))
 def test_rear_pair(self):
  self.assertEqual(antenna_layout(replace(Parameters(),StandoffCount='6 (3 pairs)',StandoffPair3Y=-90))['pair'][0]['point'][1],-90)
