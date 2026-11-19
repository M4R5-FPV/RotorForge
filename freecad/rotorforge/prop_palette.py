"""Real-world-inspired FPV propeller finishes for 3D presentation only.

The colour values approximate moulded polycarbonate propellers; they do not
change blade geometry, hardware, exports, material mass or aerodynamics.
Transparency is an approximate FreeCAD viewport effect, not optical simulation.
"""

# label: ((red, green, blue), viewport transparency 0..100)
PROP_FINISHES = {
    "Smoke grey": ((0.27, 0.30, 0.33), 22),
    "Clear": ((0.86, 0.91, 0.95), 55),
    "Clear black": ((0.17, 0.18, 0.21), 38),
    "Black": ((0.10, 0.11, 0.13), 0),
    "White": ((0.86, 0.89, 0.91), 0),
    "Orange": ((0.96, 0.40, 0.075), 0),
    "Pink": ((0.96, 0.14, 0.51), 0),
    "Purple": ((0.50, 0.23, 0.73), 0),
    "Neon yellow": ((0.89, 0.98, 0.12), 0),
    "Lime green": ((0.53, 0.90, 0.12), 0),
    "Blue": ((0.16, 0.39, 0.82), 0),
    "Red": ((0.81, 0.11, 0.15), 0),
    "Teal": ((0.14, 0.62, 0.63), 0),
    "Neon yellow clear": ((0.90, 0.99, 0.16), 56),
    "Neon green clear": ((0.32, 0.98, 0.12), 56),
    "Neon orange clear": ((1.00, 0.42, 0.075), 52),
    "Neon pink clear": ((1.00, 0.22, 0.60), 52),
    "Lime green clear": ((0.53, 0.90, 0.12), 56),
    "Yellow clear": ((0.98, 0.81, 0.12), 58),
    "Orange clear": ((0.98, 0.47, 0.13), 57),
    "Red clear": ((0.92, 0.18, 0.22), 52),
    "Pink clear": ((0.98, 0.39, 0.65), 62),
    "Purple clear": ((0.63, 0.34, 0.86), 58),
    "Blue clear": ((0.22, 0.49, 0.96), 58),
    "Ice blue clear": ((0.49, 0.80, 0.98), 65),
    "Teal clear": ((0.16, 0.78, 0.78), 60),
    "Amber clear": ((0.91, 0.55, 0.16), 55),
    "Smoke brown": ((0.39, 0.27, 0.20), 40),
    "Smoke blue": ((0.29, 0.40, 0.55), 40),
    "Smoke purple": ((0.43, 0.32, 0.53), 40),
}
PROP_FINISH_CHOICES = tuple(PROP_FINISHES)

def prop_finish(name):
    return PROP_FINISHES[name]

def prop_swatch(name):
    rgb = PROP_FINISHES[name][0]
    return "#" + "".join(f"{round(channel*255):02x}" for channel in rgb)


def prop_optics(name):
    """Studio transmission and IOR for tinted moulded polycarbonate.

    Viewport alpha is an approximation, not a physically measured transmission.
    Neon finishes are saturated tints, never self-emissive light sources.
    """
    _, transparency = prop_finish(name)
    if not transparency:
        return dict(transmission=0., ior=1.58, roughness=.32)
    if name == 'Clear':
        return dict(transmission=.94, ior=1.58, roughness=.16)
    if name.lower().endswith('clear'):
        return dict(transmission=.86, ior=1.58, roughness=.22)
    return dict(transmission=.55 if transparency>=35 else .40, ior=1.58, roughness=.27)
