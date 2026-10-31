import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.flex import validate_flex
from freecad.rotorforge.protection_layout import guard_layout
class RearWirePocketTests(unittest.TestCase):
 def setUp(self):self.p=Parameters(FlexSideGuards=True,FlexGuardWireEnabled=True,FlexGuardWirePairs='Rear',FlexGuardWireRearY=-46.,FlexGuardWireWidth=12.)
 def test_rear_opening_can_pass_under_grip_and_through_end(self):
  for design in ('2 plates','3 plates'):
   for gap in (0.,1.):self.assertFalse(validate_flex(replace(self.p,PlateDesign=design,FlexGuardClearance=gap))[0])
 def test_actual_grip_and_web_are_protected(self):
  self.assertTrue(validate_flex(replace(self.p,FlexGuardWireHeight=10.))[0])
  p=replace(self.p,FlexGuardWirePairs='Front',FlexGuardWireFrontY=44.)
  self.assertFalse(validate_flex(p)[0])
 def test_pocket_cannot_miss_guard_entirely(self):
  self.assertTrue(validate_flex(replace(self.p,FlexGuardWireRearY=-80.))[0])
 def test_can_pass_under_intermediate_upper_fc_grip(self):
  p=replace(self.p,FlexGuardExtendFront=True,StandoffCount='6 (3 pairs)',StandoffPair3Y=-94.,StandoffPair3Width=28.,MidReachMode='Custom',MidRearReach=102.,TopReachMode='Custom',TopRearReach=102.)
  self.assertFalse(validate_flex(p)[0])
