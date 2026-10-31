"""Motor clocking must preserve diameter, layout, and existing designs."""
from pathlib import Path
import unittest,math,tempfile
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,motor_hole_offsets,arm_layouts,validate,save_parameters,load_parameters

class MotorHoleRotationTests(unittest.TestCase):
 def test_four_holes_at_45_match_square_corners(self):
  p=Parameters(MotorHoleLayout='4-hole bolt circle',MotorBoltCircle=16*math.sqrt(2),MotorHoleRotation=45)
  self.assertEqual({(round(x,8),round(y,8)) for x,y in motor_hole_offsets(p)},{(-8,-8),(-8,8),(8,-8),(8,8)})
 def test_three_holes_can_point_inward(self):
  p=Parameters(MotorHoleLayout='3-hole bolt circle',MotorBoltCircle=20,MotorHoleRotation=180)
  pts=motor_hole_offsets(p)
  self.assertAlmostEqual(pts[0][0],-10);self.assertAlmostEqual(pts[0][1],0)
  self.assertTrue(all(abs(math.hypot(x,y)-10)<1e-9 for x,y in pts))
 def test_signed_angles_and_full_turn(self):
  p=Parameters(MotorHoleLayout='3-hole bolt circle',MotorBoltCircle=20,MotorHoleRotation=-30)
  self.assertAlmostEqual(motor_hole_offsets(p)[0][1],-5)
  for a,b in zip(motor_hole_offsets(p),motor_hole_offsets(replace(p,MotorHoleRotation=330))):
   self.assertAlmostEqual(a[0],b[0]);self.assertAlmostEqual(a[1],b[1])
 def test_legacy_square_preserves_holes(self):
  p=Parameters.from_dict({'MotorHoleLayout':'Rectangle','MotorSpacingX':16,'MotorSpacingY':16,'MotorHoleRotation':37})
  self.assertEqual(p.MotorHoleLayout,'4-hole bolt circle')
  self.assertEqual({(round(x,8),round(y,8)) for x,y in motor_hole_offsets(p)},{(-8,-8),(-8,8),(8,-8),(8,8)})
 def test_only_circle_options_are_exposed(self):
  from freecad.rotorforge.parameters import ENUMERATIONS
  self.assertEqual(ENUMERATIONS['MotorHoleLayout'],('4-hole bolt circle','3-hole bolt circle'))
 def test_bad_legacy_dimensions_are_rejected(self):
  for value in (True,0,-2,float('nan'),'16'):
   with self.assertRaises(ValueError):Parameters.from_dict({'MotorHoleLayout':'Rectangle','MotorSpacingX':value})
 def test_old_settings_default_to_zero(self):
  self.assertEqual(Parameters.from_dict({'MotorHoleLayout':'3-hole bolt circle'}).MotorHoleRotation,0)
 def test_round_trip_preserves_negative_angle(self):
  p=Parameters(MotorHoleLayout='3-hole bolt circle',MotorBoltCircle=20,MotorHoleRotation=-22.5)
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'frame.json';save_parameters(f,p);self.assertEqual(load_parameters(f),p)
 def test_all_arms_use_local_pad_direction(self):
  for layout in ('True X','Stretched X','Deadcat'):
   p=Parameters(Layout=layout,MotorHoleLayout='3-hole bolt circle',MotorBoltCircle=20,MotorHoleRotation=30)
   for a in arm_layouts(p):
    dx=a['motor_holes'][0][0]-a['motor'][0];dy=a['motor_holes'][0][1]-a['motor'][1];ux,uy=a['unit']
    self.assertAlmostEqual(dx*ux+dy*uy,10*math.cos(math.pi/6))
    self.assertAlmostEqual(-dx*uy+dy*ux,5)
 def test_rotation_does_not_move_motor_or_pad(self):
  p=Parameters(MotorHoleLayout='4-hole bolt circle',MotorBoltCircle=20)
  for a,b in zip(arm_layouts(p),arm_layouts(replace(p,MotorHoleRotation=45))):
   self.assertEqual(a['motor'],b['motor']);self.assertEqual(a['unit'],b['unit'])
 def test_rotation_range(self):
  self.assertTrue(validate(Parameters(MotorHoleRotation=361))[0])
  self.assertTrue(validate(Parameters(MotorHoleRotation=-361))[0])
