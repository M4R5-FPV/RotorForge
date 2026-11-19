"""Generic anodized motor-bell finishes; strictly visual, no geometry changes."""
MOTOR_FINISHES = {
    'Black': (.11,.125,.14),
    'Gunmetal': (.30,.32,.35),
    'Silver': (.68,.70,.73),
    'Gold': (.76,.52,.16),
    'Bronze': (.55,.34,.19),
    'Copper': (.72,.40,.24),
    'Red': (.68,.085,.12),
    'Orange': (.88,.30,.075),
    'Blue': (.10,.31,.75),
    'Purple': (.46,.19,.67),
    'Pink': (.84,.20,.47),
    'Green': (.20,.55,.20),
    'Teal': (.08,.53,.53),
}
MOTOR_FINISH_CHOICES = tuple(MOTOR_FINISHES)
# Internal face tag, resolved before applying colours to FreeCAD or Blender.
MOTOR_BELL = 'motor_bell'

def motor_finish(name):
    return MOTOR_FINISHES[name]

def motor_swatch(name):
    return '#' + ''.join(f'{round(c*255):02x}' for c in motor_finish(name))

def reference_face_colours(palette, name):
    bell = motor_finish(name)
    return tuple(bell if c == MOTOR_BELL else c for c in palette)
