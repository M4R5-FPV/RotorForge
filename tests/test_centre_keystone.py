"""Centre profiles, real arm-root coupling and two-plate key retention."""
from dataclasses import replace
from pathlib import Path
import json,math,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import (Parameters,arm_layouts,motor_centres,arm_root_x,validate,keystone_active,
    keystone_retainers,load_parameters,save_parameters,SCHEMA,bottom_bounds)
from freecad.rotorforge.plate_profiles import centre_width_at,centre_polygon,profiled_interior_distance


class CentreKeystoneTests(unittest.TestCase):
    def test_per_part_width_and_tapers(self):
        p=Parameters(BottomCentreWidth=70,TopCentreWidth=60,CentreSectionLength=60,CentreShoulderLength=10)
        self.assertEqual(centre_width_at(p,'BottomPlate',0,50),70)
        self.assertEqual(centre_width_at(p,'BottomPlate',35,50),60)
        self.assertEqual(centre_width_at(p,'BottomPlate',50,50),50)
        self.assertEqual(centre_width_at(p,'TopPlate',0,46),60)
        self.assertEqual(centre_width_at(p,'MidPlate',0,50),50)
        self.assertEqual(centre_polygon(Parameters(),'BottomPlate',50,-40,70),())

    def test_exact_reach_clips_the_widening(self):
        p=Parameters(BottomCentreWidth=80,BottomReachMode='Custom',BottomRearReach=45,BottomFrontReach=83)
        points=centre_polygon(p,'BottomPlate',50,*bottom_bounds(p))
        self.assertGreaterEqual(min(y for x,y in points),-45)
        self.assertLessEqual(max(y for x,y in points),83)
        self.assertGreater(profiled_interior_distance((35,0),p,'BottomPlate',50,-45,83,5),0)
        self.assertLess(profiled_interior_distance((35,75),p,'BottomPlate',50,-45,83,5),0)

    def test_arm_roots_can_follow_or_keep_their_spacing(self):
        p=Parameters(BottomCentreWidth=70)
        self.assertEqual(arm_root_x(p,True),25)
        self.assertEqual(arm_root_x(replace(p,ArmRootsFollowCentre=False),True),15)

    def test_deadcat_compensates_unequal_root_spans(self):
        p=Parameters(Layout='Deadcat',Wheelbase=270,BottomCentreWidth=70,MidCentreWidth=70,TopCentreWidth=70,
                     CentreSectionY=15,CentreSectionLength=50)
        self.assertNotEqual(arm_root_x(p,True),arm_root_x(p,False))
        arms=arm_layouts(p)
        self.assertAlmostEqual(arms[0]['length'],arms[2]['length'])
        a,b,c,d=motor_centres(p)
        self.assertAlmostEqual(math.dist(a,c),270);self.assertAlmostEqual(math.dist(b,d),270)

    def test_key_on_both_clamp_arm_positions(self):
        p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True)
        self.assertTrue(keystone_active(p));self.assertEqual(keystone_retainers(p),())
        from freecad.rotorforge.parameters import underside_clamp_active;self.assertTrue(underside_clamp_active(p))
        self.assertEqual(validate(p)[0],[])
        q=replace(p,TwoPlateArmPosition='Above bottom plate')
        self.assertTrue(keystone_active(q));self.assertEqual(keystone_retainers(q),())
        self.assertFalse(keystone_active(replace(p,ArmBracesEnabled=False)))
        self.assertEqual(keystone_retainers(replace(p,PlateDesign='3 plates')),())

    def test_invalid_width_or_retainer_geometry(self):
        p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True)
        for changes in (dict(BottomCentreWidth=40),dict(BottomCentreWidth=-1),dict(BottomCentreWidth=70,CentreShoulderLength=0),
                        dict(UndersideClampThickness=0),dict(UndersideClampThickness=-1)):
            self.assertTrue(validate(replace(p,**changes))[0],changes)

    def test_alternate_rotorforge_schema_writes_canonical_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'compatible.json'
            path.write_text(json.dumps(dict(schema='rotorforge-frame/1',units='mm',parameters={})))
            p=load_parameters(path);self.assertEqual(p.BottomCentreWidth,0)
            save_parameters(path,p);self.assertEqual(json.loads(path.read_text())['schema'],SCHEMA)


if __name__=='__main__':unittest.main()
