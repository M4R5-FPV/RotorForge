import unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,bottom_bounds,validate
from freecad.rotorforge.bottom_nose import NOSE_SHAPES,nose_commands,nose_polygon
from freecad.rotorforge.plate_profiles import profiled_interior_distance
class BottomNoseTests(unittest.TestCase):
 def setUp(self):self.p=Parameters()
 def test_straight_is_default_and_does_not_add_a_mask(self):
  self.assertEqual(self.p.BottomNoseShape,'Straight');self.assertEqual(nose_commands(self.p,50,-40,82.5),())
  self.assertEqual(Parameters.from_dict({}).BottomNoseShape,'Straight')
 def test_all_profiles_are_symmetric_and_stay_inside_front_reach(self):
  for name in NOSE_SHAPES[1:]:
   p=replace(self.p,BottomNoseShape=name);poly=nose_polygon(p,50,-40,82.5);self.assertTrue(poly);self.assertLessEqual(max(y for x,y in poly),82.5+1e-9)
   for x,y in poly:self.assertLess(min(abs(xx+x)+abs(yy-y) for xx,yy in poly),1e-6,name)
 def test_point_and_notch_have_different_central_material(self):
  point=replace(self.p,BottomNoseShape='Pointed nose');notch=replace(self.p,BottomNoseShape='V-notch')
  self.assertGreater(profiled_interior_distance((0,80),point,'BottomPlate',50,-40,82.5,5),0)
  self.assertLess(profiled_interior_distance((0,80),notch,'BottomPlate',50,-40,82.5,5),0)
 def test_tip_width_and_depth_change_the_shape(self):
  p=replace(self.p,BottomNoseShape='Flat-tip nose');a=nose_commands(p,50,-40,82.5);self.assertNotEqual(a,nose_commands(replace(p,BottomNoseTipWidth=65.),50,-40,82.5));self.assertNotEqual(a,nose_commands(replace(p,BottomNoseDepth=12.),50,-40,82.5))
 def test_centre_widening_does_not_refill_the_nose_cut(self):
  p=replace(self.p,BottomNoseShape='V-notch',BottomCentreWidth=80.,CentreSectionLength=180.)
  self.assertLess(profiled_interior_distance((0,80),p,'BottomPlate',50,-40,82.5,5),0)
 def test_limits_hardware_checks_and_roundtrip(self):
  p=replace(self.p,BottomNoseShape='Rounded nose');self.assertFalse(validate(p)[0]);self.assertEqual(Parameters.from_dict(p.to_dict()),p)
  self.assertTrue(validate(replace(p,BottomNoseDepth=0))[0]);self.assertTrue(validate(replace(p,BottomNoseDepth=1000))[0]);self.assertTrue(validate(replace(p,BottomNoseTipWidth=0))[0])
  self.assertTrue(validate(replace(p,BottomNoseShape='Pointed nose',BottomNoseDepth=60.))[0])
 def test_preview_changes_front_material_without_importing_cad(self):
  try:
   from freecad.rotorforge.airflow_gui import bottom_plate_path,QtCore
  except ImportError:self.skipTest('Qt unavailable')
  p=replace(self.p,BottomNoseShape='V-notch');f=bottom_bounds(p)[1]
  self.assertTrue(bottom_plate_path(self.p).contains(QtCore.QPointF(0,f-2)))
  self.assertFalse(bottom_plate_path(p).contains(QtCore.QPointF(0,f-2)))

 def test_camera_following_keeps_the_full_bottom_contact_supported(self):
  from freecad.rotorforge.fpv import camera_mounts
  from freecad.rotorforge.parameters import bottom_interior_distance
  for name in NOSE_SHAPES[1:]:
   p=replace(self.p,FPVEnabled=True,BottomNoseShape=name);self.assertFalse(validate(p)[0],name)
   for mount in camera_mounts(p):
    for x in mount['plate_x']:
     for y,z in mount['attachment_profile'][:2]:self.assertGreaterEqual(bottom_interior_distance((x,y),p),p.MinimumWeb-1e-6)
 def test_trimmed_export_cubic_preserves_curve_points(self):
  from freecad.rotorforge.bezier import trim_cubic
  def value(pts,t):return tuple((1-t)**3*pts[0][j]+3*(1-t)**2*t*pts[1][j]+3*(1-t)*t*t*pts[2][j]+t**3*pts[3][j] for j in range(2))
  points=((0.,0.),(0.,8.),(5.,8.),(5.,0.));cut=trim_cubic(points,.2,.7)
  for t in (0.,.25,.5,.75,1.):
   for a,b in zip(value(cut,t),value(points,.2+.5*t)):self.assertAlmostEqual(a,b,places=10)

 def test_middle_only_widening_does_not_change_the_nose_or_get_trimmed(self):
  p=replace(self.p,BottomNoseShape='Rounded nose');q=replace(p,BottomCentreWidth=80.)
  a=[c for c in nose_commands(p,50,-40,82.5) if c[0]=='C'];b=[c for c in nose_commands(q,50,-40,82.5) if c[0]=='C'];self.assertEqual(a,b)
  self.assertGreater(profiled_interior_distance((35,0),q,'BottomPlate',50,-40,82.5,5),0)
