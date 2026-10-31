"""Underside capture and centred, independently attached camera plates."""
from pathlib import Path
from dataclasses import replace
import math,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import *
from freecad.rotorforge.fpv import *
from freecad.rotorforge.cutouts import encode_patterns,parse_patterns

class CaptureCameraTests(unittest.TestCase):
    def test_lower_capture_and_fc_deck(self):
        p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True)
        self.assertTrue(underside_clamp_active(p));lower=underside_clamp_layout(p)
        self.assertEqual(lower['z']+lower['thickness'],-p.ArmThickness)
        self.assertEqual(stack_reference_z(p),p.BottomThickness)
        self.assertEqual(arm_clamp_grip(p),p.BottomThickness+p.ArmThickness+p.UndersideClampThickness)
        self.assertEqual([2*r for _,r,n in plate_holes(p,'ArmLowerClampPlate') if n=='stack'],[6]*4)
        self.assertTrue(underside_clamp_active(replace(p,KeystoneEnabled=False)))
        for changes in ({'PlateDesign':'3 plates'},{'ArmBracesEnabled':False},{'TwoPlateArmPosition':'Above bottom plate'}):
            self.assertFalse(underside_clamp_active(replace(p,**changes)))

    def test_optional_arm_reliefs(self):
        p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,ArmRootY=24)
        self.assertEqual(validate(p)[0],[])
        self.assertTrue(any('stack access passage' in e for e in validate(replace(p,ArmRootReliefsEnabled=False))[0]))
        self.assertEqual(validate(Parameters(ArmRootReliefsEnabled=False))[0],[])

    def test_custom_standoff_access(self):
        p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,StandoffCount='8 (4 pairs)')
        holes=plate_holes(p,'ArmLowerClampPlate')
        expected=sum(arm_clamp_interior_distance(s['point'],p)>=0 and not s['shared_arm'] for s in standoff_layouts(p))
        self.assertEqual(sum(n=='standoff access' for _,_,n in holes),expected)
        self.assertTrue(all(2*r==6 for _,r,n in holes if n=='standoff access'))
        self.assertEqual(validate(p)[0],[])

    def test_larger_bore_web(self):
        p=Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,StandoffCount='6 (3 pairs)',StandoffPair3Y=14,StandoffPair3Width=16)
        self.assertTrue(any('Lower capture' in e for e in validate(p)[0]))
        self.assertTrue(any('Lower capture' in e for e in validate(replace(p,KeystoneEnabled=False))[0]))
        self.assertEqual(validate(replace(p,ArmBracesEnabled=False))[0],[])

    def test_shorter_top_creates_independent_tabs_and_centres_camera(self):
        for mode in PLATE_DESIGNS:
            p=Parameters(PlateDesign=mode,FPVEnabled=True,StandoffHeight=35,CameraSideBoltSpacing=8,TopReachMode='Custom',TopFrontReach=60,TopRearReach=100)
            self.assertEqual(validate(p)[0],[])
            bottom,top=camera_wall_centres(p)
            self.assertLess(top,bottom);self.assertEqual(top_bounds(p),(-100,60))
            self.assertNotEqual(camera_slots(p),camera_slots(p,'TopPlate'))
            self.assertAlmostEqual(camera_position_y(p),(bottom+top)/2)

    def test_dual_slots_have_no_translation(self):
        p=Parameters(FPVEnabled=True,StandoffHeight=35,CameraSideBoltSpacing=8)
        for angle in (0,20,45):
            self.assertEqual(camera_body_centre(p,angle),camera_body_centre(p))
            self.assertEqual(camera_mounts(p),camera_mounts(replace(p,CameraTilt=angle)))
        m=camera_mounts(p)[0];self.assertEqual(m['side_holes'],());self.assertEqual(len(m['side_arcs']),2)
        self.assertEqual([a['radius'] for a in m['side_arcs']],[4,4])

    def test_upper_pivot_is_upper_screw(self):
        p=Parameters(FPVEnabled=True,StandoffHeight=35,CameraSideBoltSpacing=8,CameraTiltMechanism='Upper pivot + lower arc')
        m=camera_mounts(p)[0];pivot=m['side_holes'][0]
        self.assertEqual(m['side_arcs'][0]['centre'],pivot)
        for angle in (0,20,45):
            y,z=camera_body_centre(p,angle);a=math.radians(angle)
            self.assertAlmostEqual(math.dist((y-4*math.sin(a),z+4*math.cos(a)),pivot),0)
            self.assertLess(z-4*math.cos(a),pivot[1])

    def test_custom_position_and_height(self):
        p=Parameters(FPVEnabled=True,StandoffHeight=35,CameraSideBoltSpacing=8,CameraPositionMode='Custom position',CameraMountY=71,CameraPivotMode='Custom height',CameraPivotHeight=21)
        self.assertEqual(camera_body_centre(p),(71,23));self.assertEqual(validate(p)[0],[])
        self.assertTrue(validate(replace(p,CameraAutoExtend=False,CameraMountY=100))[0])
        self.assertTrue(validate(replace(p,CameraPivotHeight=4))[0])

    def test_old_coordinates_and_airflow_migrate_once(self):
        d=Parameters(FPVEnabled=True,StandoffHeight=35,CameraSideBoltSpacing=8,CameraPivotMode='Custom height',CameraPivotHeight=18).to_dict()
        for name in ('CameraPositionMode','CameraTiltMechanism','CameraFollowPlates','CameraPlateY','ArmRootReliefsEnabled','UndersideClampThickness'):d.pop(name)
        d['CutoutPatterns']=encode_patterns([dict(role='CameraMountLeft',shape='Circle',width=2,x=-5,y=5)])
        p=Parameters.from_dict(d);y,z=camera_body_centre(p)
        self.assertAlmostEqual(y,70+4*math.cos(math.radians(20)))
        self.assertAlmostEqual(z,20+4*math.sin(math.radians(20)))
        self.assertAlmostEqual(camera_position_y(p)+parse_patterns(p.CutoutPatterns)[0]['x'],65)
        self.assertEqual(Parameters.from_dict(p.to_dict()),p)

    def test_shorter_bottom_and_unused_custom_y(self):
        p=Parameters(FPVEnabled=True,StandoffHeight=35,CameraSideBoltSpacing=8,BottomReachMode='Custom',BottomFrontReach=60,BottomRearReach=45,CameraMountY=0)
        self.assertEqual(validate(p)[0],[]);self.assertLess(*camera_wall_centres(p))

    def test_dual_arc_end_web(self):
        p=Parameters(FPVEnabled=True,StandoffHeight=35,CameraSideBoltSpacing=3.8,CameraTiltMax=60)
        self.assertTrue(any('between their ends' in e for e in validate(p)[0]))
        self.assertEqual(validate(replace(p,CameraSideBoltSpacing=8))[0],[])

if __name__=='__main__':unittest.main()
