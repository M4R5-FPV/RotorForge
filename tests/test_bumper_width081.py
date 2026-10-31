import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.front_bumper import shoulder_hull
class BumperWidthTests(unittest.TestCase):
 def test_width_migrates_and_roundtrips(self):
  self.assertEqual(Parameters.from_dict({'FlexFrontBumper':True}).FlexBumperWidth,0.)
  p=Parameters(FlexFrontBumper=True,FlexBumperWidth=70.)
  self.assertEqual(Parameters.from_dict(p.to_dict()),p)
  self.assertFalse(validate(p)[0])
  for v in (1.,-1.,float('nan')):self.assertTrue(validate(replace(p,FlexBumperWidth=v))[0])
 def test_shoulder_envelope_removes_side_recesses(self):
  h=shoulder_hull(((-30,0),(-30,15),(-12,15),(-12,19),(12,19),(12,15),(30,15),(30,0)),40,22,18)
  self.assertIn((-40.,18.),h);self.assertIn((-40.,22.),h);self.assertIn((40.,22.),h)
  # Every turn is convex: no side notch remains in the joining envelope.
  for a,b,c in zip(h,h[1:]+h[:1],h[2:]+h[:2]):
   self.assertGreaterEqual((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]),-1e-8)
 def test_live_width_and_fit_are_independent(self):
  from freecad.rotorforge.bumper_preview import front_bumper_path
  p=Parameters(FlexFrontBumper=True)
  narrow=front_bumper_path(replace(p,FlexBumperWidth=24.));wide=front_bumper_path(replace(p,FlexBumperWidth=80.))
  self.assertGreater(wide.boundingRect().width(),narrow.boundingRect().width())
  self.assertAlmostEqual(wide.boundingRect().bottom(),narrow.boundingRect().bottom())
  self.assertEqual(p.FlexBumperFit,.2)
