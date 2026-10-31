"""Fast inspection views include finished holes and respond to active parts."""
import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,stack_holes
try:
 from freecad.rotorforge.part_preview import part_path,preview_roles,pad_path
 from freecad.rotorforge.airflow_gui import QtCore
 HAS_QT=True
except ImportError:HAS_QT=False
@unittest.skipUnless(HAS_QT,'Qt is supplied by FreeCAD')
class PartPreviewTests(unittest.TestCase):
 def test_active_parts_follow_plate_mode(self):
  p=Parameters(PlateDesign='3 plates',LiPoPadEnabled=True)
  self.assertIn('MidPlate',preview_roles(p));self.assertIn('LiPoPad',preview_roles(p))
  self.assertNotIn('MidPlate',preview_roles(replace(p,PlateDesign='2 plates')))
 def test_plate_holes_are_void(self):
  p=Parameters()
  for role in ('BottomPlate','MidPlate'):
   path=part_path(p,role)
   for x,y in stack_holes(p):self.assertFalse(path.contains(QtCore.QPointF(x,y)))
 def test_arm_holes_and_tip_slot_are_void(self):
  from freecad.rotorforge.parameters import arm_layouts
  p=Parameters(MotorPadShape='Arrowhead',MotorTipSlotEnabled=True)
  a=arm_layouts(p)[0];path=part_path(p,'ArmFrontRight',align=False)
  for pt in [*a['bolts'],*a['motor_holes'],a['motor']]:self.assertFalse(path.contains(QtCore.QPointF(*pt)))
 def test_saved_cutouts_change_inspection(self):
  import json
  from freecad.rotorforge.cutouts import PATTERN_DEFAULTS
  p=Parameters();before=part_path(p,'TopPlate')
  pattern=dict(PATTERN_DEFAULTS,role='TopPlate',shape='Circle',width=5.,length=5.,x=0.,y=0.,columns=1,rows=1,enabled=True)
  after=part_path(replace(p,CutoutPatterns=json.dumps([pattern])),'TopPlate')
  self.assertTrue(before.contains(QtCore.QPointF(0,0)));self.assertFalse(after.contains(QtCore.QPointF(0,0)))
 def test_pad_follows_carrier_when_requested(self):
  p=Parameters(LiPoPadEnabled=True,LiPoPadWidth=200,LiPoPadLength=200)
  self.assertLess(pad_path(p).boundingRect().width(),200)
  self.assertAlmostEqual(pad_path(replace(p,LiPoPadFollowPlate=False)).boundingRect().width(),200)
