"""Inset fit must sit under both plates and retain a usable preview."""
import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,plate_levels
from freecad.rotorforge.protection_layout import guard_layout,guard_wall_inner_x

class GuardInset0891Tests(unittest.TestCase):
 def test_between_plates_contacts_faces_for_all_clearances(self):
  for design in ('2 plates','3 plates'):
   for arms in ('Above bottom plate','Below bottom plate'):
    for clearance in (0.,.05,1.,2.):
     p=Parameters(PlateDesign=design,TwoPlateArmPosition=arms,FlexSideGuards=True,
                  FlexGuardFitMode='Between plates',FlexGuardClearance=clearance)
     lv=plate_levels(p)
     for g in guard_layout(p):
      self.assertEqual(g['z'],lv['deck_z'])
      self.assertEqual(g['top'],lv['top_z'])

 def test_entire_wall_is_inside_each_edge_and_mirrored(self):
  for clearance in (0.,.5,2.):
   for thickness in (1.,2.,3.):
    p=Parameters(FlexGuardFitMode='Between plates',FlexGuardClearance=clearance,FlexGuardWall=thickness)
    for sign in (-1,1):
     inner=guard_wall_inner_x(p,sign*25.,sign)
     outer=inner+sign*thickness
     self.assertAlmostEqual(sign*outer,25.-clearance)
     self.assertAlmostEqual(sign*inner,25.-clearance-thickness)
     self.assertAlmostEqual(guard_wall_inner_x(replace(p,FlexGuardFitMode='Plate-edge wrap'),sign*25.,sign),sign*(25.+clearance))

 def test_plan_preview_moves_inside_and_preserves_post_bores(self):
  from freecad.rotorforge.flex_preview import guard_plan_path,QtCore
  p=Parameters(FlexSideGuards=True,FlexGuardFitMode='Between plates',FlexGuardStyle='Solid')
  for g in guard_layout(p):
   path=guard_plan_path(p,g);s=g['sign']
   self.assertTrue(path.contains(QtCore.QPointF(s*21.,0.)))
   self.assertFalse(path.contains(QtCore.QPointF(s*26.,0.)))
   for stand in g['stands']:self.assertFalse(path.contains(QtCore.QPointF(*stand['point'])))
   wrap=guard_plan_path(replace(p,FlexGuardFitMode='Plate-edge wrap'),g)
   self.assertFalse(wrap.contains(QtCore.QPointF(s*21.,0.)))
   self.assertTrue(wrap.contains(QtCore.QPointF(s*26.5,0.)))

 def test_larger_inset_moves_preview_toward_centre(self):
  from freecad.rotorforge.flex_preview import guard_plan_path,QtCore
  p=Parameters(FlexSideGuards=True,FlexGuardFitMode='Between plates',FlexGuardClearance=0.)
  for g in guard_layout(p):
   original=guard_plan_path(p,g);inset=guard_plan_path(replace(p,FlexGuardClearance=2.),g)
   self.assertAlmostEqual(inset.boundingRect().width(),original.boundingRect().width()-2.,places=5)
   s=g['sign'];self.assertTrue(original.contains(QtCore.QPointF(s*24.,0.)))
   self.assertFalse(inset.contains(QtCore.QPointF(s*24.,0.)))

if __name__=='__main__':unittest.main()
