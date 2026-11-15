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
}
PROP_FINISH_CHOICES = tuple(PROP_FINISHES)

def prop_finish(name):
    return PROP_FINISHES[name]

def prop_swatch(name):
    rgb = PROP_FINISHES[name][0]
    return "#" + "".join(f"{round(channel*255):02x}" for channel in rgb)
