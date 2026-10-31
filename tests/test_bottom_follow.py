"""Three-plate bottom rear tabs follow arms; the main body stays supported."""
from dataclasses import replace
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import (Parameters,arm_layouts,bottom_bounds,bottom_body_bounds,bottom_tabs,
    bottom_interior_distance,bottom_tab_interior_distance,stack_holes,validate)
from freecad.rotorforge.plate_profiles import profiled_interior_distance
from test_mid_follow import matched_mid

class BottomFollowTests(unittest.TestCase):
    def test_rear_rectangle_overhang_is_removed(self):
        for layout in ('True X','Stretched X','Deadcat'):
            for width in (14,24,36):
                p=matched_mid(Layout=layout,ArmRootWidth=width)
                rear,front=bottom_bounds(p);pt=(0,rear+1)
                self.assertGreater(profiled_interior_distance(pt,p,'BottomPlate',p.BodyWidth,rear,front,p.CornerRadius),0)
                self.assertLess(bottom_interior_distance(pt,p),0)
                self.assertGreater(bottom_body_bounds(p)[0],rear)

    def test_bolts_and_stack_service_openings_keep_edge_material(self):
        for layout in ('True X','Stretched X','Deadcat'):
            for width in (14,24,36):
                p=matched_mid(Layout=layout,ArmRootWidth=width)
                self.assertEqual(validate(p)[0],[])
                for arm in arm_layouts(p):
                    for pt in arm['bolts']:self.assertGreaterEqual(bottom_interior_distance(pt,p),p.RootHoleDiameter/2+p.MinimumWeb-1e-6)
                for pt in stack_holes(p):self.assertGreaterEqual(bottom_interior_distance(pt,p),p.StackAccessDiameter/2+p.MinimumWeb-1e-6)

    def test_front_and_stack_body_remain_independent_of_rear_tabs(self):
        p=matched_mid()
        for pt in ((0,50),(0,0),(15,15)):
            self.assertEqual(bottom_interior_distance(pt,p),bottom_interior_distance(pt,replace(p,ArmRootWidth=36)))
        self.assertEqual(len(bottom_tabs(p)),2)
        rear=next(a for a in arm_layouts(p) if a['root'][1]<0)
        self.assertLess(bottom_tab_interior_distance((1,-1),p,rear),0)

    def test_custom_reach_caps_tabs_and_rejects_cut_bolt_support(self):
        p=matched_mid(BottomReachMode='Custom',BottomRearReach=42,BottomFrontReach=100)
        self.assertEqual(validate(p)[0],[])
        self.assertEqual(bottom_bounds(p),(-42,100))
        self.assertLess(bottom_interior_distance((20,-43),p),0)
        self.assertTrue(validate(replace(p,BottomRearReach=31))[0])

    def test_two_plate_profile_is_unchanged(self):
        for position in ('Above bottom plate','Below bottom plate'):
            p=Parameters(PlateDesign='2 plates',TwoPlateArmPosition=position)
            self.assertEqual(bottom_body_bounds(p),bottom_bounds(p));self.assertFalse(bottom_tabs(p))
            for pt in ((0,-45),(20,-45),(0,50),(24,0),(0,0)):
                self.assertEqual(bottom_interior_distance(pt,p),profiled_interior_distance(pt,p,'BottomPlate',p.BodyWidth,*bottom_bounds(p),p.CornerRadius))

if __name__=='__main__':unittest.main()
