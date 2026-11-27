"""Export selections, independent of Qt, FreeCAD and the geometry engine."""

DEFAULT_EXPORT_OPTIONS = {
    'cam_solids': True,
    'assembly_step': True,
    'carbon_dxf': True,
    'carbon_svg': True,
    'carbon_stl': True,
    'carbon_step': True,
    'printed_parts': True,
    'reports': True,
    'remove_existing_cam_layout': False,
}


def normalize_export_options(value=None):
    """Validate selections; callers that omit options preserve older full exports."""
    if value is None:
        return dict(DEFAULT_EXPORT_OPTIONS)
    if not isinstance(value, dict):
        raise TypeError('Export options must be a mapping.')
    unknown = set(value) - set(DEFAULT_EXPORT_OPTIONS)
    if unknown:
        raise ValueError('Unknown export selection: ' + ', '.join(sorted(unknown)))
    result = dict(DEFAULT_EXPORT_OPTIONS)
    result.update(value)
    for key, selected in result.items():
        if type(selected) is not bool:
            raise ValueError('Export selection '+key+' must be checked or unchecked.')
    if result['cam_solids'] and result['remove_existing_cam_layout']:
        raise ValueError('Cannot create and remove the CAM layout in the same export.')
    if not any(result[k] for k in ('cam_solids','assembly_step','carbon_dxf','carbon_svg','carbon_stl','carbon_step','printed_parts','reports')) and not result['remove_existing_cam_layout']:
        raise ValueError('Select at least one export item.')
    return result
