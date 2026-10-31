from dataclasses import replace
import unittest
from freecad.rotorforge.parameters import Parameters,arm_brace_layouts,arm_layouts,arm_clamp_interior_distance,stack_holes,validate
from freecad.rotorforge.clamp_outline import clamp_outline_layout
class ClampFollowTests(unittest.TestCase):
 def test_end_centres_removed_bolts_supported(self):
  for layout in ('True X','Stretched X','Deadcat'):
   for position in ('Above bottom plate','Below bottom plate'):
    p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,Layout=layout,TwoPlateArmPosition=position)
    c=arm_brace_layouts(p)[0]
    self.assertLess(arm_clamp_interior_distance((0,c['front']-1),p),0)
    self.assertLess(arm_clamp_interior_distance((0,c['rear']+1),p),0)
    self.assertFalse(validate(p)[0])
    for a in arm_layouts(p):
     for pt in a['bolts']:self.assertGreaterEqual(arm_clamp_interior_distance(pt,p),p.RootHoleDiameter/2+p.MinimumWeb-1e-6)
    for pt in stack_holes(p):self.assertGreaterEqual(arm_clamp_interior_distance(pt,p),p.StackHoleDiameter/2+p.MinimumWeb-1e-6)
 def test_preview_matches_trimmed_ends(self):
  from freecad.rotorforge.airflow_gui import clamp_plate_path,QtCore
  p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True);c=arm_brace_layouts(p)[0];path=clamp_plate_path(p)
  self.assertFalse(path.contains(QtCore.QPointF(0,c['front']-1)));self.assertFalse(path.contains(QtCore.QPointF(0,c['rear']+1)))
  for arm in arm_layouts(p):
   for pt in arm['bolts']:self.assertTrue(path.contains(QtCore.QPointF(*pt)))
 def test_local_standoff_pads(self):
  p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,StandoffFrontMount='Arm inner hole',StrapSlotsEnabled=False)
  self.assertFalse(validate(p)[0]);self.assertTrue(clamp_outline_layout(p)[2])
