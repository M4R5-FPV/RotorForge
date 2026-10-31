"""Independent stack-referenced rear body reach and settings migration."""
from pathlib import Path
from dataclasses import replace
import sys,tempfile,unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
from freecad.rotorforge.parameters import (Parameters,bottom_bounds,bottom_body_bounds,legacy_bottom_body_reach,
    validate,save_parameters,load_parameters)
from test_mid_follow import matched_mid

class BottomStackReachTests(unittest.TestCase):
    def test_edge_uses_stack_centre_and_reach(self):
        for offset in (-8,0,8):
            for reach in (26,32,38):
                p=matched_mid(StackOffsetY=offset,BottomBodyRearReach=reach)
                self.assertEqual(bottom_body_bounds(p)[0],offset-reach)

    def test_arm_dimensions_do_not_choose_the_body_edge(self):
        p=matched_mid(BottomBodyRearReach=32,StackOffsetY=3)
        for width in (14,24,36):
            q=replace(p,ArmRootWidth=width,RootBolt1Y=-2,RootBolt2Y=2)
            self.assertEqual(bottom_body_bounds(q)[0],-29)
            self.assertEqual(validate(q)[0],[])

    def test_automatic_outer_limit_grows_for_explicit_body(self):
        p=matched_mid(BottomBodyRearReach=70)
        self.assertEqual(bottom_body_bounds(p)[0],-70)
        self.assertLessEqual(bottom_bounds(p)[0],-70)
        self.assertEqual(validate(p)[0],[])

    def test_custom_limit_and_short_body_report_problems(self):
        p=matched_mid(BottomBodyRearReach=50,BottomReachMode='Custom',BottomRearReach=45)
        self.assertTrue(any('custom bottom rear limit' in e for e in validate(p)[0]))
        self.assertTrue(any('reach' in e.lower() or 'edge' in e.lower() for e in validate(replace(p,BottomBodyRearReach=5))[0]))

    def test_old_settings_capture_the_previous_automatic_edge(self):
        for layout in ('True X','Stretched X','Deadcat'):
            p=matched_mid(Layout=layout,StackOffsetY=3)
            data=p.to_dict();data.pop('BottomBodyRearReach')
            restored=Parameters.from_dict(data)
            self.assertAlmostEqual(restored.BottomBodyRearReach,legacy_bottom_body_reach(p))
            self.assertAlmostEqual(bottom_body_bounds(restored)[0],p.StackOffsetY-legacy_bottom_body_reach(p))
            self.assertEqual({k:v for k,v in restored.to_dict().items() if k!='BottomBodyRearReach'},data)

    def test_roundtrip_and_inactive_two_plate_dimension(self):
        p=matched_mid(BottomBodyRearReach=37,StackOffsetY=5)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'frame.json';save_parameters(path,p);self.assertEqual(load_parameters(path),p)
        q=replace(Parameters(),PlateDesign='2 plates',BottomBodyRearReach=0)
        self.assertEqual(bottom_body_bounds(q),bottom_bounds(q));self.assertEqual(validate(q)[0],[])

if __name__=='__main__':unittest.main()
