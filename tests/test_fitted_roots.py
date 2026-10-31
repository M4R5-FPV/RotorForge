"""Close arm-root arrangements, bolt support and settings compatibility."""
from dataclasses import replace
from pathlib import Path
import math
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters, arm_layouts, validate, save_parameters, load_parameters
from freecad.rotorforge.arm_roots import compact_key_centre


def close_roots(**changes):
    return replace(Parameters(ArmRootFit='Fitted miters',ArmRootY=8,RootInset=17,
                              RootExtension=20,RootBoltSpacing=8,StandoffHeight=35),**changes)


class FittedRootTests(unittest.TestCase):
    def test_overlapping_tails_are_allowed_only_with_fitted_joints(self):
        for layout in ('True X','Stretched X','Deadcat'):
            p=close_roots(Layout=layout,Wheelbase=270)
            self.assertEqual(validate(p)[0],[])
            self.assertTrue(any('Replaceable arms intersect' in error for error in validate(replace(p,ArmRootFit='Independent'))[0]))

    def test_fitting_preserves_motor_and_mount_coordinates(self):
        for layout in ('True X','Stretched X','Deadcat'):
            p=close_roots(Layout=layout)
            self.assertEqual(arm_layouts(p),arm_layouts(replace(p,ArmRootFit='Independent')))

    def test_all_supported_plate_sandwiches_accept_close_roots(self):
        for plate,position,clamp in [('3 plates','Below bottom plate',False),
                                     ('2 plates','Below bottom plate',True),
                                     ('2 plates','Above bottom plate',True)]:
            for key in (False,True):
                p=close_roots(PlateDesign=plate,TwoPlateArmPosition=position,ArmBracesEnabled=clamp,
                              KeystoneEnabled=key,ArmJointClearance=.2)
                self.assertEqual(validate(p)[0],[])

    def test_joint_and_key_cuts_protect_the_root_bolts(self):
        p=close_roots(KeystoneEnabled=True)
        for changes in ({'KeystoneWidth':15,'KeystoneLength':15}, {'RootInset':21},
                        {'ArmRootY':3}, {'ArmJointClearance':-1}, {'ArmJointClearance':1.01},
                        {'KeystoneWidth':0}, {'KeystoneLength':-1}, {'KeystoneWidth':2,'KeystoneLength':2}):
            with self.subTest(changes=changes):self.assertTrue(validate(replace(p,**changes))[0])

    def test_old_settings_keep_independent_rounded_roots(self):
        data=Parameters().to_dict()
        for name in ('ArmRootFit','ArmJointClearance','KeystoneWidth','KeystoneLength'):data.pop(name)
        self.assertEqual(Parameters.from_dict(data),Parameters())

    def test_fitted_settings_roundtrip_with_personal_json(self):
        p=close_roots(KeystoneEnabled=True,ArmJointClearance=.15,KeystoneWidth=9,KeystoneLength=10)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'frame.json';save_parameters(path,p)
            self.assertEqual(load_parameters(path),p)

    def test_inactive_fitting_dimensions_are_retained(self):
        p=replace(Parameters(),ArmJointClearance=-1,KeystoneWidth=0,KeystoneLength=-1)
        self.assertEqual(validate(p)[0],[])
        self.assertTrue(validate(replace(p,ArmRootFit='Fitted miters'))[0])
        p=close_roots(KeystoneWidth=0,KeystoneLength=-1)
        self.assertEqual(validate(p)[0],[])
        self.assertTrue(validate(replace(p,KeystoneEnabled=True))[0])

    def test_key_centre_tracks_unequal_front_and_rear_root_widths(self):
        p=close_roots(BottomCentreWidth=58,CentreSectionY=8,CentreSectionLength=8,CentreShoulderLength=4)
        arms=arm_layouts(p);centre=compact_key_centre(arms)
        self.assertNotEqual(centre[1],0)
        distances=[math.dist(centre,a['root']) for a in arms]
        self.assertLess(max(distances)-min(distances),1e-9)


if __name__=='__main__':unittest.main()
