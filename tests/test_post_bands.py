"""Optional-part datums must not move when another component is disabled."""
import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.mount_bands import rear_pair,stack_pair
from freecad.rotorforge.protection_layout import guard_layout
from freecad.rotorforge.flex import flex_roles,validate_flex
from freecad.rotorforge.plate_fillets import fillet_radius,fillet_openings
class PostBandTests(unittest.TestCase):
 def test_guard_bands_and_lower_plate(self):
  for design,role in (('2 plates','BottomPlate'),('3 plates','MidPlate')):
   for g in guard_layout(Parameters(PlateDesign=design,FlexSideGuards=True)):
    self.assertEqual(g['lower_role'],role);self.assertAlmostEqual(g['bands'][0][1]-g['bands'][0][0],g['stands'][0]['length']-.3);self.assertAlmostEqual(g['bands'][1][1]-g['bands'][1][0],6)
 def test_arm_fillet_is_opt_in_and_persistent(self):
  p=Parameters();self.assertEqual(fillet_radius(p,'ArmFrontRight'),0);self.assertFalse(fillet_openings(p,'ArmFrontRight'))
  q=replace(p,ArmEdgeFillet=3,ArmFilletOpenings=True);self.assertEqual(Parameters.from_dict(q.to_dict()),q);self.assertEqual(fillet_radius(q,'ArmRearLeft'),3);self.assertTrue(fillet_openings(q,'ArmRearLeft'))
