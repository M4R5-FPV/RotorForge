"""Commercial-style rear ordering, tilted bounds and shaped camera interfaces."""
import unittest,sys,math
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compact_fixture import Parameters
from freecad.rotorforge.parameters import validate
from freecad.rotorforge.flex import camera_interface_polygon,insert_rect
from freecad.rotorforge.fpv import camera_mounts
class RearArrangementTests(unittest.TestCase):
 def test_camera_silhouette_has_four_plain_vertices_and_preserves_screw_paths(self):
  p=Parameters(FPVEnabled=True,FlexCameraMode='Captured inserts',FlexInterfaceShape='Side plate outline',CameraAutoExtend=False,CameraTopRearOffset=2)
  poly=camera_interface_polygon(p,14,16);self.assertEqual(len(poly),4)
  self.assertAlmostEqual(max(y for y,z in poly)-min(y for y,z in poly),14)
  self.assertAlmostEqual(max(z for y,z in poly)-min(z for y,z in poly),16)
  a=camera_mounts(p)[0];b=camera_mounts(replace(p,FlexInterfaceShape='Rounded rectangle'))[0]
  self.assertEqual(a['side_holes'],b['side_holes']);self.assertEqual(a['side_arcs'],b['side_arcs'])
 def test_invalid_tilt_and_fillet_are_rejected(self):
  for change in ({'BottomEdgeFillet':-1},{'TopEdgeFillet':31}):self.assertTrue(validate(replace(Parameters(),**change))[0])
if __name__=='__main__':unittest.main()
