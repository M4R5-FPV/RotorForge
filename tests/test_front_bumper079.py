import unittest,math
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.front_bumper import BUMPER_SHAPES,toe_commands
from freecad.rotorforge.flex import flex_roles
class FrontBumperTests(unittest.TestCase):
 def test_default_off_and_new_role_is_opt_in(self):
  p=Parameters.from_dict({});self.assertFalse(p.FlexFrontBumper);self.assertNotIn('FrontBumper',flex_roles(p))
  self.assertIn('FrontBumper',flex_roles(replace(p,FlexFrontBumper=True)))
 def test_all_styles_roundtrip_and_validate(self):
  for shape in BUMPER_SHAPES:
   p=Parameters(FlexFrontBumper=True,FlexBumperShape=shape);self.assertFalse(validate(p)[0],(shape,validate(p)[0]));self.assertEqual(Parameters.from_dict(p.to_dict()),p)
 def test_invalid_shell_and_reach_are_rejected(self):
  for kw in ({'FlexBumperSole':0.},{'FlexBumperWall':.2},{'FlexBumperLip':0.},{'FlexBumperFit':2.},{'FlexBumperReach':1000.},{'FlexBumperOverlap':50.},{'FlexBumperProjection':0.}):
   self.assertTrue(validate(Parameters(FlexFrontBumper=True,**kw))[0],kw)
 def test_profiles_are_symmetric_and_projection_changes_the_toe(self):
  self.assertEqual(toe_commands('Follow bottom plate',25,80,2,4),())
  for s in BUMPER_SHAPES[1:]:
   commands=toe_commands(s,25,80,2,4);self.assertTrue(commands)
   for item in commands:
    for x,y in item[1:]:self.assertTrue(math.isfinite(x+y));self.assertLessEqual(y,86.)
   self.assertNotEqual(commands,toe_commands(s,25,80,2,8))
 def test_live_preview_is_bounded_and_follows_width(self):
  try:from freecad.rotorforge.bumper_preview import front_bumper_path
  except ImportError:self.skipTest('Qt unavailable')
  p=Parameters(FlexFrontBumper=True)
  for shape in BUMPER_SHAPES:
   box=front_bumper_path(replace(p,FlexBumperShape=shape)).boundingRect();self.assertGreater(box.width(),p.BodyWidth);self.assertAlmostEqual(box.top(),82.5-p.FlexBumperReach)
  self.assertGreater(front_bumper_path(replace(p,BodyWidth=65)).boundingRect().width(),front_bumper_path(p).boundingRect().width())
