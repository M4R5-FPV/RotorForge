import unittest,math
from dataclasses import replace
from freecad.rotorforge.reference_options import blade_pitch_angle,PROP_HUB_HEIGHT,SHAFT_DIAMETER,LOCKNUT_AF,LOCKNUT_HEIGHT,shaft_top
from freecad.rotorforge.parameters import Parameters,validate
class MotorAssemblyTests(unittest.TestCase):
 def test_fixed_hardware_dimensions_and_engagement(self):
  self.assertEqual(PROP_HUB_HEIGHT,6.);self.assertEqual(SHAFT_DIAMETER,5.)
  self.assertEqual((LOCKNUT_AF,LOCKNUT_HEIGHT),(8.,5.))
  self.assertEqual(shaft_top(16.),28.)
 def test_pitch_is_distance_not_a_fixed_angle(self):
  for r in (8.,25.,50.,100.):self.assertAlmostEqual(2*math.pi*r*math.tan(blade_pitch_angle(r)),3.7*25.4)
  self.assertGreater(blade_pitch_angle(20),blade_pitch_angle(50))
 def test_detailed_props_ignore_simple_disc_height(self):
  p=Parameters(DetailedPropReferences=True,PropReferenceHeight=1.)
  self.assertFalse(validate(p)[0]);self.assertTrue(validate(replace(p,DetailedPropReferences=False))[0])
