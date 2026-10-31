import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.airflow_gui import QtGui,QtCore
from freecad.rotorforge.plate_fillets import preview_fillet
class FilletPreviewTests(unittest.TestCase):
 def path(self):
  p=QtGui.QPainterPath();p.setFillRule(QtCore.Qt.OddEvenFill);p.addRect(-30,-40,60,80);p.addRect(-5,-8,10,16);p.addEllipse(QtCore.QPointF(15,20),2,2);return p
 def test_outer_and_internal_cutout_corners_are_rounded(self):
  original=self.path();p=preview_fillet(Parameters(TopEdgeFillet=3,TopFilletOpenings=True),'TopPlate',original)
  self.assertTrue(original.contains(QtCore.QPointF(29.8,39.8)));self.assertFalse(p.contains(QtCore.QPointF(29.8,39.8)))
  self.assertFalse(original.contains(QtCore.QPointF(4.8,7.8)));self.assertTrue(p.contains(QtCore.QPointF(4.8,7.8)))
 def test_circular_holes_and_zero_setting_keep_their_geometry(self):
  original=self.path();self.assertEqual(preview_fillet(Parameters(),'TopPlate',original),original)
  p=preview_fillet(Parameters(TopEdgeFillet=3,TopFilletOpenings=True),'TopPlate',original)
  self.assertFalse(p.contains(QtCore.QPointF(16.8,20)));self.assertTrue(p.contains(QtCore.QPointF(17.2,20)))
if __name__=='__main__':unittest.main()
