import unittest,math
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.bottom_nose import NOSE_SHAPES,REAR_SHAPES,REAR_FRONT_MAP,edge_commands,edge_polygon
from freecad.rotorforge.fpv import camera_mounts,camera_slots,camera_tab_reliefs
class EdgeProfileTests(unittest.TestCase):
 def test_front_and_rear_share_mirrored_profiles(self):
  for rear,front in REAR_FRONT_MAP.items():
   p=Parameters(PlateDesign='2 plates',BottomNoseShape=front,BottomRearShape=rear)
   a=edge_commands(p,'BottomPlate','Front',50,-80,80)
   b=edge_commands(p,'BottomPlate','Rear',50,-80,80)
   self.assertEqual(tuple((i[0],*((x,-y) for x,y in i[1:])) for i in a),b,rear)
 def test_every_profile_is_finite_symmetric_and_trim_only(self):
  from shapely.geometry import Polygon
  for end,names in (('Front',NOSE_SHAPES),('Rear',REAR_SHAPES)):
   for name in names[1:]:
    for tip in (10.,35.,90.):
     p=Parameters(PlateDesign='2 plates',**{('BottomNose' if end=='Front' else 'BottomRear')+'Shape':name,('BottomNose' if end=='Front' else 'BottomRear')+'TipWidth':tip})
     pts=edge_polygon(p,'BottomPlate',end,50,-80,80)
     # Repeated collinear mask points are harmless to both CAD and polygon union.
     polygon=Polygon(pts)
     self.assertTrue(polygon.is_valid,(end,name,tip))
     self.assertGreater(polygon.area,0)
     for x,y in pts:
      self.assertTrue(math.isfinite(x+y))
      self.assertLessEqual(y,81);self.assertGreaterEqual(y,-81)
      self.assertLess(min(abs(xx+x)+abs(yy-y) for xx,yy in pts),1e-6,name)
 def test_inactive_rear_profiles_do_not_trim_other_plate_mode(self):
  p=Parameters(BottomRearShape='Split tail')
  self.assertFalse(edge_commands(p,'BottomPlate','Rear',50,-80,80))
  p=Parameters(PlateDesign='2 plates',MidRearShape='Split tail')
  self.assertFalse(edge_commands(p,'MidPlate','Rear',50,-80,80))
 def test_rear_depth_and_mount_checks(self):
  p=Parameters(TopRearShape='Cable channel',TopRearDepth=2.)
  self.assertFalse(validate(p)[0],validate(p)[0])
  self.assertTrue(validate(replace(p,TopRearDepth=1000))[0])
  self.assertTrue(validate(replace(p,TopRearShape='Pointed end',TopRearDepth=50))[0])
 def test_tab_offsets_move_sockets_and_reliefs_without_moving_camera(self):
  p=Parameters(FPVEnabled=True)
  q=replace(p,CameraTabBottomRearOffset=.5,CameraTabBottomFrontOffset=-.75,CameraTabTopRearOffset=.25,CameraTabTopFrontOffset=-.5)
  self.assertFalse(validate(q)[0],validate(q)[0])
  for a,b in zip(camera_mounts(p),camera_mounts(q)):
   for name in ('wall_profile','side_holes','side_arcs','attachment_profile'):self.assertEqual(a[name],b[name])
   for name,shifts in (('tabs_y',(.5,-.75)),('top_tabs_y',(.25,-.5))):
    for v,w,d in zip(a[name],b[name],shifts):self.assertAlmostEqual(w-v,d)
   ra=camera_tab_reliefs(p,a);rb=camera_tab_reliefs(q,b)
   self.assertNotEqual(ra,rb)
  for role in ('BottomPlate','TopPlate'):self.assertNotEqual(camera_slots(p,role),camera_slots(q,role))
  self.assertEqual(Parameters.from_dict(q.to_dict()),q)
 def test_tab_overlap_outside_contact_and_nan_rejected(self):
  for kwargs in ({'CameraTabBottomRearOffset':100.},{'CameraTabTopFrontOffset':-100.},{'CameraTabBottomFrontOffset':float('nan')}):
   self.assertTrue(validate(Parameters(FPVEnabled=True,**kwargs))[0])
