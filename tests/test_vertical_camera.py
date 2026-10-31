"""Physical camera screw alignment, pivot kinematics and swept clearance."""
from dataclasses import replace
from pathlib import Path
import math,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.fpv import (camera_mounts,camera_body_centre,camera_angles,
                           camera_vertical_limits,CAMERA_TILT_MECHANISMS)


class VerticalCameraTests(unittest.TestCase):
    def camera(self,**changes):
        return replace(Parameters(FPVEnabled=True,CameraWidth=22,CameraHeight=22,
                                  CameraSideBoltSpacing=6.5,StandoffHeight=40),**changes)

    def test_level_fixed_pair_has_equal_y_and_6p5_vertical_pitch(self):
        p=self.camera(CameraMountMode='Fixed',CameraTilt=0)
        for mount in camera_mounts(p):
            lower,upper=mount['side_holes']
            self.assertAlmostEqual(lower[0],upper[0])
            self.assertAlmostEqual(upper[1]-lower[1],6.5)

    def test_fixed_pair_follows_camera_upright_axis(self):
        for tilt in (0,20,45,60):
            p=self.camera(CameraMountMode='Fixed',CameraTilt=tilt)
            cy,cz=camera_body_centre(p);a=math.radians(tilt)
            lower,upper=camera_mounts(p)[0]['side_holes']
            for point,offset in ((lower,-3.25),(upper,3.25)):
                dy,dz=point[0]-cy,point[1]-cz
                self.assertAlmostEqual(dy*math.cos(a)+dz*math.sin(a),0)
                self.assertAlmostEqual(-dy*math.sin(a)+dz*math.cos(a),offset)
            self.assertAlmostEqual(math.dist(lower,upper),6.5)

    def test_dual_slots_pass_through_both_screw_paths(self):
        p=self.camera(CameraTiltMax=60)
        cy,cz=camera_body_centre(p)
        upper,lower=camera_mounts(p)[0]['side_arcs']
        self.assertEqual((upper['start'],lower['start']),(90,270))
        for tilt in (0,17,45,60):
            a=math.radians(tilt)
            for offset,arc in ((3.25,upper),(-3.25,lower)):
                point=(cy-offset*math.sin(a),cz+offset*math.cos(a))
                self.assertAlmostEqual(math.dist(point,arc['centre']),arc['radius'])
                angle=math.degrees(math.atan2(point[1]-cz,point[0]-cy))%360
                self.assertGreaterEqual(angle+1e-9,arc['start'])
                self.assertLessEqual(angle-1e-9,arc['end'])
            self.assertEqual(camera_body_centre(p,tilt),(cy,cz))

    def test_upper_pivot_stays_fixed_while_lower_screw_moves(self):
        p=self.camera(CameraTiltMechanism='Upper pivot + lower arc',CameraTiltMax=60)
        mount=camera_mounts(p)[0];pivot=mount['side_holes'][0]
        for tilt in (0,17,45,60):
            cy,cz=camera_body_centre(p,tilt);a=math.radians(tilt)
            upper=(cy-3.25*math.sin(a),cz+3.25*math.cos(a))
            lower=(cy+3.25*math.sin(a),cz-3.25*math.cos(a))
            self.assertAlmostEqual(math.dist(upper,pivot),0)
            self.assertAlmostEqual(math.dist(lower,pivot),6.5)
            self.assertLess(lower[1],upper[1])

    def test_clearance_extrema_cover_dense_rotation_sweep(self):
        for mechanism in CAMERA_TILT_MECHANISMS:
            p=self.camera(CameraTiltMechanism=mechanism,CameraTiltMax=60)
            low,high=camera_vertical_limits(p)
            dense=[camera_vertical_limits(p,i/100) for i in range(6001)]
            self.assertLessEqual(low,min(v[0] for v in dense)+1e-9)
            self.assertGreaterEqual(high,max(v[1] for v in dense)-1e-9)
            self.assertLessEqual(max(b-a for a,b in zip(camera_angles(p),camera_angles(p)[1:])),2+1e-9)

    def test_pattern_uses_body_height_instead_of_body_depth(self):
        p=self.camera(CameraHeight=22,CameraBodyDepth=6,CameraSideBoltSpacing=8)
        self.assertEqual(validate(p)[0],[])
        errors=validate(replace(p,CameraHeight=9,CameraBodyDepth=20))[0]
        self.assertTrue(any('vertical side screw pattern' in e for e in errors))

    def test_single_pivot_and_custom_width_remain_independent(self):
        p=self.camera(CameraSideBoltSpacing=0,CameraWidth=17.2)
        left,right=camera_mounts(p)
        self.assertEqual(len(left['side_holes']),1);self.assertFalse(left['side_arcs'])
        self.assertAlmostEqual(right['plate_x'][0]-left['plate_x'][1],17.2+p.CameraSideClearance)
        self.assertEqual(validate(p)[0],[])

    def test_saved_pivot_choice_converts_once(self):
        data=self.camera().to_dict();data['CameraTiltMechanism']='Front pivot + rear arc'
        p=Parameters.from_dict(data)
        self.assertEqual(p.CameraTiltMechanism,'Upper pivot + lower arc')
        self.assertEqual(p.CameraSideBoltSpacing,6.5)
        self.assertEqual(Parameters.from_dict(p.to_dict()),p)


if __name__=='__main__':unittest.main()
