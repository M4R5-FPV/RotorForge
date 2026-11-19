"""Render-only quality settings; no FreeCAD or Blender imports."""
QUALITY_NAMES = ('Fast', 'Balanced', 'High Quality', 'Ultra Quality')
MESH_DETAILS = (("Ultra (0.02 mm)", .02), ("Very fine (0.04 mm)", .04),
                ("Fine (0.08 mm)", .08), ("Standard (0.18 mm)", .18),
                ("Draft (0.35 mm)", .35))
# samples, min samples, noise threshold, pixel filter width, mesh index, denoise
QUALITY_PRESETS = (
    (64, 16, .03, 1.5, 3, True),
    (256, 32, .01, 1.25, 2, True),
    (512, 64, .005, 1.0, 1, True),
    (1024, 128, .0025, .9, 0, True),
)


def quality_options(samples, minimum, threshold, filter_width, mesh_index, denoise, preview=False):
    """Preview remains inexpensive and never changes the selected final settings."""
    if preview:
        samples, minimum, threshold, filter_width, mesh_index, denoise = (min(16,samples), 8, .05, 1.5, 3, True)
    return dict(samples=int(samples), minimum_samples=min(int(minimum), int(samples)),
                noise_threshold=float(threshold), filter_width=float(filter_width),
                deflection=MESH_DETAILS[mesh_index][1], denoise=bool(denoise), preview=bool(preview))


def set_optional(target, name, value):
    """Some Cycles properties/enums vary by Blender release or build."""
    if not hasattr(target,name):
        print('RotorForge: unsupported render property:', name, flush=True)
        return False
    try:
        setattr(target,name,value)
        return True
    except (AttributeError, TypeError, ValueError, RuntimeError) as exc:
        print('RotorForge: could not set',name,':',exc,flush=True)
        return False


def configure_cycles(scene, options):
    cycles=scene.cycles
    cycles.samples=options['samples']
    cycles.use_denoising=options.get('denoise',True)
    cycles.use_adaptive_sampling=True
    cycles.adaptive_threshold=options.get('noise_threshold',.01)
    cycles.adaptive_min_samples=min(cycles.samples,options.get('minimum_samples',32))
    set_optional(cycles,'pixel_filter_type','BLACKMAN_HARRIS')
    set_optional(cycles,'filter_width',options.get('filter_width',1.0))
    if cycles.use_denoising:
        # OIDN on CPU leaves graphics memory available for the render itself.
        # On builds without OIDN retain Blender's available denoiser.
        if set_optional(cycles,'denoiser','OPENIMAGEDENOISE'):
            set_optional(cycles,'denoising_use_gpu',False)
            set_optional(cycles,'denoising_prefilter','FAST' if options.get('preview') else 'ACCURATE')
            set_optional(cycles,'denoising_quality','BALANCED' if options.get('preview') else 'HIGH')
        set_optional(cycles,'denoising_input_passes','RGB_ALBEDO_NORMAL')
    # Explicitly disable global motion blur where supported. Flight prop blur
    # is a separate material effect and is intentionally preserved.
    set_optional(scene.render,'use_motion_blur',False)
    print('RotorForge render quality:', {k:options.get(k) for k in ('samples','minimum_samples','noise_threshold','filter_width','deflection','denoise','preview')},flush=True)
