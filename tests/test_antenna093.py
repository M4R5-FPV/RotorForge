import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.antenna_layout import antenna_layout,validate_antenna
from freecad.rotorforge.parameter_memo import parameter_cache
from freecad.rotorforge.dependency_cache import TrackedParameters
class MountTests(unittest.TestCase):
 def test_bulkhead_thickness_independent_of_stem_length(self):
  p=replace(Parameters(),FlexRearAntenna=True,FlexAntennaConnector='SMA',FlexAntennaSocketLength=60)
  a=antenna_layout(p);self.assertEqual(a['length'],2.4);self.assertTrue(a['bulkhead']);self.assertGreaterEqual(a['radius'],6)
  self.assertEqual(antenna_layout(replace(p,FlexAntennaConnector='RP-SMA')),a)
  self.assertEqual(antenna_layout(replace(p,FlexAntennaConnector='u.FL'))['length'],60)
 def test_bulkhead_limits_and_persistence(self):
  p=replace(Parameters(),FlexRearAntenna=True,FlexAntennaConnector='SMA',FlexAntennaBulkheadThickness=3.1)
  self.assertEqual(Parameters.from_dict(p.to_dict()).FlexAntennaBulkheadThickness,3.1)
  self.assertTrue(validate_antenna(replace(p,FlexAntennaBulkheadThickness=8)))
 def test_layout_cache_reuses_unrelated_edits_and_retains_provenance(self):
  calls=[]
  @parameter_cache()
  def f(p):calls.append(1);return p.TopWidth if p.FPVEnabled else p.BodyWidth
  p=Parameters();f(p)
  q=TrackedParameters(*replace(p,FlexAntennaHolderOffset=12).signature());object.__setattr__(q,'_reads',set())
  self.assertEqual(f(q),p.BodyWidth);self.assertEqual(len(calls),1);self.assertEqual(q._reads,{'FPVEnabled','BodyWidth'})
  self.assertEqual(f(replace(p,FPVEnabled=True,TopWidth=51)),51);self.assertEqual(len(calls),2)
  f.cache_clear();f(p);self.assertEqual(len(calls),3)
