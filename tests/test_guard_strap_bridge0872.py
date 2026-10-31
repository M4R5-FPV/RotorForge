"""Guard outlines bridge top-plate strap notches without changing the carbon."""
from dataclasses import replace
import unittest
from freecad.rotorforge.parameters import Parameters, strap_positions, validate
from freecad.rotorforge.airflow_gui import finished_part_path, QtCore
from freecad.rotorforge.flex_preview import guard_plan_path
from freecad.rotorforge.protection_layout import guard_layout
from freecad.rotorforge.cutouts import PATTERN_DEFAULTS, encode_patterns


class GuardStrapBridgeTests(unittest.TestCase):
    def test_both_guards_bridge_one_or_two_straps(self):
        for design in ('2 plates', '3 plates'):
            for count in ('1 strap', '2 straps'):
                p = Parameters(PlateDesign=design, FlexSideGuards=True,
                               FlexGuardExtendFront=True, StrapOpeningStyle='Outline cutouts',
                               StrapCount=count, StrapSingleY=-4.)
                self.assertEqual(validate(p)[0], [])
                plain = replace(p, StrapSlotsEnabled=False)
                for guard in guard_layout(p):
                    self.assertEqual(guard_plan_path(p, guard), guard_plan_path(plain, guard))

    def test_carbon_keeps_cutouts_and_only_guard_guide_bridges_them(self):
        p = Parameters(StrapOpeningStyle='Outline cutouts')
        actual = finished_part_path(p, 'TopPlate')
        guide = finished_part_path(p, 'TopPlate', include_strap_notches=False)
        for y in strap_positions(p):
            for side in (-1, 1):
                pt = QtCore.QPointF(side*(p.TopWidth/2-1), y)
                self.assertFalse(actual.contains(pt))
                self.assertTrue(guide.contains(pt))
        self.assertEqual(actual, finished_part_path(p, 'TopPlate'))

    def test_widening_tapers_fillets_and_custom_notches_remain(self):
        pattern = dict(PATTERN_DEFAULTS, role='TopPlate', mode='Outline notch',
                       shape='Circle', x=Parameters().TopWidth/2, y=0., width=6.)
        for changes in ({'TopCentreWidth':60., 'CentreSectionLength':60.},
                        {'TopPlateShape':'Tapered front', 'TopEdgeFillet':1.},
                        {'CutoutPatterns':encode_patterns([pattern])}):
            p = Parameters(FlexSideGuards=True, FlexGuardExtendFront=True,
                           StrapOpeningStyle='Outline cutouts', **changes)
            for guard in guard_layout(p):
                self.assertEqual(guard_plan_path(p, guard),
                                 guard_plan_path(replace(p, StrapSlotsEnabled=False), guard))
        self.assertFalse(finished_part_path(p, 'TopPlate', include_strap_notches=False)
                         .contains(QtCore.QPointF(p.TopWidth/2-.5, 0.)))

    def test_slots_and_disabled_openings_keep_their_existing_profiles(self):
        for p in (Parameters(), Parameters(StrapOpeningStyle='Outline cutouts', StrapSlotsEnabled=False)):
            self.assertEqual(finished_part_path(p, 'TopPlate'),
                             finished_part_path(p, 'TopPlate', include_strap_notches=False))
