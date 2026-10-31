"""Millimetre-based frame layout, validation, and portable JSON settings.

This module deliberately has no FreeCAD or Qt imports. X is right, +Y is front.
Wheelbase sets the base motor diagonal. Optional Deadcat rear extensions add to it.
"""
from dataclasses import asdict, dataclass, fields, replace
from itertools import combinations
import json
import math
from .fpv import (VIDEO_SYSTEMS, VTX_PATTERNS, FPV_FIELDS, CAMERA_PIVOT_MODES, CAMERA_TILT_MECHANISMS, CAMERA_POSITION_MODES, CAMERA_BASE_MODES, camera_holes,
                  camera_slots, vtx_holes, front_platform_edge, rear_platform_edge, validate_fpv)
from .cutouts import parse_patterns
from .motor_pads import MOTOR_PAD_SHAPES, motor_pad_interior, motor_pad_bound, extended_motor_pad, motor_tip_slots, NEW_MOTOR_PAD_SHAPES, motor_corner_control, motor_pad_unit, motor_pad_rotation, motor_pad_pose
from .plate_profiles import CENTRE_WIDTH_FIELDS, centre_width_at, profiled_interior_distance, polygon_interior_distance
from .arm_roots import (ARM_ROOT_FITS, ROOT_BOLT_LAYOUTS, ROOT_PROFILE_FIELDS, ROOT_BOLT_COORDINATES, LEGACY_ROOT_BOLT_COORDINATES,
                        fitted_roots, root_joint_planes, compact_key_outline, root_width, widened_roots,
                        beam_profile_polygon, stem_interior_distance)

from .battery import BATTERY_FIELDS,validate_battery,GRIP_PATTERNS

# Read older settings without reviving removed optional parts.
RETIRED_PARAMETERS = frozenset(('CameraCutoutWidth','CameraCutoutDepth','CameraCutoutClearance','VTXNutMount','FlexELRSStem','ArmWindowWidth','VTXMountHeight','CameraPadBorder', 'CameraPadsEnabled', 'ELRSAntennaBar1', 'ELRSAntennaBar2', 'ELRSAntennaGripLength', 'ELRSAntennaLayout', 'ELRSAntennaSpacing', 'ELRSAntennaSplay', 'ELRSAntennaStemDiameter', 'ELRSAntennaStemDiameter2', 'ELRSAntennaTilt', 'GPSMountClearance', 'GPSMountDepth', 'GPSMountEnabled', 'GPSMountLength', 'GPSMountRise', 'GPSMountWidth', 'RearMountEnabled', 'RearMountFit', 'RearMountHeight', 'RearMountSetback', 'RearMountTopClearance', 'RearMountWall', 'TPUDensity', 'VTXAntennaBore', 'VTXAntennaConnector', 'VTXAntennaCount', 'VTXAntennaGripLength', 'VTXAntennaSpacing', 'VTXAntennaSplay', 'VTXAntennaStemDiameter', 'VTXAntennaTilt'))

STACK_PATTERNS = (('20 x 20 mm',20.),('30.5 x 30.5 mm',30.5))

def stack_label(value):
    return next(label for label,spacing in STACK_PATTERNS if abs(value-spacing)<1e-7)

def import_stack_spacing(value):
    if isinstance(value,str):
        for label,spacing in STACK_PATTERNS:
            if value==label:return spacing
        raise ValueError('Choose 20 x 20 mm or 30.5 x 30.5 mm for the FC stack.')
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
        raise ValueError('Stack spacing must be a finite positive size.')
    if any(abs(value-spacing)<1e-7 for label,spacing in STACK_PATTERNS):return float(value)
    import warnings
    nearest=min((spacing for label,spacing in STACK_PATTERNS),key=lambda spacing:abs(value-spacing))
    warnings.warn(f'Imported FC stack spacing {value:g} mm changed to the nearest supported pattern ({nearest:g} mm). Review the stack mounting before manufacture.',UserWarning)
    return nearest

from .design_options import OPTIONS as DESIGN_OPTIONS
from .flex_options import FLEX_OPTIONS
RETIRED_PARAMETERS=RETIRED_PARAMETERS|frozenset(('FlexClampSlit', 'FlexELRSBand', 'FlexELRSDiameter', 'FlexELRSGrip', 'FlexELRSHeight', 'FlexELRSLength', 'FlexELRSMountWidth', 'FlexELRSSecondLength', 'FlexELRSSpacing', 'FlexELRSStemDiameter', 'FlexELRSStyle', 'FlexGPSCable', 'FlexGPSClearance', 'FlexGPSHeight', 'FlexGPSLength', 'FlexGPSLip', 'FlexGPSMountWidth', 'FlexGPSStyle', 'FlexGPSTilt', 'FlexGPSWidth', 'FlexRearAnchors', 'FlexRearELRS', 'FlexRearEnabled', 'FlexRearFit', 'FlexRearGPS', 'FlexRearGripHeight', 'FlexRearOffset', 'FlexRearSetback', 'FlexRearVTX', 'FlexRearVentHeight', 'FlexRearVentLength', 'FlexRearVentWeb', 'FlexRearWall', 'FlexVTXBore', 'FlexVTXConnector', 'FlexVTXCount', 'FlexVTXDepth', 'FlexVTXHeight', 'FlexVTXMountWidth', 'FlexVTXPocket', 'FlexVTXSpacing', 'FlexVTXStyle', 'FlexVTXTilt'))
DESIGN_OPTIONS={**DESIGN_OPTIONS,**FLEX_OPTIONS}

SCHEMA = "rotorforge/1"
SUPPORTED_SCHEMAS = (SCHEMA, 'rotorforge-frame/1')
LAYOUTS = ("True X", "Stretched X", "Deadcat")
PLATE_DESIGNS = ("2 plates", "3 plates")
TWO_PLATE_ARM_POSITIONS = ('Below bottom plate', 'Above bottom plate')
ARM_LOCK_FIELDS = {'TwoPlateArmPosition', 'ArmBracesEnabled', 'ArmBraceThickness',
                   'KeystoneEnabled', 'KeystoneClearance', 'KeystoneRetainerDiameter',
                   'KeystoneRetainerHeadDiameter', 'KeystoneRetainerSpacing', 'ArmRootsFollowCentre', 'UndersideClampThickness', 'ArmRootReliefsEnabled',
                   'ArmRootFit', 'ArmJointClearance', 'KeystoneWidth', 'KeystoneLength', 'ArmRootReliefShape'} | ROOT_PROFILE_FIELDS
STANDOFF_COUNTS = ("4 (2 pairs)", "6 (3 pairs)", "8 (4 pairs)")
OUTER_STANDOFF_MOUNTS = ('Custom position', 'Arm inner hole', 'Arm outer hole')
EXTRA_STANDOFF_MOUNTS = ('Custom position', 'Front arm inner hole', 'Front arm outer hole',
                         'Rear arm inner hole', 'Rear arm outer hole')
ENUMERATIONS = {
                'BatteryMount':('Top plate','Bottom plate'), 'KeystoneShape':('Diamond','Chamfered diamond','Hexagon','Octagon'), 'LiPoPadShape':('Rounded rectangle','Rectangle','Capsule','Ellipse','Chamfered rectangle','Tapered','Hourglass','Mounting plate outline'), 'LiPoPadPattern':GRIP_PATTERNS,
                "MotorPadRotationPivot": ("Motor centre", "Pad beginning"), "MotorHoleLayout": ("4-hole bolt circle", "3-hole bolt circle"),"Layout": LAYOUTS, "PlateDesign": PLATE_DESIGNS, "StandoffCount": STANDOFF_COUNTS,
                "VideoSystem": VIDEO_SYSTEMS, "VTXPattern": VTX_PATTERNS,
                "StandoffFrontMount":OUTER_STANDOFF_MOUNTS,"StandoffRearMount":OUTER_STANDOFF_MOUNTS,
                "StandoffPair3Mount":EXTRA_STANDOFF_MOUNTS,"StandoffPair4Mount":EXTRA_STANDOFF_MOUNTS,
                "CameraPivotMode":CAMERA_PIVOT_MODES, 'TwoPlateArmPosition':TWO_PLATE_ARM_POSITIONS,
                'CameraMountMode':('Fixed', 'Variable'),
                'CameraTiltMechanism':CAMERA_TILT_MECHANISMS, 'CameraPositionMode':CAMERA_POSITION_MODES,
                'CameraBaseMode':CAMERA_BASE_MODES,
                'BottomReachMode':('Automatic', 'Custom'), 'MidReachMode':('Automatic', 'Custom'),
                'TopReachMode':('Automatic', 'Custom'), 'MotorPadShape':MOTOR_PAD_SHAPES, 'ArmRootFit':ARM_ROOT_FITS,
                'RootBoltLayout':ROOT_BOLT_LAYOUTS,
                'ArmRootReliefShape':('Round hole','Slot toward stack centre')}
ENUMERATIONS.update({k:v[3] for k,v in DESIGN_OPTIONS.items() if len(v)>3})
STRINGS = {'CutoutPatterns'}
BOOLEANS = {k for k,v in DESIGN_OPTIONS.items() if isinstance(v[0],bool)} | {'EstimateComponents','BatteryReferenceEnabled','LiPoPadEnabled','LiPoPadFollowPlate','ShowFrameCG',"ShowReferences", "FPVEnabled", "ArmBracesEnabled", "KeystoneEnabled", "StrapSlotsEnabled", 'ArmRootsFollowCentre', 'ArmRootReliefsEnabled', 'CameraFollowPlates', 'MotorTipSlotEnabled'}
ARM_NAMES = ("FrontRight", "FrontLeft", "RearLeft", "RearRight")
COMMON_STANDOFF_HEIGHTS = (22.0, 25.0, 30.0, 32.0, 35.0, 40.0)
ALIGNMENT_TOL = 1e-6
VENT_ROW_COUNTS=frozenset(('FlexGuardSlotCount','FlexGuardFCSlotCount'))


@dataclass(frozen=True)
class Parameters:
    ArmNutMount: str = "External hex nut"
    StackPressNuts: bool = False
    NutRecessDepth: float = .8
    NutRecessClearance: float = .15
    PressNutBore: float = 4.22
    PressNutFlangeDiameter: float = 5.56
    PressNutFlangeHeight: float = 1.5
    PressNutShankDiameter: float = 4.68
    PressNutShankDepth: float = 1.53
    PressNutFlangeRecess: float = 0.
    PressNutMinThickness: float = 1.53
    PrintedPartColour: str = "Black"
    FlexMotorProtectors: bool = False
    FlexProtectorWall: float = 2.0
    FlexProtectorFloor: float = 1.6
    FlexProtectorFit: float = .25
    FlexProtectorLanding: float = 3.0
    FlexProtectorRetention: str = 'Motor screws'
    FlexGuardCloseFront: bool = False
    FlexGuardFitMode: str = 'Plate-edge wrap'
    FlexGuardVTXOpening: bool = False
    FlexGuardVTXSide: str = 'Both'
    FlexGuardVTXY: float = 0.0
    FlexGuardVTXZ: float = 0.0
    FlexGuardVTXLength: float = 0.0
    FlexGuardVTXHeight: float = 0.0
    FlexGuardVTXClearance: float = 1.0
    FlexGuardCameraOverlap: float = 3.0
    FlexGuardExtendFront: bool = False
    FlexGuardVTXVents: bool = True
    FlexGuardFCVents: bool = True
    FlexGuardVentBoundaryOffset: float = 0.0
    FlexGuardFCVentShape: str = 'Horizontal slots'
    FlexGuardFCVentWidth: float = 10.0
    FlexGuardFCVentWeb: float = 3.0
    FlexGuardFCSlotHeight: float = 3.0
    FlexGuardFCSlotCount: int = 2
    FlexGuardVTXVentRearInset: float = 0.0
    FlexGuardVTXVentFrontInset: float = 0.0
    FlexGuardFCVentRearInset: float = 0.0
    FlexGuardFCVentFrontInset: float = 0.0
    FlexGuardVTXVentZOffset: float = 0.0
    FlexGuardFCVentZOffset: float = 0.0

    FlexGuardVentShape: str = 'Horizontal slots'
    FlexGuardVentWidth: float = 10.0
    FlexGuardVentWeb: float = 3.0
    FlexGuardUSBEnabled: bool = False
    FlexGuardUSBSide: str = 'Left'
    FlexGuardUSBY: float = 0.0
    FlexGuardUSBZ: float = 12.0
    FlexGuardUSBWidth: float = 14.0
    FlexGuardUSBHeight: float = 8.0
    FlexGuardStraps: bool = False
    FlexGuardStrapCount: str = '2 straps'
    FlexGuardStrapAuto: bool = True
    FlexGuardStrapY1: float = 18.0
    FlexGuardStrapY2: float = -18.0
    FlexGuardStrapWidth: float = 20.0
    FlexGuardStrapDepth: float = 6.0
    FlexGuardStrapEdge: str = 'Top edge'
    FlexGuardWireEnabled: bool = False
    FlexGuardWireSide: str = 'Both'
    FlexGuardWirePairs: str = 'Both'
    FlexGuardWireFrontY: float = 16.0
    FlexGuardWireRearY: float = -20.0
    FlexGuardWireWidth: float = 10.0
    FlexGuardWireHeight: float = 5.0

    FlexSideGuards: bool = False
    FlexGuardWall: float = 2.0
    FlexGuardFit: float = .25
    FlexFrontBumper: bool = False
    FlexBumperShape: str = 'Rounded shoe'
    FlexBumperTipWidth: float = 0.0
    FlexBumperRecess: float = 0.0
    FlexBumperLipReach: float = 0.0
    FlexBumperWidth: float = 0.0
    FlexBumperReach: float = 20.0
    FlexBumperProjection: float = 4.0
    FlexBumperWall: float = 2.0
    FlexBumperSole: float = 2.0
    FlexBumperLip: float = 1.2
    FlexBumperOverlap: float = 2.0
    FlexBumperFit: float = .2
    FlexGuardClearance: float = 1.0
    FlexGuardStyle: str = 'Vented'
    FlexGuardSlotHeight: float = 3.0
    FlexGuardSlotCount: int = 2
    FlexGuardFrontInset: float = 0.0
    FlexGuardRearInset: float = 0.0
    CameraAutoExtend: bool = True
    BottomFilletOpenings: bool = False
    MidFilletOpenings: bool = False
    TopFilletOpenings: bool = False
    ClampFilletOpenings: bool = False
    FlexInterfaceShape: str = 'Rounded rectangle'
    BottomEdgeFillet: float = 0.0
    MidEdgeFillet: float = 0.0
    TopEdgeFillet: float = 0.0
    ClampEdgeFillet: float = 0.0
    FlexCameraMode: str = 'Hard mount'
    FlexPadThickness: float = 2.0
    FlexPadPreload: float = 0.15
    FlexPadWidth: float = 16.0
    FlexPadHeight: float = 16.0
    FlexInsertWidth: float = 14.0
    FlexInsertHeight: float = 16.0
    FlexInsertCornerRadius: float = 1.0
    FlexInsertLipSide: str = 'Both sides'
    FlexInsertLip: float = 1.5
    FlexInsertFit: float = 0.15
    FlexDensity: float = 1.21
    BottomPlateShape: str = 'Rounded rectangle'
    BottomNoseShape: str = 'Straight'
    BottomNoseDepth: float = 6.0
    BottomNoseTipWidth: float = 35.0
    BottomRearShape: str = 'Straight'
    BottomRearDepth: float = 6.0
    BottomRearTipWidth: float = 35.0
    MidRearShape: str = 'Straight'
    MidRearDepth: float = 6.0
    MidRearTipWidth: float = 35.0
    TopFrontShape: str = 'Straight'
    TopFrontDepth: float = 12.0
    TopFrontTipWidth: float = 35.0
    TopFrontRecessWidth: float = 0.0
    TopFrontClearance: float = .5
    TopFrontSetback: float = 3.0
    TopRearShape: str = 'Straight'
    TopRearDepth: float = 6.0
    TopRearTipWidth: float = 35.0
    MidPlateShape: str = 'Rounded rectangle'
    TopPlateShape: str = 'Rounded rectangle'
    ClampPlateShape: str = 'Rounded rectangle'
    PlateEndWidth: float = 95.0
    ArmEdgeFillet: float = 0.0
    ArmFilletOpenings: bool = False
    ArmBeamShape: str = 'Straight'
    ArmProfileAmount: float = 30.0
    MotorPadBlendRadius: float = 2.0
    MotorPadNeckLength: float = 10.0
    MotorPadRelief: str = 'None'
    MotorPadReliefWidth: float = 3.0
    MotorPadReliefLength: float = 6.0
    EstimateComponents: bool = True
    MotorMass: float = 30.5
    PropMass: float = 4.0
    FCMass: float = 10.5
    ESCMass: float = 23.5
    VTXMass: float = 10.0
    CameraMass: float = 10.0
    OtherMass: float = 15.0
    ScrewMassScale: float = 1.0
    KeystoneShape: str = 'Diamond'
    BatteryReferenceEnabled: bool = True
    BatteryWidth: float = 38.0
    BatteryLength: float = 75.0
    BatteryHeight: float = 38.0
    BatteryMass: float = 208.0
    BatteryMount: str = 'Top plate'
    BatteryX: float = 0.0
    BatteryY: float = 0.0
    BatteryRotation: float = 0.0
    LiPoPadEnabled: bool = False
    LiPoPadOutlineWidthScale: float = 100.0
    LiPoPadOutlineLengthScale: float = 100.0
    LiPoPadFrontReach: float = 0.0
    LiPoPadRearReach: float = 0.0
    LiPoPadWidth: float = 36.0
    LiPoPadLength: float = 70.0
    LiPoPadThickness: float = 2.0
    LiPoPadShape: str = 'Rounded rectangle'
    LiPoPadCornerRadius: float = 3.0
    LiPoPadFollowPlate: bool = True
    LiPoPadPattern: str = 'Solid'
    LiPoPadGrooveWidth: float = 1.2
    LiPoPadGrooveDepth: float = 0.6
    LiPoPadGroovePitch: float = 6.0
    LiPoPadDensity: float = 1.2
    StandoffDensity: float = 2.7
    ShowFrameCG: bool = True
    MotorHoleLayout: str = '4-hole bolt circle'
    MotorBoltCircle: float = 16.0
    MotorHoleRotation: float = 0.0
    MotorPadRotation: float = 0.0
    MotorPadRotationPivot: str = 'Motor centre'
    DetailedMotorReferences: bool = False
    DetailedPropReferences: bool = False
    DetailedStackReference: bool = False
    DetailedVTXReference: bool = False
    DetailedBatteryReference: bool = False
    DetailedCameraReference: bool = False
    MotorReferenceDiameter: float = 28.0
    MotorReferenceHeight: float = 16.0
    PropReferenceHeight: float = 17.0
    Layout: str = "True X"
    Wheelbase: float = 250.0
    LengthToWidth: float = 1.18
    FrontSpread: float = 1.20
    RearArmExtension: float = 0.0
    PropDiameter: float = 129.54  # 5.1 inches
    RequiredPropGap: float = 4.0
    BodyLength: float = 115.0
    BodyWidth: float = 50.0
    TopLength: float = 108.0
    TopWidth: float = 46.0
    CornerRadius: float = 5.0
    BottomThickness: float = 2.0
    ClampThickness: float = 3.0
    TopThickness: float = 2.0
    ArmThickness: float = 5.0
    ArmWidth: float = 14.0
    ArmRootY: float = 30.0
    RootInset: float = 10.0
    RootExtension: float = 8.0
    RootBoltSpacing: float = 10.0
    RootHoleDiameter: float = 3.2
    MotorPadDiameter: float = 30.0
    MotorSpacingX: float = 16.0
    MotorSpacingY: float = 16.0
    MotorHoleDiameter: float = 3.2
    MotorCenterDiameter: float = 9.0
    StackSpacing: float = 30.5
    StackHoleDiameter: float = 3.2
    StackOffsetY: float = 0.0
    StandoffWidth: float = 34.0
    StandoffLength: float = 92.0
    StandoffHeight: float = 25.0
    StandoffDiameter: float = 5.5
    StandoffHoleDiameter: float = 3.2
    StrapCount: str = "2 straps"
    StrapSingleY: float = 0.0
    StrapOpeningStyle: str = "Slots"
    StrapNotchDepth: float = 3.0
    StackUSBFace: str = "Left"
    StackUSBOffsetY: float = 0.0
    StrapSlotWidth: float = 3.5
    StrapSlotLength: float = 18.0
    StrapOffsetY: float = 18.0
    StrapEdgeInset: float = 6.0
    MinimumWeb: float = 1.5
    CarbonDensity: float = 1.60  # g/cm^3, an estimate
    ShowReferences: bool = True
    PlateDesign: str = "3 plates"
    BottomFrontExtension: float = 25.0
    MidFrontReach: float = 24.0
    MidRearReach: float = 57.5
    StandoffCount: str = "4 (2 pairs)"
    StandoffPair3Y: float = -41.0
    StandoffPair3Width: float = 16.0
    StandoffPair4Y: float = 41.0
    StandoffPair4Width: float = 16.0
    FPVEnabled: bool = False
    VideoSystem: str = "Analog"
    CameraWidth: float = 19.0
    CameraHeight: float = 19.0
    CameraBodyDepth: float = 18.0
    CameraSideClearance: float = .5
    CameraSideHoleDiameter: float = 2.2
    CameraSideBoltSpacing: float = 6.5
    CameraMountY: float = 70.0
    CameraForeAftOffset: float = 0.0
    CameraPivotHeight: float = 18.0
    CameraTilt: float = 20.0
    CameraBracketThickness: float = 3.0
    CameraMountHoleDiameter: float = 3.2
    VTXPattern: str = "Both (20 + 25.5 mm)"
    VTXOffsetY: float = -70.0
    VTX20HoleDiameter: float = 2.2
    VTX25HoleDiameter: float = 2.2
    VTXWidth: float = 36.0
    VTXLength: float = 36.0
    VTXHeight: float = 12.0
    StandoffFrontMount: str = 'Custom position'
    StandoffRearMount: str = 'Custom position'
    StandoffPair3Mount: str = 'Custom position'
    StandoffPair4Mount: str = 'Custom position'
    CameraPivotMode: str = 'Automatic centre'
    CameraPlateLength: float = 20.0
    CameraTabReliefs: bool = True
    CameraTabCutterDiameter: float = 2.0
    CameraTabLength: float = 4.0
    CameraTabBottomRearOffset: float = 0.0
    CameraTabBottomFrontOffset: float = 0.0
    CameraTabTopRearOffset: float = 0.0
    CameraTabTopFrontOffset: float = 0.0
    CameraTabClearance: float = .1
    TwoPlateArmPosition: str = 'Below bottom plate'
    ArmBracesEnabled: bool = False
    ArmBraceThickness: float = 2.0
    KeystoneEnabled: bool = False
    KeystoneClearance: float = .1
    StrapSlotsEnabled: bool = True
    StackAccessDiameter: float = 6.0
    StackHeight: float = 18.0
    StackMountHeight: float = 0.0
    CameraMountMode: str = 'Variable'
    CameraTiltMin: float = 0.0
    CameraTiltMax: float = 45.0
    BottomReachMode: str = 'Automatic'
    BottomFrontReach: float = 82.5
    BottomRearReach: float = 45.0
    BottomBodyRearReach: float = 25.0
    MidReachMode: str = 'Automatic'
    TopReachMode: str = 'Automatic'
    TopFrontReach: float = 82.0
    TopRearReach: float = 90.0
    CutoutPatterns: str = '[]'
    MotorPadShape: str = 'Round'
    MotorPadCornerRadius: float = 4.0
    BottomCentreWidth: float = 0.0
    MidCentreWidth: float = 0.0
    TopCentreWidth: float = 0.0
    ClampCentreWidth: float = 0.0
    CentreSectionLength: float = 80.0
    CentreShoulderLength: float = 12.0
    CentreSectionY: float = 0.0
    ArmRootsFollowCentre: bool = True
    KeystoneRetainerDiameter: float = 3.2
    KeystoneRetainerHeadDiameter: float = 6.0
    KeystoneRetainerSpacing: float = 16.0
    UndersideClampThickness: float = 2.0
    ArmRootReliefsEnabled: bool = True
    ArmRootReliefShape: str = 'Round hole'
    CameraTiltMechanism: str = 'Dual arc slots'
    CameraPositionMode: str = 'Automatic centre'
    CameraFollowPlates: bool = True
    CameraPlateY: float = 70.0
    CameraTopRearOffset: float = 0.0
    CameraBaseMode: str = 'Automatic'
    CameraBaseFrontExtension: float = 0.0
    CameraBaseRearExtension: float = 0.0
    MotorTipLength: float = 8.0
    MotorTipSlotEnabled: bool = True
    MotorTipSlotWidth: float = 3.0
    MotorTipSlotLength: float = 6.0
    ArmRootFit: str = 'Independent'
    ArmJointClearance: float = 0.0
    KeystoneWidth: float = 10.0
    KeystoneLength: float = 10.0
    ArmRootWidth: float = 0.0
    ArmRootLength: float = 15.0
    ArmRootTaperLength: float = 20.0
    RootBoltLayout: str = 'Along arm'
    RootBolt1Y: float = -5.0
    RootBolt1X: float = 0.0
    RootBolt2Y: float = 5.0
    RootBolt2X: float = 0.0

    def to_dict(self):
        return asdict(self)

    def signature(self):
        from .parameter_memo import parameter_signature
        if hasattr(self,'_reads'):self._reads.update(self.__dataclass_fields__)
        return parameter_signature(self)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Parameters must be a JSON object.")
        data = dict(data)
        if data.get("StrapOpeningStyle")=="None":
            data.update(StrapOpeningStyle="Slots",StrapSlotsEnabled=False)
        # Preserve square legacy hole centres exactly; unequal rectangles cannot
        # be represented by an evenly spaced circle and are flagged for review.
        legacy_pattern = data.get('MotorHoleLayout') == 'Rectangle' or (
            'MotorHoleLayout' not in data and any(k in data for k in ('MotorSpacingX','MotorSpacingY')))
        if legacy_pattern:
            sx,sy=data.get('MotorSpacingX',16.),data.get('MotorSpacingY',16.)
            if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in (sx,sy)):
                raise ValueError('Legacy motor spacing must contain finite positive numbers.')
            data.update(MotorHoleLayout='4-hole bolt circle',MotorBoltCircle=math.hypot(sx,sy),
                        MotorHoleRotation=math.degrees(math.atan2(sy,sx)))
        if data.get('FlexBumperShape') in ('Scalloped shoe','Triple-lobe shoe'):data['FlexBumperShape']='Rounded shoe'
        legacy_bolts = {name:data.pop(name) for name in LEGACY_ROOT_BOLT_COORDINATES if name in data}
        for name,value in legacy_bolts.items():
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
                raise ValueError(name+' must be a finite number.')
        if data.get('CameraTiltMechanism')=='Front pivot + rear arc':
            data=dict(data,CameraTiltMechanism='Upper pivot + lower arc')
        if data.get('FlexProtectorRetention')=='Zip ties':data['FlexProtectorRetention']='Linked screw access'
        # Preserve old single-region settings in both sections on import/restore.
        for old,new in (('FlexGuardVentShape','FlexGuardFCVentShape'),('FlexGuardVentWidth','FlexGuardFCVentWidth'),('FlexGuardVentWeb','FlexGuardFCVentWeb'),('FlexGuardSlotHeight','FlexGuardFCSlotHeight'),('FlexGuardSlotCount','FlexGuardFCSlotCount')):
            if old in data and new not in data:data[new]=data[old]

        # Legacy row counts were lengths/floats; preserve their former rounding.
        for name in VENT_ROW_COUNTS:
            value=data.get(name)
            if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value):data[name]=int(round(value))
        legacy_lens={k:data[k] for k in ('CameraCutoutWidth','CameraCutoutDepth','CameraCutoutClearance') if k in data}
        if 'TopFrontClearance' not in data and 'CameraCutoutClearance' in legacy_lens:data['TopFrontClearance']=legacy_lens['CameraCutoutClearance']
        for name in RETIRED_PARAMETERS:data.pop(name,None)
        if 'StackSpacing' in data:data['StackSpacing']=import_stack_spacing(data['StackSpacing'])
        from .motor_pads import REPLACED_PAD_SHAPES
        if data.get('MotorPadShape') in REPLACED_PAD_SHAPES:
            import warnings
            old=data['MotorPadShape'];data['MotorPadShape']=REPLACED_PAD_SHAPES[old]
            warnings.warn(f'Motor pad {old} replaced by {data["MotorPadShape"]}; review this changed outline before manufacture.',UserWarning)
        data['ArmBeamShape']={'Slot beam':'Broad shoulder','Twin window beam':'Broad shoulder','Bridge beam':'Broad shoulder','Tapered beam':'Root taper','Waisted beam':'Hourglass neck','Double shoulder':'Broad shoulder','Scalloped beam':'Stepped beam','Faceted beam':'Motor flare','Barrel beam':'Broad shoulder'}.get(data.get('ArmBeamShape'),data.get('ArmBeamShape','Straight'))
        data['MotorPadRelief']={'Nose slot':'Neck slot','Twin nose holes':'Twin neck holes','Twin nose slots':'Twin neck slots'}.get(data.get('MotorPadRelief'),data.get('MotorPadRelief','None'))
        allowed = {f.name for f in fields(cls)}
        legacy_construction=data.pop('FrameStyle',None)
        if legacy_construction is not None:
            if legacy_construction!='Plate frame':
                raise ValueError('This saved construction is no longer supported. Use a two- or three-plate design.')
            # Earlier plate settings also saved fields for an optional retired
            # construction. Keep the supported plate dimensions on import.
            data={name:value for name,value in data.items() if name in allowed}
        unknown = sorted(set(data) - allowed)
        if unknown:
            raise ValueError("Unknown parameter(s): " + ", ".join(unknown))
        result = cls(**data)
        # Reject strings, booleans-as-numbers, NaNs, and infinities before geometry.
        for f in fields(cls):
            value = getattr(result, f.name)
            if f.name in ENUMERATIONS:
                if not isinstance(value, str) or value not in ENUMERATIONS[f.name]:
                    raise ValueError(f"{f.name} must be one of: " + ", ".join(ENUMERATIONS[f.name]))
            elif f.name in STRINGS:
                parse_patterns(value)
            elif f.name in BOOLEANS:
                if not isinstance(value, bool):
                    raise ValueError(f"{f.name} must be true or false.")
            elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{f.name} must be a finite number.")
        if legacy_lens and result.FPVEnabled and result.TopFrontShape=='Straight':
            # Translate an old automatic opening into one visible top-edge profile.
            from .fpv import camera_angles,camera_body_centre
            if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in legacy_lens.values()):raise ValueError('Legacy camera opening dimensions must be finite and non-negative.')
            clearance=float(legacy_lens.get('CameraCutoutClearance',.5))
            width=float(legacy_lens.get('CameraCutoutWidth',0)) or 2*(min(6,result.CameraWidth*.35,result.CameraHeight*.35)+clearance)
            depth=float(legacy_lens.get('CameraCutoutDepth',0)) or top_bounds(result)[1]-min(camera_body_centre(result,a)[0] for a in camera_angles(result))+result.CameraBodyDepth/2+clearance
            if depth>0:result=replace(result,TopFrontShape='Camera U recess',TopFrontDepth=depth,TopFrontRecessWidth=width,TopFrontSetback=0.,TopFrontClearance=max(0.,clearance))
        if 'LiPoPadFrontReach' not in data and 'LiPoPadRearReach' not in data and 'LiPoPadOutlineLengthScale' in data and result.LiPoPadOutlineLengthScale!=100:
            rear,front=top_bounds(result) if result.BatteryMount=='Top plate' else bottom_bounds(result)
            scale=result.LiPoPadOutlineLengthScale/100
            result=replace(result,LiPoPadFrontReach=max(.001,(front-result.StackOffsetY)*scale),LiPoPadRearReach=max(.001,(result.StackOffsetY-rear)*scale))
        if legacy_bolts:
            # Use the former front-right pattern as the reference, then mirror
            # its frame-aligned offsets. Rear offsets can change on Deadcat.
            front = arm_layouts(replace(result,RootBoltLayout='Along arm'))[0]
            ux,uy=front['unit'];hand=1 if (uy if abs(uy)>1e-12 else front['motor'][1])>0 else -1
            converted={}
            for index in (1,2):
                along=legacy_bolts.get(f'RootBolt{index}Along',-5. if index==1 else 5.)
                across=legacy_bolts.get(f'RootBolt{index}Across',0.)
                for axis,value in (('X',along*ux-across*uy*hand),('Y',along*uy+across*ux*hand)):
                    name=f'RootBolt{index}{axis}'
                    if name not in data:converted[name]=value
            result=replace(result,**converted)
        if "MidRearReach" not in data:
            result = replace(result, MidRearReach=result.BodyLength / 2 + result.StackOffsetY)
        if 'CameraSideBoltSpacing' not in data:
            result=replace(result,CameraSideBoltSpacing=0.)
        if 'CameraPositionMode' not in data:
            # Before 0.9 coordinates were body-centred; 0.9/0.10 used a rear pivot.
            angle=math.radians(result.CameraTilt)
            offset=result.CameraSideBoltSpacing/2 if 'CameraMountMode' in data else 0
            result=replace(result,CameraPositionMode='Custom position',CameraPlateY=result.CameraMountY,
                           CameraMountY=result.CameraMountY+offset*math.cos(angle),
                           CameraPivotHeight=result.CameraPivotHeight+offset*math.sin(angle))
            if offset:
                patterns=parse_patterns(result.CutoutPatterns)
                for pattern in patterns:
                    if pattern['role'] in ('CameraMountLeft','CameraMountRight'):pattern['x']-=offset*math.cos(angle)
                if patterns:result=replace(result,CutoutPatterns=json.dumps(patterns,separators=(',',':'),allow_nan=False))
        if 'CameraMountMode' not in data:
            result=replace(result,CameraMountMode='Fixed' if result.CameraSideBoltSpacing else 'Variable',
                           CameraTiltMin=0.,CameraTiltMax=max(1.,result.CameraTilt))
        if result.Layout == "Stretched X" and 0 < result.LengthToWidth < 1:
            result = replace(result, LengthToWidth=1 / result.LengthToWidth)
        if 'BottomBodyRearReach' not in data and three_plate(result):
            # Preserve the existing outline when opening older native/JSON
            # settings, then expose its formerly automatic edge as a dimension.
            try:result=replace(result,BottomBodyRearReach=legacy_bottom_body_reach(result))
            except (ValueError,ZeroDivisionError,OverflowError):pass
        return result


def motor_hole_offsets(p):
    """Fixing coordinates in pad axes; whole-pad orientation is per arm."""
    count=3 if p.MotorHoleLayout.startswith('3') else 4
    phase=math.radians(p.MotorHoleRotation)
    return tuple((p.MotorBoltCircle/2*math.cos(phase+2*math.pi*i/count),p.MotorBoltCircle/2*math.sin(phase+2*math.pi*i/count)) for i in range(count))


def nominal_motor_centres(p):
    if p.Layout == "True X":
        ratio = 1.0
    elif p.Layout == "Stretched X":
        # Stretch laterally: X is left/right and Y is front/rear in this model.
        factor = max(p.LengthToWidth, 1 / p.LengthToWidth)
        ratio = 1 / factor
    else:
        ratio = p.LengthToWidth
    spread = p.FrontSpread if p.Layout == "Deadcat" else 1.0
    rear_x = p.Wheelbase / math.sqrt((1 + spread) ** 2 + 4 * ratio ** 2)
    front_x, y = rear_x * spread, rear_x * ratio
    front_y=rear_y=y
    if p.Layout=='Deadcat':
        # Equal root-to-motor lengths redistribute longitudinal reach as the
        # front spreads. Both opposite diagonals remain exactly Wheelbase.
        front_root_x=arm_root_x(p,True)
        rear_root_x=arm_root_x(p,False)
        span_y=2*y
        delta=((front_x-front_root_x)**2-(rear_x-rear_root_x)**2)/max(1e-9,span_y-2*p.ArmRootY)
        front_y,rear_y=(span_y-delta)/2,(span_y+delta)/2
        # Extend along each existing rear root-to-motor axis. The front pair,
        # root references and arm angles remain fixed; only rear reach grows.
        dx,dy=rear_x-rear_root_x,rear_y-p.ArmRootY
        length=math.hypot(dx,dy)
        if length>1e-9:
            rear_x+=p.RearArmExtension*dx/length
            rear_y+=p.RearArmExtension*dy/length
    return ((front_x, front_y), (-front_x, front_y), (-rear_x, -rear_y), (rear_x, -rear_y))


def motor_centres(p):
    centres=[]
    for mx,my in nominal_motor_centres(p):
        root=(math.copysign(arm_root_x(p,my>0),mx),math.copysign(p.ArmRootY,my))
        length=math.dist(root,(mx,my))
        if length<.001:raise ValueError('Motor centre coincides with an arm root.')
        arm=dict(motor=(mx,my),unit=((mx-root[0])/length,(my-root[1])/length))
        centres.append(motor_pad_pose(p,arm)[1])
    return tuple(centres)


def arm_root_x(p,front):
    width=centre_width_at(p,'BottomPlate',p.ArmRootY if front else -p.ArmRootY,p.BodyWidth) if p.ArmRootsFollowCentre else p.BodyWidth
    return width/2-p.RootInset


def arm_layouts(p):
    result = []
    for name, (mx, my) in zip(ARM_NAMES, nominal_motor_centres(p)):
        rx = math.copysign(arm_root_x(p,my>0), mx)
        ry = math.copysign(p.ArmRootY, my)
        length = math.hypot(mx - rx, my - ry)
        if length < 0.001:
            raise ValueError("Motor centre coincides with an arm root.")
        ux, uy = (mx - rx) / length, (my - ry) / length
        start = (rx - p.RootExtension * ux, ry - p.RootExtension * uy)
        if p.RootBoltLayout=='Along arm':
            bolts=tuple((rx+t*ux,ry+t*uy) for t in (-p.RootBoltSpacing/2,p.RootBoltSpacing/2))
        else:
            # Reference offsets use the frame X/Y axes on the front-right arm.
            # Reflect X on the left and Y on the rear, without arm rotation.
            sx,sy=(1 if mx>0 else -1),(1 if my>0 else -1)
            bolts=tuple((rx+sx*x,ry+sy*y) for x,y in ((p.RootBolt1X,p.RootBolt1Y),(p.RootBolt2X,p.RootBolt2Y)))
        nominal=(mx,my)
        base=dict(unit=(ux,uy),motor=nominal)
        pivot,(mx,my)=motor_pad_pose(p,base)
        pux,puy=motor_pad_unit(p,base)
        motor_holes = tuple((mx + pux * a - puy * b, my + puy * a + pux * b)
                            for a,b in motor_hole_offsets(p))
        result.append(dict(name=name, root=(rx, ry), start=start, motor=(mx, my),
                           unit=(ux, uy), pad_unit=(pux,puy), nominal_motor=nominal,
                           pad_pivot=pivot, beam_end=pivot if p.MotorPadRotationPivot=='Pad beginning' else nominal,
                           pad_rotation_deg=motor_pad_rotation(p,dict(motor=nominal)), bolts=bolts, motor_holes=motor_holes,
                           length=length + p.RootExtension))
    return result


def frame_bolt_offsets(p):
    """Front-right reference offsets in frame X/Y, in either placement mode."""
    if p.RootBoltLayout!='Along arm':
        return ((p.RootBolt1X,p.RootBolt1Y),(p.RootBolt2X,p.RootBolt2Y))
    front=arm_layouts(p)[0]
    return tuple((pt[0]-front['root'][0],pt[1]-front['root'][1]) for pt in front['bolts'])


def stack_holes(p):
    return tuple((x, y + p.StackOffsetY) for x in (-p.StackSpacing / 2, p.StackSpacing / 2)
                 for y in (-p.StackSpacing / 2, p.StackSpacing / 2))


def standoff_pair_count(p):
    return STANDOFF_COUNTS.index(p.StandoffCount) + 2


def standoff_pairs(p):
    """Mirror each pair across X; retain the original two outer pairs."""
    pairs = [dict(position="Rear", y=-p.StandoffLength / 2, width=p.StandoffWidth),
             dict(position="Front", y=p.StandoffLength / 2, width=p.StandoffWidth)]
    for index in range(3, standoff_pair_count(p) + 1):
        pairs.append(dict(position=f"Pair {index}", y=getattr(p, f"StandoffPair{index}Y"),
                          width=getattr(p, f"StandoffPair{index}Width")))
    for pair in pairs:
        field='Standoff'+pair['position']+'Mount' if pair['position'] in ('Front','Rear') else 'Standoff'+pair['position'].replace(' ','')+'Mount'
        mount=getattr(p,field)
        pair['mount_setting']=mount
        if mount!='Custom position':
            front=pair['position']=='Front' if pair['position'] in ('Front','Rear') else mount.startswith('Front')
            arm=next(a for a in arm_layouts(p) if a['root'][0]>0 and (a['root'][1]>0)==front)
            point=arm['bolts'][0 if 'inner' in mount else 1]
            pair['width'],pair['y']=2*abs(point[0]),point[1]
    return sorted(pairs, key=lambda pair: pair["y"])


def standoff_holes(p):
    return tuple((x, pair["y"]) for pair in standoff_pairs(p)
                 for x in (-pair["width"] / 2, pair["width"] / 2))


def shared_arm_root(p,point):
    for arm in arm_layouts(p):
        for index,bolt in enumerate(arm['bolts']):
            if math.dist(point,bolt)<=ALIGNMENT_TOL:
                return dict(arm=arm['name'],hole='inner' if index==0 else 'outer',point=bolt)
    return None


def three_plate(p):
    return p.PlateDesign == "3 plates"


def arms_above_bottom(p):
    return three_plate(p) or p.TwoPlateArmPosition == TWO_PLATE_ARM_POSITIONS[1]


def arm_braces(p):
    return not three_plate(p) and p.ArmBracesEnabled


def upper_clamp_active(p):
    return arm_braces(p) and arms_above_bottom(p)


def keystone_active(p):
    return p.KeystoneEnabled and (three_plate(p) or arm_braces(p))


def keystone_retainers(p):
    """Compatibility API: a lower capture plate replaces point retainers."""
    return ()


def underside_clamp_active(p):
    return arm_braces(p) and not arms_above_bottom(p)


def underside_clamp_layout(p):
    if not underside_clamp_active(p):return None
    return arm_brace_layouts(p)[0]


def arm_clamp_grip(p):
    return p.BottomThickness+p.ArmThickness+(p.ClampThickness if three_plate(p) else
                                             p.ArmBraceThickness if upper_clamp_active(p) else 0)+(p.UndersideClampThickness if underside_clamp_active(p) else 0)


def arm_brace_layouts(p):
    """Return the single clamp on the side of the arms opposite the bottom plate."""
    if not arm_braces(p):
        return ()
    upper=upper_clamp_active(p)
    thickness=p.ArmBraceThickness if upper else p.UndersideClampThickness
    z=p.BottomThickness+p.ArmThickness if upper else -p.ArmThickness-thickness
    bolts=tuple(pt for a in arm_layouts(p) for pt in a['bolts'])
    stack_radius=max(p.StackHoleDiameter,p.StackAccessDiameter if underside_clamp_active(p) else 0)/2
    rear=min(min(pt[1] for pt in bolts)-root_width(p)/2,
             p.StackOffsetY-p.StackSpacing/2-stack_radius-p.MinimumWeb)
    front=max(max(pt[1] for pt in bolts)+root_width(p)/2,
              p.StackOffsetY+p.StackSpacing/2+stack_radius+p.MinimumWeb)
    # Absorb nearby standoff feet into the deck instead of leaving them
    # cutting through its edge. Revisit pairs after each outline extension.
    support=max(p.StandoffDiameter/2,p.StackAccessDiameter/2 if underside_clamp_active(p) else 0)+p.MinimumWeb
    for _ in range(standoff_pair_count(p)+1):
        previous=(rear,front)
        for pair in standoff_pairs(p):
            x,y=pair['width']/2,pair['y']
            local_width=centre_width_at(p,'ArmClampPlate',y,p.BodyWidth)
            if x>local_width/2-support:
                continue
            inside=profiled_interior_distance((x,y),p,'ArmClampPlate',p.BodyWidth,rear,front,p.CornerRadius)
            if inside<-(p.StandoffDiameter/2+.25):
                continue
            q=max(0,x-(local_width/2-p.CornerRadius))
            margin=(p.CornerRadius-math.sqrt(max(0,(p.CornerRadius-support)**2-q*q))
                    if q and p.CornerRadius>support else support)
            rear=min(rear,y-margin);front=max(front,y+margin)
        if (rear,front)==previous:
            break
    return (dict(role='ArmClampPlate' if upper else 'ArmLowerClampPlate',z=z,thickness=thickness,bolts=bolts,
                 stack_holes=stack_holes(p),rear=rear,front=front,width=p.BodyWidth,radius=p.CornerRadius),)


def arm_clamp_interior_distance(point,p):
    from .clamp_outline import clamp_interior_distance
    return clamp_interior_distance(point,p)


def bottom_stack_hole_diameter(p):
    return p.StackAccessDiameter if three_plate(p) or upper_clamp_active(p) else p.StackHoleDiameter


def stack_mounting_role(p):
    return 'MidPlate' if three_plate(p) else 'ArmClampPlate' if upper_clamp_active(p) else 'BottomPlate'


def stack_reference_z(p):
    levels=plate_levels(p)
    clearance=max(0.,p.PressNutFlangeHeight-p.PressNutFlangeRecess) if p.StackPressNuts else p.StackMountHeight
    return levels['stack_deck_z']+clearance


def bottom_bounds(p,include_body=True):
    if p.BottomReachMode=='Custom':
        return -p.BottomRearReach, p.BottomFrontReach
    rear, front = -p.BodyLength/2, p.BodyLength/2 + (p.BottomFrontExtension if three_plate(p) else 0)
    if three_plate(p):
        root_reach=(p.ArmRootY+p.RootBoltSpacing/2+p.ArmWidth/2+p.MinimumWeb
                    if p.RootBoltLayout=='Along arm' and not widened_roots(p) else
                    max(-pt[1] for a in arm_layouts(p) for pt in a['bolts'])+root_width(p)/2+p.MinimumWeb)
        reach=max(root_reach,
                  -p.StackOffsetY+p.StackSpacing/2+p.StackAccessDiameter/2+p.MinimumWeb)
        # The lower sandwich ends just behind the rear arm roots. Rear VTX
        # and mid-mounted standoffs are carried independently by the mid.
        for pair in standoff_pairs(p):
            pt=(pair['width']/2,pair['y'])
            if pair['position']!='Rear' and not shared_arm_root(p,pt):
                mr,mf=mid_bounds(p)
                on_mid=max([profiled_interior_distance(pt,p,'MidPlate',p.BodyWidth,mr,mf,p.CornerRadius)]+
                           [mid_tab_interior_distance(pt,p,a) for a in arm_layouts(p) if a['root'][1]>0])>=0
                if not on_mid:reach=max(reach,-pair['y']+p.StandoffDiameter/2+p.MinimumWeb)
        rear=-min(p.BodyLength/2,reach)
        if include_body:rear=min(rear,p.StackOffsetY-p.BottomBodyRearReach)
    if p.FPVEnabled:
        if not three_plate(p):
            rear=min(rear, rear_platform_edge(p))
        front=max(front, front_platform_edge(p))
        if three_plate(p): front=max(front,top_bounds(p)[1]+p.MinimumWeb)
    return rear, front


def top_bounds(p):
    if p.TopReachMode=='Custom':
        return -p.TopRearReach, p.TopFrontReach
    if p.FPVEnabled:
        return min(-p.TopLength/2,rear_platform_edge(p)),max(p.TopLength/2,front_platform_edge(p,'TopPlate'))
    return -p.TopLength/2,p.TopLength/2


def mid_bounds(p):
    rear = p.StackOffsetY - p.MidRearReach
    if p.FPVEnabled and p.MidReachMode=='Automatic':
        rear = min(rear, rear_platform_edge(p))
    return rear, p.StackOffsetY + p.MidFrontReach


def mid_tabs(p):
    """Bolt-pad envelopes; actual tabs are clipped to each front arm profile."""
    return tuple((arm["bolts"][0], arm["bolts"][1], root_width(p) / 2)
                 for arm in arm_layouts(p) if arm["root"][1] > 0)


def bottom_body_bounds(p):
    """Three-plate body ends at an explicit distance behind the stack."""
    rear,front=bottom_bounds(p)
    if not three_plate(p):return rear,front
    return p.StackOffsetY-p.BottomBodyRearReach,front


def legacy_bottom_body_reach(p):
    """Recover the pre-0.20 body edge only when migrating older settings."""
    rear,front=bottom_bounds(p,include_body=False)
    arms=arm_layouts(p)
    edge=min(p.StackOffsetY-p.StackSpacing/2-p.StackAccessDiameter/2-p.MinimumWeb,
             min(max(pt[1] for pt in arm['bolts'])+p.MinimumWeb for arm in arms if arm['root'][1]<0))
    # Extra bottom-mounted standoffs still need their full bearing surface.
    mr,mf=mid_bounds(p)
    for pair in standoff_pairs(p):
        pt=(pair['width']/2,pair['y'])
        if pair['position']=='Rear' or shared_arm_root(p,pt):continue
        on_mid=max([profiled_interior_distance(pt,p,'MidPlate',p.BodyWidth,mr,mf,p.CornerRadius)]+
                   [mid_tab_interior_distance(pt,p,a,arms) for a in arms if a['root'][1]>0])>=0
        if pair['position']=='Front' or not on_mid:edge=min(edge,pair['y']-p.StandoffDiameter/2-p.MinimumWeb)
    return p.StackOffsetY-max(rear,edge)


def bottom_tabs(p):
    """Rear bolt envelopes; clipped to arms and both sandwich plates."""
    if not three_plate(p):return ()
    return tuple((arm['bolts'][0],arm['bolts'][1],root_width(p)/2)
                 for arm in arm_layouts(p) if arm['root'][1]<0)


def plate_levels(p):
    arm_z = p.BottomThickness if arms_above_bottom(p) else -p.ArmThickness
    mid_z = p.BottomThickness + p.ArmThickness
    deck_z = mid_z + p.ClampThickness if three_plate(p) else p.BottomThickness
    stack_deck_z=deck_z
    if upper_clamp_active(p):
        clamp=arm_brace_layouts(p)[0]
        stack_deck_z=clamp['z']+clamp['thickness']
    rear_base=deck_z
    if not three_plate(p):
        pair=next(pair for pair in standoff_pairs(p) if pair['position']=='Rear')
        point=(pair['width']/2,pair['y'])
        if upper_clamp_active(p) and arm_clamp_interior_distance(point,p)>=0:
            rear_base=stack_deck_z
        elif arms_above_bottom(p) and shared_arm_root(p,point):
            rear_base=p.BottomThickness+p.ArmThickness
    return dict(arm_z=arm_z, mid_z=mid_z, deck_z=deck_z,stack_deck_z=stack_deck_z,
                top_z=rear_base + p.StandoffHeight)


def standoff_layouts(p):
    levels = plate_levels(p)
    result = []
    for pair in standoff_pairs(p):
        for x in (-pair["width"] / 2, pair["width"] / 2):
            point = (x, pair["y"])
            shared=shared_arm_root(p,point)
            on_mid = three_plate(p) and (shared is not None or pair["position"] == "Rear" or
                     (pair["position"] != "Front" and mid_interior_distance(point, p) >= 0))
            base = levels["deck_z"] if on_mid else p.BottomThickness
            mount='Mid plate' if on_mid else 'Bottom plate'
            if upper_clamp_active(p) and arm_clamp_interior_distance(point,p)>=0:
                base=levels['stack_deck_z'];mount='Arm clamp plate'
            elif not three_plate(p) and arms_above_bottom(p) and shared:
                base=p.BottomThickness+p.ArmThickness;mount='Arm top'
            result.append(dict(point=point, base=base, length=levels["top_z"] - base,
                               position=pair["position"], mount=mount,
                               shared_arm=shared,grip_length=arm_clamp_grip(p) if shared else None))
    return result


def standoff_heights(p):
    return {stand["position"]: stand["length"] for stand in standoff_layouts(p)}


def strap_positions(p):
    return (p.StrapSingleY,) if p.StrapCount=='1 strap' else (p.StrapOffsetY,-p.StrapOffsetY)


def strap_slots(p):
    if not p.StrapSlotsEnabled or p.StrapOpeningStyle != "Slots":
        return ()
    half = (p.StrapSlotLength - p.StrapSlotWidth) / 2
    return tuple(((x, y - half), (x, y + half), p.StrapSlotWidth / 2)
                 for x in (-(p.TopWidth / 2 - p.StrapEdgeInset), p.TopWidth / 2 - p.StrapEdgeInset)
                 for y in strap_positions(p))


def point_segment_distance(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    if length2 < 1e-18:
        return math.dist(point, a)
    t = max(0.0, min(1.0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length2))
    return math.hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dy)


def segment_distance(a, b, c, d):
    def cross(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    ca, cb = cross(a, b, c), cross(a, b, d)
    ac, ad = cross(c, d, a), cross(c, d, b)
    if ca * cb < 0 and ac * ad < 0:
        return 0.0
    return min(point_segment_distance(a, c, d), point_segment_distance(b, c, d),
               point_segment_distance(c, a, b), point_segment_distance(d, a, b))


def rect_interior_distance(point, width, length, radius):
    """Positive distance to a rounded rectangle boundary for interior points."""
    qx = abs(point[0]) - (width / 2 - radius)
    qy = abs(point[1]) - (length / 2 - radius)
    return radius - math.hypot(max(qx, 0), max(qy, 0)) - min(max(qx, qy), 0)


def bottom_interior_distance(point, p):
    rear,front=bottom_body_bounds(p)
    inside=profiled_interior_distance(point,p,'BottomPlate',p.BodyWidth,rear,front,p.CornerRadius)
    if not three_plate(p):return inside
    arms=arm_layouts(p)
    return max([inside]+[bottom_tab_interior_distance(point,p,arm,arms) for arm in arms if arm['root'][1]<0])


def bottom_tab_interior_distance(point,p,arm,arms=None):
    arms=arm_layouts(p) if arms is None else arms
    return min(mid_tab_interior_distance(point,p,arm,arms),
               profiled_interior_distance(point,p,'BottomPlate',p.BodyWidth,*bottom_bounds(p),p.CornerRadius),
               profiled_interior_distance(point,p,'MidPlate',p.BodyWidth,*mid_bounds(p),p.CornerRadius))


def top_interior_distance(point,p):
    rear,front=top_bounds(p)
    inside=profiled_interior_distance(point,p,'TopPlate',p.TopWidth,rear,front,p.CornerRadius)
    return inside


def mid_interior_distance(point, p):
    rear, front = mid_bounds(p)
    inside = profiled_interior_distance(point,p,'MidPlate',p.BodyWidth,rear,front,p.CornerRadius)
    arms=arm_layouts(p)
    tabs=max(mid_tab_interior_distance(point,p,arm,arms) for arm in arms if arm['root'][1]>0)
    # Only the forward clamp ears are trimmed. The mid carries the rear VTX
    # independently of the shorter bottom plate.
    return max(inside,min(tabs,bottom_interior_distance(point,p)))


def mid_tab_interior_distance(point,p,arm,arms=None):
    """Conservative edge clearance inside a pad trimmed to its arm root."""
    inside=min(root_width(p)/2-point_segment_distance(point,*arm['bolts']),stem_interior_distance(p,arm,point))
    if fitted_roots(p):
        arms=arm_layouts(p) if arms is None else arms
        inside=min([inside]+[limit-n[0]*point[0]-n[1]*point[1] for n,limit in root_joint_planes(p,arm,arms)])
        if keystone_active(p):inside=min(inside,-polygon_interior_distance(point,compact_key_outline(p,arms,True)))
    return inside


def plate_holes(p,role):
    """Layer-specific holes; a rear mid standoff needs no hole in the bottom."""
    arms=arm_layouts(p)
    if role=='TopPlate':
        return [(s['point'],p.StandoffHoleDiameter/2,'standoff') for s in standoff_layouts(p)]
    stack_d=bottom_stack_hole_diameter(p) if role=='BottomPlate' else p.StackAccessDiameter if role=='ArmLowerClampPlate' else p.StackHoleDiameter
    holes=[(pt,stack_d/2,'stack') for pt in stack_holes(p)]
    holes += [(pt,p.RootHoleDiameter/2,'arm root') for arm in arms for pt in arm['bolts']]
    if role in ('BottomPlate','ArmClampPlate'):
        holes += [(r['point'],r['bore']/2,'keystone retainer') for r in keystone_retainers(p)]
    for stand in standoff_layouts(p):
        use=((arm_clamp_interior_distance(stand['point'],p)>=0 or stand['shared_arm'] is not None) if role=='ArmLowerClampPlate' else
             stand['mount']=='Mid plate' if role=='MidPlate' else
             stand['mount']=='Arm clamp plate' if role=='ArmClampPlate' else
             stand['mount']!='Mid plate' or stand['shared_arm'] is not None)
        if use:
            access=role=='ArmLowerClampPlate' and stand['shared_arm'] is None
            holes.append((stand['point'],(p.StackAccessDiameter if access else p.StandoffHoleDiameter)/2,'standoff access' if access else 'standoff'))
    if role=='MidPlate' or role=='BottomPlate' and not three_plate(p):
        holes += [(pt,r,'VTX') for pt,r,_ in vtx_holes(p)]
    from .nut_seats import seats
    press=[s['point'] for s in seats(p,role) if s['mode']=='M3 press nut']
    return [(pt,p.PressNutBore/2 if any(math.dist(pt,q)<1e-6 for q in press) else r,kind) for pt,r,kind in holes]


def prop_gap(p):
    return min(math.dist(a, b) for a, b in combinations(motor_centres(p), 2)) - p.PropDiameter


from .parameter_memo import parameter_cache

@parameter_cache(maxsize=32)
def _validation_result(p):
    """Return (errors, warnings). Invalid layouts never reach the CAD kernel."""
    if p.StackSpacing not in (20.,30.5):return ['FC stack pattern must be 20 x 20 mm or 30.5 x 30.5 mm.'], []
    if p.MotorHoleLayout not in ENUMERATIONS['MotorHoleLayout']:
        return ['Select a 4-hole or 3-hole bolt-circle motor pattern.'], []
    try:
        Parameters.from_dict(p.to_dict())
    except (TypeError, ValueError) as exc:
        return [str(exc)], []
    from .flex import validate_flex
    flex_errors,flex_warnings=validate_flex(p)
    errors, warnings = validate_battery(p)+flex_errors, flex_warnings
    from .nut_seats import validate_seats
    errors.extend(validate_seats(p))
    if p.StackSpacing not in (20.,30.5):errors.append("FC stack pattern must be 20 x 20 mm or 30.5 x 30.5 mm.")
    if (p.MotorHoleLayout=='4-hole bolt circle' and not math.isclose(p.MotorSpacingX,p.MotorSpacingY)
        and math.isclose(p.MotorBoltCircle,math.hypot(p.MotorSpacingX,p.MotorSpacingY))
        and math.isclose(p.MotorHoleRotation,math.degrees(math.atan2(p.MotorSpacingY,p.MotorSpacingX)))):
        warnings.append('An older unequal rectangular motor pattern was converted to a regular four-hole circle. Hole positions changed; measure your motor and set its bolt-circle diameter and rotation before manufacturing.')
    if not -180<=p.MotorPadRotation<=180:errors.append("Motor pad rotation must be between -180 and 180 degrees.")
    if not -360<=p.MotorHoleRotation<=360:errors.append("Motor hole rotation must be between -360 and 360 degrees.")
    if not p.DetailedPropReferences and p.PropReferenceHeight<=p.MotorReferenceHeight:errors.append("Prop reference height must be above the motor reference body.")
    if p.BottomNoseShape!='Straight':
        nr,nf=bottom_bounds(p)
        if not math.isfinite(p.BottomNoseDepth) or not 0<p.BottomNoseDepth<=(nf-nr)/2:errors.append('Front edge depth must be positive and no more than half the bottom plate length.')
        if not math.isfinite(p.BottomNoseTipWidth) or not 10<=p.BottomNoseTipWidth<=90:errors.append('Front tip width must be between 10 and 90 percent.')
    if not 40<=p.PlateEndWidth<=100:errors.append('Plate end width must be between 40 and 100 percent.')
    if not 0<=p.ArmProfileAmount<=100:errors.append('Arm profile widening must be between 0 and 100 percent.')
    if not 0<=p.MotorPadBlendRadius<=p.ArmWidth/2:errors.append('Pad transition radius must be between zero and half the arm width.')
    for name in ('BottomEdgeFillet','MidEdgeFillet','TopEdgeFillet','ClampEdgeFillet','ArmEdgeFillet'):
        if not math.isfinite(getattr(p,name)) or not 0<=getattr(p,name)<=30:errors.append(name+' must be between zero and 30 mm.')
    from .bottom_nose import edge_settings,CAMERA_FRONT_SHAPES,camera_recess_width
    if not math.isfinite(p.TopFrontClearance) or p.TopFrontClearance<0:errors.append('Top front camera clearance must be finite and non-negative.')
    if p.TopFrontShape!='Straight':
        rear,front=top_bounds(p)
        camera_front=p.TopFrontShape in CAMERA_FRONT_SHAPES
        setback=p.TopFrontSetback if camera_front else 0.
        if not math.isfinite(p.TopFrontDepth) or not math.isfinite(setback) or p.TopFrontDepth<=0 or setback<0 or p.TopFrontDepth+setback>(front-rear)/2:
            errors.append('Top front depth must be positive, shoulder setback non-negative, and their sum at most half the plate length.')
        if camera_front:
            width=camera_recess_width(p)
            if not math.isfinite(p.TopFrontRecessWidth) or p.TopFrontRecessWidth<0 or not math.isfinite(width) or width<=0 or width>=max(p.TopWidth,p.TopCentreWidth)-2*p.MinimumWeb:
                errors.append('Camera recess width must be positive (or zero for automatic) and leave side material inside the top plate. Reduce its width or widen the plate.')
        elif not math.isfinite(p.TopFrontTipWidth) or not 10<=p.TopFrontTipWidth<=90:errors.append('Top front feature width must be between 10 and 90 percent.')
    from .bottom_nose import edge_settings
    for role,bounds_fn in (('BottomPlate',bottom_bounds),('MidPlate',mid_bounds),('TopPlate',top_bounds)):
        shape,depth,tip=edge_settings(p,role,'Rear')
        if shape!='Straight':
            bounds=bounds_fn(p)
            if not math.isfinite(depth) or not 0<depth<=(bounds[1]-bounds[0])/2:errors.append(role+' rear shaping depth must be positive and at most half the plate length.')
            if not math.isfinite(tip) or not 10<=tip<=90:errors.append(role+' rear feature width must be between 10 and 90 percent.')
    for f in fields(p):
        if f.name in DESIGN_OPTIONS:continue
        if f.name in ('MotorMass','PropMass','FCMass','ESCMass','VTXMass','CameraMass','OtherMass','ScrewMassScale'):
            if getattr(p,f.name)<0 or not math.isfinite(getattr(p,f.name)):errors.append(f.name+' must be finite and non-negative.')
            continue
        if f.name in BATTERY_FIELDS or f.name in ('StandoffDensity','ShowFrameCG'):continue
        if f.name in ('MotorHoleRotation','MotorPadRotation'):continue
        if f.name=='RearArmExtension':continue
        if f.name in ROOT_BOLT_COORDINATES or f.name in ('ArmRootWidth','ArmRootLength'):continue
        if f.name=='RootBoltSpacing' and p.RootBoltLayout!='Along arm':continue
        if f.name=='ArmRootTaperLength' and not widened_roots(p):continue
        if f.name=='ArmJointClearance':continue
        if f.name in ('KeystoneWidth','KeystoneLength') and not (fitted_roots(p) and keystone_active(p)):continue
        if f.name.startswith('MotorTip') and not extended_motor_pad(p):continue
        if f.name in ('MotorTipSlotWidth','MotorTipSlotLength') and (not p.MotorTipSlotEnabled or p.MotorPadShape in NEW_MOTOR_PAD_SHAPES):continue
        if f.name=='MotorTipLength':continue
        if f.name in CENTRE_WIDTH_FIELDS.values() or f.name=='CentreSectionY':continue
        if f.name in ('CentreSectionLength','CentreShoulderLength') and not any(getattr(p,n)>0 for n in CENTRE_WIDTH_FIELDS.values()):continue
        if f.name.startswith('KeystoneRetainer') and not keystone_retainers(p):continue
        if p.StrapCount=='1 strap' and f.name=='StrapOffsetY':continue
        if p.StrapOpeningStyle=='Outline cutouts' and f.name in ('StrapSlotWidth','StrapEdgeInset'):continue
        if (not p.StrapSlotsEnabled or p.StrapOpeningStyle=='None') and f.name.startswith('Strap'):
            continue
        if not p.FPVEnabled and f.name in FPV_FIELDS:
            continue
        if f.name in STRINGS or f.name in ENUMERATIONS or f.name in BOOLEANS or f.name in ("StackOffsetY", "RequiredPropGap", "BottomFrontExtension",
                                               "StandoffPair3Y", "StandoffPair4Y", "FPVEnabled", "CameraTilt",
                                               "CameraSideClearance", "CameraSideBoltSpacing", "VTXOffsetY", 'CameraTiltMin', 'CameraTiltMax'):
            continue
        if f.name in ('CameraTabClearance','CameraMountHoleDiameter','TopFrontClearance','KeystoneClearance','StackMountHeight','CameraBaseFrontExtension','CameraBaseRearExtension','CameraTopRearOffset'):
            continue
        if f.name=='CameraTabCutterDiameter' and not p.CameraTabReliefs:continue
        if f.name=='StackAccessDiameter' and not (three_plate(p) or arm_braces(p) or p.ArmRootReliefsEnabled):
            continue
        if f.name=='UndersideClampThickness' and not underside_clamp_active(p):continue
        if f.name=='ArmBraceThickness' and not upper_clamp_active(p):
            continue
        if f.name=='CameraPivotHeight' and p.CameraPivotMode==CAMERA_PIVOT_MODES[0]:
            continue
        if f.name=='CameraMountY' and p.CameraPositionMode=='Automatic centre':continue
        if f.name in ('StandoffWidth','StandoffLength') and p.StandoffFrontMount!='Custom position' and p.StandoffRearMount!='Custom position':
            continue
        if f.name in ('StandoffPair3Width','StandoffPair4Width') and getattr(p,'StandoffPair'+f.name[12]+'Mount')!='Custom position':
            continue
        if f.name.startswith("StandoffPair") and int(f.name[12]) > standoff_pair_count(p):
            continue
        if not three_plate(p) and f.name in ("ClampThickness", "MidFrontReach", "MidRearReach",'BottomBodyRearReach'):
            continue
        if getattr(p, f.name) <= 0:
            errors.append(f"{f.name} must be greater than zero.")
    if not math.isfinite(p.CameraForeAftOffset) or not -100<=p.CameraForeAftOffset<=100:errors.append('Camera fore/aft offset must be between -100 and 100 mm.')
    if p.BottomFrontExtension < 0:
        errors.append("Bottom front extension cannot be negative.")
    if p.ArmRootWidth < 0 or 0 < p.ArmRootWidth < p.ArmWidth:
        errors.append('Arm root width must be zero (follow arm width) or at least the arm width.')
    if widened_roots(p) and p.ArmRootLength < 0:
        errors.append('Wide root length cannot be negative.')
    for role,name in CENTRE_WIDTH_FIELDS.items():
        value=getattr(p,name);base=p.TopWidth if role=='TopPlate' else p.BodyWidth
        if value<0 or value and value<base:
            errors.append(name+' must be zero (off) or at least the plate base width.')
    if keystone_active(p) and not 0 <= p.KeystoneClearance <= .5:
        errors.append('Keystone clearance must be between 0 and 0.5 mm per mating edge.')
    if fitted_roots(p) and not 0 <= p.ArmJointClearance <= 1:
        errors.append('Arm joint clearance must be between 0 and 1 mm across the complete joint.')
    if fitted_roots(p) and keystone_active(p) and p.KeystoneWidth>0 and p.KeystoneLength>0:
        if p.KeystoneWidth*p.KeystoneLength/(2*math.hypot(p.KeystoneWidth,p.KeystoneLength)) < p.MinimumWeb:
            errors.append('The compact keystone is too narrow; increase its width or length.')
    for r in keystone_retainers(p):
        if r['head_diameter']<=r['bore'] or r['countersink_depth']>=p.ArmBraceThickness:
            errors.append('The combined clamp must be thicker than the 90° keystone-retainer countersink depth; adjust clamp thickness or retainer diameters.')
    if p.RequiredPropGap < 0:
        errors.append("RequiredPropGap cannot be negative.")
    if not 100 <= p.Wheelbase <= 700:
        errors.append("Wheelbase must be between 100 and 700 mm.")
    if not 0 <= p.RearArmExtension <= 300:
        errors.append('Rear arm extension must be between 0 and 300 mm.')
    if not 0.65 <= p.LengthToWidth <= 1.8 or not 1.0 <= p.FrontSpread <= 1.8:
        errors.append("Length/width must be 0.65–1.8; front spread must be 1.0–1.8.")
    if p.CornerRadius >= min(p.BodyWidth, p.BodyLength, p.TopWidth, p.TopLength) / 2:
        errors.append("Corner radius must be less than half the smallest plate dimension.")
    if three_plate(p) and p.CornerRadius >= (p.MidFrontReach + p.MidRearReach) / 2:
        errors.append("Mid plate body is too short for the corner radius.")
    if not 0 < p.RootInset < min(arm_root_x(p,True),arm_root_x(p,False))+p.RootInset:
        errors.append("Root inset must be positive and less than half the local bottom width at both arm-root positions.")
    if p.StrapSlotsEnabled and p.StrapOpeningStyle=="Slots" and p.StrapSlotLength <= p.StrapSlotWidth:
        errors.append("Strap slots must be longer than their width.")
    if (three_plate(p) or arm_braces(p)) and p.StackAccessDiameter<p.StackHoleDiameter:
        errors.append('Bottom stack access holes must be at least as large as the stack mounting holes.')
    if p.StackMountHeight<0:
        errors.append('Stack spacer height cannot be negative.')
    for mode,front,rear in ((p.BottomReachMode,p.BottomFrontReach,p.BottomRearReach),
                            (p.TopReachMode,p.TopFrontReach,p.TopRearReach)):
        if mode=='Custom' and front+rear<=2*p.CornerRadius:
            errors.append('Custom plate reaches are too short for the corner radius.')
    if p.StandoffDiameter <= p.StandoffHoleDiameter:
        errors.append("Standoff outside diameter must exceed its bore.")
    if errors:
        return errors, warnings
    if p.Layout=='Deadcat' and (motor_centres(p)[0][1]<=0 or motor_centres(p)[2][1]>=0):
        return ['Deadcat spread moves the front motors behind the centre; reduce front spread or increase the length/width ratio or wheelbase.'],warnings
    arms = arm_layouts(p)
    if prop_gap(p) < -1e-6:
        errors.append(f"Propellers overlap by {-prop_gap(p):.2f} mm. Increase wheelbase or reduce prop diameter.")
    elif prop_gap(p) < p.RequiredPropGap:
        warnings.append(f"Minimum prop gap is {prop_gap(p):.2f} mm, below the requested {p.RequiredPropGap:.2f} mm.")
    if any(math.dist(*arm['bolts']) < p.RootHoleDiameter+p.MinimumWeb-1e-6 for arm in arms):
        errors.append("Arm root bolts leave insufficient material between holes.")
    for arm in arms:
        if any(stem_interior_distance(p,arm,bolt) < p.RootHoleDiameter/2+p.MinimumWeb-1e-6 for bolt in arm['bolts']):
            errors.append(arm['name']+': arm bolts need more material at the root edge; widen or lengthen the root, or move the bolts inward.')
        if p.MotorPadRotationPivot=='Pad beginning' and math.dist(arm['root'],arm['beam_end'])<p.ArmWidth:
            errors.append('Motor pad beginning is too close to the arm root; increase arm reach or reduce pad size.')
        if widened_roots(p) and p.ArmRootLength+p.ArmRootTaperLength > math.dist(arm['root'],arm.get('nominal_motor',arm['motor']))-motor_pad_bound(p)-p.MinimumWeb:
            errors.append(arm['name']+': the root taper reaches the motor pad; reduce the wide root length or taper length.')
    if p.RootBoltLayout=='Along arm' and p.RootExtension < p.RootBoltSpacing / 2:
        errors.append("Root extension must be at least half the root bolt spacing.")
    motor_edge = min(motor_pad_interior(pt,p) for pt in motor_hole_offsets(p))-p.MotorHoleDiameter/2
    if motor_edge < p.MinimumWeb:
        errors.append(f"Motor pad leaves only {motor_edge:.2f} mm outside the bolt holes; enlarge the pad.")
    centre_gap = min(math.hypot(*pt) for pt in motor_hole_offsets(p)) - (p.MotorCenterDiameter + p.MotorHoleDiameter) / 2
    if centre_gap < p.MinimumWeb:
        errors.append("Motor centre bore is too large for the bolt pattern.")
    if min(math.dist(a,b) for a,b in combinations(motor_hole_offsets(p),2)) - p.MotorHoleDiameter < p.MinimumWeb:
        errors.append("Motor bolt holes are too close together.")
    if p.MotorPadDiameter < p.ArmWidth:
        errors.append("Motor pad diameter must be at least the arm width.")
    if motor_corner_control(p):
        if not 0<p.MotorPadCornerRadius<p.MotorPadDiameter/2:
            errors.append('Motor pad corner, chamfer or scallop radius must be between zero and half the pad width.')
    if extended_motor_pad(p) and p.MotorTipLength<0:
        errors.append('Motor tip extension cannot be negative.')
    if p.MotorPadShape in NEW_MOTOR_PAD_SHAPES and p.MotorPadNeckLength<0:errors.append('Motor pad neck length cannot be negative.')
    if p.MotorPadShape in NEW_MOTOR_PAD_SHAPES and p.MotorPadRelief!='None':
        if p.MotorPadReliefWidth<=0 or p.MotorPadReliefLength<=0:errors.append('Pad cutout dimensions must be positive.')
        if p.MotorPadRelief!='Twin neck holes' and p.MotorPadReliefLength<p.MotorPadReliefWidth:errors.append('Pad cutout slot length must be at least its width.')
    if p.MotorPadShape not in NEW_MOTOR_PAD_SHAPES and motor_tip_slots(p) and p.MotorTipSlotLength<p.MotorTipSlotWidth:
        errors.append('Motor tip slot length must be at least its width.')
    for a,b,radius in motor_tip_slots(p):
        if min(motor_pad_interior(pt,p) for pt in (a,b))<radius+p.MinimumWeb-1e-6:
            errors.append('The motor tip slot needs more material at the outline; lengthen the tip or reduce the slot size.')
        bores=[((x,y),p.MotorHoleDiameter/2) for x,y in motor_hole_offsets(p)]+[((0.,0.),p.MotorCenterDiameter/2)]
        if any(point_segment_distance(pt,a,b)<radius+r+p.MinimumWeb-1e-6 for pt,r in bores):
            errors.append('The motor tip slot is too close to a mounting hole or centre bore; extend the tip or reduce the slot size.')
    if p.ArmBeamShape!='Straight' and p.ArmProfileAmount>0 and any(not beam_profile_polygon(p,a) for a in arm_layouts(p)):
        errors.append('No free beam length for the selected arm profile; shorten the root shoulder or increase arm length.')
    body_holes = plate_holes(p,'BottomPlate')
    for pt, radius, name in body_holes:
        if bottom_interior_distance(pt, p) < radius + p.MinimumWeb:
            errors.append(f"A {name} hole is too close to the bottom plate edge.")
    for (a, ra, na), (b, rb, nb) in combinations(body_holes, 2):
        if {na,nb}=={'standoff','arm root'} and math.dist(a,b)<=ALIGNMENT_TOL:
            if abs(ra-rb)>ALIGNMENT_TOL:
                errors.append('A shared arm/standoff mount needs matching arm-hole and standoff-bore diameters.')
            continue
        if math.dist(a, b) < ra + rb + p.MinimumWeb - 1e-6:
            errors.append(f"{na.capitalize()} and {nb} holes leave insufficient material between them.")
    if three_plate(p):
        bottom_rear, bottom_front = bottom_bounds(p)
        body_rear,body_front=bottom_body_bounds(p)
        if body_rear<bottom_rear-1e-6:
            errors.append('Bottom body reach behind stack exceeds the custom bottom rear limit; increase that limit or reduce the body reach.')
        if body_front-body_rear<=2*p.CornerRadius:
            errors.append('The bottom body is too short for its corner radius; increase its reach.')
        for a,b,radius in bottom_tabs(p):
            overlap=max(profiled_interior_distance(pt,p,'BottomPlate',p.BodyWidth,body_rear,body_front,p.CornerRadius) for pt in (a,b))+radius
            if overlap<p.MinimumWeb:
                errors.append('The bottom body does not connect firmly to its rear arm tabs; increase Bottom body reach behind stack.')
        mid_rear, mid_front = mid_bounds(p)
        for a, b, radius in mid_tabs(p):
            overlap = max(profiled_interior_distance(pt,p,'MidPlate',p.BodyWidth,mid_rear,mid_front,p.CornerRadius)
                          for pt in (a, b)) + radius
            if overlap < p.MinimumWeb:
                errors.append("The mid body does not connect firmly to its front arm tabs; increase its front reach.")
        mid_points = {stand["point"] for stand in standoff_layouts(p) if stand["mount"] == "Mid plate"}
        mid_holes = plate_holes(p,'MidPlate')
        for pt, radius, name in mid_holes:
            if mid_interior_distance(pt, p) < radius + p.MinimumWeb - 1e-6:
                errors.append(f"A {name} hole has insufficient material in the mid plate; increase its reach or adjust the mount.")
        for stand in standoff_layouts(p):
            pt = stand["point"]
            if stand["mount"] == "Bottom plate":
                if -mid_interior_distance(pt, p) < p.StandoffDiameter / 2 + p.MinimumWeb:
                    errors.append(stand["position"] + ": the mid plate or an arm tab intersects a bottom-mounted standoff; adjust its position or mid reach.")
            elif mid_interior_distance(pt, p) < p.StandoffDiameter / 2 + p.MinimumWeb:
                errors.append(stand["position"] + ": a standoff needs more supporting material on the mid plate.")
    if arm_braces(p):
        for pt in tuple(pt for a in arms for pt in a['bolts'])+stack_holes(p):
            radius=p.StackHoleDiameter/2 if pt in stack_holes(p) else p.RootHoleDiameter/2
            if arm_clamp_interior_distance(pt,p)<radius+p.MinimumWeb-1e-6:
                errors.append('The combined clamp needs more material around an arm or stack hole; adjust the mounting pattern or body width.')
        for stand in standoff_layouts(p):
            inside=arm_clamp_interior_distance(stand['point'],p)
            if stand['mount']=='Arm clamp plate' and inside<p.StandoffDiameter/2+p.MinimumWeb-1e-6:
                errors.append('A standoff is too close to the combined clamp edge; reposition the pair.')
            elif upper_clamp_active(p) and stand['mount']=='Bottom plate' and -inside<p.StandoffDiameter/2+.25:
                errors.append('A bottom-mounted standoff intersects the combined clamp edge; reposition the pair.')
        if underside_clamp_active(p):
            lower_holes=plate_holes(p,'ArmLowerClampPlate')
            for pt,radius,name in lower_holes:
                if arm_clamp_interior_distance(pt,p)<radius+p.MinimumWeb-1e-6:errors.append('A '+name+' hole needs more material at the lower capture plate edge.')
            for (a,ra,na),(b,rb,nb) in combinations(lower_holes,2):
                if {na,nb}=={'standoff','arm root'} and math.dist(a,b)<=ALIGNMENT_TOL:continue
                if math.dist(a,b)<ra+rb+p.MinimumWeb-1e-6:errors.append('Lower capture '+na+' and '+nb+' holes leave insufficient material between them.')
    for a, b in combinations(standoff_holes(p), 2):
        if math.dist(a, b) < p.StandoffDiameter + p.MinimumWeb - 1e-6:
            errors.append("Standoffs are too close together; adjust pair positions or left–right spacing.")
    for stand in standoff_layouts(p):
        pt=stand['point']
        if stand['mount']=='Bottom plate' and bottom_interior_distance(pt, p) < p.StandoffDiameter / 2 + p.MinimumWeb:
            errors.append("A standoff needs more supporting material on the bottom plate.")
        if top_interior_distance(pt,p) < p.StandoffDiameter / 2 + p.MinimumWeb:
            errors.append("A standoff is too close to the top plate edge.")
    if any(s['length']<=0 for s in standoff_layouts(p)):
        errors.append('A standoff has no room above its arm mounting surface; increase the rear standoff height.')
    if arms_above_bottom(p) and not three_plate(p):
        arm_top=p.BottomThickness+p.ArmThickness+(p.ArmBraceThickness if arm_braces(p) else 0)
        if plate_levels(p)['top_z']<arm_top+.2:
            errors.append('The top plate does not clear the arms and braces above the bottom; increase standoff height.')
    if not math.isfinite(p.StrapSingleY):errors.append('Single strap position must be finite.')
    from .strap_openings import validate_notches
    errors.extend(validate_notches(p))
    if p.DetailedStackReference and (not math.isfinite(p.StackUSBOffsetY) or abs(p.StackUSBOffsetY)>p.StackSpacing/2-7.5):
        errors.append('FC USB offset must keep the connector clear of the corner grommets (maximum '+str(p.StackSpacing/2-7.5)+' mm).')
    slots = strap_slots(p)
    for a, b, radius in slots:
        if min(top_interior_distance(pt,p) for pt in (a,b)) < radius + p.MinimumWeb:
            errors.append("A strap slot is too close to the top plate edge.")
        for pt in standoff_holes(p):
            if point_segment_distance(pt, a, b) < radius + p.StandoffDiameter / 2 + p.MinimumWeb:
                errors.append("A strap slot is too close to a standoff mounting footprint.")
    for role,inside,plate_name in (('BottomPlate',bottom_interior_distance,'bottom'),('TopPlate',top_interior_distance,'top')):
        layer_slots=camera_slots(p,role)
        for a,b,radius in layer_slots:
            if min(inside(pt,p) for pt in (a,b))<radius+p.MinimumWeb-1e-6:
                errors.append('A camera tab slot needs more material in the '+plate_name+' plate.')
            for pt in standoff_holes(p):
                if point_segment_distance(pt,a,b)<radius+p.StandoffDiameter/2+p.MinimumWeb:errors.append('A camera tab slot is too close to a standoff.')
            for pt,hole_radius,name in (body_holes if role=='BottomPlate' else plate_holes(p,'TopPlate')):
                if point_segment_distance(pt,a,b)<radius+hole_radius+p.MinimumWeb:errors.append('A camera tab slot is too close to a '+name+' hole.')
            for c,d,r in (slots if role=='TopPlate' else ()):
                if segment_distance(a,b,c,d)<radius+r+p.MinimumWeb:errors.append('A camera tab slot is too close to a strap slot.')
        for (a,b,ra),(c,d,rb) in combinations(layer_slots,2):
            if segment_distance(a,b,c,d)<ra+rb+p.MinimumWeb-1e-6:errors.append('Camera tab slots overlap or leave insufficient material; increase side plate length or reduce tab length/clearance.')
    for (a, b, r1), (c, d, r2) in combinations(slots, 2):
        if segment_distance(a, b, c, d) < r1 + r2 + p.MinimumWeb:
            errors.append("Strap slots overlap or leave insufficient material between them.")
    hardware = [(pt, bottom_stack_hole_diameter(p) / 2, "stack access passage" if three_plate(p) or arm_braces(p) else 'stack bolt', .25)
                for pt in stack_holes(p)]
    hardware += [(pt, p.CameraMountHoleDiameter/2, "camera mount bolt", .25) for pt in camera_holes(p)]
    hardware += [(pt, radius, "VTX bolt", .25) for pt, radius, _ in vtx_holes(p)]
    hardware += [(stand["point"], (p.StandoffDiameter if three_plate(p) and stand["mount"] == "Bottom plate"
                                  else p.StandoffHoleDiameter) / 2, "standoff or its bolt",
                  0 if three_plate(p) and stand["mount"] == "Bottom plate" else .25)
                 for stand in standoff_layouts(p)]
    for arm in arms:
        if arm["length"] < p.MotorPadDiameter:
            errors.append("A motor is too close to its arm root.")
        if fitted_roots(p):
            planes=root_joint_planes(p,arm,arms)
            for bolt in arm['bolts']:
                if any(limit-n[0]*bolt[0]-n[1]*bolt[1] < p.RootHoleDiameter/2+p.MinimumWeb-1e-6 for n,limit in planes):
                    errors.append(arm['name']+': a fitted joint cuts into arm-bolt support; move the roots outward, reduce bolt spacing or reduce the joint clearance.')
                if keystone_active(p) and -polygon_interior_distance(bolt,compact_key_outline(p,arms,True)) < p.RootHoleDiameter/2+p.MinimumWeb-1e-6:
                    errors.append(arm['name']+': the compact keystone pocket cuts into arm-bolt support; reduce the key size or move the roots outward.')
        for pt, radius, name, clearance in hardware:
            if p.ArmRootReliefsEnabled and (name=='stack access passage' or name=='stack bolt' and not arms_above_bottom(p)):
                # Matching reliefs are cut through any arm material beneath
                # the separate stack carrier, preserving the access tunnel.
                continue
            shared=shared_arm_root(p,pt) if name=='standoff or its bolt' else None
            if shared and shared['arm']==arm['name'] and abs(p.StandoffHoleDiameter-p.RootHoleDiameter)<=ALIGNMENT_TOL:
                continue
            if fitted_roots(p):
                if any(limit-n[0]*pt[0]-n[1]*pt[1] <= -radius-clearance for n,limit in root_joint_planes(p,arm,arms)):
                    continue
                if keystone_active(p) and polygon_interior_distance(pt,compact_key_outline(p,arms,True)) >= radius+clearance:
                    continue
            gap = min(-stem_interior_distance(p,arm,pt),
                      math.dist(pt, arm["motor"]) - motor_pad_bound(p)) - radius
            if gap < clearance:
                errors.append(f"An arm intersects a {name}; change root position or mounting pattern.")
    for a, b in combinations(arms, 2):
        if fitted_roots(p) or widened_roots(p):continue  # CAD checks the final trimmed/tapered solids.
        gap = min(segment_distance(a["start"], a["motor"], b["start"], b["motor"]) - p.ArmWidth,
                  point_segment_distance(a["motor"], b["start"], b["motor"]) - motor_pad_bound(p)-p.ArmWidth/2,
                  point_segment_distance(b["motor"], a["start"], a["motor"]) - motor_pad_bound(p)-p.ArmWidth/2,
                  math.dist(a["motor"], b["motor"]) - 2*motor_pad_bound(p))
        if gap < 0.25:
            errors.append("Replaceable arms intersect; shorten root extensions or move the arm roots apart.")
    thicknesses = (p.BottomThickness, p.TopThickness) + ((p.ClampThickness,) if three_plate(p) else ())
    if min(thicknesses) < 1.5:
        warnings.append("At least one plate is thinner than 1.5 mm.")
    if p.ArmThickness < 4 and p.PropDiameter >= 120:
        warnings.append("Arm thickness is below 4 mm for a 5-inch-or-larger propeller.")
    if p.StandoffHeight < 20:
        warnings.append("Check electronics and connector clearance in the selected stack height.")
    if stack_reference_z(p)+p.StackHeight>plate_levels(p)['top_z']-.2:
        warnings.append('The stack envelope exceeds the space under the top plate; fit taller standoffs or check the configured stack/spacer height.')
    if p.Layout == "Deadcat":
        warnings.append("Deadcat geometry spreads the front motors; camera field-of-view clearance still needs checking.")
    errors.extend(validate_fpv(p, standoff_layouts(p)))
    return tuple(dict.fromkeys(errors)), tuple(warnings)


def validate(p):
    errors,warnings=_validation_result(p)
    return list(errors),list(warnings)


from functools import lru_cache as _validation_cache

@_validation_cache(maxsize=16)
def _checked_parameters(signature):
    errors,warnings=validate(Parameters(*signature))
    if errors:raise ValueError("\n".join(errors))
    return tuple(warnings)

def require_valid(p):
    return list(_checked_parameters(p.signature()))


def save_parameters(path, p):
    require_valid(p)
    with open(path, "w", encoding="utf-8") as stream:
        json.dump({"schema": SCHEMA, "units": "mm", "parameters": p.to_dict()}, stream, indent=2, allow_nan=False)
        stream.write("\n")


def load_parameters(path):
    with open(path, encoding="utf-8") as stream:
        data = json.load(stream)
    return parameters_from_settings(data)


def parameters_from_settings(data):
    """Validate an already decoded settings file, including legacy migration."""
    if not isinstance(data, dict) or data.get("schema") not in SUPPORTED_SCHEMAS or data.get("units") != "mm":
        raise ValueError("Expected RotorForge settings with millimetre units.")
    p = Parameters.from_dict(data.get("parameters"))
    require_valid(p)
    return p
