import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.front_bumper import BUMPER_SHAPES,toe_commands
class PresentationTests(unittest.TestCase):
 def test_simple_defaults_and_independent_switches(self):
  p=Parameters.from_dict({})
  for k in ('DetailedMotorReferences','DetailedPropReferences','DetailedStackReference','DetailedCameraReference'):
   self.assertFalse(getattr(p,k));q=replace(p,**{k:True});self.assertEqual(Parameters.from_dict(q.to_dict()),q)
 def test_removed_bumpers_migrate(self):
  for name in ('Scalloped shoe','Triple-lobe shoe'):
   self.assertNotIn(name,BUMPER_SHAPES)
   self.assertEqual(Parameters.from_dict({'FlexBumperShape':name}).FlexBumperShape,'Rounded shoe')
 def test_new_dimensions_validate_and_roundtrip(self):
  for shape in BUMPER_SHAPES:
   p=Parameters(FlexFrontBumper=True,FlexBumperShape=shape,FlexBumperTipWidth=45.,FlexBumperRecess=70.,FlexBumperLipReach=8.)
   self.assertFalse(validate(p)[0],shape);self.assertEqual(Parameters.from_dict(p.to_dict()),p)
  for kw in ({'FlexBumperTipWidth':91.},{'FlexBumperRecess':100.},{'FlexBumperLipReach':21.},{'FlexBumperLipReach':1.}):self.assertTrue(validate(Parameters(FlexFrontBumper=True,**kw))[0])
 def test_controls_change_the_intended_toe(self):
  args=('V-recess shoe',30,80,2,6)
  self.assertNotEqual(toe_commands(*args),toe_commands(*args,70,80))
  from freecad.rotorforge.bumper_preview import front_bumper_plan
  p=Parameters(FlexFrontBumper=True);full=front_bumper_plan(p);short=front_bumper_plan(replace(p,FlexBumperLipReach=8.))
  self.assertNotEqual(full,short)
