import unittest
from dataclasses import fields,replace
from freecad.rotorforge.parameters import Parameters,top_bounds,top_interior_distance
from freecad.rotorforge.editor_sections import FIELD_LOCATION
from freecad.rotorforge.bottom_nose import camera_recess_width
class SingleRecessTests(unittest.TestCase):
 def test_legacy_controls_are_not_parameters_or_editor_fields(self):
  names={f.name for f in fields(Parameters)}
  for key in ('CameraCutoutWidth','CameraCutoutDepth','CameraCutoutClearance'):
   self.assertNotIn(key,names);self.assertNotIn(key,FIELD_LOCATION)
 def test_straight_front_has_no_hidden_fpv_notch(self):
  p=Parameters(FPVEnabled=True,TopFrontShape='Straight')
  self.assertGreater(top_interior_distance((0,top_bounds(p)[1]-3),p),0)
 def test_explicit_profile_is_not_overridden_by_legacy_settings(self):
  p=Parameters.from_dict(dict(FPVEnabled=True,TopFrontShape='Camera swept recess',TopFrontDepth=12.,CameraCutoutWidth=30.,CameraCutoutDepth=40.,CameraCutoutClearance=1.))
  self.assertEqual(p.TopFrontShape,'Camera swept recess');self.assertEqual(p.TopFrontDepth,12.)
  self.assertEqual(p.TopFrontClearance,1.);self.assertEqual(camera_recess_width(p),p.CameraWidth+2.)
  self.assertNotIn('CameraCutoutDepth',p.to_dict())
 def test_legacy_opening_moves_to_visible_top_profile_once(self):
  p=Parameters.from_dict(dict(FPVEnabled=True,CameraCutoutWidth=14.,CameraCutoutDepth=28.,CameraCutoutClearance=.75))
  self.assertEqual((p.TopFrontShape,p.TopFrontDepth,p.TopFrontRecessWidth,p.TopFrontSetback),('Camera U recess',28.,14.,0.))
  self.assertEqual(Parameters.from_dict(p.to_dict()),p)
 def test_legacy_automatic_opening_is_migrated_and_non_fpv_stays_straight(self):
  p=Parameters.from_dict(dict(FPVEnabled=True,CameraCutoutWidth=0.,CameraCutoutDepth=0.,CameraCutoutClearance=.5))
  self.assertEqual(p.TopFrontShape,'Camera U recess');self.assertGreater(p.TopFrontDepth,0.)
  self.assertEqual(Parameters.from_dict(dict(CameraCutoutWidth=14.)).TopFrontShape,'Straight')
