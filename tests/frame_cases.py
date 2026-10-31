"""Representative frame parameters used only by regression checks."""
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters, STANDOFF_COUNTS

FRAME_CASES = {
    '5-inch True X': Parameters(),
    '5-inch Stretched X': replace(Parameters(), Layout="Stretched X", Wheelbase=260.0),
    '5-inch Deadcat': replace(Parameters(), Layout="Deadcat", Wheelbase=270.0, LengthToWidth=1.05),
    '7-inch True X': replace(Parameters(), Wheelbase=340.0, PropDiameter=177.8,
                           ArmThickness=6.0, ArmWidth=16.0, RootExtension=6.0,
                           MotorSpacingX=19.0, MotorSpacingY=19.0, MotorPadDiameter=36.0),
}
FPV_CASES = {
    '5-inch FPV Analog': replace(FRAME_CASES['5-inch True X'], FPVEnabled=True),
    '5-inch FPV Digital': replace(FRAME_CASES['5-inch Stretched X'], FPVEnabled=True, VideoSystem='Digital',
                                 StandoffCount=STANDOFF_COUNTS[1],CameraSideBoltSpacing=0.),
    '5-inch FPV Deadcat': replace(FRAME_CASES['5-inch Deadcat'],FPVEnabled=True,TopWidth=50,
                                 StandoffFrontMount='Arm outer hole',StandoffRearMount='Arm outer hole'),
}
