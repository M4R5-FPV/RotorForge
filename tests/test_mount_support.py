import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,arm_layouts,validate,plate_holes
from freecad.rotorforge.mount_support import arm_supports,plate_supports,plate_distance
from freecad.rotorforge.arm_roots import stem_interior_distance
class MountSupportTests(unittest.TestCase):
 def test_original_outlines_unchanged(self):
  p=Parameters()
  self.assertFalse(any(arm_supports(p,a) for a in arm_layouts(p)))
  for role in ('BottomPlate','MidPlate','TopPlate'):self.assertEqual(plate_supports(p,role),())
 def test_custom_arm_bolts_grow_all_receiving_plates(self):
  p=Parameters(RootBoltLayout='Custom coordinates',RootBolt1X=20,RootBolt1Y=0,RootBolt2X=35,RootBolt2Y=10)
  self.assertEqual(validate(p)[0],[])
  for a in arm_layouts(p):
   self.assertTrue(arm_supports(p,a))
   for pt in a['bolts']:self.assertGreaterEqual(stem_interior_distance(p,a,pt),p.RootHoleDiameter/2+p.MinimumWeb)
  for role in ('BottomPlate','MidPlate'):
   self.assertTrue(plate_supports(p,role))
   for pt,r,kind in plate_holes(p,role):
    if kind=='arm root':self.assertGreaterEqual(plate_distance(pt,p,role),r+p.MinimumWeb)
 def test_posts_outside_sides_and_ends(self):
  for design in ('2 plates','3 plates'):
   p=Parameters(PlateDesign=design,StandoffFrontMount='Custom position',StandoffRearMount='Custom position',StandoffWidth=85,StandoffLength=170)
   self.assertEqual(validate(p)[0],[])
   roles=('BottomPlate','TopPlate')+ (('MidPlate',) if design=='3 plates' else ())
   for role in roles:
    self.assertTrue(plate_supports(p,role))
    for pt,r,kind in plate_holes(p,role):
     if kind=='standoff':self.assertGreaterEqual(plate_distance(pt,p,role),p.StandoffDiameter/2+p.MinimumWeb)
 def test_growth_is_reversible(self):
  p=Parameters();q=replace(p,StandoffWidth=85,StandoffFrontMount='Custom position',StandoffRearMount='Custom position')
  self.assertTrue(plate_supports(q,'TopPlate'));self.assertEqual(plate_supports(p,'TopPlate'),())
 def test_close_holes_still_rejected(self):
  p=Parameters(RootBoltLayout='Custom coordinates',RootBolt1X=20,RootBolt2X=20,RootBolt1Y=0,RootBolt2Y=1)
  self.assertTrue(any('between' in s for s in validate(p)[0]))

class InsertStockTests(unittest.TestCase):
 def test_flange_uses_full_minimum_web(self):
  p=Parameters(RootBoltLayout='Custom coordinates',RootBolt1X=20,RootBolt1Y=0,RootBolt2X=35,RootBolt2Y=10,ArmNutMount='M3 press nut',MinimumWeb=2.5)
  supports=plate_supports(p,'MidPlate')
  self.assertTrue(supports)
  for pt,anchor,r in supports:self.assertGreaterEqual(r,p.PressNutFlangeDiameter/2+p.MinimumWeb)
 def test_recess_and_larger_insert_increase_stock(self):
  p=Parameters(RootBoltLayout='Custom coordinates',RootBolt1X=20,RootBolt1Y=0,RootBolt2X=35,RootBolt2Y=10,ArmNutMount='M3 press nut')
  a={pt:r for pt,anchor,r in plate_supports(p,'MidPlate')}
  q=replace(p,PressNutFlangeDiameter=8.,PressNutFlangeRecess=.3,NutRecessClearance=.4)
  for pt,anchor,r in plate_supports(q,'MidPlate'):
   self.assertGreater(r,a[pt]);self.assertGreaterEqual(r,4.2+p.MinimumWeb)
 def test_stack_insert_also_gains_stock(self):
  p=Parameters(StackPressNuts=True,BodyWidth=35)
  from freecad.rotorforge.parameters import stack_holes
  pads={pt:r for pt,anchor,r in plate_supports(p,'MidPlate')}
  for pt in stack_holes(p):self.assertGreaterEqual(pads[pt],p.PressNutFlangeDiameter/2+p.MinimumWeb)
