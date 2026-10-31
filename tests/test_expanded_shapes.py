"""Contracts for the FC selector and shared planar outline families."""
import unittest,sys,math,warnings
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters,STACK_PATTERNS,validate,arm_layouts
from freecad.rotorforge.motor_pads import MOTOR_PAD_SHAPES,NEW_MOTOR_PAD_SHAPES,motor_tip_slots
from freecad.rotorforge.design_options import OPTIONS,ARM_BEAM_SHAPES,PLATE_SHAPES,MOTOR_PAD_RELIEFS
from freecad.rotorforge.plate_profiles import plate_base_polygon,polygon_interior_distance
from freecad.rotorforge.arm_roots import beam_profile_polygon
from freecad.rotorforge.cutouts import CUTOUT_TYPES,cutout_polygon,encode_patterns,parse_patterns
class ExpandedShapeTests(unittest.TestCase):
 def test_standard_stack_dimensions_and_height(self):
  self.assertEqual([n for text,n in STACK_PATTERNS],[20.,30.5])
  for size in (20.,30.5):
   p=Parameters(StackSpacing=size,StackMountHeight=4,StackHeight=16)
   self.assertEqual(validate(p)[0],[]);self.assertEqual(Parameters.from_dict(p.to_dict()),p)
  self.assertTrue(validate(Parameters(StackSpacing=25.5))[0])
  with warnings.catch_warnings(record=True) as recorded:
   warnings.simplefilter('always');p=Parameters.from_dict(dict(StackSpacing=25.5,StackHeight=17))
   self.assertEqual(p.StackSpacing,30.5);self.assertEqual(p.StackHeight,17);self.assertTrue(recorded)
 def test_all_new_pads_and_reliefs_support_default_hardware(self):
  self.assertEqual(len(NEW_MOTOR_PAD_SHAPES),12);self.assertEqual(len(MOTOR_PAD_SHAPES),22)
  for name in NEW_MOTOR_PAD_SHAPES:
   for relief in MOTOR_PAD_RELIEFS:
    p=Parameters(MotorPadShape=name,MotorPadRelief=relief)
    self.assertEqual(validate(p)[0],[],(name,relief))
    self.assertEqual(len(motor_tip_slots(p)),0 if relief=='None' else 1 if relief=='Neck slot' else 2)
 def test_beam_axes_and_roots_stay_fixed(self):
  base=arm_layouts(Parameters())
  for name in ARM_BEAM_SHAPES[1:]:
   p=Parameters(ArmBeamShape=name);arms=arm_layouts(p)
   self.assertEqual(arms,base);self.assertEqual(validate(p)[0],[])
   poly=beam_profile_polygon(p,arms[0]);self.assertTrue(poly)
   self.assertEqual(poly,beam_profile_polygon(Parameters.from_dict(p.to_dict()),arms[0]))
 def test_plate_and_cutout_families(self):
  for name in PLATE_SHAPES:
   p=Parameters(BottomPlateShape=name,MidPlateShape=name,TopPlateShape=name)
   self.assertEqual(validate(p)[0],[],name)
  self.assertEqual(len(CUTOUT_TYPES),20)
  for name in CUTOUT_TYPES[12:]:
   pattern=dict(shape=name,width=8,length=12)
   points=cutout_polygon(pattern)
   self.assertGreaterEqual(len(points),4)
   self.assertAlmostEqual(min(x for x,y in points),-4,places=6)
   self.assertAlmostEqual(max(y for x,y in points),6,places=6)
   self.assertEqual(parse_patterns(encode_patterns([pattern]))[0]['shape'],name)
 def test_invalid_new_numeric_values(self):
  for key in ('MotorPadBlendRadius','ArmProfileAmount','PlateEndWidth','MotorPadReliefWidth'):
   self.assertTrue(validate(replace(Parameters(),**{key:math.nan}))[0],key)
  self.assertTrue(validate(Parameters(MotorPadShape='Round-shoulder shield',MotorPadRelief='Neck slot',MotorPadReliefWidth=7,MotorPadReliefLength=3))[0])
if __name__=='__main__':unittest.main()
