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
from .paths import help_path
from .motor_sizes import MOTOR_SIZES,apply_motor_size
from .appearance import CARBON_HEX,CARBON_EDGE,PAD_HEX,printed_hex,PRINTED_COLOURS,design_signature
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
    'BatteryReferenceEnabled':'Show LiPo reference',
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
    "FPVEnabled": "FPV camera drone", "VideoSystem": "Video system",
    "CameraWidth": "Camera body width", "CameraHeight": "Camera body height",
    "CameraBodyDepth": "Camera body depth (without lens)", "CameraSideClearance": "Extra width clearance (total)",
    "CameraSideHoleDiameter": "Camera side screw hole diameter", "CameraSideBoltSpacing": "Vertical screw spacing (0 = pivot)",
    "CameraMountY": "Custom camera centre Y", "CameraPivotHeight": "Custom camera centre height above bottom",
    "CameraPivotMode":"Camera height placement", "CameraPlateLength":"Side plate minimum length",
    "CameraTabLength":"Tab length along frame", "CameraTabClearance":"Tab clearance per side",
    "CameraTilt": "Camera uptilt", "CameraBracketThickness": "Camera side plate thickness",
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
    'BatteryReferenceEnabled':'Display the editable nominal 1300 mAh 6S battery envelope when Show references is on. It is excluded from manufactured parts and bare-frame mass; its mass is used only in the separately labelled frame-plus-battery estimate.',
    'BatteryWidth':'Battery envelope width in its local X direction. Default 38 mm; capacity alone does not define pack dimensions.',
    'BatteryLength':'Battery envelope length along local Y before rotation. Default 75 mm.',
    'BatteryHeight':'Battery envelope height. Default 38 mm. The pack rests on the optional pad or directly on the chosen plate.',
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
    'BatteryMass':'Mass used for both the frame-plus-reference-battery and loaded equipment estimates. Default 208 g. Weigh your actual pack; this is not a complete aircraft weight.',
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
    'LiPoPadShape':'Choose rounded rectangle, rectangle, capsule, ellipse, chamfered rectangle, tapered or hourglass. Mounting plate outline copies the entire finished top plate (or bottom plate when selected), including its holes and cutouts; use Plate outline width scale and independent front/rear reaches from the stack. Ends are cut straight when shortened; all pads leave a 6 mm clear radius around standoff centres. Grip patterns cover the finished pad automatically; battery pose does not move a plate-following pad or its grip pattern.',
    'LiPoPadCornerRadius':'Corner radius for Rounded rectangle. Zero makes square corners; positive values must be smaller than half the shorter pad dimension. Use Capsule for fully rounded ends.',
    'LiPoPadFollowPlate':'Clip the pad to the finished mounting plate, including its holes, strap slots and applied cutouts. Disabling this keeps the independent pad outline. CAD rejects empty or disconnected pads.',
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
    'MotorPadShape':'The first ten choices through Scalloped shield are retained. Twelve shield variations add shallow edge scallops, swept or curved shoulders and compact crowns. Both mounting patterns remain available.',
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
    "CameraBodyDepth": "Reference body depth excluding the approximate 6 mm front lens. Measure your camera for clearance checks.",
    "CameraSideBoltSpacing":'Vertical centre-to-centre spacing on one camera side, measured with the camera level. Use 6.5 mm for that measured pattern, a custom pitch, or zero for a single pivot screw. Camera body width is independent.',
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
    "LengthToWidth": "Stretched X: left–right motor span divided by front–rear spacing. Deadcat: length divided by rear span. Ignored for True X.",
    "FrontSpread": "Deadcat only: front/rear motor span ratio of the base layout. Automatic rear reach compensates for front spread. Extra rear arm extension is applied afterwards, increasing the final rear span and actual diagonals.",
    "PropDiameter": "Full propeller diameter: 5 inch = 127 mm; 5.1 inch = 129.54 mm; 7 inch = 177.8 mm.",
    "ArmRootY": "The front/rear arm root reference centres sit at +Y and -Y of this distance. Moving custom bolts does not move these references or the motors.",
    "RootInset": "Horizontal distance from the bottom plate side edge to each arm root centre.",
    "RootExtension": "Untrimmed tail reach behind the midpoint of the two root bolts. Fitted miters trim it at the joint lines and compact key pocket. Increase it until the required seats meet.",
    "RootBoltSpacing": "Two bolts per arm. Three plates: bottom/arm/mid sandwich. Two plates: arms above or below the bottom, with the optional combined clamp on the same bolts.",
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
        self.setMinimumSize(320, 260)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor("#f3f6f8"))
        p = self.params
        self.last_error = None
        try:
            if self.view_mode!='Overall':
                draw_parts(painter,QtCore.QRectF(6,30,self.width()-12,self.height()-60),p,self.view_mode)
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
                painter.setBrush(QtGui.QColor("#414448"))
                painter.drawPath(finished_part_path(p,'BottomPlate') if p.BottomEdgeFillet else bottom_path)
            if arms_above_bottom(p):
                draw_bottom()
            for arm in arms:
                painter.setPen(QtGui.QPen(QtGui.QColor('#384655'),.5));painter.setBrush(QtGui.QColor(CARBON_HEX))
                painter.drawPath(finished_part_path(p,'Arm'+arm['name']) if p.ArmEdgeFillet else arm_stack_access_path(p,arm_blank_path(p,arm,arms)))
                for pt in arm["bolts"]:
                    ellipse(pt, p.RootHoleDiameter / 2, "#202b36")
                for pt in arm["motor_holes"]:
                    ellipse(pt, p.MotorHoleDiameter / 2, "#202b36")
                for a,b,radius in motor_tip_slots(p,arm):capsule(a,b,2*radius,'#202b36')
                ellipse(arm["motor"], p.MotorCenterDiameter / 2, "#202b36")
            if three_plate(p):
                mid_path = mid_plate_path(p,arms)
                painter.setPen(QtGui.QPen(QtGui.QColor("#17191b"), 0.6))
                painter.setBrush(QtGui.QColor("#45484c"))
                painter.drawPath(finished_part_path(p,'MidPlate') if p.MidEdgeFillet else mid_path)
            elif not arms_above_bottom(p):
                draw_bottom()
            for clamp in arm_brace_layouts(p) if upper_clamp_active(p) else ():
                path=finished_part_path(p,clamp['role'])
                painter.setPen(QtGui.QPen(QtGui.QColor('#17191b'),.6))
                painter.setBrush(QtGui.QColor('#3a3d40'))
                painter.drawPath(path)
            if fitted_roots(p):
                # Show the otherwise hidden joints through the mid/clamp plate.
                painter.save()
                span=max(abs(v) for a in arms for v in a['root'])+root_width(p)
                painter.setClipRect(QtCore.QRectF(-span,-span,2*span,2*span))
                painter.setPen(QtGui.QPen(QtGui.QColor('#384655'),.55,QtCore.Qt.DashLine))
                painter.setBrush(QtCore.Qt.NoBrush)
                for arm in arms:painter.drawPath(finished_part_path(p,'Arm'+arm['name']) if p.ArmEdgeFillet else arm_stack_access_path(p,arm_blank_path(p,arm,arms)))
                if keystone_active(p):
                    painter.setPen(QtGui.QPen(QtGui.QColor('#17191b'),.6))
                    painter.setBrush(QtGui.QColor('#35383b'))
                    painter.drawPath(keystone_path(p,arms))
                painter.restore()
            for arm in arms:
                for pt in arm["bolts"]:
                    ellipse(pt, p.RootHoleDiameter / 2, "#202b36")
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtGui.QPen(QtGui.QColor("#657d90"), 0.65, QtCore.Qt.DashLine))
            top_rear,top_front=top_bounds(p)
            top_path=profile_path(p,'TopPlate',p.TopWidth,top_rear,top_front,p.CornerRadius)
            painter.drawPath(finished_part_path(p,'TopPlate') if p.TopEdgeFillet or (p.StrapSlotsEnabled and p.StrapOpeningStyle=='Outline cutouts') else top_path)
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
                painter.setBrush(QtGui.QColor(CARBON_HEX))
                for mount in camera_mounts(p):
                    xmin,xmax=mount['plate_x']
                    rear=min(y for y,z in mount['wall_profile']);front=max(y for y,z in mount['wall_profile'])
                    painter.drawRect(QtCore.QRectF(xmin,rear,xmax-xmin,front-rear))
                painter.setBrush(QtGui.QColor('#546a77'))
                body_y=camera_body_centre(p)[0]
                painter.drawRect(QtCore.QRectF(-p.CameraWidth/2,body_y-p.CameraBodyDepth/2,p.CameraWidth,p.CameraBodyDepth))
                ellipse((0,body_y+p.CameraBodyDepth/2+3),min(6,p.CameraWidth*.35),'#163e50','#7ac4d8')
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
            if p.FlexSideGuards:
                from .protection_layout import guard_layout
                from .flex_preview import guard_plan_path
                for g in guard_layout(p):
                    painter.setPen(QtGui.QPen(QtGui.QColor('#617c7c'),.4));painter.setBrush(QtGui.QColor(printed_hex(p)));painter.drawPath(guard_plan_path(p,g))
            if p.BatteryReferenceEnabled and p.ShowReferences:
                outline=QtGui.QPainterPath();points=[battery_point(p,x,y) for x,y in ((-p.BatteryWidth/2,-p.BatteryLength/2),(p.BatteryWidth/2,-p.BatteryLength/2),(p.BatteryWidth/2,p.BatteryLength/2),(-p.BatteryWidth/2,p.BatteryLength/2))]
                outline.moveTo(*points[0])
                for point in points[1:]:outline.lineTo(*point)
                outline.closeSubpath();painter.setPen(QtGui.QPen(QtGui.QColor('#c46a18'),.7));painter.setBrush(QtGui.QColor(234,147,61,75));painter.drawPath(outline)
            if self.mass_metrics and p.ShowFrameCG and p.ShowReferences:
                x,y,z=self.mass_metrics['display_cg_mm'];painter.setPen(QtGui.QPen(QtGui.QColor('#d92332'),.9));painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawEllipse(QtCore.QPointF(x,y),2.5,2.5)
                painter.drawLine(QtCore.QPointF(x-5,y),QtCore.QPointF(x+5,y));painter.drawLine(QtCore.QPointF(x,y-5),QtCore.QPointF(x,y+5))
            painter.restore()
            painter.setPen(QtGui.QColor("#3b4c5b"))
            painter.drawText(QtCore.QRectF(0, 8, self.width(), 24), QtCore.Qt.AlignCenter, "FRONT  +Y")
            painter.drawText(QtCore.QRectF(0, self.height() - 27, self.width(), 20), QtCore.Qt.AlignCenter,
                             "Top view • orange: LiPo reference • red cross: calculated frame CG" if p.BatteryReferenceEnabled and p.ShowReferences else
                             "Top view • camera: teal • VTX: purple" if p.FPVEnabled else
                             "Top view • beige: bottom • blue: mid • dashed: top")
        except Exception as exc:
            self.last_error = str(exc)
            # Malformed intermediate input must not disrupt editing.
            painter.end()
            return
        painter.end()




class FrameDialog(QtWidgets.QDialog):
    def __init__(self, settings=None):
        super().__init__(Gui.getMainWindow())
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowMaximizeButtonHint)
        self.settings = settings
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
        tabs = QtWidgets.QTabWidget()
        self.tabs = tabs
        tabs.setMinimumWidth(440)
        forms = {}; field_forms = {}; self.section_pages = {}; self.category_tabs = {}
        for category, title, description, groups in SECTIONS:
            if category not in self.category_tabs:
                section_tabs=QtWidgets.QTabWidget()
                section_tabs.setObjectName('Sections_'+category)
                self.category_tabs[category]=section_tabs
                tabs.addTab(section_tabs,category)
            section_tabs=self.category_tabs[category]
            page=QtWidgets.QWidget();page_layout=QtWidgets.QVBoxLayout(page)
            intro=QtWidgets.QLabel(description);intro.setWordWrap(True)
            page_layout.addWidget(intro)
            info=QtWidgets.QWidget();forms[title]=QtWidgets.QFormLayout(info)
            forms[title].setContentsMargins(0,0,0,0);page_layout.addWidget(info)
            for heading,names in groups:
                box=QtWidgets.QGroupBox(heading);form=QtWidgets.QFormLayout(box)
                form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
                form.setRowWrapPolicy(QtWidgets.QFormLayout.WrapLongRows)
                page_layout.addWidget(box)
                for name in names:field_forms[name]=form
            page_layout.addStretch()
            scroll=QtWidgets.QScrollArea();scroll.setWidgetResizable(True)
            scroll.setFrameShape(QtWidgets.QFrame.NoFrame);scroll.setWidget(page)
            section_tabs.addTab(scroll,title.replace('&','&&'));self.section_pages[title]=(category,scroll)
        self.find_control=QtWidgets.QLineEdit()
        self.find_control.setPlaceholderText('Find a control… (e.g. keystone, strap, camera tilt)')
        self.find_control.setClearButtonEnabled(True)
        self.find_control.setToolTip('Type a control name or topic, then choose a result to open its page.')
        settings_files.insertWidget(0,self.find_control,1)
        self.fpv_info=QtWidgets.QLabel()
        self.fpv_info.setWordWrap(True)
        forms['Side plates'].addRow(self.fpv_info)
        self.vtx_info=QtWidgets.QLabel()
        self.vtx_info.setWordWrap(True)
        forms['VTX'].addRow(self.vtx_info)
        fit=QtWidgets.QPushButton('Fit camera height')
        fit.setToolTip('Centre the camera and raise the standoffs to a common size if needed.')
        fit.clicked.connect(self.fit_camera)
        self.fit_camera_button=fit
        forms['Tilt & position'].addRow(fit)
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
                if name=="PrintedPartColour":
                    for i,text in enumerate(ENUMERATIONS[name]):control.setItemData(i,QtGui.QColor(PRINTED_COLOURS[text]),QtCore.Qt.DecorationRole)
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
                if name=='FlexInsertCornerRadius':
                    control.setRange(.25,20);control.setSuffix(' mm');control.setSingleStep(.25)
                elif name=='CameraTabCutterDiameter':
                    control.setRange(.2,6);control.setSuffix(' mm');control.setSingleStep(.5)
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
        self.plate_info=QtWidgets.QLabel();self.plate_info.setWordWrap(True);forms['Bottom plate'].insertRow(0,self.plate_info)
        self.mid_plate_info=QtWidgets.QLabel();self.mid_plate_info.setWordWrap(True);forms['Mid plate'].insertRow(0,self.mid_plate_info)
        self.top_plate_info=QtWidgets.QLabel();self.top_plate_info.setWordWrap(True);forms['Top plate'].insertRow(0,self.top_plate_info)
        self.root_fit_info=QtWidgets.QLabel();self.root_fit_info.setWordWrap(True);forms['Roots'].insertRow(0,self.root_fit_info)
        self.airflow=AirflowEditor(self.values)
        self.airflow.changed.connect(self.controls['CutoutPatterns'].setText)
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
        self.search_locations['FPV > Tilt & position > Fit camera height']='@fit_camera'
        self.search_locations['Finishing > Airflow / outlines > Cutout type, outline notch, patterns']='@airflow'
        self.extra_search_targets={}
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
                   'columns':'Columns','rows':'Rows','pitch_x':'Pitch U','pitch_y':'Pitch V','rotation':'Rotation'}
        cuts.extend((cut_names[key],control) for key,control in self.airflow.inputs.items())
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
        main.addLayout(right, 6)
        outer.addLayout(main, 1)
        self.note = QtWidgets.QLabel()
        self.note.setWordWrap(True)
        outer.addWidget(self.note)
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel)
        self.maximize_button = self.buttons.addButton("Maximize window", QtWidgets.QDialogButtonBox.ActionRole)
        self.maximize_button.setToolTip("Toggle between a maximized editor and its previous size.")
        self.maximize_button.clicked.connect(self.toggle_maximized)
        self.generate = self.buttons.addButton("Update frame" if settings else "Create frame", QtWidgets.QDialogButtonBox.AcceptRole)
        self.buttons.rejected.connect(self.reject)
        self.generate.clicked.connect(self.apply)
        # Enter in the finder must not invoke a fit or create action.
        for button in self.findChildren(QtWidgets.QPushButton):
            button.setAutoDefault(False)
            button.setDefault(False)
        outer.addWidget(self.buttons)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(80)
        self.timer.timeout.connect(self.refresh)
        load.clicked.connect(self.load)
        save.clicked.connect(self.save)
        self.set_values(read_parameters(settings) if settings else Parameters())
        sizing=QtWidgets.QComboBox();sizing.addItem('Apply motor / prop sizing…');sizing.addItems(tuple(MOTOR_SIZES))
        sizing.activated.connect(lambda i:self.set_values(apply_motor_size(self.values(),sizing.itemText(i))) if i else None)
        forms['Motors'].addRow('Motor / prop size',sizing)
        self.motor_sizing=sizing

    def set_preview_mode(self,*_):
        if not hasattr(self,'preview'):return
        self.preview.view_mode=self.preview_mode.currentData() or 'Overall';self.preview.update()

    def update_preview_modes(self,p):
        from .airflow_gui import ROLE_LABELS
        current=self.preview_mode.currentData();self.preview_mode.blockSignals(True);self.preview_mode.clear()
        for text,value in [('Overall frame — top view','Overall'),('All parts — flat profiles','AllParts'),('All four arms — flat profiles','Arms')]:self.preview_mode.addItem(text,value)
        for role in preview_roles(p):self.preview_mode.addItem(ROLE_LABELS.get(role,'LiPo pad'),role)
        index=self.preview_mode.findData(current);self.preview_mode.setCurrentIndex(max(0,index));self.preview_mode.blockSignals(False);self.set_preview_mode()

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
                 '@fit_camera':('Tilt & position',self.fit_camera_button),
                 '@airflow':('Airflow / outlines',self.airflow)}
        special.update(self.extra_search_targets)
        if name in special:title,control=special[name]
        else:title,control=tab_name(name),self.controls[name]
        category,scroll=self.section_pages[title]
        self.tabs.setCurrentWidget(self.category_tabs[category])
        self.category_tabs[category].setCurrentWidget(scroll)
        scroll.ensureWidgetVisible(control,10,70)
        control.setFocus(QtCore.Qt.OtherFocusReason)

    def find_control_enter(self):
        text=self.find_control.text().strip().casefold()
        matches=[caption for caption in self.search_locations if text and text in caption.casefold()]
        if len(matches)==1:self.jump_to_control(matches[0])

    def toggle_maximized(self):
        if self.isMaximized():
            normal_geometry = self.normalGeometry()
            self.showNormal()
            self.setGeometry(normal_geometry)
        else:
            self.showMaximized()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.WindowStateChange and hasattr(self, "maximize_button"):
            self.maximize_button.setText("Restore window" if self.isMaximized() else "Maximize window")

    def values(self):
        values = {}
        for name, control in self.controls.items():
            values[name] = (control.currentData() if name=='StackSpacing' else control.currentText() if name in ENUMERATIONS else
                            control.text() if name in STRINGS else
                            control.isChecked() if name in BOOLEANS else control.value())
        if getattr(self,'_bottom_body_reach_value',None) is not None:
            values['BottomBodyRearReach']=self._bottom_body_reach_value
        return Parameters.from_dict(values)

    def set_values(self, p):
        p = Parameters.from_dict(p.to_dict())
        # Migrated arm-derived edges can contain more precision than the
        # displayed millimetres. Keep it until the user edits this dimension.
        self._bottom_body_reach_value=p.BottomBodyRearReach
        if p.StackPressNuts:self.field_labels['StackMountHeight'].setText(f'Stack support (automatic; actual {stack_reference_z(p)-plate_levels(p)["stack_deck_z"]:.2f} mm)')
        ratio = self.controls["LengthToWidth"]
        ratio.blockSignals(True)
        ratio.setRange(1.0 if p.Layout == "Stretched X" else .65, 1.8)
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
        self.airflow.set_json(p.CutoutPatterns)
        self.timer.stop()
        self.refresh()

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
        low,high=camera_vertical_limits(p)
        required=2*max(-low,high)+.4
        stand=required-(camera_cage_height(p)-p.StandoffHeight)
        if stand>p.StandoffHeight:
            target=next((v for v in COMMON_STANDOFF_HEIGHTS if v>=stand),math.ceil(stand*2)/2)
            self.controls['StandoffHeight'].setValue(target)
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

    def refresh(self):
        p = self.values()
        for control in self.controls.values():control.setEnabled(True)
        for name in ('StackSpacing','StackHoleDiameter','StackHeight','StackMountHeight'):self.field_labels[name].setText(label(name))
        if p.StackPressNuts:self.field_labels['StackMountHeight'].setText(f'Stack support (automatic; actual {stack_reference_z(p)-plate_levels(p)["stack_deck_z"]:.2f} mm)')
        self.controls["StackMountHeight"].setEnabled(not p.StackPressNuts)
        ratio = self.controls["LengthToWidth"]
        ratio.blockSignals(True)
        ratio.setRange(1.0 if p.Layout == "Stretched X" else .65, 1.8)
        ratio.setValue(p.LengthToWidth)
        ratio.blockSignals(False)
        self.field_labels["LengthToWidth"].setText("Width / front–rear spacing" if p.Layout == "Stretched X" else "Length / rear motor span")
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
        for name in ('KeystoneWidth','KeystoneLength'):
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
            if name.startswith('FlexBumper'):enabled=p.FlexFrontBumper and (name not in ('FlexBumperProjection','FlexBumperWidth','FlexBumperTipWidth','FlexBumperRecess') or p.FlexBumperShape!='Follow bottom plate')
            if name=='FlexBumperTipWidth':enabled=enabled and p.FlexBumperShape in ('Chamfered shoe','Swept-shoulder shoe','Flat-tip shoe','Centre-crown shoe','Recessed-centre shoe','Stepped shoe','Capsule shoe','Bullnose shoe','Arrowhead shoe','V-recess shoe','Twin-shoulder shoe','Clipped-corner shoe')
            if name=='FlexBumperRecess':enabled=enabled and p.FlexBumperShape in ('Twin-lobe shoe','Recessed-centre shoe','V-recess shoe','Twin-shoulder shoe')
            elif name.startswith('FlexProtector'):enabled=p.FlexMotorProtectors
            elif name.startswith('FlexGuardStrap'):enabled=p.FlexSideGuards and (name=='FlexGuardStraps' or p.FlexGuardStraps)
            elif name.startswith('FlexGuard'):enabled=p.FlexSideGuards
            elif name=='FlexInterfaceShape':enabled=soft_camera(p)
            elif name.startswith(('FlexPad','FlexInsert')):enabled=soft_camera(p) and (not name.startswith('FlexInsert') or p.FlexCameraMode=='Captured inserts')
            elif name=='FlexCameraMode':enabled=p.FPVEnabled
            self.controls[name].setEnabled(enabled)
        for name in ('DetailedMotorReferences','DetailedPropReferences','DetailedStackReference','DetailedCameraReference','DetailedVTXReference','DetailedBatteryReference'):
            self.controls[name].setEnabled(p.ShowReferences and (name not in ('DetailedCameraReference','DetailedVTXReference') or p.FPVEnabled) and (name!='DetailedBatteryReference' or p.BatteryReferenceEnabled))
        self.controls['PropReferenceHeight'].setEnabled(not p.DetailedPropReferences)
        for name in ('FlexGuardStrapY1','FlexGuardStrapY2'):
            self.controls[name].setEnabled(p.FlexSideGuards and p.FlexGuardStraps and not p.FlexGuardStrapAuto and (name!='FlexGuardStrapY2' or p.FlexGuardStrapCount=='2 straps'))
        self.controls['CameraTabCutterDiameter'].setEnabled(p.FPVEnabled and p.CameraTabReliefs)
        self.controls['CameraSideClearance'].setEnabled(p.FPVEnabled and not soft_camera(p))
        self.controls['FlexPadWidth'].setEnabled(soft_camera(p) and p.FlexCameraMode=='Compression pads')
        self.controls['FlexPadHeight'].setEnabled(soft_camera(p) and p.FlexCameraMode=='Compression pads')
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
            self.controls[name].setEnabled(p.FPVEnabled and active)
        self.fpv_info.setText(
            f'Two side plates are captured by tabs in the bottom and top (+Y front). Cage gap {camera_cage_height(p):g} mm; '
            f'camera centre Y {camera_position_y(p):g} mm; height {camera_pivot_height(p):g} mm above bottom. '
            f'Lower contact {camera_attachment_lengths(p)[0]:g} mm; upper contact {camera_attachment_lengths(p)[1]:g} mm. '
            'Side screws are stacked vertically at zero tilt. Dual upper/lower slots keep the body centred; the alternative fixes the upper screw. '
            'Width shortcuts fit the standoff height.' if p.FPVEnabled else
            'Enable FPV camera drone on Frame > Layout to add tabbed camera side plates.')
        self.vtx_info.setText(
            'Rear (−Y) VTX holes are on the bottom with two plates and on the mid with three. '
            'Automatic reach supports and covers the VTX; Custom uses the exact reaches you enter. Both patterns make eight holes; '
            'fit one set of four screws and insulating spacers. Match hole diameters to your hardware. '
            'For a wider VTX, configure VTX clearance on TPU > Side guards; a fully covering opening allows lateral overhang.' if p.FPVEnabled else
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
        from .equipment_mass import MASS_FIELDS
        for name in MASS_FIELDS:self.controls[name].setEnabled(p.EstimateComponents and (name not in ('VTXMass','CameraMass') or p.FPVEnabled))
        self.update_preview_modes(p)
        if self.mass_signature!=design_signature(p):
            self.preview.mass_metrics=None
            self.mass_result.setText('Weight / CG needs calculation for the current settings. Bare frame and editable equipment estimates are reported separately.')
        self.mass_button.setEnabled(not errors)
        self.preview.params = p
        self.preview.update()
        self.airflow.preview.update()
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
                p=parameters_from_settings(raw);old=raw['parameters'].get('StackSpacing',30.5);self.set_values(p)
                if isinstance(old,(int,float)) and old not in (20.,30.5):
                    QtWidgets.QMessageBox.warning(self,'FC mounting pattern updated',f'The saved {old:g} mm stack pattern was changed to {stack_label(p.StackSpacing)}. Other dimensions are retained. Review stack hardware before manufacturing.')
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self, "Cannot load settings", str(exc))

    def save(self):
        if not self.airflow.require_applied():return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save RotorForge frame settings", "frame.json", "RotorForge settings (*.json)")
        if path:
            try:
                save_parameters(path if path.lower().endswith(".json") else path + ".json", self.values())
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
            view_front()
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(self.settings)
            self.accept()
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Frame could not be built", str(exc))
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()


def show_editor(settings=None):
    dialog = FrameDialog(settings)
    return dialog.exec() if hasattr(dialog, "exec") else dialog.exec_()


def report_error(exc):
    QtWidgets.QMessageBox.warning(Gui.getMainWindow(), "RotorForge", str(exc))


class NewCommand:
    def GetResources(self):
        return {"Pixmap": ICON, "MenuText": "New frame…", "ToolTip": "Generate a parametric quadcopter frame"}

    def Activated(self):
        show_editor()


class EditCommand:
    def GetResources(self):
        return {"Pixmap": ICON, "MenuText": "Edit frame…", "ToolTip": "Edit the selected frame or the only frame in this document"}

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            show_editor(find_parameters(Gui.Selection.getSelection()))
        except Exception as exc:
            report_error(exc)


class ExportCommand(EditCommand):
    def GetResources(self):
        return {"Pixmap": os.path.join(os.path.dirname(ICON), "export.svg"),
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
        return {"Pixmap": os.path.join(os.path.dirname(ICON), "props.svg"), "MenuText": "Toggle references",
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
        return {"MenuText": "Help manual (PDF)", "ToolTip": "Open the complete illustrated help in your PDF viewer"}

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
        return {'Pixmap':ICON,'MenuText':'Front isometric','ToolTip':'View the frame from its +Y nose'}

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        view_front()
