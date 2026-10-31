import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,plate_levels
from freecad.rotorforge.protection_layout import guard_layout,guard_plate_gap,usb_window
class GuardClearanceTests(unittest.TestCase):
 def test_zero_and_small_gap_datums(self):
  for clearance,expected in ((0.,0.),(.05,.05),(1.,.15)):
   p=Parameters(FlexSideGuards=True,FlexGuardClearance=clearance);levels=plate_levels(p);self.assertEqual(guard_plate_gap(p),expected)
   for g in guard_layout(p):
    self.assertAlmostEqual(g['inner_bottom'],levels['deck_z']+expected);self.assertAlmostEqual(g['inner_top'],levels['top_z']-expected)
    self.assertAlmostEqual(g['z'],levels['mid_z']);self.assertAlmostEqual(g['top'],levels['top_z']+p.TopThickness)
 def test_usb_height_stays_anchored_to_carrier(self):
  zs=[]
  for gap in (0.,.05,1.):
   p=Parameters(FlexSideGuards=True,FlexGuardClearance=gap,FlexGuardExtendFront=True,FlexGuardUSBEnabled=True)
   zs.append(usb_window(p,guard_layout(p)[0])[1])
  self.assertEqual(zs,[zs[0]]*3)
 def test_zero_preview_starts_at_plate_edge(self):
  try:
   from freecad.rotorforge.flex_preview import guard_plan_path,_guard_plan_cached,QtCore,QtGui
  except ImportError:self.skipTest('Qt unavailable')
  from unittest.mock import patch
  plate=QtGui.QPainterPath();plate.addRect(QtCore.QRectF(-25,-100,50,200))
  p=Parameters(FlexSideGuards=True,FlexGuardClearance=0.)
  _guard_plan_cached.cache_clear()
  try:
   with patch('freecad.rotorforge.airflow_gui.finished_part_path',return_value=plate):
    path=guard_plan_path(p,guard_layout(p)[1]);self.assertTrue(path.contains(QtCore.QPointF(25.1,0)))
    q=replace(p,FlexGuardClearance=.05);path=guard_plan_path(q,guard_layout(q)[1]);self.assertFalse(path.contains(QtCore.QPointF(25.01,0)));self.assertTrue(path.contains(QtCore.QPointF(25.1,0)))
  finally:_guard_plan_cached.cache_clear()
