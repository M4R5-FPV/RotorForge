import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.protection_layout import guard_layout,guard_vent_sections,guard_vents,grip_bridge,outline_side_x
from freecad.rotorforge.flex import validate_flex
class GuardSections(unittest.TestCase):
 def setUp(self):self.p=Parameters(FlexSideGuards=True)
 def test_switches(self):
  for a,b,expected in ((True,False,{'VTX'}),(False,True,{'FC'}),(True,True,{'VTX','FC'}),(False,False,set())):
   p=replace(self.p,FlexGuardVTXVents=a,FlexGuardFCVents=b);self.assertEqual({v['section'] for v in guard_vents(p,guard_layout(p)[0])},expected)
 def test_independent_shapes_and_sizes(self):
  p=replace(self.p,FlexGuardVentShape='Hexagons',FlexGuardVentWidth=6.,FlexGuardSlotHeight=2.,FlexGuardSlotCount=1.,FlexGuardFCVentShape='Diamonds',FlexGuardFCVentWidth=9.,FlexGuardFCSlotHeight=4.)
  g=guard_layout(p)[0];vs=guard_vents(p,g);self.assertEqual({v['shape'] for v in vs},{'Hexagons','Diamonds'})
  for v in vs:
   if v['section']=='VTX':self.assertLessEqual(v['width'],6.);self.assertEqual(v['height'],2.)
   else:self.assertLessEqual(v['width'],9.)
 def test_boundary_and_insets(self):
  p=replace(self.p,StackOffsetY=5.,FlexGuardVentBoundaryOffset=-2.,FlexGuardVTXVentRearInset=3.,FlexGuardFCVentFrontInset=4.);g=guard_layout(p)[0];a,b=guard_vent_sections(p,g)
  self.assertEqual(a['front'],5-p.StackSpacing/2-2);self.assertEqual(a['rear'],g['rear']+3);self.assertEqual(b['front'],g['front']-4)
 def test_webs_and_shift_limits(self):
  for shift in (-100.,100.):
   p=replace(self.p,FlexGuardVTXVentZOffset=shift,FlexGuardFCVentZOffset=shift);g=guard_layout(p)[0]
   for v in guard_vents(p,g):
    self.assertGreaterEqual(v['z']-v['height']/2,g['z']+p.FlexGuardWall-1e-7);self.assertLessEqual(v['z']+v['height']/2,g['top']-p.FlexGuardWall+1e-7)
 def test_old_settings_seed_both(self):
  p=Parameters.from_dict(dict(FlexGuardVentShape='Chevrons',FlexGuardVentWidth=7.,FlexGuardSlotHeight=2.5,FlexGuardSlotCount=3.,FlexGuardVentWeb=4.))
  self.assertEqual((p.FlexGuardFCVentShape,p.FlexGuardFCVentWidth,p.FlexGuardFCSlotHeight,p.FlexGuardFCSlotCount,p.FlexGuardFCVentWeb),('Chevrons',7.,2.5,3.,4.))
 def test_bridge_mirrors(self):
  l,r=guard_layout(self.p);a,b,rad=grip_bridge(self.p,r,r['stands'][0],(46.,24.,24.,10.));c,d,rr=grip_bridge(self.p,l,l['stands'][0],(46.,-24.,-24.,10.));self.assertEqual(a,(-c[0],c[1]));self.assertEqual(b,(-d[0],d[1]));self.assertEqual(rad,rr)
 def test_no_opposite_edge(self):
  points=[(10.,1.),(20.,1.),(20.,2.),(10.,2.)];self.assertIsNone(outline_side_x(points,1.5,-1));self.assertEqual(outline_side_x(points,1.5,1),20.)
 def test_inactive_section(self):
  self.assertTrue(validate_flex(replace(self.p,FlexGuardFCSlotCount=0.))[0]);self.assertFalse(validate_flex(replace(self.p,FlexGuardFCVents=False,FlexGuardFCSlotCount=0.))[0])
 def test_roundtrip_and_location(self):
  from freecad.rotorforge.editor_sections import FIELD_LOCATION
  p=replace(self.p,FlexGuardVTXVents=False,FlexGuardFCVentShape='Ellipses',FlexGuardFCVentZOffset=-2.);self.assertEqual(Parameters.from_dict(p.to_dict()),p);self.assertEqual(FIELD_LOCATION['FlexGuardFCVentShape'][:2],('TPU','Side guard vents'))
