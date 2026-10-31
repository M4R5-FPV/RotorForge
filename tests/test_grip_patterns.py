import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,ENUMERATIONS
from freecad.rotorforge.battery import GRIP_PATTERNS,groove_segments,grip_bounds,grip_point
class GripPatternTests(unittest.TestCase):
 def test_existing_choices_and_new_options(self):
  self.assertEqual(ENUMERATIONS['LiPoPadPattern'][:3],('Solid','Transverse grooves','Cross grooves'))
  self.assertEqual(len(GRIP_PATTERNS),25)
 def test_finished_bounds_override_obsolete_dimensions(self):
  p=Parameters(LiPoPadEnabled=True,LiPoPadShape='Mounting plate outline',LiPoPadWidth=2,LiPoPadLength=2,LiPoPadPattern='Cross grooves')
  a=groove_segments(p,(-22,-80,22,60));b=groove_segments(replace(p,LiPoPadWidth=100,LiPoPadLength=200),(-22,-80,22,60))
  self.assertEqual(a,b);self.assertTrue(any(max(y for x,y in seg)>50 for seg in a));self.assertTrue(any(min(y for x,y in seg)<-70 for seg in a))
 def test_every_pattern_generates_finite_segments(self):
  for kind in GRIP_PATTERNS[1:]:
   p=Parameters(LiPoPadEnabled=True,LiPoPadPattern=kind,LiPoPadGroovePitch=8);segments=groove_segments(p,(-25,-55,25,45))
   self.assertGreater(len(segments),0,kind);self.assertTrue(all(a!=b or kind in ('Dimple grid','Staggered dimples') for a,b in segments),kind)
 def test_frame_following_patterns_ignore_battery_pose(self):
  p=Parameters(LiPoPadShape='Mounting plate outline',BatteryX=100,BatteryY=-100,BatteryRotation=45)
  self.assertEqual(grip_point(p,4,5),(4,5));self.assertEqual(grip_bounds(p,(-20,-50,20,50)),(-20,-50,20,50))
 def test_actual_footprint_density_guard(self):
  p=Parameters(LiPoPadEnabled=True,LiPoPadPattern='Zigzag grooves',LiPoPadGroovePitch=.1)
  with self.assertRaisesRegex(ValueError,'too dense'):groove_segments(p,(-20,-60,20,60))
