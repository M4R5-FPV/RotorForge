import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,VENT_ROW_COUNTS
from freecad.rotorforge.flex import validate_flex
class VentRowTests(unittest.TestCase):
 def test_unitless_integer_defaults_and_json(self):
  p=Parameters.from_dict({})
  for name in VENT_ROW_COUNTS:self.assertIs(type(getattr(p,name)),int)
  self.assertEqual(Parameters.from_dict(p.to_dict()),p)
 def test_old_fractional_values_keep_the_previous_layout_rounding(self):
  p=Parameters.from_dict({'FlexGuardSlotCount':3.6});self.assertEqual(p.FlexGuardSlotCount,4);self.assertEqual(p.FlexGuardFCSlotCount,4)
  p=Parameters.from_dict({'FlexGuardSlotCount':2.5,'FlexGuardFCSlotCount':4.8});self.assertEqual((p.FlexGuardSlotCount,p.FlexGuardFCSlotCount),(2,5))
 def test_active_sections_reject_fractional_direct_parameters(self):
  p=Parameters(FlexSideGuards=True)
  for key in VENT_ROW_COUNTS:
   self.assertTrue(validate_flex(replace(p,**{key:2.5}))[0])
   for value in (1,2,3,4,5,6):self.assertFalse(validate_flex(replace(p,**{key:value}))[0])
