"""Optional camera isolation, motor protectors and side guards."""
GUARD_VENT_SHAPES=('Horizontal slots','Rounded slots','Ellipses','Hexagons','Diamonds','Chevrons','Circles','Triangles','Inverted triangles','Octagons','Slanted slots','Arrows','Shields','Teardrops','Crosses','Hourglasses')
FLEX_OPTIONS={'FlexCameraMode': ('Hard mount',
                    'Camera attachment',
                    'Hard mount retains the original side plates. Compression pads widen the cage for two pressed '
                    'pads. Captured inserts replace the side-plate screw openings with retained flexible inserts; tilt '
                    'settings and screw paths stay unchanged.',
                    ('Hard mount', 'Compression pads', 'Captured inserts')),
 'FlexPadThickness': (2.0,
                      'Camera pad thickness',
                      'Free thickness of each pad between the camera and side plate. Soft modes set their own side '
                      'spacing; the ordinary Camera side clearance applies only to Hard mount.'),
 'FlexPadPreload': (0.15,
                    'Camera pad compression',
                    'Per-side compression allowance. Printed free material extends this far into the nominal camera '
                    'side; adjust after a test print.'),
 'FlexPadWidth': (16.0,
                  'Camera pad length',
                  'Compression-pad size along the frame front/rear direction; captured inserts use the opening size '
                  'and retaining lip instead.'),
 'FlexPadHeight': (16.0,
                   'Camera pad height',
                   'Compression-pad vertical size; must contain the complete existing tilt screw paths with supporting '
                   'material.'),
 'FlexInsertWidth': (14.0,
                     'Insert opening length',
                     'Length of the carbon opening along frame Y, using the selected camera interface outline.'),
 'FlexInsertHeight': (16.0,
                      'Insert opening height',
                      'Vertical opening size in the carbon camera side plates. The original tilt holes and arcs are '
                      'cut in the insert instead.'),
 'FlexInsertLip': (1.5,
                   'Insert retaining lip',
                   'Flange overlap around the carbon opening on the selected retaining-lip faces.'),
 'FlexInsertFit': (0.15,
                   'Insert fit clearance',
                   'Radial clearance between the printed insert neck and its carbon opening. Positive values loosen '
                   'the fit.'),
 'FlexDensity': (1.21,
                 'Flexible material density',
                 'Nominal printed TPU/silicone density in g/cm3 for volume-based mass estimates; adjust for your '
                 'actual print/material.'),
 'FlexInterfaceShape': ('Rounded rectangle',
                        'Camera interface outline',
                        'Choose a rounded rectangle or a scaled plain side-wall silhouette, without locating tabs. '
                        'Captured openings and matching TPU necks use the insert corner radius. Compression-pad '
                        'outlines retain their existing geometry.',
                        ('Rounded rectangle', 'Side plate outline')),
 'FlexMotorProtectors': (False,
                         'Create motor-pad protectors',
                         'Generate four separate TPU cups matching the selected pad shape, rotation and actual arm '
                         'thickness. They are excluded from carbon cutting profiles.'),
 'FlexProtectorWall': (2.0,
                       'Protector wall thickness',
                       'Material outside the measured motor-pad outline; follows scallops, rotation and neck shape.'),
 'FlexProtectorFloor': (1.6,
                        'Protector underside thickness',
                        'Base beneath the carbon arm. Motor-screw retention needs screws longer by this amount; verify '
                        'motor thread depth.'),
 'FlexProtectorFit': (0.25,
                      'Protector fit clearance',
                      'Radial clearance around the actual carbon outline. Print a fit sample for the selected TPU.'),
 'FlexProtectorLanding': (3.0,
                          'Landing foot height',
                          'Extra downward perimeter foot below the cup floor. Zero keeps a flat underside. Screw and '
                          'shaft access remain open.'),
 'FlexProtectorRetention': ('Motor screws',
                            'Protector screw access',
                            'Motor screws keeps small fixing holes. Linked screw access joins larger screw-head '
                            'clearances to the shaft opening using radial slots; no tie tunnels are created.',
                            ('Motor screws', 'Linked screw access')),
 'FlexSideGuards': (False,
                    'Create electronics side guards',
                    'Create separate left/right guards. Plate-edge wrap covers the plate edges; Between plates moves the wall inside the plate outlines with its ends bearing against the bottom/mid and top plate faces for clamping. The foremost covered post uses the available '
                    'height; intermediate FC sleeves use upper 10 mm and rear sleeves middle 6 mm. '
                    'Inboard grip surfaces are circular to preserve electronics space.'),
 'FlexGuardWall': (2.0, 'Side guard thickness', 'Thickness of the protective side panels and post clips.'),
 'FlexGuardFit': (0.25,
                  'Side guard post clearance',
                  'Diametral fit allowance around the actual metal standoffs. Test the sleeves using your material and '
                  'printer.'),
 'FlexGuardClearance': (1.0,
                        'Side guard plate clearance',
                        'Plate-edge wrap: outward gap from the finished plate edges. Between plates: inward setback of the outer wall face from those edges; the full wall thickness sits beneath the plates. '
                        'Between plates has nominal contact with both plate faces, without a vertical assembly gap. '
                        'Standoff fit clearance remains independent.'),
 'FlexGuardStyle': ('Vented',
                    'Side guard style',
                    'Solid panels cover the bay. Vented panels use the selected opening shape, rows and dimensions '
                    'while preserving bearing regions.',
                    ('Solid', 'Vented')),
 'FlexGuardSlotHeight': (3.0,
                         'Side guard slot height',
                         'Airflow opening height; limited to retain top and bottom material.'),
 'FlexGuardSlotCount': (2,
                        'Side guard slot rows',
                        'Whole-number count of airflow rows (1 to 6); actual openings fit the available '
                        'panel height.'),
 'FlexGuardFrontInset': (0.0,
                         'Side guard front inset',
                         'Shorten the main wall from the foremost covered row while its full-height circular sleeve '
                         'remains attached by the outboard support.'),
 'FlexGuardRearInset': (0.0,
                        'Side guard rear inset',
                        'Shorten the main wall from the rear attachment row; a broad bearing pad retains the complete '
                        'middle 6 mm sleeve.'),
 'FlexGuardExtendFront': (False,
                          'Extend to foremost posts',
                          'Extend the side guards to the actual foremost standoff row, including an added forward '
                          'pair, while retaining the FC-row bearings.'),
 'FlexGuardVentShape': ('Horizontal slots',
                        'Vent shape',
                        'Opening profile used by Vented side guards. Individual repeated shapes use vent width and '
                        'web; horizontal slots span each clear post bay.',
                        GUARD_VENT_SHAPES),
 'FlexGuardVentWidth': (10.0,
                        'Vent width',
                        'Fore/aft size of individual repeated vent shapes; horizontal slots use the clear bay length.'),
 'FlexGuardVentWeb': (3.0, 'Vent web', 'Minimum spacing between repeated openings and their bearing regions.'),
 'FlexGuardUSBEnabled': (False,
                         'USB access opening',
                         'Cut an adjustable USB cable/connector opening in the extended side guard. Place it clear of '
                         'the bearing sleeves.'),
 'FlexGuardUSBSide': ('Left',
                      'USB access side',
                      'Choose the side that carries the FC USB connector.',
                      ('Left', 'Right', 'Both')),
 'FlexGuardUSBY': (0.0,
                   'USB fore/aft offset',
                   'Opening centre relative to FC stack Y. Positive moves forward; negative moves rearward.'),
 'FlexGuardUSBZ': (12.0, 'USB centre above carrier', 'Opening centre height above the lower carrier plate. Near the guard top, the opening continues through the top edge instead of leaving a fragile strip.'),
 'FlexGuardUSBWidth': (14.0,
                       'USB opening width',
                       'Fore/aft clear opening size, including room for the cable plug housing.'),
 'FlexGuardUSBHeight': (8.0,
                        'USB opening height',
                        'Vertical clear opening size, including room for the cable plug housing.')}
FLEX_ROLES=('CameraPadLeft', 'CameraPadRight', 'MotorProtectorFrontRight', 'MotorProtectorFrontLeft', 'MotorProtectorRearLeft', 'MotorProtectorRearRight', 'ElectronicsGuardLeft', 'ElectronicsGuardRight')

FLEX_OPTIONS.update({
 'FlexGuardFitMode':('Plate-edge wrap','Side guard fit','Plate-edge wrap keeps the original lips covering the plate edges. Between plates moves the wall inward beneath the plate edges and seats its ends against the bottom/mid carrier and top plate for clamping. Plate clearance sets the inward setback. Top-plate strap passages receive 2 mm clearance underneath. Its motor-wire opening joins the front and rear positions into one continuous cutout.',('Plate-edge wrap','Between plates')),
 'FlexGuardVTXOpening':(False,'VTX clearance opening','Leave room for a wider VTX through the selected guard wall. Follows the VTX envelope position and size; independent of ventilation. Requires FPV mode. Openings near the lower edge continue through it; standoff sleeves and a top web must remain intact.'),
 'FlexGuardVTXSide':('Both','VTX opening side','Choose which guard receives the VTX clearance opening.',('Left','Right','Both')),
 'FlexGuardVTXY':(0.,'VTX opening fore/aft offset','Opening centre offset from VTX centre Y. Positive is forward, negative rearward.'),
 'FlexGuardVTXZ':(0.,'VTX opening vertical offset','Opening centre offset from the VTX envelope centre height. Positive raises the opening; negative lowers it.'),
 'FlexGuardVTXLength':(0.,'VTX opening length','Fore/aft clear length. Zero follows VTX envelope length plus twice the opening clearance; a positive value is the exact custom length.'),
 'FlexGuardVTXHeight':(0.,'VTX opening height','Clear vertical height. Zero follows VTX envelope height plus twice the opening clearance; a positive value is the exact custom height.'),
 'FlexGuardVTXClearance':(1.,'VTX opening clearance','Extra space on each edge for automatically sized dimensions. Custom length/height already include their desired clearance.')})

FLEX_OPTIONS.update({'FlexGuardWireEnabled': (False, 'Motor-wire bottom openings', 'Open the lower edge for motor wires. Front and rear positions are independent and referenced to the FC stack. Openings preserve actual grip bands; rear exits may pass underneath raised grips and open through the rear end.'), 'FlexGuardWireSide': ('Both', 'Motor-wire side', 'Choose which side guards receive wire openings.', ('Left', 'Right', 'Both')), 'FlexGuardWirePairs': ('Both', 'Motor-wire positions', 'Create front, rear or both bottom-edge openings on each selected side.', ('Front', 'Rear', 'Both')), 'FlexGuardWireFrontY': (16.0, 'Front wire fore/aft offset', 'Front opening centre relative to the FC stack. Positive is forward; negative is rearward.'), 'FlexGuardWireRearY': (-20.0, 'Rear wire fore/aft offset', 'Rear opening centre relative to the FC stack. Negative moves rearward, including beneath raised standoff grips or through the rear end if height permits.'), 'FlexGuardWireWidth': (10.0, 'Motor-wire opening width', 'Clear fore/aft width for each wire bundle. Leave room for insulation and movement; retain material around the actual grip height.'), 'FlexGuardWireHeight': (5.0, 'Motor-wire opening height', 'Clear height above the local carrier top. The cut extends down through the plate-height skirt automatically, keeping wire space unchanged. Rounded upper corners soften the wire exit.')})

FLEX_OPTIONS.update({'FlexGuardVTXVents': (True,
                       'VTX section vents',
                       'Enable vents in the rear section. Requires Vented style.'),
 'FlexGuardFCVents': (True,
                      'FC section vents',
                      'Enable vents in the forward section. Disable for VTX-only ventilation.'),
 'FlexGuardVentBoundaryOffset': (0.0,
                                 'Vent boundary offset',
                                 'Shift the section boundary from the rear FC stack mounting-hole '
                                 'row (stack Y minus half its spacing). Positive moves forward; '
                                 'negative moves rearward. Limited to the guard ends.'),
 'FlexGuardFCVentShape': ('Horizontal slots',
                          'FC vent shape',
                          'Opening shape used only in the FC section.',
                          GUARD_VENT_SHAPES),
 'FlexGuardFCVentWidth': (10.0,
                          'FC vent width',
                          'Fore/aft width of repeated openings. Horizontal slots span each clear '
                          'FC section/post bay.'),
 'FlexGuardFCVentWeb': (3.0,
                        'FC vent web',
                        'Minimum material between openings, posts and section edges; never less '
                        'than guard thickness.'),
 'FlexGuardFCSlotHeight': (3.0,
                           'FC vent height',
                           'Requested opening height, reduced to fit the local available wall.'),
 'FlexGuardFCSlotCount': (2,
                          'FC vent rows',
                          'One to six whole-number rows. Shallow upper strips can use '
                          'fewer rows.'),
 'FlexGuardVTXVentRearInset': (0.0,
                               'VTX vent rear inset',
                               'Extra solid material at the rear edge of the VTX vent region.'),
 'FlexGuardVTXVentFrontInset': (0.0,
                                'VTX vent front inset',
                                'Extra solid material at the front edge of the VTX vent region.'),
 'FlexGuardFCVentRearInset': (0.0,
                              'FC vent rear inset',
                              'Extra solid material at the rear edge of the FC vent region.'),
 'FlexGuardFCVentFrontInset': (0.0,
                               'FC vent front inset',
                               'Extra solid material at the front edge of the FC vent region.'),
 'FlexGuardVTXVentZOffset': (0.0,
                             'VTX vent vertical offset',
                             'Move VTX rows up (positive) or down (negative), limited to retain '
                             'top and bottom webs.'),
 'FlexGuardFCVentZOffset': (0.0,
                            'FC vent vertical offset',
                            'Move FC rows up (positive) or down (negative), limited to retain top '
                            'and bottom webs.')})

for _key,_label in (('FlexGuardVentShape','VTX vent shape'),('FlexGuardVentWidth','VTX vent width'),('FlexGuardVentWeb','VTX vent web'),('FlexGuardSlotHeight','VTX vent height'),('FlexGuardSlotCount','VTX vent rows')):
 _v=FLEX_OPTIONS[_key]
 FLEX_OPTIONS[_key]=(_v[0],_label,'VTX section only. '+_v[2])+_v[3:]

FLEX_OPTIONS.update({'FlexGuardCloseFront':(False,'Close sides to camera plates','Add a solid full-height panel ahead of the foremost standoffs down to the bottom plate, tapering to the actual camera side plates. Includes foremost post coverage. Requires FPV camera side plates; camera tilt stays unchanged.'),'FlexGuardCameraOverlap':(3.0,'Camera plate landing length','Length of the guard landing along the outside rear edge of each camera side plate. Nominal face contact; carbon and camera screw access are relieved automatically. Between plates seats against the frame plate faces; Plate-edge wrap uses plate clearance 0 mm for nominal edge contact.')})

FLEX_OPTIONS.update({
 'FlexInsertCornerRadius':(1.0,'Insert opening corner radius','Round the carbon opening and matching TPU neck, including Side plate outline shapes. Local radii reduce on short edges to keep the rounded profile connected. Tilt screw paths are unchanged.'),
 'FlexInsertLipSide':('Both sides','Retaining lip faces','Inside faces the camera; outside faces away from it. Select a retaining flange on either face or both. The soft camera contact and through-plate neck remain in every mode.',('Both sides','Outside only','Inside only'))})

from .front_bumper import FIELDS as BUMPER_FIELDS
FLEX_OPTIONS.update(BUMPER_FIELDS)
FLEX_ROLES=FLEX_ROLES+('FrontBumper',)

_v=FLEX_OPTIONS['FlexGuardWireFrontY']
FLEX_OPTIONS['FlexGuardWireFrontY']=(_v[0],_v[1],_v[2]+' Front exits follow stepped lower edges and are trimmed around bearing sleeves with a local 0.8 mm buffer. The usable opening can narrow beside a grip; adjust width/height and inspect the model.')

FLEX_OPTIONS.update({
 'FlexGuardStraps':(False,'Battery strap openings','Open one or two strap passages through the selected edge of both side guards. Keep their full width clear of standoff grips.'),
 'FlexGuardStrapCount':('2 straps','Strap opening count','Create one front opening or a front/rear pair on each side guard.',('1 strap','2 straps')),
 'FlexGuardStrapAuto':(True,'Follow plate strap positions','Use +Strap fore/aft offset for one strap and both +/- offsets for two. Positions follow the existing top-plate slots even when those slots are disabled.'),
 'FlexGuardStrapY1':(18.,'Front strap offset','Custom opening centre relative to the FC stack along frame Y. Positive is forward.'),
 'FlexGuardStrapY2':(-18.,'Rear strap offset','Independent second opening centre relative to the stack. Used for two straps; negative is rearward.'),
 'FlexGuardStrapWidth':(20.,'Strap opening width','Clear fore/aft opening span in mm. Allow room for the actual strap width and assembly movement.'),
 'FlexGuardStrapDepth':(6.,'Strap opening depth','Clear depth inward from the chosen guard edge. The cut opens through that edge and retains material at the opposite edge.'),
 'FlexGuardStrapEdge':('Top edge','Strap opening edge','Top edge lets straps pass beneath/around the top plate. Bottom edge opens the lower carrier skirt (mid plate in three-plate mode, bottom plate in two-plate mode).',('Top edge','Bottom edge'))})

# Explain the shared controls in both fit modes without changing saved values.
for _name,_extra in {
 'FlexGuardWireEnabled':' Between plates joins the front and rear positions into one wide opening on each selected side.',
 'FlexGuardWirePairs':' Used only by Plate-edge wrap; Between plates always spans both saved positions.',
 'FlexGuardWireFrontY':' In Between plates this sets one end of the combined span.',
 'FlexGuardWireRearY':' In Between plates this sets the other end of the combined span.',
 'FlexGuardWireWidth':' Between plates adds this width to the distance between the front and rear centres.',
 'FlexGuardVTXOpening':' A fully covering opening also permits lateral VTX overhang beyond the plates while retaining mounting-hole support and collision checks.'
}.items():
 _entry=FLEX_OPTIONS[_name];FLEX_OPTIONS[_name]=(_entry[0],_entry[1],_entry[2]+_extra)+_entry[3:]
