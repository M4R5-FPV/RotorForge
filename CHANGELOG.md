# Changelog

Release history is listed newest first. The Help PDF describes the current feature set.

## 0.89.1 - 2026-10-29

- Corrected Between plates guard fit: the full wall thickness now sits inward beneath the plate outlines, with nominal face contact at the top and carrier instead of a vertical gap.
- Side guard plate clearance now sets inward setback in Between plates mode; Plate-edge wrap keeps its existing outward clearance. The plan preview and optional camera closure use the same placement.
- Keep a 2 mm passage beneath intersecting top-plate strap slots and outline cutouts. Apply these clearances with the other guard openings to retain connected printable solids.
- Preserve single motor-wire exits, VTX openings, standoff sleeves and assembly collision checks. Updated diagrams, tooltips and guides; older saved frames regenerate with Update frame.

## 0.89.0

- Added Plate-edge wrap / Between plates fit. Existing settings keep Plate-edge wrap; Between plates removes edge-covering lips and limits the main wall and grips to the inner plate faces. Camera closure and stepped mid-plate regions follow their local carrier.
- Between plates uses one continuous motor-wire cutout spanning the saved front and rear positions. Side selection, height and width remain adjustable; returning to Plate-edge wrap restores the saved Front / Rear / Both choice.
- Added independent VTX clearance openings on either or both sides, automatic envelope sizing, custom length/height, signed position offsets and clearance. Fully covering openings permit lateral VTX overhang while preserving screw support, fore/aft deck coverage, bearing material and exact collision checks.
- Updated live side previews, saved settings, native properties, component dependencies, exports and illustrated Help. Retains 0.88.0 loading and geometry-cache improvements.

## 0.88.0

- Faster saved-settings loading: reuse immutable parameter snapshots and validation results, and decode the JSON file once.
- Keep a bounded local cache of successful native builds across FreeCAD sessions. Verify exact settings, generator/CAD versions, payload digests and shape validity; retain normal assembly checks. Missing, incompatible, corrupt or unwritable cache data falls back to generation.
- Prepare display triangulation before assigning restored solids to FreeCAD views, avoiding display meshing stalls without changing exact CAD geometry.
- Reduce repeated FreeCAD property-list reads, BRep serialization and volume/centre-of-mass integration. Preserve current battery properties during updates.
- Audit Help against all 331 active controls and current choices. Correct navigation, strap openings, camera recess descriptions, lower-clamp nut placement, flexible-part export/mass descriptions and reference displays. Remove the obsolete cover warning and document caching. Guide versions follow the application automatically; builds reject stale control metadata.
- Retain the requested Windows installation path `%APPDATA%\FreeCAD\v1-1\Mod` and the FreeCAD command that opens the active user Mod directory.

## 0.87.2

- Side guards now bridge top-plate strap outline cutouts along the outside plate edge. They leave the strap passage clear instead of following its recessed edge inward.
- Applied the same outline to the guard wall, plate-clearance envelope and editor preview. The top plate retains its cutouts; one/two strap positions, depth and length remain editable.
- Kept widened/tapered plate outlines, fillets and custom outline cuts, plus the separate top/bottom strap-opening controls for the guards.
- Updated illustrated Help. Use Update frame on saved projects and re-export side-guard print files.

## 0.87.1

- Two-plate frames now create exactly one arm clamp opposite the bottom plate: a lower clamp for below-bottom arms, or an upper clamp for above-bottom arms. The keystone does not add another clamp.
- With below-bottom arms, the bottom plate carries the FC stack and receives the arm nuts. Stack mounting bores, lower service openings, standoff mounting surfaces and screw grip lengths follow this arrangement.
- Previews, carbon mass, cutting profiles and manufacturing exports omit the inactive clamp. Existing documents clear and hide its old solid when updated.
- Upper and lower thickness settings remain independent and saved; only the active setting is enabled. Both ends retain the arm-following outlines from 0.87.0.
- Updated the illustrated Help. Restart FreeCAD after installing, update existing frames and re-export manufacturing files.

## 0.87.0

- Combined clamp front and rear ends now follow all four arm-root outlines using trimmed bolt-pad tabs. A continuous centre deck retains stack support; existing clamp-mounted standoffs retain local bearing pads.
- Applied the same outline to the optional lower capture plate, validation, live preview and manufacturing exports.
- Updated illustrated Help. Regenerate and re-export clamp plates after updating.

## 0.86.0

- Removed None from top-plate strap styles; existing None settings migrate to disabled openings.
- Added one/two strap selection for slots and outline cutouts. A signed single-strap position defaults to centre; original two-strap spacing stays saved. Automatic guard strap positions follow the selected plate positions.
- USB openings may approach or open through the guard top edge. Thin top strips are removed automatically; lower-wall and standoff-sleeve protections remain active.
- Updated illustrated Help and regression checks.

## 0.85.0

- Detailed FC reference gains a hollow side-facing USB-C connector with left/right selection and signed fore/aft offset. The editor reports the matching guard cutout centre coordinates.
- Top-plate strap openings now offer Slots, Outline cutouts, and None. Existing slot settings remain intact; edge cutouts add an independent depth control, rounded inner corners, local-width following and mounting-support checks.
- Previews, CNC profiles, persisted settings and illustrated Help include the new controls. USB-only edits reuse carbon geometry; the visual connector is excluded from manufacturing exports and mass estimates.

## 0.84.1

- Flipped the detailed LiPo reference so its leads and connector exit toward the rear at the default battery rotation. Top and bottom mounting retain the selected battery position and rotation.
- The included Help PDF remains the 0.84.0 guide; controls are unchanged.

## 0.84.0

- Corrected detailed FC/ESC grommets: opposing necks meet between the PCBs, the FC neck extends downward, and upper nuts seat above its short flange at the selected stack height.
- Added independent optional detailed VTX and LiPo references. Existing dimensions/placements and estimated masses remain in use; LiPo wiring is schematic and extends beyond the pack body.
- Added one/two-strap side-guard edge openings, with automatic plate-slot alignment or custom stack-relative positions, adjustable width/depth and top/bottom selection. Grip clearance and connected printable geometry are checked.
- Strap edits reuse the guard base and carbon parts. New power models use dimension-based caches. Help sections and illustrations are integrated into their relevant chapters.

## 0.83.2

- Raised the grey stator to the lower bell edge and added a dark central support from the feet to the stator. Its radius leaves 0.5 mm clearance to motor mounting screw shanks.
- Updated the detailed motor Help illustration.

## 0.83.1

- Raised the detailed copper windings above the lower bell edge, leaving the motor feet clear. Their tops remain just below the bell roof.
- Updated the Help illustration to match.

## 0.83.0

- Detailed motors have rounded radial mounting feet aligned with the actual three-/four-hole pattern, a taller stator and windings, and an M5 shaft through the prop hub with a self-locking nut above it.
- Detailed three-blade props use a 6 mm hub, 5.1 mm bore and 3.7-inch geometric pitch. They seat directly on the bell; simple prop-disc height remains independent.
- Detailed-prop clearance checks cover the actual swept blade-height range. Simple references, physical frame geometry, weight estimates and manufacturing exports remain unchanged.
- Updated presentation reference descriptions and illustration in the Help.

## 0.82.0

- Eighteen front-bumper profiles, including six new rounded, angular and recessed toes. Retired the scalloped and triple-lobe toes; saved selections migrate to Rounded shoe.
- Added toe feature width, recess depth and independent upper-lip capture length while preserving the continuous grip transition and fit cavity.
- Independent optional detailed motor, three-blade propeller, two-PCB FC/ESC stack with silicone grommets, and FPV camera references. Simple models remain the default; LiPo and VTX references are unchanged.
- Detailed references use existing dimensions and placements, preserve full clearance probes and mass estimates, and remain excluded from manufacturing exports. Canonical models are cached by dimensions and visual edits reuse carbon components.
- Integrated controls and matching illustrations into the Help.

## 0.81.0

- Adjustable front-bumper toe width, with automatic sizing retained.
- Continuous shoulder transition joins the toe to the plate grip without side notches. Plate-fit clearances and retaining surfaces remain independent of toe width.
- Matching live preview, selective rebuilds, exports and Help documentation.

## 0.80.0

- Eight additional bumper toe styles; existing six styles retained.
- Front motor-wire exits follow the stepped lower guard edge across the mid-plate end and front enclosure transition.
- Front exits trim around actual standoff bearing sleeves with a local retaining web instead of rejecting their entire rectangular envelope. Rear-wire and USB protection remain unchanged.

## 0.79.0

- Optional bottom-plate front TPU shoe with six toe profiles, adjustable reach, projection, fit, wall, sole and retaining lip.
- Shoe follows the finished carbon outline, preserves bolt access and relieves nearby camera/assembly parts; carbon geometry stays unchanged.
- Printed-part colour, volume/mass estimates, part previews and separate printable exports include the bumper.

## 0.78.0

- Removed the FPV top lens-cutout section and its separate automatic opening from CAD, preview and export.
- Top plate front-edge/recess settings now define the complete opening. Automatic width uses Camera recess clearance on the same top-plate page.
- Older straight-front FPV frames translate their former opening to a visible U recess on load. Explicit existing front profiles remain selected, with no additional hidden opening.
- Updated Help and front-profile illustrations for the single set of controls.

## 0.77.0

- Airflow locator: numbered patterns, text search and part filtering.
- Fixed the editor text limit that could truncate large saved cutout lists before the 200-pattern capacity was reached.
- Click an opening to select its saved pattern; repeated clicks cycle overlapping patterns. Selecting an array member selects its whole pattern.
- Highlight selected geometry, optional preview numbers, Zoom to selected and Fit plate. Disabled patterns remain editable from the list.
- Keep unapplied edits when selecting another pattern; Apply or Discard before switching. Filtering and preview picking do not rebuild CAD or modify saved cutouts.

## 0.76.0

- Independent top-front edge selector, including six camera recesses: U, flared, swept, crescent, stepped and chamfered.
- Recess width, depth and shoulder setback, plus the existing general front profiles. Camera cutouts remain independent and combine with the edge shaping.
- Automatic camera contacts follow the new upper profile. Required mounting stock is checked, and existing frames default to Straight.
- Shared native, preview and CNC boundaries; unaffected arm geometry is reused.

## 0.75.0

- Black reference screws, nuts and press nuts, including refreshed references in existing frames.
- Four independent frame-direction offsets for camera tabs, with matching sockets and cutter reliefs.
- Six additional bottom-front profiles; independent rear profiles on bottom (two plates), mid and top decks, including cable channels and split/stepped tails.
- Shared CAD, editor and clearance-check profiles; unchanged arms and hardware geometry remain cached. Signed tab offsets persist in saved FreeCAD documents.
- Hardware reference groups use a hidden source link for FreeCAD 1.0 group compatibility.

## 0.74.0

- Rounded captured camera-insert openings, including the side-plate outline profile, with an adjustable corner radius and matching TPU neck.
- Added inside-only, outside-only and both-side retaining lips. Camera position and tilt paths remain unchanged; reference screw positions follow the selected outer lip.

## 0.73.2

- Fixed full-height side guards failing at sleeve joins: OCC splitter cleanup can mutate a valid solid into an invalid one. Cleanup now runs on an independent copy and retains the original valid solid if refinement fails. Guard height, mounting geometry and clearance checks remain unchanged.
- Closed guard STL exports also repair microscopic float-precision seams when necessary, without filling actual openings.

## 0.73.1

- Hardware reference screws and nuts now follow frame changes automatically. Existing reference objects, group choices and hidden states are retained; unchanged fasteners keep their geometry.

## 0.73.0

- Extended side guards to the top-plate top surface and the underside of the bottom plate (two plates) or mid plate (three plates), with vertical plate-edge lips and local carbon/prop clearance.
- Kept standoff grip bands, USB and vent locations unchanged. Wire openings automatically extend through the new lower skirt without losing clearance above the carrier.

## 0.72.0

- Added adjustable circular cutter reliefs beside all camera side-plate tabs. Reliefs extend half the cutter diameter into the plate body, keeping the tabs and sockets unchanged. Preview and CNC profiles include the cuts.

## 0.71.2

- Restored round button-head screws below the FC stack carrier when press nuts are enabled. Screw shafts and heads form one solid; upper nuts and direct-flange stack height remain aligned.

## 0.71.1

- Corrected FC press-nut stack placement: the stack rests directly on the exposed flange, without an extra gap or retained manual spacer. Upper nuts follow automatically. The 1 mm radial material margin is unchanged.

## 0.71.0

- Added optional FC stack press nuts with automatic flange clearance and repositioned stack screws/upper nuts.
- Removed VTX retention nuts and cutouts; VTX hardware now uses screws only.
- Set the press-nut material margin to 1 mm around the flange or counterbore.

## 0.70.0

- Added low-profile round button-head hardware references.
- Added receiving-plate hex nut pockets and configurable M3 press-nut bores, with FC stack nuts unchanged.
- Added secondary pocket operations to manufacturing exports and updated the Help.

## 0.69.0

- Added optional nominal hardware references and related Help instructions.

## 0.68.0

- Added a shared ten-colour appearance selector for all soft/printed parts and the LiPo pad, without geometry rebuilds.
- Rebuilt the Help illustrations in one technical style and audited the guide against current controls.
- Corrected copyright and maintainer attribution to Michael Struggl.
- Consolidated and ordered the release history.

## 0.67.0

- Component-level dependency caching replaces whole-model regeneration for local edits. Dependencies come from parameter reads and upstream geometry, including warm pure-layout caches.
- Separated solid side-guard shells from vent/USB/wire cutting for faster opening edits.
- Preserved unchanged native Shapes; stored verified per-part provenance and source geometry for reuse after reopening.
- Cached exact overlap results by geometry and avoided repeated portable validation, with bounded cache memory and history.
- Added geometry-build timing and rebuilt/reused component results, plus integrated Help instructions.

## 0.66.1

- Forward enclosure lower edge begins at the foremost standoffs, preserving FC/front-arm clearance and motor-wire openings.
- Short-top camera attachments taper only the upper join rearward. Preview, wire validation and Help share the corrected boundary.

## 0.66.0

- Ten additional side-guard vent shapes, independently selectable for FC and VTX sections.
- Optional full-height forward closure to the real camera side plates and bottom plate, with adjustable landing length.
- Portable preview and integrated Help coverage for the new controls. Existing designs retain their previous coverage until enabled.

## 0.65.1

- VTX and FC vent rows now use unitless integer controls from 1 to 6 in both the editor and FreeCAD properties.
- Older fractional row settings use their previous layout rounding on read; property types migrate only on explicit update.

## 0.65.0

- Independent bottom front-edge selector: Straight plus rounded, pointed, flat-tip, swept, concave, V-notch and twin-lobe shapes.
- Adjustable shaping depth and flat-tip width. Shared smooth curves drive native geometry, preview and portable support checks.
- Shaping trims the bottom plate inside its existing reach after centre widening; arm/standoff positions stay fixed; camera following checks the complete lower contact footprint. Existing frames default to Straight.
- Integrated shape catalogue and controls in the plate section of the Help.

## 0.64.2

- Rear motor-wire pockets can extend underneath raised standoff grips and open through the rear guard edge.
- Grip clearance uses actual vertical bearing bands, preserving a supporting web and the complete sleeves. Openings entirely beyond the wall are rejected.

## 0.64.1

- True zero side-guard plate clearance: close the hidden plate-face and relief gaps when set to 0 mm.
- Fixed the zero-width Qt stroker fallback that still showed an offset in the preview.
- Kept standoff fit independent, preserved normal positive clearance and anchor USB height to the carrier.

## 0.64.0

- Rounded capsule supports at the front/rear side-guard grips.
- Fixed motor-wire width overwriting the second wall thickness. Exact native plate-edge intersections prevent opposite-side tab spikes.
- Separate VTX and FC vent controls: enable, shape, dimensions, rows, web, insets and vertical position, plus a shared adjustable stack-relative boundary.
- Dedicated Side guard vents page and integrated help. Old single vent settings seed both sections on read, preserving fast saved-frame restore.

## 0.63.0

- Optional bottom-edge motor-wire exits on either side guard, with front/rear selection, separate stack-relative positions and adjustable width/height.
- Rounded upper shoulders, sleeve and top-web protection, lightweight preview and documented controls.

## 0.62.0

- Enclose the foremost covered standoffs over their full exposed height, with
  assembly clearance at the ends; forward extension reaches the actual front row.
- Round the inboard grip shoulders by moving the connecting stock outward,
  freeing the former square corners beside the electronics.
- Relieve local arm/clamp interference while preserving a continuous grip.
- Match overall/part previews and native Help illustrations to the new sleeves.

## 0.61.0

- Defer saved-document migration and rebuilding until an actual parameter edit
  or explicit Update. Unchanged restored BReps remain intact during recompute.
- Prevent each dependent feature from retrying the same failed solid build;
  changed parameters and explicit build actions can retry.
- Cache planar editor profiles, reuse them during TPU tuning, trace guard outer
  contours only, and avoid a duplicate initial editor refresh.

## 0.60.0

- Removed rear antenna/GPS/ELRS generation and controls. Existing saved settings
  import without those components; Update removes obsolete document parts.
- Added optional forward side-guard coverage, six vent profiles and adjustable
  left/right/both USB openings.
- Replaced tie retention with linked screw-head service openings, without tunnels.
- Fixed blank overall top preview caused by a premature protector drawing pass.
- Restrict adaptive arm fillets to stock beyond the protected mounting root.
- Updated Help, examples, editor previews and manufacturing exports.

## 0.59.0

- Side guards follow finished top/mid or top/bottom contours, with full upper
  10 mm FC-post bearings and central 6 mm rear bearings.
- Separate upper VTX and lower GPS/ELRS printable parts use only the outermost
  rear pair, on fixed post bands even when guards are disabled.
- Broad direct rear saddles and filled tilt supports replace lateral offset
  links. ELRS hooks attach directly below the flange with central feed holes.
- Added adaptive arm outline fillets and opt-in internal-opening fillets.
- Integrate updated controls, examples and native geometry illustrations in Help.

## 0.58.0

- Replaced the serial rear carrier with a reinforced bridge and short post sleeves. Place VTX high, GPS aft, and ELRS clips under the GPS front lip.
- Preserved measured hardware pockets and clear final-fusion insertion, wiring and GPS sky volumes. Fit each fitting's true rotor envelope, including forward-projecting ELRS supports.
- Added adjustable rear sleeve grip and a warning for forward posts beneath a long covering plate. Include a compact six-post example with a rearward pair.
- Added four shape-matched motor-pad cups with motor-screw/zip-tie retention, shaft access, fit allowance and optional perimeter landing feet.
- Added separate solid/vented electronics side guards with adjustable clearance, slots and end insets. Separate their post collar bands from the rear sleeves and trim exposed upper panels below prop sweeps.
- Included all new printable parts in native objects, previews, STL/STEP export and mass/CG, excluding them from carbon cutting profiles.
- Integrate 271 visible controls and new native illustrations into Help. Camera tilt/travel and opt-in internal fillets are preserved.

## 0.57.0

- Redesign the combined rear mount around one open, shared low yoke with local VTX gussets, two ELRS handles per crossbar and a single aft GPS pocket.
- Kept full ELRS crossbar insertion axes, local T-junction clearance and underside cable routes clear after all fittings are fused. Add a measured ELRS stem/cable clearance control.
- Preserved independent accessory switches, connector choices, widths, tilt and two/four actual rear-standoff selection. Keep four-point bracing/windows between the post rows.
- Make closed internal-opening fillets independently opt-in for each plate and the clamp pair; outside corners and edge notches continue using the selected radius.
- Added automatic camera bearing-area extension for fore/aft travel, preserving the captured attachment edges, tongues, sockets and tilt settings. Handle automatic lens-notch sizing when the camera is ahead of the top plate.
- Replaced the rear illustrations and integrate the new controls into Help.

## 0.56.0

- Replaced global outline offsets with local tangent fillets that adapt the radius at tight corners instead of failing the complete plate.
- Included sharp internal cutout corners, outline-notch intersections and combined-cut junctions.
- Preserved circular drill geometry, smooth slots, thickness, countersinks, fastener support and minimum web.
- Round internal cutout loops in the lightweight editor preview and update the integrated Help illustration and guidance.

## 0.55.0

- Added independent VTX, ELRS and GPS carrier outer widths, with automatic defaults and measured hardware fit checks.
- Fit rear collars and closed side panels to actual exposed standoff spans. Top-reference the VTX holder and separate accessories fore/aft instead of summing their heights.
- Replaced narrow tier-height connections with continuous full-height side panels and aft side braces. Keep four-post airflow windows between post rows.
- Removed the manual rear-height fitting button. Retain measured pocket/bore sizes; oversized aft bodies may extend below the carrier behind the frame.
- Refresh rear geometry illustrations and integrated Help.

## 0.54.0

- Added an independent signed camera forward/backward offset under FPV > Tilt & position, layered onto automatic or custom camera placement.
- Kept the wall outline, captured tabs and tilt settings fixed; translate camera, fixing paths and soft interfaces together.
- Included the control in Help, saved settings, native properties and geometry checks. Old frames default to zero offset.

## 0.53.0

- Arrange VTX above the low GPS/ELRS tier. Place GPS at the outermost rear, with ELRS ahead of it.
- Added signed GPS tray pitch with a supported floor and side gussets.
- Added scaled plain side-plate silhouettes for camera pads and captured inserts, excluding locating tabs. Keep the original outline and tilt screw paths.
- Added independent bottom/mid/top perimeter fillets and a shared clamp fillet, with fastener and slot support checks.
- Integrate controls and exact geometry illustrations into the Help.

## 0.52.0

- Combine independently enabled VTX, ELRS and GPS features into one printable rear mount.
- Select two actual rearmost standoffs or the two rearmost pairs; four-point mounts include adjustable side airflow windows.
- Replaced bulky ELRS housings with adjustable paired slide-in eyes or split clips.
- Close the aft side braces around tilted VTX holders.
- Retire separate rear components on update; export one rear STL. Camera isolation geometry and tilt controls remain unchanged.
- Integrate the new controls and native geometry illustrations into Help.

## 0.51.0

- Added five focused TPU pages for optional camera interfaces and independently selectable rear VTX/ELRS/GPS housings. Defaults preserve existing frames.
- Retain camera tilt paths in pressed pads or captured, flanged inserts; cut corresponding carbon windows in insert mode.
- Added one/two digital VTX holders (one for analog), four RF-end labels, measured pigtail pockets or split tie clamps, and housing tilt.
- Use broad rear cheeks and captive standoff collars. Pack selected modules without empty layers, account for motor/prop references and expose a height-fitting action.
- Export independent printable STL/STEP parts, include flexible mass/CG, and keep printed parts out of carbon CNC nesting.
- Document all 42 new controls in the integrated Help with native geometry illustrations and example settings. Keep live editing free of solid-kernel calls.

## 0.50.0

- Replaced the Help cover frame image with the updated user-supplied screenshot.

- Refine the cover warning layout and clarify that antenna/GPS mounts, camera vibration-isolation parts and other flexible accessories need separate design.

- Give all carbon parts, including camera sides and locking parts, a satin graphite material. Use distinct matte near-black for the LiPo pad. Update existing physical parts without recoloring electronics references.
- Match the editor previews to the physical material palette. Keep the technical Help diagrams in contrasting colors for clarity.
- Added a prominent design-starting-point warning to the Help cover and describe material appearance in the relevant chapter.

## 0.49.0

- Kept the first ten motor pads and replace the following twelve with scalloped shield variations. Scallop depth uses the corner-size control. Saved retired names migrate with a review warning.
- Removed the three windowed beam profiles and their width field. Older settings become solid Broad shoulder arms; native updates remove the retired property.
- Rebuild the rear VTX Help illustration using actual rear plate profiles, a clearance section and dimensioned hole-pattern details. Remove discussion of the deleted VTX setting and refresh the motor-pad and solid-arm catalogues.

## 0.48.0

- Help artwork revision: colour technical diagrams throughout, unified 20-cutout catalogue, smooth union examples, filled CNC sheets and outline-notch comparisons. Full rendered-page review; runtime unchanged.

- Seat the VTX directly on its carbon carrier. Remove the spacer-height editor/native setting, spacer parts-list row and spacer mass/height assumptions. Ignore that retired setting on import.
- Preserved the first ten motor-pad geometries through Scalloped shield. Replace the following 23 choices with twelve compact motor-bearing platforms and optional root-facing neck reliefs. Warn and map retired choices when imported.
- Replaced whole-outline preview rounding with direct concave-corner construction and cache the resulting paths. Keep the exact native rolling-radius blend. No native solid generation runs in live rotation preview.
- Replaced the six similar beam bulges with eight distinct taper, shoulder and window designs around fixed straight arm axes, plus Straight. Add adjustable protected window width.
- Added ten grip patterns to the previous fifteen. Trim only invisible groove-tool overhang outside the pad to avoid unnecessary native boolean work.
- Put all 25 grip cards on one Help page. Replace the dark VTX image with a light rear-deck diagram, revise the arm/pad catalogues, and integrate the current 193 controls.

## 0.47.0

- Restrict FC stack patterns to 20 x 20 and 30.5 x 30.5 mm in the editor and native project. Preserve adjustable stack heights and warn when importing a nonstandard older spacing.
- Retain all 23 motor-pad outlines and add ten new outlines with optional single nose slots, paired holes or paired slots.
- Added adjustable planar rounding at rotated pad / beam junctions for either rotation pivot, with a lightweight cached editor preview.
- Added independent bottom, mid, top and clamp base-outline selectors, a shared taper percentage, and six straight-axis beam designs with adjustable widening.
- Added eight airflow / outline-cut profiles, retaining overlapping-pattern unions and material checks.
- Integrate all 192 controls and consistent coloured shape catalogues into the Help.

## 0.46.0

- Removed the optional rear printed carrier and camera spacer section, generators, previews, reference bodies, exports, assets and example.
- Import earlier settings without the retired optional values. Updating an older project removes obsolete generated components and their parameter group.
- Retain the LiPo pad creator, carbon camera side plates, motor-pad options and general recompute optimizations.
- Updated the integrated Help for the remaining controls.

## 0.44.0

- Preserved the nine existing LiPo grip patterns and add Dimple grid, Staggered dimples, Dash grid, Basket weave, Hexagon cells and Wavy grooves. Retain automatic finished-pad coverage, adjustable width/depth/spacing, a continuous backing and standoff clearances.
- Added FPV > Side plates > Upper attachment rearward offset. Move the upper wall contact, tongues and matching top-plate sockets rearward independently after the original fitting. Preserve lower contact, camera position/tilt and all existing settings. Zero reproduces previous behavior; validate shifted support and fixing material.
- Included the new value in native settings, JSON and export metadata. Integrate additional grip and camera illustrations into the relevant Help chapters.

## 0.43.0

- Generated grip channels from the actual finished pad footprint, including carrier following, width scaling, asymmetric reaches, clipping and standoff clearances. Remove the former independent grip-region crop. Pad width/length now size only independent pad shapes and are disabled in carrier-outline mode.
- Preserved Solid, Transverse grooves and Cross grooves. Add Longitudinal, Diagonal, Diamond, Chevron, Zigzag and Rectangular rings, with shared preview/CAD layout and adjustable width, depth and spacing.
- Kept continuous backing on both mounting sides and guard dense finished-pad patterns at 512 segments. Preserve physical mass calculation, STEP/STL export and ungrooved cutting outlines. Integrate a consistent colour pattern catalogue into the LiPo Help chapter.

## 0.42.0

- Added independent front/rear pad reaches measured in millimetres from the FC stack centre. Trim shortened ends straight across Y while retaining the carrier profile along the sides; width scaling remains independent. Zero reach keeps that carrier end.
- Removed pad material within a 6 mm radius of every standoff-hole centre for all pad shapes. Preserve fixed hole positions, CAD/preview agreement, connected-part checks, mass calculation and manufacturing exports.
- Retain the former length percentage as a hidden compatibility value and convert old saved percentages to explicit stack-referenced reaches on import. Update the integrated Help.

## 0.41.0

- Added independent width and length percentage scales for the mounting-plate-outline LiPo pad. Scale the outer boundary about the carrier centre, clip to its finished footprint and preserve actual hole/cutout positions. Keep 100/100 as the old full-outline behavior.
- Updated live inspection, exact CAD, mass estimates and pad exports through the same parameters; persist scales in JSON and native documents. Explain outline size versus grip-region dimensions in the Help.

## 0.40.0

- Added Hardware > Weight estimates with editable representative motor, prop, FC, ESC, VTX, camera and extra equipment masses. Compute separate bare-frame, equipped and loaded mass/CG; expose native results and use the active equipped/loaded CG for the reference cross.
- Estimate steel screw masses from automatic counts, diameters and grip-dependent lengths with a user multiplier. Avoid double-counting shared arm/standoff fasteners. Standoff estimates continue to follow actual tube dimensions, pair counts, front/rear lengths and material density.
- Export per-item assumed masses and centres in EquipmentMass.csv and MassProperties.json. Include FPV equipment only in FPV mode, independently of reference visibility. Preserve the previous bare-frame outputs.
- Retain all three LiPo pad outlines and add ellipse, chamfered rectangle, tapered, hourglass and full mounting-plate outline. The full-outline option copies the finished top or bottom carrier, including holes and cutouts; CAD and editor inspection use the same outline rules.
- Added chamfered diamond, hexagon and octagon compact fitted-miter keystones with matching arm pockets and parallel edge clearances. Independent roots retain automatic arm-following key seats. Preserve all bolt support, captured plate, connectivity and access checks.
- Integrate all new controls into the relevant Help chapters with consistent colour shape catalogues. Keep the modern namespaced workbench layout and old-document compatibility.

## 0.39.0

- Added Battery > Placement with an editable nominal 1300 mAh 6S battery envelope, shared pad/reference XY offsets, rotation and top/bottom mounting. Default reference dimensions/mass are 75 x 38 x 38 mm / 208 g; actual packs must be measured.
- Added Battery > LiPo pad: separate rounded rectangle, rectangle or capsule pad, optional finished-plate following, adjustable shallow transverse/cross grooves and material density. Reject empty/disconnected pads and physical intersections.
- Export the pad separately as flat printable STL, assembled/flat STEP and ungrooved DXF/SVG outline. Keep pad/reference geometry outside carbon nesting; include the physical pad in the assembly STEP.
- Calculate frame mass/CG from finished solid volumes and separate carbon, standoff and pad densities. Report carbon, modelled frame, and frame-plus-reference-battery estimates with explicit scope. Add native result properties, a frame CG reference cross, MassProperties.json and per-item mass data in PartsList.csv.
- Added a preview selector for the overall frame, all flat parts, all arms and individual active parts, including finished holes, slots and applied cutouts. Clear stale mass/CG when parameters change and require pending cutout drafts to be applied/discarded before calculation.
- Integrate the controls and workflows into the Help, with native editor illustrations. Retain the namespaced layout and old-document compatibility bridge.

## 0.38.0

- Migrate the implementation to the native freecad.rotorforge namespace using the current FreeCAD Addon-Template structure. Replace root Init.py/InitGui.py hooks with a lightweight package entry point and init_gui.py.
- Kept workbench and command IDs stable; register once, and load editor and CAD code lazily when activated.
- Retain a small rotorforge.document import bridge so older saved FCStd proxies restore to the canonical classes. New saves use the namespaced module path.
- Package icons and runtime manuals inside the namespace; add pyproject.toml and verify wheel/source-distribution builds and installed wheel operation.
- Updated the one-session launcher, manifest, Help and Windows/macOS/Linux installation guide for the new structure. Replace the old installation folder completely when updating.

## 0.37.0

- Added Motor pad rotation pivot under Arms > Motors > Pad outline: Motor centre or Pad beginning. Existing projects retain Motor centre.
- Pivot beginning mode at the root-facing extent of the unrotated outline, with mirrored rotation signs. Move motor bores, fixing holes, tip slots and motor/prop references together.
- Join the fixed main beam to the transformed pad with a continuous full arm-width elbow, including widened-root geometry and matching editor/cutout previews.
- Recalculate prop clearance and actual motor positions and include pivot coordinates in export metadata. Preserve all existing outlines and CNC arm realignment.
- Document both pivots, their effect on spans and the connected transition in the motor mounting Help chapter.

## 0.36.0

- Removed Rectangle motor mounting from the editor and native property choices. Retain only four-hole and three-hole bolt circles, independent hole clocking and mirrored pad rotation.
- Use explicit circle diameters in all motor sizing actions, with zero hole clocking. Keep the existing 23 motor-pad outlines.
- Convert saved square mounting patterns to an equivalent four-hole circle without moving holes. Convert unequal legacy rectangles to a regular circle and show a manufacturing review warning while the converted diameter/angle remain unchanged.
- Hide legacy pad-lobe dimensions retained for outline compatibility, and update the motor mounting Help chapter and control reference.

## 0.35.0

- Added Motor pad rotation (mirrored) under Arms > Motors. Front-right/rear-left use the entered angle; the other corners use its opposite, relative to each arm.
- Rotate complete pad outlines, fixing patterns and nose slots around fixed motor centres while keeping arm beams, roots and motor positions unchanged.
- Preserved independent bolt-circle hole clocking as a local offset within the pad and retain zero pad rotation for existing designs.
- Apply the same orientation to CAD, editor and cutout previews, STL/STEP and CNC DXF/SVG. Record per-arm angles and fixing centres in export metadata.
- Added a mirrored-pad CAD illustration and explain both rotation controls in the motor mounting Help chapter.

## 0.34.0

- Added Motor hole rotation under Arms > Motors for three-hole and four-hole bolt-circle patterns. Signed angles are relative to each arm and pad.
- Kept existing designs at zero rotation and leave Rectangle patterns unchanged while retaining the saved angle.
- Use the rotated hole coordinates consistently for CAD, previews, minimum-web checks and DXF/SVG cutting profiles. Export the effective angle in manufacturing metadata.
- Persist rotation in JSON and native FreeCAD angle properties; describe the control and angle conventions in the motor mounting Help chapter.

## 0.33.0

- Focus the editor on two- and three-plate frames and remove the experimental alternative construction and its printed components.
- Simplify the controls, parameter model and manufacturing exports; retain all motor-pad shapes, fixing patterns and motor/prop sizing actions.
- Rebuild the Help around the supported plate-design workflow, with complete control descriptions and updated chapter navigation.
- Import earlier plate-frame JSON settings and remove obsolete generated components/properties when updating older plate projects.

## 0.29.0

- Added explicit 9 x 9, 12 x 12, 16 x 16 and 19 x 19 mm motor/prop sizing actions, independent motor-body references and square/three-hole/four-hole bolt-circle patterns.

## 0.28.0

- Added commercial-inspired Recessed cross and Vented spear motor pads while preserving all 21 earlier outlines.
- Integrate reference links and matching coloured catalogue illustrations.

## 0.21.1

- Fixed adding outline cuts to designs already holding 32 patterns. Allow up to 200 saved patterns while retaining the total limit of 200 enabled cut instances, including grids.
- Show saved-pattern and enabled-cut counts above the pattern list. Failed additions display a visible warning and preserve existing settings.
- Mark unapplied pattern edits and require Add pattern or Apply to pattern before CAD checks, saving settings or building a frame, preventing misleading success on unchanged patterns.

## 0.21.0

- Kept all ten previous motor pad outlines and add Swept shield, Wide shoulder, Clipped round, Dogbone and Twin scallop. Motor screw positions and centre bore stay independently adjustable.
- Added Interior / Outline notch modes to the Airflow / outlines pattern editor. Outline notches cross an outside edge of bottom, mid, top and clamp plates; all twelve shapes, grid, size, rotation and position controls remain available.
- Combine overlapping outline notches and interior patterns. Preserve existing holes, sockets and fastener bearing areas, and reject cuts that disconnect a plate.
- Kept older patterns in Interior mode; retain editable patterns in saved designs and export metadata. Add illustrated help and editable examples.

## 0.20.0

- Added Bottom body reach behind stack for three-plate frames. The main rear edge is Stack Offset Y minus this independent reach, mirroring the mid plate front-body control.
- Kept rear arm-matched tabs beyond the body edge. Automatic outer limits include the chosen body reach; a conflicting Custom outer limit reports an error. Check stack and mounting support and tab connections.
- Preserved older native and JSON outlines by converting their previously automatic body edge into the new stored dimension. Two-plate bottoms keep their existing geometry.
- Show the body edge in the plate readout and export metadata; include an editable example and updated illustrated help.

## 0.19.0

- Kept the four original Airflow shapes and add Ellipse, Rectangle, Triangle, Diamond, Trapezoid, Pentagon, Octagon and Chevron.
- Merge overlapping cutouts on the same part, including overlapping grid instances and different pattern types. Check new openings against the original part, then cut their union.
- Retain edge, fastener, captured-tab, separate-opening web and connected-part checks. Explain the difference between overlapping cuts and edges that only touch.
- Show merged openings in both previews; export exact ellipse curves and trimmed elliptic arcs in DXF/SVG as well as STEP.
- Added an editable combined-cutout example and update the illustrated help.

## 0.18.0

- Shape three-plate bottom rear clamping tabs to the rear arm roots, including width, taper, custom bolts, fitted joints and keystone pockets.
- Preserved the nose/stack body, bearing material for bottom-mounted standoffs and the configured reach limits. Keep two-plate outlines unchanged.
- Use the matching profile in CAD, previews, edge checks and manufacturing exports. Add an editable example and illustrated help.

## 0.17.0

- Added Teardrop, Shouldered, Compact hex and Scalloped shield motor pad outlines while retaining all six existing shapes and their dimensions.
- Join the Teardrop neck tangentially to its round nose. Add tapered shoulders, compact clipped ends and adjustable concave edge reliefs through the new profiles.
- Kept motor centres, measured mounting patterns and centre bores fixed. Use the same profiles for native geometry, previews, material checks and cutting exports.
- Included four editable native examples and illustrated help. Preserve the approved installation guide and supplied cover image.

## 0.16.2

- Trim the mid plate's front clamping tabs to the arm-root outlines, including root width and taper, custom bolt positions, fitted joints and keystone pockets. Keep each tab within the bottom support.
- Use the same matching outline for CAD, the main preview, Airflow preview, support checks and manufacturing profiles.
- Added an editable example and a CAD comparison of the removed overhang. The main stack deck and rear VTX body retain their configured dimensions.

## 0.16.1

- Orient custom arm-bolt offsets along the frame X/Y axes. Changing one coordinate leaves the other fixed, independently of the arm sweep or motor layout.
- Label the controls Bolt 1/2 X offset and Y offset. Use the front-right root as the reference and reflect X on the left arms and Y on the rear arms.
- Convert the centred front-right bolt pair into frame offsets when copying the current spacing. Convert older arm-relative settings from their front-right bolt positions; rear positions on Deadcat layouts now follow the mirrored frame pattern.
- Updated native properties, export metadata, editable examples and illustrated help for the corrected coordinate system.

## 0.16.0

- Added an independent root width, wide-root reach and taper length. Wider roots taper back to the existing beam without changing the motor outline or motor centres.
- Added custom lengthwise and sideways coordinates for each of the two arm bolts, mirrored across all four arms. Retain the original centred spacing mode and add a button to copy that spacing into custom coordinates.
- Follow the custom pattern in bottom, mid and clamp holes, shared arm-hole standoffs, previews, service checks and manufacturing exports. Keep the arm root reference centres independent of the bolt offsets.
- Fit joint trims and keystone seats to the actual widened roots; check edge material, motor-pad separation, neighbouring arms and standoffs. Preserve existing geometry with default settings.
- Included two editable wider-root examples and updated illustrated help. Keep the approved installation guide unchanged.

## 0.15.0

- Added optional Fitted miters to trim arm tails at shared joint lines without moving the motor or mounting-hole coordinates. A zero joint gap gives nominal contact; a positive gap provides cutting clearance.
- Added a compact diamond keystone with independent width and length, matched clearance pockets in the fitted arms and the existing captured mounting arrangements.
- Checked root- and motor-bolt support after fitting, actual arm intersections, key seating and stack-screw access. Keep Independent roots as the default for existing designs.
- Size an underside capture plate for the full stack access diameter when close roots no longer determine its reach.
- Included fitted outlines in the previews, native settings, cutting files, mass and export metadata; document the workflow and add editable examples.

## 0.14.2

- Removed the built-in frame catalog, Start from menu and bundled JSON preset files.
- Kept personal JSON configurations through Load settings / Save settings; existing saved settings and native documents remain editable.
- Updated the help and editor illustrations for the simplified workflow, including maximize/restore.

## 0.14.1

- Enable the editor's native title-bar maximize button.
- Added a Maximize window / Restore window button, preserving the previous window size and current settings.

## 0.14.0

- Added Tapered nose and Arrowhead motor pad outlines, with an editable outward extension and an optional tip relief slot with independent width and total length.
- Kept the four measured motor bores and centre opening unchanged; rotate each extended tip outward with its own arm in every layout.
- Checked supporting material around the motor holes, pad outline and tip opening; include the shapes and exact circular slot ends in CAD, cutting profiles, mass and export metadata.
- Added native examples, JSON presets, editor controls, previews and a CAD-derived comparison of all six motor pad outlines.
- Replaced the help cover with the supplied RotorForge frame image and document the new motor controls. Preserve the approved installation PDF unchanged.

## 0.13.1

- Replaced the Markdown help and plain-text installation instructions with two formatted PDFs, including searchable text, PDF bookmarks, page numbers and illustrated camera mounting guidance.
- Open the complete manual through Help manual (PDF), using the system PDF viewer, with a file path if no viewer can be opened.
- Included the help and Windows/macOS/Linux installation PDFs in the plugin folder.

## 0.13.0

- Added Automatic or Custom lower camera attachment sizing, with separate front and rear extensions for each side plate's bottom contact edge.
- Fit the longer lower edge independently of the upper attachment; move its tongues and bottom receiving slots together, while retaining the shorter top's outline and attachment length.
- Included lower contact dimensions and active extensions in native documents, presets, exact cutting profiles, mass and export metadata; retain extension values when switching to Automatic.
- Added support checks, editor controls, a shorter-top extended-base example and help explaining the settings.

## 0.12.0

- Arrange two camera side screws vertically at zero tilt, with editable pitch and a 6.5 mm shortcut; retain single-screw pivots and custom camera width.
- Rotate fixed round holes and upper/lower circular adjustment slots with the camera's upright axis.
- Replaced the pivot alternative with a fixed upper screw and an exact lower arc; update camera motion, clearance extrema, side-plate sizing and export metadata.
- Refresh mounting choices in existing native documents and convert the previous pivot selection when loading settings.
- Updated the help, presets, examples and camera illustrations.

## 0.11.1

- Use RotorForge consistently in installed code, installation guidance, license attribution and bundled native-document metadata.
- Store all bundled examples and compatibility fixtures with canonical rotorforge.document proxy paths and RotorForge group/property names.
- Removed obsolete import aliases and accept RotorForge preset schemas.
- Restore missing parameter and component proxies when applying an editor update.

## 0.11.0

- Capture below-bottom two-plate arms and keystone with a full lower plate, secured by the eight arm bolts. Keep the upper combined plate as the FC deck.
- Maintain full 6 mm/default stack access through the lower plate, arms, key and bottom. Add a root-relief switch and protect arm-bolt support.
- Included lower plate stock, cutting profiles, mass and complete bolt grip in exports. Replace obsolete point-retainer screws/countersinks.
- Fit camera tongues independently inside the actual top/bottom outlines, with sloping side walls for different plate ends.
- Added centred dual arc slots and a fixed front pivot/rear arc alternative; automatic or custom camera position and height.
- Migrate older camera positions and airflow coordinates; update native examples and GUI figures.
- Included installation instructions for Windows, macOS and Linux.

## 0.10.0

- Rename the workbench, package, menus, commands, launcher, document labels and export folders to RotorForge — Drone Frame Editor. Retain compatibility with older native proxies and presets; resaving uses the new implementation.
- Added keystones to two-plate frames with the combined clamp. Above-bottom keys are captured by bottom/clamp; below-bottom keys use two flush countersunk retainers with nuts underneath.
- Included retaining bores, real conical head seats, BOM hardware and separate MachiningOps.csv operations; keep DXF/SVG as smaller through-cut profiles.
- Added independent bottom/mid/top/clamp centre widths, shared full-width length, tapered shoulder length and Y position, clipped to each plate reach.
- Allow arm roots to follow the local widened bottom edge or retain their old span. Keep Deadcat length/diagonal compensation correct with unequal root spans.
- Use the widened outlines throughout support checks, standoff placement, camera/VTX fit, airflow, native geometry, mass and exports.
- Added widened and two-plate-key examples, including both arm positions and eight shared standoffs.

## 0.9.0

- Added fixed two-screw camera mounts and variable single-screw friction pivots or rear-pivot/arc-slot mounts, with adjustable range and full-range clearance checks. Preview tilt leaves variable bracket geometry unchanged.
- Place the stack at its carrier upper face plus exactly the configured spacer height; default new-frame spacer is zero, with no hidden lift over arms.
- Added exact custom front/rear reaches for bottom and top, exact/custom mid reach, and a shorter automatic three-plate bottom. Let the mid rear deck extend independently and carry three-plate VTX holes without duplicating them in the bottom.
- Added a per-part airflow pattern editor, local camera-side preview, circles/slots/rounded rectangles/hexagons, grid size/pitch/position/rotation and independent pattern enable switches. Protect boundaries, fasteners, standoff feet and camera tabs in CAD.
- Added round, rounded-square, chamfered-square and four-lobe motor pads with the same measured four-hole pattern.
- Included all choices in native files, presets, mass, manufacturing geometry and export metadata; add examples and a legacy 0.8 fixture.

## 0.8.0

- Replaced the optional two-piece arm clamp with one continuous clamp carrying all eight arm holes and four FC stack mounts.
- Position the carrier above the arms or bottom plate for either arm placement; preserve grip lengths and linked standoff heights.
- Added default 6 mm bottom service holes under separate stack carriers, with matching access reliefs through intervening arms and keystone. Keep normal stack holes in the carrier.
- Added an on/off switch for top battery strap slots; omit their geometry, checks and cutting paths when disabled, while retaining settings.
- Make stack spacer/envelope heights editable, follow the actual carrier, and add Fit stack height.
- Migrate old clamp objects to inactive geometry and include one combined clamp, stack hardware and strap/access metadata in exports.
- Refresh examples and document the Mac installation folder.

## 0.7.0

- Added an automatically sized, rounded front camera cutout in every FPV top; retain all upper camera tab slots and allow a raised lens through the opening.
- Extended the top over the full rear VTX envelope and check width, edge material and board/spacer height.
- Added an optional three-plate central keystone, matched to all four arm seats and captured between bottom and mid.
- Added above/below-bottom arm placement in two-plate mode and optional separate front/rear connecting plates on the existing arm bolt patterns.
- Place shared standoffs above the complete arm sandwich and compute different free/shared lengths where needed; retain the actual rear length and level top.
- Included locking parts in native documents, mass, STEP, exact cutting profiles and BOM grip lengths, and export arm/cutout metadata.
- Added examples for each new assembly option and preserve earlier defaults when upgrading.

## 0.6.0

- Allow standoffs to share exactly aligned, compatible arm-root holes; deduplicate holes and check the coaxial clamp path through all layers.
- Added front/rear/extra-pair arm-hole snapping that follows geometry changes, plus a top-plate fitting shortcut.
- Place shared three-plate standoffs on the mid or its front arm tabs; export lower clamp grip and count shared hardware once.
- Kept camera, front arm identities, and Deadcat spread on +Y. Compensate rear reach so rear arms grow when front spread increases while preserving opposite diagonal wheelbase.
- Replaced L camera brackets with full-height side plates captured by two lower and two upper tongues in matching bottom/top slots.
- Extended the top nose to capture the camera plates, and make tab length/clearance and side plate thickness/length editable.
- Added automatic camera centring and a stock-height fitting shortcut, including the lens envelope in clearance calculations.
- Included flattened camera side plates in carbon DXF/SVG sheets and mass; export separate STEP and flat STL plates.
- Added a shared-mount FPV Deadcat preset and regenerate every native example with the front-facing view.

## 0.5.0

- Open newly generated/edited frames in a front-facing isometric view and add a Front isometric command.
- Added optional FPV mode, plus Analog and Digital presets and separate Camera/VTX tabs.
- Generated two bolted L camera brackets with common-width shortcuts, custom body dimensions, pivot height, tilt, screw diameter, and optional two-hole side patterns.
- Added rear 20×20, 25.5×25.5, or combined VTX patterns with independent clearance diameters and adjustable position/envelope/spacer height.
- Extended the bottom nose and rear mounting decks automatically to support the FPV mounts; restore original geometry when FPV is disabled.
- Checked bracket/electronics/frame collisions, camera foot clearance, VTX/standoff clearance, and material between nested patterns.
- Export separate camera bracket STEP/STL files, include physical brackets in the assembly STEP, and add mounting data and hardware quantities to exports.
- Preserved transformed camera references in native FreeCAD objects and across save/reopen.
- Preserved existing documents with FPV disabled by default; editor updates add missing optional components.

## 0.4.0

- Added a 4/6/8 standoff selector for two, three, or four mirrored pairs.
- Added independent Y positions and left–right spacing for each extra pair, enabled only when used.
- Generated matching holes in the bottom/top and the appropriate mid regions; removing a pair removes its geometry and holes.
- Determine extra-pair mounting by the actual mid outline. Mid-mounted pairs use short standoffs; bottom-mounted pairs use long ones while keeping the top level.
- Checked standoff spacing, plate support, mid-edge interference, arm clearance, and strap-slot clearance.
- Included all selected tubes in STEP and per-pair quantities/lengths and mounting metadata in exports.
- Preserved four-standoff layouts when opening older documents and presets.

## 0.3.0

- Corrected Stretched X to widen the motor pattern left–right, with a clear width/front–rear aspect label.
- Added front and rear standoff controls with common-size shortcuts and custom lengths in the Standoffs tab.
- Link both height controls so the top stays level: three-plate fronts span bottom-to-top; rears span mid-to-top. Two-plate pairs stay equal.
- Show both standoff lengths in the editor summary and verify selected lengths in manufacturing exports.
- Preserved old configurations and normalize older wide Stretched X ratio values.

## 0.2.0

- Added a two-plate / three-plate selector in the Layout tab.
- Give the three-plate bottom an adjustable front extension.
- Replaced the duplicated mid outline with a stack-to-rear body and small front arm clamping tabs.
- Added independent mid front/rear reach controls.
- Use bottom-mounted front standoffs and mid-mounted rear standoffs in three-plate mode; calculate and export the required lengths.
- Mount arms below the bottom in two-plate mode, with no mid geometry, mass, STEP solid, or cutting profile.
- Updated live preview, validation, exports, presets, and example documents.
- Added support for updating existing 0.1 documents and presets.
