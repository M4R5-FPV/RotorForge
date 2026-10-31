"""Independent lower camera contact length and captured attachment locations."""
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import (Parameters,PLATE_DESIGNS,bottom_bounds,top_bounds,
                                   validate,save_parameters,load_parameters)
from freecad.rotorforge.fpv import (CAMERA_TILT_MECHANISMS,camera_mounts,camera_slots,
                            camera_attachment_lengths,camera_position_y,camera_pivot_height,
                            camera_cage_height)


class CameraBaseTests(unittest.TestCase):
    def base(self,**changes):
        return replace(Parameters(FPVEnabled=True,StandoffHeight=35,TopReachMode='Custom',
                                  TopFrontReach=60,TopRearReach=100),**changes)

    def test_automatic_ignores_retained_extensions(self):
        p=self.base()
        retained=replace(p,CameraBaseFrontExtension=6,CameraBaseRearExtension=10)
        self.assertEqual(camera_mounts(p),camera_mounts(retained))
        self.assertEqual(bottom_bounds(p),bottom_bounds(retained))
        self.assertEqual(camera_attachment_lengths(p),(20,20))
        self.assertEqual(validate(retained)[0],[])

    def test_independent_front_and_rear_extensions(self):
        for front,rear in ((6,0),(0,10),(6,10)):
            with self.subTest(front=front,rear=rear):
                original=camera_mounts(self.base())[0]
                p=self.base(CameraBaseMode='Custom',CameraBaseFrontExtension=front,CameraBaseRearExtension=rear)
                mount=camera_mounts(p)[0]
                self.assertEqual(camera_attachment_lengths(p),(20+front+rear,20))
                self.assertEqual(mount['wall_profile'][2:],original['wall_profile'][2:])
                self.assertEqual(mount['top_tabs_y'],original['top_tabs_y'])
                self.assertAlmostEqual(mount['wall_profile'][0][0],original['wall_profile'][0][0]-rear)
                self.assertAlmostEqual(mount['wall_profile'][1][0],original['wall_profile'][1][0]+front)
                self.assertAlmostEqual(mount['tabs_y'][0],original['tabs_y'][0]-rear)
                self.assertAlmostEqual(mount['tabs_y'][1],original['tabs_y'][1]+front)
                self.assertEqual(validate(p)[0],[])

    def test_both_plate_designs_and_camera_mounts(self):
        for design in PLATE_DESIGNS:
            for mechanism in CAMERA_TILT_MECHANISMS+('Fixed','Single pivot'):
                p=self.base(PlateDesign=design,CameraBaseMode='Custom',CameraBaseFrontExtension=6,CameraBaseRearExtension=10)
                if mechanism=='Fixed':p=replace(p,CameraMountMode='Fixed')
                elif mechanism=='Single pivot':p=replace(p,CameraSideBoltSpacing=0)
                else:p=replace(p,CameraTiltMechanism=mechanism)
                with self.subTest(design=design,mechanism=mechanism):
                    self.assertEqual(validate(p)[0],[])
                    mount=camera_mounts(p)[0]
                    height_fraction=camera_pivot_height(p)/camera_cage_height(p)
                    self.assertAlmostEqual(camera_position_y(p),mount['bottom_centre_y']+
                                           (mount['top_centre_y']-mount['bottom_centre_y'])*height_fraction)

    def test_automatic_bottom_reach_grows_without_extending_top(self):
        p=self.base(TopReachMode='Automatic',CameraBaseMode='Custom',CameraBaseFrontExtension=12)
        original=replace(p,CameraBaseMode='Automatic')
        self.assertGreater(bottom_bounds(p)[1],bottom_bounds(original)[1])
        self.assertEqual(top_bounds(p),top_bounds(original))
        self.assertEqual(camera_mounts(p)[0]['top_tabs_y'],camera_mounts(original)[0]['top_tabs_y'])
        self.assertEqual(validate(p)[0],[])

    def test_custom_plate_reaches_are_exact(self):
        p=self.base(CameraBaseMode='Custom',CameraBaseFrontExtension=6,CameraBaseRearExtension=10,
                    BottomReachMode='Custom',BottomFrontReach=90,BottomRearReach=45)
        self.assertEqual(bottom_bounds(p),(-45,90));self.assertEqual(top_bounds(p),(-100,60))
        self.assertEqual(validate(p)[0],[])
        # A disabled follow option must reject an unsupported extended base.
        bad=replace(p,CameraFollowPlates=False,BottomFrontReach=75)
        self.assertEqual(bottom_bounds(bad),(-45,75))
        self.assertTrue(any('lower camera attachment' in error for error in validate(bad)[0]))

    def test_unfitted_attachment_retains_directional_extensions(self):
        p=self.base(CameraFollowPlates=False,TopReachMode='Automatic')
        custom=replace(p,CameraBaseMode='Custom',CameraBaseFrontExtension=6,CameraBaseRearExtension=10)
        original=camera_mounts(p)[0];mount=camera_mounts(custom)[0]
        self.assertAlmostEqual(mount['wall_profile'][0][0],original['wall_profile'][0][0]-10)
        self.assertAlmostEqual(mount['wall_profile'][1][0],original['wall_profile'][1][0]+6)
        self.assertEqual(mount['wall_profile'][2:],original['wall_profile'][2:])
        self.assertEqual(validate(custom)[0],[])

    def test_receiving_slots_follow_each_attachment(self):
        p=self.base(CameraBaseMode='Custom',CameraBaseFrontExtension=6,CameraBaseRearExtension=10)
        for role,key in (('BottomPlate','tabs_y'),('TopPlate','top_tabs_y')):
            expected={(sum(m['plate_x'])/2,y) for m in camera_mounts(p) for y in m[key]}
            actual={((a[0]+b[0])/2,(a[1]+b[1])/2) for a,b,r in camera_slots(p,role)}
            self.assertEqual(actual,expected)

    def test_old_settings_and_custom_json_roundtrip(self):
        p=self.base();old=p.to_dict()
        for field in ('CameraBaseMode','CameraBaseFrontExtension','CameraBaseRearExtension'):old.pop(field)
        restored=Parameters.from_dict(old)
        self.assertEqual(restored,p)
        custom=replace(p,CameraBaseMode='Custom',CameraBaseFrontExtension=6,CameraBaseRearExtension=10)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'custom_camera_base.json';save_parameters(path,custom)
            self.assertEqual(load_parameters(path),custom)

    def test_invalid_or_blocked_extensions_are_rejected(self):
        p=self.base(CameraBaseMode='Custom')
        for changes in ({'CameraBaseFrontExtension':-1},{'CameraBaseRearExtension':-1},
                        {'CameraBaseRearExtension':100}):
            self.assertTrue(validate(replace(p,**changes))[0])
        with self.assertRaises(ValueError):Parameters.from_dict(dict(p.to_dict(),CameraBaseFrontExtension=float('nan')))


if __name__=='__main__':unittest.main()
