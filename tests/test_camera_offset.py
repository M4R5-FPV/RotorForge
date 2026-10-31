"""An additive camera translation preserves cage attachments and tilt geometry."""
import sys,unittest
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.fpv import camera_mounts,camera_body_centre,camera_position_y,camera_angles
class CameraOffsetTests(unittest.TestCase):
 def test_translation_in_both_position_modes_and_tilt_mechanisms(self):
  for position in ('Automatic centre','Custom position'):
   for mechanism in ('Dual arc slots','Upper pivot + lower arc'):
    p=Parameters(FPVEnabled=True,CameraPlateLength=32,CameraPositionMode=position,CameraMountMode='Variable',CameraTiltMechanism=mechanism)
    for offset in (-2.,2.):
     q=replace(p,CameraForeAftOffset=offset);a=camera_mounts(p)[0];b=camera_mounts(q)[0]
     self.assertEqual(validate(q)[0],[]);self.assertEqual(a['wall_profile'],b['wall_profile']);self.assertEqual(a['tabs_y'],b['tabs_y']);self.assertEqual(a['top_tabs_y'],b['top_tabs_y'])
     self.assertAlmostEqual(camera_position_y(q)-camera_position_y(p),offset)
     for angle in camera_angles(p):
      x,z=camera_body_centre(p,angle);xx,zz=camera_body_centre(q,angle);self.assertAlmostEqual(xx-x,offset);self.assertEqual(zz,z)
     for aa,bb in zip(a['side_arcs'],b['side_arcs']):
      self.assertAlmostEqual(bb['centre'][0]-aa['centre'][0],offset);self.assertEqual(aa['start'],bb['start']);self.assertEqual(aa['end'],bb['end']);self.assertEqual(aa['radius'],bb['radius'])
 def test_default_roundtrip_and_travel_checks(self):
  self.assertEqual(Parameters().CameraForeAftOffset,0)
  p=Parameters(CameraForeAftOffset=-2);self.assertEqual(Parameters.from_dict(p.to_dict()),p)
  self.assertTrue(validate(Parameters(FPVEnabled=True,CameraAutoExtend=False,CameraForeAftOffset=100))[0])
  self.assertTrue(validate(Parameters(CameraForeAftOffset=-101))[0])
if __name__=='__main__':unittest.main()
