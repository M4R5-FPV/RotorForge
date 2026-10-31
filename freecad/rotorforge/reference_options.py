"""Portable selectors and simple reference appearance; no CAD imports."""
FLAGS={'MotorEnvelopes':'DetailedMotorReferences','PropellerDiscs':'DetailedPropReferences','StackEnvelope':'DetailedStackReference','CameraEnvelope':'DetailedCameraReference','VTXEnvelope':'DetailedVTXReference','BatteryEnvelope':'DetailedBatteryReference'}
SIMPLE={'MotorEnvelopes':((.42,.46,.52),50),'PropellerDiscs':((.18,.70,.82),86),'StackEnvelope':((.20,.68,.36),68),'CameraEnvelope':((.18,.21,.25),15),'VTXEnvelope':((.58,.27,.68),35),'BatteryEnvelope':((.91,.45,.12),65)}

def enabled(p,role):return bool(p is not None and getattr(p,FLAGS.get(role,''),False))

# Requested generic 5-inch-class presentation hardware. Not fabrication models.
SHAFT_DIAMETER=5.0
PROP_BORE=5.1
PROP_HUB_HEIGHT=6.0
PROP_PITCH_INCH=3.7
LOCKNUT_AF=8.0
LOCKNUT_HEIGHT=5.0
SHAFT_EXPOSURE=1.0

def blade_pitch_angle(radius):
 import math
 return math.atan(PROP_PITCH_INCH*25.4/(2*math.pi*radius))

def shaft_top(bell_height):return bell_height+PROP_HUB_HEIGHT+LOCKNUT_HEIGHT+SHAFT_EXPOSURE


def stack_usb_centre(p):
 """Socket face centre in frame coordinates; PCB top plus half socket height."""
 from .parameters import stack_reference_z
 cap=min(1.,p.StackHeight*.1)
 return ((-1 if p.StackUSBFace=='Left' else 1)*((p.StackSpacing+6)/2+.8),
         p.StackOffsetY+p.StackUSBOffsetY,stack_reference_z(p)+p.StackHeight-cap+1.6)
