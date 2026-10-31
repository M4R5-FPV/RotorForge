import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,standoff_layouts
from freecad.rotorforge.protection_layout import guard_layout,grip_pad_bounds
class GuardGrip062Tests(unittest.TestCase):
 def test_forward_end_uses_the_whole_exposed_post(self):
  for design in ('2 plates','3 plates'):
   for extend in (False,True):
    p=Parameters(PlateDesign=design,FlexSideGuards=True,FlexGuardExtendFront=extend,StandoffCount='6 (3 pairs)',StandoffPair3Y=-90)
    for g in guard_layout(p):
     post=g['stands'][0];lo,hi=g['bands'][0];self.assertAlmostEqual(lo,post['base']+.15);self.assertAlmostEqual(hi,post['base']+post['length']-.15)
 def test_forward_extension_uses_the_actual_foremost_row(self):
  p=Parameters(FlexSideGuards=True,FlexGuardExtendFront=True,StandoffCount='8 (4 pairs)',StandoffPair4Y=65.,StandoffPair4Width=34.)
  for g in guard_layout(p):self.assertEqual(g['front'],max(s['point'][1] for s in standoff_layouts(p)))
 def test_support_pad_stays_outboard_of_the_post_centre(self):
  p=Parameters(FlexSideGuards=True)
  for g in guard_layout(p):
   post=g['stands'][0];sx,sy=post['point'];sign=g['sign'];station=(sy,sign*27,sign*25,10)
   x0,x1,y0,y1=grip_pad_bounds(p,g,post,station)
   if sign>0:self.assertEqual(x0,sx);self.assertGreater(x1,sx)
   else:self.assertEqual(x1,sx);self.assertLess(x0,sx)
   self.assertLess(y0,sy);self.assertGreater(y1,sy)
