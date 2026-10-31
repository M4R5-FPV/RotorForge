import math,unittest
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.camera_interface import profile_corners,insert_layers,lip_sides
from freecad.rotorforge.fpv import camera_mounts
from freecad.rotorforge.flex import insert_rect,camera_interface_polygon
class InsertProfileTests(unittest.TestCase):
 def setUp(self):self.p=Parameters(FPVEnabled=True,FlexCameraMode='Captured inserts',StandoffHeight=35.)
 def test_old_settings_keep_both_lips(self):
  data=self.p.to_dict();data.pop('FlexInsertLipSide');data.pop('FlexInsertCornerRadius')
  p=Parameters.from_dict(data);self.assertEqual(lip_sides(p),(True,True));self.assertEqual(p.FlexInsertCornerRadius,1.)
 def test_lip_face_choices(self):
  for choice,expected in [('Both sides',(True,True)),('Outside only',(False,True)),('Inside only',(True,False))]:
   self.assertEqual(lip_sides(replace(self.p,FlexInsertLipSide=choice)),expected)
 def test_layers_mirror_across_camera(self):
  p=self.p;left,right=camera_mounts(p)
  for a,b in zip(insert_layers(p,left,-1),insert_layers(p,right,1)):
   self.assertAlmostEqual(a['x']+a['thickness'],-b['x']);self.assertEqual(a['offset'],b['offset'])
 def test_outside_only_has_no_inner_flange(self):
  p=replace(self.p,FlexInsertLipSide='Outside only');layers=insert_layers(p,camera_mounts(p)[0],-1)
  self.assertEqual(layers[0]['offset'],-p.FlexInsertFit);self.assertEqual(len(layers),3)
 def test_inside_only_keeps_contact_and_neck(self):
  p=replace(self.p,FlexInsertLipSide='Inside only');layers=insert_layers(p,camera_mounts(p)[0],-1)
  self.assertEqual([l['kind'] for l in layers],['contact','neck']);self.assertEqual(layers[0]['offset'],p.FlexInsertLip)
 def test_rectangle_has_circular_corner_plan(self):
  p=self.p;cy,cz,_,_=insert_rect(p);corners=profile_corners(p,14.,16.)
  self.assertEqual(len(corners),4)
  self.assertEqual(corners[0]['start'],(cy-7,cz-7));self.assertEqual(corners[0]['end'],(cy-6,cz-8))
  self.assertTrue(all(abs(c['radius']-1.)<1e-8 for c in corners))
 def test_sloped_outline_rounds_all_actual_corners(self):
  p=replace(self.p,FlexInterfaceShape='Side plate outline',CameraAutoExtend=False,CameraTopRearOffset=2.)
  raw=camera_interface_polygon(p,14.,16.);corners=profile_corners(p,14.,16.)
  self.assertEqual(len(raw),len(corners))
  for vertex,c in zip(raw,corners):
   self.assertGreater(c['radius'],0.);self.assertGreater(math.dist(vertex,c['start']),0.);self.assertGreater(math.dist(vertex,c['end']),0.)
 def test_position_and_tilt_paths_do_not_move(self):
  for choice in ('Inside only','Outside only'):
   self.assertEqual(camera_mounts(self.p),camera_mounts(replace(self.p,FlexInsertLipSide=choice,FlexInsertCornerRadius=.5)))
 def test_corner_radius_validation(self):
  for radius in (0.,-.1,9.):
   self.assertTrue(validate(replace(self.p,FlexInsertCornerRadius=radius))[0])
 def test_preview_rounds_opening_corner(self):
  from freecad.rotorforge.flex_preview import camera_interface_path,QtCore
  p=self.p;_,cz,_,_=insert_rect(p);path=camera_interface_path(p,14.,16.)
  self.assertFalse(path.contains(QtCore.QPointF(-6.9,cz-p.BottomThickness-7.9)))
  self.assertTrue(path.contains(QtCore.QPointF(0,cz-p.BottomThickness)))
