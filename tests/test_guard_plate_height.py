import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,plate_levels
from freecad.rotorforge.protection_layout import guard_layout,guard_wire_openings,guard_vents,usb_window,closure_profile
class GuardPlateHeightTests(unittest.TestCase):
 def test_outer_faces_and_unchanged_internal_datums(self):
  for mode in ('2 plates','3 plates'):
   for gap in (0.,.05,1.):
    p=Parameters(PlateDesign=mode,FlexSideGuards=True,FlexGuardClearance=gap);levels=plate_levels(p)
    for g in guard_layout(p):
     self.assertEqual(g['z'],0. if mode=='2 plates' else levels['mid_z'])
     self.assertEqual(g['top'],levels['top_z']+p.TopThickness)
     for stand,(lo,hi) in zip(g['stands'],g['bands']):
      self.assertGreaterEqual(lo,stand['base']);self.assertLessEqual(hi,stand['base']+stand['length'])
 def test_wire_notch_keeps_original_top_edge(self):
  for mode in ('2 plates','3 plates'):
   p=Parameters(PlateDesign=mode,FlexSideGuards=True,FlexGuardWireEnabled=True)
   g=guard_layout(p)[0]
   for opening in guard_wire_openings(p,g):
    self.assertEqual(opening['bottom'],g['z'])
    self.assertAlmostEqual(opening['bottom']+opening['height'],g['inner_bottom']+p.FlexGuardWireHeight)
 def test_vents_and_usb_stay_inside_carrier_space(self):
  p=Parameters(FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardUSBEnabled=True,FlexGuardUSBSide='Both')
  for g in guard_layout(p):
   self.assertEqual(usb_window(p,g)[1],plate_levels(p)['deck_z']+p.FlexGuardUSBZ)
   for vent in guard_vents(p,g):
    self.assertGreaterEqual(vent['z']-vent['height']/2,g['inner_bottom'])
    self.assertLessEqual(vent['z']+vent['height']/2,g['inner_top'])
 def test_front_closure_follows_outer_faces(self):
  p=Parameters(FPVEnabled=True,FlexSideGuards=True,FlexGuardCloseFront=True)
  g=guard_layout(p)[0];closure=closure_profile(p,g)
  self.assertEqual(closure['sections'][0][0],0.)
  self.assertEqual(closure['sections'][-1][0],plate_levels(p)['top_z']+p.TopThickness)
