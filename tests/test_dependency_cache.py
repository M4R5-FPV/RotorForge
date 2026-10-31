import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.dependency_cache import ComponentCache,clear_geometry_caches
from freecad.rotorforge.parameter_memo import parameter_cache
class Shape:
 def __init__(self,value):self.value=value;self.Placement=0;self.Orientation='Forward'
 def isNull(self):return False
 def hashCode(self):return 1
 def isSame(self,other):return self.value==other.value
 def copy(self):return Shape(self.value)
 def exportBrepToString(self):return str(self.value)
class DependencyTests(unittest.TestCase):
 def setUp(self):clear_geometry_caches();self.cache=ComponentCache();self.p=Parameters();self.calls=[]
 def build(self,p,inputs):self.calls.append(p.TopWidth);return Shape(p.TopWidth)
 def test_unrelated_values_reuse_and_outputs_are_copies(self):
  a=self.cache.get('top',self.p,{},self.build);a.value=-1
  b=self.cache.get('top',replace(self.p,FlexGuardWall=3.),{},self.build)
  self.assertEqual(b.value,self.p.TopWidth);self.assertEqual(len(self.calls),1)
  self.cache.get('top',replace(self.p,TopWidth=50.),{},self.build);self.assertEqual(len(self.calls),2)
 def test_branch_dependencies_retraced_after_toggle(self):
  def make(p,i):self.calls.append(1);return Shape(p.TopWidth if p.FPVEnabled else p.BodyWidth)
  self.cache.get('x',self.p,{},make);self.cache.get('x',replace(self.p,TopWidth=60),{},make);self.assertEqual(len(self.calls),1)
  self.cache.get('x',replace(self.p,FPVEnabled=True,TopWidth=60),{},make);self.assertEqual(len(self.calls),2)
 def test_upstream_only_when_read_and_hash_collision_safe(self):
  def make(p,i):self.calls.append(1);return Shape(i['Top'].value+p.TopThickness)
  self.cache.get('pad',self.p,{'Top':Shape(1),'Arm':Shape(4)},make)
  self.cache.get('pad',self.p,{'Top':Shape(1),'Arm':Shape(9)},make);self.assertEqual(len(self.calls),1)
  self.cache.get('pad',self.p,{'Top':Shape(2),'Arm':Shape(9)},make);self.assertEqual(len(self.calls),2)
 def test_memoized_layout_still_records_reads_when_warm(self):
  @parameter_cache()
  def layout(p):return p.TopWidth
  layout(self.p)
  def make(p,i):self.calls.append(1);return Shape(layout(p))
  self.cache.get('top',self.p,{},make);self.cache.get('top',replace(self.p,TopWidth=55.),{},make)
  self.assertEqual(len(self.calls),2)
 def test_provenance_roundtrip_and_modified_shape_rejected(self):
  s=self.cache.get('top',self.p,{},self.build);manifest=self.cache.manifest('top');self.cache.clear()
  self.assertTrue(self.cache.seed('top',manifest,s));self.cache.get('top',replace(self.p,FlexGuardWall=3),{},self.build);self.assertEqual(len(self.calls),1)
  self.assertFalse(self.cache.seed('top',manifest,Shape(-2)));self.assertFalse(self.cache.seed('arm',manifest,s));self.assertFalse(self.cache.seed('top','{}',s))
 def test_failed_factory_never_publishes_a_cache_entry(self):
  def fail(p,i):raise ValueError('bad')
  with self.assertRaises(ValueError):self.cache.get('bad',self.p,{},fail)
  self.assertFalse(self.cache.manifest('bad'))
 def test_entries_are_bounded(self):
  self.cache=ComponentCache(max_entries=2)
  for width in (40.,50.,60.):self.cache.get('top',replace(self.p,TopWidth=width),{},self.build)
  self.assertEqual(len(self.cache.entries),2)
 def test_oversized_result_is_returned_without_retention(self):
  self.cache=ComponentCache(max_bytes=1)
  s=self.cache.get('top',self.p,{},self.build)
  self.assertEqual(s.value,self.p.TopWidth);self.assertFalse(self.cache.entries)
 def test_validation_warnings_are_not_shared(self):
  from freecad.rotorforge.parameters import require_valid
  warnings=require_valid(self.p);warnings.append('mutated');self.assertNotIn('mutated',require_valid(self.p))

class ParameterSnapshotTests(unittest.TestCase):
 def test_replaced_snapshot_and_cold_warm_dependencies(self):
  from freecad.rotorforge.parameter_memo import parameter_signature
  from freecad.rotorforge.dependency_cache import TrackedParameters
  p=Parameters();first=parameter_signature(p)
  self.assertIs(first,parameter_signature(p));self.assertNotIn('_parameter_signature',p.to_dict())
  self.assertNotEqual(first,parameter_signature(replace(p,TopWidth=p.TopWidth+3)))
  @parameter_cache()
  def branch(p):return p.TopWidth if p.FPVEnabled else p.BodyWidth
  for enabled in (False,False,True,True):
   traced=TrackedParameters(*replace(p,FPVEnabled=enabled).signature());object.__setattr__(traced,'_reads',set())
   branch(traced);self.assertEqual(traced._reads,{'FPVEnabled','TopWidth' if enabled else 'BodyWidth'})
 def test_cached_validation_retains_errors_and_returns_fresh_lists(self):
  from freecad.rotorforge.parameters import validate
  p=Parameters();a,b=validate(p);a.append('foreign error');b.append('foreign warning')
  self.assertNotIn('foreign error',validate(p)[0]);self.assertNotIn('foreign warning',validate(p)[1])
  q=replace(p,TopThickness=-1)
  self.assertTrue(validate(q)[0]);self.assertTrue(validate(q)[0]);self.assertFalse(validate(p)[0])
 def test_seed_uses_supplied_brep_without_reserializing(self):
  from unittest.mock import patch
  cache=ComponentCache();p=Parameters();s=cache.get('top',p,{},lambda p,i:Shape(p.TopWidth));m=cache.manifest('top');cache.clear()
  with patch.object(Shape,'exportBrepToString',side_effect=AssertionError('duplicate serialization')):
   self.assertTrue(cache.seed('top',m,s,str(s.value)))
