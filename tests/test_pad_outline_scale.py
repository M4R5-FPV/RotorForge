import unittest,tempfile
from pathlib import Path
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate,save_parameters,load_parameters
from freecad.rotorforge.part_preview import pad_path
class PadOutlineScaleTests(unittest.TestCase):
 def test_old_settings_retain_full_outline(self):
  data=Parameters().to_dict()
  for key in ('LiPoPadOutlineWidthScale','LiPoPadOutlineLengthScale'):data.pop(key)
  p=Parameters.from_dict(data);self.assertEqual((p.LiPoPadOutlineWidthScale,p.LiPoPadOutlineLengthScale),(100,100))
 def test_scale_range_only_for_active_outline(self):
  p=Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline')
  for key in ('LiPoPadOutlineWidthScale','LiPoPadOutlineLengthScale'):
   for value in (0,101,float('nan')):self.assertTrue(validate(replace(p,**{key:value}))[0])
  self.assertFalse(validate(replace(p,LiPoPadShape='Rectangle',LiPoPadOutlineWidthScale=0))[0])
 def test_independent_preview_dimensions(self):
  p=Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline');full=pad_path(p).boundingRect()
  q=replace(p,LiPoPadOutlineWidthScale=80,LiPoPadFrontReach=25,LiPoPadRearReach=35);b=pad_path(q).boundingRect()
  self.assertAlmostEqual(b.width(),full.width()*.8,places=4);self.assertAlmostEqual(b.height(),60,places=4)
  self.assertAlmostEqual(b.center().x(),full.center().x(),places=4);self.assertAlmostEqual(b.center().y(),-5,places=4)
 def test_scaled_settings_roundtrip(self):
  p=Parameters(LiPoPadShape='Mounting plate outline',LiPoPadOutlineWidthScale=83.5,LiPoPadOutlineLengthScale=67)
  with tempfile.TemporaryDirectory() as folder:
   f=Path(folder)/'settings.json';save_parameters(f,p);self.assertEqual(load_parameters(f),p)

 def test_stack_offset_and_independent_ends(self):
  p=Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline',StackOffsetY=7,LiPoPadFrontReach=20,LiPoPadRearReach=30)
  b=pad_path(p).boundingRect();self.assertAlmostEqual(b.top(),-23);self.assertAlmostEqual(b.bottom(),27)
  c=pad_path(replace(p,LiPoPadFrontReach=15)).boundingRect();self.assertAlmostEqual(c.top(),b.top());self.assertAlmostEqual(c.bottom(),22)
 def test_old_length_scale_migrates_to_reaches(self):
  data=Parameters(LiPoPadOutlineLengthScale=65).to_dict()
  for k in ('LiPoPadFrontReach','LiPoPadRearReach'):data.pop(k)
  p=Parameters.from_dict(data);self.assertGreater(p.LiPoPadFrontReach,0);self.assertGreater(p.LiPoPadRearReach,0)
 def test_reach_validation(self):
  p=Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline')
  self.assertFalse(validate(p)[0])
  for k in ('LiPoPadFrontReach','LiPoPadRearReach'):self.assertTrue(validate(replace(p,**{k:-1}))[0])
