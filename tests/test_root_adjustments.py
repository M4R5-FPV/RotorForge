"""Root widening and mirrored custom mounting patterns without CAD imports."""
from dataclasses import replace
from pathlib import Path
import math
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters, arm_layouts, motor_centres, validate, save_parameters, load_parameters, standoff_layouts
from freecad.rotorforge.arm_roots import ROOT_PROFILE_FIELDS, arm_local_point, stem_interior_distance


def wide(**changes):
    return replace(Parameters(ArmRootFit='Fitted miters',ArmRootY=8,RootInset=17,RootExtension=20,
        RootBoltSpacing=8,StandoffHeight=35,Wheelbase=270,ArmRootWidth=24,ArmRootLength=15,
        ArmRootTaperLength=20,RootBoltLayout='Custom coordinates',RootBolt1X=-4,
        RootBolt1Y=0,RootBolt2X=4,RootBolt2Y=0),**changes)


class RootAdjustmentTests(unittest.TestCase):
    def test_width_and_bolts_do_not_move_motors_or_root_references(self):
        for layout in ('True X','Stretched X','Deadcat'):
            p=wide(Layout=layout);plain=replace(p,ArmRootWidth=0,RootBoltLayout='Along arm')
            self.assertEqual(motor_centres(p),motor_centres(plain))
            self.assertEqual([a['root'] for a in arm_layouts(p)],[a['root'] for a in arm_layouts(plain)])

    def test_custom_coordinates_mirror_on_every_arm(self):
        for layout in ('True X','Stretched X','Deadcat'):
            p=wide(Layout=layout)
            for arm in arm_layouts(p):
                rx,ry=arm['root'];sx=1 if rx>0 else -1;sy=1 if ry>0 else -1
                for bolt,(x,y) in zip(arm['bolts'],((-4,0),(4,0))):
                    self.assertAlmostEqual((bolt[0]-rx)*sx,x)
                    self.assertAlmostEqual((bolt[1]-ry)*sy,y)
            arms=arm_layouts(p)
            for right,left in ((arms[0],arms[1]),(arms[3],arms[2])):
                for a,b in zip(right['bolts'],left['bolts']):
                    self.assertAlmostEqual(a[0],-b[0]);self.assertAlmostEqual(a[1],b[1])
        # Each frame offset changes only its own axis, at any arm sweep.
        for root_y in (8,100):
            for layout in ('True X','Stretched X','Deadcat'):
                p=wide(ArmRootY=root_y,Layout=layout)
                before=arm_layouts(p);move_x=arm_layouts(replace(p,RootBolt1X=-3));move_y=arm_layouts(replace(p,RootBolt1Y=1))
                for a,x,y in zip(before,move_x,move_y):
                    self.assertEqual(a['bolts'][0][1],x['bolts'][0][1])
                    self.assertEqual(a['bolts'][0][0],y['bolts'][0][0])
                    self.assertAlmostEqual(abs(a['bolts'][0][0]-x['bolts'][0][0]),1)
                    self.assertAlmostEqual(abs(a['bolts'][0][1]-y['bolts'][0][1]),1)
                    self.assertEqual(a['bolts'][1],x['bolts'][1]);self.assertEqual(a['bolts'][1],y['bolts'][1])

    def test_offsets_stay_fixed_when_the_arm_angle_changes(self):
        for layout in ('True X','Stretched X','Deadcat'):
            p=wide(Layout=layout,RootBolt1X=-3,RootBolt1Y=1.25)
            before=arm_layouts(p);after=arm_layouts(replace(p,FrontSpread=1.4,LengthToWidth=1.5,Wheelbase=310))
            for a,b in zip(before,after):
                for axis in (0,1):
                    self.assertAlmostEqual(a['bolts'][0][axis]-a['root'][axis],b['bolts'][0][axis]-b['root'][axis])

    def test_older_arm_coordinates_convert_to_frame_offsets(self):
        for layout in ('True X','Stretched X','Deadcat'):
            p=wide(Layout=layout);data={k:v for k,v in p.to_dict().items() if not k.startswith(('RootBolt1','RootBolt2'))}
            data.update(RootBolt1Along=-4,RootBolt1Across=2.5,RootBolt2Along=4,RootBolt2Across=-2.5)
            converted=Parameters.from_dict(data);arm=arm_layouts(converted)[0];ux,uy=arm['unit'];rx,ry=arm['root']
            for actual,(t,s) in zip(arm['bolts'],((-4,2.5),(4,-2.5))):
                self.assertAlmostEqual(actual[0],rx+t*ux-s*uy)
                self.assertAlmostEqual(actual[1],ry+t*uy+s*ux)
            self.assertEqual(Parameters.from_dict(converted.to_dict()),converted)

    def test_wide_stem_has_constant_root_taper_and_unchanged_beam(self):
        p=wide();arm=arm_layouts(p)[0]
        for t,s,distance in ((0,10,2),(10,12,0),(25,9.5,0),(45,6,1),(-20,12,0),(-32,0,0)):
            self.assertAlmostEqual(stem_interior_distance(p,arm,arm_local_point(arm,t,s)),distance,places=7)
        self.assertLess(stem_interior_distance(p,arm,arm_local_point(arm,0,12.1)),0)
        self.assertLess(stem_interior_distance(p,arm,arm_local_point(arm,45,7.1)),0)

    def test_active_geometry_rejects_bad_width_taper_and_bolt_support(self):
        for changes in ({'ArmRootWidth':13},{'ArmRootWidth':-1},{'ArmRootTaperLength':0},
                        {'ArmRootLength':-1},{'ArmRootTaperLength':120},
                        {'RootBolt1X':30},{'RootBolt2X':-4,'RootBolt2Y':0}):
            with self.subTest(changes=changes):self.assertTrue(validate(wide(**changes))[0])

    def test_custom_signed_settings_roundtrip_and_old_files_default(self):
        p=wide(RootBoltSpacing=0,RootBolt1Y=-.5,RootBolt2Y=.5)
        self.assertEqual(validate(p)[0],[])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'frame.json';save_parameters(path,p)
            self.assertEqual(load_parameters(path),p)
        old={k:v for k,v in Parameters().to_dict().items() if k not in ROOT_PROFILE_FIELDS}
        self.assertEqual(Parameters.from_dict(old),Parameters())
        for name in ROOT_PROFILE_FIELDS-{'RootBoltLayout'}:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):Parameters.from_dict(dict(p.to_dict(),**{name:math.nan}))

    def test_default_bolt_pair_and_unused_custom_values_are_preserved(self):
        p=Parameters(RootBolt1Y=-200,RootBolt1X=200,ArmRootLength=-1,ArmRootTaperLength=0)
        self.assertEqual(validate(p)[0],[])
        for a in arm_layouts(p):
            for bolt,t in zip(a['bolts'],(-p.RootBoltSpacing/2,p.RootBoltSpacing/2)):
                self.assertEqual(bolt,arm_local_point(a,t,0))

    def test_shared_standoffs_follow_custom_bolt_identity(self):
        p=wide(BodyWidth=70,TopWidth=70,ArmRootY=25,RootInset=15,RootExtension=50,
               StandoffCount='8 (4 pairs)',StandoffFrontMount='Arm outer hole',StandoffRearMount='Arm outer hole',
               StandoffPair3Mount='Front arm inner hole',StandoffPair4Mount='Rear arm inner hole')
        bolts=[pt for a in arm_layouts(p) for pt in a['bolts']]
        for stand in standoff_layouts(p):
            self.assertTrue(stand['shared_arm']);self.assertIn(stand['point'],bolts)


if __name__=='__main__':unittest.main()
