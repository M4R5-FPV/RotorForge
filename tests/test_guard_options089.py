"""Guard fit modes and real VTX clearance, including old saved profiles."""
from dataclasses import replace
import math
import unittest
from freecad.rotorforge.parameters import Parameters,validate,plate_levels
from freecad.rotorforge.protection_layout import (guard_layout,guard_wire_openings,
    guard_vtx_window,closure_profile,guard_plate_gap)
from freecad.rotorforge.flex import validate_flex


def vtx_frame(**changes):
    p=Parameters(Wheelbase=300.,FPVEnabled=True,StandoffHeight=35.,FlexSideGuards=True,
        FlexGuardVTXOpening=True,StandoffWidth=42.,TopWidth=54.,BodyWidth=58.,VTXWidth=70.,VTXOffsetY=-50.,VTXLength=28.,
        VTXPattern='20 x 20 mm',StandoffLength=150.,
        MidReachMode='Custom',MidRearReach=90.,MidFrontReach=35.,
        TopReachMode='Custom',TopRearReach=90.,TopFrontReach=90.,
        BottomReachMode='Custom',BottomRearReach=90.,BottomFrontReach=90.)
    return replace(p,**changes)


class GuardOptions089Tests(unittest.TestCase):
    def test_old_settings_keep_original_design(self):
        p=Parameters.from_dict({'FlexSideGuards':True,'FlexGuardWireEnabled':True})
        self.assertEqual(p.FlexGuardFitMode,'Plate-edge wrap')
        self.assertFalse(p.FlexGuardVTXOpening)
        self.assertEqual(len(guard_wire_openings(p,guard_layout(p)[0])),2)

    def test_inner_faces_and_bearing_bounds(self):
        for design in ('2 plates','3 plates'):
            for position in ('Above bottom plate','Below bottom plate'):
                for clearance in (0.,.05,1.):
                    p=Parameters(PlateDesign=design,TwoPlateArmPosition=position,
                        FlexSideGuards=True,FlexGuardFitMode='Between plates',FlexGuardClearance=clearance)
                    levels=plate_levels(p)
                    for g in guard_layout(p):
                        self.assertEqual(g['z'],levels['deck_z']+guard_plate_gap(p))
                        self.assertEqual(g['top'],levels['top_z']-guard_plate_gap(p))
                        for low,high in g['bands']:
                            self.assertGreaterEqual(low,g['z']);self.assertLessEqual(high,g['top'])

    def test_one_wire_span_uses_both_endpoints_and_restores_pair_choice(self):
        p=Parameters(FlexSideGuards=True,FlexGuardFitMode='Between plates',FlexGuardWireEnabled=True,
                     FlexGuardWirePairs='Rear',StackOffsetY=3.,FlexGuardWireFrontY=16.,FlexGuardWireRearY=-20.)
        g=guard_layout(p)[0];openings=guard_wire_openings(p,g)
        self.assertEqual(len(openings),1)
        o=openings[0];self.assertEqual((o['name'],o['y'],o['width']),('Combined',1.,46.))
        self.assertEqual(o['bottom'],g['z'])
        self.assertEqual(len(guard_wire_openings(replace(p,FlexGuardFitMode='Plate-edge wrap'),g)),1)

    def test_wire_side_and_disabled_are_respected(self):
        p=Parameters(FlexSideGuards=True,FlexGuardFitMode='Between plates',FlexGuardWireEnabled=True,FlexGuardWireSide='Right')
        left,right=guard_layout(p)
        self.assertFalse(guard_wire_openings(p,left));self.assertTrue(guard_wire_openings(p,right))
        self.assertFalse(guard_wire_openings(replace(p,FlexGuardWireEnabled=False),right))

    def test_combined_opening_follows_lower_steps_without_middle_gap(self):
        p=Parameters(FlexSideGuards=True,FlexGuardFitMode='Between plates',FlexGuardWireEnabled=True,
            MidReachMode='Custom',MidFrontReach=24.,FlexGuardWireFrontY=32.,FlexGuardWireHeight=3.)
        windows=guard_wire_openings(p,guard_layout(p)[0])
        self.assertEqual(len(windows),2)
        self.assertAlmostEqual(windows[0]['y']+windows[0]['width']/2,windows[1]['y']-windows[1]['width']/2)
        self.assertNotEqual(windows[0]['bottom'],windows[1]['bottom'])

    def test_camera_closure_uses_inner_faces(self):
        p=Parameters(FPVEnabled=True,FlexSideGuards=True,FlexGuardCloseFront=True,FlexGuardFitMode='Between plates')
        c=closure_profile(p,guard_layout(p)[0])
        self.assertEqual(c['sections'][0][0],p.BottomThickness+guard_plate_gap(p))
        self.assertEqual(c['sections'][-1][0],plate_levels(p)['top_z']-guard_plate_gap(p))

    def test_vtx_opening_tracks_envelope_and_supports_wider_hardware(self):
        for design in ('2 plates','3 plates'):
            p=vtx_frame(PlateDesign=design)
            self.assertEqual(validate(p)[0],[])
            for g in guard_layout(p):
                y,z,w,h=guard_vtx_window(p,g)
                self.assertEqual(y,p.VTXOffsetY);self.assertEqual(w,p.VTXLength+2)
                self.assertLess(z-h/2,g['z']);self.assertEqual(z+h/2,g['deck_z']+p.VTXHeight+1)
            self.assertTrue(validate(replace(p,FlexGuardVTXOpening=False))[0])
            self.assertTrue(validate(replace(p,FlexGuardVTXSide='Left'))[0])

    def test_custom_window_and_signed_offsets(self):
        p=vtx_frame(FlexGuardVTXY=-3.,FlexGuardVTXZ=4.,FlexGuardVTXLength=18.,FlexGuardVTXHeight=4.)
        g=guard_layout(p)[0]
        self.assertEqual(guard_vtx_window(p,g),(p.VTXOffsetY-3,g['deck_z']+p.VTXHeight/2+4,18.,4.))
        self.assertEqual(Parameters.from_dict(p.to_dict()),p)

    def test_vtx_is_independent_of_vents_and_inactive_without_fpv(self):
        p=vtx_frame(FlexGuardStyle='Solid',FlexGuardVTXSide='Right')
        l,r=guard_layout(p)
        self.assertIsNone(guard_vtx_window(p,l));self.assertIsNotNone(guard_vtx_window(p,r))
        self.assertIsNone(guard_vtx_window(replace(p,FPVEnabled=False),r))
        self.assertIsNone(guard_vtx_window(replace(p,FlexGuardVTXOpening=False),r))

    def test_invalid_openings_protect_top_and_bearing_material(self):
        p=vtx_frame()
        for changes in ({'FlexGuardVTXHeight':100.},{'FlexGuardVTXY':-25.,'FlexGuardVTXZ':5.},
                        {'FlexGuardVTXZ':-100.},{'FlexGuardVTXLength':1.},
                        {'FlexGuardVTXY':math.nan},{'FlexGuardVTXZ':math.inf}):
            self.assertTrue(validate_flex(replace(p,**changes))[0],changes)

    def test_longitudinal_and_screw_support_still_required(self):
        p=vtx_frame(MidRearReach=45.,TopRearReach=45.)
        errors=validate(p)[0]
        self.assertTrue(any('VTX' in e for e in errors),errors)

    def test_preview_matches_new_height_wire_and_vtx_cuts(self):
        from freecad.rotorforge.flex_preview import flex_path,QtCore
        p=Parameters(FlexSideGuards=True,FlexGuardFitMode='Between plates',FlexGuardWireEnabled=True,FlexGuardStyle='Solid')
        g=guard_layout(p)[0];path=flex_path(p,g['role'])
        self.assertFalse(path.contains(QtCore.QPointF(0.,g['z']+2.)))
        self.assertTrue(path.contains(QtCore.QPointF(0.,g['top']-1.)))
        self.assertFalse(path.contains(QtCore.QPointF(0.,g['top']+1.)))
        p=vtx_frame(FlexGuardStyle='Solid');g=guard_layout(p)[0]
        self.assertFalse(flex_path(p,g['role']).contains(QtCore.QPointF(p.VTXOffsetY,g['deck_z']+6.)))
        self.assertTrue(flex_path(replace(p,FlexGuardVTXOpening=False),g['role']).contains(QtCore.QPointF(p.VTXOffsetY,g['deck_z']+6.)))
