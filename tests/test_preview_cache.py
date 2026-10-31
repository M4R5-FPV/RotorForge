"""Cached previews must be reused without sharing mutable painter paths."""
import unittest
from dataclasses import replace
try:
 from freecad.rotorforge.airflow_gui import QtGui,finished_part_path,_finished_part_path_cached
except ImportError:QtGui=None
from freecad.rotorforge.parameters import Parameters
class PreviewCacheTests(unittest.TestCase):
 @unittest.skipIf(QtGui is None,'Qt bindings unavailable')
 def test_returned_paths_cannot_poison_later_paints(self):
  p=Parameters();a=finished_part_path(p,'TopPlate');bounds=a.boundingRect();a.addRect(1000,1000,20,20)
  self.assertEqual(finished_part_path(p,'TopPlate').boundingRect(),bounds)
 @unittest.skipIf(QtGui is None,'Qt bindings unavailable')
 def test_guard_tuning_reuses_carbon_paths(self):
  _finished_part_path_cached.cache_clear();p=Parameters();a=finished_part_path(p,'TopPlate');misses=_finished_part_path_cached.cache_info().misses
  for width in (10.,11.,12.):self.assertEqual(finished_part_path(replace(p,FlexSideGuards=True,FlexGuardVentWidth=width),'TopPlate').boundingRect(),a.boundingRect())
  self.assertEqual(_finished_part_path_cached.cache_info().misses,misses)
 @unittest.skipIf(QtGui is None,'Qt bindings unavailable')
 def test_real_plate_changes_invalidate_preview(self):
  p=Parameters(TopReachMode='Custom');a=finished_part_path(p,'TopPlate');b=finished_part_path(replace(p,TopRearReach=p.TopRearReach+20),'TopPlate')
  self.assertNotEqual(a.boundingRect(),b.boundingRect())

 @unittest.skipIf(QtGui is None,'Qt bindings unavailable')
 def test_side_guard_does_not_trace_internal_plate_holes(self):
  from freecad.rotorforge.flex_preview import guard_plan_path
  from freecad.rotorforge.protection_layout import guard_layout
  from freecad.rotorforge.airflow_gui import QtCore
  p=Parameters(FlexSideGuards=True)
  path=guard_plan_path(p,guard_layout(p)[1]);self.assertFalse(path.contains(QtCore.QPointF(20,-30)))
