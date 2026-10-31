"""Equipment changes, symmetry, shared fasteners and saved defaults."""
import unittest,math
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate,standoff_layouts
from freecad.rotorforge.equipment_mass import equipment_items
class EquipmentEstimateTests(unittest.TestCase):
 def test_nominal_defaults(self):
  items=equipment_items(Parameters());motors=[i for i in items if i['part']=='Motor']
  self.assertEqual(len(motors),4);self.assertAlmostEqual(sum(i['mass_g'] for i in motors),122)
  self.assertAlmostEqual(sum(i['mass_g']*i['centre_mm'][0] for i in items),0)
 def test_zero_screw_scale_and_negative_mass(self):
  items=equipment_items(Parameters(ScrewMassScale=0))
  self.assertTrue(all(i['mass_g']==0 for i in items if 'screw' in i['part'].lower()))
  for name in ('MotorMass','FCMass','ESCMass','VTXMass','CameraMass','OtherMass','PropMass','ScrewMassScale'):
   self.assertTrue(validate(replace(Parameters(),**{name:-1}))[0],name)
 def test_visibility_independent_and_fpv_conditional(self):
  self.assertEqual(equipment_items(Parameters()),equipment_items(Parameters(ShowReferences=False)))
  for enabled in (False,True):
   names=[i['part'] for i in equipment_items(Parameters(FPVEnabled=enabled))]
   self.assertEqual('Camera' in names,enabled);self.assertEqual('VTX' in names,enabled)
 def test_standoff_counts_and_sharing(self):
  for count in ('4 (2 pairs)','6 (3 pairs)','8 (4 pairs)'):
   p=Parameters(StandoffCount=count);items=equipment_items(p)
   self.assertEqual(sum(i['part']=='Standoff top screw' for i in items),len(standoff_layouts(p)))
  p=Parameters(StandoffFrontMount='Arm outer hole',StandoffRearMount='Arm outer hole')
  items=equipment_items(p)
  self.assertEqual(sum(i['part']=='Shared arm screw' for i in items),4)
  self.assertEqual(sum(i['part']=='Arm root screw' for i in items),4)
  self.assertFalse(any(i['part']=='Standoff base screw' for i in items))
 def test_length_sensitive_stack_screws(self):
  def mass(p):return sum(i['mass_g'] for i in equipment_items(p) if i['part']=='Stack screw')
  self.assertGreater(mass(Parameters(StackHeight=20)),mass(Parameters(StackHeight=10)))
 def test_motor_pad_pivot_moves_mass(self):
  a=equipment_items(Parameters(MotorPadRotationPivot='Pad beginning',MotorPadRotation=0))
  b=equipment_items(Parameters(MotorPadRotationPivot='Pad beginning',MotorPadRotation=25))
  self.assertNotEqual([i['centre_mm'] for i in a if i['part']=='Motor'],[i['centre_mm'] for i in b if i['part']=='Motor'])
