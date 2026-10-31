import unittest,math
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.protection_layout import guard_layout,closure_profile,vent_polygon,usb_window
from freecad.rotorforge.flex_options import GUARD_VENT_SHAPES,FLEX_OPTIONS
from freecad.rotorforge.flex import validate_flex
class SideClosureTests(unittest.TestCase):
 def test_shapes_shared_and_bounded(self):
  self.assertEqual(len(GUARD_VENT_SHAPES),16)
  self.assertEqual(FLEX_OPTIONS['FlexGuardVentShape'][3],FLEX_OPTIONS['FlexGuardFCVentShape'][3])
  for name in GUARD_VENT_SHAPES[6:]:
   points=vent_polygon(dict(shape=name,width=10.,height=4.));self.assertGreaterEqual(len(points),3)
   self.assertTrue(all(abs(x)<=5.000001 and abs(y)<=2.000001 for x,y in points),name)
   area=sum(x*v-y*u for (x,y),(u,v) in zip(points,points[1:]+points[:1]))
   self.assertGreater(abs(area),1.,name)
 def test_disabled_is_backward_compatible(self):
  p=Parameters(FlexSideGuards=True)
  self.assertIsNone(closure_profile(p,guard_layout(p)[0]));self.assertFalse(p.FlexGuardCloseFront)
 def test_closure_uses_camera_and_bottom(self):
  p=Parameters(FPVEnabled=True,FlexSideGuards=True,FlexGuardCloseFront=True,FlexGuardUSBEnabled=True)
  a,b=guard_layout(p);ca,cb=closure_profile(p,a),closure_profile(p,b)
  self.assertEqual(ca['sections'],cb['sections']);self.assertEqual(ca['x'],-cb['x'])
  self.assertAlmostEqual(ca['sections'][0][0],0.)
  self.assertIsNotNone(usb_window(p,a))
  self.assertEqual(Parameters.from_dict(p.to_dict()),p)
 def test_camera_required_and_landing_bounds(self):
  p=Parameters(FlexSideGuards=True,FlexGuardCloseFront=True)
  self.assertTrue(any('requires FPV' in e for e in validate_flex(p)[0]))
  self.assertTrue(any('landing' in e for e in validate_flex(replace(p,FPVEnabled=True,FlexGuardCameraOverlap=12.))[0]))
 def test_fc_wire_retains_original_edge(self):
  from freecad.rotorforge.protection_layout import guard_wire_openings
  p=Parameters(FPVEnabled=True,FlexSideGuards=True,FlexGuardCloseFront=True,FlexGuardWireEnabled=True,FlexGuardWirePairs='Front')
  opening=guard_wire_openings(p,guard_layout(p)[0])[0]
  self.assertAlmostEqual(opening['bottom'],guard_layout(p)[0]['z'])
  errors=validate_flex(replace(p,FlexGuardWireFrontY=guard_layout(p)[0]['front']-p.StackOffsetY))[0]
  self.assertFalse(errors)
 def test_preview_contains_front_and_low_panel(self):
  from freecad.rotorforge.flex_preview import flex_path,guard_plan_path
  from PySide6.QtCore import QPointF
  p=Parameters(FPVEnabled=True,FlexSideGuards=True,FlexGuardCloseFront=True,FlexGuardStyle='Solid')
  g=guard_layout(p)[0];path=flex_path(p,g['role'])
  self.assertFalse(path.contains(QPointF(p.StackOffsetY+1,5)))
  self.assertFalse(path.contains(QPointF(g['front']-8,5)))
  self.assertEqual(closure_profile(p,g)['start'],g['front'])
  self.assertTrue(path.contains(QPointF(55,5)));self.assertFalse(guard_plan_path(p,g).isEmpty())
if __name__=='__main__':unittest.main()
