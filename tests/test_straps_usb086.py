import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,strap_positions,strap_slots,ENUMERATIONS,validate
from freecad.rotorforge.strap_openings import notch_polygons
from freecad.rotorforge.protection_layout import guard_layout,usb_window,guard_strap_windows
class StrapUSB086(unittest.TestCase):
 def test_removed_none_migrates_disabled(self):
  self.assertEqual(ENUMERATIONS['StrapOpeningStyle'],('Slots','Outline cutouts'))
  p=Parameters.from_dict({'StrapOpeningStyle':'None','StrapSlotsEnabled':True,'StrapOffsetY':22.})
  self.assertFalse(p.StrapSlotsEnabled);self.assertEqual(p.StrapOpeningStyle,'Slots');self.assertEqual(p.StrapOffsetY,22.)
 def test_single_pair_position_and_saved_spacing(self):
  for style in ('Slots','Outline cutouts'):
   p=Parameters(StrapCount='1 strap',StrapSingleY=-4.,StrapOpeningStyle=style)
   self.assertEqual(strap_positions(p),(-4.,));self.assertEqual(Parameters.from_dict(p.to_dict()),p)
   self.assertFalse(validate(p)[0]);self.assertEqual(len(strap_slots(p) or notch_polygons(p)),2)
   q=replace(p,StrapCount='2 straps');self.assertEqual(len(strap_slots(q) or notch_polygons(q)),4)
   self.assertEqual(q.StrapOffsetY,18.)
 def test_guard_auto_tracks_single_position(self):
  p=Parameters(StrapCount='1 strap',StrapSingleY=-4.,FlexSideGuards=True,FlexGuardStraps=True)
  self.assertEqual([w['y'] for w in guard_strap_windows(p,guard_layout(p)[0])],[-4.])
 def test_high_usb_opens_top_but_keeps_lower_wall(self):
  p=Parameters(FPVEnabled=True,FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardUSBEnabled=True,FlexGuardUSBZ=24.)
  g=guard_layout(p)[0];y,z,w,h=usb_window(p,g)
  self.assertGreater(z+h/2,g['top']);self.assertAlmostEqual(z-h/2,g['deck_z']+24.-p.FlexGuardUSBHeight/2)
  self.assertFalse(validate(p)[0]);self.assertTrue(validate(replace(p,FlexGuardUSBZ=60.))[0])
  self.assertTrue(validate(replace(p,FlexGuardUSBZ=2.))[0])
