"""Mid clamping tabs stay within the configured front arm profiles."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import (Parameters,arm_layouts,mid_interior_distance,mid_tab_interior_distance,
                                   point_segment_distance,validate)

def matched_mid(**changes):
    return replace(Parameters(Wheelbase=300,BodyWidth=80,TopWidth=80,BodyLength=160,TopLength=160,
        MidRearReach=80,MidFrontReach=25,StandoffLength=140,StandoffHeight=35,RootInset=20,ArmRootY=30,RootExtension=40,
        ArmRootFit='Fitted miters',ArmRootWidth=24,ArmRootLength=15,ArmRootTaperLength=20,
        RootBoltLayout='Custom coordinates',RootBolt1X=-4,RootBolt1Y=0,RootBolt2X=4,RootBolt2Y=0,
        KeystoneEnabled=True,KeystoneWidth=20,KeystoneLength=20,StrapSlotsEnabled=False),**changes)

class MidFollowTests(unittest.TestCase):
    def test_old_rounded_pad_overhang_is_outside_the_mid(self):
        for width,point in ((14,(13,35.5)),(24,(10,38)),(36,(6,43))):
            for layout in ('True X','Stretched X','Deadcat'):
                with self.subTest(width=width,layout=layout):
                    p=matched_mid(ArmRootWidth=width,Layout=layout);arm=arm_layouts(p)[0]
                    self.assertGreater(width/2-point_segment_distance(point,*arm['bolts']),0)
                    self.assertLess(mid_tab_interior_distance(point,p,arm),0)
                    self.assertLess(mid_interior_distance(point,p),0)

    def test_bolts_keep_their_required_edge_material(self):
        for layout in ('True X','Stretched X','Deadcat'):
            for width in (14,24,36):
                p=matched_mid(Layout=layout,ArmRootWidth=width)
                self.assertEqual(validate(p)[0],[])
                for arm in arm_layouts(p)[:2]:
                    for bolt in arm['bolts']:
                        self.assertGreaterEqual(mid_interior_distance(bolt,p),p.RootHoleDiameter/2+p.MinimumWeb-1e-6)

    def test_mid_tab_clearance_includes_joint_and_key_pocket(self):
        p=matched_mid(KeystoneWidth=20,KeystoneLength=20);arm=arm_layouts(p)[0]
        self.assertLess(mid_tab_interior_distance((-1,30),p,arm),0)
        self.assertLess(mid_tab_interior_distance((1,1),p,arm),0)

    def test_rear_stack_deck_keeps_its_own_support(self):
        p=matched_mid()
        self.assertGreater(mid_interior_distance((0,-50),p),10)
        self.assertEqual(mid_interior_distance((0,-50),p),mid_interior_distance((0,-50),replace(p,ArmRootWidth=36)))

if __name__=='__main__':unittest.main()
