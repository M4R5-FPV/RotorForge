import unittest,math
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate,top_bounds,top_interior_distance
from freecad.rotorforge.bottom_nose import TOP_FRONT_SHAPES,CAMERA_FRONT_SHAPES,edge_commands,edge_polygon,camera_recess_width
from freecad.rotorforge.fpv import camera_mounts
class TopFrontTests(unittest.TestCase):
 def test_older_frames_keep_the_existing_top_front(self):
  p=Parameters.from_dict({})
  self.assertEqual(p.TopFrontShape,'Straight')
  self.assertFalse(edge_commands(p,'TopPlate','Front',40,-90,90))
 def test_profiles_are_finite_symmetric_and_trim_only(self):
  from shapely.geometry import Polygon
  for shape in TOP_FRONT_SHAPES[1:]:
   p=Parameters(TopFrontShape=shape)
   pts=edge_polygon(p,'TopPlate','Front',50,-90,90)
   self.assertTrue(Polygon(pts).is_valid,shape)
   self.assertLessEqual(max(y for x,y in pts),90)
   for x,y in pts:
    self.assertTrue(math.isfinite(x+y))
    self.assertLess(min(abs(xx+x)+abs(yy-y) for xx,yy in pts),1e-6,shape)
 def test_camera_recess_depth_and_setback_are_independent(self):
  for shape in CAMERA_FRONT_SHAPES:
   p=Parameters(TopFrontShape=shape,TopFrontRecessWidth=22.,TopFrontDepth=12.,TopFrontSetback=5.)
   a=edge_polygon(p,'TopPlate','Front',50,-90,90)
   edgepts=[(x,y) for x,y in a if y>40]
   self.assertAlmostEqual(max(y for x,y in edgepts),85)
   self.assertAlmostEqual(min(y for x,y in edgepts),73)
   self.assertNotEqual(a,edge_polygon(replace(p,TopFrontRecessWidth=26.),'TopPlate','Front',50,-90,90))
 def test_auto_width_tracks_camera_and_custom_width_overrides(self):
  p=Parameters();self.assertEqual(camera_recess_width(p),p.CameraWidth+2*p.TopFrontClearance)
  self.assertEqual(camera_recess_width(replace(p,TopFrontRecessWidth=26.,CameraWidth=14.)),26.)
 def test_camera_contacts_and_selected_recess_are_supported(self):
  for shape in CAMERA_FRONT_SHAPES:
   p=Parameters(FPVEnabled=True,TopFrontShape=shape,StandoffHeight=35.,CameraTilt=55.,CameraTiltMax=60.)
   self.assertFalse(validate(p)[0],(shape,validate(p)[0]))
   self.assertEqual(p.TopFrontShape,shape)
   for mount in camera_mounts(p):
    for x in mount['plate_x']:
     for y,z in mount['attachment_profile'][2:]:self.assertGreaterEqual(top_interior_distance((x,y),p),p.MinimumWeb-1e-6)
   self.assertEqual(Parameters.from_dict(p.to_dict()),p)
 def test_invalid_dimensions_and_lost_hardware_stock_rejected(self):
  p=Parameters(TopFrontShape='Camera U recess')
  for kwargs in ({'TopFrontDepth':0.},{'TopFrontDepth':1000.},{'TopFrontRecessWidth':-1.},{'TopFrontRecessWidth':80.},{'TopFrontSetback':-1.},{'TopFrontSetback':float('nan')},{'TopFrontDepth':80.,'TopFrontSetback':5.}):
   self.assertTrue(validate(replace(p,**kwargs))[0],kwargs)
 def test_preview_has_the_same_recess_and_remains_cad_free(self):
  from freecad.rotorforge.airflow_gui import profile_path,QtCore
  p=Parameters(TopFrontShape='Camera U recess',TopFrontDepth=16.,TopFrontSetback=3.,TopFrontRecessWidth=22.)
  q=profile_path(p,'TopPlate',50,-90,90,5)
  self.assertFalse(q.contains(QtCore.QPointF(0,85)))
  self.assertTrue(q.contains(QtCore.QPointF(18,85)))
  self.assertFalse(q.contains(QtCore.QPointF(18,89)))
