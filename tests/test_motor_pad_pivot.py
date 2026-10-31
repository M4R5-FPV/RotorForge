"""Pivot kinematics, frame symmetry, clearance and backwards compatibility."""
import unittest,math,tempfile
from pathlib import Path
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,arm_layouts,motor_centres,nominal_motor_centres,prop_gap,save_parameters,load_parameters,validate
from freecad.rotorforge.motor_pads import motor_pad_start,MOTOR_PAD_SHAPES
class MotorPadPivotTests(unittest.TestCase):
 def test_old_settings_keep_centre_pivot(self):
  data=Parameters(MotorPadRotation=25).to_dict();data.pop('MotorPadRotationPivot')
  self.assertEqual(Parameters.from_dict(data).MotorPadRotationPivot,'Motor centre')
 def test_centre_mode_keeps_motor_positions(self):
  for layout in ('True X','Stretched X','Deadcat'):
   p=Parameters(Layout=layout,MotorPadRotation=65)
   self.assertEqual(motor_centres(p),nominal_motor_centres(p))
 def test_beginning_pivot_is_fixed_and_distance_is_preserved(self):
  for shape in MOTOR_PAD_SHAPES:
   for angle in (-65,0,35,90):
    p=Parameters(MotorPadShape=shape,MotorPadRotationPivot='Pad beginning',MotorPadRotation=angle)
    for a,nominal in zip(arm_layouts(p),nominal_motor_centres(p)):
     d=-motor_pad_start(p);ux,uy=a['unit'];pivot=(nominal[0]-d*ux,nominal[1]-d*uy)
     self.assertEqual(a['pad_pivot'],pivot)
     self.assertAlmostEqual(math.dist(pivot,a['motor']),d)
     self.assertAlmostEqual(a['motor'][0],pivot[0]+d*a['pad_unit'][0])
     self.assertAlmostEqual(a['motor'][1],pivot[1]+d*a['pad_unit'][1])
     self.assertEqual(a['beam_end'],pivot)
 def test_both_axes_reflect_and_roots_stay_fixed(self):
  for layout in ('True X','Stretched X','Deadcat'):
   p=Parameters(Layout=layout,MotorPadRotation=40,MotorPadRotationPivot='Pad beginning')
   arms=arm_layouts(p);base=arm_layouts(replace(p,MotorPadRotation=0))
   for a,b in zip(arms,base):
    for key in ('root','start','unit','bolts','beam_end'):self.assertEqual(a[key],b[key])
   for i,j in ((0,1),(2,3)):
    self.assertAlmostEqual(arms[i]['motor'][0],-arms[j]['motor'][0]);self.assertAlmostEqual(arms[i]['motor'][1],arms[j]['motor'][1])
 def test_props_follow_moved_motor_centres(self):
  p=Parameters(MotorPadRotation=50,MotorPadRotationPivot='Pad beginning')
  self.assertEqual(motor_centres(p),tuple(a['motor'] for a in arm_layouts(p)))
  self.assertNotEqual(motor_centres(p),nominal_motor_centres(p))
  self.assertNotEqual(prop_gap(p),prop_gap(replace(p,MotorPadRotation=0)))
 def test_moved_prop_overlap_is_rejected(self):
  p=Parameters(Layout='Deadcat',MotorPadShape='Crown shield',MotorPadRotationPivot='Pad beginning',MotorPadRotation=60,MotorHoleLayout='3-hole bolt circle',MotorBoltCircle=20)
  self.assertTrue(any('Propellers overlap' in e for e in validate(p)[0]))
 def test_settings_round_trip_and_bad_mode(self):
  p=Parameters(MotorPadRotation=30,MotorPadRotationPivot='Pad beginning')
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'frame.json';save_parameters(path,p);self.assertEqual(load_parameters(path),p)
  self.assertTrue(validate(replace(p,MotorPadRotationPivot='Invalid'))[0])
