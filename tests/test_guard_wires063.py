import unittest,math
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.protection_layout import guard_layout,guard_wire_openings
from freecad.rotorforge.flex import validate_flex
class GuardWireTests(unittest.TestCase):
 def test_opt_in_and_side_pair_selection(self):
  p=Parameters(FlexSideGuards=True)
  self.assertFalse(guard_wire_openings(p,guard_layout(p)[0]))
  p=replace(p,FlexGuardWireEnabled=True,FlexGuardWireSide='Left',FlexGuardWirePairs='Rear')
  left,right=guard_layout(p);self.assertEqual(len(guard_wire_openings(p,left)),1);self.assertFalse(guard_wire_openings(p,right))
 def test_signed_stack_anchor_and_size(self):
  p=Parameters(FlexSideGuards=True,FlexGuardWireEnabled=True,StackOffsetY=3.,FlexGuardWireFrontY=18.,FlexGuardWireRearY=-21.,FlexGuardWireWidth=12.,FlexGuardWireHeight=4.)
  a,b=guard_wire_openings(p,guard_layout(p)[0]);self.assertEqual((a['y'],b['y']),(21.,-18.));self.assertEqual(a['width'],12.);self.assertAlmostEqual(a['bottom']+a['height'],guard_layout(p)[0]['inner_bottom']+4.)
  self.assertFalse(validate_flex(p)[0])
 def test_invalid_openings_preserve_grips_and_top_web(self):
  p=Parameters(FlexSideGuards=True,FlexGuardWireEnabled=True)
  self.assertFalse(validate_flex(p)[0])
  for changes in ({'FlexGuardWireFrontY':100.},{'FlexGuardWireWidth':200.},{'FlexGuardWireHeight':100.},{'FlexGuardWireHeight':0.},{'FlexGuardWireRearY':math.nan}):self.assertTrue(validate_flex(replace(p,**changes))[0],changes)
 def test_local_upper_strip_anchor(self):
  p=Parameters(FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardWireEnabled=True,MidReachMode='Custom',MidFrontReach=24.,FlexGuardWireFrontY=32.,FlexGuardWireWidth=8.)
  g=guard_layout(p)[0];a,b=guard_wire_openings(p,g);self.assertEqual(a['bottom'],g['inner_top']-10);self.assertEqual(b['bottom'],g['z'])

class GuardWirePreviewTests(unittest.TestCase):
 def test_side_preview_clears_bottom_exit_and_retains_top(self):
  try:
   from freecad.rotorforge.flex_preview import flex_path,QtCore
  except ImportError:self.skipTest('Qt is unavailable')
  p=Parameters(FlexSideGuards=True,FlexGuardStyle='Solid',FlexGuardWireEnabled=True)
  g=guard_layout(p)[0];o=guard_wire_openings(p,g)[0];path=flex_path(p,g['role'])
  self.assertFalse(path.contains(QtCore.QPointF(o['y'],o['bottom']+o['height']/2)))
  self.assertTrue(path.contains(QtCore.QPointF(o['y'],g['top']-1)))
  plain=flex_path(replace(p,FlexGuardWireEnabled=False),g['role'])
  self.assertTrue(plain.contains(QtCore.QPointF(o['y'],o['bottom']+o['height']/2)))
 def test_existing_serialized_design_defaults_and_roundtrip(self):
  p=Parameters.from_dict({'FlexSideGuards':True});self.assertFalse(p.FlexGuardWireEnabled)
  p=replace(p,FlexGuardWireEnabled=True,FlexGuardWireFrontY=-8.,FlexGuardWireRearY=-28.,FlexGuardWireSide='Right',FlexGuardWirePairs='Rear')
  self.assertEqual(Parameters.from_dict(p.to_dict()),p)
