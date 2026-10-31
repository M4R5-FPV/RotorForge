"""Portable layout and opt-in finishing contracts for the shared rear yoke."""
import unittest
from dataclasses import replace
from compact_fixture import Parameters
from freecad.rotorforge.parameters import validate

from freecad.rotorforge.fpv import camera_mounts
from freecad.rotorforge.plate_fillets import fillet_openings
class OpenRearTests(unittest.TestCase):
 def test_opening_rounding_is_independent_and_opt_in(self):
  p=Parameters.from_dict({})
  for role in ('BottomPlate','MidPlate','TopPlate','ArmClampPlate','ArmLowerClampPlate'):self.assertFalse(fillet_openings(p,role))
  q=replace(p,TopFilletOpenings=True);self.assertTrue(fillet_openings(q,'TopPlate'));self.assertFalse(fillet_openings(q,'BottomPlate'));self.assertEqual(Parameters.from_dict(q.to_dict()),q)
 def test_camera_travel_keeps_contacts_and_paths(self):
  for mode in ('Hard mount','Compression pads','Captured inserts'):
   p=Parameters(FPVEnabled=True,FlexCameraMode=mode);a=camera_mounts(p)[0]
   for offset in (5,10,20):
    q=replace(p,CameraForeAftOffset=offset);b=camera_mounts(q)[0];self.assertEqual(validate(q)[0],[])
    for key in ('attachment_profile','tabs_y','top_tabs_y'):self.assertEqual(a[key],b[key])
    for x,y in zip(a['side_arcs'],b['side_arcs']):
     self.assertAlmostEqual(y['centre'][0]-x['centre'][0],offset)
     for key in ('radius','start','end'):self.assertEqual(x[key],y[key])
   self.assertTrue(validate(replace(p,CameraAutoExtend=False,CameraForeAftOffset=20))[0])
