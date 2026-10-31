"""Layout contracts, opt-in compatibility and camera tilt invariants."""
import unittest,sys
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compact_fixture import Parameters
from freecad.rotorforge.parameters import validate
from freecad.rotorforge.flex import flex_roles,camera_inner
from freecad.rotorforge.fpv import camera_mounts,camera_screw_offsets,camera_angles
class FlexiblePartTests(unittest.TestCase):
 def test_soft_modes_preserve_tilt_paths(self):
  for mechanism in ('Dual arc slots','Upper pivot + lower arc'):
   p=Parameters(FPVEnabled=True,StandoffHeight=40,CameraMountMode='Variable',CameraTiltMechanism=mechanism)
   a=camera_mounts(p)[0]
   for mode in ('Compression pads','Captured inserts'):
    soft=replace(p,FlexCameraMode=mode);b=camera_mounts(soft)[0]
    self.assertEqual(validate(soft)[0],[])
    self.assertEqual(a['side_holes'],b['side_holes']);self.assertEqual(a['side_arcs'],b['side_arcs'])
    self.assertEqual(camera_angles(p),camera_angles(soft));self.assertEqual(camera_screw_offsets(p,p.CameraTilt),camera_screw_offsets(soft,soft.CameraTilt))
    self.assertGreater(camera_inner(soft),camera_inner(p))
if __name__=='__main__':unittest.main()
