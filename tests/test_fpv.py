"""Mechanical FPV options, independent of FreeCAD/Qt."""
from dataclasses import replace
from pathlib import Path
import math
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from freecad.rotorforge.parameters import Parameters, PLATE_DESIGNS, STANDOFF_COUNTS, bottom_bounds, mid_bounds, validate, save_parameters, load_parameters
from tests.frame_cases import FRAME_CASES, FPV_CASES
from freecad.rotorforge.fpv import (camera_holes,camera_slots,camera_mounts,camera_pivot_height,
                               camera_cage_height,vtx_holes,VTX_PATTERNS)


class FPVTests(unittest.TestCase):
    def test_fpv_all_presets_modes_counts(self):
        for preset in list(FRAME_CASES.values())+list(FPV_CASES.values()):
            for mode in PLATE_DESIGNS:
                for count in STANDOFF_COUNTS:
                    p=replace(preset,FPVEnabled=True,PlateDesign=mode,StandoffCount=count,StandoffHeight=30)
                    with self.subTest(mode=mode,count=count,layout=p.Layout):
                        self.assertEqual(validate(p)[0],[])
                        self.assertEqual(len(camera_slots(p)),4)
                        self.assertEqual(len(camera_holes(p)),0)
                        self.assertEqual(len(vtx_holes(p)),8)
                        if mode=='3 plates':
                            self.assertLess(mid_bounds(p)[0],bottom_bounds(p)[0])
                            self.assertLessEqual(mid_bounds(p)[0],p.VTXOffsetY-p.VTXLength/2-p.MinimumWeb)
                        else: self.assertLessEqual(bottom_bounds(p)[0],p.VTXOffsetY-p.VTXLength/2-p.MinimumWeb)

    def test_optional_fpv_legacy_defaults(self):
        data=Parameters().to_dict()
        from freecad.rotorforge.fpv import FPV_FIELDS
        data={k:v for k,v in data.items() if k not in FPV_FIELDS}
        p=Parameters.from_dict(data)
        self.assertFalse(p.FPVEnabled)
        self.assertEqual(camera_holes(p),())
        self.assertEqual(vtx_holes(p),())
        self.assertEqual(bottom_bounds(p),(-43.5,82.5))
        self.assertEqual(validate(replace(p,CameraWidth=0,VTXWidth=0))[0],[])

    def test_exact_camera_and_vtx_holes(self):
        p=replace(Parameters(),FPVEnabled=True)
        self.assertEqual({((a[0]+b[0])/2,(a[1]+b[1])/2,r) for a,b,r in camera_slots(p)},
                         {(x,y,1.6) for x in (-11.25,11.25) for y in (64,76)})
        for pattern,count,spacing in ((VTX_PATTERNS[0],4,20),(VTX_PATTERNS[1],4,25.5),(VTX_PATTERNS[2],8,None)):
            holes=vtx_holes(replace(p,VTXPattern=pattern))
            self.assertEqual(len(holes),count)
            if spacing:
                self.assertEqual({point for point,r,s in holes},{(x,-70+y) for x in (-spacing/2,spacing/2) for y in (-spacing/2,spacing/2)})

    def test_common_widths_and_two_screw_mounts(self):
        for width in (14,19,20,22,28):
            for angle in (0,20,45):
                height=math.ceil(((width*math.cos(math.radians(angle))+18*math.sin(math.radians(angle)))/2+4)*2)/2
                p=replace(Parameters(),FPVEnabled=True,CameraWidth=width,CameraHeight=width,
                          CameraPivotHeight=max(18,height),CameraTilt=angle,StandoffHeight=35)
                self.assertEqual(validate(p)[0],[])
                mounts=camera_mounts(p)
                self.assertAlmostEqual(mounts[1]['plate_x'][0]-mounts[0]['plate_x'][1],width+.5)
                self.assertEqual(mounts[0]['z0'],p.BottomThickness)
                self.assertEqual(mounts[0]['z1'],p.BottomThickness+camera_cage_height(p))
        p=replace(p,CameraMountMode="Fixed",CameraSideBoltSpacing=8,StandoffHeight=40)
        mount=camera_mounts(p)[0]
        self.assertEqual(len(mount['side_holes']),2)
        self.assertAlmostEqual(math.dist(*mount['side_holes']),8)

    def test_fpv_collisions_and_insufficient_web(self):
        p=replace(Parameters(),FPVEnabled=True)
        for changes in (dict(VTXOffsetY=-40),dict(CameraPivotMode='Custom height',CameraPivotHeight=8),dict(CameraWidth=60),
                        dict(VTXWidth=55),dict(CameraMountY=25,CameraPositionMode="Custom position",CameraAutoExtend=False),dict(CameraTilt=70),
                        dict(CameraSideBoltSpacing=2),dict(VTX20HoleDiameter=3.2),dict(CameraPlateLength=14),
                        dict(CameraSideBoltSpacing=20)):
            with self.subTest(changes=changes): self.assertTrue(validate(replace(p,**changes))[0])
        self.assertEqual(validate(replace(p,VTXPattern=VTX_PATTERNS[0],VTX20HoleDiameter=3.2))[0],[])

    def test_fpv_native_settings_json(self):
        p=replace(FPV_CASES['5-inch FPV Digital'],CameraTilt=30,CameraSideBoltSpacing=8,StandoffHeight=35)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'fpv.json'
            save_parameters(path,p)
            self.assertEqual(load_parameters(path),p)
        for changes in ({'FPVEnabled':'yes'},{'VideoSystem':'Other'},{'VTXPattern':'30 x 30 mm'}):
            with self.assertRaises(ValueError): Parameters.from_dict(changes)


if __name__=='__main__': unittest.main()
