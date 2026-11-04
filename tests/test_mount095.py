import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.elrs_layout import elrs_layout,validate_elrs
class Mount095Tests(unittest.TestCase):
 def test_hook_offset_leaves_bar_and_grip_fixed(self):
  p=Parameters();a=elrs_layout(p);b=elrs_layout(replace(p,FlexELRSHookReach=15))
  self.assertEqual(a['points'],b['points']);self.assertEqual(a['z0'],b['z0']);self.assertEqual(a['bar_y'],b['bar_y']);self.assertEqual(a['y']-b['y'],15)
 def test_pass_through_needs_surrounding_stock(self):
  p=replace(Parameters(),FlexELRSEnabled=True)
  self.assertFalse(validate_elrs(p));self.assertTrue(validate_elrs(replace(p,FlexELRSPassThroughDiameter=6)))
  self.assertFalse(validate_elrs(replace(p,FlexELRSPassThroughDiameter=0)))
 def test_new_controls_round_trip(self):
  p=replace(Parameters(),FlexELRSHookReach=8,FlexELRSPassThroughDiameter=4)
  self.assertEqual(Parameters.from_dict(p.to_dict()),p)
