import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,plate_holes,validate,stack_holes
from freecad.rotorforge.nut_seats import seats,validate_seats
from freecad.rotorforge.hardware_layout import hardware_layout
class NutSeatTests(unittest.TestCase):
 def test_default_preserves_geometry(self):self.assertEqual(seats(Parameters()),[])
 def test_only_receiver_plate_gets_press_holes(self):
  p=Parameters(PlateDesign='3 plates',ArmNutMount='M3 press nut');self.assertEqual({s['role'] for s in seats(p)},{'MidPlate'})
  hs=plate_holes(p,'MidPlate');self.assertTrue(all(abs(r-2.11)<1e-6 for pt,r,k in hs if k=='arm root'))
  self.assertTrue(all(r==p.StackHoleDiameter/2 for pt,r,k in hs if k=='stack'))
 def test_stack_never_gets_press_nuts(self):
  p=Parameters(ArmNutMount='M3 press nut');hw=hardware_layout(p,dict(nuts=False));stack=[s for s in hw if s['group']=='Stack hardware'];self.assertTrue(all(s['nut'] and not s.get('press') for s in stack))
 def test_two_plate_receiver_faces(self):
  for pos,axis in [('Above bottom plate',-1),('Below bottom plate',1)]:
   p=Parameters(PlateDesign='2 plates',TwoPlateArmPosition=pos,ArmNutMount='Recessed hex nut');self.assertTrue(all(s['role']=='BottomPlate' and s['axis']==axis for s in seats(p)))
 def test_minimum_carbon_and_shank_fit(self):
  self.assertTrue(validate_seats(Parameters(ArmNutMount='M3 press nut',BottomThickness=1.4,PlateDesign='2 plates')))
  self.assertTrue(validate_seats(Parameters(ArmNutMount='Recessed hex nut',NutRecessDepth=2.5)))
 def test_vtx_has_no_retention(self):
  p=Parameters(FPVEnabled=True);self.assertTrue(all(not s['nut'] and not s.get('press') for s in hardware_layout(p) if s['group']=='VTX hardware'))
 def test_stack_lift_and_upper_nuts(self):
  from freecad.rotorforge.parameters import stack_reference_z,plate_levels
  p=Parameters(StackPressNuts=True);self.assertAlmostEqual(stack_reference_z(p)-plate_levels(p)['stack_deck_z'],1.5)
  specs=[s for s in hardware_layout(p) if s['group']=='Stack hardware'];self.assertEqual(len(specs),4)
  for s in specs:
   self.assertTrue(s['nut'] and s['press'] and not s.get('stud'));self.assertAlmostEqual(s['point'][2]+s['nut_distance'],stack_reference_z(p)+p.StackHeight)
  for s in specs:self.assertAlmostEqual(s['point'][2],plate_levels(p)['stack_deck_z']-p.ClampThickness)
  q=replace(p,StackMountHeight=7.);self.assertAlmostEqual(stack_reference_z(q)-plate_levels(q)['stack_deck_z'],1.5)
  for recess in (0.,.2,1.5):
   q=replace(p,PressNutFlangeRecess=recess);self.assertAlmostEqual(stack_reference_z(q)-plate_levels(q)['stack_deck_z'],max(0.,1.5-recess))
  q=replace(p,StackPressNuts=False,StackMountHeight=7.);self.assertAlmostEqual(stack_reference_z(q)-plate_levels(q)['stack_deck_z'],7.)
 def test_stack_bores_only_change_receiver(self):
  p=Parameters(StackPressNuts=True);self.assertEqual(len(seats(p)),4)
  self.assertTrue(all(r==p.PressNutBore/2 for pt,r,k in plate_holes(p,'MidPlate') if k=='stack'))
 def test_button_heads_no_display_washers(self):
  self.assertTrue(all('washer' not in s for s in hardware_layout(Parameters())))
 def test_roundthrough_and_recess_depth_separate(self):
  p=Parameters(ArmNutMount='M3 press nut',PressNutFlangeRecess=.2,PlateDesign='3 plates');self.assertFalse(validate_seats(p));self.assertTrue(all(s['depth']==.2 for s in seats(p)))
