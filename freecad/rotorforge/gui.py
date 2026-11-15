"""Qt editor with a fast top-view preview; imports only inside GUI FreeCAD."""
from dataclasses import fields, replace
import math
import os
import re

import FreeCAD as App
import FreeCADGui as Gui
try:
    from PySide import QtCore, QtGui, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
    except ImportError:
        from PySide6 import QtCore, QtGui, QtWidgets

from .battery import BATTERY_FIELDS,battery_point,groove_segments
from .part_preview import preview_roles,draw_parts,pad_path
from .paths import help_path, icon_path
from .motor_sizes import MOTOR_SIZES,apply_motor_size
from .appearance import CARBON_HEX,CARBON_EDGE,PAD_HEX,printed_hex,PRINTED_COLOURS,design_signature,carbon_brush
from .prop_palette import prop_swatch
from . import __version__
from .editor_sections import SECTIONS, FIELD_LOCATION, FIELD_ORDER, HIDDEN_FIELDS
from .airflow_gui import arm_stack_access_path
from .parameters import (Parameters, ENUMERATIONS, BOOLEANS, STRINGS, VENT_ROW_COUNTS, arm_layouts, motor_centres,
                         stack_holes, standoff_holes, strap_slots, validate,
                         prop_gap, save_parameters, parameters_from_settings, three_plate,
                         bottom_bounds, bottom_body_bounds, top_bounds, mid_bounds, mid_tabs, standoff_heights, standoff_pairs,
                         standoff_pair_count, standoff_layouts, COMMON_STANDOFF_HEIGHTS,
                         arms_above_bottom, arm_braces, arm_brace_layouts, bottom_stack_hole_diameter,
                         plate_levels, stack_reference_z, stack_mounting_role)
from .parameters import keystone_active, keystone_retainers, upper_clamp_active, underside_clamp_active
from .parameters import frame_bolt_offsets,STACK_PATTERNS,stack_label
from .document import (ICON, FLOATS, read_parameters, create_frame, update_frame,
                        find_parameters, GEOMETRY_FIELDS, ARM_FIELDS, MOTOR_FIELDS)
from .fpv import (FPV_FIELDS, CAMERA_WIDTHS, camera_mounts, camera_slots, camera_pivot_height,
                  camera_cage_height, camera_vertical_limits, camera_body_centre, vtx_holes)
from .fpv import camera_position_y, camera_attachment_lengths
from .airflow_gui import finished_part_path, AirflowEditor, motor_pad_path, cutout_path, profile_path, arm_blank_path, keystone_path, mid_plate_path, bottom_plate_path, combined_cutout_path
from .cutouts import parse_patterns, pattern_instances
from .view import view_front
from .motor_pads import extended_motor_pad, motor_tip_slots, motor_corner_control
from .arm_roots import fitted_roots, compact_key_centre, widened_roots, root_width, ROOT_BOLT_COORDINATES

LABELS = {
    'CarbonTextureEnabled': 'Show carbon-fiber weave texture',
    'CarbonTextureTile': 'Weave texture repeat (mm)',
    'CarbonTextureOpacity': 'Carbon weave opacity',
    'BatteryReferenceEnabled':'Show LiPo reference',
    'BatteryPreset':'LiPo size preset',
    'BatteryCells':'Cell count (S)',
    'BatteryWidth':'Battery width',
    'BatteryLength':'Battery length',
    'BatteryHeight':'Battery height',
    'BatteryMass':'Battery reference mass',
    'KeystoneShape':'Compact key outline', 'EstimateComponents':'Include equipment estimates',
    'MotorMass':'Motor mass (each)', 'PropMass':'Propeller mass (each)',
    'FCMass':'Flight controller mass', 'ESCMass':'4-in-1 ESC mass',
    'VTXMass':'VTX mass', 'CameraMass':'Camera mass',
    'OtherMass':'Other equipment / wiring allowance', 'ScrewMassScale':'Screw mass multiplier',
    'BatteryMount':'Battery mounting face',
    'BatteryX':'Battery / pad X offset',
    'BatteryY':'Battery / pad Y offset',
    'BatteryRotation':'Battery / pad rotation',
    'LiPoPadEnabled':'Create LiPo pad',
    'LiPoPadOutlineWidthScale':'Plate outline width scale',
    'LiPoPadOutlineLengthScale':'Legacy pad length scale',
    'LiPoPadFrontReach':'Pad front reach from stack (0 = full)',
    'LiPoPadRearReach':'Pad rear reach from stack (0 = full)',
    'LiPoPadWidth':'Pad width',
    'LiPoPadLength':'Pad length',
    'LiPoPadThickness':'Pad thickness',
    'LiPoPadShape':'Pad outline',
    'LiPoPadCornerRadius':'Pad corner radius',
    'LiPoPadFollowPlate':'Follow mounting plate',
    'LiPoPadCopyAirflow':'Copy airflow cuts to LiPo pad',
    'LiPoPadPattern':'Grip surface',
    'LiPoPadGrooveWidth':'Groove width',
    'LiPoPadGrooveDepth':'Groove depth',
    'LiPoPadGroovePitch':'Groove spacing',
    'LiPoPadDensity':'Pad material density',
    'StandoffDensity':'Standoff material density',
    'ShowFrameCG':'Show estimated CG marker',

    'MotorPadRotation':'Motor pad rotation (mirrored)',
    'MotorHoleRotation':'Motor hole rotation',
    'MotorPadRotationPivot':'Motor pad rotation pivot', 'MotorHoleLayout':'Motor mounting pattern', 'MotorBoltCircle':'Motor bolt circle diameter',
    'MotorReferenceDiameter':'Motor reference bell diameter', 'MotorReferenceHeight':'Motor reference body height',
    'PropReferenceHeight':'Prop plane above motor mounting face',

    'ArmRootReliefShape':'Arm stack relief shape',
    'RearArmExtension':'Deadcat rear arm extension',
    'ArmRootWidth':'Arm root width (0 = follow arm)', 'ArmRootLength':'Wide root length toward motor',
    'ArmRootTaperLength':'Root taper length', 'RootBoltLayout':'Arm bolt placement',
    'ArmBoltMaterialAllowance':'Extra material around arm bolts',
    'RootBolt1X':'Bolt 1 X offset', 'RootBolt1Y':'Bolt 1 Y offset',
    'RootBolt2X':'Bolt 2 X offset', 'RootBolt2Y':'Bolt 2 Y offset',
    'ArmRootFit':'Arm root fit', 'ArmJointClearance':'Arm joint clearance',
    'KeystoneWidth':'Compact keystone width', 'KeystoneLength':'Compact keystone length',
    'ArmRootReliefsEnabled':'Relieve arm roots for stack access', 'UndersideClampThickness':'Lower clamp thickness',
    'CameraTiltMechanism':'Variable tilt mechanism', 'CameraPositionMode':'Camera fore/aft placement',
    'CameraFollowPlates':'Side plates follow actual plate ends', 'CameraPlateY':'Preferred side-plate centre Y',
    'CameraTopRearOffset':'Upper attachment rearward offset',
    'CameraBaseMode':'Lower attachment sizing',
    'CameraBaseFrontExtension':'Lower attachment front extension',
    'CameraBaseRearExtension':'Lower attachment rear extension',
    'BottomCentreWidth':'Bottom centre width (0 = off)', 'MidCentreWidth':'Mid centre width (0 = off)',
    'TopCentreWidth':'Top centre width (0 = off)', 'ClampCentreWidth':'Clamp centre width (0 = off)',
    'CentreSectionLength':'Full-width centre length', 'CentreShoulderLength':'Taper length at each end',
    'CentreSectionY':'Centre section position Y', 'ArmRootsFollowCentre':'Arm roots follow wider bottom centre',
    'KeystoneRetainerDiameter':'Key retainer through-hole diameter', 'KeystoneRetainerHeadDiameter':'Key retainer countersink diameter',
    'KeystoneRetainerSpacing':'Key retainer fore/aft spacing',
    'CameraMountMode':'Camera tilt mount', 'CameraTiltMin':'Minimum adjustable tilt', 'CameraTiltMax':'Maximum adjustable tilt',
    'BottomReachMode':'Bottom plate reach', 'BottomFrontReach':'Bottom reach toward front (+Y)',
    'BottomRearReach':'Bottom outer rear limit (frame Y=0)', 'BottomBodyRearReach':'Bottom body reach behind stack', 'MidReachMode':'Mid plate reach',
    'TopReachMode':'Top plate reach', 'TopFrontReach':'Top reach toward front (+Y)', 'TopRearReach':'Top reach toward rear (−Y)',
    'MotorPadShape':'Motor pad outline', 'MotorPadDiameter':'Motor pad overall width', 'MotorPadCornerRadius':'Motor corner / chamfer / scallop size',
    'MotorTipLength':'Motor tip extension', 'MotorTipSlotEnabled':'Enable motor tip slot',
    'MotorTipSlotWidth':'Motor tip slot width', 'MotorTipSlotLength':'Motor tip slot total length',
    'TwoPlateArmPosition':'Arm position (2 plates)', 'ArmBracesEnabled':'Arm clamp plate (2 plates)',
    'ArmBraceThickness':'Upper clamp thickness', 'KeystoneEnabled':'Arm locking keystone',
    'KeystoneClearance':'Keystone clearance per mating edge',
    'ArmRootFillet':'Arm root corner fillet', 'KeystoneFillet':'Keystone corner fillet',
    "FPVEnabled": "FPV camera drone", "VideoSystem": "Video system",
    "CameraWidth": "Camera body width", "CameraHeight": "Camera body height",
    "CameraTPUHardClearance": "Hard-mount side clearance",
    "CameraBodyDepth": "Camera body depth (without lens)", "CameraSideClearance": "Extra width clearance (total)",
    "CameraSideHoleDiameter": "Camera side screw hole diameter", "CameraSideBoltSpacing": "Vertical screw spacing (0 = pivot)",
    "CameraPhysicalProfile":"Physical camera model", "CameraSideScrewRearInset":"Side screw from rear face (mm)", "CameraLensProjection":"Lens projection (0 = auto)",
    "CameraMountY": "Custom camera centre Y", "CameraPivotHeight": "Custom camera centre height above bottom",
    "CameraPivotMode":"Camera height placement", "CameraPlateLength":"Cage minimum length",
    "CameraTabLength":"Tab length along frame", "CameraTabClearance":"Tab clearance per side",
    "CameraTilt": "Camera uptilt", "CameraBracketThickness": "Cage wall thickness",
    'CameraViewProfile':'Camera view lens profile',
    'CameraViewAspect':'Camera view aspect ratio',
    'CameraViewFOV':'Diagonal FOV override (0 = automatic)',
    'CameraViewPupilOffset':'Optical offset forward of casing (0 = automatic)', 
    "CameraMountHoleDiameter": "Bracket base hole diameter", "VTXPattern": "Rear VTX mounting pattern",
    "VTXOffsetY": "VTX centre position Y", "VTX20HoleDiameter": "20 × 20 hole diameter",
    "VTX25HoleDiameter": "25.5 × 25.5 hole diameter", "VTXWidth": "VTX envelope width",
    "VTXLength": "VTX envelope length", "VTXHeight": "VTX envelope height",
    "Layout": "Motor layout", "Wheelbase": "Diagonal wheelbase", "LengthToWidth": "Length / rear width",
    "FrontSpread": "Front / rear motor span", "PropDiameter": "Propeller diameter", "RequiredPropGap": "Desired prop gap",
    "PlateDesign": "Plate design", "BodyLength": "Bottom base length", "BodyWidth": "Bottom / mid base width", "TopLength": "Top plate length",
    "ClampThickness": "Mid plate thickness", "BottomFrontExtension": "Bottom front extension (3 plates)",
    "MidFrontReach": "Mid body reach ahead of stack", "MidRearReach": "Mid body reach behind stack",
    "TopWidth": "Top base width", "ArmRootY": "Arm root distance from centre", "RootInset": "Root inset from local bottom edge",
    "RootExtension": "Arm tail behind root centre", "RootBoltSpacing": "Arm root bolt spacing",
    "StackSpacing": "FC stack mounting pattern", "StackHoleDiameter": "Stack hole diameter",
    'StackAccessDiameter':'Stack screw access diameter', 'StackHeight':'FC / ESC stack envelope height',
    'StackMountHeight':'Stack spacer height', 'StrapSlotsEnabled':'Enable battery strap openings',
    "MotorSpacingX": "Motor hole spacing along arm", "MotorSpacingY": "Motor hole spacing across arm",
    "MotorCenterDiameter": "Motor centre bore", "StandoffWidth": "Outer pairs left–right spacing",
    "StandoffLength": "Outer pairs front–rear spacing", "StandoffHeight": "Rear standoff height",
    "StandoffCount": "Number of standoffs",
    "StandoffFrontMount":"Front pair position", "StandoffRearMount":"Rear pair position",
    "StandoffPair3Mount":"Pair 3 position mode", "StandoffPair4Mount":"Pair 4 position mode",
    "StandoffPair3Y": "Pair 3 position Y", "StandoffPair3Width": "Pair 3 left–right spacing",
    "StandoffPair4Y": "Pair 4 position Y", "StandoffPair4Width": "Pair 4 left–right spacing",
    "StandoffDiameter": "Standoff outside diameter", "StandoffHoleDiameter": "Standoff through-hole diameter",
    "StrapOffsetY": "Slot centre distance from centre", "StrapEdgeInset": "Slot inset from top plate edge",
    "CarbonDensity": "Carbon density estimate", "MinimumWeb": "Minimum material around holes",
    "ShowReferences": "Show prop / motor / stack references",
}
TIPS = {
    'CarbonTextureOpacity': 'Strength of the visible weave over the opaque carbon finish. 0% shows solid carbon; 100% shows the full plain weave. The carbon parts never become transparent.',
    'CarbonTextureTile': 'Physical repeat size of the plain weave in mm. Each arm automatically aligns its weave with the root-to-motor axis, while frame plates stay aligned with the fuselage.',
    'CameraViewProfile': 'Automatically follows FPV > Camera when a camera is selected. You can override the virtual lens manually here; choosing another physical camera restores automatic lens, aspect and FOV. Physical geometry is unchanged.',
    'CameraViewAspect': 'Preview image aspect ratio. Switching aspect cannot recreate proprietary camera crops or stabilization.',
    'CameraViewFOV': 'Measured maximum DIAGONAL FOV in degrees. Zero uses the optical profile. Use your exact camera mode/lens measurement for better results.',
    'CameraViewPupilOffset': 'Lens entrance pupil in mm forward from camera housing front. 0 estimates it from the physical camera lens projection (near the front element, not just 3 mm out). This is NOT a certified optical pupil location.',

    'BatteryReferenceEnabled':'Show the selected LiPo pack reference when Show references is enabled. This is a visual fit reference, not a manufactured frame component.',
    'BatteryPreset':'Choose a typical 3S–8S pack to fill in nominal dimensions, mass and cell count. Select Custom dimensions to retain individual measurements. Published battery dimensions vary by manufacturer.',
    'BatteryCells':'Actual number of cells in series (3–8). Controls the illustrated cell layers and balance connector contacts; does not change battery dimensions or mass automatically.',
    'BatteryWidth':'Measured pack width, including protective wrap. Changing this switches the preset to Custom dimensions while retaining the selected cell count.',
    'BatteryLength':'Measured pack length along the local Y axis, before pack rotation. The visual power leads are decorative and not included in this measurement.',
    'BatteryHeight':'Measured total pack thickness. The reference sits on the selected mounting surface or LiPo pad; the detailed cell layers are scaled to this height.',
    'KeystoneShape':'Outline of the compact fitted-miter key and its matching arm pockets. Independent roots retain automatic arm seats; switch Root joints to Fitted miters to choose a compact outline.',
    'EstimateComponents':'Include editable nominal motors, props, FC, ESC, FPV camera/VTX and automatically counted steel screws. The CG marker uses the equipped estimate, plus battery when enabled.',
    'MotorMass':'Mass of one motor including its wires. Default 30.5 g represents a 2207 motor; change for your actual motor size.',
    'PropMass':'Mass of one propeller. Default 4 g is a planning allowance for a 5-inch prop; change for your props.',
    'FCMass':'One FC mass, default 10.5 g. Located at three quarters of the stack envelope height.',
    'ESCMass':'One 4-in-1 ESC mass, default 23.5 g. Located at one quarter of the stack envelope height.',
    'VTXMass':'One VTX mass, default 10 g nominal allowance. Included only in FPV mode; edit for analog or digital hardware.',
    'CameraMass':'One camera mass, default 10 g nominal allowance. Uses the camera body centre and is included only in FPV mode.',
    'OtherMass':'Allowance for cables, antennas, receiver, nuts, spacers and straps. Default 15 g, placed at the stack centre. Set zero or enter your weighed allowance.',
    'ScrewMassScale':'Multiplier for automatically counted steel screw masses. Thread diameter and grip length follow the frame geometry, plus estimated engagement. Default 1; zero excludes screw mass. Not a screw purchase specification.',
    'BatteryMass':'Actual battery weight in grams used for frame-plus-battery and loaded CG estimates. Preset values are illustrative: weigh your real pack for accurate results.',
    'BatteryMount':'Top plate places the pad and battery above the top carbon face. Bottom plate places them below the bottom carbon face, keeping the pad between plate and pack.',
    'BatteryX':'Shared left/right placement of the battery and pad in frame coordinates; positive X is right. The frame carbon remains fixed.',
    'BatteryY':'Shared front/rear placement of the battery and pad in frame coordinates; positive Y is forward.',
    'BatteryRotation':'Rotate the battery footprint and pad together around their shared centre in the frame XY plane. Zero places the longer local dimension along frame Y; positive turns counterclockwise in top view.',
    'LiPoPadEnabled':'Create one separate pad solid, not carbon. It is included in the native assembly and assembled STEP, and exported separately as flat STL/STEP and an ungrooved DXF/SVG outline.',
    'LiPoPadOutlineWidthScale':'Width of the plate-following pad as a percentage of the carrier outline. 100% keeps full width; 80% makes it narrower about the carrier centre. Actual carrier holes remain aligned. Used only with Mounting plate outline.',
    'LiPoPadFrontReach':'Distance in mm forward from the FC stack centre (frame +Y). Zero keeps the full carrier front. A shorter reach makes a straight transverse front edge; width still follows the plate. Standoff centres keep a 6 mm clear radius.',
    'LiPoPadRearReach':'Distance in mm rearward from the FC stack centre (frame -Y). Zero keeps the full carrier rear. Adjust independently from the front; shorter reaches cut a straight rear edge.',
    'LiPoPadOutlineLengthScale':'Legacy value retained for old-document migration. Length of the plate-following pad as a percentage of the carrier outline. Independent from width. 100% keeps full length. Shrinks about the carrier centre; holes and cutouts stay in their real positions.',
    'LiPoPadWidth':'Width of an independent pad before carrier clipping. With Mounting plate outline this is unused; use width scale for the outline. Grip patterns always cover the finished pad automatically.',
    'LiPoPadLength':'Length of an independent pad before carrier clipping. With Mounting plate outline this is unused; use front/rear reaches. Grip patterns always cover the finished pad automatically.',
    'LiPoPadThickness':'Overall pad thickness. Grooves cut into the battery-facing surface and must leave a continuous backing. This height also lifts or lowers the battery reference away from the carbon face.',
    'LiPoPadShape':'Choose rounded rectangle, rectangle, capsule, ellipse, chamfered rectangle, tapered or hourglass. Mounting plate outline follows the top or bottom plate, retaining mandatory mounting/strap openings; the Copy airflow cuts option decides whether it also inherits airflow openings. Use Plate outline width scale and independent front/rear reaches from the stack. Ends are cut straight when shortened; all pads leave a 6 mm clear radius around standoff centres. Grip patterns cover the finished pad automatically; battery pose does not move a plate-following pad or its grip pattern.',
    'LiPoPadCornerRadius':'Corner radius for Rounded rectangle. Zero makes square corners; positive values must be smaller than half the shorter pad dimension. Use Capsule for fully rounded ends.',
    'LiPoPadFollowPlate':'Clip an independent pad to the mounting plate. For an outline-following pad the carrier is always used. The separate airflow option controls whether the pad copies air openings. CAD rejects empty or disconnected pads.',
    'LiPoPadCopyAirflow':'When enabled, the LiPo pad inherits the mounting carbon plate’s airflow through-cuts and outline notches (where they intersect the pad). When disabled, the pad bridges these openings but retains mounting holes and strap access. Carbon additions remain in the pad boundary. With the option enabled, blind pocket outlines may also become through-holes in the pad, so inspect the finished solid. This changes the actual printable solid only on Create / Update, not the live 2-D editor. Existing designs default to enabled to preserve their shape.',
    'LiPoPadPattern':'Choose from 25 grip surfaces, including dots, staggered dots, dashes, basket weave, hexagon cells and waves as well as the existing groove layouts. Every non-solid pattern repeats over the entire finished pad and is clipped to its outline and clearance openings. Width, depth and spacing remain adjustable; the backing stays continuous.',
    'LiPoPadGrooveWidth':'Channel width, or dot diameter for the dimple patterns. All features are shallow recesses.',
    'LiPoPadGrooveDepth':'Depth into the battery-facing surface. Must be smaller than pad thickness so the backing stays continuous.',
    'LiPoPadGroovePitch':'Pattern spacing: row/grid pitch for grooves and dots, base pitch for weave (tile is twice this), hexagon radius for cells, ring inset for rectangular rings. Waves have this row spacing and a wavelength six times this value. Must exceed feature width. Increase it if the finished pattern exceeds 512 segments.',
    'LiPoPadDensity':'Density used to convert exact pad volume into its mass estimate. Default 1.2 g/cm3 is a nominal solid TPU value. Enter the actual material/effective printed density; infill and adhesive are not modelled.',
    'StandoffDensity':'Density used for the modelled hollow standoff tubes. Default 2.7 g/cm3 is nominal aluminium. Screw/nut and strap masses are not included.',
    'ShowFrameCG':'Show a red CG cross when references are visible. Uses loaded CG when equipment and battery estimates are enabled, equipped CG without a battery, or bare-frame CG with equipment estimates off. Readouts are independent from marker visibility.',

    'MotorPadRotationPivot':'Motor centre keeps the motor fixed. Pad beginning pivots at the root-facing extent of the unrotated pad. The motor, holes and references move together; a full-width elbow links the arm to the pad.',
    'MotorPadRotation':'Rotates the complete motor pad, fixing holes and tip slots about the selected pivot. Relative to each arm, the front-right and rear-left use the entered angle; front-left and rear-right use the opposite angle. This mirrors pad orientation across the frame. Pad beginning mode moves motor and prop centres. Motor hole rotation remains an additional local bolt-circle adjustment.',
    'MotorHoleRotation':'Rotates the 3-hole or 4-hole bolt-circle pattern about each motor centre, relative to that pad. Zero puts one hole toward the outward arm tip. Positive angles turn counterclockwise when viewed from above. The pad outline and centre bore do not rotate.',
    'ArmRootReliefShape':'Round hole keeps the existing stack-screw relief. Slot toward stack centre opens each intersecting relief inward toward the actual stack centre (including Stack Offset Y), allowing the arm to slide away from the screw. Slot width follows Stack screw access diameter. CAD checks reject cuts into arm-bolt support or disconnected arms.',
    'RearArmExtension':'Deadcat only: extra length added to each rear arm along its existing root-to-motor direction. Front motors and arm roots stay fixed. Zero keeps the original layout. Actual motor diagonals and rear span increase beyond the base layout.',
    'ArmRootWidth':'Width of the root before joint trimming. Zero follows Arm width. A larger value widens only the root and tapers back into the beam; fitted joints and keystone pockets still trim this material.',
    'ArmRootLength':'Distance from the arm root reference centre toward the motor before the wider root begins to taper. The tail behind the reference centre uses Arm tail behind root centre.',
    'ArmRootTaperLength':'Length of the transition from the wider root to the ordinary arm beam. The transition must finish before the motor pad.',
    'RootBoltLayout':'Along arm uses the centred pair and Arm root bolt spacing. Custom coordinates uses independent frame-aligned X/Y offsets from each root reference centre. The front-right reference pattern is mirrored across the frame.',
    'RootBolt1X':'Frame X offset for bolt 1 on the front-right arm: + right, - left, relative to the root reference centre. Mirrored on the left arms. Shared inner-hole standoffs follow bolt 1.',
    'RootBolt1Y':'Frame Y offset for bolt 1 on the front-right arm: + front, - rear, relative to the root reference centre. Mirrored on the rear arms. Changing Y leaves X unchanged.',
    'RootBolt2X':'Frame X offset for bolt 2 on the front-right arm: + right, - left, relative to the root reference centre. Mirrored on the left arms. Shared outer-hole standoffs follow bolt 2.',
    'RootBolt2Y':'Frame Y offset for bolt 2 on the front-right arm: + front, - rear, relative to the root reference centre. Mirrored on the rear arms. Changing Y leaves X unchanged.',
    'ArmRootFit':'Independent keeps the rounded tails. Fitted miters trim the roots along shared joint lines, allowing them to meet without overlapping. Root centres, mounting holes and motor positions stay where you set them.',
    'ArmJointClearance':'Complete gap between neighbouring fitted arms. Zero gives nominal contact where the tails reach each other; use a small positive gap for your cutting process. Increase the tail extension if the roots do not yet meet.',
    'KeystoneWidth':'Full left/right width of the compact diamond key with Fitted miters. Its matching pocket is cut from the arms. Move roots inward and extend their tails so all four arms reach the key; bolt support is checked.',
    'KeystoneLength':'Full front/rear length of the compact key with Fitted miters. It follows the junction of the root joints and uses the same stock thickness as the arms.',
    'UndersideClampThickness':'Thickness of the single clamp beneath below-bottom arms, with or without a keystone. Arm bolts clamp it against the bottom plate; stack service holes give access to the stack screws in the bottom plate.',
    'ArmRootReliefsEnabled':'Relieve arm material crossing stack screws. Choose a round hole or a slot opening toward the stack centre below. Width follows Stack screw access diameter on Hardware > Stack. Disable to keep uninterrupted roots. CAD checks protect arm-bolt support and connected material.',
    'CameraTiltMechanism':'Vertically stacked side screws use centred upper/lower arc slots. The alternative fixes the upper screw and moves the lower screw along an exact arc. Enter the measured vertical pitch.',
    'CameraPositionMode':'Centre the camera on the actual side plates at its configured height, or choose a custom camera centre Y. Height can be centred or set independently.',
    'CameraFollowPlates':'Fit upper and lower tongues independently inside the actual plate outlines and away from fasteners. A shorter top plate produces sloping side walls. Custom reaches remain exact.',
    'CameraPlateY':'Preferred cage centre, before fitting the separate upper/lower attachments to the actual plate ends. Camera position within the cage is controlled independently.',
    'CameraTopRearOffset':'Move only the upper camera-plate contact and its top-plate sockets rearward (frame -Y) by this distance after the existing fit. Zero preserves the original shape. Lower contact, camera position and tilt settings remain unchanged. Excessive offsets are rejected if support or screw/slot material is lost.',
    'CameraBaseMode':'Automatic uses the fitted side-plate length at both heights. Custom adds independent front/rear length only to the lower edge resting on the bottom plate, including matching tongue positions and receiving slots.',
    'CameraBaseFrontExtension':'Extra contact length toward the nose (+Y), beyond the normal lower edge, in Custom sizing. The top attachment length stays the same. Automatic bottom reach grows when needed; Custom plate reaches stay exact.',
    'CameraBaseRearExtension':'Extra contact length toward the stack (−Y), beyond the normal lower edge, in Custom sizing. The bottom attachment refits around fasteners; check the live fit. Automatic camera placement follows the resulting cage.',
    'BottomCentreWidth':'Zero keeps the base width. A larger value widens only the middle stack/arm section, with tapered shoulders. Front/rear reach stays exact.',
    'MidCentreWidth':'Independent centre widening for the mid body. The integrated front arm tabs still follow the actual roots.',
    'TopCentreWidth':'Independent centre widening for the top. Camera and rear sections retain their normal width outside the taper.',
    'ClampCentreWidth':'Independent centre widening for the active upper or lower arm clamp in two-plate designs.',
    'CentreSectionLength':'Length of the full-width region shared by the plate centre profiles. Each plate is clipped to its own front/rear reach.',
    'CentreShoulderLength':'Length of each sloping transition from the normal plate width to its widened centre.',
    'CentreSectionY':'Position of the widened section, measured from frame centre. Positive is front.',
    'ArmRootsFollowCentre':'When enabled, the arm root inset is measured from the local widened bottom edge. Disable to retain the original arm-root spacing. Deadcat compensation follows the actual roots.',
    'CameraMountMode':'Variable uses a single-screw friction pivot, or a vertical screw pair in upper/lower arc slots. Fixed uses two vertically spaced round holes at the chosen uptilt.',
    'CameraTiltMin':'Lowest intended adjustable angle. Clearance is checked across the configured range. Single-screw pivots rely on friction and have no mechanical end stops.',
    'CameraTiltMax':'Highest intended adjustable angle. Two-screw mounts have arc-slot end stops. Fit camera height after changing the range.',
    'BottomRearReach':'Maximum rearward extent of the bottom plate in Custom mode. In three-plate designs the rear tabs follow the arms, including fitted joints and keystone pockets; extending this limit does not add a full-width rear deck.',
    'BottomBodyRearReach':'Three-plate main-body distance behind the FC stack centre. Rear edge Y = Stack Offset Y minus this reach. Increase it to fill more of the centre between the rear arm tabs; decrease it to shorten the body. Tabs still follow the arms beyond that edge. Mounting support is checked.',
    'BottomReachMode':'Automatic computes the outer limits. Bottom body reach behind stack independently controls the three-plate body edge. Rear clamping tabs follow the actual rear arm-root outlines. Custom front/rear reaches cap the outline without automatic growth; two-plate bottoms keep their full profile.',
    'MidReachMode':'Automatic can extend the mid rear deck to support the VTX. Custom uses the exact front/rear reaches measured from the stack centre.',
    'TopReachMode':'Automatic covers the camera and rear VTX. Custom uses the exact independent reaches from frame centre; insufficient coverage is reported.',
    'MotorPadShape':'Choose from the supported motor-pad profiles. The experimental Scalloped racer and Swept hook were retired because their silhouettes were incompatible with reliable TPU motor protection and tip sleeves. Older presets map to Crown shield and Swept-shoulder shield with a warning.',
    'MotorPadCornerRadius':'Corner radius for Rounded square; chamfer for Chamfered square, Shouldered and Tapered nose/Arrowhead. Scalloped shield uses this size for its three edge reliefs; the twelve shield variations use it to adjust scallop depth. Inactive for Round, Four-lobe, Teardrop and Compact hex.',
    'MotorTipLength':'Extra outward nose reach for Tapered nose, Arrowhead and the ten additional pad families. Replacement platforms use the separate neck-length control. Pad-beginning rotation can move the motor centre.',
    'MotorTipSlotEnabled':'Cut a separate rounded relief slot near the end of a Tapered nose or Arrowhead. It does not replace motor screw holes; airflow settings are independent.',
    'MotorTipSlotWidth':'Width of the optional tip relief. Keep the configured material around the outside edge, motor screws and centre bore.',
    'MotorTipSlotLength':'Complete end-to-end length, including the semicircular ends. The slot sits one quarter of the extension beyond the normal pad front; increase the extension if the cut leaves too little material.',
    'TwoPlateArmPosition':'Choose arms below the bottom plate or above it, inside the frame. Shared standoffs sit above the complete arm sandwich.',
    'ArmBracesEnabled':'Create one arm clamp opposite the bottom plate: above the arms when they are above the bottom, or beneath the arms when they are below. The lower clamp is independent of the optional keystone. The FC stack mounts on the upper clamp or, with below-bottom arms, on the bottom plate.',
    'ArmBraceThickness':'Thickness of the upper arm clamp / FC deck when arms are above the bottom plate. Below-bottom arms use Lower clamp thickness instead; both values remain saved.',
    'StackAccessDiameter':'Default 6 mm service openings beneath the FC carrier: in the lower clamp for below-bottom arms, or in the bottom beneath an upper clamp or mid. The carrier keeps normal mounting holes. Matching arm and keystone reliefs preserve screw access.',
    'StackHeight':'Approximate assembled FC/ESC height above its spacers. Check actual connectors and components; the reference is excluded from manufacturing exports.',
    'StackMountHeight':'Spacer height above the supporting plate when FC stack press nuts are disabled. With press nuts enabled, the stack starts directly on the exposed flange; this manual value is ignored.',
    'StrapSlotsEnabled':'Enable top-plate strap openings in the selected style. Disable to omit them while retaining all settings.',
    'KeystoneEnabled':'Add a four-seat key in the arm layer. Bottom and mid capture it in three-plate designs. In two-plate designs, the bottom and the single active upper or lower clamp capture it with the eight arm bolts.',
    'KeystoneClearance':'Lateral gap between the key and each arm seat. Zero gives nominal contact; allow a suitable fit for your cutting process.',
    "FPVEnabled": "Add camera side plates captured by tabs in the bottom and top, plus rear VTX holes. The nose and rear decks extend to support them.",
    "VideoSystem": "Analog and digital cameras can share widths. Select the actual width, body dimensions and screw pattern below; this label does not force one camera model.",
    "CameraWidth": "Actual camera width between side faces. Common-size shortcuts set body height, centre the camera and choose taller stock standoffs if necessary.",
    "CameraPivotMode":'Centre the nominal body and mounting pattern halfway between bottom/top, or set a custom height. Fit camera height raises the standoffs when needed.',
    "CameraTabClearance":"Per-side clearance between the camera plate tongues and the matching rounded slots. The top plate captures the upper tongues when bolted down.",
    "CameraBodyDepth": "Housing depth (not including lens barrel). Real camera housing dimensions are used for collision checks; detailed visual appearance does not change mounting fit.",
    "CameraSideBoltSpacing":'Vertical centre-to-centre spacing on one camera side. Foxeer T-Rex Mini uses 6.3 mm; Caddx Ratel Pro has one screw per side (0 mm spacing).',
    "CameraSideScrewRearInset":'Custom camera: enter the measured M2 thread position from the REAR of the housing (not lens); positive mm. 0 keeps legacy centred mounting for existing presets. Hole position affects physical plate slots, TPU inserts, camera tilt and detailed thread markers. Unpublished positions in named presets are estimates.',
    "CameraLensProjection":'Length of lens assembly protruding beyond the camera housing front. Foxeer T-Rex Mini is approximately 10.5 mm; Caddx Ratel Pro approximately 14.3 mm based on the supplied drawing.',
    "CameraPhysicalProfile":'Select physical analog or digital camera dimensions (including DJI O4 Pro, Walksnail and HDZero). Generic camera sizes are estimates. Use Custom for your own measured rear-to-screw inset. Each model automatically selects its optical preview.',
    "CameraMountY":'Custom nominal body centre Y (+Y front). With an upper pivot this is the centre at the middle of the variable range. Automatic centres it on the actual side plates.',
    "CameraTilt": "Displayed camera angle. In Variable mode it must be inside the adjustment range; changing the preview angle does not change the bracket or arc slots.",
    "VTXPattern": "Select 20 × 20, 25.5 × 25.5, or both centred patterns. Both makes eight holes; fit one set of four VTX screws.",
    "VTXOffsetY": "Negative Y is rear. Keep the VTX behind the stack and standoffs; the lower mounting deck extends to support it.",
    "VTX20HoleDiameter": "Clearance-hole diameter, independent of spacing. 2.2 mm for M2 or 3.2 mm for M3; match your VTX fasteners.",
    "VTX25HoleDiameter": "Clearance-hole diameter, independent of spacing. Default 2.2 mm for M2. Check material between nested patterns when choosing both.",
    "PlateDesign": "Two plates: choose arms above/below the bottom and one optional clamp on the opposite side of the arms. The upper clamp carries the FC stack; below-bottom arms keep the FC stack on the bottom. Three plates: arms between bottom and mid, with an optional captured keystone.",
    "BodyLength": "Automatic base length before the front extension. Three-plate bottoms are trimmed behind the rear arm sandwich; use Custom for exact independent reaches.",
    "BottomFrontExtension": "Extra bottom length toward +Y in three-plate mode. Its rear edge does not move. Ignored in two-plate mode.",
    "MidFrontReach": "Front reach of the main stack deck. Its front arm-clamping tabs follow the actual arm-root outlines, including width, fitted joints and key pockets, within the bottom support.",
    "MidRearReach": "Main mid plate extends this far rearward from the stack centre. Independent of bottom plate length.",
    "Wheelbase": "Base distance between diagonally opposite motor centres, not the carbon outside size. A Deadcat rear arm extension increases the actual diagonal; the summary shows the resulting distance.",
    "LengthToWidth": "Squashed X: left–right motor span divided by front–rear spacing. Deadcat: length divided by rear span. Ignored for True X.",
    "FrontSpread": "Deadcat only: front/rear motor span ratio of the base layout. Automatic rear reach compensates for front spread. Extra rear arm extension is applied afterwards, increasing the final rear span and actual diagonals.",
    "PropDiameter": "Full propeller diameter: 5 inch = 127 mm; 5.1 inch = 129.54 mm; 7 inch = 177.8 mm.",
    "ArmRootY": "The front/rear arm root reference centres sit at +Y and -Y of this distance. Moving custom bolts does not move these references or the motors.",
    "RootInset": "Horizontal distance from the bottom plate side edge to each arm root centre.",
    "RootExtension": "Untrimmed tail reach behind the midpoint of the two root bolts. Fitted miters trim it at the joint lines and compact key pocket. Increase it until the required seats meet.",
    "RootBoltSpacing": "Two bolts per arm. Three plates: bottom/arm/mid sandwich. Two plates: arms above or below the bottom, with the optional combined clamp on the same bolts.",
    'ArmBoltMaterialAllowance':'Extra radial material (0–6 mm) around arm fixing holes. This adjusts the arm stock, not the receiving plate press-nut/hex-nut support radius. Mid/Bottom receiving tabs keep their original structural footprint as the adjustable arm bolt stock grows, so the nut pads do not chase the arm. Bolt and nut centres and hole sizes do not move. 0 mm preserves the original stock. Check screw access and nearby cutouts before manufacture.',
    "StackSpacing": "Choose 20 x 20 mm or 30.5 x 30.5 mm. The square hole spacing is fixed by this choice; stack height, mounting spacers and hole diameter remain editable.",
    "StackHoleDiameter": "30.5 mm stacks often use M3; some 20 mm / 25.5 mm stacks use M2. Match your hardware.",
    "MotorSpacingX": "Legacy pad-lobe spacing retained for older outlines.",
    "StandoffCount": "Choose 4, 6, or 8 standoffs in 2, 3, or 4 mirrored left/right pairs. Extra pair positions are adjustable below.",
    "StandoffFrontMount":"Custom uses the spacing fields. Arm-hole choices snap this pair exactly onto the front arm bolt centres and follow geometry changes. In three plates these standoffs sit on the mid arm tabs.",
    "StandoffRearMount":"Custom uses the spacing fields. Arm-hole choices snap this pair exactly onto rear arm bolt centres. Shared holes require matching diameters and supporting material.",
    "StandoffPair3Mount":"Choose a custom pair position or snap it to a front/rear arm inner/outer bolt pair. Near misses and incompatible diameters are rejected.",
    "StandoffPair4Mount":"Choose a custom pair position or snap it to a front/rear arm inner/outer bolt pair. Near misses and incompatible diameters are rejected.",
    "StandoffPair3Y": "Extra pair centre along Y: negative is rear, positive is front. Keep it between the outer pairs. Its mounting plate determines its length.",
    "StandoffPair4Y": "Extra pair centre along Y: negative is rear, positive is front. Keep it between the outer pairs. Its mounting plate determines its length.",
    "StandoffHeight": "Actual rear pair length. Other pairs are linked to keep the top level. Pairs on the mid or combined clamp have different bases from pairs on the bottom. Lengths follow the actual support and keep the top level.",
    "CarbonDensity": "Used only to estimate carbon mass. Hardware, electronics, tolerances, and coatings are excluded.",
    "MinimumWeb": "Geometric edge / hole spacing check. This does not predict structural strength.",
    "ShowReferences": "Reference volumes are approximate and are excluded from manufacturing exports.",
}


def label(name):
    return LABELS.get(name, re.sub(r"(?<!^)(?=[A-Z])", " ", name))


def tab_name(name):
    return FIELD_LOCATION[name][1] if name in FIELD_LOCATION else None


def standoff_size_row(spin):
    """Keep the numeric field for custom sizes and offer common-size shortcuts."""
    row = QtWidgets.QWidget()
    layout = QtWidgets.QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    choices = QtWidgets.QComboBox()
    choices.addItem("Custom", None)
    for height in COMMON_STANDOFF_HEIGHTS:
        choices.addItem(f"{height:g} mm", height)
    choices.setToolTip("Choose a common size or enter any custom length in the numeric field.")
    layout.addWidget(spin, 1)
    layout.addWidget(choices)
    def sync(value):
        index = next((i for i in range(1, choices.count()) if abs(choices.itemData(i) - value) < .005), 0)
        choices.blockSignals(True)
        choices.setCurrentIndex(index)
        choices.blockSignals(False)
    def choose(index):
        if index > 0:
            spin.setValue(choices.itemData(index))
    choices.currentIndexChanged.connect(choose)
    spin.valueChanged.connect(sync)
    return row, choices, sync


def camera_spacing_row(spin):
    row=QtWidgets.QWidget();layout=QtWidgets.QHBoxLayout(row);layout.setContentsMargins(0,0,0,0)
    choices=QtWidgets.QComboBox()
    for title,value in (('Custom',None),('Vertical pair 6.5 mm',6.5),('Single pivot',0.)):
        choices.addItem(title,value)
    choices.setToolTip('Vertical pitch on one camera side. Camera body width is a separate setting.')
    layout.addWidget(spin,1);layout.addWidget(choices)
    def sync(value):
        index=next((i for i in range(1,choices.count()) if abs(choices.itemData(i)-value)<.005),0)
        choices.blockSignals(True);choices.setCurrentIndex(index);choices.blockSignals(False)
    def choose(index):
        value=choices.itemData(index)
        if value is not None:spin.setValue(value)
    choices.currentIndexChanged.connect(choose);spin.valueChanged.connect(sync)
    return row,choices,sync


def camera_size_row(spin, editor):
    row=QtWidgets.QWidget()
    layout=QtWidgets.QHBoxLayout(row); layout.setContentsMargins(0,0,0,0)
    choices=QtWidgets.QComboBox(); choices.addItem('Custom',None)
    for title,width in CAMERA_WIDTHS: choices.addItem(title,width)
    layout.addWidget(spin,1); layout.addWidget(choices)
    def sync(width):
        index=next((i for i in range(1,choices.count()) if abs(choices.itemData(i)-width)<.005),0)
        choices.blockSignals(True); choices.setCurrentIndex(index); choices.blockSignals(False)
    def choose(index):
        width=choices.itemData(index)
        if width is None: return
        spin.setValue(width)
        editor.controls['CameraHeight'].setValue(width)
        p=editor.values()
        editor.fit_camera()
    choices.currentIndexChanged.connect(choose)
    return row,choices,sync


from .design_options import OPTIONS as DESIGN_OPTIONS
from .flex_options import FLEX_OPTIONS
DESIGN_OPTIONS={**DESIGN_OPTIONS,**FLEX_OPTIONS}
LABELS.update({k:v[1] for k,v in DESIGN_OPTIONS.items()})
TIPS.update({k:v[2] for k,v in DESIGN_OPTIONS.items()})
TIPS['PropReferenceHeight']='Height of simple prop discs above the arm. Detailed three-blade props instead seat their 6 mm hubs directly on the motor bells.'
TIPS['MotorReferenceHeight']='Motor bell body height above the arm. Detailed motor shafts and self-locking nuts extend above this height.'

class TopPreview(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.params = Parameters()
        self.view_mode = 'Overall'
        self.mass_metrics = None
        self.last_error = None
        self.zoom = 1.0
        self.pan = QtCore.QPointF()
        self._drag = None
        self.setToolTip('Scroll to zoom around the pointer. Drag to pan. Double-click or Fit view to reset.')
        self.setMinimumSize(320, 180)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def reset_view(self):
        self.zoom = 1.0
        self.pan = QtCore.QPointF()
        self.update()

    def zoom_at(self, point, factor):
        new_zoom = max(0.25, min(20.0, self.zoom * factor))
        ratio = new_zoom / self.zoom
        self.pan = point - (point - self.pan) * ratio
        self.zoom = new_zoom
        self.update()

    def wheelEvent(self, event):
        point = event.position() if hasattr(event, 'position') else QtCore.QPointF(event.pos())
        self.zoom_at(point, 1.2 ** (event.angleDelta().y() / 120.0))
        event.accept()

    def mousePressEvent(self, event):
        if event.button() in (QtCore.Qt.LeftButton, QtCore.Qt.MiddleButton):
            self._drag = event.position() if hasattr(event, 'position') else QtCore.QPointF(event.pos())
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag is not None:
            point = event.position() if hasattr(event, 'position') else QtCore.QPointF(event.pos())
            self.pan += point - self._drag
            self._drag = point
            self.update()
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag = None
        self.unsetCursor()

    def mouseDoubleClickEvent(self, event):
        self.reset_view()
        event.accept()

    def paintEvent(self, event):
        # Record vector drawing only when the design, mode or viewport changes.
        # QPicture retains vector detail at every zoom without rebuilding paths.
        # Lens simulation settings do not affect this 2-D frame drawing.
        # Avoid redrawing thousands of Qt paths when changing only optics.
        _not_drawing=('CameraViewProfile','CameraViewAspect','CameraViewFOV','CameraViewPupilOffset')
        key = (tuple(getattr(self.params,n) for n in self.params.__dataclass_fields__
                     if n not in _not_drawing), self.view_mode, self.width(), self.height(),
               repr(self.mass_metrics), self.font().toString())
        if key != getattr(self, '_picture_key', None):
            self._picture = QtGui.QPicture()
            self._record_picture(self._picture)
            self._picture_key = key
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor("#f3f6f8"))
        painter.translate(self.pan)
        painter.scale(self.zoom, self.zoom)
        painter.drawPicture(0, 0, self._picture)
        painter.end()

    def _record_picture(self, picture):
        painter = QtGui.QPainter(picture)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        p = self.params
        self.last_error = None
        try:
            if self.view_mode!='Overall':
                draw_parts(painter,QtCore.QRectF(6,30,self.width()-12,self.height()-60),p,self.view_mode)
                painter.resetTransform()
                painter.setPen(QtGui.QColor('#294554'))
                painter.drawText(QtCore.QRectF(0,5,self.width(),20),QtCore.Qt.AlignCenter,'Part inspection — carbon flats / TPU schematics')
                painter.end();return
            motors, arms = motor_centres(p), arm_layouts(p)
            extent_x = max(abs(x) for x, y in motors) + p.PropDiameter / 2 + 15
            rear, front = bottom_bounds(p)
            extent_y = max(max(abs(y) for x, y in motors) + p.PropDiameter / 2, abs(rear), abs(front), max(abs(v) for v in top_bounds(p))) + 15
            if p.BatteryReferenceEnabled and p.ShowReferences:
                points=[battery_point(p,x,y) for x in (-p.BatteryWidth/2,p.BatteryWidth/2) for y in (-p.BatteryLength/2,p.BatteryLength/2)]
                extent_x=max(extent_x,max(abs(x) for x,y in points)+10)
                extent_y=max(extent_y,max(abs(y) for x,y in points)+10)
            scale = min((self.width() - 20) / (2 * extent_x), (self.height() - 60) / (2 * extent_y))
            painter.save()
            painter.translate(self.width() / 2, self.height() / 2 + 5)
            painter.scale(scale, -scale)
            def ellipse(pt, radius, colour, fill="white", width=0.5):
                painter.setPen(QtGui.QPen(QtGui.QColor(colour), width))
                painter.setBrush(QtGui.QColor(fill))
                painter.drawEllipse(QtCore.QPointF(*pt), radius, radius)
            def capsule(a, b, diameter, colour):
                pen = QtGui.QPen(QtGui.QColor(colour), diameter)
                pen.setCapStyle(QtCore.Qt.RoundCap)
                painter.setPen(pen)
                painter.drawLine(QtCore.QPointF(*a), QtCore.QPointF(*b))
            prop_colour = "#a52e36" if prop_gap(p) < 0 else "#79b7c5"
            for pt in motors:
                ellipse(pt, p.PropDiameter / 2, prop_colour, "#dcecf1")
            bottom_path = bottom_plate_path(p,arms)
            def draw_bottom():
                painter.setPen(QtGui.QPen(QtGui.QColor("#111315"), 0.5))
                painter.setBrush(carbon_brush(p,QtGui,"#414448"))
                painter.drawPath(finished_part_path(p,'BottomPlate') if p.BottomEdgeFillet or p.CutoutPatterns!='[]' else bottom_path)
            if arms_above_bottom(p):
                draw_bottom()
            for arm in arms:
                painter.setPen(QtGui.QPen(QtGui.QColor('#384655'),.5));painter.setBrush(carbon_brush(p,QtGui,role='Arm'+arm['name']))
                painter.drawPath(finished_part_path(p,'Arm'+arm['name']))
                for pt in arm["bolts"]:
                    ellipse(pt, p.RootHoleDiameter / 2, "#202b36")
                for pt in arm["motor_holes"]:
                    ellipse(pt, p.MotorHoleDiameter / 2, "#202b36")
                for a,b,radius in motor_tip_slots(p,arm):capsule(a,b,2*radius,'#202b36')
                ellipse(arm["motor"], p.MotorCenterDiameter / 2, "#202b36")
            if three_plate(p):
                mid_path = mid_plate_path(p,arms)
                painter.setPen(QtGui.QPen(QtGui.QColor("#17191b"), 0.6))
                painter.setBrush(carbon_brush(p,QtGui,"#45484c"))
                painter.drawPath(finished_part_path(p,'MidPlate') if p.MidEdgeFillet or p.CutoutPatterns!='[]' else mid_path)
            elif not arms_above_bottom(p):
                draw_bottom()
            for clamp in arm_brace_layouts(p) if upper_clamp_active(p) else ():
                path=finished_part_path(p,clamp['role'])
                painter.setPen(QtGui.QPen(QtGui.QColor('#17191b'),.6))
                painter.setBrush(carbon_brush(p,QtGui,'#3a3d40'))
                painter.drawPath(path)
            if fitted_roots(p):
                # Show the otherwise hidden joints through the mid/clamp plate.
                painter.save()
                span=max(abs(v) for a in arms for v in a['root'])+root_width(p)
                painter.setClipRect(QtCore.QRectF(-span,-span,2*span,2*span))
                painter.setPen(QtGui.QPen(QtGui.QColor('#384655'),.55,QtCore.Qt.DashLine))
                painter.setBrush(QtCore.Qt.NoBrush)
                for arm in arms:painter.drawPath(finished_part_path(p,'Arm'+arm['name']))
                if keystone_active(p):
                    painter.setPen(QtGui.QPen(QtGui.QColor('#17191b'),.6))
                    painter.setBrush(carbon_brush(p,QtGui,'#35383b'))
                    painter.drawPath(keystone_path(p,arms))
                painter.restore()
            for arm in arms:
                for pt in arm["bolts"]:
                    ellipse(pt, p.RootHoleDiameter / 2, "#202b36")
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtGui.QPen(QtGui.QColor("#657d90"), 0.65, QtCore.Qt.DashLine))
            top_rear,top_front=top_bounds(p)
            top_path=profile_path(p,'TopPlate',p.TopWidth,top_rear,top_front,p.CornerRadius)
            painter.drawPath(finished_part_path(p,'TopPlate') if p.TopEdgeFillet or p.CutoutPatterns!='[]' or (p.StrapSlotsEnabled and p.StrapOpeningStyle=='Outline cutouts') else top_path)
            for pt in stack_holes(p):
                if three_plate(p) or arm_braces(p):
                    ellipse(pt,bottom_stack_hole_diameter(p)/2,'#158652','#e3f5e9')
                ellipse(pt, p.StackHoleDiameter / 2, "#158652", "#b3e6c9")
            for pt in standoff_holes(p):
                ellipse(pt, p.StandoffDiameter / 2, "#b97d27", "#efd09a")
            for a, b, radius in strap_slots(p):
                capsule(a, b, 2 * radius, "#ffffff")
            if p.FPVEnabled:
                painter.setPen(QtGui.QPen(QtGui.QColor(CARBON_EDGE),.6))
                painter.setBrush(QtGui.QColor(printed_hex(p)) if p.CameraCageStyle=='TPU cage' else carbon_brush(p,QtGui))
                if p.CameraCageStyle=='TPU cage':
                    # The preview uses the single connected floor footprint;
                    # do not draw the retired two rectangular carbon-style cheeks.
                    from .cage_preview import front_band_path
                    painter.drawPath(front_band_path(p))
                else:
                    for mount in camera_mounts(p):
                        xmin,xmax=mount['plate_x']
                        rear=min(y for y,z in mount['wall_profile']);front=max(y for y,z in mount['wall_profile'])
                        painter.drawRect(QtCore.QRectF(xmin,rear,xmax-xmin,front-rear))
                painter.setBrush(QtGui.QColor('#546a77'))
                body_y=camera_body_centre(p)[0]
                from .camera_housing import body_top_outline,screw_line_y
                footprint=body_top_outline(p.CameraWidth,p.CameraBodyDepth,p.VideoSystem=='Digital',p.CameraPhysicalProfile,screw_line_y(p.CameraBodyDepth,p.CameraSideScrewRearInset))
                poly=QtGui.QPolygonF([QtCore.QPointF(x,body_y+y) for y,x in footprint])
                painter.drawPolygon(poly)
                ellipse((0,body_y+p.CameraBodyDepth/2+3),(10. if p.FPVSystemProfile=='DJI O4 Air Unit Pro' else min(6,p.CameraWidth*.35)),'#163e50','#7ac4d8')
                for a,b,r in camera_slots(p)+camera_slots(p,'TopPlate'): capsule(a,b,2*r,'#e8fcff')
                painter.setPen(QtGui.QPen(QtGui.QColor('#854c9b'),.6))
                painter.setBrush(QtGui.QColor('#dfc6e6'))
                painter.drawRect(QtCore.QRectF(-p.VTXWidth/2,p.VTXOffsetY-p.VTXLength/2,p.VTXWidth,p.VTXLength))
                for point,radius,_ in vtx_holes(p): ellipse(point,radius,'#854c9b')
            if p.FlexFrontBumper:
                from .bumper_preview import front_bumper_plan
                painter.setPen(QtGui.QPen(QtGui.QColor('#0c0d0e'),.4));painter.setBrush(QtGui.QColor(printed_hex(p)));painter.drawPath(front_bumper_plan(p))
            patterns=parse_patterns(p.CutoutPatterns);drawn_roles=set()
            for pattern in patterns:
                if not pattern['enabled'] or pattern['role'].startswith('Camera'):continue
                if pattern['role']=='MidPlate' and not three_plate(p):continue
                if pattern['role']=='ArmClampPlate' and not upper_clamp_active(p):continue
                if pattern['role']=='ArmKeystone' and not keystone_active(p):continue
                if pattern['role']=='ArmLowerClampPlate' and not underside_clamp_active(p):continue
                painter.setPen(QtGui.QPen(QtGui.QColor('#178a96'),.45));painter.setBrush(QtGui.QColor('#f3f6f8'))
                if pattern['role'] not in drawn_roles:
                    painter.drawPath(combined_cutout_path(patterns,pattern['role']));drawn_roles.add(pattern['role'])
            if p.LiPoPadEnabled:
                painter.setPen(QtGui.QPen(QtGui.QColor('#222b30'),.4));painter.setBrush(QtGui.QColor(printed_hex(p)));painter.drawPath(pad_path(p))
            from .flex_preview import flex_path
            if p.FlexMotorProtectors:
                for a in arm_layouts(p):
                    painter.setPen(QtGui.QPen(QtGui.QColor('#617c7c'),.4));painter.setBrush(QtGui.QColor(printed_hex(p)));painter.drawPath(flex_path(p,'MotorProtector'+a['name']))
            if p.FlexELRSEnabled:
                painter.setPen(QtGui.QPen(QtGui.QColor('#617c7c'),.4));painter.setBrush(QtGui.QColor(printed_hex(p)));painter.drawPath(flex_path(p,'ELRSAntennaMount'))
            if p.FlexRearAntenna:
                painter.setPen(QtGui.QPen(QtGui.QColor('#617c7c'),.4));painter.setBrush(QtGui.QColor(printed_hex(p)));painter.drawPath(flex_path(p,'RearAntennaMount'))
            if p.FlexSideGuards:
                from .protection_layout import guard_layout
                from .flex_preview import guard_plan_path
                for g in guard_layout(p):
                    painter.setPen(QtGui.QPen(QtGui.QColor('#617c7c'),.4));painter.setBrush(QtGui.QColor(printed_hex(p)));painter.drawPath(guard_plan_path(p,g))
            if p.BatteryReferenceEnabled and p.ShowReferences:
                outline=QtGui.QPainterPath();points=[battery_point(p,x,y) for x,y in ((-p.BatteryWidth/2,-p.BatteryLength/2),(p.BatteryWidth/2,-p.BatteryLength/2),(p.BatteryWidth/2,p.BatteryLength/2),(-p.BatteryWidth/2,p.BatteryLength/2))]
                outline.moveTo(*points[0])
                for point in points[1:]:outline.lineTo(*point)
                outline.closeSubpath();painter.setPen(QtGui.QPen(QtGui.QColor('#546a79'),.7));painter.setBrush(QtGui.QColor(85,107,124,75));painter.drawPath(outline)
            if self.mass_metrics and p.ShowFrameCG and p.ShowReferences:
                x,y,z=self.mass_metrics['display_cg_mm'];painter.setPen(QtGui.QPen(QtGui.QColor('#d92332'),.9));painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawEllipse(QtCore.QPointF(x,y),2.5,2.5)
                painter.drawLine(QtCore.QPointF(x-5,y),QtCore.QPointF(x+5,y));painter.drawLine(QtCore.QPointF(x,y-5),QtCore.QPointF(x,y+5))
            painter.restore()
            painter.resetTransform()
            painter.setPen(QtGui.QColor("#3b4c5b"))
            painter.drawText(QtCore.QRectF(0, 8, self.width(), 24), QtCore.Qt.AlignCenter, "FRONT  +Y")
            painter.drawText(QtCore.QRectF(0, self.height() - 27, self.width(), 20), QtCore.Qt.AlignCenter,
                             "Top view • LiPo: slate • CG: red" if p.BatteryReferenceEnabled and p.ShowReferences else
                             "Top view • camera: teal • VTX: purple" if p.FPVEnabled else
                             "Top view • beige: bottom • blue: mid • dashed: top")
        except Exception as exc:
            self.last_error = str(exc)
            # Malformed intermediate input must not disrupt editing.
            painter.end()
            return
        painter.end()





class CameraPreviewLabel(QtWidgets.QLabel):
    """Aspect-preserving camera image that follows the available preview area.

    Resizing the editor scales the cached QPixmap only; the expensive ray
    tracing is still run exclusively when the user requests a new render.
    """
    def __init__(self):
        super().__init__('Click Render camera view to inspect the lens projection.')
        self._source_pixmap = None
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumSize(290, 175)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setStyleSheet('background:#223242; color:#dce8f2; border:1px solid #687988;')

    def sizeHint(self):
        # A pixmap must not force the horizontal editor to be wider than the
        # actual dialog. Unlike QLabel's default, this never grows after render.
        return QtCore.QSize(480, 270)

    def minimumSizeHint(self):
        return QtCore.QSize(290, 175)

    def show_frame(self, pixmap):
        self._source_pixmap = pixmap
        self._fit_frame()

    def _fit_frame(self):
        if self._source_pixmap is not None and not self._source_pixmap.isNull():
            available = self.contentsRect().size()
            if available.width()>1 and available.height()>1:
                super().setPixmap(self._source_pixmap.scaled(
                    available, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_frame()

    def clear(self):
        self._source_pixmap = None
        super().clear()

    def setText(self, text):
        self._source_pixmap = None
        super().setText(text)


class CameraWorkspace(QtWidgets.QWidget):
    """Side-by-side camera controls / image, stacked only on narrow windows."""
    def __init__(self, options, preview):
        super().__init__()
        self.options = options
        self.preview = preview
        self.columns = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight, self)
        self.columns.setContentsMargins(0, 0, 0, 0)
        self.columns.setSpacing(10)
        self.columns.addWidget(options, 2)
        self.columns.addWidget(preview, 3)
        self._reflow()

    def _reflow(self):
        # Do not squeeze the controls and image side-by-side on scaled displays.
        wide = self.width() >= 720
        direction = (QtWidgets.QBoxLayout.LeftToRight if wide else
                     QtWidgets.QBoxLayout.TopToBottom)
        if self.columns.direction() != direction:
            self.columns.setDirection(direction)
        self.options.setMaximumWidth(420 if wide else 16777215)
        self.columns.setStretch(0, 2 if wide else 0)
        self.columns.setStretch(1, 3 if wide else 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow()


class FrameDialog(QtWidgets.QDialog):
    def __init__(self, settings=None):
        super().__init__(Gui.getMainWindow())
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowMaximizeButtonHint)
        self.settings = settings
        self._loaded_hardware_preferences = None
        self.controls = {}
        self.field_labels = {}
        self.setWindowTitle("RotorForge — Drone Frame Editor — " + ("Edit frame" if settings else "New frame"))
        self.resize(1100, 750)
        self.setMinimumSize(950, 650)
        outer = QtWidgets.QVBoxLayout(self)
        settings_files = QtWidgets.QHBoxLayout()
        settings_files.addStretch()
        load = QtWidgets.QPushButton("Load settings…")
        save = QtWidgets.QPushButton("Save settings…")
        settings_files.addWidget(load)
        settings_files.addWidget(save)
        outer.addLayout(settings_files)
        main = QtWidgets.QHBoxLayout()
        from .editor_navigation import CategorySections
        tabs = CategorySections()
        self.tabs = tabs
        tabs.setMinimumWidth(550)
        forms = {}; field_forms = {}; self.section_pages = {}; self.category_tabs = {}; self.cage_control_pages = {}; self.section_contents = {}
        for category, title, description, groups in SECTIONS:
            if category not in self.category_tabs:
                from .editor_navigation import WrappingSections
                section_tabs=WrappingSections()
                section_tabs.setObjectName('Sections_'+category)
                self.category_tabs[category]=section_tabs
                icon = QtGui.QIcon(os.path.join(os.path.dirname(ICON),
                                                'category-' + category.lower() + '.svg'))
                index = tabs.addTab(section_tabs, icon, '')
                tabs.setTabToolTip(index, category)
                tabs.setTabWhatsThis(index, 'Open the ' + category + ' section.')
            section_tabs=self.category_tabs[category]
            page=QtWidgets.QWidget();page_layout=QtWidgets.QVBoxLayout(page)
            intro=QtWidgets.QLabel(description);intro.setWordWrap(True)
            page_layout.addWidget(intro)
            info=QtWidgets.QWidget();forms[title]=QtWidgets.QFormLayout(info)
            forms[title].setContentsMargins(0,0,0,0)
            if title!='Camera cage':page_layout.addWidget(info)
            cage_tabs=None;cage_pages={}
            if title=='Camera cage':
                from .editor_navigation import CageSections
                cage_tabs=CageSections();self.cage_tabs=cage_tabs
            for heading,names in groups:
                target=page_layout
                if cage_tabs is not None and heading!='Construction':
                    section={'Shared side walls':'Dimensions','Camera attachment':'Mounting & tilt','Camera / insert position':'Position','Front and rear profiles':'Profiles','Upper attachment':'Plate contacts','Lower contact':'Plate contacts','Captured tabs':'Tabs','Mounting positions':'Plate contacts','TPU attachment':'TPU attachment','Integrated bumper':'Integrated bumper'}[heading]
                    if section not in cage_pages:
                        sub=QtWidgets.QWidget();layout=QtWidgets.QVBoxLayout(sub)
                        subscroll=QtWidgets.QScrollArea();subscroll.setWidgetResizable(True);subscroll.setWidget(sub);subscroll.setFrameShape(QtWidgets.QFrame.NoFrame)
                        cage_tabs.addTab(subscroll,section);cage_pages[section]=(layout,subscroll)
                    target,subscroll=cage_pages[section]
                    for name in names:self.cage_control_pages[name]=subscroll
                box=QtWidgets.QGroupBox(heading);form=QtWidgets.QFormLayout(box)
                form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
                form.setRowWrapPolicy(QtWidgets.QFormLayout.WrapLongRows)
                target.addWidget(box)
                for name in names:field_forms[name]=form
            if title=='Camera cage':
                for layout,subscroll in cage_pages.values():layout.addStretch()
                page_layout.addWidget(cage_tabs,1)
                cage_pages['Position'][0].addWidget(info)
            page_layout.addStretch()
            self.section_contents[title]=page_layout
            scroll=QtWidgets.QScrollArea();scroll.setWidgetResizable(True)
            scroll.setFrameShape(QtWidgets.QFrame.NoFrame);scroll.setWidget(page)
            section_tabs.addTab(scroll,title.replace('&','&&'));self.section_pages[title]=(category,scroll)
        self.find_control=QtWidgets.QLineEdit()
        self.find_control.setPlaceholderText('Find a control… (e.g. keystone, strap, camera tilt)')
        self.find_control.setClearButtonEnabled(True)
        self.find_control.setToolTip('Type a control name or topic, then choose a result to open its page.')
        # Control search is placed next to the bottom frame actions.
        self.fpv_info=QtWidgets.QLabel()
        self.fpv_info.setWordWrap(True)
        forms['Camera cage'].addRow(self.fpv_info)
        self.vtx_info=QtWidgets.QLabel()
        self.vtx_info.setWordWrap(True)
        forms['VTX'].addRow(self.vtx_info)
        fit=QtWidgets.QPushButton('Fit camera height')
        fit.setToolTip('Centre the camera and raise the standoffs to a common size if needed.')
        fit.clicked.connect(self.fit_camera)
        self.fit_camera_button=fit
        forms['Camera cage'].addRow(fit)
        self.fit_stack_button=QtWidgets.QPushButton('Fit stack height')
        self.fit_stack_button.setToolTip('Raise the standoffs to a common size so the configured stack clears the top.')
        self.fit_stack_button.clicked.connect(self.fit_stack)
        forms['Stack'].addRow(self.fit_stack_button)
        fit_mounts=QtWidgets.QPushButton('Fit top plate around shared arm mounts')
        fit_mounts.clicked.connect(self.fit_shared_mounts)
        field_forms['StandoffFrontMount'].addRow(fit_mounts)
        ordered_fields=sorted(fields(Parameters),key=lambda f:FIELD_ORDER.get(f.name,10000))
        for f in ordered_fields:
            name = f.name
            if name=='StackSpacing':
                control=QtWidgets.QComboBox()
                for text,spacing in STACK_PATTERNS:control.addItem(text,spacing)
                control.currentIndexChanged.connect(self.queue_refresh)
            elif name in ENUMERATIONS:
                control = QtWidgets.QComboBox()
                control.addItems(ENUMERATIONS[name])
                # Camera profiles are populated after the video system is set.
                # A combined list here would allow incompatible selections.
                if name=='CameraPhysicalProfile':
                    control.clear()
                    control.addItem('Custom measurements')
                if name in ("PrintedPartColour","PropReferenceColour"):
                    for i,text in enumerate(ENUMERATIONS[name]):
                        swatch=PRINTED_COLOURS[text] if name=="PrintedPartColour" else prop_swatch(text)
                        control.setItemData(i,QtGui.QColor(swatch),QtCore.Qt.DecorationRole)
                control.currentIndexChanged.connect(self.queue_refresh)
            elif name in STRINGS:
                control=QtWidgets.QLineEdit('[]')
                if name=='CutoutPatterns':control.setMaxLength(1_000_000)
                control.textChanged.connect(self.queue_refresh)
            elif name in BOOLEANS:
                control = QtWidgets.QCheckBox()
                control.toggled.connect(self.queue_refresh)
            elif name in VENT_ROW_COUNTS:
                control=QtWidgets.QSpinBox()
                control.setRange(1,6);control.setSingleStep(1)
                control.valueChanged.connect(self.queue_refresh)
            else:
                control = QtWidgets.QDoubleSpinBox()
                control.setDecimals(3 if name in FLOATS else 2)
                control.setRange(-300 if name in ROOT_BOLT_COORDINATES or name in ("StackOffsetY", "StandoffPair3Y", "StandoffPair4Y", "VTXOffsetY", 'CentreSectionY','BatteryX','BatteryY') else 0, 1000)
                control.setSingleStep(0.05 if name in FLOATS else 0.5)
                if name=='CarbonTextureOpacity':
                    control.setRange(0,100);control.setDecimals(0);control.setSingleStep(5);control.setSuffix(' %')
                elif name=='FlexAntennaHolderOffset':
                    control.setRange(-80,100);control.setSuffix(' mm');control.setSingleStep(.5)
                elif name=='FlexAntennaBulkheadThickness':
                    control.setRange(2,5);control.setSuffix(' mm');control.setSingleStep(.1)
                elif name=='FlexAntennaTilt':
                    control.setRange(0,90);control.setSuffix(' degrees');control.setSingleStep(1)
                elif name=='FlexBumperCameraFrontProjection':
                    control.setRange(0,8);control.setSingleStep(.5);control.setDecimals(2);control.setSuffix(' mm')
                elif name=='FlexBumperCameraBlendReach':
                    control.setRange(0,20);control.setSingleStep(1);control.setDecimals(0);control.setSuffix(' mm')
                elif name=='FlexInsertFit':
                    control.setRange(0.0,0.25);control.setDecimals(2);control.setSingleStep(.01);control.setSuffix(' mm')
                elif name=='ArmBoltMaterialAllowance':
                    control.setRange(0,6);control.setSingleStep(.25);control.setDecimals(2);control.setSuffix(' mm')
                elif name=='FlexInsertCornerRadius':
                    control.setRange(.25,20);control.setSuffix(' mm');control.setSingleStep(.25)
                elif name=='CameraTabCutterDiameter':
                    control.setRange(.2,6);control.setSuffix(' mm');control.setSingleStep(.5)
                elif name=='CameraViewFOV':
                    control.setRange(0,179);control.setSingleStep(1);control.setSuffix(' degrees')
                elif name=='CameraViewPupilOffset':
                    control.setRange(0,20);control.setSingleStep(.5);control.setSuffix(' mm')
                elif name=='CameraForeAftOffset':
                    control.setRange(-100,100);control.setSuffix(' mm');control.setSingleStep(.5)
                elif name.endswith("EdgeFillet"):
                    control.setRange(0,30);control.setSuffix(" mm")
                elif name == "LengthToWidth":
                    control.setRange(0.65, 1.8)
                elif name == "FrontSpread":
                    control.setRange(1, 1.8)
                elif name in ('StrapSingleY','StackUSBOffsetY','FlexGuardUSBY','FlexGuardStrapY1','FlexGuardStrapY2','FlexGuardWireFrontY','FlexGuardWireRearY','FlexGuardVentBoundaryOffset','FlexGuardVTXY','FlexGuardVTXZ','FlexGuardVTXVentZOffset','FlexGuardFCVentZOffset'):
                    control.setRange(-300,300);control.setSuffix(' mm')
                elif name.startswith('CameraTab') and name.endswith('Offset'):
                    control.setRange(-100,100);control.setSuffix(' mm')
                elif name == 'RearArmExtension':
                    control.setRange(0,300)
                    control.setSuffix(' mm')
                elif name in ("CarbonDensity","StandoffDensity","LiPoPadDensity","FlexDensity"):
                    control.setRange(0.001 if name=='LiPoPadDensity' else 0.1, 10)
                    control.setSuffix(" g/cm³")
                elif name in ('MotorPadRotation','BatteryRotation'):
                    control.setRange(-180,180)
                    control.setSingleStep(1)
                    control.setSuffix('°')
                elif name=='MotorHoleRotation':
                    control.setRange(-360,360)
                    control.setSingleStep(1)
                    control.setSuffix('°')
                elif name in ('CameraTilt','CameraTiltMin','CameraTiltMax'):
                    control.setRange(0,60)
                    control.setSuffix('°')
                elif name in ('BottomNoseTipWidth','BottomRearTipWidth','MidRearTipWidth','TopRearTipWidth','TopFrontTipWidth'):
                    control.setRange(10,90);control.setSuffix(' %');control.setSingleStep(1)
                elif name in ('FlexBumperTipWidth','FlexBumperRecess'):
                    control.setRange(0,90);control.setSuffix(' %');control.setSingleStep(1)
                elif name in ('PlateEndWidth','ArmProfileAmount'):
                    control.setRange(40 if name=='PlateEndWidth' else 0,100);control.setSuffix(' %');control.setSingleStep(1)
                elif name.startswith('LiPoPadOutline'):
                    control.setRange(1,100);control.setSuffix(' %');control.setSingleStep(1)
                elif name in ('MotorMass','PropMass','FCMass','ESCMass','VTXMass','CameraMass','OtherMass'):
                    control.setRange(0,3000);control.setSuffix(' g')
                elif name=='ScrewMassScale':
                    control.setRange(0,10);control.setSuffix(' ×')
                elif name=='BatteryCells':
                    control.setRange(3,8);control.setDecimals(0);control.setSingleStep(1);control.setSuffix('S')
                elif name=='BatteryMass':
                    control.setRange(.1,3000);control.setSuffix(' g')
                elif name not in FLOATS:
                    control.setSuffix(" mm")
                if name == "FlexGuardClearance":
                    control.setRange(0,1000);control.setDecimals(2);control.setSingleStep(.05)
                if name == "StandoffHeight":
                    control.setMinimum(0.1)
                if name=='ArmJointClearance':
                    control.setRange(0,1)
                    control.setSingleStep(.05)
                control.valueChanged.connect(self.queue_refresh)
                if name=='BottomBodyRearReach':
                    control.valueChanged.connect(lambda _value:setattr(self,'_bottom_body_reach_value',None))
            control.setToolTip(TIPS.get(name, label(name) + (" in millimetres." if name not in FLOATS else ".")))
            control.setObjectName(name)
            self.controls[name] = control
            field_label = QtWidgets.QLabel(label(name))
            self.field_labels[name] = field_label
            if name in HIDDEN_FIELDS:
                control.hide(); field_label.hide()
                continue
            display = control
            if name == "StandoffHeight":
                display, self.rear_standoff_sizes, self._sync_rear_size = standoff_size_row(control)
            elif name == 'CameraWidth':
                display,self.camera_width_sizes,self._sync_camera_size=camera_size_row(control,self)
            elif name == 'CameraSideBoltSpacing':
                display,self.camera_spacing_sizes,self._sync_camera_spacing=camera_spacing_row(control)
            field_forms[name].addRow(field_label, display)
            if name=='RootBoltLayout':
                self.copy_bolt_spacing_button=QtWidgets.QPushButton('Use current spacing for custom bolts')
                self.copy_bolt_spacing_button.setToolTip('Copy the front-right centred pair into frame X/Y offsets, mirror the pattern on the other arms, then enable custom placement.')
                self.copy_bolt_spacing_button.clicked.connect(self.custom_bolts_from_spacing)
                field_forms[name].addRow(self.copy_bolt_spacing_button)
            if name == "StandoffHeight":
                self.front_standoff_height = QtWidgets.QDoubleSpinBox()
                self.front_standoff_height.setDecimals(2)
                self.front_standoff_height.setSuffix(" mm")
                self.front_standoff_height.setRange(0.1, 2000)
                self.front_standoff_height.setSingleStep(0.5)
                self.front_standoff_height.setToolTip("Actual front pair length from its mounting surface to the top. Changing this adjusts the rear length to keep the top level.")
                front_row, self.front_standoff_sizes, self._sync_front_size = standoff_size_row(self.front_standoff_height)
                field_forms[name].addRow("Front standoff height", front_row)
                self.front_standoff_height.valueChanged.connect(self.set_front_standoff_height)
                self.standoff_info = QtWidgets.QLabel()
                self.standoff_info.setWordWrap(True)
                field_forms[name].addRow(self.standoff_info)
        # Optical camera preview uses the *currently edited* parameter values,
        # not saved objects or the last generated model. Render on demand because
        # tessellation/ray tests are intentionally not part of every GUI refresh.
        self._init_camera_view()
        # A saved design from older releases may still contain the former 4 mm
        # default cage web. Selecting O4 Pro should adopt the 2 mm interface
        # default before validation; a user can still choose a larger web.
        self.controls['FPVSystemProfile'].currentTextChanged.connect(self._on_fpv_profile_selected)
        self.controls['CameraPhysicalProfile'].currentTextChanged.connect(self._on_camera_physical_profile_selected)
        self.controls['VideoSystem'].currentTextChanged.connect(self._on_video_system_selected)
        self.controls['BatteryPreset'].currentTextChanged.connect(self._on_battery_preset_selected)
        for battery_field in ('BatteryWidth','BatteryLength','BatteryHeight','BatteryMass','BatteryCells'):
            self.controls[battery_field].valueChanged.connect(self._on_battery_measurement_edited)
        self.plate_info=QtWidgets.QLabel();self.plate_info.setWordWrap(True);forms['Bottom plate'].insertRow(0,self.plate_info)
        self.mid_plate_info=QtWidgets.QLabel();self.mid_plate_info.setWordWrap(True);forms['Mid plate'].insertRow(0,self.mid_plate_info)
        self.top_plate_info=QtWidgets.QLabel();self.top_plate_info.setWordWrap(True);forms['Top plate'].insertRow(0,self.top_plate_info)
        self.root_fit_info=QtWidgets.QLabel();self.root_fit_info.setWordWrap(True);forms['Roots'].insertRow(0,self.root_fit_info)
        self.airflow=AirflowEditor(self.values)
        self.airflow.changed.connect(self._airflow_geometry_changed)
        self.airflow.metadataChanged.connect(self._airflow_metadata_changed)
        # One setting, two convenient views. Both checkboxes stay in sync;
        # only the standard parameter control owns the persisted value.
        self.airflow.copy_to_pad.setChecked(self.controls['LiPoPadCopyAirflow'].isChecked())
        self.airflow.copy_to_pad.toggled.connect(self.controls['LiPoPadCopyAirflow'].setChecked)
        self.controls['LiPoPadCopyAirflow'].toggled.connect(self.airflow.copy_to_pad.setChecked)
        airflow_scroll=QtWidgets.QScrollArea();airflow_scroll.setWidgetResizable(True);airflow_scroll.setWidget(self.airflow)
        airflow_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        finishing=self.category_tabs['Finishing'];finishing.insertTab(0,airflow_scroll,'Airflow / outlines')
        self.section_pages['Airflow / outlines']=('Finishing',airflow_scroll)
        self.search_locations={}
        for name,(category,title,group) in FIELD_LOCATION.items():
            caption=f'{category} > {title} > {label(name)}'
            self.search_locations[caption]=name
        self.search_locations['Hardware > Standoffs > Front standoff height']='@front_height'
        self.search_locations['Hardware > Stack > Fit stack height']='@fit_stack'
        self.search_locations['FPV > Camera cage > Position > Fit camera height']='@fit_camera'
        self.search_locations['FPV > Camera view > Render camera view']='@camera_view_render'
        self.search_locations['FPV > Camera view > Check tilt range']='@camera_view_sweep'
        self.search_locations['Finishing > Airflow / outlines > Cutout type, outline notch, patterns']='@airflow'
        self.extra_search_targets={'@camera_view_render':('Camera view',self.camera_view_render),
                                   '@camera_view_sweep':('Camera view',self.camera_view_sweep)}
        cuts=[('Part',self.airflow.role),('Cutout type',self.airflow.shape),
              ('Cutting mode / outline notch',self.airflow.mode),('Enabled',self.airflow.enabled),
              ('Saved patterns',self.airflow.pattern_list),('Find saved cutout',self.airflow.find_pattern),
              ('Filter cutouts by part',self.airflow.filter_role),('Show pattern numbers',self.airflow.show_numbers),
              ('Zoom to selected cutout',self.airflow.zoom_button),('Fit cutout plate preview',self.airflow.fit_button),
              ('Add pattern',self.airflow.add_button),
              ('Apply to pattern',self.airflow.apply_button),('Remove pattern',self.airflow.remove_button),
              ('Discard unapplied changes',self.airflow.discard_button),
              ('Copy to other camera side',self.airflow.copy_button),('Check plate cuts in CAD',self.airflow.check_button)]
        cut_names={'width':'Width','length':'Length','x':'Centre U','y':'Centre V',
                   'columns':'Columns','rows':'Rows','pitch_x':'Pitch U','pitch_y':'Pitch V','rotation':'Rotation',
                   'depth':'Pocket depth'}
        cuts.extend((cut_names.get(key,key.replace('_',' ').capitalize()),control) for key,control in self.airflow.inputs.items())
        for title,control in cuts:
            key='@cut_'+title
            self.search_locations['Finishing > Airflow / outlines > '+title]=key
            self.extra_search_targets[key]=('Airflow / outlines',control)
        for caption,key,title,control in [
            ('Use current spacing for custom bolts','@copy_bolts','Bolts',self.copy_bolt_spacing_button),
            ('Fit top plate around shared arm mounts','@fit_mounts','Standoffs',fit_mounts)]:
            category=self.section_pages[title][0]
            self.search_locations[f'{category} > {title} > {caption}']=key
            self.extra_search_targets[key]=(title,control)
        self.finder=QtWidgets.QCompleter(sorted(self.search_locations),self)
        self.finder.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.finder.setFilterMode(QtCore.Qt.MatchContains)
        self.finder.setMaxVisibleItems(12)
        self.find_control.setCompleter(self.finder)
        self.finder.activated[str].connect(self.jump_to_control)
        self.find_control.returnPressed.connect(self.find_control_enter)
        main.addWidget(tabs, 5)
        right = QtWidgets.QVBoxLayout()
        self.preview_mode=QtWidgets.QComboBox()
        self.preview_mode.setToolTip('Inspect the assembled top view, all flat parts, all arms, or one complete part before creating the frame.')
        self.preview_mode.currentIndexChanged.connect(self.set_preview_mode)
        right.addWidget(self.preview_mode)
        self.preview = TopPreview()
        preview_tools = QtWidgets.QHBoxLayout()
        preview_hint = QtWidgets.QLabel('Wheel: zoom • drag: pan • double-click: fit')
        preview_tools.addWidget(preview_hint, 1)
        fit_preview = QtWidgets.QPushButton('Fit view')
        fit_preview.setAutoDefault(False)
        fit_preview.clicked.connect(self.preview.reset_view)
        preview_tools.addWidget(fit_preview)
        right.addLayout(preview_tools)
        right.addWidget(self.preview, 1)
        self.summary = QtWidgets.QLabel()
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet("font-weight: bold; padding: 6px;")
        right.addWidget(self.summary)
        self.mass_button=QtWidgets.QPushButton('Calculate frame weight / CG')
        self.mass_button.setToolTip('Use exact current solids and material densities. No document is created. Screws, straps, motors and electronics are excluded.')
        self.mass_button.clicked.connect(self.calculate_mass)
        self.mass_result=QtWidgets.QLabel('Calculate to see frame mass and centre of gravity.');self.mass_result.setWordWrap(True)
        self.mass_signature=None
        right.addWidget(self.mass_button);right.addWidget(self.mass_result)
        self.messages = QtWidgets.QPlainTextEdit()
        self.messages.setReadOnly(True)
        self.messages.setMaximumHeight(130)
        right.addWidget(self.messages)
        self.preview_panel = QtWidgets.QWidget()
        self.preview_panel.setLayout(right)
        main.addWidget(self.preview_panel, 6)
        def workspace_changed(*_):
            airflow_active = (tabs.currentWidget() is finishing and
                              finishing.currentWidget() is airflow_scroll)
            # The optical camera-view tab has its own image renderer, just as
            # Airflow / outlines has its own full-width cutting workspace.
            camera_view_active = (tabs.currentWidget() is self.category_tabs['FPV'] and
                                  self.category_tabs['FPV'].currentWidget() is self.section_pages['Camera view'][1])
            self.preview_panel.setVisible(not (airflow_active or camera_view_active))
        tabs.currentChanged.connect(workspace_changed)
        finishing.currentChanged.connect(workspace_changed)
        self.category_tabs['FPV'].currentChanged.connect(workspace_changed)
        workspace_changed()
        outer.addLayout(main, 1)
        self.note = QtWidgets.QLabel()
        self.note.setWordWrap(True)
        outer.addWidget(self.note)
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel)
        self.generate = self.buttons.addButton("Update frame" if settings else "Create frame", QtWidgets.QDialogButtonBox.AcceptRole)
        self.buttons.rejected.connect(self.reject)
        self.generate.clicked.connect(self.apply)
        # Enter in the finder must not invoke a fit or create action.
        for button in self.findChildren(QtWidgets.QPushButton):
            button.setAutoDefault(False)
            button.setDefault(False)
        actions = QtWidgets.QHBoxLayout()
        actions.addWidget(self.find_control, 1)
        actions.addWidget(self.buttons)
        outer.addLayout(actions)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(140)
        self.timer.timeout.connect(self.refresh)
        load.clicked.connect(self.load)
        save.clicked.connect(self.save)
        # Restore the values while constructing the *hidden* editor. A complete
        # geometry validation/preview here blocks the command and encourages
        # a partially sized transient window on slower FreeCAD/Qt systems.
        self.set_values(read_parameters(settings) if settings else replace(Parameters(), StrapSlotsEnabled=False),
                        defer_refresh=True)
        sizing=QtWidgets.QComboBox();sizing.addItem('Apply motor / prop sizing…');sizing.addItems(tuple(MOTOR_SIZES))
        sizing.activated.connect(lambda i:self.set_values(apply_motor_size(self.values(),sizing.itemText(i))) if i else None)
        forms['Motors'].addRow('Motor / prop size',sizing)
        self.motor_sizing=sizing
        # Finish validation and all widget sizing while the native window is
        # still hidden. A zero-delay timer previously entered a full refresh
        # while Qt was showing the dialog; Windows could display a small blank
        # window before the layout settled and a correctly sized one appeared.
        self.generate.setEnabled(False)
        self.summary.setText('Preparing the selected frame…')
        self._initial_refresh()
        self.ensurePolished()
        self.layout().activate()
        self.resize(max(1100,self.minimumWidth()), max(750,self.minimumHeight()))

    def _initial_refresh(self):
        # Do not launch two competing refreshes when a native resize/focus
        # event reaches the editor during its first display.
        self.timer.stop()
        try:
            self.refresh()
        except Exception as exc:
            self.generate.setEnabled(False)
            self.messages.setPlainText('Cannot initialise frame preview: ' + str(exc))
            # Keep the editor visible so settings can be inspected or changed.


    def _init_camera_view(self):
        # Keep the Camera view's standard introductory text and optical-profile
        # controls, but move them out of the one-column form into an uncluttered
        # camera workspace. No part of the frame's ordinary 2-D preview is used.
        page_layout = self.section_contents['Camera view']
        optical_group = next(
            (page_layout.itemAt(i).widget() for i in range(page_layout.count())
             if isinstance(page_layout.itemAt(i).widget(), QtWidgets.QGroupBox)
             and page_layout.itemAt(i).widget().title() == 'Optical profile'), None)
        if optical_group is None:
            raise RuntimeError('Camera view optical profile group is missing.')
        page_layout.removeWidget(optical_group)
        # The regular section builder inserts a bottom stretch, which would
        # otherwise steal half of the available vertical space from the image.
        for i in reversed(range(page_layout.count())):
            item = page_layout.itemAt(i)
            if item.spacerItem():
                page_layout.takeAt(i)

        options = QtWidgets.QGroupBox('Camera options')
        options.setMinimumWidth(285)
        left = QtWidgets.QVBoxLayout(options)
        left.setSpacing(7)
        self.camera_view_active_camera = QtWidgets.QLabel()
        self.camera_view_active_camera.setWordWrap(True)
        self.camera_view_active_camera.setToolTip(
            'Automatically follows the physical camera chosen in FPV > Camera. '
            'Selecting another physical camera restores its manufacturer/estimated optics. '
            'Manual optical overrides are available under Optical settings.')
        left.addWidget(self.camera_view_active_camera)

        tilt_row = QtWidgets.QHBoxLayout()
        self.camera_view_use_tilt = QtWidgets.QCheckBox('Use current camera tilt')
        self.camera_view_use_tilt.setToolTip(
            'Use Camera uptilt from FPV > Camera, even for adjustable mounts. '
            'The adjustment range midpoint is not the selected viewing tilt.')
        self.camera_view_use_tilt.setChecked(True)
        self.camera_view_tilt = QtWidgets.QDoubleSpinBox()
        self.camera_view_tilt.setRange(0, 60)
        self.camera_view_tilt.setSingleStep(1)
        self.camera_view_tilt.setSuffix('°')
        self.camera_view_tilt.setEnabled(False)
        self.camera_view_tilt.setToolTip('Preview-only tilt override; does not move the physical camera or frame.')
        self.camera_view_use_tilt.toggled.connect(self._camera_view_use_tilt_changed)
        self.camera_view_tilt.valueChanged.connect(lambda _: self._camera_view_mark_stale())
        tilt_row.addWidget(self.camera_view_use_tilt)
        tilt_row.addWidget(self.camera_view_tilt)
        left.addLayout(tilt_row)

        choices = QtWidgets.QFormLayout()
        choices.setContentsMargins(0, 0, 0, 0)
        choices.setRowWrapPolicy(QtWidgets.QFormLayout.WrapLongRows)
        self.camera_view_recording_mode = QtWidgets.QComboBox()
        self.camera_view_recording_mode.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                                      QtWidgets.QSizePolicy.Fixed)
        self.camera_view_recording_mode.setToolTip(
            'Choose a supported resolution/aspect. Yellow boundary = expected image area. '
            'Real sensor, FOV and stabilization crops are not calibrated.')
        self.camera_view_recording_mode.currentIndexChanged.connect(self._camera_view_mode_changed)
        choices.addRow('Recording mode', self.camera_view_recording_mode)
        self.camera_view_extra_crop = QtWidgets.QSpinBox()
        self.camera_view_extra_crop.setRange(0, 30)
        self.camera_view_extra_crop.setSuffix('%')
        self.camera_view_extra_crop.setToolTip(
            'Optional MANUAL crop applied equally to both image dimensions. '
            '0% means no extra ASSUMED crop; it does not mean RockSteady or Gyroflow crop is zero.')
        self.camera_view_extra_crop.valueChanged.connect(self._camera_view_refresh_crop)
        choices.addRow('Additional crop', self.camera_view_extra_crop)
        left.addLayout(choices)

        self.camera_view_show_props = QtWidgets.QCheckBox('Show possible propeller visibility')
        self.camera_view_show_props.setChecked(True)
        self.camera_view_show_props.setToolTip(
            'Show where a spinning propeller could sweep through the lens view. '
            'The translucent bright-magenta overlay is not solid blockage, and actual blade visibility '
            'depends on RPM, shutter, recording mode and lighting. No frame geometry is changed.')
        self.camera_view_show_props.toggled.connect(self._camera_view_props_changed)
        left.addWidget(self.camera_view_show_props)

        self.camera_view_render = QtWidgets.QPushButton('Render camera view')
        self.camera_view_render.clicked.connect(self.render_camera_view)
        self.camera_view_sweep = QtWidgets.QPushButton('Check visible frame through tilt range')
        self.camera_view_sweep.setToolTip(
            'Tests sample viewing angles, without changing physical mounting geometry. '
            'It is not a collision or guaranteed optical calibration test.')
        self.camera_view_sweep.clicked.connect(self.sweep_camera_view)
        left.addWidget(self.camera_view_render)
        left.addWidget(self.camera_view_sweep)

        self.camera_view_optics_toggle = QtWidgets.QToolButton()
        self.camera_view_optics_toggle.setText('Optical settings (advanced)')
        self.camera_view_optics_toggle.setCheckable(True)
        self.camera_view_optics_toggle.setChecked(False)
        self.camera_view_optics_toggle.setArrowType(QtCore.Qt.RightArrow)
        self.camera_view_optics_toggle.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.camera_view_optics_toggle.setToolTip('Optional lens, aspect, FOV and optical-pupil overrides.')
        def show_optics(visible):
            self.camera_view_optics_toggle.setArrowType(
                QtCore.Qt.DownArrow if visible else QtCore.Qt.RightArrow)
            optical_group.setVisible(visible)
        self.camera_view_optics_toggle.toggled.connect(show_optics)
        left.addWidget(self.camera_view_optics_toggle)
        # Move the original field widgets, keeping settings, validation, search,
        # and parameter binding exactly as they were in previous versions.
        left.addWidget(optical_group)
        optical_group.hide()
        left.addStretch(1)

        preview = QtWidgets.QGroupBox('Virtual camera preview')
        right = QtWidgets.QVBoxLayout(preview)
        right.setSpacing(6)
        self.camera_view_picture = CameraPreviewLabel()
        right.addWidget(self.camera_view_picture, 1)
        self.camera_view_crop_info = QtWidgets.QLabel(
            'Yellow = recording area; magenta = possible propeller sweep. '
            'Crosshair = optical centre; dashed box = central obstruction test.')
        self.camera_view_crop_info.setWordWrap(True)
        right.addWidget(self.camera_view_crop_info)

        # Detailed diagnostics can be longer than the preview itself. Give
        # results their own bounded area instead of stretching the entire page.
        result_widget = QtWidgets.QWidget()
        result_layout = QtWidgets.QVBoxLayout(result_widget)
        result_layout.setContentsMargins(3, 3, 3, 3)
        result_layout.setSpacing(4)
        self.camera_view_status = QtWidgets.QLabel('Camera field of view not yet checked.')
        self.camera_view_status.setWordWrap(True)
        self.camera_view_status.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        result_layout.addWidget(self.camera_view_status)
        self.camera_view_recording_info = QtWidgets.QLabel(
            'Choose a recording mode to display its estimated captured area.')
        self.camera_view_recording_info.setWordWrap(True)
        self.camera_view_recording_info.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        result_layout.addWidget(self.camera_view_recording_info)
        result_layout.addStretch()
        results = QtWidgets.QScrollArea()
        results.setWidgetResizable(True)
        results.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        results.setFrameShape(QtWidgets.QFrame.StyledPanel)
        results.setWidget(result_widget)
        results.setFixedHeight(115)
        results.setToolTip('Detailed camera and recording results. Scroll here only for longer reports.')
        right.addWidget(results)
        self.camera_view_results = results

        workspace = CameraWorkspace(options, preview)
        workspace.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.camera_view_workspace = workspace
        page_layout.addWidget(workspace, 1)
        self._camera_view_mesh_cache = None
        self._camera_view_last_settings = None
        self._camera_view_last_result = None
        self._camera_view_mode_profile = None
        self._camera_view_update_recording_modes(Parameters())

    def _camera_view_update_recording_modes(self,p):
        from .camera_view import resolved_optics,recording_modes
        name,fov,aspect,_=resolved_optics(p)
        if hasattr(self,'camera_view_active_camera'):
            detail=('manual optical override' if
                    p.CameraViewProfile!='Follow selected camera' or p.CameraViewFOV>0 else
                    'follows FPV camera selection')
            self.camera_view_active_camera.setText(
                'Active virtual camera: %s  |  %.1f° diagonal FOV  |  %s  (%s)' %
                (name,fov,aspect,detail))
        # Include the PHYSICAL model, not just resolved lens name. Different
        # custom cameras can use the same generic optical profile but must
        # never reuse the previous camera's rendered image.
        identity=(p.FPVSystemProfile,p.CameraPhysicalProfile,name)
        if self._camera_view_mode_profile==identity:return
        modes=recording_modes(name)
        combo=self.camera_view_recording_mode
        combo.blockSignals(True)
        combo.clear()
        combo.addItem('Full lens preview (no recording crop)',None)
        for mode in modes:combo.addItem(mode[1],mode[0])
        combo.setCurrentIndex(0)  # a mode on the previous camera is not transferable
        combo.blockSignals(False)
        self._camera_view_mode_profile=identity
        self._camera_view_last_result=None
        self._camera_view_last_settings=None
        # Do not display stale rays from a different camera as valid results.
        self.camera_view_picture.clear()
        self.camera_view_picture.setText(
            'Camera changed to %s.\nClick Render camera view to inspect its field of view.' % name)
        self.camera_view_status.setText('Camera profile selected: %s. Render to update obstructions.' % name)
        self.camera_view_recording_info.setText(
            'Recording modes updated for %s. Choose a mode and render to see its expected image boundary.' % name)

    def _camera_view_selected_mode(self,p):
        from .camera_view import resolved_optics,recording_modes
        mode_key=self.camera_view_recording_mode.currentData()
        profile=resolved_optics(p)[0]
        return next((mode for mode in recording_modes(profile) if mode[0]==mode_key),None)

    def _camera_view_render_aspect(self,p):
        from .camera_view import resolved_optics,recording_reference_aspect,CAMERA_ASPECT_FOV
        name,_,aspect,_=resolved_optics(p)
        mode=self._camera_view_selected_mode(p)
        if mode and name in CAMERA_ASPECT_FOV:
            # Foxeer 16:9 can have WIDER optics than 4:3: do not represent
            # a real manufacturer change of FOV as merely a centre crop.
            return mode[2]
        return recording_reference_aspect(name,aspect) if mode else aspect

    def _camera_view_inputs(self,p):
        from .geometry import _geometry_signature
        return (_geometry_signature(p),p.CameraViewProfile,p.CameraViewAspect,
                p.CameraViewFOV,p.CameraViewPupilOffset)

    def _camera_view_refresh_crop(self,*_):
        if not hasattr(self,'camera_view_recording_info'):return
        p=self.values()
        if (self._camera_view_last_settings != self._camera_view_inputs(p) or
                self._camera_view_last_result is None or
                self._camera_view_last_result['aspect']!=self._camera_view_render_aspect(p) or
                abs(self._camera_view_last_result['tilt']-self._camera_view_tilt(p))>0.001):
            self.camera_view_recording_info.setText('Recording crop changed. Click Render camera view to update the full lens projection.')
            return
        self._draw_camera_view(self._camera_view_last_result)
        self._camera_view_recording_summary(self._camera_view_last_result,p)

    def _camera_view_mode_changed(self,*_):
        self._camera_view_refresh_crop()

    def _camera_view_props_changed(self,*_):
        # Visibility is a preview-only option. Repaint existing ray samples
        # without rebuilding CAD or recasting the physical obstruction mesh.
        result=self._camera_view_last_result
        if result is None:return
        p=self.values()
        if (self._camera_view_last_settings != self._camera_view_inputs(p) or
                result['aspect'] != self._camera_view_render_aspect(p) or
                abs(result['tilt'] - self._camera_view_tilt(p))>.001):
            self.camera_view_status.setText('Camera view settings changed. Render again before inspecting the propeller overlay.')
            return
        self._draw_camera_view(result)
        self._camera_view_recording_summary(result,p)
        self._camera_view_update_status(result)

    def _camera_view_update_status(self,result):
        # Cached optical and build timings are preserved when the user only
        # toggles the prop overlay, so the reported percentages stay correct.
        if not hasattr(self,'_camera_view_status_base') or self._camera_view_status_base is None:return
        message=self._camera_view_status_base
        if self.camera_view_show_props.isChecked():
            roles=sorted(result.get('prop_roles',{}).items(),key=lambda part:part[1],reverse=True)
            labels=', '.join('%s %.1f%%'%(name,n*100/max(1,len(result['pixels'])*len(result['pixels'][0])))
                             for name,n in roles) or 'none'
            message+=('\nPossible prop sweep: %.1f%% of image, %.1f%% of centre (not a solid blockage). Motors: %s.' %
                      (result.get('prop_visible_pct',0.),result.get('centre_prop_visible_pct',0.),labels))
        else:
            message+='\nPropeller visibility overlay is hidden; frame/TPU obstruction remains unchanged.'
        self.camera_view_status.setText(message)

    def _camera_view_recording_summary(self,result,p):
        from .camera_view import recording_crop_bounds,recording_obstruction
        mode=self._camera_view_selected_mode(p)
        if mode is None:
            text='Full simulated lens view. Yellow recording boundary is disabled.'
            if self.camera_view_show_props.isChecked():
                text+=' Magenta overlay indicates potential propeller swept area, not blade opacity.'
            self.camera_view_recording_info.setText(text)
            return
        bounds=recording_crop_bounds(result['aspect'],mode,self.camera_view_extra_crop.value())
        blocked,roles=recording_obstruction(result['pixels'],bounds)
        rows=result['pixels'];height=len(rows);width=len(rows[0]);x0,y0,x1,y1=bounds
        sample_count=sum(1 for j,row in enumerate(rows) for i in range(width)
                         if x0<=(i+.5)/width<=x1 and y0<=(j+.5)/height<=y1)
        contributors=', '.join('%s %.1f%%'%(name,n*100/max(1,sample_count))
                               for name,n in sorted(roles.items(),key=lambda pair:pair[1],reverse=True)[:3]) or 'none'
        margin_note=('Manual additional crop: %d%% of both dimensions. '%self.camera_view_extra_crop.value()
                     if self.camera_view_extra_crop.value() else '')
        prop_note=''
        if self.camera_view_show_props.isChecked():
            prop_pct,prop_roles=recording_obstruction(result.get('prop_pixels',[]),bounds)
            prop_names=', '.join(sorted(prop_roles)) or 'none'
            prop_note=' Possible prop sweep in recording window: %.1f%% (%s); NOT solid obstruction.\n' % (prop_pct,prop_names)
        self.camera_view_recording_info.setText(
            'Recording window: %s | estimated frame/TPU obstruction %.1f%%. Visible parts: %s.\n%s%s%s. '
            'Aspect-ratio crop is centred; sensor readout, EIS, camera FOV modes and lens distortion are NOT calibrated.' %
            (mode[1],blocked,contributors,prop_note,margin_note,mode[4]))

    def _camera_view_mark_stale(self):
        if hasattr(self, 'camera_view_status') and self._camera_view_last_settings is not None:
            self.camera_view_status.setText('Preview tilt changed. Click Render camera view to inspect the new angle.')

    def _camera_view_geometry(self,p):
        from .geometry import camera_view_physical_shapes,physical_roles,_geometry_signature
        from .camera_view import tessellate_physical,make_bvh
        signature=_geometry_signature(p)
        cached=self._camera_view_mesh_cache
        if cached is not None and cached[0]==signature:return cached[1:]
        shapes=camera_view_physical_shapes(p)
        roles=tuple(shapes)
        # Retry coarser preview meshes for unusually complex TPU/airflow
        # models. Never omit a physical part and call the FOV clear.
        for tolerance in (0.9,1.6,2.8):
            try:
                tris=tessellate_physical(shapes,roles,tolerance=tolerance)
                break
            except ValueError as exc:
                if '300,000 triangles' not in str(exc) or tolerance>=2.8:raise
        bvh=make_bvh(tris)
        self._camera_view_mesh_cache=(signature,tris,bvh)
        return tris,bvh

    def _camera_view_use_tilt_changed(self,on):
        self.camera_view_tilt.setEnabled(not on)
        if on:
            # Keep the disabled spin box honest: it displays the actual FPV
            # camera uptilt, not the mechanical arc-slot construction midpoint.
            self.camera_view_tilt.setValue(self.values().CameraTilt)
        self._camera_view_mark_stale()

    def _camera_view_tilt(self,p):
        # For Variable mounts camera_reference_angle() deliberately returns the
        # slot-construction midpoint. That angle is NOT the selected camera pose.
        return p.CameraTilt if self.camera_view_use_tilt.isChecked() else self.camera_view_tilt.value()

    def _camera_view_busy(self,busy):
        self.camera_view_render.setEnabled(not busy)
        self.camera_view_sweep.setEnabled(not busy)
        if busy:QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        else:QtWidgets.QApplication.restoreOverrideCursor()

    def render_camera_view(self):
        if not self.values().FPVEnabled:
            self.camera_view_status.setText('Enable FPV in Frame > Layout to use the virtual camera.')
            return
        p=self.values()
        self._camera_view_update_recording_modes(p)
        tilt=self._camera_view_tilt(p)
        self._camera_view_busy(True)
        self.camera_view_status.setText('Generating current frame geometry and checking viewing rays…')
        import time
        camera_view_start=time.perf_counter()
        QtWidgets.QApplication.processEvents()
        try:
            from .camera_view import render_rays
            tris,tree=self._camera_view_geometry(p)
            camera_mesh_seconds=time.perf_counter()-camera_view_start
            from .camera_view import resolved_optics,CAMERA_BODY_WIDTHS
            name,fov,original_aspect,source=resolved_optics(p)
            aspect=self._camera_view_render_aspect(p)
            width,height=(128,72) if aspect=='16:9' else (120,90)
            # Recording overlays can change without changing geometry, optics,
            # or rays. Reuse the prior projection instead of rerunning the BVH.
            from .geometry import _geometry_signature
            ray_key=(self._camera_view_inputs(p),round(tilt,6),aspect,width,height)
            cached=getattr(self,'_camera_view_ray_cache',None)
            if cached is not None and cached[0]==ray_key:
                result=cached[1]
            else:
                result=render_rays(tris,tree,p,tilt,width=width,height=height,aspect_override=aspect)
                self._camera_view_ray_cache=(ray_key,result)
            camera_render_seconds=time.perf_counter()-camera_view_start-camera_mesh_seconds
            fov=result['fov']  # report the rendered mode's true preset FOV
            self._camera_view_last_settings=self._camera_view_inputs(p)
            self._camera_view_last_result=result
            self._draw_camera_view(result)
            self._camera_view_recording_summary(result,p)
            counts=sorted(result['roles'].items(),key=lambda item:item[1],reverse=True)
            contributors=', '.join('%s %.1f%%'%(role,count*100/(width*height)) for role,count in counts[:4]) or 'none'
            assessment='Visible obstruction' if result['blocked_pct']>0 else 'No obstruction found in sampled rays'
            if not self.camera_view_use_tilt.isChecked() and (p.CameraMountMode=='Fixed' and abs(p.CameraTilt-tilt)>0.01 or
                p.CameraMountMode=='Variable' and not p.CameraTiltMin<=tilt<=p.CameraTiltMax):
                assessment+=' — WARNING: preview tilt lies outside the selected physical mount settings'
            profile_warning=(' The optical preset does NOT change the physical camera dimensions.' if
                p.CameraViewProfile!='Follow selected camera' else '')
            expected_width=CAMERA_BODY_WIDTHS.get(name)
            if expected_width and abs(expected_width-p.CameraWidth)>1.1:
                profile_warning+=' WARNING: %g mm physical camera is not the nominal %g mm body width of this optical model.' % (p.CameraWidth,expected_width)
            self._camera_view_status_base=(
                '%s | %s | %.1f degrees diagonal FOV | %.1f degrees tilt | %s\n'
                'Frame/TPU pixels: %.1f%% overall, %.1f%% central region. Parts: %s.\n%s%s\n'
                'Preview: %.2fs geometry/mesh + %.2fs ray tracing. Approximate lens projection; confirm actual camera mode, stabilization crop and physical video.' %
                (assessment,name,fov,tilt,aspect,result['blocked_pct'],result['centre_blocked_pct'],contributors,source,profile_warning,camera_mesh_seconds,camera_render_seconds))
            self._camera_view_update_status(result)
        except Exception as exc:
            self.camera_view_status.setText('Cannot render virtual camera: '+str(exc))
        finally:
            self._camera_view_busy(False)

    def _draw_camera_view(self,result):
        from .camera_view import resolved_optics
        pixels=result['pixels'];height=len(pixels);width=len(pixels[0]);aspect=result['aspect']
        prop_pixels=result.get('prop_pixels') if self.camera_view_show_props.isChecked() else None
        image=QtGui.QImage(width,height,QtGui.QImage.Format_RGB32)
        for row in range(height):
            for col in range(width):
                role=pixels[row][col]
                if role:
                    if 'Bumper' in role or 'Protector' in role or 'Guard' in role or 'Pad' in role or 'CameraTPU' in role:
                        rgb=(37,178,161)  # TPU silhouette
                    elif 'Standoff' in role:
                        rgb=(184,139,91)
                    else:
                        rgb=(27,36,51)   # carbon silhouette
                else:
                    t=row/float(height)
                    rgb=(max(50,int(115-50*t)),max(80,int(169-45*t)),max(106,int(207-28*t)))
                if prop_pixels and prop_pixels[row][col]:
                    # Bright magenta distinguishes possible propeller sweep from
                    # the teal TPU, dark carbon, blue sky and yellow crop line.
                    # Retain transparency: this is NOT solid obstruction.
                    alpha=.76 if (row+col)%4 in (0,1) else .68
                    tint=(255,52,205)
                    rgb=tuple(int((1.-alpha)*c+alpha*t) for c,t in zip(rgb,tint))
                    # A vivid, thin perimeter keeps the disc visible where its
                    # interior overlaps dark frame components or similar tones.
                    if (row==0 or row==height-1 or col==0 or col==width-1 or
                            not prop_pixels[row-1][col] or not prop_pixels[row+1][col] or
                            not prop_pixels[row][col-1] or not prop_pixels[row][col+1]):
                        rgb=(255,85,226)
                image.setPixel(col,row,(255<<24)|(rgb[0]<<16)|(rgb[1]<<8)|rgb[2])
        scaled=image.scaled(600,338 if aspect=='16:9' else 450,QtCore.Qt.IgnoreAspectRatio,QtCore.Qt.SmoothTransformation)
        painter=QtGui.QPainter(scaled)
        try:
            painter.setPen(QtGui.QPen(QtGui.QColor(255,255,255,120),1))
            x,y=scaled.width()/2,scaled.height()/2
            painter.drawLine(int(x-8),int(y),int(x+8),int(y))
            painter.drawLine(int(x),int(y-8),int(x),int(y+8))
            painter.setPen(QtGui.QPen(QtGui.QColor(245,245,245,95),1,QtCore.Qt.DashLine))
            painter.drawRect(int(scaled.width()*.175),int(scaled.height()*.175),
                             int(scaled.width()*.65),int(scaled.height()*.65))
            from .camera_view import recording_crop_bounds
            mode=self._camera_view_selected_mode(self.values())
            if mode is not None:
                x0,y0,x1,y1=recording_crop_bounds(aspect,mode,self.camera_view_extra_crop.value())
                sw,sh=scaled.width(),scaled.height()
                l,t,r,b=(int(sw*x0),int(sh*y0),int(sw*x1),int(sh*y1))
                shade=QtGui.QColor(8,13,21,155)
                painter.fillRect(0,0,sw,t,shade)
                painter.fillRect(0,b,sw,sh-b,shade)
                painter.fillRect(0,t,l,b-t,shade)
                painter.fillRect(r,t,sw-r,b-t,shade)
                painter.setPen(QtGui.QPen(QtGui.QColor(255,195,83),2))
                painter.drawRect(l,t,max(1,r-l-1),max(1,b-t-1))
        finally:painter.end()
        self.camera_view_picture.show_frame(QtGui.QPixmap.fromImage(scaled))

    def sweep_camera_view(self):
        p=self.values()
        if not p.FPVEnabled:
            self.camera_view_status.setText('Enable FPV before checking tilt angles.')
            return
        self._camera_view_busy(True)
        self.camera_view_status.setText('Checking candidate angles against frame / TPU and potential propeller sweep…')
        QtWidgets.QApplication.processEvents()
        try:
            from .camera_view import tilt_sweep
            tris,tree=self._camera_view_geometry(p)
            if p.CameraMountMode=='Fixed':angles=[p.CameraTilt]
            else:
                lo,hi=p.CameraTiltMin,p.CameraTiltMax
                angles=sorted(set([lo,hi]+[float(i) for i in range(0,61,5) if lo<=i<=hi]))
            include_props=self.camera_view_show_props.isChecked()
            samples=tilt_sweep(tris,tree,p,angles,include_props=include_props)
            clear=[item[0] for item in samples if item[1]<.25]
            best=min(samples,key=lambda item:(item[2],item[1],item[4] if include_props else 0))
            note=('No sampled angle was fully clear.' if not clear else
                  'Sampled angles without detectable frame obstruction: '+', '.join('%g°'%a for a in clear)+'.')
            prop_note=(' Potential prop sweep at this angle: %.1f%% of image, %.1f%% of centre (not solid obstruction).'
                       % (best[3],best[4])) if include_props else ''
            self.camera_view_status.setText(
                '%s\nBest sampled angle: %g degrees (%.1f%% total, %.1f%% centre frame/TPU obstruction).%s '
                'Tested %s. Mechanical tilt fit, true lens distortion and recording crop are NOT validated.' %
                (note,best[0],best[1],best[2],prop_note,', '.join('%g degrees'%a for a in angles)))
        except Exception as exc:
            self.camera_view_status.setText('Cannot check tilt range: '+str(exc))
        finally:self._camera_view_busy(False)

    def set_preview_mode(self,*_):
        if not hasattr(self,'preview'):return
        mode = self.preview_mode.currentData() or 'Overall'
        if mode != self.preview.view_mode:self.preview.reset_view()
        self.preview.view_mode=mode;self.preview.update()

    def update_preview_modes(self,p):
        # Most parameter edits do not change the set of available views.
        # Avoid clearing/refilling the Qt model and invalidating the preview
        # on every debounced refresh (particularly costly with many controls).
        from .airflow_gui import ROLE_LABELS
        options=[('Overall frame — top view','Overall'),
                 ('All parts — flat profiles','AllParts'),
                 ('All four arms — flat profiles','Arms')]
        options.extend((ROLE_LABELS.get(role,'LiPo pad'),role) for role in preview_roles(p))
        if getattr(self,'_preview_mode_options',None)==options:
            return
        current=self.preview_mode.currentData()
        self.preview_mode.blockSignals(True)
        try:
            self.preview_mode.clear()
            for caption,value in options:self.preview_mode.addItem(caption,value)
            index=self.preview_mode.findData(current)
            self.preview_mode.setCurrentIndex(max(0,index))
        finally:
            self.preview_mode.blockSignals(False)
        self._preview_mode_options=options
        self.set_preview_mode()

    def calculate_mass(self):
        if self.airflow.has_pending_changes():
            self.mass_signature=None;self.preview.mass_metrics=None;self.preview.update()
            self.mass_result.setText('Apply or discard pending airflow/outline edits before calculating weight / CG.')
            return
        try:
            from .geometry import build_shapes,invalidate_failed_build
            from .mass_properties import mass_properties
            p=self.values();QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            try:
                invalidate_failed_build(p);metrics=mass_properties(p,build_shapes(p))
            finally:QtWidgets.QApplication.restoreOverrideCursor()
            self.mass_signature=design_signature(p);self.preview.mass_metrics=metrics
            x,y,z=metrics['frame_cg_mm']
            text=f"Frame estimate: {metrics['frame_mass_g']:.2f} g • CG X {x:+.2f}, Y {y:+.2f}, Z {z:+.2f} mm\n"
            text+=f"Carbon {metrics['carbon_mass_g']:.2f} g • standoffs {metrics['standoff_mass_g']:.2f} g • pad {metrics['pad_mass_g']:.2f} g\n"
            if 'frame_plus_battery_mass_g' in metrics:
                a,b,c=metrics['frame_plus_battery_cg_mm']
                text+=f"Frame + reference LiPo: {metrics['frame_plus_battery_mass_g']:.2f} g • CG ({a:+.2f}, {b:+.2f}, {c:+.2f}) mm\n"
            if 'equipped_mass_g' in metrics:
                text+=f"Equipped (without LiPo): {metrics['equipped_mass_g']:.2f} g • CG {tuple(round(v,2) for v in metrics['equipped_cg_mm'])} mm\n"
            if 'loaded_mass_g' in metrics:
                text+=f"Equipped + LiPo: {metrics['loaded_mass_g']:.2f} g • CG {tuple(round(v,2) for v in metrics['loaded_cg_mm'])} mm\n"
            text+='Equipment uses editable nominal masses and size-based screw estimates. Verify actual build weight.'
            self.mass_result.setText(text);self.preview.update()
        except Exception as exc:
            self.mass_signature=None;self.preview.mass_metrics=None;self.mass_result.setText('Cannot calculate: '+str(exc))

    def jump_to_control(self, caption):
        name=self.search_locations.get(caption)
        if name is None:return
        special={'@front_height':('Standoffs',self.front_standoff_height),
                 '@fit_stack':('Stack',self.fit_stack_button),
                 '@fit_camera':('Camera cage',self.fit_camera_button),
                 '@airflow':('Airflow / outlines',self.airflow)}
        special.update(self.extra_search_targets)
        if name in special:title,control=special[name]
        else:title,control=tab_name(name),self.controls[name]
        category,scroll=self.section_pages[title]
        self.tabs.setCurrentWidget(self.category_tabs[category])
        self.category_tabs[category].setCurrentWidget(scroll)
        if title=='Camera cage' and (name in self.cage_control_pages or name=='@fit_camera'):
            subscroll=self.cage_control_pages.get(name,self.cage_control_pages['CameraPivotHeight'])
            self.cage_tabs.setCurrentWidget(subscroll);subscroll.ensureWidgetVisible(control,10,70)
        else:
            # Advanced optical controls are collapsed on this compact page.
            # Opening a matching finder result must reveal the actual widget.
            if name in ('CameraViewProfile','CameraViewAspect',
                        'CameraViewFOV','CameraViewPupilOffset'):
                self.camera_view_optics_toggle.setChecked(True)
            scroll.ensureWidgetVisible(control,10,70)
        control.setFocus(QtCore.Qt.OtherFocusReason)

    def find_control_enter(self):
        text=self.find_control.text().strip().casefold()
        matches=[caption for caption in self.search_locations if text and text in caption.casefold()]
        if len(matches)==1:self.jump_to_control(matches[0])

    def _on_battery_preset_selected(self, name):
        from .lipo_profiles import selected_profile
        profile = selected_profile(name)
        if profile is None:
            return
        self._applying_battery_preset = True
        try:
            for field, value in zip(('BatteryCells','BatteryWidth','BatteryLength','BatteryHeight','BatteryMass'),profile):
                self.controls[field].setValue(value)
        finally:
            self._applying_battery_preset = False
        self.queue_refresh()

    def _on_battery_measurement_edited(self, *_):
        if getattr(self, '_applying_battery_preset', False):
            return
        selector = self.controls['BatteryPreset']
        if selector.currentText() != 'Custom dimensions':
            selector.setCurrentText('Custom dimensions')
        self.queue_refresh()

    def values(self):
        values = {}
        for name, control in self.controls.items():
            values[name] = (control.currentData() if name=='StackSpacing' else int(control.value()) if name=='BatteryCells' else control.currentText() if name in ENUMERATIONS else
                            control.text() if name in STRINGS else
                            control.isChecked() if name in BOOLEANS else control.value())
        if getattr(self,'_bottom_body_reach_value',None) is not None:
            values['BottomBodyRearReach']=self._bottom_body_reach_value
        return Parameters.from_dict(values)

    def set_values(self, p, defer_refresh=False):
        p = Parameters.from_dict(p.to_dict())
        # Migrated arm-derived edges can contain more precision than the
        # displayed millimetres. Keep it until the user edits this dimension.
        self._bottom_body_reach_value=p.BottomBodyRearReach
        if p.StackPressNuts:self.field_labels['StackMountHeight'].setText(f'Stack support (automatic; actual {stack_reference_z(p)-plate_levels(p)["stack_deck_z"]:.2f} mm)')
        ratio = self.controls["LengthToWidth"]
        ratio.blockSignals(True)
        ratio.setRange(1.0 if p.Layout == "Squashed X" else .65, 1.8)
        ratio.blockSignals(False)
        for name, control in self.controls.items():
            control.blockSignals(True)
            if name=='StackSpacing':
                control.setCurrentIndex(control.findData(p.StackSpacing))
            elif name in ENUMERATIONS:
                control.setCurrentText(getattr(p, name))
            elif name in STRINGS:
                control.setText(getattr(p,name))
            elif name in BOOLEANS:
                control.setChecked(getattr(p,name))
            else:
                control.setValue(int(round(getattr(p,name))) if name in VENT_ROW_COUNTS else getattr(p,name))
            control.blockSignals(False)
        self._sync_interface_shape_choices()
        # Restore a newly loaded TPU-only shape after changing the combo's
        # available choices. Qt cannot select an item not yet in its list.
        shape=self.controls['FlexInterfaceShape']
        if shape.findText(p.FlexInterfaceShape)>=0:
            shape.blockSignals(True)
            shape.setCurrentText(p.FlexInterfaceShape)
            shape.blockSignals(False)
        self._populate_camera_profiles(p.VideoSystem, p.CameraPhysicalProfile)
        self.airflow.set_json(p.CutoutPatterns)
        self.timer.stop()
        if not defer_refresh:
            self.refresh()

    def _populate_camera_profiles(self, video_system, preferred=None):
        """Keep the physical-camera selector restricted to the active system.

        Rebuilding it blocks selection signals: changing the video system or
        loading a design must not overwrite custom dimensions/optical settings.
        """
        from .camera_profiles import camera_choices_for_system
        control=self.controls['CameraPhysicalProfile']
        selected=control.currentText() if preferred is None else preferred
        choices=camera_choices_for_system(video_system)
        control.blockSignals(True)
        try:
            control.clear()
            control.addItems(choices)
            control.setCurrentText(selected if selected in choices else 'Custom measurements')
        finally:
            control.blockSignals(False)

    def _on_video_system_selected(self, video_system):
        if video_system not in ('Analog','Digital'):
            return
        # O4 Pro equipment forces digital in Parameters.from_dict. Explicitly
        # leaving Digital must also release the O4 equipment lock.
        if video_system=='Analog' and self.controls['FPVSystemProfile'].currentText()=='DJI O4 Air Unit Pro':
            equipment=self.controls['FPVSystemProfile']
            equipment.blockSignals(True)
            equipment.setCurrentText('Custom camera / VTX')
            equipment.blockSignals(False)
        self._populate_camera_profiles(video_system)
        self._camera_view_follow_selected_physical()
        self.queue_refresh()

    def _camera_view_follow_selected_physical(self):
        # When a NEW camera is explicitly chosen, any manual lens selection,
        # FOV, aspect or pupil calibration from the PREVIOUS camera must not
        # silently carry over and cause an incorrect preview. A user can still
        # deliberately override these values after selecting a new camera.
        for name,value in (
            ('CameraViewProfile','Follow selected camera'),
            ('CameraViewAspect','Camera default'),
            ('CameraViewFOV',0.),
            ('CameraViewPupilOffset',0.),
        ):
            control=self.controls[name]
            control.blockSignals(True)
            if isinstance(value,str):control.setCurrentText(value)
            else:control.setValue(value)
            control.blockSignals(False)

    def _on_camera_physical_profile_selected(self, profile):
        # Explicit selection only; preset loading blocks signals, preserving
        # dimensions in old saved designs and user-defined custom cameras.
        from .camera_profiles import get_camera_spec
        spec=get_camera_spec(profile)
        self._camera_view_follow_selected_physical()
        if spec is None:
            # Leaving DJI through Custom must also release its dedicated
            # equipment lock. Otherwise the editor continues to treat the
            # new custom dimensions as O4 and rejects their mounting pattern.
            equipment=self.controls['FPVSystemProfile']
            equipment.blockSignals(True)
            equipment.setCurrentText('Custom camera / VTX')
            equipment.blockSignals(False)
            # Custom cameras infer analog/digital optical presets from the
            # user's actual selected video system and measured dimensions.
            self.queue_refresh()
            return
        tilt=self.controls['CameraTilt'].value()
        dji_pro=profile=='DJI O4 Air Unit Pro'
        updates={
            'FPVEnabled':True,
            'VideoSystem':'Digital' if spec.digital else 'Analog',
            'FPVSystemProfile':profile if dji_pro else 'Custom camera / VTX',
            'CameraWidth':spec.width,'CameraHeight':spec.height,
            'CameraBodyDepth':spec.housing_depth,
            'CameraLensProjection':spec.lens_projection,
            'CameraSideBoltSpacing':spec.screw_spacing,
            'CameraSideScrewRearInset':spec.rear_screw_inset,
            'CameraSideHoleDiameter':2.2,
            'CameraReferenceStyle':'Automatic' if dji_pro or profile in ('Generic Analog 28 mm','Generic Digital 20 mm') else profile,
            'DetailedCameraReference':True,
        }
        if dji_pro:
            # Preserve the dedicated O4 camera, camera mount and air-unit profile.
            updates.update(VTXWidth=33.5,VTXLength=33.5,VTXHeight=13.,
                           VTXPattern='25.5 x 25.5 mm',
                           VTX25HoleDiameter=2.2,VTX20HoleDiameter=2.2)
            if abs(self.controls['CameraCageEdgeWeb'].value()-4.)<1e-6:
                updates['CameraCageEdgeWeb']=2.
        if spec.screw_spacing==0:
            # A single M2 side screw cannot form a two-point fixed tilt mount.
            updates.update(CameraMountMode='Variable',CameraTiltMin=0.,
                           CameraTiltMax=max(45.,tilt),CameraTiltMechanism='Upper pivot + lower arc')
        for key,value in updates.items():
            ctrl=self.controls.get(key)
            if ctrl is None:continue
            ctrl.blockSignals(True)
            if isinstance(value,bool):ctrl.setChecked(value)
            elif isinstance(value,str):ctrl.setCurrentText(value)
            else:ctrl.setValue(value)
            ctrl.blockSignals(False)
        self.queue_refresh()

    def _on_fpv_profile_selected(self, profile):
        if profile in ('DJI O4 Air Unit Pro','DJI O4 Air Unit','DJI O3 Air Unit'):
            # DJI is chosen through FPV System rather than the non-DJI
            # physical camera dropdown. Follow that choice automatically too.
            self._camera_view_follow_selected_physical()
        if profile == 'DJI O4 Air Unit Pro':
            # Legacy FPV equipment selector still works; use the same camera list.
            video=self.controls['VideoSystem']
            video.setCurrentText('Digital')
            control_profile=self.controls['CameraPhysicalProfile']
            control_profile.blockSignals(True)
            control_profile.setCurrentText('DJI O4 Air Unit Pro')
            control_profile.blockSignals(False)
            control = self.controls['CameraCageEdgeWeb']
            if abs(control.value() - 4.0) < 1e-6:
                control.setValue(2.0)
        self.queue_refresh()

    def _airflow_geometry_changed(self, encoded):
        """Commit validated cutout JSON without an unrelated whole-frame refresh.

        The AirflowEditor already validates profile syntax and R0.5 geometry
        before publishing. Expensive overall validation and native CAD checks
        remain on Create / Update and the explicit CAD check button.
        """
        field=self.controls['CutoutPatterns']
        if field.text()==encoded:
            return
        previous=field.blockSignals(True)
        try:
            field.setText(encoded)
        finally:
            field.blockSignals(previous)
        # Other controls may have a pending refresh. Do not overwrite that
        # refresh with an outdated snapshot; it will read the new JSON.
        if self.timer.isActive():
            return
        old=getattr(self.preview,'params',None)
        if old is not None:
            current=replace(old,CutoutPatterns=encoded)
            self.preview.params=current
            self.airflow.preview.set_frame_parameters(current)
            # The main preview is covered by the Airflow workspace and need
            # not record any geometry until the user switches to it.
            if self.preview.isVisible():
                self.preview.update()
        self.mass_signature=None
        self.preview.mass_metrics=None
        self.mass_result.setText('Weight / CG needs recalculation after changing airflow cuts.')

    def _airflow_metadata_changed(self, encoded):
        """Persist Keep flags without rebuilding unchanged plate geometry."""
        field=self.controls['CutoutPatterns']
        previous=field.blockSignals(True)
        try:
            field.setText(encoded)
        finally:
            field.blockSignals(previous)
        # No validation or redraw needed: the geometry is identical.

    def queue_refresh(self, *args):
        if hasattr(self, "timer"):
            self.timer.start()

    def custom_bolts_from_spacing(self,*args):
        p=self.values()
        (x1,y1),(x2,y2)=frame_bolt_offsets(replace(p,RootBoltLayout='Along arm'))
        self.set_values(replace(p,RootBoltLayout='Custom coordinates',
                               RootBolt1X=x1,RootBolt1Y=y1,RootBolt2X=x2,RootBolt2Y=y2))

    def set_front_standoff_height(self, height):
        p = self.values()
        difference = standoff_heights(p)["Front"] - p.StandoffHeight
        self.controls["StandoffHeight"].setValue(height - difference)
        self.queue_refresh()

    def fit_camera(self, *args):
        self.controls['CameraPivotMode'].setCurrentText('Automatic centre')
        self.controls['CameraPositionMode'].setCurrentText('Automatic centre')
        p=self.values()
        if p.FPVSystemProfile=='DJI O4 Air Unit Pro':
            # A lens/case axis-aligned box is NOT a standoff-height request.
            # An O4 may fit through the existing front plate cutouts, and
            # three-plate designs have the full bottom-to-top cavity.
            from .fpv import camera_angles,camera_centre_offset,camera_screw_offsets
            travels=[camera_centre_offset(p,a)[1]+z for a in camera_angles(p)
                     for y,z in camera_screw_offsets(p,a)]
            # Raise the deck only when the *screw pattern itself* cannot fit,
            # not just because the lens traverses the plane of a front cutout.
            required=max(travels)-min(travels)+p.CameraSideHoleDiameter+2*p.CameraCageEdgeWeb+.2
        else:
            low,high=camera_vertical_limits(p)
            required=2*max(-low,high)+.4
        stand=required-(camera_cage_height(p)-p.StandoffHeight)
        if stand>p.StandoffHeight+1e-6:
            target=next((v for v in COMMON_STANDOFF_HEIGHTS if v>=stand),math.ceil(stand*2)/2)
            self.controls['StandoffHeight'].setValue(target)
        # Fit the O4 Pro's *real* side-screw and moving insert footprint into
        # the available side-wall area.  A three-plate design may have 30 mm
        # between plates even when its rear standoffs are 22 mm long.  Never
        # enlarge those standoffs merely because the lens spans a plate plane.
        # This is an explicit Fit camera action, not an implicit CAD change.
        p=self.values()
        if p.FPVSystemProfile=='DJI O4 Air Unit Pro' and p.FlexCameraMode!='Hard mount':
            from .fpv import suggest_o4_soft_fit
            proposed=suggest_o4_soft_fit(p)
            for key,value in proposed.items():
                control=self.controls.get(key)
                if control is not None and abs(control.value()-value)>1e-6:
                    control.setValue(value)
            if proposed:
                p=self.values()
        # A saved DJI O4 profile may leave a 12-mm generic soft insert while
        # its 16-mm screw pitch is still selected. Resizing only the cosmetic
        # camera won't fix that real mounting incompatibility.
        if p.FPVSystemProfile!='DJI O4 Air Unit Pro' and p.FlexCameraMode!='Hard mount':
            from .fpv import camera_angles,camera_centre_offset,camera_screw_offsets
            dyz=[(y+dy,z+dz) for a in camera_angles(p)
                 for dy,dz in (camera_centre_offset(p,a),)
                 for y,z in camera_screw_offsets(p,a)]
            extra=p.CameraSideHoleDiameter/2+p.MinimumWeb+.25
            required_w=2*(max(abs(y) for y,z in dyz)+extra)
            required_h=2*(max(abs(z) for y,z in dyz)+extra)
            wkey,hkey=(('FlexInsertWidth','FlexInsertHeight') if p.FlexCameraMode=='Captured inserts'
                       else ('FlexPadWidth','FlexPadHeight'))
            for key,needed in ((wkey,required_w),(hkey,required_h)):
                control=self.controls[key]
                if control.value()+1e-7<needed:
                    control.setValue(math.ceil(needed*2)/2)
        self.queue_refresh()

    def fit_flexible(self,*args):
        # Backward-compatible refresh hook; rear mounts follow current posts.
        self.queue_refresh()

    def fit_stack(self,*args):
        p=self.values()
        from .hardware_layout import SIZES,metric_size
        nutheight=SIZES[metric_size(p.StackHoleDiameter)][5] if p.StackPressNuts else 0.
        needed=p.StandoffHeight+stack_reference_z(p)+p.StackHeight+nutheight+.2-plate_levels(p)['top_z']
        if needed>p.StandoffHeight:
            target=next((h for h in COMMON_STANDOFF_HEIGHTS if h>=needed),math.ceil(needed*2)/2)
            self.controls['StandoffHeight'].setValue(target)
        self.queue_refresh()

    def fit_shared_mounts(self,*args):
        p=self.values()
        shared=[s for s in standoff_layouts(p) if s['shared_arm']]
        if shared:
            width=2*(max(abs(s['point'][0]) for s in shared)+p.StandoffDiameter/2+p.MinimumWeb+.25)
            length=2*(max(abs(s['point'][1]) for s in shared)+p.StandoffDiameter/2+p.MinimumWeb+p.CornerRadius)
            self.controls['TopWidth'].setValue(max(p.TopWidth,p.BodyWidth,math.ceil(width*2)/2))
            self.controls['TopLength'].setValue(max(p.TopLength,math.ceil(length*2)/2))
        self.queue_refresh()

    def _sync_interface_shape_choices(self):
        """Use independent TPU shape choices without altering carbon options."""
        from .tpu_isolation_layout import TPU_INTERFACE_SHAPES, CARBON_INTERFACE_SHAPES
        combo=self.controls.get('FlexInterfaceShape')
        if combo is None:return
        style=self.controls['CameraCageStyle'].currentText()
        choices=TPU_INTERFACE_SHAPES if style=='TPU cage' else CARBON_INTERFACE_SHAPES
        current=combo.currentText()
        selected=current if current in choices else 'Rounded rectangle'
        if combo.count()!=len(choices) or any(combo.itemText(i)!=v for i,v in enumerate(choices)):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(choices)
            combo.setCurrentText(selected)
            combo.blockSignals(False)
        elif selected!=current:
            combo.blockSignals(True)
            combo.setCurrentText(selected)
            combo.blockSignals(False)

    def refresh(self):
        # A refresh toggles hundreds of controls and recomputes text, previews,
        # and section visibility. Batch painting to avoid showing half-updated
        # panels and unnecessary Windows/Qt widget repaints.
        self.setUpdatesEnabled(False)
        try:
            return self._refresh_impl()
        finally:
            self.setUpdatesEnabled(True)

    def _refresh_impl(self):
        self._sync_interface_shape_choices()
        p = self.values()
        for control in self.controls.values():control.setEnabled(True)
        for name in ('StackSpacing','StackHoleDiameter','StackHeight','StackMountHeight'):self.field_labels[name].setText(label(name))
        if p.StackPressNuts:self.field_labels['StackMountHeight'].setText(f'Stack support (automatic; actual {stack_reference_z(p)-plate_levels(p)["stack_deck_z"]:.2f} mm)')
        self.controls["StackMountHeight"].setEnabled(not p.StackPressNuts)
        ratio = self.controls["LengthToWidth"]
        ratio.blockSignals(True)
        ratio.setRange(1.0 if p.Layout == "Squashed X" else .65, 1.8)
        ratio.setValue(p.LengthToWidth)
        ratio.blockSignals(False)
        self.field_labels["LengthToWidth"].setText("Width / front–rear spacing" if p.Layout == "Squashed X" else "Length / rear motor span")
        self.controls["LengthToWidth"].setEnabled(p.Layout != "True X")
        self.controls["FrontSpread"].setEnabled(p.Layout == "Deadcat")
        self.controls['RearArmExtension'].setEnabled(p.Layout=='Deadcat')
        extended=p.Layout=='Deadcat' and p.RearArmExtension>0
        self.field_labels['Wheelbase'].setText('Base diagonal wheelbase' if extended else 'Diagonal wheelbase')
        self.field_labels['FrontSpread'].setText('Base front / rear motor span' if extended else 'Front / rear motor span')
        if extended:self.field_labels['LengthToWidth'].setText('Base length / rear motor span')
        for name in ("ClampThickness", "MidFrontReach", "MidRearReach",'MidReachMode','MidCentreWidth','BottomBodyRearReach'):
            self.controls[name].setEnabled(three_plate(p))
        self.controls['BottomFrontExtension'].setEnabled(three_plate(p) and p.BottomReachMode=='Automatic')
        self.controls['BodyLength'].setEnabled(p.BottomReachMode=='Automatic')
        self.controls['TopLength'].setEnabled(p.TopReachMode=='Automatic')
        for prefix in ('Bottom','Top'):
            for suffix in ('FrontReach','RearReach'):
                self.controls[prefix+suffix].setEnabled(getattr(p,prefix+'ReachMode')=='Custom')
        self.controls['MotorPadCornerRadius'].setEnabled(motor_corner_control(p))
        from .motor_pads import NEW_MOTOR_PAD_SHAPES
        new_pad=p.MotorPadShape in NEW_MOTOR_PAD_SHAPES
        self.controls['ArmProfileAmount'].setEnabled(p.ArmBeamShape!='Straight')
        self.controls['MidEdgeFillet'].setEnabled(three_plate(p))
        for flag,field,active in (('ArmFilletOpenings','ArmEdgeFillet',True),('BottomFilletOpenings','BottomEdgeFillet',True),('TopFilletOpenings','TopEdgeFillet',True),('MidFilletOpenings','MidEdgeFillet',three_plate(p)),('ClampFilletOpenings','ClampEdgeFillet',arm_braces(p) or underside_clamp_active(p))):self.controls[flag].setEnabled(active and getattr(p,field)>0)
        self.controls['ClampEdgeFillet'].setEnabled(arm_braces(p) or underside_clamp_active(p))
        self.controls['MidPlateShape'].setEnabled(three_plate(p))
        self.controls['ClampPlateShape'].setEnabled(arm_braces(p) or underside_clamp_active(p))
        for prefix,active in (('BottomRear',not three_plate(p)),('MidRear',three_plate(p)),('TopRear',True)):
            shape=getattr(p,prefix+'Shape')
            self.controls[prefix+'Shape'].setEnabled(active)
            self.controls[prefix+'Depth'].setEnabled(active and shape!='Straight')
            self.controls[prefix+'TipWidth'].setEnabled(active and shape in ('Flat-tip end','Swept shoulders','Stepped end','Flat recess','Round U recess','Cable channel','Dual cable channels','Split tail','Stepped electronics tail'))
        from .bottom_nose import CAMERA_FRONT_SHAPES
        camera_front=p.TopFrontShape in CAMERA_FRONT_SHAPES
        self.controls['TopFrontDepth'].setEnabled(p.TopFrontShape!='Straight')
        self.controls['TopFrontTipWidth'].setEnabled(p.TopFrontShape in ('Flat-tip nose','Swept shoulders','Stepped nose','Flat recess','Round U recess'))
        for name in ('TopFrontRecessWidth','TopFrontClearance','TopFrontSetback'):self.controls[name].setEnabled(camera_front)
        self.controls['TopFrontClearance'].setEnabled(camera_front and p.TopFrontRecessWidth==0)
        self.controls['BottomNoseDepth'].setEnabled(p.BottomNoseShape!='Straight')
        self.controls['BottomNoseTipWidth'].setEnabled(p.BottomNoseShape in ('Flat-tip nose','Swept shoulders','Stepped nose','Flat recess','Round U recess'))
        self.controls['PlateEndWidth'].setEnabled(any(getattr(p,k) in ('Tapered front','Tapered rear','Hexagonal','Faceted shield') for k in ('BottomPlateShape','MidPlateShape','TopPlateShape','ClampPlateShape')))
        self.controls['MotorPadBlendRadius'].setEnabled(abs(p.MotorPadRotation)>1e-8)
        for name in ('MotorPadNeckLength','MotorPadRelief','MotorPadReliefWidth','MotorPadReliefLength'):self.controls[name].setEnabled(new_pad and (name in ('MotorPadNeckLength','MotorPadRelief') or p.MotorPadRelief!='None'))
        self.controls['MotorPadReliefLength'].setEnabled(new_pad and p.MotorPadRelief in ('Neck slot','Twin neck slots'))
        for name in ('MotorTipLength','MotorTipSlotEnabled'):self.controls[name].setEnabled(extended_motor_pad(p) and (name=='MotorTipLength' or not new_pad))
        for name in ('MotorTipSlotWidth','MotorTipSlotLength'):self.controls[name].setEnabled(extended_motor_pad(p) and p.MotorTipSlotEnabled and not new_pad)
        bottom_rect=bottom_plate_path(p).boundingRect()
        mid_rect=mid_plate_path(p).boundingRect() if three_plate(p) else None
        self.plate_info.setText(f'Actual bottom bounds (rear → front Y): {bottom_rect.top():g} → {bottom_rect.bottom():g} mm. '+
                               (f'Body rear Y = {bottom_body_bounds(p)[0]:g} mm (stack − reach). Rear tabs follow the arms.' if three_plate(p) else 'Custom reaches cap the outline.'))
        self.mid_plate_info.setText((f'Actual mid bounds (rear → front Y): {mid_rect.top():g} → {mid_rect.bottom():g} mm. Front tabs follow the arms.' if mid_rect else 'The mid plate is used only in three-plate designs. Choose Plate design on Frame > Layout.'))
        self.top_plate_info.setText(f'Actual top bounds (rear → front Y): {top_bounds(p)[0]:g} → {top_bounds(p)[1]:g} mm. Custom reaches cap the outline.')
        self.controls['TwoPlateArmPosition'].setEnabled(not three_plate(p))
        self.controls['ArmBracesEnabled'].setEnabled(not three_plate(p))
        self.controls['ArmBraceThickness'].setEnabled(upper_clamp_active(p))
        self.controls['UndersideClampThickness'].setEnabled(underside_clamp_active(p))
        self.controls['KeystoneEnabled'].setEnabled(three_plate(p) or arm_braces(p))
        self.controls['KeystoneClearance'].setEnabled(keystone_active(p))
        self.controls['KeystoneShape'].setEnabled(fitted_roots(p) and keystone_active(p))
        self.controls['ArmJointClearance'].setEnabled(fitted_roots(p))
        for name in ('ArmRootLength','ArmRootTaperLength'):self.controls[name].setEnabled(widened_roots(p))
        self.controls['RootBoltSpacing'].setEnabled(p.RootBoltLayout=='Along arm')
        for name in ROOT_BOLT_COORDINATES:self.controls[name].setEnabled(p.RootBoltLayout=='Custom coordinates')
        for name in ('KeystoneWidth','KeystoneLength','KeystoneFillet'):
            self.controls[name].setEnabled(fitted_roots(p) and keystone_active(p))
        key_note=''
        if fitted_roots(p) and keystone_active(p):
            try:
                key_note=f' Compact key: {p.KeystoneWidth:g} × {p.KeystoneLength:g} mm, centre Y {compact_key_centre(arm_layouts(p))[1]:g} mm.'
            except ValueError:
                key_note=' Adjust the root centres to locate the compact key.'
        self.root_fit_info.setText(
            f'Root width {root_width(p):g} mm; beam width {p.ArmWidth:g} mm. '+
            ('Custom bolts use frame X/Y, relative to the front-right root: +X right, +Y front. Mirrored on left/rear arms. Inner/outer shared mounts follow bolts 1/2. ' if p.RootBoltLayout=='Custom coordinates' else '')+(
            f'Fitted root joints: {p.ArmJointClearance:g} mm total arm gap. Move the root centres inward and extend the tails until the joints meet. Dashed lines show the joints beneath the plates.'+
            key_note
            if fitted_roots(p) else 'Independent roots retain their rounded tails and need space between the arms. Select Fitted miters to let the roots meet along trimmed joint lines.'))
        self.controls['ClampCentreWidth'].setEnabled(arm_braces(p))
        self.controls['ArmRootsFollowCentre'].setEnabled(p.BottomCentreWidth>p.BodyWidth)
        for name in ('KeystoneRetainerDiameter','KeystoneRetainerHeadDiameter','KeystoneRetainerSpacing'):
            self.controls[name].setEnabled(bool(keystone_retainers(p)))
        self.controls['StackAccessDiameter'].setEnabled(three_plate(p) or arm_braces(p) or p.ArmRootReliefsEnabled)
        self.controls['ArmRootReliefShape'].setEnabled(p.ArmRootReliefsEnabled)
        self.controls['StrapOpeningStyle'].setEnabled(p.StrapSlotsEnabled)
        for name in ('StrapSlotLength','StrapCount'):
            self.controls[name].setEnabled(p.StrapSlotsEnabled and p.StrapOpeningStyle!='None')
        self.controls['StrapSingleY'].setEnabled(p.StrapSlotsEnabled and p.StrapCount=='1 strap')
        self.controls['StrapOffsetY'].setEnabled(p.StrapSlotsEnabled and p.StrapCount=='2 straps')
        for name in ('StrapSlotWidth','StrapEdgeInset'):
            self.controls[name].setEnabled(p.StrapSlotsEnabled and p.StrapOpeningStyle=='Slots')
        self.controls['StrapNotchDepth'].setEnabled(p.StrapSlotsEnabled and p.StrapOpeningStyle=='Outline cutouts')
        for name in ('StackUSBFace','StackUSBOffsetY'):
            self.controls[name].setEnabled(p.ShowReferences and p.DetailedStackReference)
        for index in (3, 4):
            for suffix in ("Y", "Width"):
                self.controls[f"StandoffPair{index}{suffix}"].setEnabled(standoff_pair_count(p) >= index and getattr(p,f'StandoffPair{index}Mount')=='Custom position')
            self.controls[f'StandoffPair{index}Mount'].setEnabled(standoff_pair_count(p)>=index)
        for name in ('StandoffWidth','StandoffLength'):
            self.controls[name].setEnabled(p.StandoffFrontMount=='Custom position' or p.StandoffRearMount=='Custom position')
        for name in FPV_FIELDS-{'FPVEnabled'}:
            self.controls[name].setEnabled(p.FPVEnabled)
        from .flex import soft_camera
        from .flex_options import FLEX_OPTIONS
        for name in FLEX_OPTIONS:
            enabled=True
            if name.startswith('FlexBumper'):
                full=p.FlexBumperVariant=='Integrated camera cage bumper'
                enabled=p.FlexFrontBumper and (name not in ('FlexBumperShape','FlexBumperWidth','FlexBumperTipWidth','FlexBumperRecess','FlexBumperLipReach') or not full)
                enabled=enabled and (name not in ('FlexBumperProjection','FlexBumperWidth','FlexBumperTipWidth','FlexBumperRecess') or full or p.FlexBumperShape!='Follow bottom plate')
            if name=='FlexBumperTipWidth':enabled=enabled and p.FlexBumperShape in ('Chamfered shoe','Swept-shoulder shoe','Flat-tip shoe','Centre-crown shoe','Recessed-centre shoe','Stepped shoe','Capsule shoe','Bullnose shoe','Arrowhead shoe','V-recess shoe','Twin-shoulder shoe','Clipped-corner shoe')
            if name=='FlexBumperRecess':enabled=enabled and p.FlexBumperShape in ('Twin-lobe shoe','Recessed-centre shoe','V-recess shoe','Twin-shoulder shoe')
            elif name.startswith('FlexELRS') and name!='FlexELRSEnabled':enabled=p.FlexELRSEnabled
            elif name.startswith('FlexAntenna'):enabled=p.FlexRearAntenna and (name!='FlexAntennaSpacing' or p.FlexAntennaCount=='2 antennas')
            elif name.startswith('FlexProtector'):enabled=p.FlexMotorProtectors
            elif name.startswith('FlexGuardStrap'):enabled=p.FlexSideGuards and (name=='FlexGuardStraps' or p.FlexGuardStraps)
            elif name.startswith('FlexGuard'):enabled=p.FlexSideGuards
            elif name=='FlexInterfaceShape':enabled=soft_camera(p)
            elif name.startswith(('FlexPad','FlexInsert')):enabled=soft_camera(p) and (not name.startswith('FlexInsert') or p.FlexCameraMode=='Captured inserts')
            elif name=='FlexCameraMode':enabled=p.FPVEnabled
            self.controls[name].setEnabled(enabled)
        self.controls['FlexAntennaGuardGap'].setEnabled(p.FlexRearAntenna and p.FlexSideGuards)
        self.controls['FlexELRSGuardGap'].setEnabled(p.FlexELRSEnabled and p.FlexSideGuards)
        self.controls['FlexELRSFit'].setEnabled(p.FlexELRSEnabled and p.FlexELRSStandoffBore==0)
        self.controls['FlexAntennaHolderStyle'].setEnabled(p.FlexRearAntenna and p.FlexAntennaConnector in ('u.FL','MMCX'))
        self.controls['FlexAntennaRetainingLip'].setEnabled(p.FlexRearAntenna and p.FlexAntennaConnector in ('u.FL','MMCX') and p.FlexAntennaHolderStyle=='Side-entry clip')
        bulkhead=p.FlexAntennaConnector in ('SMA','RP-SMA')
        self.controls['FlexAntennaBulkheadThickness'].setEnabled(p.FlexRearAntenna and bulkhead)
        self.controls['FlexAntennaSocketLength'].setEnabled(p.FlexRearAntenna and not bulkhead)
        self.field_labels['FlexAntennaBore'].setText('Pigtail mounting hole' if bulkhead else 'Antenna bore diameter')
        self.controls['FlexAntennaFit'].setEnabled(p.FlexRearAntenna and p.FlexAntennaStandoffBore==0)
        for name in ('DetailedMotorReferences','DetailedPropReferences','DetailedStackReference','DetailedCameraReference','DetailedVTXReference','DetailedBatteryReference'):
            self.controls[name].setEnabled(p.ShowReferences and (name not in ('DetailedCameraReference','DetailedVTXReference') or p.FPVEnabled) and (name!='DetailedBatteryReference' or p.BatteryReferenceEnabled))
        self.controls['CameraReferenceStyle'].setEnabled(p.ShowReferences and p.FPVEnabled and p.DetailedCameraReference and p.FPVSystemProfile!='DJI O4 Air Unit Pro')
        from .camera_cages import screw_cage
        cage=p.FPVEnabled
        for name in ('CameraCageFrontShape','CameraCageRearShape','CameraCageProfileDepth','CameraCageFrontReach','CameraCageRearReach'):
            self.controls[name].setEnabled(cage and p.CameraCageStyle!='TPU cage')
        self.controls['CameraCageEdgeWeb'].setEnabled(cage)
        for name in ('CameraTPUAttachment','CameraTPUBridge'):self.controls[name].setEnabled(p.FPVEnabled and p.CameraCageStyle=='TPU cage')
        for name in ('CameraTPUScrewBore','CameraTPUScrewClearance'):self.controls[name].setEnabled(p.FPVEnabled and screw_cage(p))
        self.controls['CameraBracketThickness'].setEnabled(p.FPVEnabled)
        self.controls['CameraAutoExtend'].setEnabled(p.FPVEnabled)
        for name in ('ArmTipBumperReach','ArmTipBumperWidth','ArmTipBumperDirection','ArmTipBumperCutout','ArmTipBumperCutoutWall'):self.controls[name].setEnabled(p.ArmTipBumperStyle!='Disabled')
        full_bumper=p.FlexFrontBumper and p.FPVEnabled and p.FlexBumperVariant=='Integrated camera cage bumper'
        self.controls['FlexBumperVariant'].setEnabled(p.FlexFrontBumper and p.CameraCageStyle!='TPU cage')
        self.controls['FlexBumperCameraCover'].setEnabled(False)  # hidden legacy field
        for name in ('FlexBumperCameraGripDepth','FlexBumperCameraHeight','FlexBumperCameraFrontProjection','FlexBumperCameraBlendReach'):
            self.controls[name].setEnabled(full_bumper)
        self.controls['FlexProtectorBumperSleeve'].setEnabled(p.ArmTipBumperStyle!='Disabled' and p.FlexMotorProtectors)
        self.controls['PropReferenceColour'].setEnabled(p.ShowReferences and p.DetailedPropReferences)
        self.controls['VTXReferenceStyle'].setEnabled(p.ShowReferences and p.FPVEnabled and p.DetailedVTXReference)
        self.controls['PropReferenceHeight'].setEnabled(not p.DetailedPropReferences)
        self.controls['ShowVTXAntennaReference'].setEnabled(p.ShowReferences and p.FlexRearAntenna)
        self.controls['ShowELRSTReference'].setEnabled(p.ShowReferences and p.FlexELRSEnabled)
        show_vtx=p.ShowReferences and p.FlexRearAntenna and p.ShowVTXAntennaReference
        show_elrs=p.ShowReferences and p.FlexELRSEnabled and p.ShowELRSTReference
        self.controls['VTXAntennaReferencePreset'].setEnabled(show_vtx)
        self.controls['VTXAntennaHeadColour'].setEnabled(show_vtx)
        for field in ('VTXAntennaReferenceLength','VTXAntennaReferenceDiameter'):
            self.controls[field].setEnabled(show_vtx and p.VTXAntennaReferencePreset=='Custom')
        self.controls['ELRSTReferencePreset'].setEnabled(show_elrs)
        self.controls['ELRSTReferenceSpan'].setEnabled(show_elrs and p.ELRSTReferencePreset=='Custom')
        for name in ('FlexGuardStrapY1','FlexGuardStrapY2'):
            self.controls[name].setEnabled(p.FlexSideGuards and p.FlexGuardStraps and not p.FlexGuardStrapAuto and (name!='FlexGuardStrapY2' or p.FlexGuardStrapCount=='2 straps'))
        self.controls['CameraTabCutterDiameter'].setEnabled(p.FPVEnabled and p.CameraTabReliefs)
        self.controls['CameraSideClearance'].setEnabled(p.FPVEnabled and (p.CameraCageStyle=='TPU cage' or not soft_camera(p)))
        self.controls['FlexPadWidth'].setEnabled(soft_camera(p) and p.FlexCameraMode=='Compression pads')
        self.controls['FlexPadHeight'].setEnabled(soft_camera(p) and p.FlexCameraMode=='Compression pads')
        tpu_cage=p.FPVEnabled and p.CameraCageStyle=='TPU cage'
        for name in ('CameraTPUScrewBore','CameraTPUInsertDepth','CameraTPUBossWall','CameraTPUScrewClearance','CameraTPUBridge'):
            self.controls[name].setEnabled(tpu_cage)
        for name in ('CameraTabLength','CameraTabClearance','CameraTabReliefs','CameraTabCutterDiameter'):
            self.controls[name].setEnabled(p.FPVEnabled and not tpu_cage)
        for name in ('FlexFrontBumper',)+tuple(n for n in self.controls if n.startswith('FlexBumper')):
            if tpu_cage:self.controls[name].setEnabled(False)
        self.controls['FlexFrontBumper'].blockSignals(True);self.controls['FlexFrontBumper'].setChecked(p.FlexFrontBumper);self.controls['FlexFrontBumper'].blockSignals(False)
        for name in ('CameraTPUBumperReach','CameraTPUBumperWidth','CameraTPUBumperToe'):
            self.controls[name].setEnabled(False)
        for key,visible in (('CameraTabLength',not tpu_cage),('CameraTPUScrewBore',tpu_cage),('CameraCageFrontShape',not tpu_cage)):
            page=self.cage_control_pages[key];self.cage_tabs.setTabVisible(self.cage_tabs.indexOf(page),visible)
        bumper_page=self.cage_control_pages['CameraTPUBumperReach']
        self.cage_tabs.setTabVisible(self.cage_tabs.indexOf(bumper_page),False)
        o4=p.FPVSystemProfile=='DJI O4 Air Unit Pro'
        self.controls['CameraTPUFlushInserts'].setEnabled(tpu_cage and p.FlexCameraMode=='Captured inserts' and p.FlexInsertLipSide in ('Outside only','Both sides'))
        self.controls['CameraCarbonFlushInserts'].setEnabled(p.FPVEnabled and p.CameraCageStyle=='Carbon side plates' and p.FlexCameraMode=='Captured inserts' and p.FlexInsertLipSide in ('Outside only','Both sides'))
        self.controls['O4InsertDiameter'].setEnabled(p.FPVEnabled and o4 and p.FlexCameraMode=='Captured inserts')
        self.controls['O4PadDiameter'].setEnabled(p.FPVEnabled and o4 and p.FlexCameraMode=='Compression pads')
        self.controls['CameraTPUInnerReach'].setEnabled(False)
        self.controls['CameraTPUBridge'].setEnabled(tpu_cage)
        for name in ('CameraTPUBottomRearReach','CameraTPUTopRearReach','CameraTPUFrontBridgeRearReach','CameraTPUFrontBridgeHeight','CameraTPUFrontBridgeBlend'):
            self.controls[name].setEnabled(tpu_cage)
        self.controls['CameraTPUClampBottom'].setEnabled(False)
        for name in ('CameraTPUClampFit','CameraTPUClampWall'):
            self.controls[name].setEnabled(tpu_cage and p.CameraTPUBumper and p.CameraTPUClampBottom)
        if o4:
            for name in ('CameraWidth','CameraHeight','CameraBodyDepth','CameraSideBoltSpacing','CameraSideHoleDiameter','CameraSideScrewRearInset','CameraLensProjection','VTXWidth','VTXLength','VTXHeight','VTX25HoleDiameter','VTX20HoleDiameter'):
                control=self.controls[name];control.blockSignals(True);control.setValue(getattr(p,name));control.blockSignals(False);control.setEnabled(False)
            self.controls['DetailedCameraReference'].blockSignals(True);self.controls['DetailedCameraReference'].setChecked(True);self.controls['DetailedCameraReference'].blockSignals(False);self.controls['DetailedCameraReference'].setEnabled(False)
            for name in ('VideoSystem','VTXPattern'):
                control=self.controls[name];control.blockSignals(True);control.setCurrentText(getattr(p,name));control.blockSignals(False);control.setEnabled(False)
            for name in ('FlexInsertWidth','FlexInsertHeight','FlexInsertCornerRadius','FlexInterfaceShape','FlexPadWidth','FlexPadHeight'):
                self.controls[name].setEnabled(False)

        vented=p.FlexSideGuards and p.FlexGuardStyle=='Vented'
        for name in ('FlexGuardVTXVents','FlexGuardFCVents','FlexGuardVentBoundaryOffset'):self.controls[name].setEnabled(vented)
        for name in ('FlexGuardVentShape','FlexGuardVentWidth','FlexGuardVentWeb','FlexGuardSlotHeight','FlexGuardSlotCount','FlexGuardVTXVentRearInset','FlexGuardVTXVentFrontInset','FlexGuardVTXVentZOffset'):self.controls[name].setEnabled(vented and p.FlexGuardVTXVents)
        for name in ('FlexGuardFCVentShape','FlexGuardFCVentWidth','FlexGuardFCVentWeb','FlexGuardFCSlotHeight','FlexGuardFCSlotCount','FlexGuardFCVentRearInset','FlexGuardFCVentFrontInset','FlexGuardFCVentZOffset'):self.controls[name].setEnabled(vented and p.FlexGuardFCVents)
        self.controls['FlexGuardVentWidth'].setEnabled(vented and p.FlexGuardVTXVents and p.FlexGuardVentShape!='Horizontal slots')
        self.controls['FlexGuardFCVentWidth'].setEnabled(vented and p.FlexGuardFCVents and p.FlexGuardFCVentShape!='Horizontal slots')
        self.controls['FlexGuardWireEnabled'].setEnabled(p.FlexSideGuards)
        for name in ('FlexGuardWireSide','FlexGuardWirePairs','FlexGuardWireFrontY','FlexGuardWireRearY','FlexGuardWireWidth','FlexGuardWireHeight'):self.controls[name].setEnabled(p.FlexSideGuards and p.FlexGuardWireEnabled)
        self.controls['FlexGuardWirePairs'].setEnabled(p.FlexSideGuards and p.FlexGuardWireEnabled and p.FlexGuardFitMode=='Plate-edge wrap')
        self.controls['FlexGuardVTXOpening'].setEnabled(p.FlexSideGuards and p.FPVEnabled)
        for name in ('FlexGuardVTXSide','FlexGuardVTXY','FlexGuardVTXZ','FlexGuardVTXLength','FlexGuardVTXHeight'):
            self.controls[name].setEnabled(p.FlexSideGuards and p.FPVEnabled and p.FlexGuardVTXOpening)
        self.controls['FlexGuardVTXClearance'].setEnabled(p.FlexSideGuards and p.FPVEnabled and p.FlexGuardVTXOpening and (not p.FlexGuardVTXLength or not p.FlexGuardVTXHeight))
        self.controls['FlexGuardCloseFront'].setEnabled(p.FlexSideGuards and p.FPVEnabled)
        self.controls['FlexGuardCameraOverlap'].setEnabled(p.FlexSideGuards and p.FPVEnabled and p.FlexGuardCloseFront)
        self.controls['FlexGuardUSBEnabled'].setEnabled(p.FlexSideGuards and (p.FlexGuardExtendFront or p.FlexGuardCloseFront))
        for name in ('FlexGuardUSBSide','FlexGuardUSBY','FlexGuardUSBZ','FlexGuardUSBWidth','FlexGuardUSBHeight'):self.controls[name].setEnabled(p.FlexSideGuards and (p.FlexGuardExtendFront or p.FlexGuardCloseFront) and p.FlexGuardUSBEnabled)
        self.camera_width_sizes.setEnabled(p.FPVEnabled)
        self.camera_spacing_sizes.setEnabled(p.FPVEnabled)
        self.fit_camera_button.setEnabled(p.FPVEnabled)
        self.controls['CameraPivotHeight'].setEnabled(p.FPVEnabled and p.CameraPivotMode=='Custom height')
        self.controls['CameraMountY'].setEnabled(p.FPVEnabled and p.CameraPositionMode=='Custom position')
        for name in ('CameraBaseFrontExtension','CameraBaseRearExtension'):
            self.controls[name].setEnabled(p.FPVEnabled and p.CameraBaseMode=='Custom')
        self.controls['CameraTiltMechanism'].setEnabled(p.FPVEnabled and p.CameraMountMode=='Variable' and p.CameraSideBoltSpacing>0)
        for name in ('CameraTiltMin','CameraTiltMax'):
            self.controls[name].setEnabled(p.FPVEnabled and p.CameraMountMode=='Variable')
        self._sync_camera_size(p.CameraWidth)
        self._sync_camera_spacing(p.CameraSideBoltSpacing)
        for name,active in (('VTX20HoleDiameter',p.VTXPattern!='25.5 x 25.5 mm'),
                            ('VTX25HoleDiameter',p.VTXPattern!='20 x 20 mm')):
            self.controls[name].setEnabled(p.FPVEnabled and active and not o4)
        self.fpv_info.setText(
            f'{"M3 heat-set insert bosses attach the TPU cage to both plates" if tpu_cage else "Side plates use captured tabs"}. Cage gap {camera_cage_height(p):g} mm; '
            f'camera datum Y {camera_position_y(p):g} mm; height {camera_pivot_height(p):g} mm above bottom. '
            f'Lower contact {camera_attachment_lengths(p)[0]:g} mm; upper contact {camera_attachment_lengths(p)[1]:g} mm. '
            + ('Single-screw cameras have one pivot per side and rotate about that M2 location. ' if p.CameraSideBoltSpacing<=0 else 'Dual upper/lower slots keep the body centred; upper-pivot mounting fixes the upper screw. ') +
            'Width shortcuts fit the standoff height.' if p.FPVEnabled else
            'Enable FPV camera drone on Frame > Layout to add tabbed camera side plates.')
        self.vtx_info.setText(
            'Rear (−Y) VTX holes are on the bottom with two plates and on the mid with three. '
            'Automatic reach supports and covers the VTX; Custom uses the exact reaches you enter. Both patterns make eight holes; '
            'fit one set of four screws and insulating spacers. Match hole diameters to your hardware. '
            'The VTX housing may extend beyond the carbon carrier; all mounting holes need supporting carbon. Check side guards, props and other nearby parts for collisions; add a TPU guard opening only where necessary.' if p.FPVEnabled else
            'Enable FPV camera drone on Frame > Layout to add rear VTX mounting holes.')
        heights = standoff_heights(p)
        self.front_standoff_height.blockSignals(True)
        difference = heights["Front"] - heights["Rear"]
        self.front_standoff_height.setRange(max(.1,difference + .1), self.controls["StandoffHeight"].maximum() + difference)
        self.front_standoff_height.setValue(heights["Front"])
        self.front_standoff_height.blockSignals(False)
        self._sync_front_size(heights["Front"])
        self._sync_rear_size(heights["Rear"])
        layouts = standoff_layouts(p)
        front=next(s for s in layouts if s['position']=='Front')
        rear=next(s for s in layouts if s['position']=='Rear')
        mounting=f"Front: {front['mount'].lower()} → top. Rear: {rear['mount'].lower()} → top. Lengths stay linked to keep the top level."
        pair_notes = []
        for pair in standoff_pairs(p):
            stand = next(s for s in layouts if s["position"] == pair["position"])
            pair_notes.append(f"{pair['position']} (Y {pair['y']:.2f}, span {pair['width']:.2f}): 2 × {stand['length']:g} mm, {stand['mount'].lower()} → top")
            if stand['shared_arm']:
                pair_notes.append(f"  Shares {stand['shared_arm']['hole']} arm holes; clamp grip {stand['grip_length']:g} mm.")
        self.standoff_info.setText(mounting + "\n\n" + "\n".join(pair_notes))
        self.note.setText("All dimensions are mm. " + (
            '3 plates: bottom → arms / optional keystone → mid → top. Shared arm mounts use screws through the sandwich into the standoffs.'
            if three_plate(p) else '2 plates: arms '+('above' if arms_above_bottom(p) else 'below')+
            ' the bottom'+((' with one upper clamp / FC deck.' if upper_clamp_active(p) else ' with one lower clamp; FC stack on the bottom plate.') if arm_braces(p) else '.')+
            ' Standoff lengths follow their actual mounting surfaces and keep the top level.'))
        if underside_clamp_active(p):
            self.note.setText(self.note.text()+f' A {p.UndersideClampThickness:g} mm lower clamp captures the arms and optional key. Eight arm bolts secure it; stack access is {p.StackAccessDiameter:g} mm from below.')
        if p.FlexRearAntenna:
            from .antenna_layout import antenna_layout
            try:
                antenna=antenna_layout(p)
                self.note.setText(self.note.text()+f" Antenna grip: {antenna['height']:.2f} mm used / {antenna['available']:.2f} mm available. Tilt {p.FlexAntennaTilt:g} degrees; dual yaw 30 degrees each.")
            except (ValueError,IndexError):pass
        if p.FlexELRSEnabled:
            from .elrs_layout import elrs_seat
            try:
                seat=elrs_seat(p);self.note.setText(self.note.text()+f" ELRS grip: {seat['height']:.2f} mm / {seat['available']:.2f} mm available below the guards.")
            except (ValueError,IndexError):pass
        errors, warnings = validate(p)
        for name in BATTERY_FIELDS:
            if name.startswith('LiPoPad') and name!='LiPoPadEnabled':self.controls[name].setEnabled(p.LiPoPadEnabled and (not name.startswith('LiPoPadGroove') or p.LiPoPadPattern!='Solid'))
        self.controls['LiPoPadCornerRadius'].setEnabled(p.LiPoPadEnabled and p.LiPoPadShape=='Rounded rectangle')
        outline=p.LiPoPadShape=='Mounting plate outline'
        for key,axis in (('LiPoPadWidth','width'),('LiPoPadLength','length')):
            self.field_labels[key].setText('Pad '+axis)
            self.controls[key].setEnabled(p.LiPoPadEnabled and not outline)
        for name in ('LiPoPadOutlineWidthScale','LiPoPadFrontReach','LiPoPadRearReach'):self.controls[name].setEnabled(p.LiPoPadEnabled and p.LiPoPadShape=='Mounting plate outline')
        self.controls['LiPoPadFollowPlate'].setEnabled(p.LiPoPadEnabled and p.LiPoPadShape!='Mounting plate outline')
        self.controls['LiPoPadCopyAirflow'].setEnabled(p.LiPoPadEnabled and (outline or p.LiPoPadFollowPlate))
        self.airflow.copy_to_pad.setEnabled(p.LiPoPadEnabled and (outline or p.LiPoPadFollowPlate))
        from .equipment_mass import MASS_FIELDS
        for name in MASS_FIELDS:self.controls[name].setEnabled(p.EstimateComponents and (name not in ('VTXMass','CameraMass') or p.FPVEnabled))
        self.update_preview_modes(p)
        if hasattr(self,'camera_view_picture'):
            self._camera_view_update_recording_modes(p)
            self.camera_view_render.setEnabled(p.FPVEnabled)
            self.camera_view_sweep.setEnabled(p.FPVEnabled)
            if self.camera_view_use_tilt.isChecked():
                self.camera_view_tilt.setValue(p.CameraTilt)
            if self._camera_view_last_settings is not None and self._camera_view_last_settings!=self._camera_view_inputs(p):
                self.camera_view_status.setText('Settings changed. Click Render camera view to check the new geometry and optics.')
        if self.mass_signature!=design_signature(p):
            self.preview.mass_metrics=None
            self.mass_result.setText('Weight / CG needs calculation for the current settings. Bare frame and editable equipment estimates are reported separately.')
        self.mass_button.setEnabled(not errors)
        self.preview.params = p
        self.preview.update()
        # Reuse the parameter snapshot built at the start of refresh. Moving
        # the pointer over the Airflow preview must not scrape/validate every
        # main-dialog control on every mouse move.
        self.airflow.preview.set_frame_parameters(p)
        self.generate.setEnabled(not errors)
        gap = prop_gap(p)
        motors=motor_centres(p)
        actual_diagonal=math.dist(motors[0],motors[2])
        self.summary.setText(f"{p.PlateDesign}  •  {p.Layout}  •  {actual_diagonal:.1f} mm diagonal\n"
                             f"{p.PropDiameter / 25.4:.2f}-inch props  •  minimum prop gap {gap:.1f} mm\n"
                             f"{2 * standoff_pair_count(p)} standoffs ({standoff_pair_count(p)} pairs): rear {heights['Rear']:g} mm / front {heights['Front']:g} mm"
                             + (f"\nFPV {p.VideoSystem} • camera {p.CameraWidth:g} mm • VTX {p.VTXPattern}" if p.FPVEnabled else '\nNon-FPV frame'))
        if p.Layout=='Deadcat':
            arms=arm_layouts(p)
            self.summary.setText(self.summary.text()+f"\nFront arms {arms[0]['length']:.1f} mm • rear arms {arms[2]['length']:.1f} mm • front +Y")
            if p.RearArmExtension:
                self.summary.setText(self.summary.text()+f'\nRear extension +{p.RearArmExtension:g} mm per arm • base diagonal {p.Wheelbase:g} mm')
        carrier_name={'MidPlate':'mid plate','ArmClampPlate':'combined clamp','BottomPlate':'bottom plate'}[stack_mounting_role(p)]
        self.summary.setText(self.summary.text()+f"\nStack on {carrier_name} • bottom holes {bottom_stack_hole_diameter(p):g} mm • strap openings "+(p.StrapOpeningStyle if p.StrapSlotsEnabled else 'off'))
        if p.DetailedStackReference:
            from .reference_options import stack_usb_centre
            ux,uy,uz=stack_usb_centre(p)
            guard_z=uz-plate_levels(p)['deck_z']
            self.summary.setText(self.summary.text()+f"\nFC USB: {p.StackUSBFace} • guard centre Y offset {p.StackUSBOffsetY:g} mm / Z {guard_z:.2f} mm (allow cable clearance)")
        self.summary.setStyleSheet("font-weight: bold; padding: 6px; color: " + ("#b43737" if errors else "#21805b") + ";")
        self.messages.setPlainText("\n".join(["FIX: " + text for text in errors] + ["CHECK: " + text for text in warnings])
                                    or "Layout checks passed. Edit a dimension to preview changes, then create the frame.")

    def load(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load RotorForge frame settings", "", "RotorForge settings (*.json)")
        if path:
            try:
                import json
                with open(path,encoding='utf-8') as stream:raw=json.load(stream)
                from .hardware_preferences import from_settings
                p=parameters_from_settings(raw)
                hardware=from_settings(raw)
                old=raw['parameters'].get('StackSpacing',30.5)
                self.set_values(p)
                self._loaded_hardware_preferences=hardware
                if isinstance(old,(int,float)) and old not in (20.,30.5):
                    QtWidgets.QMessageBox.warning(self,'FC mounting pattern updated',f'The saved {old:g} mm stack pattern was changed to {stack_label(p.StackSpacing)}. Other dimensions are retained. Review stack hardware before manufacturing.')
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self, "Cannot load settings", str(exc))

    def save(self):
        if not self.airflow.require_applied():return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save RotorForge frame settings", "frame.json", "RotorForge settings (*.json)")
        if path:
            try:
                from .hardware_refs import saved_preferences
                hardware = self._loaded_hardware_preferences
                if hardware is None:hardware = saved_preferences(self.settings)
                save_parameters(path if path.lower().endswith(".json") else path + ".json", self.values(), hardware)
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self, "Cannot save settings", str(exc))

    def apply(self):
        if not self.airflow.require_applied():return
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            p = self.values()
            if self.settings:
                update_frame(self.settings, p)
            else:
                self.settings = create_frame(p)
            if self._loaded_hardware_preferences is not None:
                from .hardware_refs import restore_preferences
                restore_preferences(self.settings, self._loaded_hardware_preferences)
            view_front()
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(self.settings)
            self.accept()
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Frame could not be built", str(exc))
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()


_ACTIVE_FRAME_EDITOR = None
_EDITOR_OPENING = False


def show_editor(settings=None):
    # Guard before construction, not after: PySide/Qt or FreeCAD callbacks can
    # re-enter commands during the setup of this unusually large dialog.
    global _ACTIVE_FRAME_EDITOR, _EDITOR_OPENING
    if _EDITOR_OPENING:
        return None
    if _ACTIVE_FRAME_EDITOR is not None:
        _ACTIVE_FRAME_EDITOR.raise_()
        _ACTIVE_FRAME_EDITOR.activateWindow()
        return None
    _EDITOR_OPENING = True
    try:
        dialog = FrameDialog(settings)
        _ACTIVE_FRAME_EDITOR = dialog
        _EDITOR_OPENING = False
        return dialog.exec() if hasattr(dialog, "exec") else dialog.exec_()
    finally:
        _ACTIVE_FRAME_EDITOR = None
        _EDITOR_OPENING = False


def report_error(exc):
    QtWidgets.QMessageBox.warning(Gui.getMainWindow(), "RotorForge", str(exc))


class NewCommand:
    def GetResources(self):
        return {"Pixmap": icon_path("toolbar-new-frame.png"), "MenuText": "New frame…", "ToolTip": "Generate a parametric quadcopter frame"}

    def Activated(self):
        show_editor()


class EditCommand:
    def GetResources(self):
        return {"Pixmap": icon_path("toolbar-edit-frame.png"), "MenuText": "Edit frame…", "ToolTip": "Edit the selected frame or the only frame in this document"}

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            show_editor(find_parameters(Gui.Selection.getSelection()))
        except Exception as exc:
            report_error(exc)


class ExportCommand(EditCommand):
    def GetResources(self):
        return {"Pixmap": icon_path("toolbar-export-frame.png"),
                "MenuText": "Export frame…", "ToolTip": "Save STEP, exact millimetre DXF / SVG profiles, and parameters"}

    def Activated(self):
        try:
            settings = find_parameters(Gui.Selection.getSelection())
            destination = QtWidgets.QFileDialog.getExistingDirectory(Gui.getMainWindow(), "Choose a folder for the frame export")
            if not destination:
                return
            from .exporters import export_package
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            try:
                folder = export_package(settings, destination)
            finally:
                QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QMessageBox.information(Gui.getMainWindow(), "Frame exported", "Export saved to:\n" + str(folder))
        except Exception as exc:
            report_error(exc)


class ReferencesCommand(EditCommand):
    def GetResources(self):
        return {"Pixmap": icon_path("toolbar-toggle-references.png"), "MenuText": "Toggle references",
                "ToolTip": "Show or hide propeller discs, motor envelopes, and electronics envelope"}

    def Activated(self):
        try:
            settings = find_parameters(Gui.Selection.getSelection())
            from dataclasses import replace
            update_frame(settings, replace(read_parameters(settings), ShowReferences=not settings.ShowReferences))
        except Exception as exc:
            report_error(exc)


class HelpCommand:
    def GetResources(self):
        return {"Pixmap": icon_path("toolbar-help-pdf.png"), "MenuText": "Help manual (PDF)", "ToolTip": "Open the complete illustrated help in your PDF viewer"}

    def Activated(self):
        path=help_path()
        if not os.path.isfile(path):
            QtWidgets.QMessageBox.warning(Gui.getMainWindow(),"RotorForge help",
                "The help PDF is missing:\n"+path+"\n\nReinstall the complete RotorForge folder.")
        elif not QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path)):
            QtWidgets.QMessageBox.warning(Gui.getMainWindow(),"RotorForge help",
                "The PDF viewer could not be opened. Open this file manually:\n"+path)


def register_commands():
    from .hardware_gui import HardwareCommand
    commands = (("RotorForge_NewFrame", NewCommand()), ("RotorForge_EditFrame", EditCommand()),
                ("RotorForge_ExportFrame", ExportCommand()), ("RotorForge_References", ReferencesCommand()),
                ("RotorForge_HardwareReferences", HardwareCommand()), ("RotorForge_FrontView", FrontViewCommand()), ("RotorForge_Help", HelpCommand()))
    for name, command in commands:
        Gui.addCommand(name, command)
    return [name for name, command in commands]


class FrontViewCommand:
    def GetResources(self):
        return {'Pixmap':icon_path('toolbar-front-isometric.png'),'MenuText':'Front isometric','ToolTip':'View the frame from its +Y nose'}

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        view_front()
