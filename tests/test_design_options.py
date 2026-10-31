"""New design choices and their portable parameter contracts."""
from dataclasses import replace
import json
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import (Parameters,validate,bottom_bounds,mid_bounds,top_bounds,
    plate_levels,stack_reference_z,plate_holes)
from freecad.rotorforge.fpv import camera_mounts,camera_body_centre,camera_vertical_limits
from freecad.rotorforge.cutouts import encode_patterns,parse_patterns,cutouts_for
from freecad.rotorforge.motor_pads import MOTOR_PAD_SHAPES


class DesignOptionsTests(unittest.TestCase):
    def test_stack_has_no_hidden_lift(self):
        for mode,clamp,expected in (('2 plates',False,2),('2 plates',True,9),('3 plates',False,10)):
            p=Parameters(PlateDesign=mode,ArmBracesEnabled=clamp,TwoPlateArmPosition='Above bottom plate')
            self.assertEqual(stack_reference_z(p),expected)
            self.assertEqual(stack_reference_z(replace(p,StackMountHeight=4)),expected+4)

    def test_custom_reaches_are_exact_and_independent(self):
        p=Parameters(FPVEnabled=True,BottomReachMode='Custom',BottomFrontReach=85,BottomRearReach=45,
                     MidReachMode='Custom',MidRearReach=100,TopReachMode='Custom',TopFrontReach=84,TopRearReach=101)
        self.assertEqual(validate(p)[0],[])
        self.assertEqual(bottom_bounds(p),(-45,85));self.assertEqual(mid_bounds(p),(-100,24));self.assertEqual(top_bounds(p),(-101,84))
        self.assertTrue(validate(replace(p,MidRearReach=60))[0])
        self.assertTrue(validate(replace(p,TopRearReach=60))[0])
        self.assertFalse(any(name=='VTX' for _,_,name in plate_holes(p,'BottomPlate')))
        self.assertEqual(sum(name=='VTX' for _,_,name in plate_holes(p,'MidPlate')),8)

    def test_variable_geometry_does_not_follow_preview_angle(self):
        p=Parameters(FPVEnabled=True,CameraSideBoltSpacing=8,StandoffHeight=35)
        self.assertEqual(camera_mounts(p),camera_mounts(replace(p,CameraTilt=40)))
        m=camera_mounts(p)[0];self.assertEqual(len(m['side_holes']),0);self.assertEqual(len(m['side_arcs']),2)
        self.assertEqual(m['side_arcs'][0]['radius'],4)
        p=replace(p,CameraMountMode='Fixed');m=camera_mounts(p)[0]
        self.assertEqual(len(m['side_holes']),2);self.assertEqual(m['side_arcs'],[])
        self.assertAlmostEqual(math.dist(*m['side_holes']),8)
        self.assertTrue(validate(replace(p,CameraSideBoltSpacing=0))[0])
        self.assertTrue(validate(replace(p,CameraMountMode='Variable',CameraTiltMax=10))[0])

    def test_airflow_grid_rotates_about_its_centre(self):
        p=Parameters(CutoutPatterns=encode_patterns([dict(role='CameraMountLeft',shape='Circle',width=2,
                      x=3,y=5,columns=3,pitch_x=4,rotation=90)]))
        self.assertEqual([(round(q['x']),round(q['y'])) for q in cutouts_for(p,'CameraMountLeft')],[(3,1),(3,5),(3,9)])
        self.assertEqual(cutouts_for(p,'TopPlate'),())
        for bad in ('{}','[{"columns":1.5}]','[{"width":true}]','[{"shape":"unknown"}]','[{"rows":20,"columns":20}]','[{"x":NaN}]'):
            with self.assertRaises(ValueError):parse_patterns(bad)
        self.assertEqual(parse_patterns(encode_patterns(parse_patterns(p.CutoutPatterns))),parse_patterns(p.CutoutPatterns))

    def test_motor_pad_options_preserve_motor_pattern(self):
        from freecad.rotorforge.parameters import arm_layouts
        base=arm_layouts(Parameters(MotorBoltCircle=22.627416997969522,MotorHoleRotation=45))
        for shape in MOTOR_PAD_SHAPES:
            p=Parameters(MotorBoltCircle=22.627416997969522,MotorHoleRotation=45,MotorPadShape=shape)
            self.assertEqual(validate(p)[0],[]);self.assertEqual(arm_layouts(p),base)
        self.assertTrue(validate(Parameters(MotorPadShape='Four-lobe',MotorPadDiameter=20))[0])

    def test_legacy_two_screw_camera_keeps_body_position(self):
        old={'FPVEnabled':True,'CameraSideBoltSpacing':8,'CameraMountY':70,'CameraTilt':20,
             'CameraPivotMode':'Custom height','CameraPivotHeight':18}
        p=Parameters.from_dict(old)
        self.assertEqual(p.CameraMountMode,'Fixed')
        y,z=camera_body_centre(p)
        self.assertAlmostEqual(y,70);self.assertAlmostEqual(z,20)


if __name__=='__main__':unittest.main()
