"""Exact plan outlines showing the guard outside an open strap recess."""
from guide_style import *
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.airflow_gui import finished_part_path
from freecad.rotorforge.flex_preview import guard_plan_path
from freecad.rotorforge.protection_layout import guard_layout

p = Parameters(PlateDesign='2 plates', BodyWidth=36., TopWidth=36.,
               FlexSideGuards=True, FlexGuardExtendFront=True, FlexGuardClearance=.3,
               StrapOpeningStyle='Outline cutouts', StrapCount='1 strap', StrapSingleY=0.)
region = rect(11., -12., 11., 24.)
plate = finished_part_path(p, 'TopPlate').intersected(region)
guard = guard_plan_path(p, guard_layout(p)[1]).intersected(region)
turn = QtGui.QTransform(); turn.rotate(90)
plate, guard = turn.map(plate), turn.map(guard)
gallery('GuardStrapBridge0872.png', [cell('Top view / one side of the top plate',
        (plate, LIGHT), (guard, TPU), box=QtCore.QRectF(-13., 10., 26., 13.))],
        1, rowheight=550, cellwidth=1000)
