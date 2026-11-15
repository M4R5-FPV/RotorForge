"""Physical analog and digital FPV camera presets for RotorForge.

+Y is forward (lens), rear_screw_inset is measured from the REAR of the
camera casing, not from the lens or its bezel.  Dimensions in this table are
not interchangeable with the maker's often *overall* depth (body + lens).
Published face dimensions and optics are cited by URL.  Where no dimensioned
side view exists, housing depth and rear screw inset are deliberately labelled
as estimates and remain individually user-editable.  This is a reference
library, NOT certified dimensional CAD / lens calibration data.

Custom measurements are never changed automatically. The DJI O4 Pro entry
is an equipment selection that retains its dedicated camera/air-unit geometry.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class CameraSpec:
    width: float
    height: float
    housing_depth: float
    lens_projection: float
    screw_spacing: float
    rear_screw_inset: float
    digital: bool
    fov: float
    aspect: str
    source: str
    fov_16_9: float = 0.0
    screw_measured: bool = False
    measured_body_depth: bool = False
    note: str = ''

# screw_spacing=0 means ONE M2 screw per side; nonzero is a vertical pair.
# 14 and 19-mm camera back-to-thread dimensions are often NOT documented;
# unlike the 7.7-mm T-Rex dimension, these are editable drawing estimates.
CAMERAS = {
    'DJI O4 Air Unit Pro': CameraSpec(20.,23.3,19.45,6.10,16.,16.,True,155.,'16:9',
        'https://dl.djicdn.com/downloads/DJI_O4_Air_Unit_Series/UM/DJI_O4_Air_Unit_Series_User_Manual_v1.0_en.pdf',
        screw_measured=True,measured_body_depth=True,
        note='DJI Pro dedicated model: 16 mm vertical pair AND 16 mm from casing rear to side thread line; 20 x 23.3 mm camera face, 25.55 mm overall depth.'),
    'Foxeer T-Rex Mini': CameraSpec(22,22,14.,10.5,6.3,7.7,False,150.,'4:3',
        'https://www.foxeer.com/foxeer-t-rex-mini-1500tvl-6ms-low-latency-super-wdr-fpv-camera-g-314',
        fov_16_9=175.,screw_measured=True,
        note='22×22 face, 6.3 mm pair, 7.7 mm rear inset; housing depth estimated from the dimension drawing. FOV 4:3 150°, 16:9 175°.'),
    'Caddx Ratel Pro': CameraSpec(19,19,14.2,14.3,0.,9.,False,125.,'4:3',
        'https://www.caddxfpv.com/products/caddxfpv-ratel-pro-analog-camera',
        note='One side screw. 28.5 mm overall from user drawing; 14.2 mm casing and 9 mm screw inset visually estimated. FOV aspect unspecified.'),
    'RunCam Phoenix 2': CameraSpec(19,19,12.,8.,0.,7.5,False,155.,'4:3',
        'https://www.runcam.com/download/Phoenix2/Phoenix_2_Manual.pdf',
        note='19×19 face, 20 mm camera depth in official drawing; 12/8 body/lens split inferred. Single M2 side screw, inset approximate.'),
    'Caddx Ratel 2': CameraSpec(19,19,13.,8.,0.,7.5,False,165.,'4:3',
        'https://en.caddxfpv.com.cn/products/ratel-2.html',fov_16_9=160.,
        note='19×19 mm face confirmed. Housing depth, lens projection, and rear screw inset are reference estimates. 165° / 160° FOV ratio assignment is approximate.'),
    'Foxeer Predator 5 Nano': CameraSpec(14,14,10.5,6.5,0.,5.5,False,155.,'4:3',
        'https://www.foxeer.com/foxeer-nano-predator-5-racing-camera-4ms-latency-super-wdr-g-305',
        note='14×14 mm without adapter. 155° diagonal, 125° horizontal. Depth, projection and side screw inset approximate.'),
    'Foxeer Razer Nano': CameraSpec(14,14,10.5,6.5,0.,5.5,False,150.,'4:3',
        'https://www.foxeer.com/foxeer-razer-nano-low-latency-fpv-camera-g-273',fov_16_9=140.,
        note='14×14 mm. Diagonal FOV 150° (4:3) or 140° (16:9). Body and screw dimensions approximate.'),
    'Walksnail Avatar HD Pro': CameraSpec(19,19,14.,10.,0.,7.5,True,160.,'16:9',
        'https://www.caddxfpv.com/products/walksnail-avatar-hd-pro-camera',
        note='Maker lists 19×19×24 mm overall. 14/10 body/lens split and single side screw inset approximate.'),
    'Walksnail Avatar HD Nano V3': CameraSpec(14,14,9.8,7.,0.,5.2,True,160.,'4:3',
        'https://www.caddxfpv.com/products/walksnail-avatar-hd-nano-camera-v3',
        note='Maker lists 14×14×16.8 mm overall and native 4:3. Housing/lens split and screw inset approximate.'),
    'HDZero Micro V3': CameraSpec(19,19,14.,10.,0.,7.5,True,157.,'16:9',
        'https://docs.hd-zero.com/camera-micro-v3',
        note='Maker lists 19×19×24 mm overall. 14/10 casing/lens split and side screw inset approximate. D157 H133 V72.'),
    'HDZero Nano V3': CameraSpec(14,14,10.,6.,0.,5.,True,155.,'4:3',
        'https://docs.hd-zero.com/camera-nano-v3',
        note='Maker lists 14×16×14 mm, 14×14 front. 10/6 casing/lens split and screw inset approximate. D155 H126 V94.'),
    # Width-only generic patterns: avoid suggesting exact optics / screw models.
    'Generic Analog 28 mm': CameraSpec(28,28,16.,8.,0.,8.,False,150.,'4:3',
        'Generic estimate — measure your camera',
        note='Unverified generic full-size 28 mm analog housing and lens. Measure all dimensions and optical FOV.'),
    'Generic Digital 20 mm': CameraSpec(20,20,13.,9.,0.,6.5,True,155.,'16:9',
        'Generic estimate — measure your camera',
        note='Unverified 20 mm camera geometry and optics. Measure all dimensions and FOV.'),
}

# Keep a single readable camera selector: analog first, then digital.
CAMERA_CHOICES = (('Custom measurements',) +
                  tuple(name for name,spec in CAMERAS.items() if not spec.digital) +
                  tuple(name for name,spec in CAMERAS.items() if spec.digital))

def get_camera_spec(name):
    return CAMERAS.get(name)


def camera_choices_for_system(video_system):
    """User-facing physical cameras for the chosen analog/digital FPV system."""
    if video_system not in ('Analog', 'Digital'):
        raise ValueError('Unknown video system: '+str(video_system))
    digital = video_system == 'Digital'
    return ('Custom measurements',) + tuple(
        name for name, spec in CAMERAS.items() if spec.digital == digital
    )
