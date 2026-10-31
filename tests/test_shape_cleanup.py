import unittest
from freecad.rotorforge.shape_cleanup import guard_refine
class Shape:
 def __init__(self,valid=True,count=1,result_valid=True,result_count=1,raises=False):
  self.valid=valid;self.Solids=[None]*count;self.result_valid=result_valid;self.result_count=result_count;self.raises=raises
 def isValid(self):return self.valid
 def copy(self):return Shape(self.valid,len(self.Solids),self.result_valid,self.result_count,self.raises)
 def removeSplitter(self):
  # Model OCC's in-place mutation, including a failed refinement.
  self.valid=self.result_valid;self.Solids=[None]*self.result_count
  if self.raises:raise RuntimeError('cleanup failed')
  return self
class GuardCleanupTests(unittest.TestCase):
 def test_valid_refinement_uses_independent_copy(self):
  source=Shape();result=guard_refine(source);self.assertIsNot(result,source);self.assertTrue(result.isValid());self.assertTrue(source.isValid())
 def test_invalid_refinement_keeps_original(self):
  source=Shape(result_valid=False);self.assertIs(guard_refine(source),source);self.assertTrue(source.isValid())
 def test_exception_cannot_damage_original(self):
  source=Shape(result_valid=False,raises=True);self.assertIs(guard_refine(source),source);self.assertTrue(source.isValid())
 def test_split_solids_are_not_accepted(self):
  source=Shape(result_count=2);self.assertIs(guard_refine(source),source);self.assertEqual(len(source.Solids),1)
 def test_lost_solids_are_not_accepted(self):
  source=Shape(count=2,result_count=1);self.assertIs(guard_refine(source),source)
 def test_invalid_input_stays_invalid_unless_repaired(self):
  source=Shape(valid=False,result_valid=False);self.assertFalse(guard_refine(source).isValid())
  self.assertTrue(guard_refine(Shape(valid=False,result_valid=True)).isValid())
