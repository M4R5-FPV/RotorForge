"""Mirrored pad orientation while retaining arm/root geometry and local clocking."""
import math,tempfile,unittest
from pathlib import Path
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,arm_layouts,motor_centres,save_parameters,load_parameters,validate
from freecad.rotorforge.motor_pads import motor_pad_rotation,motor_pad_unit,motor_tip_slots

def close_sets(a,b):
 return len(a)==len(b) and all(any(math.dist(x,y)<1e-8 for y in b) for x in a)

class MotorPadRotationTests(unittest.TestCase):
 def test_quadrants_use_opposite_directions(self):
  arms=arm_layouts(Parameters(MotorPadRotation=25))
  self.assertEqual([a['pad_rotation_deg'] for a in arms],[25,-25,25,-25])
 def test_negative_angle_reverses_directions(self):
  self.assertEqual([a['pad_rotation_deg'] for a in arm_layouts(Parameters(MotorPadRotation=-25))],[-25,25,-25,25])
 def test_pad_axes_mirror_across_both_frame_axes(self):
  for layout in ('True X','Stretched X'):
   arms=arm_layouts(Parameters(Layout=layout,MotorPadRotation=30));x,y=arms[0]['pad_unit']
   for a,expected in zip(arms,((x,y),(-x,y),(-x,-y),(x,-y))):
    self.assertAlmostEqual(a['pad_unit'][0],expected[0]);self.assertAlmostEqual(a['pad_unit'][1],expected[1])
 def test_deadcat_pairs_keep_left_right_symmetry(self):
  a=arm_layouts(Parameters(Layout='Deadcat',RearArmExtension=20,MotorPadRotation=35))
  for i,j in ((0,1),(2,3)):
   self.assertAlmostEqual(a[i]['pad_unit'][0],-a[j]['pad_unit'][0]);self.assertAlmostEqual(a[i]['pad_unit'][1],a[j]['pad_unit'][1])
 def test_fixing_patterns_mirror_with_pads(self):
  for pattern in ('3-hole bolt circle','4-hole bolt circle'):
   a=arm_layouts(Parameters(MotorHoleLayout=pattern,MotorBoltCircle=20,MotorPadRotation=23))
   fr=a[0]['motor_holes']
   self.assertTrue(close_sets([(-x,y) for x,y in fr],a[1]['motor_holes']))
   self.assertTrue(close_sets([(-x,-y) for x,y in fr],a[2]['motor_holes']))
   self.assertTrue(close_sets([(x,-y) for x,y in fr],a[3]['motor_holes']))
 def test_arm_geometry_and_motor_centres_do_not_move(self):
  for layout in ('True X','Stretched X','Deadcat'):
   p=Parameters(Layout=layout);q=replace(p,MotorPadRotation=40)
   self.assertEqual(motor_centres(p),motor_centres(q))
   for a,b in zip(arm_layouts(p),arm_layouts(q)):
    for key in ('root','start','motor','unit','bolts','length'):self.assertEqual(a[key],b[key])
 def test_tip_slot_follows_pad_symmetry(self):
  p=Parameters(MotorPadShape='Arrowhead',MotorTipSlotEnabled=True,MotorPadRotation=25)
  arms=arm_layouts(p);a,b,r=motor_tip_slots(p,arms[0])[0];aa,bb,rr=motor_tip_slots(p,arms[1])[0]
  self.assertTrue(close_sets([(-a[0],a[1]),(-b[0],b[1])],[aa,bb]));self.assertEqual(r,rr)
 def test_hole_clocking_remains_a_local_offset(self):
  p=Parameters(MotorHoleLayout='3-hole bolt circle',MotorBoltCircle=20,MotorHoleRotation=30,MotorPadRotation=25)
  for a in arm_layouts(p):
   ux,uy=a['pad_unit'];x,y=a['motor_holes'][0];mx,my=a['motor'];dx,dy=x-mx,y-my
   self.assertAlmostEqual(dx*ux+dy*uy,10*math.cos(math.pi/6));self.assertAlmostEqual(-dx*uy+dy*ux,5)
 def test_existing_settings_keep_zero_pad_rotation(self):
  self.assertEqual(Parameters.from_dict({'MotorHoleRotation':-30}).MotorPadRotation,0)
 def test_signed_angle_json_round_trip(self):
  p=Parameters(MotorPadRotation=-25)
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'frame.json';save_parameters(f,p);self.assertEqual(load_parameters(f),p)
 def test_angle_limits(self):
  self.assertTrue(validate(Parameters(MotorPadRotation=181))[0]);self.assertTrue(validate(Parameters(MotorPadRotation=-181))[0])
