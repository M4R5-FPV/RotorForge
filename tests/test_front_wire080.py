import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.flex import validate_flex
from freecad.rotorforge.protection_layout import guard_layout,guard_wire_openings
from freecad.rotorforge.front_bumper import BUMPER_SHAPES,toe_commands
class FrontWireTests(unittest.TestCase):
 def setUp(self):self.p=Parameters(FPVEnabled=True,StandoffHeight=35.,FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardWireEnabled=True,FlexGuardWirePairs='Front')
 def test_front_moves_across_mid_end_and_near_front_post(self):
  for y in (18.,20.,23.,24.,25.,30.,36.,40.,43.,46.):
   p=replace(self.p,FlexGuardWireFrontY=y);self.assertFalse(validate(p)[0],(y,validate(p)[0]))
 def test_crossing_mid_end_splits_at_each_actual_lower_edge(self):
  p=replace(self.p,FlexGuardWireFrontY=24.)
  g=guard_layout(p)[0];cuts=guard_wire_openings(p,g)
  self.assertEqual(len(cuts),2);self.assertAlmostEqual(sum(v['width'] for v in cuts),p.FlexGuardWireWidth)
  self.assertEqual(cuts[0]['bottom'],g['z']);self.assertEqual(cuts[1]['bottom'],g['inner_top']-10)
  self.assertAlmostEqual(cuts[0]['y']+cuts[0]['width']/2,p.MidFrontReach)
 def test_front_enclosure_transition_can_be_crossed(self):
  p=replace(self.p,FlexGuardCloseFront=True,FlexGuardWireFrontY=46.)
  g=guard_layout(p)[0];cuts=guard_wire_openings(p,g);self.assertEqual(len(cuts),2)
  self.assertEqual(cuts[1]['bottom'],0.);self.assertFalse(validate(p)[0])
 def test_bad_height_and_missed_wall_still_rejected(self):
  for changes in ({'FlexGuardWireFrontY':100.},{'FlexGuardWireHeight':100.},{'FlexGuardWireWidth':200.}):self.assertTrue(validate_flex(replace(self.p,**changes))[0])
 def test_new_bumper_styles_keep_old_names_and_roundtrip(self):
  self.assertEqual(len(BUMPER_SHAPES),18)
  for name in BUMPER_SHAPES:
   p=Parameters(FlexFrontBumper=True,FlexBumperShape=name);self.assertEqual(Parameters.from_dict(p.to_dict()),p)
   if name!='Follow bottom plate':self.assertTrue(toe_commands(name,25,80,2,4))
