"""Illustrative LiPo reference presets, not manufacturer-specific dimensions.

Nominal dimensions in mm and masses in g; edit for the actual battery.
Cell count is independent from measured dimensions and survives customization.
"""

LIPO_PRESETS = {
    '3S · 1500 mAh': (3, 35., 75., 21., 135.),
    '4S · 1500 mAh': (4, 35., 75., 28., 175.),
    '5S · 1300 mAh': (5, 38., 75., 32., 185.),
    '6S · 1300 mAh': (6, 38., 75., 38., 208.),
    '7S · 1300 mAh': (7, 39., 78., 44., 250.),
    '8S · 1100 mAh': (8, 40., 80., 47., 270.),
}
LIPO_CHOICES = tuple(LIPO_PRESETS) + ('Custom dimensions',)

def selected_profile(name):
    return LIPO_PRESETS.get(name)
