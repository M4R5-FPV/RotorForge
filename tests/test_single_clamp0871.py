"""The arm position chooses exactly one clamp and its receiving plate."""
from dataclasses import replace
import unittest
from freecad.rotorforge.parameters import (
    Parameters, TWO_PLATE_ARM_POSITIONS, arm_brace_layouts, arm_clamp_grip,
    arm_layouts, plate_holes, plate_levels, stack_mounting_role,
    standoff_layouts, underside_clamp_active, upper_clamp_active, validate)
from freecad.rotorforge.hardware_layout import hardware_layout
from freecad.rotorforge.nut_seats import joint_seat
from freecad.rotorforge.part_preview import preview_roles


class SingleClampTests(unittest.TestCase):
    def test_position_selects_one_clamp_independently_of_key(self):
        for position in TWO_PLATE_ARM_POSITIONS:
            for key in (False, True):
                p = Parameters(PlateDesign='2 plates', ArmBracesEnabled=True,
                               TwoPlateArmPosition=position, KeystoneEnabled=key)
                upper = position == 'Above bottom plate'
                expected = 'ArmClampPlate' if upper else 'ArmLowerClampPlate'
                self.assertEqual([c['role'] for c in arm_brace_layouts(p)], [expected])
                self.assertEqual(upper_clamp_active(p), upper)
                self.assertEqual(underside_clamp_active(p), not upper)
                self.assertEqual([r for r in preview_roles(p) if r in
                                  ('ArmClampPlate', 'ArmLowerClampPlate')], [expected])
                self.assertEqual(validate(p)[0], [])

    def test_only_selected_thickness_affects_grip_and_height(self):
        p = Parameters(PlateDesign='2 plates', ArmBracesEnabled=True,
                       ArmBraceThickness=4., UndersideClampThickness=3.)
        self.assertEqual(arm_clamp_grip(p), 10.)
        self.assertEqual(arm_brace_layouts(p)[0]['z'], -8.)
        self.assertEqual(plate_levels(p)['stack_deck_z'], 2.)
        self.assertEqual(validate(replace(p, ArmBraceThickness=0.))[0], [])
        p = replace(p, TwoPlateArmPosition='Above bottom plate')
        self.assertEqual(arm_clamp_grip(p), 11.)
        self.assertEqual(arm_brace_layouts(p)[0]['z'], 7.)
        self.assertEqual(plate_levels(p)['stack_deck_z'], 11.)
        self.assertEqual(validate(replace(p, UndersideClampThickness=0.))[0], [])

    def test_lower_clamp_service_holes_and_bottom_mounting_bores(self):
        p = Parameters(PlateDesign='2 plates', ArmBracesEnabled=True)
        self.assertEqual(stack_mounting_role(p), 'BottomPlate')
        self.assertEqual([2*r for _, r, n in plate_holes(p, 'BottomPlate') if n == 'stack'], [3.2]*4)
        self.assertEqual([2*r for _, r, n in plate_holes(p, 'ArmLowerClampPlate') if n == 'stack'], [6.]*4)
        p = replace(p, StackPressNuts=True)
        self.assertEqual([2*r for _, r, n in plate_holes(p, 'BottomPlate') if n == 'stack'], [p.PressNutBore]*4)
        self.assertEqual([2*r for _, r, n in plate_holes(p, 'ArmLowerClampPlate') if n == 'stack'], [6.]*4)

    def test_lower_arm_screws_span_one_clamp_and_receive_on_bottom(self):
        p = Parameters(PlateDesign='2 plates', ArmBracesEnabled=True,
                       ArmBraceThickness=4., UndersideClampThickness=3.)
        for mode in ('External hex nut', 'Recessed hex nut', 'M3 press nut'):
            q = replace(p, ArmNutMount=mode)
            for arm in arm_layouts(q):
                for point in arm['bolts']:
                    seat = joint_seat(q, 'Arm bolts', point)
                    self.assertEqual((seat['role'], seat['z'], seat['axis']), ('BottomPlate', 2., 1))
            specs = hardware_layout(q)
            self.assertTrue(all(s['point'][2] == -8. for s in specs if s['group'] == 'Arm bolts'))
            self.assertTrue(all(s['owner'] == 'BottomPlate' and s['point'][2] == 0.
                                for s in specs if s['group'] == 'Stack hardware'))

    def test_shared_standoffs_use_single_lower_sandwich(self):
        p = Parameters(PlateDesign='2 plates', ArmBracesEnabled=True,
                       StandoffFrontMount='Arm inner hole', StrapSlotsEnabled=False,
                       ArmBraceThickness=4., UndersideClampThickness=3.)
        for stand in standoff_layouts(p):
            self.assertEqual(stand['mount'], 'Bottom plate')
            if stand['shared_arm']:
                self.assertEqual(stand['grip_length'], 10.)
                self.assertEqual(stand['base'], 2.)
        self.assertEqual(validate(p)[0], [])

    def test_disabled_and_three_plate_ignore_clamp_settings(self):
        for p in (Parameters(PlateDesign='2 plates', KeystoneEnabled=True),
                  Parameters(ArmBracesEnabled=True, KeystoneEnabled=True)):
            self.assertFalse(upper_clamp_active(p) or underside_clamp_active(p))
            self.assertEqual(arm_brace_layouts(p), ())
            self.assertFalse(set(preview_roles(p)) & {'ArmClampPlate', 'ArmLowerClampPlate'})
