"""Protective options persist without changing disabled frame geometry."""
import unittest
from dataclasses import replace
from compact_fixture import Parameters
from freecad.rotorforge.parameters import validate
from freecad.rotorforge.flex import flex_roles
from freecad.rotorforge.protection_layout import guard_layout
class ProtectionTests(unittest.TestCase):
 def test_guard_layout_uses_actual_posts_and_clearance(self):
  p=Parameters(FlexSideGuards=True);a,b=guard_layout(p);self.assertEqual(a['x'],-b['x']);self.assertEqual(a['front'],b['front']);self.assertEqual(a['rear'],b['rear'])
  self.assertGreater(b['x']-p.FlexGuardWall/2,(p.StackSpacing+6)/2)
 def test_invalid_wall_sizes_and_removed_panels_are_rejected(self):
  p=Parameters(FlexMotorProtectors=True,FlexSideGuards=True)
  for change in ({'FlexProtectorWall':.1},{'FlexGuardWall':.5},{'FlexGuardSlotCount':0},{'FlexGuardFrontInset':1000}):self.assertTrue(validate(replace(p,**change))[0])
