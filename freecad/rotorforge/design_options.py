"""Shape controls shared by the editor and the integrated user guide."""
PLATE_SHAPES=('Rounded rectangle','Chamfered rectangle','Tapered front','Tapered rear','Hexagonal','Faceted shield','Octagonal')
ARM_BEAM_SHAPES=('Straight','Root taper','Motor flare','Hourglass neck','Broad shoulder','Stepped beam')
MOTOR_PAD_RELIEFS=('None','Neck slot','Twin neck holes','Twin neck slots')
OPTIONS={
 'StrapOpeningStyle':('Slots','Top plate strap openings','Choose enclosed slots or open left/right outline cutouts while retaining the saved dimensions and positions. Side guards bridge the outline cutouts along the outside plate edge, leaving the strap passages clear. Use the enable switch to omit openings.',('Slots','Outline cutouts')),
 'StrapCount':('2 straps','Number of top-plate straps','Choose one left/right opening pair or two pairs. Two-strap spacing remains saved when using one strap.',('1 strap','2 straps')),
 'StrapSingleY':(0.,'Single strap fore/aft position','Single-strap centre in frame Y: zero is centred, positive is forward, negative is rearward. Used for slots and outline cutouts.'),
 'StrapNotchDepth':(3.,'Outline cutout depth','Depth inward from the local top-plate side edge. Outline cutouts use the existing strap length and fore/aft positions. Inner corners are rounded; slot width and inset remain saved for Slots mode.'),
 'StackUSBFace':('Left','FC USB side','Side-facing USB-C socket on the upper PCB. Left is negative frame X; right is positive X. Generic side-centred commercial-style placement, not an exact board footprint.',('Left','Right')),
 'StackUSBOffsetY':(0.,'FC USB fore/aft offset','USB socket centre relative to the stack centre. Positive moves forward; negative moves rearward. Adjust to match the actual FC before locating a side-guard USB opening.'),
 'BottomPlateShape':('Rounded rectangle','Bottom plate outline','Base outline before centre widening, arm-matched tabs and applied cutouts. Reaches and width retain their existing meaning. Check fastener support after narrowing an end.',PLATE_SHAPES),
 'MidPlateShape':('Rounded rectangle','Mid plate outline','Independent mid-plate base outline. The fitted front-arm tabs still follow the actual arms; changing the base does not move mounting holes.',PLATE_SHAPES),
 'TopPlateShape':('Rounded rectangle','Top plate outline','Top outline before strap slots, camera sockets, front edge profiles and custom cuts. Tapered ends may require more width for standoffs and camera tabs.',PLATE_SHAPES),
 'ClampPlateShape':('Rounded rectangle','Clamp plate outline','Base shape for the active upper or lower arm clamp. Existing stack and arm fixings retain their positions.',PLATE_SHAPES),
 'PlateEndWidth':(95.,'Plate end width','Narrow-end width as a percentage of the base width for tapered, hexagonal and shield outlines. Does not alter the independently widened centre. 100 percent removes the taper.'),
 'ArmBeamShape':('Straight','Arm beam profile','Changes the beam outline around its straight centreline. Root references, bolt positions and motor centres remain fixed. The shaping begins beyond the arm bolts and widened root shoulder.',ARM_BEAM_SHAPES),
 'ArmProfileAmount':(30.,'Arm profile widening','Maximum extra beam width as a percentage of Arm width. Arm width remains the minimum beam stock width. Zero removes extra widening. Choose Straight for an unshaped solid beam. Root fitting and plate-following tabs use the finished profile.'),
 'MotorPadBlendRadius':(2.,'Rotated pad transition radius','Rounds inward junctions near a rotated motor pad using a 2D rolling-radius blend. Adds local supporting material without rounding the carbon thickness edges. Zero keeps the original junction. Reduce if a large radius cannot be built.'),
 'MotorPadNeckLength':(10.,'Motor pad neck length','Length of the root-facing neck on the twelve replacement pad outlines. Optional reliefs are placed here, away from the motor bearing and screws.'),
 'MotorPadRelief':('None','Additional pad cutouts','Optional neck relief on the twelve replacement motor-pad outlines. Neck length and the cutout dimensions set the available material. Holes and slots rotate with the pad and are checked against mounting hardware and outline material.',MOTOR_PAD_RELIEFS),
 'MotorPadReliefWidth':(3.,'Pad cutout width / diameter','Slot width or circular relief diameter on the new pad outlines. Paired openings keep at least Minimum web between them. The native builder checks remaining edge and screw support.'),
 'MotorPadReliefLength':(6.,'Pad cutout slot length','Overall slot length along the motor-pad axis. Used by Neck slot and Twin neck slots; ignored for twin circular holes. Must be at least the width.'),
}

OPTIONS.update({name:(0.0,label,'Target plan-view corner radius in mm; zero keeps the finished plate unchanged. Rounds outer edges and outline notches after cutting. Closed cutout corners are included only when Round internal openings is enabled for this plate. Tight corners use smaller local radii to preserve edge lengths, mounting support and minimum web; constrained corners are reported. Circular drills, tangent slots, plate thickness and countersinks retain their geometry.') for name,label in [('BottomEdgeFillet','Bottom plate / cutout fillet'),('MidEdgeFillet','Mid plate / cutout fillet'),('TopEdgeFillet','Top plate / cutout fillet'),('ClampEdgeFillet','Clamp plate / cutout fillet')]})

OPTIONS['CameraForeAftOffset']=(0.0,'Camera forward / backward offset','Additional camera translation in frame Y: positive moves toward the front, negative toward the rear. Added to Automatic centre or Custom position. Moves the camera, fixing holes/slots and flexible interfaces together; captured tabs and tilt settings remain fixed. Automatic travel support can grow the middle side-wall bearing area; disable it to retain a fixed wall outline. Actual component and material clearances still apply.')

OPTIONS['CameraAutoExtend']=(True,'Support camera travel automatically','Extend only the middle bearing area of each camera side plate when fore/aft travel needs more screw, slot or TPU flange support. Captured top/bottom tabs and their plate sockets keep their current positions. Disable to keep a fixed wall outline. Real body, edge and height clearances remain checked.')
OPTIONS.update({key:(False,label,'Opt in to rounding closed airflow/cutout boundaries using the plate fillet radius. Disabled preserves internal openings; external corners and outline notches still use the plate fillet. Circular drills and tangent slots remain unchanged.') for key,label in [('BottomFilletOpenings','Round bottom internal openings'),('MidFilletOpenings','Round mid internal openings'),('TopFilletOpenings','Round top internal openings'),('ClampFilletOpenings','Round clamp internal openings')]})

OPTIONS.update({'ArmEdgeFillet':(0.0,'Arm corner fillet','Adaptive beam/motor-pad corner radius from the root outward. The root outline and mounting stock remain unchanged; radii reduce locally to preserve material.'),'ArmFilletOpenings':(False,'Fillet arm internal openings','Also round corners in arm cutouts. Disabled by default; circular fixing holes remain circular.')})

from .bottom_nose import NOSE_SHAPES
OPTIONS.update({
 'BottomNoseShape':('Straight','Front edge shape','Trim only the absolute front of the bottom plate. Straight retains the existing outline. The nose never extends beyond the front reach. Arm and standoff positions stay fixed.',NOSE_SHAPES),
 'BottomNoseDepth':(6.,'Front edge depth','Fore/aft shaping depth in mm. Convex noses retreat at the shoulders; concave noses retreat at the centre. Keep enough stock around front standoffs and camera sockets.'),
 'BottomNoseTipWidth':(35.,'Front tip width','Width of the flat front tip as a percentage of the nose span. Used by flat-tip, swept, stepped and recessed profiles; other profiles ignore it.')})

from .appearance import PRINTED_COLOURS
OPTIONS['PrintedPartColour']=('Black','Printed part colour','Shared matte display colour for camera isolation pads/inserts, motor protectors, electronics side guards and the LiPo pad. Changes appearance only; dimensions, mass and cutting/export profiles are unchanged.',tuple(PRINTED_COLOURS))

from .nut_seats import FIELDS as NUT_FIELDS
OPTIONS.update(NUT_FIELDS)

OPTIONS.update({
 'CameraTabReliefs':(True,'Relieve camera tab shoulders','Round cutter reliefs beside the upper and lower tabs. Removes material from the side-plate body only; tab width and mating sockets stay unchanged.'),
 'CameraTabCutterDiameter':(2.0,'Camera tab cutter diameter','Milling cutter diameter for tab-shoulder reliefs. Relief depth into the plate is half this diameter: 1 mm cutter gives 0.5 mm depth, 2 mm gives 1 mm. Use the actual cutter diameter.')})

from .bottom_nose import REAR_SHAPES
for prefix,plate in (('BottomRear','Bottom'),('MidRear','Mid'),('TopRear','Top')):
 OPTIONS[prefix+'Shape']=('Straight','Rear edge shape','Trim the rear inside its existing reach. Mounting locations and required material remain checked. Bottom rear shaping is available only in two-plate mode; mid rear shaping only in three-plate mode.',REAR_SHAPES)
 OPTIONS[prefix+'Depth']=(6.,'Rear edge depth','Fore/aft depth of the rear shaping zone in mm; never adds stock beyond the rear reach.')
 OPTIONS[prefix+'TipWidth']=(35.,'Rear feature width','Feature half-width as a percentage of the rear half-span. Controls flats, stepped tips and central cable/recess openings where applicable.')
OPTIONS['CameraTabBottomRearOffset']=(0.,'Bottom rear tab offset','Independent tab shift along frame Y in mm: positive is forward. Matching sockets and cutter reliefs follow. Camera, side-wall position and tilt stay fixed. Keep the tab inside its contact edge.')
OPTIONS['CameraTabBottomFrontOffset']=(0.,'Bottom front tab offset','Independent tab shift along frame Y in mm: positive is forward. Matching sockets and cutter reliefs follow. Camera, side-wall position and tilt stay fixed. Keep the tab inside its contact edge.')
OPTIONS['CameraTabTopRearOffset']=(0.,'Top rear tab offset','Independent tab shift along frame Y in mm: positive is forward. Matching sockets and cutter reliefs follow. Camera, side-wall position and tilt stay fixed. Keep the tab inside its contact edge.')
OPTIONS['CameraTabTopFrontOffset']=(0.,'Top front tab offset','Independent tab shift along frame Y in mm: positive is forward. Matching sockets and cutter reliefs follow. Camera, side-wall position and tilt stay fixed. Keep the tab inside its contact edge.')

from .bottom_nose import TOP_FRONT_SHAPES
OPTIONS.update({
 'TopFrontShape':('Straight','Front edge shape','Top front outline inside the existing front reach. Camera recesses clear the centre and can set back the shoulders; Straight preserves the existing profile. This profile is the sole built-in top-front camera opening.',TOP_FRONT_SHAPES),
 'TopFrontDepth':(12.,'Front edge depth','Fore/aft shaping depth. For camera recesses, measured behind the set-back shoulder line to the deepest point. Mounting holes and camera tabs retain support checks.'),
 'TopFrontTipWidth':(35.,'Front feature width','Central feature width as a percentage of the front span for flat-tip, swept, stepped and general recessed profiles. Camera-specific recesses use Camera recess width instead.'),
 'TopFrontRecessWidth':(0.,'Camera recess width (0 = auto)','Camera-specific opening width in mm. Zero uses camera width plus twice the top front camera clearance. Flared and swept mouths open up to 20 percent wider; stepped/flared bottoms are narrower. This sets a profile, not a measured guarantee of camera clearance.'),
 'TopFrontSetback':(3.,'Camera shoulder setback','Retract both front shoulders from the current top front reach, in mm. Applied only to camera-specific profiles. Depth is measured from this new shoulder line; the full recess reaches setback plus depth behind the original front.')})

OPTIONS['TopFrontClearance']=(.5,'Camera recess clearance','Extra clearance on each side of the camera body when Camera recess width is automatic. Used only by top-front camera recesses; custom width is used directly.')

OPTIONS.update({
 'DetailedMotorReferences':(False,'Detailed motor references','Replace the cylinders with radial mounting feet, a tall stator and copper windings, bell, M5 shaft and self-locking nut. Diameter/height describe the bell body; the shaft and nut extend above it. Display only.'),
 'DetailedPropReferences':(False,'Three-blade prop references','Curved three-blade references with 3.7-inch geometric pitch, 6 mm hubs and 5.1 mm bores, seated directly on the motor bells. Adjacent motors have mirrored props. The simple-disc height is ignored; clearance uses the full swept blade-height range.'),
 'DetailedStackReference':(False,'Detailed FC / ESC stack','Display two component-populated PCBs and silicone grommets at the existing stack mounting pattern and height. A generic visual model, not an exact electronics footprint.'),
 'DetailedCameraReference':(False,'Detailed FPV camera','Display a shaped camera housing, side fixing recesses and stepped lens with glass. Keeps the current body size, camera position and tilt. The original envelope remains the clearance check.')})

OPTIONS.update({
 'DetailedVTXReference':(False,'Detailed VTX reference','Generic populated VTX board with RF shield, heatsink fins, cable header and RF sockets. Follows the existing VTX size, mounting pattern and plate level; FPV required.'),
 'DetailedBatteryReference':(False,'Detailed LiPo reference','Generic shrink-wrapped LiPo with end protection, cell seams, label, leads and an XT-style plug. Dimensions describe the pack body; schematic leads extend beyond it. Follows its position, rotation and top/bottom mounting; requires the LiPo reference.')})
