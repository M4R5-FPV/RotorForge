"""Slots point to the actual stack centre and open only intersecting reliefs."""
from dataclasses import replace
from pathlib import Path
import math,sys,os,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters,stack_holes,validate
from freecad.rotorforge.stack_reliefs import stack_escape_segment
class StackEscapeGeometryTests(unittest.TestCase):
 def test_points_through_offset_stack_centre_and_outside_arm_bounds(self):
  for offset in (-17.,0.,23.):
   p=Parameters(StackOffsetY=offset)
   for pt in stack_holes(p):
    a,b,r=stack_escape_segment(p,pt,(-50,-60,50,70))
    d=(b[0]-a[0],b[1]-a[1]);c=(-a[0],offset-a[1])
    self.assertAlmostEqual(d[0]*c[1]-d[1]*c[0],0)
    self.assertGreater(d[0]*c[0]+d[1]*c[1],0)
    self.assertGreater(math.hypot(*d),math.hypot(*c))
    self.assertFalse(-50<=b[0]<=50 and -60<=b[1]<=70)
    self.assertEqual(a,pt);self.assertEqual(r,p.StackAccessDiameter/2)
 def test_width_and_long_root_clearance(self):
  for width in (4,6,8):
   p=Parameters(StackAccessDiameter=width)
   for pt in stack_holes(p):
    a,b,r=stack_escape_segment(p,pt,(-300,-300,300,300))
    self.assertEqual(r,width/2);self.assertTrue(abs(b[0])>300 or abs(b[1])>300)
 def test_old_settings_keep_round_reliefs_and_off_switch(self):
  p=Parameters();data=p.to_dict();data.pop('ArmRootReliefShape')
  self.assertEqual(Parameters.from_dict(data).ArmRootReliefShape,'Round hole')
  for enabled in (False,True):
   p=Parameters(ArmRootReliefsEnabled=enabled,ArmRootReliefShape='Slot toward stack centre')
   self.assertEqual(Parameters.from_dict(p.to_dict()),p)
 def test_invalid_shape_rejected(self):
  with self.assertRaises(ValueError):Parameters.from_dict(dict(Parameters().to_dict(),ArmRootReliefShape='slot backwards'))
try:
 from freecad.rotorforge.airflow_gui import QtCore,QtGui,QtWidgets,arm_stack_access_path
except ImportError:QtWidgets=None
@unittest.skipIf(QtWidgets is None,'Qt is supplied by FreeCAD')
class StackEscapePreviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
  cls.app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
 def blank(self):
  path=QtGui.QPainterPath();path.addRect(QtCore.QRectF(8,8,16,14));return path
 def test_round_is_closed_but_slot_opens_inward(self):
  p=Parameters();blank=self.blank()
  circle=arm_stack_access_path(p,blank)
  slot=arm_stack_access_path(replace(p,ArmRootReliefShape='Slot toward stack centre'),blank)
  self.assertTrue(circle.contains(QtCore.QPointF(9,9)))
  self.assertFalse(slot.contains(QtCore.QPointF(9,9)))
  self.assertFalse(slot.contains(QtCore.QPointF(15.25,15.25)))
  self.assertTrue(slot.contains(QtCore.QPointF(22,20)))
 def test_other_screws_do_not_cut_a_central_arm_piece(self):
  blank=QtGui.QPainterPath();blank.addRect(QtCore.QRectF(-2,-2,4,4))
  p=Parameters(ArmRootReliefShape='Slot toward stack centre')
  self.assertEqual(arm_stack_access_path(p,blank),blank)
 def test_disabled_reliefs_preserve_entire_arm(self):
  p=Parameters(ArmRootReliefShape='Slot toward stack centre',ArmRootReliefsEnabled=False)
  self.assertEqual(arm_stack_access_path(p,self.blank()),self.blank())
 def test_slot_width_uses_access_diameter(self):
  p=Parameters(ArmRootReliefShape='Slot toward stack centre',StackAccessDiameter=6)
  cut=arm_stack_access_path(p,self.blank())
  self.assertFalse(cut.contains(QtCore.QPointF(12,8)))
  self.assertTrue(cut.contains(QtCore.QPointF(12.4,8)))
 def test_offset_translates_both_screws_and_slot_direction(self):
  p=Parameters(ArmRootReliefShape='Slot toward stack centre')
  base=arm_stack_access_path(p,self.blank())
  move=QtGui.QTransform();move.translate(0,21)
  actual=arm_stack_access_path(replace(p,StackOffsetY=21),move.map(self.blank()))
  self.assertTrue(actual.subtracted(move.map(base)).isEmpty())
  self.assertTrue(move.map(base).subtracted(actual).isEmpty())
if __name__=='__main__':unittest.main()
