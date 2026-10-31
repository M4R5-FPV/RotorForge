# Namespaced workbench migration — 0.38.0

## Guidance checked

- Current FreeCAD Addon Template: https://github.com/FreeCAD/Addon-Template/tree/cookie
- The former starter kit explicitly redirects to that template: https://github.com/FreeCAD/freecad.workbench_starterkit
- FreeCAD workbench documentation: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Workbench_creation.md

The current template uses a native `freecad` namespace with no `freecad/__init__.py`,
a lightweight package entry point, `init_gui.py`, a workbench class, packaged
resources, `package.xml` and `pyproject.toml`. FreeCAD still supports the classic
layout; this migration follows the requested namespaced choice rather than
claiming classic layouts are unsupported. The template is boilerplate, so the
existing tested editor and geometry modules are retained rather than replaced
by example commands.

## Implementation

The canonical implementation is now `freecad.rotorforge`. GUI registration is
idempotent and only imports the workbench class; editor commands and geometry
remain lazy until activation. Headless package import does not load Qt, Part or
FreeCADGui. Icons and runtime manuals are packaged under the namespace and
resolved from the installed package, so both manual Mod installation and a built
wheel use the same paths. The outer `RotorForge` directory and workbench/command
IDs stay stable. Python wheels do not supply FreeCAD itself.

`rotorforge.document` is an intentional compatibility import bridge. Old FCStd
files serialize that module path; the bridge resolves to the exact canonical
module and classes rather than duplicating proxy types. New saved documents use
`freecad.rotorforge.document`. JSON schemas and geometry algorithms are unchanged.
No top-level legacy initialization hooks remain. Install by replacing the old
folder completely; merging can leave obsolete startup hooks behind.

## Development

From the repository root, run `python -m unittest discover -s tests` for portable
checks. Native `tests/freecad_*_smoke.py` scripts run in FreeCAD's own Python
runtime. Use `python -m build` to produce a wheel and source distribution; the
wheel includes the namespace, legacy proxy bridge, icons and runtime manuals.
Manual installation of the ZIP in FreeCAD's user Mod folder remains the normal
user workflow and needs no pip packages.


## 0.48 design choices

The VTXMountHeight value is retired and ignored; updating the frame removes its
old property and seats the VTX reference directly on its bottom/mid carrier.
FC spacer and stack heights are unaffected.

Pad choices after Scalloped shield are replaced by twelve compact platforms.
Imports map retired pad names to a replacement and issue a warning. Review the
changed outline, pad-beginning pivot, reliefs and hardware fit before machining.
Former nose relief options become neck reliefs on the replacement platforms.
The six former shaped beams map to the nearest new taper/shoulder family;
Straight remains unchanged. The windowed beam choices were subsequently retired in 0.49.

## 0.51 flexible parts

New Flex-prefixed fields default to Hard mount and rear modules disabled. Old
settings keep their geometry. The former optional-part field names stay retired
and are ignored on import. Activate the new TPU choices explicitly. Update frame
adds the new parts and captured camera windows when selected.

## 0.52.0 rear mount

Existing accessory switches are retained and now build one RearAccessoryMount. Update removes the old generated rear components. Existing ELRS Open cradle settings migrate to Split clips; Protective shell migrates to Slide-in eyes. The retired ELRS stem-depth setting is ignored. Review the default two-rearmost attachment selection, fit standoff height, and antenna clearance after loading an older frame. Camera settings are preserved.

## 0.53.0 arrangement and finishing

Existing rear accessory switches are preserved. Update rebuilds them in the new fixed arrangement: GPS low and rearmost, ELRS low in front of GPS, VTX above. Recheck antenna/wiring clearances and fit the standoff height after loading an older frame. GPS tilt defaults to zero. Camera interfaces default to the original rounded rectangle, and all new plate fillet radii default to zero.

## 0.55.0 automatic rear fitting

Rear collars and side panels now follow the actual selected post span. The manual rear-height fitting button is removed; the frame's configured standoff height remains unchanged. Accessory dimensions are not added together in height, and physical pockets/bores are not scaled. Large aft housings can extend below the carbon carrier outside the frame. Review ground and prop clearance after updating older mounts. New independent carrier width fields default to zero (automatic). Existing camera mounting and tilt settings are retained.

## 0.56.0 corner fillets

Persistent fillet fields are unchanged, and zero retains the existing geometry. Positive values now act as target maximum radii with local reduction near short edges, hardware and thin webs. Sharp internal cutout and outline-notch corners are included. Read the FreeCAD report for adaptations or any retained constrained corners, and re-export CNC profiles after updating.

## 0.57.0 open rear mount and travel support

Updating rebuilds saved rear mounts using the shared open yoke and local fittings.
All accessory switches, measured sizes, post selection and tilt values are retained.
Check antenna insertion, wire routing and physical retention before printing.
ELRS stem/cable clearance defaults to 5 mm; enter your measured junction size.

New per-plate internal-opening fillet switches default to off, including when
loading older designs. Enable the appropriate switch explicitly if you want the
closed cutout rounding used in 0.56. Outside corner/notch radii remain saved.

Automatic camera travel support defaults to on. It only grows the middle of a
side plate when the current screw/slot or flexible-interface support needs it;
the existing attachment edges, tongues and sockets do not move. Disable it to
retain a fixed wall profile. Rebuild and re-export camera profiles after changing
travel. Existing tilt, height and placement controls keep their meaning.

## 0.58.0 reinforced rear bridge and protectors

Updating rebuilds an enabled rear mount with the reinforced bridge and overlapping
fitting arrangement. Existing hardware dimensions and accessory switches remain.
New sleeve grip defaults to 8 mm below the top plate; zero uses the complete
exposed span. Rear hardware behind the covering plate can extend above/below the
frame. A compact bridge requires a genuinely rearward post pair; a warning
identifies excessive reach. Recheck all antenna and GPS fit before printing.

Motor protectors and electronics side guards default off. Activating them adds
separate printable objects and export files without changing carbon outlines.
Side guards and an active rear mount share separate lower/upper post bands.
Camera isolation, travel and tilt controls, motor pad shapes and internal-opening
fillet selection keep their previous meaning.

## 0.59 rear datums and arm finishing

Saved rear attachment-count, grip-height, offset and yoke-vent fields remain
readable but no longer drive the new geometry. Only the actual rearmost pair is
used. Fixed middle guard bands determine the upper VTX and lower GPS sleeve
heights independently of side-guard activation. Updating removes the old combined
rear feature and creates the enabled separate parts; existing carbon geometry
and camera controls are retained. Fit may need review because old long reaches
are blocked instead of routed sideways. Arm fillets default to zero and internal
opening fillets default off. Installation remains a complete folder replacement.

## 0.60 protection and root preservation

The rear accessory generator and all its controls are removed. Its saved fields
are ignored on import; Update removes its old document objects and properties.
The PCB VTX fixing patterns and reference envelope remain available under FPV.
The old motor-guard tie choice imports as Linked screw access, creating larger
connected service openings without transverse tunnels. Side guards default to
their previous reach; forward FC-row extension and USB access are opt-in. The new
arm-fillet boundary preserves the complete mounting root, including fitted joints
and bolt-support stock; arm radius and internal-opening choices stay editable.

## 0.61 saved-frame performance

Opening a saved frame now reads its existing settings without adding/removing
properties or regenerating components. The saved solids remain until a real
parameter change or Update frame. Update performs the same migration and exact
checks as before, including removal of retired rear parts. A failed geometry
attempt is not repeated by every dependent part during the same recompute.
Correcting parameters or explicitly updating permits another attempt. No saved
frame dimensions or native file contents are rewritten merely by opening them.

## 0.62 front guard sleeves

No new parameters are required. The forward end now grips the full exposed post
height, and Extend to foremost posts selects the actual maximum-Y row. The saved
forward-extension boolean retains its meaning. Inboard grip shoulders are round
and their support bridges extend outward. Intermediate and rear band heights are
retained. Open an existing frame and apply Update frame once to replace its saved
guard solids; the fast, non-regenerating restore behavior remains in place.

Motor-wire access: TPU → Side guards → Motor-wire access. Enable bottom openings, choose sides and front/rear positions, then set offsets from the stack and opening width/height. Existing designs keep the openings off; click Update frame after enabling them. Keep them clear of grips and the mid-plate height transition.

Side-guard ventilation: choose Vented style under TPU → Side guards, then use TPU → Side guard vents. VTX and FC sections have independent enable switches and shape, size, row, web, inset and vertical-position controls. The shared boundary starts at the rear stack mounting-hole row. Disable FC vents for VTX-only ventilation. Earlier single vent settings seed both sections. Restart FreeCAD after installing and use Update frame to regenerate saved guard solids.

Set TPU → Side guards → Side guard plate clearance to 0 mm for nominal plate contact, then click Update frame. Standoff fit remains independently adjustable.

Rear motor-wire pockets may pass below raised standoff grip bands, including through the rear guard end. Move Rear wire fore/aft offset backward (negative) and keep the pocket height low enough to retain the required supporting web below each grip. Use Update frame after adjusting a saved design.

Bottom front shapes: Frame → Bottom plate → Front edge. Choose Straight, Rounded nose, Pointed nose, Flat-tip nose, Swept shoulders, Concave nose, V-notch or Twin lobes. Depth controls the shaping zone; tip width applies to flat-tip and swept profiles. Shapes trim only the bottom nose within its front reach. Reduce depth or increase reach if camera or fastener support checks fail. Existing designs keep Straight until changed. Restart FreeCAD after installing and use Update frame to regenerate a saved frame.

VTX and FC vent rows are whole-number counts (1 to 6), without millimetre units. Older fractional counts retain their previous rounding on load. Update frame converts the saved FreeCAD row properties to bounded integers.

TPU / Side guards / Forward coverage: Close sides to camera plates adds a full-height tapered forward panel down to the bottom plate, with a 1–8 mm outside camera-plate landing. Requires FPV side plates; existing frames default to disabled. Set plate clearance to zero for nominal contact. Ten additional vent profiles are available independently under TPU / Side guard vents. Restart FreeCAD and Update frame to regenerate saved designs.

The forward camera enclosure starts its lower skirt at the foremost standoff row. It preserves the FC/front-arm lower edge and the original wire-notch height behind that row. Update frame to replace older generated guards.

Incremental updates: unchanged component geometry and verified clearance results are reused. Edited parts and their dependencies rebuild automatically; side-guard opening edits can reuse their solid shells. Save the FCStd after updating to retain component provenance and cached geometry across reopen. Older documents need one update to establish the current cache. Frame Parameters / 09 Results exposes LastBuildSeconds, RebuiltComponents and ReusedComponents. Initial creation and broad layout changes still require the corresponding geometry.

Version 0.68.0 adds TPU / Appearance / Printed part colour. Existing settings default to Black. Colour changes affect the printed/soft parts and LiPo pad only; geometry, cutting profiles and mass estimates are reused. Restart FreeCAD after replacing the installed folder.

Version 0.70.0: Hardware references replace the earlier auxiliary tools. Retired display objects are cleaned up when opening Hardware references or updating a frame. Nut retention defaults to external hex nuts; optional pockets and press-nut bores require an explicit frame update.

Version 0.71.0 adds optional FC stack press nuts and removes VTX retention seats. Update existing frames once to regenerate their plate holes. FC stack lift and upper-nut positions follow the selected flange dimensions automatically. From 0.71.1, the stack sits directly on the exposed flange and ignores the manual spacer setting in press-nut mode.

Version 0.72.0 enables camera tab-shoulder cutter reliefs by default (2 mm cutter, 1 mm depth). Update existing FPV frames and re-export cutting profiles to apply them. Disable Relieve camera tab shoulders to retain the former outline. Tab and mating socket dimensions are unchanged.

Version 0.73.0 extends existing side guards across the carrier/top plate thickness. Update frame to apply the new height. Grip bands, USB and vent positions remain anchored to their former internal references. Motor-wire opening height remains measured above the carrier; cuts extend to the new lower edge automatically. Front closure still starts at the foremost posts. Local carbon and propeller reliefs take priority over full-height coverage.

Version 0.73.1 synchronizes previously created hardware references after valid frame edits. Selected groups and visibility remain saved. Existing saved references gain update metadata on the next frame update; opening the hardware dialog alone does not enable references.

Version 0.73.2 repairs guard generation at plate-height lip / standoff sleeve joins. Update the frame with your existing settings; no geometry adjustments or larger plate clearance are needed for this cleanup failure.

Version 0.74.0 rounds captured insert openings, including Side plate outline profiles. Existing settings default to Both sides retaining lips and a 1 mm opening corner radius. Update the frame and re-export carbon profiles and printed inserts as a matching set. Camera position and tilt settings are retained.

Version 0.75.0 keeps all new rear edge selectors Straight and all four camera tab offsets at zero when older settings are loaded. Existing dimensions and front profiles remain unchanged. Edit Frame > Bottom/Mid/Top plate for rear shapes and FPV > Side plates > Tab positions for signed offsets; update and re-export matching carbon profiles after changing them. Hardware references use a black finish on refresh or the next valid frame update.

Version 0.76.0 defaults the new top-front selector to Straight, retaining the previous top outline and FPV lens cutout. Camera-specific recesses can retract the outer shoulders and clear the centre independently. Follow plates may reposition the upper camera contact to retain support. After changing an edge profile, update the assembly and re-export matching plate/side-plate profiles. Tilt controls are unchanged.

Version 0.77.0 adds an editor-only cutout locator. Saved cutout data and manufacturing geometry are unchanged. Pattern numbers reflect list order and may change after removal. The editor now retains unapplied edits when selecting a different pattern, and its hidden data field accepts the full 200-pattern capacity without truncation.

Version 0.78.0 removes the separate FPV lens-opening parameters. Older FPV settings with a straight top front translate that opening into a visible Camera U recess, with explicit width/depth and zero shoulder setback. Already selected top-front profiles stay selected and now define the entire opening. Review camera clearance, update the frame, and re-export profiles. Obsolete properties are removed on update.

Version 0.79.0 adds an optional FrontBumper component. It is off for existing settings. Enabling it adds a printed shoe without modifying carbon geometry; update and export FlexibleParts for its separate print model. Test fit and retention using your material and plate thickness.

Version 0.80.0 keeps existing bumper style names and adds eight choices. Front motor-wire offsets now cross lower-edge transitions and trim locally around bearing sleeves; update and re-export the guards to use the revised openings. Their usable width may narrow near a grip.

## 0.81.0 bumper width

Existing frames use automatic toe width. Update the frame and re-export the bumper to use the continuous shoulder transition. A custom toe width changes the external protection, not the plate cavity; Follow bottom plate continues to follow the original plate.

## 0.82.0 presentation references and bumper profiles

Detailed references default off for new and existing frames. Enable individual models under Finishing / Detailed references and update the frame. The two retired bumper selections import as Rounded shoe; review and re-export any affected bumper. New toe feature and lip capture controls default to automatic/full reach.

## 0.83.0 motor and prop assembly

Update frames using detailed references to regenerate the M5 shaft/locknut and seated 6 mm prop hub. Motor reference height describes the bell body; the shaft and nut extend above it. Prop reference height controls only simple discs. Detailed props now use 3.7-inch pitch and the actual swept blade-height range for clearance checks.

## 0.84.0 grommets, power references and straps

Update existing detailed stacks to regenerate the corrected grommets. Detailed VTX/LiPo references and side-guard strap cuts default off. Enable them in Finishing / Detailed references or TPU / Side guard straps, update, and re-export changed guards. Custom strap positions are signed frame Y offsets relative to the stack.
