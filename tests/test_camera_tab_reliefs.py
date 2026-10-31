from dataclasses import replace
import unittest, math
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.fpv import camera_mounts,camera_tab_reliefs,camera_slots

class CameraTabReliefTests(unittest.TestCase):
 def test_cutter_radius_and_tab_tangency(self):
  for diameter in (1.,2.,3.):
   p=Parameters(FPVEnabled=True,CameraTabCutterDiameter=diameter);m=camera_mounts(p)[0]
   cuts=camera_tab_reliefs(p,m);self.assertEqual(len(cuts),8)
   for (ys,z),batch in zip(((m['tabs_y'],m['z0']),(m['top_tabs_y'],m['z1'])),(cuts[:4],cuts[4:])):
    for y in ys:
     centres=[c for c in batch if abs(c[0]-y)<p.CameraTabLength/2+diameter]
     self.assertEqual(len(centres),2)
     for cy,cz,r in centres:
      self.assertAlmostEqual(cz,z);self.assertAlmostEqual(r,diameter/2)
      self.assertAlmostEqual(abs(cy-y)-r,p.CameraTabLength/2)
 def test_disabled_and_socket_dimensions(self):
  p=Parameters(FPVEnabled=True);q=replace(p,CameraTabReliefs=False)
  self.assertEqual(camera_tab_reliefs(q,camera_mounts(q)[0]),())
  self.assertEqual(camera_mounts(p),camera_mounts(q))
  for role in ('BottomPlate','TopPlate'):self.assertEqual(camera_slots(p,role),camera_slots(q,role))
 def test_diameter_validation(self):
  for v in (-1.,0.,float('nan'),float('inf'),6.1):
   self.assertTrue(validate(Parameters(FPVEnabled=True,CameraTabCutterDiameter=v))[0])
 def test_preview_body_cut_not_tab_cut(self):
  from freecad.rotorforge.airflow_gui import finished_part_path,QtCore
  p=Parameters(FPVEnabled=True);q=replace(p,CameraTabReliefs=False)
  from freecad.rotorforge.fpv import camera_position_y
  m=camera_mounts(p)[0];origin=camera_position_y(p);old=finished_part_path(q,'CameraMountLeft');new=finished_part_path(p,'CameraMountLeft')
  y,z,r=camera_tab_reliefs(p,m)[0];pt=QtCore.QPointF(y-origin,z-p.BottomThickness+r*.5)
  self.assertTrue(old.contains(pt));self.assertFalse(new.contains(pt))
  y=m['tabs_y'][0]
  for delta in (-.49,0,.49):
   pt=QtCore.QPointF(y-origin+delta*p.CameraTabLength,-p.BottomThickness/2)
   self.assertTrue(new.contains(pt))
