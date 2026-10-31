from pathlib import Path
import sys,unittest,tempfile,math
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters,validate,motor_hole_offsets,save_parameters,load_parameters
from freecad.rotorforge.motor_sizes import MOTOR_SIZES,apply_motor_size
class MotorSizingTests(unittest.TestCase):
 def test_circle_diameters_and_reference_sizes(self):
  for name in list(MOTOR_SIZES)[:4]:
   p=apply_motor_size(Parameters(),name);pitch=MOTOR_SIZES[name][0]
   self.assertEqual(p.MotorBoltCircle,pitch);self.assertEqual(p.MotorHoleLayout,'4-hole bolt circle');self.assertEqual(p.MotorHoleRotation,0)
   self.assertGreater(p.MotorReferenceDiameter,0);self.assertGreater(p.PropReferenceHeight,p.MotorReferenceHeight)
 def test_square_and_circle_are_distinct(self):
  square=motor_hole_offsets(Parameters.from_dict({'MotorHoleLayout':'Rectangle','MotorSpacingX':9,'MotorSpacingY':9}))
  circle=motor_hole_offsets(Parameters(MotorHoleLayout='4-hole bolt circle',MotorBoltCircle=9))
  self.assertNotEqual(square,circle)
  for pt in circle:self.assertAlmostEqual(math.hypot(*pt),4.5)
 def test_three_hole_circle(self):
  pts=motor_hole_offsets(Parameters(MotorHoleLayout='3-hole bolt circle',MotorBoltCircle=6.6));self.assertEqual(len(pts),3)
  for pt in pts:self.assertAlmostEqual(math.hypot(*pt),3.3)
 def test_legacy_defaults_retained(self):
  p=Parameters.from_dict({'MotorSpacingX':16,'MotorSpacingY':19});self.assertEqual(p.MotorHoleLayout,'4-hole bolt circle');self.assertTrue(any('Hole positions changed' in w for w in validate(p)[1]))

class PlateSettingsCompatibilityTests(unittest.TestCase):
 def test_old_plate_settings_keep_dimensions(self):
  p=Parameters.from_dict({'FrameStyle':'Plate frame','Wheelbase':280.,'ObsoleteFeatureSize':16.})
  self.assertEqual(p.Wheelbase,280.)
  self.assertNotIn('FrameStyle',p.to_dict())
 def test_unsupported_construction_is_not_reinterpreted(self):
  with self.assertRaisesRegex(ValueError,'no longer supported'):
   Parameters.from_dict({'FrameStyle':'Unsupported printed construction'})
 def test_current_settings_still_reject_unknown_keys(self):
  with self.assertRaisesRegex(ValueError,'Unknown parameter'):
   Parameters.from_dict({'MisspelledDimension':1.})
