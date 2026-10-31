import unittest,tempfile
from pathlib import Path
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters,validate,save_parameters,load_parameters
from freecad.rotorforge.fpv import camera_mounts,camera_wall_centres,camera_body_centre,camera_slots
class CameraTopOffsetTests(unittest.TestCase):
 def test_only_top_attachment_moves(self):
  for follow in (False,True):
   p=Parameters(FPVEnabled=True,CameraFollowPlates=follow);q=replace(p,CameraTopRearOffset=5)
   old,new=camera_mounts(p)[0],camera_mounts(q)[0]
   self.assertEqual(old['bottom_centre_y'],new['bottom_centre_y']);self.assertEqual(old['tabs_y'],new['tabs_y'])
   self.assertEqual(new['top_centre_y'],old['top_centre_y']-5)
   self.assertEqual(new['top_tabs_y'],tuple(y-5 for y in old['top_tabs_y']))
   self.assertEqual(old['side_arcs'],new['side_arcs']);self.assertEqual(old['side_holes'],new['side_holes'])
   self.assertEqual(camera_body_centre(p),camera_body_centre(q));self.assertEqual(camera_slots(p),camera_slots(q))
   self.assertNotEqual(camera_slots(p,'TopPlate'),camera_slots(q,'TopPlate'))
 def test_existing_lower_extensions_remain_independent(self):
  p=Parameters(FPVEnabled=True,CameraBaseMode='Custom',CameraBaseFrontExtension=2,CameraBaseRearExtension=4)
  self.assertEqual(camera_mounts(p)[0]['wall_profile'][:2],camera_mounts(replace(p,CameraTopRearOffset=3))[0]['wall_profile'][:2])
 def test_reject_negative_or_unsupported_offset(self):
  for value in (-1,1000):self.assertTrue(validate(Parameters(FPVEnabled=True,CameraTopRearOffset=value))[0])
  self.assertFalse(validate(Parameters(FPVEnabled=True,CameraTopRearOffset=5))[0])
 def test_old_settings_default_to_zero_and_roundtrip(self):
  data=Parameters().to_dict();data.pop('CameraTopRearOffset');self.assertEqual(Parameters.from_dict(data).CameraTopRearOffset,0)
  p=Parameters(CameraTopRearOffset=4.5)
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'frame.json';save_parameters(f,p);self.assertEqual(load_parameters(f),p)
