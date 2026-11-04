import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,arm_layouts
from freecad.rotorforge.dependency_cache import TrackedParameters

class LayoutCacheTests(unittest.TestCase):
 def test_results_keep_caller_ownership(self):
  p=Parameters();a=arm_layouts(p);original=a[0]['root'];a[0]['root']=(999,999);a.pop()
  b=arm_layouts(p);self.assertEqual(len(b),4);self.assertEqual(b[0]['root'],original)
 def test_warm_cache_retains_dependencies(self):
  p=Parameters();arm_layouts(p)
  tracked=TrackedParameters(*p.signature());object.__setattr__(tracked,'_reads',set());arm_layouts(tracked)
  self.assertIn('Wheelbase',tracked._reads);self.assertIn('RootExtension',tracked._reads)
 def test_changed_dimension_invalidates_layout(self):
  p=Parameters();a=arm_layouts(p);b=arm_layouts(replace(p,Wheelbase=p.Wheelbase+20))
  self.assertNotEqual(a[0]['motor'],b[0]['motor'])
