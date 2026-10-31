"""Explicit sizing actions, never silently applied on settings/project load."""
from dataclasses import replace
# nominal bolt-circle diameter, pad, clearance bore, centre bore, bell D/H, prop inches
MOTOR_SIZES={
 '9 mm bolt circle / 1404 / 3 inch':(9.,20.,2.2,4.,19.,12.,3.),
 '12 mm bolt circle / 1804 / 4 inch':(12.,25.,2.2,6.,23.,14.,4.),
 '16 mm bolt circle / 2207 / 5 inch':(16.,30.,3.2,9.,29.1,19.3,5.),
 '19 mm bolt circle / 2806.5 / 7 inch':(19.,36.,3.2,10.,33.4,20.,7.),
 '9 mm bolt circle / 1103 / 2 inch':(9.,25.,2.2,4.,14.,8.,2.),
}
def apply_motor_size(p,name):
    pitch,pad,hole,centre,diameter,height,prop=MOTOR_SIZES[name]
    return replace(p,MotorHoleLayout='4-hole bolt circle',MotorHoleRotation=0.,
                   MotorSpacingX=pitch,MotorSpacingY=pitch,MotorBoltCircle=pitch,MotorPadDiameter=pad,
                   MotorHoleDiameter=hole,MotorCenterDiameter=centre,MotorReferenceDiameter=diameter,
                   MotorReferenceHeight=height,PropReferenceHeight=height+2.,PropDiameter=prop*25.4)
