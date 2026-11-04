"""Portable JSON preferences for optional hardware display, separate from geometry."""
import math


def validate_preferences(value):
    from .hardware_layout import HARDWARE_GROUPS, DEFAULT_OPTIONS
    if not isinstance(value, dict) or value.get('version') != 1:
        raise ValueError('Unsupported hardware reference preferences.')
    for key in ('created', 'visible'):
        if type(value.get(key)) is not bool:
            raise ValueError('Hardware reference ' + key + ' must be true or false.')
    options = value.get('options')
    if not isinstance(options, dict):
        raise ValueError('Hardware reference options must be an object.')
    groups = options.get('groups', DEFAULT_OPTIONS['groups'])
    if not isinstance(groups, list) or any(g not in HARDWARE_GROUPS for g in groups):
        raise ValueError('Unknown hardware reference group.')
    nuts = options.get('nuts', DEFAULT_OPTIONS['nuts'])
    engagement = options.get('engagement', DEFAULT_OPTIONS['engagement'])
    if type(nuts) is not bool:
        raise ValueError('Hardware retaining-hardware preference must be true or false.')
    if type(engagement) not in (float, int) or not math.isfinite(engagement) or not .5 <= engagement <= 10:
        raise ValueError('Thread engagement must be between 0.5 and 10 mm.')
    hidden = value.get('hidden_roles', [])
    if not isinstance(hidden, list) or any(not isinstance(role, str) for role in hidden):
        raise ValueError('Hidden hardware roles must be a list of names.')
    return dict(version=1, created=value['created'], visible=value['visible'],
                options=dict(groups=list(dict.fromkeys(groups)), nuts=nuts, engagement=float(engagement)),
                hidden_roles=list(dict.fromkeys(hidden)))


def from_settings(data):
    # Legacy JSON has no hardware information: leave the current preference alone.
    return validate_preferences(data['hardware_references']) if 'hardware_references' in data else None
