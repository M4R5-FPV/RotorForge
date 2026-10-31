import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.protection_layout import guard_layout,guard_strap_windows
from freecad.rotorforge.reference_options import enabled
class PowerStrapsTests(unittest.TestCase):
 def test_defaults_and_migration(self):
  p=Parameters.from_dict({})
  self.assertFalse(p.DetailedVTXReference);self.assertFalse(p.DetailedBatteryReference);self.assertFalse(p.FlexGuardStraps)
  q=replace(p,DetailedVTXReference=True,DetailedBatteryReference=True,FlexGuardStraps=True,FlexGuardStrapY2=-23.)
  self.assertEqual(Parameters.from_dict(q.to_dict()),q)
 def test_auto_and_custom_positions(self):
  p=Parameters(FlexSideGuards=True,FlexGuardStraps=True);g=guard_layout(p)[0]
  self.assertFalse(validate(p)[0]);self.assertEqual([w['y'] for w in guard_strap_windows(p,g)],[18.,-18.])
  q=replace(p,FlexGuardStrapCount='1 strap');self.assertEqual(len(guard_strap_windows(q,g)),1)
  q=replace(p,FlexGuardStrapAuto=False,StackOffsetY=3.,FlexGuardStrapY1=10.,FlexGuardStrapY2=-24.)
  self.assertEqual([w['y'] for w in guard_strap_windows(q,g)],[13.,-21.])
 def test_invalid_slots_and_grip_overlap(self):
  p=Parameters(FlexSideGuards=True,FlexGuardStraps=True)
  for kw in ({'FlexGuardStrapDepth':100.},{'FlexGuardStrapWidth':0.},{'FlexGuardStrapAuto':False,'FlexGuardStrapY1':46.},{'FlexGuardStrapAuto':False,'FlexGuardStrapY2':18.}):self.assertTrue(validate(replace(p,**kw))[0],kw)
 def test_preview_shows_the_selected_edge_notch(self):
  try:from freecad.rotorforge.flex_preview import flex_path
  except ImportError:self.skipTest('Qt unavailable')
  from freecad.rotorforge.airflow_gui import QtCore
  p=Parameters(FlexSideGuards=True,FlexGuardStyle='Solid',FlexGuardStraps=True)
  g=guard_layout(p)[0];point=QtCore.QPointF(p.StrapOffsetY,g['top']-.5)
  self.assertFalse(flex_path(p,'ElectronicsGuardLeft').contains(point))
  self.assertTrue(flex_path(replace(p,FlexGuardStraps=False),'ElectronicsGuardLeft').contains(point))
