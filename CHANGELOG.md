## v1.0.10 — Airflow cutout position precision
- Allow three decimal places for Centre U and Centre V in Airflow / outlines (for example, 10.625 mm), with 0.001 mm adjustment steps. Saved cutout positions retain the entered precision.

## v1.0.9.1 — Recessed LiPo pad mounting clearance
- Keep the machined top-plate pockets selected for recessed LiPo inserts outside the same mounting-fastener clearance areas as their matching pads. This prevents exposed pocket recesses beside screw openings.
- Use the same corrected geometry for blind-pocket DXF/SVG machining profiles. Unselected pockets and other LiPo pad modes retain their existing behavior.

## v1.0.9 — Arm-tip and TPU motor-protector updates
- Add seven reference-inspired **arm-tip bumper** outlines: Seeker arrow, Matey swept hook, SR-Beast sweep, Podracer spear, Master hex, Vertex dagger and Volador fork. These are separate from motor-pad outlines and preserve the selected motor fixing pattern.
- Mirror asymmetric bumper profiles between front/rear and left/right arms, with Pad direction, Front / rear and Sideways outwards extension choices.
- Rework optional arm-tip outline openings to follow the cap contour while accounting for motor-hole safety stock, minimum web and the selected CNC cutter radius; omit openings that cannot meet these constraints.
- Reduce redundant arm-tip outline vertices and reuse unchanged geometry in the editor, retaining the full-resolution detailed 2D viewer.
- Add the **Tip-only inward taper** TPU landing-foot style as a filled front sole alongside the original full-perimeter ring. Keep decorative carbon-tip cutouts out of the filled TPU foot and preserve motor mounting openings.
- Restore **Linked screw access** for both landing-foot styles, alongside the individual Motor screws option, including the corresponding 2D part preview.
- Replace only the main workbench icon with the existing magenta R mark; retain the toolbar icons.

## v1.0.8.1 — Carbon texture visibility
- Carbon weave and cut-edge overlays follow FreeCAD part visibility, including model-tree hide/show and restored documents.

## v1.0.8 — Straight outermost LiPo retaining lips
- Replace contour-following side bands with straight retaining walls on the global left/right extrema of the finished unsplit pad surface. Stop at angled transitions, rounded corners and recessed sides; never follow internal cuts or split edges.
- Preserve individual split-pad selection, wall dimensions, grip relief and lettering clearances. Use matching straight-edge selection in 2D and CAD. If no eligible straight edge exists, omit the lip and report a warning rather than altering the pad outline.

## v1.0.7 — Individual split LiPo pad lips
- Add layout-aware checkboxes for each left/right, front/rear, or four-part pad. Preserve existing global side selection, wall dimensions, and saved behavior by default.
- Use the same outer-perimeter selection in exact geometry and the 2D previews; unchecked pads retain their normal grip surface, and no lips form along split edges. Settings persist in FreeCAD documents and JSON presets.

## v1.0.6 — LiPo grip relief and side retaining lips
- Add Honeycomb (shared-edge hexagonal tessellation with across-flats spacing) alongside all existing surface patterns.
- Choose Debossed or Embossed relief independently of the pattern; adjust width, height/depth and spacing. Raised relief lifts the battery reference; existing saved designs retain debossed grooves.
- Add optional left, right or bilateral retaining lips with adjustable height, wall thickness and front/rear clearance. Derive lips from the unsplit outer footprint, then clip to the actual pad pieces, preserving openings and avoiding artificial walls along split boundaries.
- Preview lips and grip relief in the pad inspection view, preserve reserved lettering areas and export the raised details as part of the existing printable solids. Outline-only exports omit raised surface details.

## v1.0.5 — Cross-platform Pivy / SWIG initialization
- Initialize FreeCAD’s bundled Pivy/Coin3D before registering RotorForge commands and before optional texture scene-graph or Render Studio camera-node access.
- Keep base material colours when the optional texture scene graph is unavailable, preventing scene-root failures from discarding standoffs, CG markers or other valid CAD geometry. Log initialization and scene-root failures once per session; retry binding imports when needed.
- Preserve all v1.0.1–v1.0.4 Runic lettering, split LiPo pads and seamless multi-pocket inserts, including their existing geometry, validation and exports.

## v1.0.4 — Seamless combined pocket inserts
- Merge actual pocket boundaries before applying fit clearance, eliminating internal profile seams in LiPo inserts.
- Extrude connected outlines as single pads, preserving separate islands, stepped undersides and the existing thickness rule.

## v1.0.3 — Multi-pocket LiPo pad inserts
- Replace numbered pocket selection with a saved multi-select checklist; selections follow saved patterns when reordered or edited.
- Combine overlapping pocket footprints and fit stepped undersides to actual machined floors of different depths. Separate recesses remain separate pieces.
- Define pad thickness from the deepest selected pocket floor to the shared top surface; require at least twice that depth. Update battery height, grip and lettering depth validation accordingly.
- Migrate former v1.0.2 numbered selections to saved flags and convert the old projection into total thickness, preserving the original battery-facing height.

## v1.0.2 — Split and pocket-fitting LiPo pads
- Add single, left/right, front/rear and four-piece pad layouts with an adjustable split gap.
- Add top-plate pocket inserts from a selected blind pocket or all equal-depth pockets with adjustable per-side fit clearance.
- Update pad previews, exact connectivity checks, mass/BOM and combined plus individual printable exports.

## v1.0.1 — Runic CNC lettering
- Add an original angular Runic alphabet for carbon lettering and LiPo pad engraving.
- Allow the Runic font as a full-depth Interior cut or a blind Pocket; keep all existing font and legacy pattern behaviour.
- Fit and validate Runic strokes against the selected cutter diameter and minimum web, with the existing final CAD connectivity and clearance checks.

## v1.0.0 — First major release
- Promote the tested v0.93.56 workbench to the 1.0 release baseline. Preserve design parameters, detailed preview, manufacturing geometry, and established performance optimizations.
- Replace the bundled Help manual with a complete, text-only 30-chapter guide using the original cover and visual identity. Update the installation guide version.

## v0.93.56 — Unified CNC perimeter cutter radius
- Use the selected global CNC cutter radius for conservative Bottom/Mid outer-perimeter cleanup in the exact CAD and detailed 2D paths, replacing the fixed 2 mm cutter reference.
- Tighten small-spur detection caps for smaller cutters without enlarging the existing maximum trim limits for larger cutters. Retain bearing-stock protection, validation, and original-blank fallback.
- Report the actual cutter size and clarify optional cleanup failures. No changes to other CNC operations or preview rendering.

## v0.93.55 — Local CAD operation optimization
- Use verified straight-edge fillet edit bounds to avoid distant wire-distance and bearing-stock Boolean tests. Retain original exact checks for nearby geometry and non-linear edits, plus final CNC validation.
- Group only provably separated side-guard opening cutters; preserve exact overlaps and fall back to the previous fusion on failure.
- Skip disjoint LiPo rounding patch/hole intersections and report the accepted rounding substage timings. Keep exact offset, containment, and final solid checks.
- No change to the editor or detailed 2D preview.

## v0.93.54 — Targeted native geometry performance
- Share the exact auxiliary unnotched top plate, native wire sections and carbon relief tools across both TPU side guards within a frame build, retaining independent lofts and validation.
- Avoid provably disjoint guard and pad cutters, redundant full-reach pad clipping, and unnecessary isolated inner-cutout bearing-stock booleans. Preserve CNC radii and exact clearance checks.
- Reuse the exact local FPV housing across sampled clearance angles with traced parameter dependencies.
- Report detailed carbon, guard and LiPo geometry stage timings. No changes to the 2D preview.

## v0.93.53 — Exact geometry generation performance
- Build straight round-ended slots as a single analytic wire extrusion, with the previous Boolean construction retained as fallback.
- Lazily evaluate CNC minimum-web distances using conservative enclosing bounds; reuse immutable wire endpoints and defect lists. All exact checks remain for unresolved cases.
- Skip compound collision checks only when every pair of solid bounds has a strict separation; preserve exact intersections for possible contact.
- Split LiPo pad and TPU intersections in build timing and report per-component build and collision timings. No 2D preview changes.

## v0.93.52 — LiPo outline startup performance
- Remove only sub-0.005 mm redundant vertices from the temporary eroded LiPo pad preview contour before the expensive native Qt dilation, retaining the original carrier, rounding radius, hole checks and legacy fallback.
- Avoid redundant full-carrier clipping and clearance booleans for disjoint fasteners; reuse localized flush-seat containment tests.
- Report individual LiPo carrier, clipping, erosion, dilation and clearance timings. No change to detailed overview drawing commands or manufactured solids.

## v0.93.51 — Cold detailed-preview acceleration
- Restrict native Qt point-in-profile tests to contours that can contain the probe, retaining the original curves and fill rule.
- Reuse the exact detailed Fit-view image across FreeCAD sessions for identical visual settings, viewport and runtime. Cache is bounded; zoom and editing retain original vector rendering.
- Report separate cold-preview timings for carbon, TPU, LiPo and airflow operations. No CNC or 3D geometry changes.

## v0.93.50 — Editor startup / detailed preview rendering
- Keep untouched settings pages outside the active Qt stacked-layout tree until first visited; all parameter controls and navigation remain available.
- Draw the unchanged detailed preview directly into a native-resolution, DPI-aware pixmap at Fit view, avoiding QPicture texture serialization and replay during opening. Preserve vector rendering for zoom/pan and cache the fitted image within a bounded memory budget.
- Report page construction, field widget construction, parameter restore, plate bounds, validation, preview build and actual paint timings separately.
- No changes to the detailed drawing commands, CNC geometry, model generation, or render options.

## v0.93.49 — Detailed editor performance
- Reuse exact combined cutout paths between finished profiles and the overlay; preserve the same 100x Qt Boolean precision and selected CNC radius.
- Cache complete detailed vector recordings across editor instances, with bounded memory and DPI/viewport-aware keys.
- Reuse native carbon texture pixmaps and TPU front plan paths; avoid repeated fillet segment/turn calculations.
- Record the opening preview after the initial editor layout and skip no-change debounced refreshes.
- Dispose closed editor dialogs and their timers instead of retaining parent-owned widget trees.
- Retain detailed overview as the default, all existing drawing operations, geometry, and manufacturing checks.

## v0.93.48 — Restore detailed 2D preview
- Default New frame and Edit frame to Detailed overview again; retain Fast overview as an explicit optional schematic.
- Preserve the selected preview mode across parameter edits; fall back to Detailed overview if a selected part is no longer available.
- Keep existing preview caching, CNC radius rules, and CAD/render pipelines unchanged.

## v0.93.47 — Pre-1.0 performance and stability
- Cache immutable parameter signature hashes and reuse snapshots in dependency-traced layout calculations.
- Reuse motor centres, plate bounds, standoff pairs, standoff layouts and plate levels while retaining caller-owned mutable data and dependency invalidation.
- Avoid duplicate component input fingerprints, repeated cutout parsing/encoding and unnecessary document property and BRep metadata reads.
- Reduce redundant editor label updates and apply fixed DJI O4 Pro control states through the batched refresh mechanism.
- Preserve existing CAD geometry rules, manufacturing validation, render settings and project compatibility.

## v0.93.46 — System Pictures export location
- Default all image renders and previews to the operating system’s Pictures folder via Qt, including redirected and localized locations. Manual save destinations remain available; project/look naming and collision protection are unchanged.

## v0.93.45 — Render names and CNC cutter radius
- Blender render exports include the selected look and receive a version suffix rather than overwrite an existing image.
- Frame > Layout includes the CNC cutter radius, shared by carbon profile finishing, cutout construction and validation. Existing designs default to R0.5.

## v0.93.44 — Clean render progress

- Keep the Blender rendering progress dialog to a single status line; retain process output for error diagnostics.

## v0.93.42 — Project-based export names

- Use the current FreeCAD project label for default Quick/Studio render image names, preview names, frame export folders and individually saved JSON settings. Fall back to the saved project filename for generic labels, or Untitled for new RotorForge documents.
- Sanitize invalid filename characters and preserve timestamp/collision handling for export folders. Keep manufacturing part filenames and export contents unchanged.

## v0.93.41 — Creative studio lighting

- Add nine distinct Blender studio looks: Neon Cyberpunk, Teal & Amber, Crimson Edge, Ice Blue, Violet & Gold, Overhead Softbox, Striplight Studio, Rim Silhouette and Pastel Editorial.
- Add six independently selectable lighting arrangements, including rectangular stripboxes, overhead and frontal softboxes, cross and back lighting. Add a fourth adjustable accent light.
- Advanced lighting controls include colour pickers for key, fill, rim, accent and ambient light, studio backdrop and floor, as well as AgX tonal contrast. Manual changes mark the look Custom; reset restores all look settings. White/Black/Transparent background overrides remain available.
- Retain original looks, camera/flight and render-quality presets, seamless floor transition, conditional Blender-only controls and frame geometry. New controls are render-only and collapsed by default.

## v0.93.40 — Conditional Blender controls & TPU cage edges

- Hide Blender-only controls and the Studio Render engine choice when no valid Blender installation is selected. Keep all shared Quick Render settings and manual path, Browse and Auto-detect controls available.
- Reveal Studio Render on detection or valid manual paths; return to Quick Render if the path becomes invalid. Avoid repeated installation discovery on ordinary UI changes.
- Match TPU camera cage edge shading more closely to other printed parts, without changing its face colour, metal mounts or CAD geometry.

## v0.93.39 — Cross-platform Blender discovery & seamless studio backdrop

- Expand native installation discovery on Windows, macOS and Linux, including Steam library folders, common portable locations, per-user installations, Windows Store executable aliases and Snap paths.
- Detect Blender Flatpak installations; stage only render job assets in a per-job directory and grant the renderer access for that launch.
- Add Auto-detect, support manual executable paths and recover from missing saved paths. Persist the selected installation after successful rendering. No recursive drive scans or Blender launch during detection.
- Blend the distant studio floor into the world backdrop using a smooth camera-only material transition. Preserve near-floor shadows and reflections without volumetric fog or subject blur.
- Rendering quality settings, geometry and existing design controls are unchanged. Cross-platform launch, sandbox behavior and backdrop appearance require live testing.

## v0.93.38 — High-quality studio rendering

- Add independent Fast, Balanced, High Quality (default), Ultra Quality and Custom rendering presets. Default Blender output is 4K when detected; resolution remains independent of quality.
- Expose maximum/minimum samples, adaptive noise threshold, denoising toggle, pixel filter width and finer 0.04/0.02 mm rendering mesh options. Use guided high-quality OpenImageDenoise where supported and keep camera depth of field disabled.
- Keep preview renders at up to 960 px and 16 samples with standard mesh detail; final renders use the selected settings. Export final PNG at 16-bit per channel and JPEG at maximum quality.
- No changes to frame geometry, editor, lighting/pose presets, viewport matching or manufacturing export. Syntax and isolated settings tests; live FreeCAD/Blender verification pending.

## v0.93.37 — Match FreeCAD viewport

- Add a Blender camera mode capturing the actual FreeCAD camera position, orientation, projection and field of view. Preserve pan and perspective; widen for output aspect or edge safety without moving the camera.
- Default to viewport matching when Blender is available; existing pose presets and orientation-only auto-fit remain available.
- Disable manual projection and focal length while matching the viewport. No changes to geometry or materials.
- Syntax and isolated camera-math checks; live FreeCAD/Blender verification pending.

## v0.93.36 — Studio-only rendering

- Remove outdoor landscape look presets, Outdoor Flight pose and outdoor HDRI controls and rendering code.
- Retain the original ten studio looks, nine pose presets including flight and hover, propeller blur, transparent PNG export and v0.93.35 perspective camera controls and focal lengths.
- Validation: Python syntax and isolated preset regression checks; live FreeCAD and Blender testing remains pending.

## v0.93.35
- Made Blender studio renders clearly support perspective views.
- Renamed projection choices to distinguish Perspective from Orthographic CAD-style rendering.
- Lowered default studio focal lengths so renders no longer look unintentionally orthographic.
- Updated pose presets and flight presets to use more natural perspective-friendly focal lengths.

## v0.93.34 — Outdoor flight environments

- Add Outdoor — Field & Forest and Outdoor — Golden Hour looks, plus an independent Outdoor Flight composition with low perspective, forward pitch, roll and prop blur.
- Generate a seeded metre-scale meadow, grass, mixed woodland and sunlight exclusively inside the external Blender render process. Outdoor ground distance and light azimuth are adjustable; no extra dependencies, download, CAD regeneration or editor initialization.
- Optionally load a local equirectangular HDR/EXR environment for photographic scenery and illumination. Panorama rotation is adjustable; an HDRI replaces the procedural scenery and does not provide a physical ground or contact shadows. Perspective projection is recommended.
- Preserve existing studio presets and all manufacturing geometry. Syntax and isolated preset tests only; actual Blender and FreeCAD rendering remains unverified.

## v0.93.33 — Studio looks and flight poses

- Rename the engine selector to Studio Render (Blender); Cycles remains the internal rendering engine.
- Add six independent look presets: Soft Dark Studio, High Contrast Studio, White Catalog, Warm Product Shot, Technical Gray and Showroom. Preserve the original four looks and their indices.
- Add nine composition presets, including hovering, forward flight and aggressive flight. Custom changes and reset actions are independent for lighting and camera/pose.
- Add render-only pitch, roll, yaw, flight height, shadow, propeller blur and forward composition margin controls. Spin uses lightweight annular exposure-coverage meshes with coloured transparent shaders and sharp hubs for detailed prop references, not a physical motion simulation. Hidden references remain hidden.
- Fit the transformed assembly and prop sweep bounds in the final aspect ratio; reserve forward margin before fitting. Flight effects are available only in Blender and do not change any CAD solids, saved frame parameters or manufacturing exports.
- Validation: syntax and isolated preset/framing tests; live Blender and FreeCAD testing remains pending.

## v0.93.32 — True black TPU

- Give the Black printed-part finish a dedicated neutral near-black (#080808) rather than borrowing the blue-grey propeller finish. Use the same opaque colour in native 3D, editor previews, swatches and Studio Render. Preserve all other colours, propeller finishes, saved selection names and geometry.
- Validation: Python syntax and isolated palette regression checks; live FreeCAD and Blender verification remains pending.

## v0.93.31 — Responsive frame editor startup

- Initialize Airflow / outlines and virtual FPV camera workspaces only on first use; retain control search, saved patterns, and the existing unapplied-edit protection.
- Open New / Edit frame in Fast overview, a lightweight schematic of the frame, motor/prop and mounting locations, basic component envelopes and bounded cutout markers. Detailed overview and individual part previews remain available from the existing preview selector. The fast schematic deliberately omits fine contour/TPU/texture details and is not a manufacturing check.
- Avoid repeated parameter normalization for unchanged editor inputs, unused detailed plate paths and duplicate arm paths. Cache the 2D carbon texture composition in memory; do not alter the native 3D or Studio texture pipeline.
- Avoid repacking identical navigation rows and emitting degenerate Bezier curves in the detailed 2D fillet preview; preserve normal validation and native CAD fillet/geometry generation.
- Add one-line editor startup timings to the FreeCAD Report view, separating widget construction, initial validation/control updates, and initial preview recording. This is diagnostic instrumentation, not a measured end-to-end speedup.
- Validation: Python syntax and isolated model/preview logic tests; live FreeCAD/PySide verification remains pending.

## v0.93.30 — Motor and prop finishes, studio materials and editor startup

- Expand the propeller palette from 13 to 30 finishes, including tinted clear and neon-clear choices, and share the new shades with the TPU palette. Use dedicated tinted polycarbonate transmission, IOR and roughness in Studio Render; keep original saved colour names.
- Add 13 motor bell colours under Arms > Motor references, shared by the FreeCAD viewport and Studio Render. Preserve copper windings, mounting feet, shafts and nuts; colour-only edits avoid shape generation.
- Prioritize fastener material classification over TPU camera cage role prefixes.
- Retune dark/cinematic lighting and low-key contrast; differentiate matte TPU from satin carbon without changing selected base colours or requiring carbon weave. Add subtle shader-only polymer grain.
- Share equivalent Blender materials; skip unused face palette and weave classification work.
- Defer initial editor validation until after first window exposure; avoid recording an obsolete default-frame preview. Keep Create/Update disabled until validation completes.
- Streamline loaded cutout list normalization, avoid repeat draft/title work, and cache preview-only TPU and LiPo text paths.
- Validation: source-level and pure-Python checks; live FreeCAD and Blender tests pending.

## v0.93.29 — Incremental performance and studio colour correction

- Reuse drilled structural plate and arm blanks across machining-only edits using a bounded native cache with parameter dependency tracking. Keep downstream machining and exact geometry checks intact.
- Reuse assembly collision bounds and propeller clearance probes; eliminate repeated intersections and unnecessary null-shape allocations.
- Reduce redundant document cache priming, native shape copies, BRep serialization and hardware parameter reads; index component cache lookups by role and reuse manifest serialization.
- Optimize preview path caching, parameter hashing, disk cache encoding and LiPo pad bounds calculations.
- Recalibrate studio light power for metre-scaled geometry, with distinct brightness levels per preset, darker studio floors and lower unwanted reflections. Preserve configured carbon, TPU and propeller colours and restore detailed reference face palettes when available.
- Validation: Python syntax and isolated cache/dependency, colour/power, archive and default parameter checks passed. Live FreeCAD geometry and Blender image output require local testing; no full-build speedup measured.

## v0.93.28 — Render Studio presets and automatic framing

- Apply complete Dark Studio, Light Studio, Cinematic and Clay Render lighting presets, with manual adjustments, Custom state and reset to the selected base preset.
- Separate backdrop and ambient lighting; add independent rim light, world strength and ground roughness, rebalance Cycles light intensity and use camera-relative light placement and AgX contrast.
- Preserve configured carbon, TPU and detailed propeller colours and read modern FreeCAD per-face appearance; use distinct surface finishes instead of a uniform grey look.
- Fit the full visible drone mesh to the output aspect ratio in perspective and orthographic projections; balance projected bounds using camera position and lens shift. The default zoom reserves at least 6% of the image dimension on each edge; lower zoom adds space.
- Skip UV generation for untextured parts. CAD generation, geometry and manufacturing exports remain unchanged.
- Camera fit mathematical tests cover 2,250 simulated perspective/orthographic configurations; live FreeCAD/Blender testing remains pending.

## v0.93.27 — Experimental Render Studio and performance pass

- Add a separate Render Studio command with high-resolution FreeCAD viewport export and optional external Blender Cycles rendering, without generating or changing CAD parts.
- Add camera angles, framing, preview export, resolution, studio lighting presets, material roughness, exposure, ground plane, transparent PNG, CPU / NVIDIA device selection and cancelable external rendering.
- Transfer visible frame solids and hardware, per-face reference colours and carbon weave/edge textures; keep the original CAD geometry and use display-only tessellation.
- Cache complete parameter validation and memoization field indexes, avoid duplicate appearance work on old geometry, reduce repetitive document property lookups and skip LiPo groove cutters fully removed by lettering reservations.
- Experimental: FreeCAD and Blender GUI/runtime validation remains necessary; no measured full-build speedup claimed.

## v0.93.26 — Custom LiPo pad lettering

- Add optional blind lettering to the battery-facing LiPo pad surface, with five fixed orientations/positions, independent XY offsets and inset from either end.
- Choose from 17 portable lettering designs with regular, bold, italic or bold italic styles; adjust height, width scale, stroke diameter, character spacing, depth and the smooth area on each side/end of the lettering.
- Keep grip grooves outside the reserved text area and preserve mounting/strap/airflow openings; reject lettering that crosses the finished pad or compromises the backing.
- Show lettering and the reserved area in the individual pad preview. Printable STL and STEP contain the lettering; the ungrooved DXF/SVG outline stays unchanged. Existing designs default to lettering off.

## v0.93.25 — Plate-following LiPo pad corner radius

- Enable the pad corner radius control for Mounting plate outline and round its outside perimeter after width and reach adjustments. Preserve internal openings, screw clearances, and the carbon carrier; zero keeps the unrounded carrier outline.
- Apply the same operation in the 2D preview and the manufactured/exported pad; reduce the effective radius when the outline cannot safely accommodate it.

## v0.93.24 — Structural countersinks and LiPo pad screw coverage

- Apply plate screw-head settings to non-shared arm bolts and shared joints on exposed arm roots or clamp plates. Motor, VTX and FC stack screws are unchanged.
- Add optional coverage of flush screws by the LiPo pad; preserve round-head clearances, structural openings and defaults.
- Keep the ungrooved LiPo outline export consistent with its airflow and screw coverage settings.

## v0.93.23 — Optional countersunk fasteners and airflow shape mirroring

- Separate round/countersunk screw-head settings for top, mid and bottom plate standoff mounts and TPU cage screws. Countersinks are machined at the actual screw-head seat; motor hardware is unchanged.
- Add local U/V shape reflection to Airflow / Outlines, including text and asymmetric profiles.
- Preserve through-cut DXF/SVG profiles and record countersinks separately in machining reports.

## v0.93.22 — Extended CNC engraving font selection

- Add Aerospace, Cyber, Industrial, Extended, Narrow, Reverse italic, Rounded italic, Racing block, Digital and Slab serif engraving styles. All eighteen built-in lettering styles use blind pockets.
- Preserve the existing styles, minimum cutter diameter, half-thickness pocket depth, preview and manufacturing export integration.

## v0.93.21 — Expanded CNC engraving styles

- Add Block, Compact, Racing, Rounded and Serif engraving styles; retain Technical, Italic and Dot matrix. All listed CNC fonts are selectable and use blind pockets only.
- Replace obsolete Block/Compact stencil topology with pocket cutter strokes; saved stencil patterns migrate to their matching engraving style at the original dimensions and 1 mm stroke. Keep the existing dot-matrix geometry and technical/italic lettering dimensions.
- Show live minimum fit dimensions for the chosen text and cutter diameter; preserve the R0.5 minimum tool radius and half-thickness limit.

## v0.93.20 — Blind CNC engraving

- Replace the selectable stencil fonts with Technical and Italic centre-line engraving, using exact round-ended cutter strokes of at least 1 mm diameter. Text is limited to blind pockets; older through-text patterns become shallow pockets at their saved depth.
- Keep legacy lettering geometry readable, retain half-thickness depth validation, and fuse overlapping engraving strokes per glyph before CAD machining and pocket-outline export.
- Update preview and minimum-size fitting to support readable compact labels without imposing through-cut web spacing within letters.

## v0.93.19 — Compact CNC lettering

- Add Compact stencil as the default font for new text patterns. Separate narrow rounded cutter strokes from material gaps and fit only the clearance bands needed by the glyphs and between characters.
- Retain R0.5, through-cut minimum web and final plate clearance/connectivity checks; allow smaller shallow lettering using Pocket.
- Keep the original Block stencil and Dot matrix dimensions and saved contours unchanged. Update the lettering controls and fit guidance.

## v0.93.18 — CNC lettering and side guard closure contour repair

- Add Text to Airflow / Outlines, with two self-contained CNC lettering styles, adjustable size, rotation, placement, dot diameter and a minimum-size fit tool.
- Use analytic R0.5-or-larger cutter profiles; preserve stencil bridges, minimum web and plate/fastener clearance validation. Support through cuts and half-thickness-limited pockets, including all glyph contours in machining exports.
- Keep the exterior of the combined plate-and-camera side guard closure on the plate-following profile. Guide only the inside of the panel toward recessed camera cages, avoiding outward landing flares.

## v0.93.17 — Front side guard contour control

- Add a front closure contour selector: both plate outlines and camera cage, plate outlines only, camera cage only, or either individual plate and camera cage.
- In the combined mode, anchor both carbon-edge lips to the finished plate profiles and steer the free wall toward the cage with a local landing.
- Sample both finished carrier outlines through the forward closure; update the plan preview and preserve the existing seam overlap and clearance operations.

## v0.93.16 — Continuous side guard front closure

- Start the camera enclosure before the lower carrier ends instead of leaving a gap beside the foremost standoff.
- Match the closure to the existing wall cross section in the shared overlap and then blend to the camera landing; synchronize both schematic and plan previews.
- Keep same-height motor-wire opening segments continuous rather than cutting separate rounded slivers at the transition.

## v0.93.15 — Simplify detailed LiPo reference

- Remove the external main and balance connectors, their contacts and wire harnesses from the detailed LiPo reference.
- Preserve the pack dimensions, cell layers, placement and clearance envelope.

## v0.93.14 — Optional M5 action-camera nut recess

- Add an optional reinforced hex-nut seat on the outside of the action-camera hinge, with a continuous M5 bore.
- Preserve the original three-finger mount when disabled and update its inspection preview.

## v0.93.13 — LiPo reference connector geometry

- Join both main power leads to the XT60-style connector and attach the balance-lead harness to its plug.
- Keep contact details within the balance connector housing rather than leaving them detached.
- Preserve the editable 3S–8S battery reference dimensions, battery clearance envelope, and all manufacturing geometry.

## v0.93.12 — Side guard camera enclosure correction

- Correct the forward-side guard closure for sloped camera walls. Its forward
  edge now uses one consistent reach rather than following the rear edge of
  the camera side plate at every height, avoiding the triangular extension.
- Keep the preview and actual 3D profile consistent and retain the existing
  plate-edge fit, wire access, camera openings and mount clearances.

## v0.93.11 — Correct front-closing electronics side guards

- Repair front-closing TPU side guards for every frame layout when a camera cage's
  sloping rear edge extends behind the foremost posts at upper heights.
- Keep the rear closure seam stationary and extend only its forward edge toward
  the camera cage; eliminate the large backward-folding triangular transition.
- Preserve front-post coverage, carbon-plate reliefs, camera screw access,
  normal motor-wire cutouts and all existing side-guard options.

## v0.93.10 — Rear antenna mount cleanup

- Restore the standard rear VTX antenna mount.
- Left all other workbench features and the bundled Help manual unchanged.

## v0.93.0 — Restore independent motor-screw visibility

- Fix shared hardware-reference objects that made Motor screws follow Arm bolts (and could also couple standoff, TPU cage and VTX screws on shared plates). Each screw group now has its own independently controlled reference object per component.
- Keep nuts and press nuts independently selectable; do not change mounting positions, reference screw dimensions, carbon geometry or manufacturing exports.
- Migrate existing frame hardware references on the next refresh, preserving saved display preferences and the global visibility setting. The new grouping affects display objects only.

## v0.92.99 — Export choices and independent nut references

- Added an export selection dialog for native FreeCAD CAM solids, STEP assembly, DXF and SVG cutting profiles, printable STL/STEP components, and manufacturing reports. Existing generated CAM solids can be removed only by explicit selection and confirmation.
- Separated modelled nuts and press nuts from screw geometry in Hardware References. Nut visibility is controlled by its own checkbox, independently of individual screw-group visibility; hardware retention geometry remains unchanged.

## v0.92.98 — Separate camera and TPU cage hardware references

- Split the hardware references window into independent **Camera screws** (FPV camera-to-side-mount screws) and **TPU cage screws** (M3 screws securing the TPU cage to the carbon plates).
- Preserve the geometry, mounting locations and lengths of both fastener sets, including the four raised upper cage screws with the optional action-camera mount.
- Migrate older saved hardware-display preferences so the original combined camera-screw visibility choice initially applies to both groups; once separated, each choice persists independently in the FreeCAD project and saved JSON.
- Leave all manufacturing geometry, frame parameters, exports and the bundled manual unchanged.

## v0.92.97 — Native 3D solids for CAM cutting sheets

- Export keeps the existing exact DXF/SVG cutting profiles and material-separated layout files on disk.
- The cutting layout embedded in the FreeCAD document now contains flattened **3D carbon solids** instead of planar faces. Existing snapshots are replaced in place on the next export.
- Preserve machined depths and surfaces, including blind airflow pockets, nut seats and countersinks, in the native CAM parts while maintaining the DXF/SVG through-cut profiles unchanged.
- Retain thickness groups, original per-part labels/links, alternating arm orientation and the established gaps and stock coordinates. Each part is placed on the stock plane at Z=0.
- The CAM solids are a manufacturing snapshot; re-export after editing frame parameters and create CAM jobs from the individual solids as needed.

## v0.92.96 — HD action-camera mount preview and hardware positioning

- Name the removable action-camera mount correctly in the 2D editor view selector and individual-part previews.
- Raise the four top TPU-cage M3 hardware reference heads to the added action-camera mounting base and increase shaft lengths by the same amount, preserving insert engagement.
- Leave bottom TPU cage screws, carbon holes and all other fasteners unchanged when the mount is enabled; disabled configurations retain their previous geometry.

## v0.92.95 — Optional TPU action-camera mount

- Optional separate TPU mount for the unified TPU camera cage, secured through its four existing upper M3 screws.
- Standard three-finger, M5-bolt action-camera hinge with adjustable height, fore/aft position and base thickness.
- Included in FreeCAD assembly, printable STEP/STL exports, part lists and mass estimates; preserves existing frame settings when disabled.

## v0.92.94 — Walksnail HD Pro mounting compatibility

- Repair older saved Walksnail HD Pro designs that still contain zero side-screw spacing: use the two-M2 6 mm vertical pattern and convert legacy single-pivot mounts to two fixed round mounting holes per side.
- Selecting the Walksnail HD Pro camera now starts in Fixed mode with two round holes on each side. Variable mounting remains available via the editor and uses two adjustable slots, or one pivot and one arc slot.
- Keep positive user-measured screw spacings, other camera profiles, and custom measurements unchanged.
- Clarify the editor's distinction between physical screw count and the holes/slots used by an adjustable carbon side plate.

## v0.92.93 — Walksnail Avatar HD Pro side-screw pattern

- Correct the Walksnail Avatar HD Pro physical camera profile from one M2 screw per side to two M2 screws per side, using the reported 6 mm vertical centre spacing.
- Let existing fixed and adjustable carbon/TPU mount generation, reference markers, side-plate openings, screw quantities and exported mounting information use the corrected two-screw profile automatically when selected.
- Keep previously saved custom screw spacings unchanged until the camera is deliberately reselected, avoiding silent alterations to existing designs.
- Preserve all other camera profiles, geometry, reference settings, and the bundled user manual.

## v0.92.92 — TPU cage 22 mm camera wall compatibility

- Repair a false X-bound violation in the straight TPU camera hard-mount wall when changing from a 19 mm camera to a wider 22 mm camera, including the Foxeer T-Rex Mini.
- If the plate-following contact spline overshoots the fixed wall interval, regenerate only that contact with an X-bounded, shape-preserving spline. The original smooth wall remains the default.
- Preserve the carbon-plate outer contour, fixed M3 socket positions, inner camera clearance, minimum TPU wall, and existing solid validity and interference checks. Physical width conflicts remain errors.

## v0.92.91 — Bundled user manual

- Include the newly written RotorForge user manual directly in the workbench package.
- Open the bundled PDF from the existing Help toolbar/menu command, preserving fallback support for older installation layouts.
- Include the PDF in source and wheel distributions; correct the README link and missing-file instructions.
- No changes to frame generation, saved settings, or CAD export geometry.

## v0.92.90 — Package cleanup and external Help manual

- Remove the two duplicate bundled Help PDFs and distribute the updated manual separately. The Help command now looks first beside the installed RotorForge folder in FreeCAD's Mod directory, then accepts legacy in-folder placements. When missing, it explains where to place the separate PDF.
- Remove an unused second installation-guide PDF and two unused icon SVGs. Preserve the root installation guide, icons actively used by the UI, all runtime Python modules, textures, metadata, the older saved-document compatibility bridge, and the existing geometry/export functions.
- Preserve the parameter schema, frame geometry, CAM/export operations, editor behavior, and cache implementation of v0.92.89. Update the workbench version and correct the existing README manual link without adding new README sections.
- Publish the refreshed 33-page help manual independently with the existing cover and chapter structure; add in-chapter guidance for LiPo airflow copying, automatic Keep/Randomize, Arc slot, blind pockets, machining, diagnostics and troubleshooting.

## v0.92.89 — Workbench-wide performance and stability audit

- Reduce editor refresh overhead: compute each control's final enable/disable state once, then update Qt widgets only if the state changed. Preserve all existing conditional visibility and parameter behavior.
- Reuse immutable geometry signatures across dependent FreeCAD parts, even when appearance and optical-preview options differ from defaults. Avoid repeated canonicalization of hundreds of unchanged parameters.
- Replace additional exact native solid-intersection calls with the existing conservative bounding-box-gated overlap helper. Every potential collision still uses an exact OpenCASCADE Boolean; assembly acceptance criteria remain unchanged.
- Speed common dependency-cache bookkeeping by indexing parameter names once per memoization miss and recording read dependencies in stable order.
- Avoid rebuilding optional hardware references twice on frame updates: the parameter proxy already synchronizes them during document recompute. Validate new frame parameters before restoring expensive geometry caches.
- Cache the 2D top-preview rendering signature across pan/zoom repaint events while continuing to ignore optical-only controls.
- Make dependent component failures visible and transactional: name the failed component in Report view and mark frame status invalid instead of silently clearing its solid while reporting a successful build. Report editor refresh errors and prevent building from a stale preview.
- Preserve the last actual geometry-build diagnostics on view-only color changes. Add a read-only **BuildStageTimings** property under frame parameters, separating disk-cache, carbon, TPU, battery, collision validation, references and cache-save time.
- Preserve the existing 0.92.88 parameters, cutout shapes (including Arc slot), pockets, CNC rules, exported geometry and all manuals/README. Headless tests validate parameter keys, cache dependencies, geometry grouping, generator proposals and source compilation; native FreeCAD timing and geometry behavior remain to be tested.

## v0.92.88 — CNC-safe curved arc slots in Airflow / outlines

- Add **Arc slot** to the manual airflow shape library: a smooth, round-ended curved channel with configurable width, centre-to-centre chord length, signed bend (-170° to +170°), rotation, grid and positioning.
- Use the same *analytic circular arcs* in Qt editor preview and exact FreeCAD solid-cutting tools, including blind half-depth pockets, through-holes, perimeter notches and material additions. No polygonal cutter approximation or automatic plate-wide fillet on a pocket boundary.
- Enforce the minimum R0.5 internal machining radius, at least 1 mm channel width, and non-overlapping end caps. A zero-degree arc remains a valid straight rounded channel; nonzero bends below 3° are rejected to avoid enormous-radius geometry.
- Include Arc slot among automatic manual-library and mixed generators, with correct left/right bend reversal for mirrored designs. Existing saved pattern JSON is loaded with a default arc bend, and the new field is included in path-cache keys to prevent stale contours.
- Existing full-depth web/fastener restrictions, pocket-depth limit and final validation remain in place. Headless shape-validation / geometry-continuity / serialization / mirror tests passed; FreeCAD and native Qt are not installed for end-to-end testing.

## v0.92.87 — Depth-only blind pockets; prevent unintended full-thickness fillets

- Fix spurious slits, spikes, and through-thickness contour changes around
  blind pockets: finish plate outlines and through-vent CNC R0.5 smoothing
  **before** shallow pocket machining, not afterwards.
- Pocket cutters now simply lower the selected footprint by the entered depth
  without feeding their rim into the aesthetic plate-fillet/CNC repair stage.
- Preserve the existing behavior for through holes, outside notches,
  mounting clearances, and pocket crossings of plate edges and holes.
- Reuse validated airflow pattern instances across both build stages; correct
  a 0.02 mm depth overshoot on the left carbon camera side plate.
- Bring FreeCAD Addon Manager package metadata up to the actual version.
- Exact solid and exported machining geometry still require an in-app FreeCAD
  test; native FreeCAD is not available in the automated headless environment.

## v0.92.86 — Blind pocket cable channels across existing edges and openings

- Blind airflow pockets may now cross carbon plate outlines, mounting holes, slots, through-cut vents, outline notches, and other blind pockets, including pockets of different depths. A connected half-depth cable channel no longer fails the full-depth vent perimeter/clearance checks.
- Retain strict maximum pocket depth of half the actual plate thickness, genuine through-cut minimum-web/fastener checks, CNC profile corner geometry, and final valid single-solid verification. Reject a pocket that misses carbon material altogether.
- Do not construct through-cut edge/fastener keepouts for plates containing only blind pockets, avoiding unnecessary exact CAD work.
- Keep exported through-cut DXF/SVG perimeter and holes intact when shallow pocket outlines reach outside the plate or intersect genuine through-holes. Restore pocket footprints only within the opposite unmachined plate face; do not alter the STEP/native model. Blind pocket machining profiles remain separate files with their own stated depths.
- Update editor guidance to describe open-ended cable channels and caution about reducing material near hardware seats. No parameter-schema changes; README and PDFs unchanged.
- Verification: Python compilation and headless Shapely-backed behavioral tests. Native FreeCAD BRep and DXF/CNC export still require an in-app test.

## v0.92.85 — Conservative camera-sweep broad phase and single BRep prototype

- Target TPU cage build checkpoint after insert openings: use a mathematically conservative rotated bounding box of the entire lens-plus-housing camera before constructing the expensive FreeCAD solids for individual tilt angles. Only angles whose boxes could reach a structural cheek or bridge require exact native collision Booleans; all plausible hits retain the original exact checks, OCC-artifact protection and selected-tilt hard failure.
- Build/fuse the detailed untransformed camera housing only once per TPU-cage tilt sweep. For angles requiring exact checks, rotate and translate a *copy* of that identical local solid; never mutate the prototype. Default camera_envelope behavior for all other callers is unchanged.
- Report tilt-angle counts, broad-phase skips, actual exact checks and time spent in clearance checks to distinguish this bottleneck from the rest of cage creation. Change misleading "camera clearance cuts" label to "camera clearance checks"; no geometry is cut from the cage by the camera envelope.
- Carbon material checks, the exact socket/captured insert operations and full final validation are unchanged. Existing parameter schema, saved settings, export and manuals unchanged. Native FreeCAD timing and topology must still be tested in-app.

## v0.92.84 — Scoped airflow refresh, spatial Qt previews and stability

- Reduce editor lag after editing generated/manual airflow openings: publish validated cutout JSON without triggering an unrelated whole-frame GUI refresh. A pending general frame refresh is respected; Create / Update and explicit CAD check still perform full validation and exact FreeCAD solid construction.
- Invalidate the Airflow plate silhouette only when necessary: changing saved through-cuts without changing frame geometry or additions preserves its existing cached blank. Restrict finished-part profile cache keys to the selected part's patterns; changing cuts on a different plate no longer discards unrelated entries.
- Use conservative bounding-box components to group Qt preview cutter profiles. Disjoint components are appended rather than repeatedly Boolean-united; potential intersections retain exact balanced Boolean unions. Batch disjoint holes, fastener bores, slots and cutouts into one preview subtraction. FreeCAD manufacturing/CNC tool generation is untouched.
- When randomizing around Keep cutouts, reject locally colliding candidate profiles before invoking the expensive full-plate containment Boolean. This is a change of test order, not acceptance criteria: both tests still run for every accepted proposal.
- Transform motor-pad and protector preview reference contours only once per batch of cutouts.
- Include generator wall-clock elapsed time in success and no-new-shapes messages for easier performance comparisons in FreeCAD.
- Keep existing parameter schema, saved designs, 3–10 mm selectable carbon web, R0.5 contour validation, LiPo airflow opt-in and unrelated README/manuals unchanged. Pure-Python tests passed; native FreeCAD/Qt speed, CAD topology, and dialog behavior require in-app testing.

## v0.92.83 — LiPo pad editor startup regression fix

- Fix `KeyError: 'LiPoPadCopyAirflow'` on New Frame / Edit Frame introduced in v0.92.82. The new LiPo-pad airflow checkbox existed in the parameter schema and GUI but was missing from the editor field-to-section layout.
- Place **Copy airflow cuts to LiPo pad** in **Battery → LiPo pad → Pad**, while keeping its linked control in **Airflow / outlines**.
- Verify complete GUI parameter-to-field classification, including hidden legacy fields, to catch unregistered controls in future changes.
- Keep existing airflow geometry, saved settings, LiPo pad model and performance optimizations unchanged.

## v0.92.82 — Optional LiPo airflow passthrough and lazy airflow preview

- Add **Copy airflow cuts to LiPo pad** under Battery / LiPo pad, mirrored as a linked checkbox in Airflow / outlines. On (default) retains v0.92.81 behavior; off makes the pad bridge the carrier plate's airflow holes and outline notches while preserving mandatory hardware/strap openings. Works with both outline-following pads and independent pads set to Follow mounting plate; no effect on an independent pad that is not clipped to the plate. Carbon geometry is unchanged.
- Only construct an airflow-free carrier solid when **Create Frame / Update Frame** actually builds a pad requiring it, and only if the selected carrier has relevant enabled cutouts. Avoid a second carrier build in the normal/default path.
- Airflow 2-D preview now invalidates its expensive plate silhouette only when the frame contour or enabled **Add material** patterns actually change, not when editing, keeping, reordering or regenerating ordinary cutouts. Pad-only controls no longer invalidate the carbon silhouette cache. Do not trigger redundant preview updates for unchanged parent snapshots or hidden editors.
- The fast 2-D preview remains advisory. Existing exact CAD clearance, CNC radius and solid-validation checks still execute during Create / Update and the explicit Check plate cuts in CAD action. Existing JSON/FCStd settings default to original behavior.
- Python compilation and portable geometry/settings regression tests are run headlessly; native FreeCAD and Qt validation still need end-to-end testing.

## v0.92.81 — Airflow generator redesign and fast preview

- Replace the costly whole-plate 40x Qt skeleton / region extraction / repeated simplification pipeline with a bounded, local candidate search around mounting hardware, existing user cuts and checked Keep shapes.
- Generate a more varied mix of small and medium irregular Web cells and CNC-rounded manual-library profiles; add a Cutout variety control (Mixed shapes / Web cells / Manual shapes).
- Use multiple staggered placement passes with progressively smaller proposals, allowing new openings to fit in the remaining gaps between kept shapes. Never remove the previous design when a reroll finds no valid additional cutout.
- Keep mirrored pairs linked by one Keep group, mirror genuinely asymmetric manual polygon geometry rather than only its centre, and permit occasional symmetrical central openings.
- Cache the exact eroded plate once per relevant geometry/web setting; use spatial buckets and conservative bounding-box rejection before local exact Qt path checks. Do not union kept openings into a huge growing clearance mask for every reroll.
- Enforce the configured carbon web against plate edges, mounting footprints, kept cuts and new openings; retain the analytic R0.5 validation and the final authoritative FreeCAD manufacturing checks.
- Render the Airflow preview by painting individual cached through-cut paths over the plate silhouette instead of constructing a 100x-scaled aggregate Boolean subtraction on every pattern revision. Preview filters do not hide real plate openings.
- Keep a strict generation attempt budget, guard against re-entrant actions, and preserve previous patterns on no-space results/errors. No changes to saved frame parameter schema, machine/export code, README or bundled manuals.
- Verification: full Python compilation; 120 randomized density/layout/seed scenarios with manual and Web-cell CNC checks; asymmetric mirror geometry comparisons; JSON Keep/group round trips; 35 simulated locked-shape rerolls produced additional cutouts in a representative plate. Native Qt/FreeCAD and exact BRep benchmark remain unverified in this environment.

## v0.92.80 — Stable editor opening and kept-airflow performance

- Prepare and validate the entire New/Edit dialog while it is still hidden; settle its native minimum/initial size before first display. This avoids running the expensive first refresh during the initial Windows paint, which could show a transient small white dialog before the correctly sized editor.
- Guard the editor action *before* constructing the dialog, preventing re-entrant toolbar/double-click activations from starting a second transient editor while the first is still initializing.
- Build multiple saved and generated air-cutout Qt Boolean unions in balanced pairs, avoiding repeatedly combining every new opening with an increasingly complicated accumulated plate path. Preserve exact analytic R0.5 contours, profile modes, and existing Keep semantics.
- Cache complete rounded Qt cutout paths by their immutable shape/dimensions/position/rotation/vertices (bounded to 384 entries), returning independent Qt path copies to callers.
- Exclude automatic Keep flags and group identifiers from geometric plate-preview cache keys. Keep checkbox changes are saved without rerunning full frame validation or rebuilding visually identical cutout geometry.
- Build the static mounting / saved-cutout mask once per generation, then compare candidate masks against existing obstructions and individual accepted shapes using cached rectangles instead of continuously performing Boolean operations on a growing available/keep path. Maintain original geometric intersection and perimeter acceptance criteria.
- Reuse the cached plate-safe/fastener-clearance mask on subsequent Randomize operations when the complete frame geometry, active existing openings, selected web spacing and mirror mode are unchanged. A change in any of these invalidates the single-entry cache; the random structural web itself always changes.
- Reject re-entrant Generate/Randomize execution, temporarily disable the action buttons during generation, and restore the busy cursor in a `finally` block on success, early return, or error. Report unexpected exceptions to FreeCAD's Report view.
- Keep manufacturing/export code, shape semantics, parameter schema, README, installation guide, and both existing help PDFs unchanged.
- Verification: Python compilation, cache/disk round trips, deterministic structural-web checks, 7,040 randomized Shapely geometric acceptance comparisons against the former mask logic, and 200-cutout balanced-union correctness tests passed. Native FreeCAD/Qt UI, OCC Booleans, physical manufacturing and end-to-end rebuild timings require testing inside FreeCAD.

## v0.92.79 — Document rebuild and cache performance

- Reuse the parent's already validated immutable parameter snapshot across dependent FreeCAD parts, avoiding repeated reads of every property for each component; invalidate the snapshot whenever a frame parameter changes.
- Compute frame mass and CG directly from read-only cached exact solids. Avoid creating unnecessary copies of the whole assembly and reference models solely for these calculations; exported and displayed shapes still receive independent copies.
- Cache canonical component manifests and restrict exact-match lookups to the requested component's indexed entries instead of scanning the complete BRep cache.
- On session cache restoration, skip ZIP decompression and SHA-256 hashing for components already verified in memory. Missing components continue through the original digest, FreeCAD BRep import, and shape-validity checks.
- Preserve 0.92.78's startup/UI/CNC optimizations, all Web cell cutout and Keep/Randomize behavior, the README, and both existing help PDFs without geometry or parameter-schema changes.
- Python compile/import smoke tests, 32 repeatable web-network cases, cache archive round trips, and synthetic 120-component lookup checks pass. Cache lookup was about 2.9x faster in that synthetic benchmark. Native FreeCAD rebuild speed and real BRep behavior are not yet benchmarked.

## v0.92.78 — Editor startup, layout and CAD-clearance performance

- Complete the editor widget hierarchy before beginning expensive initial validation and preview updates. Defer the first full refresh to the dialog's event loop, with a safe error message inside the open editor if the initial preview fails.
- Guard against concurrent editor windows caused by repeated New/Edit action activation. Reuse the existing window instead of creating another dialog.
- Batch Qt paint updates during settings refresh, reducing repeated intermediate GUI repaints while control states and preview messages change.
- Rebuild wrapping navigation rows only when the visible layout changes. Defer hidden-page wrapping until first display, reuse row containers across resizes, and skip redundant camera-section visibility changes.
- In the Airflow / Outlines CNC validator, skip exact OpenCASCADE edge-distance queries for edges whose XY bounding boxes cannot possibly violate the requested minimum carbon web. Keep exact distances for nearby edges and the existing acceptance limits.
- Preserve the full v0.92.77 web-first generator, Randomize, Keep selection, 3–10 mm spacing, manufacturing geometry, README and both RotorForge_Help.pdf copies.
- Standalone regression checks cover conservative clearance filtering, structural-web signatures, and mocked Qt navigation row reuse. Full GUI and BRep validation still require FreeCAD.

## v0.92.77 — Keep generated openings and optional central cutouts

- Add a **Keep** checkbox beside each automatically generated cutout in the Airflow / Outlines pattern list. It preserves checked openings when Generate/Randomize rebuilds the web, while allowing unchecked automatically generated openings to be replaced.
- Save Keep flags with the frame. If a generated opening has a mirrored partner, checking either one locks or unlocks both together; centre-spanning openings can be kept individually.
- Track the full set of kept and newly generated shapes across rerolls, including when Keep is later unchecked. Randomize remains disabled when no unlocked, unedited automatic openings are available.
- On reopening a saved design, Generate preserves checked automatic openings and manual cutouts while replacing unlocked generated cutouts on the selected plate.
- Randomize the structural web to occasionally omit a central spine section, keeping cross-ribs attached to the plate so an opening may occupy the middle. Allow the opening generator to treat this central region as a single CNC-rounded symmetrical cutout rather than forcing left/right halves.
- Preserve structural Minimum web and the selected 3–10 mm carbon spacing, hardware keepouts, and R0.5 corner checks. Manual cutout profiles remain untouched.
- Leave README and both RotorForge_Help.pdf files unchanged.

## v0.92.76 — Web-first airflow generation

- Replaced predefined-shape placement in automatic airflow designs with a randomized structural carbon-web network. The finished plate outline and protected mounting regions define the available cutout regions.
- Automatic openings now follow the safe plate boundary, mounting clearances, and generated web ribs instead of being assembled from the manual cutout palette.
- Preserved adjustable 3–10 mm carbon spacing (with global Minimum web taking precedence), exact mirrored layouts, Randomize behaviour, and through-cut/pocket modes.
- Automatically converts eligible negative-space regions into editable, analytically R0.5-rounded Web cell profiles for the FreeCAD model and CNC exporter.
- Extended custom Web cell capacity to 40 vertices for curved, plate-fitted contours; existing saved patterns remain compatible.
- Manual cutout shapes, Help PDF, README, and all unrelated frame components remain unchanged.

## v0.92.75 — Viewport, airflow and camera calculation optimizations

- Stop rebuilding the entire main dialog's parameter object during each Airflow preview mouse move. Reuse the parameter snapshot already produced by the normal 140 ms settings refresh and update it when the settings change; continue invalidating the preview geometry when its role or saved cutouts change.
- Avoid duplicate containment caches in the Airflow automatic generator. One bounded per-phase cache now owns the quantized point-in-plate queries.
- Avoid sampling shared polygon vertices twice during automatic cutout proposals. Preserve the exact original clearance sample positions, design candidates, mirrored layout, chosen gap and R0.5 requirements.
- Precompute rib-normal factors once per generated cell rather than repeating the same square roots for every potential cutout contour.
- Preselect recording-crop columns once when measuring virtual-camera frame and propeller visibility, avoiding repeated normalized-coordinate calculations on every image row.
- Preserve the exact outputs of 1,080 reference automatic cutout cases and 4,000 randomized camera-crop checks. No CAD geometry, manufacturing algorithm or saved-setting schema changes.
- Keep README and both RotorForge_Help.pdf copies byte-for-byte unchanged.

## v0.92.74 — Automatic cutout control, composite openings, spacing and performance

- Randomize remains disabled until Generate creates an automatic result; it only replaces the previous unchanged generated suffix. Manual edits, removals, and loaded designs cannot be silently replaced.
- Restore connected multi-part auto openings: randomized Web cells with overlapping machinable geometric accent primitives are proposed as atomic groups, with single-profile alternatives when the composite does not fit. Exact finished-union checks still govern acceptance.
- Add a 3–10 mm, 1 mm-step Carbon between cutouts dropdown. Save the requested spacing in each generated pattern and enforce it in the CAD final-group clearance checks, subject to the frame's structural Minimum web if that is higher.
- Adapt structural-spine/rib offsets to the chosen spacing. Cache reusable free-area queries and maintain existing geometry broad-phase rejection.
- Preserve both RotorForge_Help.pdf copies and README without modification.

## v0.92.73 — Profile reuse and editor responsiveness

- Reuse the exact R0.5 analytic local cutout profile geometry across saved-pattern validation, Airflow/Outlines 2D previews, and FreeCAD CAD tool creation. The 512-entry LRU cache is bounded and keyed by the unrotated shape, dimensions, and custom web vertices, so changing any of those dimensions generates a new profile.
- Cache edge-hit geometry for repeated mouse movement over Airflow/Outlines preview patterns, invalidated whenever patterns or zoom change. The matching and picking rules remain unchanged.
- Skip Qt path intersection checks when the broad-phase bounding boxes are disjoint; preserve the full geometric checks when they overlap.
- Skip expensive FreeCAD solid/solid overlap tests for cutout groups whose 3D bounding boxes cannot overlap; all actual overlapping groups retain the original OCC checks.
- Remove a redundant second LRU wrapper from the profile-parameter normalization cache.
- Preserve automatic structural-web generation, seeded variations, mirrored layouts, 5 mm carbon web requirements, R0.5 rounding, mounting keep-outs, and existing geometry. The README and both copies of RotorForge_Help.pdf remain unchanged.

## v0.92.72 — Randomized structural-web airflow designs

- Replaced the deterministic corridor pattern with a new randomized structural network: an axial spine, angled rib junctions, and occasional omitted ribs that create larger openings.
- Fitted custom, editable CNC-rounded web-cell cutouts between the structural lines instead of repeating fixed rows of slots and hexagons.
- Changing the design rerolls the structural lines themselves, including junction positions, slopes, and the arrangement of larger and smaller openings.
- Mirrored layouts reflect the entire finished profile; organic layouts use independently varied left/right contours.
- Added safe fallback cell proposals if a large opening cannot be placed around real mounting hardware.
- Added validated scalable polygon profile data to the existing Airflow / Outlines preview, saved patterns, CNC solids, and pocket workflow.
- Preserved automatic 5 mm minimum carbon webs and exact R0.5 profile rounding.
- Kept the README and both RotorForge_Help.pdf copies unchanged.

## v0.92.71 — Larger silhouette-filling airflow apertures

- Replaced short row-sized proposals with a corridor-based layout: the generator now scans the selected plate silhouette and its hardware keep-outs to find long, usable carbon bays.
- Increased the size of connected cutout designs (up to approximately 46–69 mm according to detail setting and available geometry), combining rounded primitive shapes into large openings where clearance permits.
- Added a second, incremental pass to fill the remaining safe bays after large openings are accepted. More candidate primitives are available for wider plates: Sparse 28, Balanced 56, Detailed 84 (subject to the 200-pattern global limit).
- Prioritized shoulder bays that can coexist with central openings, and added optional branching features and alternative sculpted axial compositions.
- Preserved exact bilateral mirroring, user-created cutouts, pocket depth limits, mounting keep-outs and 5 mm minimum carbon webs between finished automatic openings, holes and plate perimeter.
- Refused tiny point-contact overlap between joining primitives to avoid narrow, unmachinable junctions; skipped scaled duplicates already fully inside accepted cutouts to reduce boolean work.
- No changes to RotorForge_Help.pdf, README, geometry outside airflow, or manufacturing exporters.

## v0.92.70 — Connected, 5 mm web airflow cutout designs

- Reworked plate-aware automatic cutouts using the supplied commercial FPV plate examples as visual design references. The generator selects structural zones from the actual chosen plate silhouette rather than scattering cutouts on an arbitrary grid.
- Each proposed opening can be made by overlapping two or more independently CNC-rounded profiles, producing one connected opening in the Qt preview and the CAD cut operation.
- Apply a minimum 5 mm carbon web **once around the finished merged aperture**: to other openings, the plate outline, mounting holes/bearing footprints, and existing cuts. Persist this 5 mm allowance in generated patterns so FreeCAD checks it again after later frame-geometry changes. Overlap inside the same opening is permitted and required.
- Change automatic pattern acceptance to validate grouped components atomically; mirrored openings are exact reflected pairs of the complete constituent profiles, not independently-placed shapes.
- Give central spines, paired swept wings and branched side vents a purposeful front/centre/rear order that responds to available plate space; Randomize changes the recipe and proportions without free-scatter placement.
- Keep generated primitives individually editable, retain pockets/through-cut options, and preserve all existing saved patterns and manual controls.
- Preserve the README and both RotorForge_Help.pdf copies verbatim. Native FreeCAD 3D and GUI testing remain necessary before manufacturing.

## v0.92.69 — Plate-aware airflow design and reliable symmetry

- Replaced free-scatter automatic cutouts with front/centre/rear plate-specific motif grammar informed by commercial FPV carbon plate designs.
- Added Aero spear and Split bridge, two editable CNC R0.5 compatible single-opening profiles, and built mixed multi-opening motifs from existing shapes.
- Mirrored generation now submits genuine reflected left/right partners atomically; uneven mirrored accents cannot be saved by the generator.
- Replaced the numeric design variation setting with Generate plate design and Randomize design actions. Reroll replaces the immediately previous unedited automatic pattern, preserving manually authored cuts.
- Removed the unreliable automatic outline-sculpting interface and generator. Manual outline notches remain available.
- Reduced geometry sampling and avoided repeated profile/stroker calculations. Existing pocket-depth limits and manufacturing clearances remain in force.
- Left RotorForge_Help.pdf and README.md untouched.

## v0.92.68 — Preview, airflow, and build-path performance

- Cache unchanged plate and profile outlines in the 2D editor, with safe copies and bounded cache sizes.
- Reuse the saved Airflow / Outlines preview until the selected part, cutouts or frame settings change.
- Avoid rebuilding pattern JSON identifiers and repeated filter text during preview interactions.
- Halve repeated clearance probes in automatic airflow proposals while preserving the generated designs and CNC safety checks.
- Cache normalized cutout-pattern parsing without exposing mutable cached dictionaries.
- Skip expensive exact CAD distance checks for hardware keepouts whose planar bounding boxes are provably outside the clearance range.
- Avoid duplicate shape construction for accepted automatic cutouts.
- Keep the RotorForge Help PDFs, README, plate geometry rules and manufacturing output formats unchanged.

## v0.92.67 — Adaptive mixed-shape airflow cutouts and CNC-rounded profiles

- Replaced repetitive row-based internal cutout proposals with irregular, clearance-aware compositions based on the actual usable shape of the chosen carbon plate.
- Added variation seed, density, arrangement (organic or mirrored) and new interior design styles. Generated cutouts remain individually editable.
- Expanded the cutout shape menu to include triangles, diamonds, trapezoids, hexagons, pentagons, heptagons, octagons, dodecagons, chevrons, parallelograms, kites, hourglasses, crosses, shields and swept fins.
- Polygon cutters and previews use true circular R0.5 fillets at convex and concave corners; incompatible dimensions are rejected rather than silently shrinking the required cutter radius.
- Kept the legacy Crescent/Leaf profiles loadable but not offered for new CNC geometry until their freeform curvature can be guaranteed.
- Preserved the existing manual PDFs and README without modification.

## v0.92.66 — Compact virtual camera workspace

- Rearrange FPV > Camera view into side-by-side camera options on the left and a large aspect-preserving rendered preview on the right, with recording and obstruction results directly below the image.
- Keep optical profile overrides available in a collapsed Advanced options section; finding any of those controls expands the section automatically.
- Make the layout stack vertically only when the usable editor width becomes too narrow. Camera images automatically fit the available preview area without rerunning ray tracing when the window is resized.
- Bound the detailed results panel so long diagnostics no longer force the entire Camera view tab to scroll.
- Keep all optics, crop, propeller visibility, tilt analysis and frame-generation functions unchanged.
- Leave both RotorForge_Help.pdf copies and README unchanged.

## v0.92.65 — Restore workbench startup and contour-aware airflow generation

- Fix the FreeCAD startup KeyError for the new Pocket depth input in the Airflow / Outlines search-control registry. Future unnamed numeric controls use a safe fallback label.
- Replace fixed-row automatic internal cutouts with proposals sampled from the actual selected plate outline, including through-holes and protected mounting regions.
- Adapt position, shape size and orientation to usable bays in each plate, keep left/right symmetry, and preserve conservative edge and fastener webs and native CAD validation.
- Keep the redesigned Help PDFs and README unchanged.

## v0.92.64 — Airflow pockets and automatic CNC patterns

- Give the FPV camera view its own full-width workspace, hiding the redundant generic 2D frame preview while retaining the optical render and all related controls.
- Add selectable blind pocket cuts with editable depth limited to 50% of the carbon part thickness, measured from the upper or outer surface.
- Export blind-pocket contours separately from through-cut DXF/SVG profiles; add pocket depth and machining-face entries to MachiningOps.csv while retaining pocket geometry in STEP.
- Offer only cutter-accessible circular, rounded-slot, rounded-rectangle and ellipse shapes for newly designed cuts; maintain loading compatibility with older custom shapes.
- Introduce conservative automatic internal airflow patterns and sculpted exterior profiles. Proposals are symmetric, protect the existing geometry and hardware keepouts, remain editable, and undergo the normal native CAD checks on building.
- Do not modify any Help PDFs or the existing README. The manual will be revised separately.

## v0.92.63 — Complete integrated Help manual

- Rebuilt the user guide from the actual RotorForge editor sections and the original illustrated manual.
- Restored the original design explanations and added current controls, including the separate Airflow / outlines workspace.
- Relocated every original illustration to the matching feature section; front bumper profiles now appear under TPU > Front bumper.
- Integrated camera isolation, captured insert recesses, virtual propeller visibility, carbon texture and CNC guidance with the related controls.
- Preserved the existing documentation design and FreeCAD functionality; this release changes documentation and version metadata only.

## v0.92.62 — Integrated Help manual

- Rebuilt the Help manual as a cohesive, topic-organized guide rather than an original PDF followed by release supplement pages.
- Integrated recent arm-root, keystone, CNC, camera isolation, flush insert, virtual camera, propeller visibility, carbon-fiber texture and manufacturing controls within their original chapters.
- Retained the existing illustrations and established document visual style, with updated contents and PDF navigation.
- Documentation only: all CAD geometry, rendering, interface and exporters remain unchanged.

## v0.92.61 — Updated Help PDF (documentation only)

- Extend the existing 36-page RotorForge Help manual with five matching A4 pages explaining recent arm-root, keystone and CNC geometry controls, TPU/camera insert seats, virtual camera propeller visibility, carbon weave rendering and performance options.
- Preserve the existing manual typography, colour palette, cover image and page order, with a clickable Contents extension, updated bookmarks and the same Back to contents navigation.
- Synchronize both packaged Help PDF copies and update the manual and workbench edition labels.
- No frame geometry, parameter defaults, modelling functions, rendering behaviour, exporters or README changes.

## v0.92.60 — Performance optimization

- Reuse carbon surface and cut-edge scene meshes when only the texture opacity changes or FreeCAD reapplies unchanged appearance settings.
- Keep appearance-only carbon settings out of native CAD geometry cache signatures, preserving cached frame geometry and virtual-camera meshes.
- Trace virtual-camera rays through the BVH in near-first order to prune triangles behind closer obstructions; retain the existing BVH builder to avoid introducing a preprocessing slowdown.
- Avoid full BRep serialization when an unchanged FreeCAD part has the same native OCC shape and a matching verified component cache token; keep the full digest verification fallback for modified/restored solids.
- Remove duplicate, unused copies of every component in Create/Update Frame preflight; document recompute still receives independent copies as required.
- Keep camera-view samples valid across texture/colour adjustments while preserving correct invalidation for optics, tilt and geometry changes.
- No intended change to frame shapes, STL/STEP/DXF/SVG exports, 1 mm cutter rules, or saved-frame parameters.

## v0.92.59 — Default 30% carbon texture opacity

- New frames use 30% carbon texture opacity for both plain-weave faces and laminated cut edges.
- Unspecified/missing opacity values also fall back to 30%. Previously saved explicit opacity settings are preserved.
- The texture toggle, weave size, arm orientation, and all geometry/manufacturing exports are unchanged.

## v0.92.58 — Laminated carbon-fiber cut-edge texture

- When the existing Carbon fiber texture option is enabled, broad carbon faces retain the 1×1 plain weave while CNC-cut edges display subtle, horizontal, closely spaced laminate-ply lines.
- Edge UVs use world-space sheet thickness (Z on horizontal carbon sheets; Y on vertical camera side plates), including curved/filleted edges and mounting-hole walls. Separate physical scale (eight plies in 2 mm) avoids stretching the weave down cut edges.
- Existing opacity control blends both textures over opaque carbon. Both overlays are removed when disabled or at 0% opacity; no new settings or saved-frame migration.
- Rendering-only change. Native carbon geometry, manufacturing exports, arm weave directions, and 2D top-view previews are unchanged.
- Native FreeCAD 3D viewport rendering has not been tested.

## v0.92.57 — Carbon-weave opacity and arm-aligned mapping

- Adjustable carbon texture opacity (0–100%): blends the plain-weave image with opaque carbon, never making the frame transparent.
- Each carbon arm's weave direction automatically follows its root-to-motor axis; fuselage plates retain the original XY alignment.
- Matching 2D previews and 3D viewport overlays. Appearance-only settings persist with saved frames and do not rebuild or alter CNC geometry.
- Older designs default to 100% weave visibility and preserve existing appearance.

## v0.92.56 — Plain-weave carbon texture
- Replaced 2x2 diagonal twill imagery with a dark 1x1 plain-weave (over-under/checkerboard) carbon-fiber fabric texture.
- Preserved the face-only UV mapping used to prevent stretching and smeared texture on cut carbon edges.
- Kept the optional carbon texture toggle and physical weave repeat size; existing settings and saved designs are unchanged.
- Renamed the bundled PNG asset to prevent the previous texture being reused from the FreeCAD/Coin texture cache.
- Appearance-only update; no CAD geometry or manufacturing output changes.
- Native FreeCAD GUI rendering still needs verification.

## v0.92.55 — No-smear carbon weave mapping
- Replaced the old wide boundary-blended texture with a naturally periodic 2x2 twill motif sampled at its real weave repeat. This removes large blurry fade bands from the PNG itself.
- Replaced the single projection across every BRep face with explicit XY/XZ UVs on only the broad flat carbon laminate faces. Cut sides keep a dark untextured carbon edge instead of stretching one texture row over their height.
- Uses a pick-through, depth-offset, Coin3D appearance overlay without modifying the CAD Part geometry or export data.
- Matches UVs across independent flat faces and across adjacent parts in the same design coordinates, independent of their triangulation.
- Existing texture toggle and weave repeat setting retained without changing frame parameters.
- Native FreeCAD visualization still requires user GUI verification.

## v0.92.54 — Optional carbon-fiber weave texture (visual only)
- Packaged a dark 2x2 twill carbon-fiber seamless PNG texture, with matching tile edges.
- Added Finishing → Carbon texture toggle and adjustable physical repeat size in mm.
- Applied repeatable world-space texture coordinates to carbon BRep view objects using Coin3D; camera carbon side plates use vertical mapping.
- Added an optional woven pattern in editor/part inspection views.
- Treated finish-only edits as view updates, without full shape regeneration.
- Automatically attempts to restore texture scene nodes when opening saved FreeCAD frames.
- Keeps previous flat carbon finish as the default, and excludes all textures from manufactured geometry and export data.
- Native FreeCAD texture output still requires on-device validation.

## v0.92.53 — High-contrast magenta propellers in virtual camera (test build)

- Change possible propeller sweep in FPV → Camera view from faint amber to bright semi-transparent magenta, with a thin high-contrast perimeter for easier recognition.
- Update the camera-view legend, hover help, and recording-window explanation to match the new color. The yellow crop boundary, physical obstruction colors, simulation results, and frame geometry remain unchanged.
- Overlay color updates immediately when toggled; no extra geometry rebuild or ray casting is required. Native FreeCAD GUI rendering remains unverified.

## v0.92.52 — Flush carbon camera inserts (test build)

- Add **Flush carbon-side captured inserts** under TPU → Camera isolation. When a carbon side plate uses Outside/Both retaining lips, recess its outer flange into a shallow, matching YZ counterbore, leaving a minimum 1.0 mm carbon supporting ledge. No changes to through-neck openings, motor positions, or TPU-cage mounting settings.
- Generic rounded/special-shaped inserts and DJI O4 split circular/arc-track inserts use matching recess profiles. A separate pocket depth and fit clearance apply only at the exterior face. The matching TPU lip and camera screw reference relocate to the original outside carbon plane.
- Export exact recessed solids in STEP; add blind pocket operations and depths to MachiningOps.csv. Flat DXF/SVG remain **through cuts only**, so CAM must process pocket geometry separately from STEP with the specified exterior face/depth. No automatic CAM/toolpath is generated; separate aligned pocket outlines are supplied for CAM.
- Previously saved frames retain projecting carbon-side inserts by default. Native FreeCAD rebuild and machining exports require verification.

## v0.92.51 — Propeller sweep overlay in virtual FPV camera view (test build)

- Compute separate motor-centred propeller swept discs using the existing motor-pad-adjusted positions, prop diameter and reference-plane heights.
- Show translucent amber possible prop visibility in FPV → Camera view (enabled by default); toggle visibility without regenerating CAD geometry or tracing rays again.
- Trace each prop disc only in front of the entrance pupil and in front of the first physical frame/TPU hit; opaque frame and TPU measurements stay separate.
- Report image-wide, central-region, and selected recording-window propeller sweep percentages separately from actual frame/TPU obstruction; include potential prop sweep in tilt-range analysis.
- This is a conservative swept-area estimate, not simulated blade imagery: RPM, shutter, spinning blades, EIS/sensor crop and individual blade geometry are not calibrated.
- No changes to saved frame geometry, motor positions, or manufacturing exports. Native FreeCAD GUI test required.

## v0.92.50 — CNC contour auto-repair and uniform TPU camera-facing walls (test build)

- CNC: defer too-short local fillets to a final exact rolling R0.52 mm-cutter repair pass, instead of failing immediately. The pass includes under-radius line/arc junctions and small 2D pocket corners; protect all existing bores, fitted arm miter cells and topology. Refuse only geometry that cannot be repaired without violating these safeguards. Does not modify saved arm-bolt allowances.
- TPU cage: use exactly the same camera-facing wall X position and straight wall construction for Hard mount, Compression pads and Captured inserts, while keeping the carbon-derived outside shell and M3 mount coordinates fixed.
- Compression pads: create local flush seats recessed into that constant wall, using the real pad thickness and preload. Preserve the wall everywhere outside the pads and retain at least 1.2 mm of external TPU behind them. Applies also to paired DJI O4 Pro isolators.
- Flush captured inserts: move the optional camera screw hardware reference start plane and recompute its length to suit the actual flush outer flange; regular projecting lips use their real configured projection instead of a fixed estimate.
- Retain the v0.92.49 plate, keystone, motor pad, standoff, and TPU geometry features. Native FreeCAD rebuilding and CNC exports still require an in-app validation run.

## v0.92.49 — Automatically resolve cramped R0.5 arm-root transitions (test build)

- Fix the new v0.92.48 build failure at cramped concave arm-root/arm-bolt stock junctions (e.g. `ArmFrontRight X20.32/Y29.53`). The cutter rule no longer immediately rejects a corner solely because one intersecting edge is too short.
- Before applying individual exact R0.5 fillets, run an **additive rolling-circle closing** of the outer silhouette, selectively retaining only small local patches adjacent to the detected short inside corners. This merges narrow intersection fragments and generates smooth R0.52 cutter-compatible transitions without adding another bolt-stock allowance or changing screw coordinates.
- Reject any candidate patch that touches drilled holes/cutouts, escapes the fitted-miter joint cell, alters a large portion of the arm, or invalidates the connected outline. Remains strict about genuinely unmillable geometry rather than silently ignoring it.
- Preserve all saved frame settings, TPU cage improvements, motor-pad profiles, and optional cosmetic fillets. Native FreeCAD and actual CNC export should be checked before machining.

## v0.92.48 — 1 mm CNC end-mill inside-corner rule (test build)

- Introduce a mandatory **R0.5 mm minimum re-entrant corner radius** for finished carbon plate and arm contours (1 mm cutter). Zero user-set cosmetic fillets still allow sharp exterior convex edges, but not sharp concave notches or internal cutout corners.
- Round qualifying concave vertices using exact OCC arcs in the manufactured 3D carbon outline, not only in a cosmetic preview. All closed cutouts receive mandatory internal corner reliefs even when optional aesthetic cutout filleting is off. Optional nonzero fillets are never reduced to sub-0.5 mm radii.
- Prevent silent under-sized radii: if a mandatory inside fillet collides with bolt material, fitted joints, nearby geometry, or cannot fit the edge, report the affected part and X/Y position instead of emitting an unmillable profile.
- Keep compact keystone and its mating pocket aligned, with an R0.5 mm floor for their matching corner arcs. Very small key geometry that cannot support the minimum produces an explicit sizing error.
- Update 2D plate/arm previews and tooltip explanations. No changes to the saved frame setting names, hole centres, plate reaches, arm bolts, TPU or camera settings.
- Excludes through-hole drilling/tool compensation; the 1 mm cutter reference concerns plan-view internal corners. Native FreeCAD construction and CNC export need real-world verification.

## v0.92.47 — Straight TPU inner walls and flush captured inserts

- TPU cage inner side walls now use the same two-contact ruled construction in Hard mount, Compression pads and Captured inserts; eliminates soft-only intermediate loft bands.
- Added **Flush outside captured inserts** under TPU → Camera isolation. When an outside retaining lip is enabled, a matching shallow exterior seat allows the lip face to finish flush with the cage outer wall. Off preserves the projecting lip.
- A single shared axial layout is used for both left/right printable cassettes and their matching cage seats, including separate DJI O4 Pro inserts.
- Updated the 2D TPU cage preview and lower bridge wall contacts. Camera mounting centres, structural plate outlines and carbon holes are unchanged.

## v0.92.44 — Independent arm-root and keystone fillets (test build)

- Add **Arm root corner fillet** under Arms → Roots → Root shape. This controls the central junction/root corners independently of **Arm corner fillet** on the beam and motor-side outline. Radius zero keeps the corresponding corners sharp. Protect existing arm bolts and minimum webs; fitted-miter root fillets remain restricted to their own joint cell.
- Add **Keystone corner fillet** under Arms → Clamps & key → Keystone. When a compact keystone is used with fitted miters, round both the keystone and its matching pocket using a single rounded outline and an outward offset pocket with the configured clearance. Automatically limit an excessive radius so neighboring tangent points cannot cross.
- Keep analytic circular arcs for native FreeCAD keystone and matching pocket solids (and hence STEP/DXF exports); the editor preview uses closely sampled equivalents. No rounding or outline change at the new keystone setting's default zero.
- When opening saved frames from earlier versions, initialize the new arm-root radius from the old arm corner fillet to preserve existing root rounding. Newly created frames keep both radii at zero until edited.
- Preserve all other arm, bolt, standoff, plate-reach, mount-material, and plate-profile settings. Tests: 864 2D keystone geometry/clearance cases, old/new preset compatibility, separate arm-radius selection, and Python compilation. Native FreeCAD rebuild and CNC/STEP export not available to test in this environment.

## v0.92.43 — Fillet fitted arm-root junction corners (test build)

- Extend the existing Arm corner fillet into the exposed central root/junction contours when using **Fitted miters**. Previously an unconditional root-limit exclusion kept these visible corners sharp even at a nonzero fillet radius.
- Keep Independent arm-root stock unchanged. On fitted joints, preserve each arm's root-bolt support, including its configured additional material allowance and any shared standoff bearing footprint, and reject added fillet material outside the arm's own fitted-miter cell.
- Apply the same eligible root-corner treatment in the 2D arm preview; radii remain adaptive and may be reduced/skipped by geometry checks. No added material around press nuts or receiving-plate fasteners, and no changes to bolt locations or arm joint clearance.
- The central junction consists of separate CNC-cut arms. Corner rounding can leave a very small local gap at the exposed joint endpoint, while the straight load-bearing mating edge remains unchanged elsewhere. Inspect actual fitted-arm assembly clearances before cutting.
- Python syntax and configuration regression checks performed; native FreeCAD geometry generation and final 3D/STEP/DXF behavior remain unverified.

## v0.92.42 — Conservative CNC perimeter spur cleanup (test build)

- Target the tiny outward nubs at overlapping arm-following tabs and plate bodies on Bottom and Mid plates. Use a nominal 2 mm diameter cutter reference (1.0 mm geometric cleanup radius), but **only** consider small local fragments near a short, non-tangent contour junction; do not globally offset or expand the outline.
- Subtract selected tiny protrusions from the final plate blank; never increase arm, press-nut, standoff or plate mounting support. The required screw/insert/standoff/TPU bearing envelopes are protected explicitly.
- Validate each BRep subtraction for connected, valid solid geometry; if an offset or boolean fails, retain the original plate instead of blocking frame creation. Match the same conservative intent in the 2D editor preview.
- No changes to frame dimensions, mounting coordinates, arm-bolt allowance, or existing fillet options. Native FreeCAD build, DXF and STEP still require verification against real frame settings.

## v0.92.41 — Simplify editor maximize controls

- Remove the redundant Maximize window / Restore window action from the bottom bar beside Create/Update frame.
- Keep the native title-bar maximize/restore button enabled; frame creation and the rest of the editor remain unchanged.

## v0.92.40 — Restore shared arm/receiving-plate contours (test build)

- Fix the arm/plate contour mismatch introduced in v0.92.39: the front Mid-plate and rear Bottom-plate tabs were clipped against a **zero-allowance** arm root while the actual carbon arms included the user's extra bolt material.
- Build the tab masks using the **same actual arm-root silhouette** as the arms (including shaped roots and selective local bolt reinforcement). Where actual bolt reinforcement grows beyond the original fixed receiving-tab capsule, locally extend its trim mask by **only those exposed arm-bolt discs**; otherwise the old tab cap would clip all the new material and the outlines would still fail to follow. Apply this to the upper/lower clamp-plate root masks too.
- Make the 2D cutting preview and analytical tab-distance check use that same arm setting; previously the tab clearance checks also used the zero-allowance shape.
- **Do not** reapply arm-bolt material allowance to press-nut holes or receiving-plate support radii. The original tab overlap capsule, plate reaches and clipping boundaries are retained. No hardware centres or dimensions have moved.
- No changes to the FreeCAD 3D fillet system, camera TPU rim checks or standoff placement rules. Full final solid validation in native FreeCAD remains necessary.

## v0.92.39 — Independent arm and press-nut envelopes (test build)

- Fix mid-plate press-nut lobes chasing the adjustable arm-bolt reinforcement: the extra allowance now applies to carbon arms only. Receiving plates keep fixed support for their drilled holes and nut seats; their receiving tabs are calculated from the original structural arm footprint, so the nut pads no longer chase the arm as its extra material grows.
- Reduce oversized circular supports by checking the true hole or press-nut shank with MinimumWeb, and the physical standoff/flange bearing outline with a small 0.35 mm edge lip. Do not add MinimumWeb a second time outside a proud flange or standoff body. Recessed flanges still preserve a full web outside the cut pocket.
- Use the same standoff/press-nut footprint in reinforcement selection, mount validation, and protected press-nut fillets. Shared arm/standoff screws remain one physical fixing with no duplicate allowances.
- Preserve the v0.92.38 recursion fix and existing frame settings. Native FreeCAD build remains to be tested.

## v0.92.38 — Break standoff/arm-support recursion (test build)

- Fix a circular dependency in v0.92.37 that made a frame with 6 or 8 standoffs fail to update with `maximum recursion depth exceeded in comparison`.
- The arm-bolt support calculation now reads the raw standoff hole locations and infers whether the standoff actually bears on an exposed arm from the plate/arm configuration. It no longer calls the full geometry-dependent standoff layout.
- Preserve v0.92.37's rule that shared standoff and arm-bolt material requirements are independent, applied once, and only on the correct receiving layer. No changes to frame dimensions, plate perimeter geometry, or existing design settings.
- Regression-tested independently for 4, 6, 8 standoffs, shared/non-shared positions, 2/3 plates, and upper/lower arm placements. The complete 3D rebuild still requires native FreeCAD testing.

## v0.92.37 — Correct shared standoff / arm-bolt reinforcement (test build)

- Correct the shared-fastener radius calculation: arm-bolt material allowance is applied once to the arm-bolt through-hole bearing, not to the standoff outer diameter. The standoff footprint is a separate, fixed requirement, and the larger applicable envelope wins instead of adding margins.
- Assign the standoff outside-diameter footprint only to the carbon layer which actually supports the standoff (mid, bottom, upper arm clamp or exposed arm top), while the top plate still receives its normal standoff support.
- Consolidate coincident arm-root and standoff holes into one reinforcement request per physical fastener. Preserve the layer-specific machining holes, bolt positions, nut seats and standoff placement.
- Continue to use the v0.92.35 selective CAD / editor-path check: existing material stays unchanged, and only a genuinely missing portion of a bearing disk can cause an extension.
- Source-reviewed and standalone Python tests passed. Native FreeCAD rebuild / final manufacturing checks remain to be performed.

## v0.92.36 — Restore TPU cage M3 carbon bearing support lost in v0.92.35 (test build)

- Fix regression where selective arm-bolt/press-nut material could leave a neighbouring TPU cage M3 mounting hole with less than the required 2 mm carbon rim (for example 3.04 mm from hole centre instead of 3.60 mm).
- Check the four bottom and four top TPU M3 screw positions against each actual generated carbon-plate blank. Add ONLY missing bearing material at those exact positions; leave already-supported outlines completely unchanged. Never increase an entire perimeter or move mounting holes to hide a failure.
- Avoid joining unsupported floating mounting pads: if less than 75 percent of a full bearing circle contacts the plate, report the insufficient plate geometry instead of producing a large projection.
- Preserve the TPU screw bearing material during final plate edge filleting. Mirror the same local decision in the editor's 2D profile calculation.
- Measure the cage clearance against the exact CAD outside wire, not a tessellated polyline that can falsely reject an exactly sufficient circular rim.
- Keep the v0.92.35 selective arm-bolt support logic, nut/standoff coordinates and existing TPU cage contour construction unchanged. Native FreeCAD rebuild must be verified in the user's configuration.

## v0.92.35 — Only reinforce mounting material actually missing (test build)

- Use selective support geometry to prevent unwanted bumps and faceted plate edges.
- Check each bolt/press-nut support disc against the actual FreeCAD base-plate or arm solid, including tabs, reach geometry and shaped arm roots, before adding any stock. If the full disc already fits inside the part, leave that section of perimeter **completely unchanged**.
- Where additional bearing material is truly required, add only the exact circular support. Add an anchoring capsule solely when that disc would otherwise be detached or weakly attached to the existing plate.
- Apply the same incremental support selection to the 2D editor preview, with a small area tolerance for numerical slivers.
- Keep original bolt, press-nut, standoff, and other hole positions unchanged. Zero extra-material setting retains its established behavior; the selective construction applies when extra material is requested. The staged receiving-plate nut rim remains unchanged.
- Syntax and standalone support-selection tests passed; full native FreeCAD CAD/export validation requires user testing.

## v0.92.32 — Staged arm-bolt / press-nut reinforcement

- Corrected the receiving plate reinforcement: extra arm-bolt material is no longer added *on top of* the press-nut or recessed-nut bearing allowance.
- Grow the arm-bolt stock first. Keep the existing nut-seat support envelope unchanged until the growing arm-bolt pad meets it; expand the shared perimeter only after that point.
- Apply to MidPlate in three-plate frames and the applicable BottomPlate / ArmClampPlate in two-plate designs.
- Keep all arm bolts, nut seats, bores, holes, plate-contact roles and existing TPU geometry unchanged. No new preset parameters; older saved settings load as before.
- Verified the staging calculations with True-X and Deadcat presets and arm-nut retention modes. Full native FreeCAD 3D generation remains unverified.

## v0.92.31 — Arm bolt mounting-stock allowance

- Added Arms > Bolts > Extra material around arm bolts (0–6 mm; 0 retains the existing geometry).
- Increase the local arm-root stock and receiving-plate pad support around the arm bolts, including press-nut flange bearing areas when selected.
- Extensions use the existing rounded mounting-stock and blend system rather than shifting mounting positions. Mid-plate, bottom plate, and clamp plate receive support in their existing applicable layouts.
- Preserved TPU camera geometry, motor protectors, hardware centres, and older preset defaults.
- Native FreeCAD solid generation remains to be tested before machining.

## v0.92.30 — Motor protector arm-tip side coverage

- Motor protectors now follow the complete motor-pad and arm-tip bumper outline even when the optional top sleeve is disabled.
- The Cover arm tip bumper setting controls top coverage only; lateral walls and bottom protection remain around the full tip.
- Clarified the setting description. TPU camera cage and camera isolation geometry are unchanged.

## v0.92.29 — TPU captured-interface seat construction (test build)

- Use the rounded-rectangle-style prismatic-layer construction for every TPU captured interface, rather than a ruled loft that tapers retaining-flange material into the cage wall.
- Preserve the nominal full-depth aperture dimensions; the printed neck alone shrinks according to the per-side fit-clearance control.
- Keep the working v0.92.28 cage, camera hardware, hard mount, compression pads, and carbon camera geometry unchanged.
- Requires FreeCAD rebuild tests for non-rectangular shapes and retention.

## v0.92.28 — TPU mounting hardware and interface geometry

- Include the eight M3 top/bottom TPU cage fasteners in optional hardware references, aligned to the existing carbon clearance holes and heat-insert pockets.
- Create non-rectangular TPU interface cutouts and matching removable parts directly in the YZ plane, with shared polygon geometry and specific failure diagnostics.
- Keep the rounded-rectangle path, carbon camera cage, and structural TPU cage solids unchanged.

## v0.92.27
- Replace the unreliable TPU-only Side plate outline interface with selectable Chamfered rectangle, Hexagon, Octagon, Tapered rectangle, and Capsule alongside Rounded rectangle. The cutout, insert and editor preview share the same outline generator.
- Restrict the TPU and carbon-fibre camera interface menus to their supported shapes independently. Saved TPU presets using the retired Side plate outline migrate to Chamfered rectangle; carbon side-plate options stay unchanged.
- Preserve the v0.92.26 TPU cage and captured-insert fit construction.

## v0.92.26 — TPU captured insert fit and retention

- Expose insert-to-cutout clearance from 0 to 0.25 mm, with a matching pocket/insert size calculation instead of double-counting the fit.
- Align outside retaining flanges against the cage wall faces, preventing the previous axial offset.
- Use a unified TPU-derived contact silhouette for the Side plate outline option in 3D and 2D preview; carbon plate profiles are unchanged.
- Preserve the v0.92.24 cage body and lower bridge.

## v0.92.24

- Correct TPU lower bridge junctions: corner blend no longer grows exposed rearward tongues beyond the side-wall termination.
- Blend the raised front edge into the established side-wall front surfaces over a smooth transition, avoiding sharp pointwise clipping peaks.
- Keep the plate-traced bottom contact, straight Hard-mount inner walls, and existing camera-isolation construction unchanged.
- Add regression checks for the lower bridge corner limits and package metadata.

## v0.92.23

- Limit the lower TPU front bridge to the inner opening plus a controlled 0.8 mm overlap into each side wall; stop extending a separate bridge skin across the entire outer cheeks.
- Restore smooth front and rear bridge edges instead of hundreds of visible short line segments, with a bounded fallback for problematic curves.
- Constrain the raised bridge front only at the embedded wall contacts, removing the abrupt mid-front clipping that produced exposed triangular lips.
- Preserve independently adjustable bridge height, rear reach and corner blend, the straight Hard mount inner walls, M2/M3 mount positions, and existing soft isolation modes.
- Native FreeCAD solid and surface validation remain pending.

## v0.92.22

- Prevent lower-bridge front and rear spline interpolation from overshooting into sharp peaks at the side walls.
- Smooth the clipped raised bridge front boundary into the cheek contacts without moving the plate-derived bottom outline.
- Preserve straight Hard mount inner walls, selected lower-bridge reach/height/blend, M2/M3 mounting locations, and the separate Compression pads and Captured inserts geometry.
- Maintain the proven single-piece TPU shell; native FreeCAD solid rebuild still requires verification.

## v0.92.21

- Keep Hard mount inner walls straight while following the actual finished top and bottom plate nose contours at their respective contact surfaces.
- Clip the raised lower-front bridge at the side-wall front contour so its corners cannot protrude past the supporting wall.
- Add an adjustable lower bridge corner blend (0–10 mm) to soften the rearward transition into the side cheeks without shifting the outer cage or M3 mounting positions.
- Update the lightweight lower-bridge footprint preview and retain the working Compression pads and Captured inserts geometry.
- Preserve the upper-centre opening and the plate-following exterior. Native FreeCAD solid generation requires testing.

## v0.92.20
- Replace the Hard mount's height-dependent inner-wall easing and 11-station loft with a single straight camera-facing inner wall from bottom contact to top contact.
- Generate one ruled span between the actual bottom and top plate front contours; remove interpolation bands and uncontrolled upper/lower bulges while retaining the outer X boundary and straight rear edges.
- Keep M2 camera screw passages, M3 heat-insert holes, Compression pads, Captured inserts and carbon-style camera plates unchanged.
- Enforce minimum wall thickness and single valid solid; native FreeCAD verification still required.

## v0.92.19
- Refined TPU hard-mount side-wall surfaces with a constrained smooth loft rather than 29 visible ruled panels.
- Retained existing camera-facing positions, carbon-plate outline contacts, M2 camera holes and M3 heat-insert locations.
- Added a bounded geometry check and a lower-resolution ruled fallback if the smooth loft is invalid.
- Left Compression pads, Captured inserts and carbon side-plate construction unchanged.

## v0.92.18
- Changed only the TPU Hard mount inner-wall loft to a station-sampled ruled loft, preventing interpolation overshoot that produced hourglass bulges and distorted side walls.
- Preserved plate-contact geometry, straight rear termination, screw pockets, and both soft camera isolation constructions.
- Native FreeCAD OCC geometry validation remains outstanding.

## v0.92.17
- Shorten the TPU Hard mount inner-wall transition to preserve a straight camera-contact section and reduce hourglass pinching.
- Constrain the loft with more closely spaced transition sections; keep plate-following outer geometry and mounting locations unchanged.
- Leave Compression pads, Captured inserts, and carbon camera plates untouched.
- Native FreeCAD geometry and collision checks still require testing.

## v0.92.16

- Fixed hard-mount TPU side-wall contour sampling so camera-facing wall movement no longer changes the plate-derived front silhouette.
- Extended and smoothed the inner-wall transitions to avoid pronounced hourglass-like bulges.
- Preserved fixed plate-contact profiles, M3 mounting positions, existing camera screw passages, and separate compression/captured-insert construction.
- Source-level regression checks only; native FreeCAD geometry remains unverified.

## v0.92.15

- Validate OpenCASCADE camera intersections against both operand bounding boxes before rejecting TPU hard mounts.
- Cross-check the original left/right cage walls and lower bridge separately; impossible intersections are warned about rather than reported as physical collisions.
- Preserve real camera collision rejection and existing isolation geometry.

## v0.92.14 — Correct mirrored TPU hard-mount inner-wall coordinates
- Fix the X-sign error that moved both full-height hard-mount inner walls into the physical camera housing; interpolate from the original plate-contact edge to the correct signed camera-face clearance.
- Preserve the unchanged outside plate-following contours, lower bridge, M3 mounting positions, camera screw openings, compression pads and captured inserts.
- Maintain the real camera-vs-cage collision checks; no intersection is silently ignored.
- Portable geometry/parameter checks passed; native FreeCAD solid generation remains unverified.

## v0.92.13 — Continuous hard-mount camera-facing cage walls
- Replace the isolated cylindrical TPU hard-mount bearing protrusions with one continuous, lofted camera-facing wall on each side.
- Preserve both external carbon-plate-following edges and full-size M3 socket landings at top and bottom; move only the internal wall surface toward the camera between those contacts.
- Match the complete M2 camera-screw opening depth to the newly positioned inner wall, rather than hiding the hole behind a separately fused bearing cylinder.
- Leave the compression-pad and captured-insert construction unchanged.
- Correct TPU width prevalidation to use the selected camera clearance; this is a source-level experimental change and has not undergone native FreeCAD shape testing.

## v0.92.12 — Stable TPU hard-mount structural shell
- Keep the outer TPU cage and full-height side-wall profile identical across all camera isolation modes; switching to Hard mount no longer expands the entire structural wall towards the camera.
- Create short, integrated, mirrored M2-bearing lands at the actual camera screw positions for Hard mount. The chosen camera-side clearance controls their contact position without changing M3 carbon-plate mounts, plate-following outside surfaces, or the lower front bridge.
- Require each new bearing to fuse into exactly one valid wall solid. Preserve the existing camera-screw hole cuts and independent compression-pad and captured-insert construction.
- Leave carbon-fibre camera plates and all non-camera workbench geometry unchanged.
- FreeCAD native geometry execution is still required to verify the result before manufacturing.

## v0.92.11 — TPU camera clearance validation routing

- Fix the duplicated variable-tilt collision check that rejected a TPU cage at an unselected angle (for example 0 degrees with a 25-degree selected camera tilt).
- Route all camera-versus-TPU-cage checks through the existing dedicated cage validator, which checks the currently selected angle and warns about other inaccessible tilt angles.
- Retain normal camera collision checks against carbon plates, standoffs and other physical parts, and retain the carbon side-plate collision validation unchanged.
- No changes to TPU cage solids, captured inserts, compression pads, mounting holes, editor views or saved parameter formats.
- Native FreeCAD end-to-end build remains to be verified.

## v0.92.10 — TPU camera collision cross-check

- Validate the final TPU cage camera collision against the three original uncropped structural components (left/right side walls and lower bridge).
- Prevent an inconsistent OCC Boolean intersection of a cut/refined final cage from falsely rejecting a frame when none of the original components overlaps the camera.
- Keep actual component overlap blocking and report which component causes it; preserve existing carbon cage, fasteners, tilt, and preview handling.
- FreeCAD native rebuild still required to verify behavior on the reported design.

## v0.92.9 — TPU collision-range and part-preview corrections

- Validate actual housing-to-cage interference at the currently selected camera tilt as a build-blocking error; report collisions at other variable-tilt positions as explicit Report view warnings rather than blocking a safe selected position. The reported alternate angles are not safe to use without modification.
- Separate TPU cage wall and captured-insert inspection: cage views show only the receiving through-cutout, pad views show only the removable insert. Neither preview overlays the other part.
- Preserve the working v0.92.7 captured-insert solids, outer plate-following cage, carbon camera cage, M3 mounting and camera-isolation geometry unchanged.

## v0.92.8 — TPU captured-insert inspection preview

- Show the full-depth captured-insert receiving opening in the TPU camera cage side elevation, using the same Y/Z camera screw datum, insert dimensions and fit allowance as the native CAD cutter.
- Show the removable captured insert alongside its corresponding opening in one composite inspection view, including the left and right cage views and the camera pad views.
- Preserve the currently working v0.92.7 solid construction, plate-following outer cage, carbon plate cage, M3 mounting, hard mount and compression-pad geometry. The side-plate interface remains a compact removable insert profile rather than replacing the entire structural wall.
- Correct left/right camera-pad preview mount lookup; the native FreeCAD GUI must still verify the rendered preview.

## v0.92.7 — Full-depth TPU captured-insert seats

- Replace the former blind TPU cage insert recess with a matching full-thickness opening, so the insert occupies the wall rather than stopping behind a solid skin.
- Use the same camera-screw datum and YZ profile for the receiving opening and removable insert; retain the existing camera screw/tilt cuts.
- Give the soft insert a through-wall neck, with the optional retaining faces outside the load-bearing wall instead of buried in it.
- Preserve the plate-following exterior, M3 plate fasteners, the independent carbon side-plate system and compression-pad behavior.
- Native FreeCAD solid rebuilding and print-fit still require verification.

## v0.92.6 — TPU heat-insert boss micro-overlap correction

- Handle tiny near-tangent outer boss slivers without a fragile OpenCASCADE fuse, but **only** after verifying the existing cage wall already contains a continuous 1.2 mm supporting envelope around the insert pocket.
- Retain strict fusion and rejection for any socket that lacks the required material; never discard a functional mounting feature to force a build.
- Preserve all M3 coordinates, insert-pocket dimensions, plate-following contours, camera interfaces, carbon camera cages, and isolation modes.
- This is a targeted correction to the v0.92.5 hard-mount Boolean failure; native FreeCAD rebuild is not verified.

## v0.92.5 — TPU-only camera interface profile consistency and adjustable hard-mount clearance

- Use the same explicit chamfered TPU interface polygon for the captured insert and its matching cage recess; avoid the mismatched rounded/straight contours that could invalidate the removable part.
- Prefer a single-solid axial loft for the TPU Side plate outline captured insert; retain separate diagnostics for invalid insert geometry and screw/tilt openings.
- Add a user-adjustable Hard-mount side clearance in Camera cage > TPU attachment (default 0.15 mm per side, 0.05–3 mm), without moving the plate-following exterior or M3 plate mounting positions.
- Keep the carbon-fibre camera side-plate isolation generator unchanged. Native FreeCAD/OpenCASCADE solid validation is still required.

## v0.92.4 — TPU captured-insert single-solid construction

- Build the TPU-only side-plate-outline isolator profile from its target dimensions rather than OCC face offsets, preventing collapsed or self-intersecting offset contours.
- Retry a failed captured-insert layer fusion as one continuous, eight-section-profile ruled loft.
- Validate the removable isolator before and after each individual camera screw/tilt cut, with a specific failure message.
- Leave carbon camera plates, carbon camera isolation, external TPU cage and M3 plate mounting unchanged.

## v0.92.3 — Separate TPU insert interface and seat clearance

- TPU cage *Side plate outline* is now a convex, centred TPU-specific profile, not derived from the carbon side plate or the top/bottom reach.
- Its preview, removable isolator, and matching blind wall pocket use the same profile generator.
- Captured insert camera-facing flange is relieved from the cage wall; the narrow insert neck alone enters its dedicated pocket.
- Added small internal retaining-pocket clearance to avoid coincident OpenCASCADE surfaces.
- Preserved the existing carbon-fibre camera cage, M3 plate holes, plate-following exterior and compression pads.

## v0.92.2 — TPU isolation and raised bridge corrections

- Separate hard-mount wall clearance from the soft-camera interface so no pad-sized gap is reserved for hard mounting.
- Use a TPU-specific side-outline profile for removable camera isolators instead of the carbon-plate silhouette.
- Match the centre floor front at the actual raised height to the cage-wall loft to reduce raised-floor lips.
- Seat captured inserts with matched blind neck and retaining-chamber geometry, avoiding over-penetrating contact layers.
- Preserve independent M3 carbon mounting coordinates and unchanged carbon side-plate isolation construction.

## v0.92.1 — TPU camera isolator screw-datum alignment

- TPU-only pads and captured inserts now use compact rounded-rectangle geometry, never a scaled carbon camera side-plate polygon.
- Centre a removable TPU isolator on the camera screw/tilt travel envelope, not the structural cage profile or a possibly different pivot datum.
- Keep the blind insert retention pocket aligned with its matching movable insert, while leaving the cage exterior and M3 carbon mounting positions untouched.
- Reject undersized pads/inserts before cutting a screw slot through their edge; report the minimum needed dimensions.
- Match the editor preview to this TPU-only isolation positioning.
- Carbon/aluminium-cut side plate isolation geometry is unchanged. Native FreeCAD CAD rebuild is not verified.

## v0.92.0 — Align lower TPU bridge with side-wall front surface and preview

- Remove the lower bridge's upper-rim nose setback and rear Y offset, which generated visible wavy overlap seams when intersecting the plate-following side walls.
- Build the bridge as an extrusion of its finished bottom-plate contour and user-defined straight rear edge. This simplifies the operation while preserving the adjustable bridge height.
- Make the editor's lower bridge preview use the same straight rear edge and outline sampling as the 3D builder, rather than an unrelated curved blended rear edge.
- Label TPU part inspection as a side elevation rather than a flat cut part. Carbon side plates are unchanged.
- Native FreeCAD solid generation and captured-insert construction remain unverified. This is a geometry/preview consistency test build, not a verified cure for those other problems.

## v0.91.99 — Correct TPU camera clearance validation across cage height

- Remove the false 2D interference test that treated top/bottom M3 mounting sockets as though they occupied the camera's entire height. This was responsible for the misleading 11.60 mm required versus 9.20 mm available warning on the True-X design.
- Keep M3 hole X/Y coordinates fixed by the carbon mounting geometry, and retain the minimum 2 mm carbon around each drilled hole.
- Check whether the camera's required half-clearance fits within the plate-derived outer cage face with a continuous minimum 1.2 mm TPU wall. Do not use the mounting socket's inner X edge as a global limit.
- Keep the native per-socket pocket validity and exact 3D camera-to-cage collision checks active. This does not bypass real overlaps or alter the camera side walls or plate outlines.
- Carbon side-plate cage geometry and other frame components are unchanged.

Python regression and syntax tests were performed; full native FreeCAD geometry generation is still unverified.

## v0.91.98 — Separate TPU outline, carbon mounting datums and camera clearance

- Derive the TPU cage M3 X datum from the carbon plate widths and mounting socket size, not from the camera width, selected isolation mode, camera side clearance or existing side-plate geometry.
- Determine front/rear mounting holes as a supported PAIR on each plate with 2 mm of carbon outside the drill opening, keeping mounting positions independent of TPU cage reach.
- Keep the outer TPU wall at a fixed plate-derived lateral boundary. Camera width and side clearance now adjust the camera-facing wall surface only. Do not expand the outer wall to accommodate sockets during geometry construction.
- Preserve the selected straight rear contact edge instead of generating a curved rear reinforcement around the M3 insert bosses. Reject settings that cannot contain a boss within the selected contact reach.
- Report dimensional conflicts when the camera plus isolation envelope cannot fit between fixed plate boundaries and the heat-insert sockets, rather than silently moving the mounts or carving structural walls.
- Check actual finished bottom/top carbon outlines at the four M3 holes during native construction; reject less than 2 mm of remaining carbon at the outside edge.
- Retain the existing standalone TPU isolation cutters and carbon-fibre side-plate geometry generator; their 3D behavior still requires native FreeCAD verification.

Portable regression checks run using supplied True-X and Deadcat presets: consistent M3 datums across Hard mount, Compression pads and Captured inserts; unchanged mounting coordinates when changing camera width/clearance; 2 mm nominal carbon edge support. The narrower Deadcat camera + insert case correctly reports insufficient width rather than shifting the outer cage. No native FreeCAD CAD-kernel execution was available; this is an experimental build, not a verified manufacturing release.

## v0.91.97 — TPU mounting boss spacing and saved-offset diagnostics

- Ensure automatically placed front/rear TPU mounting holes have clearance for their full heat-set insert bosses, not only the M3 drill diameters.
- Explicitly flag overlapping bosses and suggest resetting legacy mounting offsets when applicable.
- Keep carbon mounting coordinates stable across camera isolation modes.
- Carbon camera side-plate geometry and mounting rules are unchanged.

## v0.91.96 — Separate TPU camera isolation and inner-wall clearance

- Make the TPU cage's camera-facing wall respect the complete camera/soft-interface clearance envelope. M3 socket footprint calculations can no longer widen the inner edge inward toward the camera.
- Keep the same TPU side-wall and plate M3 mount coordinates for Hard mount, Compression pads and Captured inserts; leave the carbon side-plate generator untouched.
- Add independent TPU-only compression-pad and captured-insert geometry using the actual expanded cage-wall bounds. Compression pads bear against the inside of the wall without structural through-cutouts. Captured inserts fit blind pockets with the selected retaining lip.
- Handle DJI O4 dual screw-track isolation separately within the TPU geometry path.
- Remove a final captured-insert support check that was written for carbon side plates and incorrectly applied to TPU blind-pockets.
- Allow Camera side clearance to be adjusted in the editor for TPU cage with any isolation mode.
- Update interface help text to distinguish carbon and TPU isolation methods.

Portable syntax checks and both user-supplied True-X/Deadcat preset coordinate checks passed, including consistent mounting positions across all modes. Native FreeCAD solid and GUI tests have not been run; verify print geometry and carbon mounting hole support before manufacturing.

## v0.91.95 — TPU camera-to-wall clearance correction

- Corrected the unified TPU cage's inner wall position to preserve actual camera and isolation clearance; mounting socket footprint adjustments can no longer push its inner face toward the camera.
- Sized the structural cage for the configured pad allowance regardless of selected isolation mode, maintaining fixed cage and M3 mounting positions when switching Hard mount, Compression pads, and Captured inserts.
- Positioned M3 heat-insert bosses outside the clear camera envelope while retaining their pocket diameters and depths; the matching plate holes follow the same positions.
- Added exact 3D camera/cage intersection bounds to FreeCAD Report view for remaining collisions, including possible lower-floor interference.
- No changes to the carbon side-plate cage builder or noncamera frame components.

Native FreeCAD/OpenCASCADE rebuild is not available in the portable test environment. Verify mounting-hole carbon support and camera clearance in FreeCAD before manufacturing.

## v0.91.94 — TPU camera clearance and isolation stability

- Keep the unified cage wall positions fixed when changing between Hard mount, Compression pads, and Captured inserts; the carbon M3 mounting pattern remains unchanged.
- Check soft-isolation clearance before generating the CAD loft.
- Report actual camera-to-cage interference instead of subtracting the camera housing from structural TPU walls and creating unexpected recesses.

## v0.91.93 — TPU cage contour definition (test build)
- Generate front edges of the unified TPU cage directly from the finished bottom and top plate outlines.
- Make upper and lower cage side-wall rear cuts straight in top view, instead of offsetting the curved front outline backward.
- Make the one-piece lower bridge rear edge straight and preserve its adjustable rear reach and height; keep the upper middle open.
- Keep M3 heat-set socket positions, camera isolation, plate shapes, and the carbon side-plate builder unchanged.
- Native FreeCAD BRep validation is still required.

## v0.91.92 — TPU socket footprint integrated into cage side walls (test build)

- Expand the *X faces* of the unified TPU cage wall when necessary to fully enclose the actual M3 heat-insert socket, before loft creation. Only the necessary socket footprint is added; camera-envelope checks remain active.
- Keep carbon-plate M3 mounting coordinates, hole diameters, camera-isolation settings and camera-side spacing unchanged.
- Aim to eliminate the small exposed socket sliver that previously required an unreliable OpenCASCADE union. Existing individual cut and validation diagnostics remain in place; an unsatisfied socket still fails visibly.
- Leave the carbon/aluminium flat camera plates, main frame geometry, TPU protection and export paths unchanged.
- Portable syntax and socket-width regression checks passed. Native FreeCAD solid generation has not been verified.

## v0.91.91 — TPU cage isolated Boolean cutting and diagnostics (test build)

- Fix the confirmed null-result failure at the first cage-opening stage: do not subtract all M3 insert pockets and camera screw/tilt cutters as one compound from a curved loft.
- Cut valid, intersecting pockets and camera openings individually; validate the remaining solid after each operation.
- Only refine a successful cut if refinement still produces one valid solid.
- Report the precise side, cutter type, cutter number and remaining solid count when a cut fails. Never skip required holes or accept fragmented cages.
- Keep TPU contour construction, camera-isolation selections, carbon camera plates, mounting coordinates and all non-camera frame generators unchanged.
- Native FreeCAD/OpenCASCADE execution remains outstanding; this is a test build.

## v0.91.90 — TPU cage redundant boss union correction (test build)

- Avoid attempting an OCC Boolean union when the loft already fully encloses the M3 mounting socket; the insert pocket is still cut normally.
- Keep mounting bosses within the top/bottom cage contact planes rather than extending a small fraction outside the plate-contact face.
- Retry required unions using different operand order, while rejecting invalid or disconnected solids.
- Distinguish already-supported bosses from partially exposed bosses in diagnostics. No sockets or mounting holes are removed to make a build pass.
- Carbon side-plate and other frame geometry generators remain unchanged. Native FreeCAD rebuild verification is outstanding.

## v0.91.89 — TPU cage boss overlap diagnostics (test build)

- Provide a small intentional overlap at each structural M3 socket while preserving its original hole centre and heat-insert pocket.
- Distinguish tangent/no-volume contact from a genuine OCC fusion failure.
- Check bosses against the finished front plate outline before attempting the costly Boolean.
- Keep the carbon camera cage path untouched.
- Native FreeCAD solid-generation verification is required.

## v0.91.88 — TPU cage integrated mounting sockets (experimental)

- Generate structural wall material around the existing four M3 heat-insert sockets during the wall loft, before Boolean operations.
- Retain plate-following front contacts, original screw coordinates, independent rear reaches and the three camera isolation choices.
- Remove the fragile small-cylinder bridging fallback that could fail with a disconnected boss.
- Limit extra rearward socket support to the immediate upper/lower plate contacts, tapering it back over 2 mm.
- Report explicit unsupported-hole errors rather than silently moving mounting holes.
- This update requires native FreeCAD solid and visual verification.

## 0.91.87 — TPU cage mounting boss connectivity

- Fuse M3 heat-insert bosses individually to the unified TPU cage wall.
- Add a bounded local rounded connector only when a boss falls outside the wall and cannot fuse directly.
- Keep plate mounting coordinates, camera isolation dimensions and the carbon camera cage unchanged.
- Provide boss-specific diagnostics when the attachment is too far from the wall.

## 0.91.86 — TPU camera isolation structural separation
- Prevent switching between Hard mount, Compression pads and Captured inserts from changing the TPU cage perimeter, rear contour or M3 hole coordinates. The camera-facing X spacing can still accommodate soft materials.
- Keep the legacy soft-isolation camera-sweep hull calculation for flat camera side plates only; the unified TPU cage continues using its own top/bottom plate-outline loft.
- Draw a consistent exterior TPU cage elevation with camera screw/tilt access. Soft-interface pockets are internal, not giant through-windows in the preview.
- On the TPU cage, compression pads seat against the inner wall without cutting it away. Captured inserts get a blind neck pocket with an optional internal retaining-lip chamber, plus separate camera screw/tilt openings. Carbon camera plates retain their previous through-insert logic.
- Verify portable mounting coordinates, TPU side-wall profiles and validation for all three isolation modes using True-X and Deadcat JSON presets. Native FreeCAD CAD Boolean and GUI rendering tests remain outstanding.

## 0.91.85 — Unified flat camera side-plate construction
- Remove Aluminium cage as a separate editor choice: use Carbon side plates for either carbon fibre or aluminium machining with the same flat geometry and export profiles.
- Import legacy Aluminium cage presets as Carbon side plates after transferring their saved dimensions; preserve all camera and plate parameters.
- Remove the redundant aluminium-material tab, dedicated exporter route and stale selector hints. TPU cage construction is unchanged.
- Check True-X and Deadcat preset loading and geometry dispatch through portable regression tests. Native FreeCAD geometry rebuild is not verified.

## 0.91.84 — TPU cage plate-anchored screw positions

- Locate TPU cage M3 mounting holes independently on the finished top and bottom carbon plates, with editable offsets relative to supported positions.
- Keep screw positions fixed when TPU cage top or bottom rear reach changes.
- Validate M3 edge clearance using actual shaped plate geometry rather than obsolete camera side-plate endpoints.
- Remove screw-boss-driven rear fin deformation; rear wall follows user-selected top and bottom reaches.
- Remove the obsolete 0.35 mm front projection from the lightweight cage preview.

## 0.91.83 — TPU camera cage side-view Qt polygon compatibility

- Fix the blank camera-mount inspection preview caused by slicing `QPolygonF` when extracting top/bottom plate perimeter polygons. Convert polygon vertices to native lists first and select the largest closed perimeter by area.
- Handle unavailable plate outlines with an explicit preview message instead of an unrelated Python indexing exception.
- Apply to all TPU camera isolation choices (hard mount, compression pads and captured inserts); the underlying 3D cage and isolation dimensions are unchanged.
- This fixes the editor rendering exception, not any separate CAD Boolean failures, which still need native FreeCAD testing.

## 0.91.82 — TPU camera isolation preview and mount checks

- Render TPU cage compression-pad and captured-insert openings in the correct camera Y/Z elevation without reusing the old bracket-outline preview. An invalid preview now reports its own error without blanking the entire canvas.
- For screw-mounted TPU cages, check the actual lower mounting screw positions against bottom-plate support rather than the retired tabbed side-plate corners.
- Remove obsolete side-plate/stack overlap and side-bracket material warnings from TPU cages. Native CAD solid, screw, camera-sweep and isolation checks remain in force.
- Preserve existing hard-mount, compression-pad and captured-insert selections and dimensions; no automatic changes to saved settings.

## 0.91.81 — TPU cage isolation and editor preview correction

- Limit captured-insert and compression-pad recess cutters to their own left/right TPU cage cheek instead of cutting across the entire connected cage.
- Replace the editor's old camera-bracket silhouette with a plate-contour-based TPU cheek elevation for TPU cage mode.
- Use the camera isolation settings when drawing the TPU cage opening in the editor.
- Avoid rejecting TPU isolation choices based on the obsolete carbon side-plate wall profile; final CAD solid validation remains required.
- Keep M3 plate screws, threaded inserts and independent upper/lower contact reaches unchanged.

## 0.91.80 — TPU cage plate-contact and surface transitions

- Increase cage wall cross-sections to follow both finished plate front contours more accurately between the original three sampling locations.
- Restrict the extra rearward wall reach needed by the heat-set insert bosses to their immediate plate mounting zones, avoiding the previous broad rearward swoop.
- Replace the extruded lower centre connection with a shallow tapered loft. Its lower contact follows the finished bottom plate, while its upper front rim transitions inward to prevent projecting front corner lips.
- Retain the unified cage, adjustable lower and upper attachment reaches, M3 mounting and camera isolation choices.
- Requires visual and solid-validity testing in native FreeCAD with the user's True-X project; static tests do not validate OpenCASCADE loft operations.

## 0.91.79 — TPU cage side profile and isolation seating correction

- Removed the lower bridge's forward edge overhang, which created small lips at the cage corners.
- Limited the hardware-boss rear extension to smooth local transitions near the mounting faces instead of pulling the whole side wall rearward.
- Added dedicated compression-pad clearance using the configured pad dimensions, separate from the hard-mount holes and captured-insert window.
- Preserved separate bottom/top carbon outline sampling, M3 insert pockets and unified lower bridge.
- Native FreeCAD rendering and connectivity of soft-isolation cutouts still require testing.

## 0.91.78 — TPU cage Boolean-stage diagnostics and contact handling

- Separate heat-insert/camera screw openings, tilt-clearance cuts and carbon contact operations; identify the exact stage that disconnects the cage.
- Skip unnecessary solid Boolean cuts when the camera envelope or carbon plate has no volume overlap with the TPU cage.
- Preserve zero-volume top/bottom carbon contact faces without Boolean subtraction, reducing tolerance-sensitive BRep fragmentation.
- Report solid counts and volumes in FreeCAD Report view, with specific error messages for camera tilt or plate-contact failures.
- No TPU cage dimensional or styling changes. FreeCAD runtime validation remains necessary.

## 0.91.77 — TPU cage performance diagnostics and outline sampling
- Cache plate-edge discretization once per rebuild instead of running dozens of full BRep section intersections.
- Reduce redundant loft and floor sampling while retaining smooth curved plate contacts.
- Add elapsed-time checkpoints to the FreeCAD report log to identify remaining slow Boolean operations.
- Preserve the unified cage and existing mounting/isolation geometry.

## 0.91.76 — Unified plate-following TPU camera cage (experimental)

- One cage style only: continuous lower TPU floor and independent upper side walls (no upper crossbar).
- Independent top and bottom contact rear-reach settings, plus adjustable centre-floor reach and height.
- Plate-outline following at each carbon contact; smooth spline wall and floor contours.
- Existing M3 carbon clearance holes and blind metal heat-set insert pockets remain.
- Hard mount, compression pads and captured insert camera mounting remain selectable.
- Remove obsolete split/one-piece chooser and redundant bumper controls from editor.
- Older saved designs migrate to the one-piece construction.
- Native FreeCAD solid generation still requires testing; do not manufacture unchecked geometry.

## 0.91.75 — TPU cage lower-bridge continuity

- Anchor the one-piece TPU cage lower bridge inside both generated side walls, not merely against the plate front line.
- Blend the bridge's rear outline smoothly from each supporting side wall to the independently adjustable central rear reach.
- Increase controlled side-wall overlap to avoid disconnected solids in saved designs with extended camera mounting tabs.
- Preserve the single plate-outline cage construction, camera isolation settings, and separate-side open bottom.

**CAD verification:** Geometry must still be rebuilt and visually checked in native FreeCAD.

## 0.91.74 — Rebuilt TPU camera cage as a single plate-outline design

- Replaced the former bracket-plus-perimeter shell assembly with a dedicated TPU camera cage builder. The old camera bracket and previous full-board outline shell are no longer combined for TPU cages.
- Shape each camera side directly from smooth lofted sections using the finished bottom-plate front edge and top-plate front edge, sampled across its physical width.
- Keep the central opening above the camera and only construct an adjustable lower connection for one-piece cages. Its forward edge follows the bottom-plate profile.
- Preserve existing heat-set mounting pockets, camera adjustment openings, captured isolation inserts, and the optional lower bridge reach/height controls.
- Fail explicitly if the resulting cage is disconnected rather than silently deleting printable walls or falling back to the previous block geometry.
- This is an unverified native-FreeCAD test build; detailed CAD operation and rendering tests still required.

## 0.91.73 — True-X saved-design TPU cage recovery

- Diagnosed the user-provided three-plate True-X FCStd design: its saved CameraMountLeft is a valid single solid, but newer full-perimeter cage generation fragments after its opening and collision cuts.
- Add a bounded recovery path for one-piece TPU cages that rebuilds the outer cage front locally from each plate contact, anchored by overlapping the original mounting cheeks. This avoids creating or keeping disconnected fragments from the full-frame annular shell.
- Preserve the existing camera mount and mounting slots, one-piece lower bridge controls, and camera motion clearance; reject fallback solids if they are disconnected or invalid.
- Native FreeCAD rebuild not available in this environment. Test with the supplied saved FCStd and verify cage silhouette before manufacturing.

## 0.91.72 — TPU cage disconnected shell fragments

- Discard small, disconnected fragments produced when the plate-outline loft is intersected with the camera aperture and collision envelope. Preserve substantial left/right cage walls and the one-piece lower bridge.
- Protect the original camera mounting solids when filtering fragments after screw/clearance cuts.
- Increase the maximum number of bounded, local solid-joining attempts so multi-piece saved profiles are not left half-repaired by an eight-iteration limit.
- Retain the existing adjustable lower-connection controls, isolation geometry, screw passages and plate outlines. This is a targeted test build: native FreeCAD Boolean verification and the user's saved design remain untested.

## 0.91.71 — TPU camera cage solid connectivity

- Repair small disconnected gaps between the plate-outline TPU cage wall and the original camera mounting cheek using localized solid TPU webs.
- Check the repair against carbon plates, camera movement envelopes, mounting screw bores and camera isolation openings; do not bridge across the camera's centre opening.
- Replace the generic CameraMountLeft solid-validation failure with a specific disconnected-cage diagnostic when a safe repair is impossible.
- Keep the plate-following upper/lower contours and adjustable one-piece lower connection unchanged.
- No native FreeCAD CAD-kernel validation was available; test the saved design before manufacturing.

## 0.91.70 — Saved design rebuild compatibility

- Made cage perimeter resampling resilient to complex plate outline edge topology from existing saved designs.
- Added a simpler matched-section loft fallback when the smoothed TPU cage shell cannot form a valid solid.
- Added a lower-connection geometry fallback when the curved loft fails on a valid older frame outline.
- Made the new lower-connection controls initialize with safe defaults when loading older settings.
- Retained one-piece/separate-side options, upper/lower plate-outline contacts, mounting openings, and camera isolation settings.

## 0.91.69 — Adjustable one-piece TPU cage lower connection

- Added **Lower connection rear reach** and **Lower connection height** to Camera cage → TPU attachment. Both controls are enabled only for a one-piece TPU cage.
- Rebuilt the lower connection with a smooth swept rear edge and lofted slope instead of a fixed-depth straight extrusion.
- Trimmed the bridge to the actual plate-derived cage exterior to remove small forward lips at the side junctions.
- Retained the existing plate outlines, camera-isolation system, screw access, and separate-side open bottom.

## 0.91.68 — TPU camera cage profile controls and smoother contours

- Disable and hide the camera cage front/rear shape-profile controls when TPU cage construction is selected; restore them for carbon and aluminium cage types.
- Bypass the legacy front/rear profile shaping in TPU camera mounting geometry, so the TPU shape is controlled by the finished top and bottom carbon plate outlines.
- Use evenly spaced arc-length samples and closed B-spline perimeter wires for smoother cage loft surfaces; increase vertical stations for smoother transitions.
- Preserve open camera centre, one-piece-only short lower bridge, side screw accessibility and camera isolation settings.
- Native FreeCAD/OpenCASCADE geometry validation is still required.

## 0.91.67 — TPU camera cage opening and accessible camera mounts

- Remove the full-width upper/lower cage contact bands that filled the camera aperture.
- Preserve an open centre above the camera; create a lower cross-bridge only for one-piece construction, limited to the frontmost 6 mm of the finished bottom-plate footprint.
- Separate-side cages have no centre cross-bridge.
- Extend the existing camera screw/arc and captured-insert openings out through the perimeter shell to restore mounting access; retain the original mounting bosses and TPU isolation options.
- Preserve upper and lower outer contours independently from the finished plates; no carbon-plate cutouts.
- Native FreeCAD loft/Boolean and assembly checks are still required.

## 0.91.66 — TPU cage plate-to-plate outline profiles

- Construct lower and upper TPU cage perimeter profiles independently from the finished bottom and top plate outlines.
- Loft between those contours; front extension is limited to the intermediate height.
- Generate plate-following perimeter regardless of the front-bumper toggle.
- Preserve existing camera mounting bosses and isolation pathways.
- This build requires native FreeCAD loft and Boolean testing.

## v0.91.66 — TPU camera cage perimeter reconstruction
- Rebuild the optional TPU front cage as physical perimeter geometry taken from the finished bottom plate outer wire, not an adjusted flat cheek profile.
- Add side cheeks, front camera aperture and top/bottom connecting rails; support both one-piece and separate-side construction.
- Keep the existing camera mounting screws, M3 insert pockets, and TPU camera isolation modes; do not add duplicate isolation controls.
- Maintain the genuine plate-contact outline and do not cut carbon to make the cage fit.
- Update cage footprint preview to show the perimeter option on separate side constructions.
- Native FreeCAD solid and Boolean regression testing still required.

## v0.91.64 — TPU camera cage outline and isolation controls

- Clip the lower camera-cage contact against the **actual finished bottom-plate perimeter**, including shaped corners and nose features, instead of relying on a single sampled front-edge position. This affects the TPU part only; no carbon cutouts are generated.
- Preserve the cage's forward protective profile **above** its plate contact; the mounting cheek's X span and the existing top/bottom heat-set insert bosses remain unchanged.
- Return **Hard mount**, **Compression pads**, and **Captured inserts** to **TPU → Camera isolation** as the single camera-isolation selection. The FPV camera-cage section retains its own cage construction, fixed/variable tilt and screw-position controls, not a duplicate isolation mode.
- This is a geometry/contact correction requiring native FreeCAD checks on the user's chosen plate shape and one-piece/separate TPU cage variants.

## v0.91.63 — TPU camera cage front and mounting support

- Incorporated the TPU cage's forward protection into a smoothly curved camera-side cheek profile, avoiding the old protruding rectangular bumper block.
- Preserved the bottom-carbon contact outline while allowing the cage nose to extend forward above the bottom plate; upper contact and left/right mounting positions remain unchanged.
- Allowed the front top and bottom TPU mounting screws to approach the front contact edge with 2 mm of material outside the M3 plate opening; separate carbon/aluminium tab requirements are retained.
- Preserved Hard mount, Compression pads, and Captured inserts as camera isolation choices for TPU cages. TPU screw and heat-set insert positions continue following the existing mounting controls.

## v0.91.62 — VTX mounting support and permitted body overhang

- Require the complete VTX mounting-hole pattern (including edge material) to remain supported by the rear carrier: mid plate for three-plate frames or bottom plate for two-plate frames.
- Permit the VTX housing to extend past the sides or rear of its carbon carrier rather than treating its entire body footprint as mandatory deck coverage.
- Remove the incorrect top-plate requirement to cover the VTX body; retain vertical overlap checks for the actual area beneath the top plate.
- Make automatic rear reach depend on the fixing pattern rather than the enclosure length, and clarify the VTX/side-guard editor guidance.
- Continue validating standoff interference and existing structural constraints, retaining exact side-guard collisions and adding exact VTX-versus-propeller interference checks.

## v0.91.61 — New-frame battery strap defaults

- Start the New frame editor with top-plate battery strap openings disabled.
- Retain user-selected slot dimensions and styles for later enabling.
- Edit frame and Load settings continue to respect the saved strap-slot state; existing frame geometry is unchanged.

## v0.91.60 — LiPo reference appearance

- Replace the orange detailed LiPo wrapper with a muted graphite-slate finish while preserving the recessed cell seams and 3S–8S individual cell layers.
- Match the simple 3D LiPo reference and the 2D plan preview to the updated battery colour.
- Keep dimensions, geometry, connector details, and existing help documentation unchanged.

## v0.91.59 — Stable LiPo cell seams

- Replace the continuous orange LiPo side-wrapper surfaces with cell-aligned 3D panels separated by shallow recessed seams.
- Reveal dark, physically recessed backing in each seam rather than relying on cell edges covered by the outer wrapper.
- Retain 3S–8S cell counts, user-editable pack dimensions, balance-connector detailing and existing frame-clearance behavior.
- Preserve cached detailed reference generation; no additional expensive Boolean cuts are necessary.

## v0.91.58 — LiPo cell-count input compatibility

- Accept valid whole-number battery series counts stored as floats (such as 6.0), including values from the Qt editor and saved configurations.
- Reject fractional, non-finite or out-of-range battery cell counts without silently rounding them.
- Preserve the editable 3S–8S battery presets and detailed cell-by-cell reference geometry.

## v0.91.57 — LiPo references

- Added nominal 3S–8S LiPo presets with editable width, length, height and mass.
- Editing pack measurements switches the selection to Custom dimensions without resetting the cell count.
- The detailed LiPo model now renders a separate pouch layer for each cell and a matching balance connector contact count.
- Existing saved designs retain their measurements and import as Custom dimensions.

## 0.91.56 — Editor and virtual camera performance; revised Help manual

- Avoid unnecessary rebuilding of the preview-mode selector on routine parameter refreshes; keep the selected view when available modes are unchanged.
- Reuse completed virtual camera ray projections for unchanged geometry, optical settings, tilt, and aspect, including when reviewing recording crop overlays.
- Update bundled Help PDF version labels and add instructions for current digital/analog camera selection, DJI O4 Pro fit checks, camera preview, and bumper handling.
- Keep carbon plates unchanged by O4 camera clearance routines. Existing physical collision detection remains enabled.

## v0.91.55 — Video-system camera selection filtering

- The physical camera dropdown now displays only analog models for Analog and only digital models for Digital; Custom measurements is available in both modes.
- Switching video systems preserves custom physical dimensions while resetting a previously selected incompatible camera profile to Custom measurements and refreshing the optical preview defaults.
- Loading presets filters the visible choices without firing camera-selection callbacks or changing the saved camera dimensions.
- Switching away from an O4 Pro equipment profile to Analog releases the dedicated digital equipment lock. Choosing O4 Pro equipment explicitly switches to Digital.
- Frame geometry, camera clearances and carbon/TPU manufacturing geometry are unchanged.

## v0.91.54 — Integrated DJI O4 Pro bumper lip false-collision fix

- Remove the unconditional height-only rejection of the DJI O4 Pro against the integrated TPU bumper lip. A forward-projecting lens may extend below the lip height without intersecting that lip in three dimensions.
- Keep the integrated front opening's structural lower limit and retain the later exact rotated-camera Boolean clearance against printable TPU. The finished bumper must remain one connected valid solid; real collisions are not silently accepted.
- Carbon bottom and top plate outlines are unchanged. No automatic camera plate cutouts.
- Native FreeCAD/OCCT rebuild against the user's exact preset is still required; syntax checks alone cannot guarantee the integrated loft and finishing Boolean succeed.

## v0.91.51 — DJI O4 Pro automatic mounting-centre alignment

- Fixed automatic front/back camera mounting alignment for the DJI O4 Pro. The camera has an asymmetric 16 mm rear-to-screw offset, so its screw-pattern midpoint must be translated onto the **actual sloping cage centreline** rather than aligning only the camera-body datum. The previous placement also missed the upper attachment's rearward offset.
- Fixed automatic vertical centring to prefer the centre of the real screw-travel envelope where the O4 housing fits between the plates; retain the housing and screw clearance constraints introduced in v0.91.50.
- Fixed and variable tilt, dual-slot and upper-pivot mounting use actual rotated screw locations. **Custom positions and user-set forward/back offsets remain intentional offsets** and are not silently removed.
- Corrected the editor information label from “camera centre” to “camera datum” to distinguish the body datum from the mounting pattern.
- Headless regression checks confirm the O4 screw-pattern travel midpoint aligns with the true cage centreline when the user offset is zero, and the saved 22 mm-standoff/three-plate hard-mount configuration still validates. The saved captured-insert preset requires Fit camera to reduce its insert opening; no silent changes to those dimensions were made.
- Native FreeCAD GUI rebuilding and the final manufacturing-part collision/boolean verification have not been performed here.

## v0.91.50 — DJI O4 Pro three-plate fit and automatic pivot correction

- Fixed the DJI O4 Pro automatic pivot height: the asymmetric rotated camera **housing** now determines the height, rather than centring only the forward-mounted screw line. This avoids incorrectly sinking the rear casing into the bottom plate at moderate/high tilt.
- Camera clearance uses the actual bottom-to-top plate cavity from `plate_levels` (e.g. 30 mm for 22 mm standoffs over a 2.5 mm bottom, 5 mm arm, and 3 mm mid plate). Camera/body parts can project through real front openings when exact CAD geometry permits it.
- `Fit camera` no longer raises O4 standoff height merely because its projected lens envelope crosses a flat-plate plane. The action proposes extra height only if the O4 side screw pattern cannot fit in the real cavity.
- `Fit camera` now finds the largest feasible O4 TPU insert diameter / retaining lip or compression pad that retains the configured cage edge web over the selected tilt range. Resizing is explicit: imported presets and user-specified printed-part fits are not silently changed.
- More specific DJI O4 Pro exact-interference messages include the failing component, tilt angle, and real plate gap. True carbon/TPU overlaps continue to be rejected; the full TPU front-bumper generator remains unchanged.
- Headless parametric regression and actual OpenCASCADE intersection tests against saved Analog Buster carbon solids verified O4 camera clearance at 0–45° with an automatically centred camera and 30 mm cavity. A full native FreeCAD rebuild remains unverified.

## v0.91.49 — DJI O4 Pro mounting & responsiveness

- Correct DJI O4 Pro side-thread positions: both screws on each side remain 16 mm apart vertically; the shared screw line now measures **16 mm forward from the rear housing face** (not the earlier -1.7 mm centre-offset estimate). The detailed thread markers and physical camera/cage fit share this same coordinate. Existing O4 mounts will be rebuilt at the corrected location; inspect them before machining.
- Balance the **automatic** DJI O4 Pro cage screw pattern vertically around its actual offset 16 mm mounting line. This avoids a false insert-edge failure in the saved Analog Buster 25-degree fixed-tilt configuration after the new screw correction. Custom pivot heights remain unchanged; impossible variable tilt/insert combinations still fail the material support check.
- Group all manufacturer camera profiles into **Analog cameras** and **Digital cameras** in the unified physical camera selector; DJI O4 Pro is available in Digital cameras. Keep the older DJI equipment enum internally for saved-preset compatibility, including its dedicated air-unit dimensions. Switching away from DJI also releases its camera-dimension locks.
- Improve the FPV camera renderer by caching lens rays across tilt tests, reducing bounding-volume hierarchy construction passes, and avoiding unnecessary copies of non-physical detailed reference models when preparing the ray mesh. Keep every physical part in the obstruction calculation and preserve image resolution, ray coverage, FOV and crop analysis.
- Fix the tilt-range sweep performing **two complete ray casts per angle** just to read two statistics. Both percentages now come from one trace at each angle.
- Reduce needless editor work: reuse the recorded vector frame preview when only virtual-optics settings change, and coalesce rapid field edits with a slightly longer editor refresh debounce (140 ms instead of 80 ms).
- Display separate geometry/mesh and ray-casting timings in the camera-view result so slow builds versus slow tracing can be diagnosed without new macros.
- No changes to the existing standard or full-height sculpted TPU bumper shape, other analog/digital camera mount profiles, toolbar graphics or README. Native FreeCAD GUI and complete assembly tests remain outstanding.

## v0.91.48 — DJI O4 Pro camera reference refinement

- Rebuilt the O4 Pro camera's detailed housing as a rounded, gently tapered single BRep sharing its silhouette with the collision probe, instead of a chamfered rectangular block.
- Reworked the camera optics with a close-fitting front collar, recessed glass, concentric retaining rings and small housing/side-thread details, guided by photographs of the actual DJI O4 Pro module.
- Kept the published 25.55 mm front-to-back, 20 mm width and 23.3 mm height, four M2 side holes at 16 mm vertical pitch, and the existing estimated -1.7 mm fore/aft screw line unchanged to preserve existing mount compatibility.
- The camera reference stays an approximate presentation model, not certified dimensional CAD; the rear screw offset and housing curvature remain undimensioned in DJI's drawing.
- Other physical camera profiles, DJI transmission module, editor options, full-height TPU bumper, icons, presets, README, and Help PDF are unchanged.

## v0.91.47 — Automatically sync virtual FPV view to selected camera

- Selecting any non-DJI physical camera (or custom measurements) automatically returns the virtual camera to **Follow selected camera**, manufacturer/default aspect, and automatic FOV/optical pupil estimate; no previous camera's manual optical calibration leaks into the newly selected camera. Users can still intentionally override optics afterward.
- Selecting DJI O3/O4/O4 Pro through the FPV system selector also resets the virtual view to follow that chosen system. DJI camera references and mounting geometry are unchanged.
- Show the currently active optical camera name, approximate diagonal FOV, aspect and follow/manual status directly in FPV > Camera view.
- When the chosen physical camera changes, update the recording-mode menu and clear any stale rendered camera image and obstruction report. Rendering remains manual to avoid costly frame rebuilding on every editor change.
- Preserve old presets and all physical camera mounting dimensions, TPU geometry, manufacturing, help PDF and toolbar assets.

## v0.91.46 — Physical camera library and camera-view optics

- Added selectable non-DJI camera references spanning analog 14/19/22 mm, Walksnail and HDZero 14/19 mm, plus editable generic 20/28 mm placeholders. Presets contain real published face sizes/FOV where available and explicitly marked estimates for undimensioned body lengths and M2 hole insets.
- Made the existing rear-face-to-side-screw offset the shared editable custom-camera measurement for mount holes, pivot, collision model and detailed reference. Single-screw cameras use a friction/variable pivot; existing preset loads are unchanged.
- Auto-linked **Follow selected camera** to the physical camera's matching optical model. Added published Foxeer T-Rex Mini 4:3/16:9 FOV distinctions, analog Foxeer/RunCam/Caddx and digital Walksnail/HDZero lens presets, while preserving manual FOV/aspect overrides.
- Placed the virtual optical viewpoint near the selected lens front rather than a fixed 3 mm outside the housing for non-DJI cameras. Simulation is still an equidistant-fisheye approximation, not calibrated distortion/stabilization.
- Expanded the rounded/tapered non-DJI housing references to include nano variants. DJI and all TPU bumper generation remain untouched.

## v0.91.45 — Caddx Ratel Pro one-screw camera profile

- Add Caddx Ratel Pro physical camera profile under FPV > Camera (19 x 19 mm housing, one side M2 screw per side, 15 mm lens, supplied drawing overall length 28.5 mm). A ~14.2 mm body-only depth, ~14.3 mm forward lens projection, and ~9 mm rear thread inset are drawing-derived estimates and remain editable.
- Add an independent black Caddx Ratel Pro detailed appearance with tapered shoulders and one M2 brass mounting insert on each side. Foxeer T-Rex Mini and other profiles are unchanged; DJI references remain untouched.
- Correct single-screw camera plates to position their pivot at the real local camera thread coordinate. Rotate a variable-angle single-screw body around that fixed pivot, not around the camera body's centre; prevent false plate/camera offset and phantom collision warnings.
- Selecting Ratel Pro changes a fixed two-screw mount to a single-screw variable friction pivot, retaining the selected camera tilt. It does not silently modify other saved camera profiles.
- Add optional Ratel Pro virtual camera optical preset with Caddx's quoted 125-degree FOV (axis and recording crop uncalibrated); follow the physical model automatically when optical selection is 'Follow selected camera'.

## v0.91.44 — Physical FPV camera housings and correct mounting holes

- Replace the generic rear cuboid with a tapered three-plane FPV housing used by both collision and detailed reference models.
- Add an explicit Foxeer T-Rex Mini physical preset: 22 x 22 mm face, 6.3 mm screw pitch, 7.7 mm rear screw inset. Approximate 14 mm body-only depth / 10.5 mm lens projection remain editable.
- Add editable physical screw rear inset and lens projection in FPV > Camera; 0 screw inset preserves legacy centred mounts.
- Align real cage holes and displayed brass side inserts with the same fore/aft position; keep DJI O4 model unchanged.
- Preserve all saved legacy camera dimensions and mounting data until user selects the physical preset.

## v0.91.43 — FPV camera fit and detailed camera references

- Fix false tilt-clearance rejections for non-DJI FPV cameras: replace the conservative full cuboid / mandatory 0.2 mm validation margin with a dimension-driven shaped camera housing and round lens probe checked against actual generated frame solids. Camera screw support, physical interference and variable-range checks remain active.
- Use one shared non-DJI housing/lens specification for analytic camera extents, CAD collision probes and detailed references; keep the DJI O4 Pro mounting and detailed camera code unchanged.
- Redesign analog and digital detailed camera references with rounded camera housings, chamfered side profiles, front bezels, stepped/knurled M8/M12-style lenses, recessed lens glass, metal side screw inserts and rear connector details. Analog and digital appearances differ. New optional visual-only styles: Foxeer T-Rex Mini, RunCam Phoenix 2, Caddx Ratel 2, Walksnail Avatar HD Pro and HDZero Micro V3. Models are manufacturer-inspired rather than exact CAD reproductions.
- Improve the existing Fit camera command to expand undersized generic pad/insert rectangles to surround the currently configured screw pitch and tilt path. Report the specific minimum required insert width and height instead of repetitive generic tilt errors. Neither visual style nor optical profile automatically changes the user's measured camera body dimensions or screw spacing.
- Preserve existing icons, full-height front bumper, saved presets, README and Help PDF. New Camera reference appearance selector is under Finishing > Detailed references.

## v0.91.42 — Distinct RotorForge toolbar icons

- Replace toolbar command icons for New Frame, Edit Frame, Export Frame, Toggle References, Hardware References, Front Isometric, and Help PDF with distinct cyan/teal icon art.
- Keep existing command names, keyboard/menu behavior, geometry, saved designs, exports, and manuals unchanged.
- Supply transparent high-resolution PNG assets inside the FreeCAD package for stable toolbar rendering.

## v0.91.41 — Virtual FPV camera tilt alignment

- Fix **FPV → Camera view → Use current camera tilt** for adjustable camera mounts: read the actual **CameraTilt** setting instead of the mechanical arc-slot reference midpoint.
- Make the disabled preview tilt field display the selected FPV camera angle and resync it when re-enabling **Use current camera tilt**.
- Keep the manual override preview-only, and preserve the existing tilt-range validity warning when an override lies outside a variable mount's adjustment range.
- Leave the mounting geometry's separate midpoint reference, frame generation, TPU bumpers, recording crops, other settings, and presets unchanged.

## v0.91.40 — FPV recording-mode crop overlays

- Add a camera-dependent recording-mode selector to **FPV → Camera view**: DJI O3/O4/O4 Pro recording resolutions and supported aspect choices, Walksnail HD Pro/Nano modes, HDZero Micro/Nano feed modes, and generic analog/DVR aspect presets.
- Render the existing frame/TPU obstruction ray trace through a full reference canvas and shade the areas outside a selected recording window. Highlight the estimated captured region with a yellow outline, preserving the optical-centre crosshair and dashed central-area guide.
- Recompute visible obstruction percentages specifically **inside the chosen recording area**, and identify the frame/TPU parts contributing to that area.
- Add optional 0–30% **manual additional crop** for stabilization or other cropping when the user has measured it. Zero assumes no *additional* crop, not that the device's EIS is crop-free. Changing modes/crop can redraw the current ray-traced view without rebuilding the frame.
- Use manufacturer-listed resolution and aspect modes where available, but DO NOT pretend to know unpublished sensor windows, proprietary lens distortion, RockSteady/Gyroflow crop, or FPS-specific FOV. Some HDZero modes are live-feed formats rather than camera-side recordings.
- Keep the feature preview-only: no modification to camera hardware geometry, frame construction, stored presets, README, TPU bumper, or STL/STEP exports.

## v0.91.39 — Virtual FPV camera view

- Add **FPV → Camera view** with camera-specific nominal diagonal field of view, 16:9/4:3 options and override for measured lens FOV and optical entrance-pupil offset.
- Render a first-obstruction ray trace against the actual generated frame, camera-cage and TPU bumper solids; mark blocked regions by part category, report full/central image coverage, and inspect alternate camera tilt angles.
- Include DJI O3, O4 and O4 Pro, Walksnail Avatar HD Pro/Nano, HDZero Micro/Nano and approximate analog nano/micro/mini/full-body optics. These presets are optical, not automatic mechanical-size modifications.
- Use an approximate equidistant fisheye map. Manufacturer maximum FOV does not reproduce their lens distortion, live-feed crop, aspect mode, Gyroflow/RockSteady or all optical entrance-pupil locations. This is a geometric fit preview and should be confirmed against real video.
- Keep all existing bumper modes and frame geometry unchanged. Camera-view fields do not invalidate the geometry build cache.

## v0.91.38 — Adaptive lower-edge fillet for integrated front bumper

- Round the bottommost outside edge of the one-piece TPU nose and bottom-plate gripping shoe, creating a softer lower perimeter.
- Automatically limit the fillet to the available sole and bumper-wall thickness. Reduce the radius, or omit it entirely when too little material remains.
- Construct the fillet before cutting the carbon mounting cavity to preserve the plate fit, retaining lip, camera opening and screw access.
- Keep the standard bottom-plate-only bumper and existing preset settings unchanged. If the CAD kernel rejects a radius, retry smaller radii without failing the whole frame.

## v0.91.37 — Adjustable integrated camera-cage front projection

- Add a dedicated **Camera cage front projection** control (0–8 mm, 0.5 mm steps) to the **Integrated camera cage bumper** settings.
- Increase only the OUTER front TPU profile around the camera cage, with a smooth upward ramp from the existing lower nose. The internal camera aperture, carbon side-plate fit and bottom-plate mounting cavity are unchanged.
- Preserve the full-height top-plate front contour while allowing the selected additional exterior projection at the upper brow.
- Keep the standard bottom-plate bumper and existing presets unchanged. Earlier presets load with front projection = 0 mm.
- Extend the 2D bumper preview and input validation to reflect the new setting.

## v0.91.36 — Restore sculpted integrated camera bumper

- Fix v0.91.35 regression: the integrated shoulder no longer extends to the rear mounting edge of the entire camera side plate.
- Restore the fluid front-cage shoulder outline while extending its front grip depth by at most 2.5 mm when needed.
- Keep the adjustable lower camera opening, with a safe minimum structural corner radius at small centre-reach settings.
- Preserve both exclusive bumper versions, the top-plate outline, lens clearance and all existing presets.

## 0.91.35

- Fix the integrated TPU bumper's ineffective camera-shoulder reach control. The setting now directly modifies the lower camera aperture and shoulder transition: **0 mm** retains the original full rounded U, and **1–20 mm** chooses the actual lower inward reach (capped by the available opening width). The upper camera opening remains unchanged.
- Extend the integrated bumper's sculpted outer rear contour around the actual camera side-plate polygon instead of following only its front edge; ease into the wider shoulders above the mounting shoe to reduce exposed carbon near the top.
- Lower the central camera opening only when the actual camera tilt/envelope requires it, reducing isolated crescent/slit cutouts from the subsequent camera-body subtraction. Reject configurations where the camera intrudes into the bottom mounting lip.
- Preserve the standard bottom-plate bumper, internal plate/camera cavity cuts, original top-plate contour handling, and the rest of the workbench.
- Update the reach field label/tool-tip and make its editor control select whole millimetres (0, 1, ..., 20). The default of 0 preserves the previous full-sweep shape for new presets; existing explicit values are respected.

## 0.91.34

- Broaden the integrated camera bumper's rear side silhouette into a continuous, tapered TPU shoulder from the original bottom shoe to the top plate, filling the thin triangular area behind each camera-cage rail.
- Construct that extra material in the same sole-to-crown loft, not as a fused-on rib, so the front nose and outside curves remain smooth.
- Leave the camera opening, front contour, bottom-plate mounting cavity, and internal camera/plate clearances unchanged. Preserve standard bottom-plate-only bumper mode.

## 0.91.33

- Rebuilt the integrated camera-cage bumper as a single continuous loft from the bottom-plate shoe sole to the upper camera protection. The bottom collar is no longer a separately fused solid that creates a hard horizontal transition.
- Used a rounded, curved nose profile that flows tangentially into the widening camera shoulders.
- Cut the bottom-plate mounting cavity, camera opening, and other required clearances from the unified shell.
- Left the standard bottom-plate bumper and existing bumper settings unchanged.

## 0.91.32

- Replace the integrated bumper's two separate lofted cage legs with one full-width sculpted TPU shell, using a smoothly lofted nose-to-cage shoulder surface and a circular lower camera opening cut through the single shell.
- Keep the original bottom-plate-only front bumper as an exclusive, unchanged alternative.
- Preserve the exact bottom-plate mounting collar, retaining recess, camera enclosure clearances, cutouts and other frame component collision cuts.
- Make the integrated camera bumper height 0 reach the top-plate underside and conform its front brow toward the sampled top-plate outline.
- Honour camera grip depth and centre blend reach in the integrated shell geometry; retain preset loading and two bumper type switching.
- Use analytic radius edges for the centre camera opening and a smooth fairing loft, with a ruled-loft fallback only when OCC cannot form a valid smooth solid.

## 0.91.31

- Added an exclusive Front bumper version selector: original Bottom plate bumper or independently built Integrated camera cage bumper.
- Preserved the normal slide-on shoe without camera-cage additions. Old camera-cover presets migrate to the integrated variant.
- Replaced the legacy add-on-cover workflow in the full variant with dedicated rounded-nose, sculpted side-support geometry anchored within the one-piece bumper.
- Retained full-height top-plate outline following and adjustable camera-guard height, grip depth, and centre reach.
- Retained bottom-plate fit, camera and side-plate clearance, carbon subtraction, and one-solid validity checks.

## 0.91.30

- Replace the faceted camera-cage bumper loft with a smooth OpenCASCADE loft while preserving a ruled-loft fallback for geometries the CAD kernel cannot interpolate reliably.
- Correct the outline-trim height: trim the curved support only at its shoe contact, preventing the triangular voids and pinched edges caused by cutting into the support above the bumper.
- Reduce the root U-slot depth to form a fuller, smoothly connected shoulder at the bumper rather than leaving a deep hollow notch.
- Keep the full-height nose behind the real top-plate front edge instead of pushing it beyond the plate outline. Full-height = 0 still reaches the top-plate underside.
- Remove the redundant interior cutter on the already-open U-shaped rails; the normal physical camera-envelope and frame-component clearance subtractions remain in place.
- Preserve the user's existing settings, adjustable centre blend reach, TPU shoe outline and camera mounting geometry. No installation macros or README changes.

## 0.91.29

- Sculpt the front camera TPU cover with a broad, tangent-controlled transition from each rounded cage grip into the existing front shoe; round the sharp outer profile bends without changing the real camera-cage mating clearance.
- Fix camera-cover height `0 = full`: the finished TPU now reaches the underside of the top plate without the previous 0.35 mm forced air gap.
- Read the actual finished top-plate front perimeter (including curved shoulders/recesses) and smoothly sweep the upper TPU brow forward to that outline; leave the inside cage-grip surfaces anchored to the real camera cage.
- Keep partial-height covers at their requested height, preserve lower outline clipping, adjustable centre reach, camera tilt clearance, and the connected one-piece bumper construction of 0.91.28.
- Update the two-dimensional preview and height-control help text. No new macros or changes to saved presets.

## 0.91.28

- Rebuild each camera-cage TPU grip and its full-width shoe transition as one continuous rounded loft, removing the Boolean mating seam and mid-transition gap.
- Shape the transition foot as a compact, embedded support rather than a deep open-ended U that leaves visible voids at the rear of the bumper.
- Clip the lower transition against the actual curved front-bumper outline, removing toe overhangs without trimming the upper camera-grip geometry.
- Preserve camera aperture, top-plate clearance, 0–20 mm centre-blend reach and existing saved frame parameters.

## 0.91.27

- Preserve the actual rounded U-shaped camera-grip width all the way into the front bumper; remove the narrow rectangular shoulder neck.
- Loft a continuously curved, full-width lower shoulder that expands into the TPU shoe, while keeping the camera channel open and upper profile inside the round grip.
- Restrict the bumper-outline trim to the shoe-contact region, so the loft is not narrowed above the retaining lip.
- Preserve the adjustable centre blend reach, rounded grip ends, top plate clearance, and existing frame/preset settings.
- Validate the revised two-sided bumper geometry and camera plate cuts against the saved Analog Buster design.

## 0.91.26

- Remove the tiny crescent-shaped lip artifacts on both rounded TPU camera-cage covers: shorten the rear tips slightly and bury the blend termination within the actual curved front wall rather than its rectangular bounding box.
- Reshape the raised camera-cover shoulder into a fluid shoe-level taper, starting in front of the open U-channel, without the exposed ledge or inner fins.
- Add **Camera cover centre blend reach** (0–20 mm, default 2 mm) to independently expand both lower support transitions toward the middle of the existing shoe, without widening its outer footprint.
- Update the TPU Front bumper editor and 2D preview for the new control; preserve existing presets and all other bumper settings.

## 0.91.25

- Fix v0.91.24's accidental rectangular-grip fallback: use the already calculated rounded camera-cover cross-sections to create the actual solid.
- Round both front nose corners and the open rear ends of each TPU camera-cage grip; retain the hollow camera channel and two-sided symmetry.
- Loft through actual camera-cage profile corners with a precise ruled path and a curved alternative when needed; never silently return a square grip.
- Retain the previously working short shoe-to-cage transition, clipping to the actual front bumper outline and stopping 0.35 mm below the top plate.
- Keep all existing frame parameters and other workbench functions unchanged; no macros added.

## 0.91.24

- Restore genuinely rounded outer camera-cover corners using a circular-section U-channel; retain the direct open-rear construction that successfully builds in v0.91.23.
- Follow only the actual camera-cage profile corners to eliminate redundant loft stations and the visible ribbing of earlier full-height lofts.
- Rebuild the lower bumper-to-cover shoulder with rounded spline-free cross-sections, a smooth zero-slope taper, and a recessed termination inside the cage cover instead of an exposed shelf.
- Limit the lower shoulder to the existing front shoe silhouette and keep the top cover 0.35 mm below the top plate, preserving all saved frame dimensions and camera clearances.
- Keep the v0.91.23 construction as a safe fallback for kernel-specific loft problems; no new options or diagnostic macros.

## 0.91.23

- Replace the failing full-height front-bumper camera-cover loft and its landing checks with two direct cage-profile U grips and short, stable lower transitions.
- Crop the entire lower camera-cover transition to the finished bumper shoe outline, so no shoulder projects beyond the toe.
- Stop the covers 0.35 mm below the underside of the real top plate; preserve the open U channel, camera tilt clearances, and screw/part subtraction.
- Maintain the existing front bumper geometry, shoe settings, and saved presets. No installation or version-check macros.

## 0.91.22

- Restore the earlier, successfully building front-bumper shoulder loft instead of the new camera-cover landing algorithm, which could reject valid shoe designs regardless of reach.
- Trim the lower transition where it joins the actual bumper outline while allowing the upper camera cage to slope rearward, preserving full-height protection.
- Cut the cover 0.35 mm below the actual top plate lower face, including custom standoff and two-/three-plate configurations.
- Preserve existing shoe geometry, U-shaped camera grip, camera-clearance subtraction, and true solid connection to the bumper. No new macros or preset changes.

## 0.91.21

- Add a FreeCAD repair installer to update the *actually loaded* RotorForge workbench folder. Addresses old bumper modules continuing to run after installing a newer ZIP or keeping duplicate installations.
- Installer displays the current source path, backs up the workbench before copying, and requires a FreeCAD restart (rather than pretending loaded Python modules have been updated).
- Retain the adaptive camera-cover-to-bumper landing geometry introduced in v0.91.20. No frame parameter changes.

## 0.91.20

- Fix curved/concave front-bumper shoes failing with "no usable landing inside the actual shoe outline." The cage cover now chooses its base by actual U-channel contact instead of demanding a full rectangular landing.
- Anchor supports to the existing bumper's real upper TPU lip, rather than empty space within the outer silhouette.
- Taper buried U-channel root wall into the specified full-wall thickness; trim any buried extension to the actual shoe outline to avoid unwanted lower protrusions.
- Preserve camera clearance, the existing frame settings and rounded upper cover.

## 0.91.19

- Fix the front-bumper camera-cover landing check rejecting valid designs with "no usable landing inside the shoe outline". The old check called solid containment on a planar face.
- Verify the entire candidate footprint with a planar boolean-intersection area check, preserving the original curved bumper outline without unwanted overhang.
- Add a local offset search for legitimate concave/tapered bumper profiles, without reducing the specified bumper wall thickness.
- Keep the v0.91.18 U-channel loft, rounded upper cover rim, and all frame/preset values unchanged.

## 0.91.18

- Fixed the camera-cage front bumper failure that surfaced as FreeCAD's "Null shape" error. The cover is now lofted as a direct, open-rear U-channel rather than cutting a slot through a densely segmented closed loft.
- Added a true-outline-constrained landing at the shoe and a smooth transition into the sloping camera cage, with a small rounded-in top termination.
- Removed a redundant potentially empty boolean intersection and added explicit connection and camera-sweep checks with descriptive error messages.
- Retained the saved frame geometry, O4 camera mounting corrections, and 2 mm camera-cage edge allowance.

## 0.91.17

- Rebuilt front bumper camera-cage shoulders as reduced-seam C1-continuous lofts to remove ribbed/wavy top artifacts.
- Shortened and smoothed the transition from the actual bottom-shoe outline into each side camera cover; retain the true shoe footprint and protective U-channel.
- Added a gentle rolled upper termination and small top-plate clearance to prevent overhangs.
- Increased shoulder-to-shoe engagement at the base without changing camera mounting or other frame dimensions.

## v0.91.16 — DJI O4 Pro existing-preset clearance fix

- Switching an existing design to DJI O4 Pro now replaces the former default 4 mm cage-edge web with the supported 2 mm web, without altering other frame settings.
- Clarify the O4 insert clearance error with the measured available and required distances.
- Verify the Analog Buster preset's 25-degree O4 camera mounting coordinates, envelope and insert fit in portable validation. The FreeCAD solid-generation engine is required for final manufacturing verification.

## v0.91.15 — DJI O4 Pro camera screw placement

- Align the O4 Pro screw paths, tilt slots, TPU inserts, hardware and detailed camera reference to one common camera-side M2 mounting datum (16 mm pitch, rearward of the lens/body centre).
- Use an approximate O4 casing profile and cylindrical lens instead of the rectangular camera envelope for assembly interference checks.
- Avoid rejecting O4 camera clearances from a bounding box before checking the actual top/bottom plate solids and cutouts.
- Limit O4 Pro camera screw penetration to DJI’s 2 mm maximum; retain the 2 mm camera cage edge web and physical collision checks.

# v0.91.3 - camera protection and continuous arm-tip joins

## 0.91.14

- Replace straight full-height camera bumper pillars with a curved transition from the finished shoe outline to the camera cage grip.
- Retain the original bottom shoe and plate fit; follow the cage front through the upper section to the top plate.
- Update the projected protection preview and Help explanation. No workbench tests run for this release.

## 0.91.13

- Keep full-height camera bumper shoulders within the bottom bumper outline.
- End unclamped split TPU cages smoothly on the bottom-plate edge without a projecting front strip; retain the optional clamp and one-piece connection.
- Land side-guard extensions on the actual TPU cage and locally enlarged insert bosses.
- Enable fixed or variable DJI O4 Pro tilt, with independent isolation pieces following each screw path and corresponding preview/support geometry.
- Update Help controls and installation version. No workbench tests run for this release.

## 0.91.12

- Move the O4 Pro choice into FPV > Camera; preserve hard mounting and add independent compression pads as well as captured inserts.
- Put O4 isolation dimensions in the TPU camera-isolation section.
- Use 4.1 mm x 3.5 mm insert pockets and independent 3.2 mm plate clearance holes; bias local bosses outward and reject camera-fixing/pocket interference.
- Restore full-height separate camera-bumper protection up to the top plate.
- Add one-piece/split TPU cages, finished-bottom-outline front connections, adjustable split inward reach and optional bottom-plate clamps.
- Update Help and installation guides. Workbench tests were not run at the user's request.

## 0.91.11

- Rename the widened X layout to Squashed X, including saved-design migration and Help.
- TPU cages use M3 plate screws and local adjustable heat-set insert pockets and bosses; captured tabs are disabled.
- Add an optional cage-integrated front bumper and conditional camera-cage subsection; disable the separate TPU shoe for TPU cages.
- Add DJI O4 Air Unit Pro camera/VTX dimensions, M2 mounting pattern, two separate captured inserts per camera side, and a dedicated detailed camera reference.
- Update the Help and installation guides. Workbench tests were not run for this release.

## 0.91.10

- Follow both inset tip and expanded motor-pad contours for tip cutouts; require 2 mm opening width and 4 mm2 area.
- Keep TPU protector side walls continuous on rotated pads and limit sleeve access slots to the sole.
- Extend the curved camera-bumper shoulder to the full selected cover height.
- Update the Help and Installation guides.

## 0.91.9

- Derive arm-tip sleeve coverage from the complete motor-protector envelope instead of the first cap polygon, retaining coverage over blended shoulders.
- Preserve motor seating clearance and the outward-only sleeve limit; update the Help guide.

## 0.91.8

- Make the curved camera-bumper shoulder define the lower outer surface, removing the overlapping rail toe at the shoe join.
- Preserve the bottom bumper outline and cage fitting slot; update the Help guide.

## 0.91.7
- Clip camera-bumper shoulders to the actual bottom shoe outline, including shaped front edges.
- Reshape outward motor-pad shoulders into a continuous envelope with stretched caps.
- Differentiate the narrow elongated Oval cap from Round cap; add Tapered cap and Shallow arch.

## 0.91.6
- Keep arm-tip roots pad-aligned; direction now stretches the outward cap.
- Replace the old tip list with four broad cap profiles; migrate saved styles.
- Replace camera bumper struts with full-depth curved shoulder bodies.

## 0.91.5
- Smooth curved shoulder transitions between the shoe and camera grips.
- Directional arm-tip extensions grow from the existing pad rim; motor-pad orientation stays unchanged.
- Five broad impact-guard profiles added ahead of the existing shapes.

## 0.91.4
- Camera bumper protection wraps both cage faces with adjustable grip depth; original bottom shoe outline preserved.
- Upper motor-protector sleeve restricted to the arm tip.
- Six additional arm-tip shapes with mirrored orientation.

- Add optional front-bumper rails following the front edge of each camera cage, with full-height or limited-height coverage and feet connected to the shoe.
- Fill pad reliefs within the arm-tip attachment footprint so the join does not introduce unintended enclosed holes; retain the separately enabled tip cutout.
- Keep TPU sleeve caps outside the motor reference diameter as well as the original pad footprint.
- Split Camera cage into wrapping subtabs with an always-visible construction selector and search routing to the appropriate subtab.

# v0.91.2 - exact front bumper camera clearance

- Cut the front bumper against actual camera cage solids, not their bounding boxes. Empty space beneath sloped or extended cages no longer removes bumper material.
- Preserve real interference relief and the existing bottom-plate fit clearance for carbon, TPU and aluminium cages.

# v0.91.1 - camera cage controls and directional arm bumpers

- Consolidate camera side walls, tilt, mounting mode and camera/insert position into FPV > Camera cage; retain insert manufacture and fit under TPU > Camera isolation.
- Share cage dimensions across all three materials and migrate the active dimensions from 0.91.0. Enable automatic camera travel support for all cage styles.
- Set a dedicated minimum 4 mm opening-to-edge web, independent of the general plate web.
- Add four extending front/rear profile options with independent reach controls and unchanged attachment endpoints.
- Add five bumper profiles, front/rear and sideways orientations, mirrored asymmetric tips, and optional outline-following cutouts beyond the motor pad.
- Update previews, sleeves, saved parameters, exports and Help for these settings.

# v0.91.0 - camera cages, material additions and presentation fixes

- Preserve the original carbon camera plates and all existing isolation choices.
- Add two-piece TPU cages (tabs or screw pilots), with independent wall, length and crossbar controls; add flat CNC aluminium cheeks with independent thickness, length and density. Both support hard mounting, compression pads and captured inserts.
- Add independent straight, swept, rounded-waist and faceted-waist front/rear cage profiles. Cage exports and mass follow the selected material; aluminium contours stay outside carbon stock sheets.
- Add material to main/clamp plate outlines with the existing pattern shapes. Require connected overlap and preserve existing holes/slots; perform additions before subtractive patterns.
- Add round, faceted and forked carbon bumpers beyond the motor pads, plus optional TPU protector sleeves.
- Make opaque prop/TPU finishes fully opaque and reset per-face materials when changing finishes. Move TPU appearance first and group parts from front to rear.
- Cache placed reference geometry separately from colours. Avoid repeating validated carbon topology checks and duplicate physical-pair collision checks; retain actual geometry and clearance checks.
- Improve the generic camera reference with recessed fasteners and a rear connector.
- Regenerate Help from current controls and update installation version. Remove build outputs, development scripts, test caches, example projects and historical design notes from the install ZIP.

## v0.90.21 — Shared propeller and TPU colours

- Extended **TPU > Appearance > TPU / printed part colour** with all 13 realistic propeller finish choices: smoke grey, clear, clear black, black, white, orange, pink, purple, neon yellow, lime green, blue, red, and teal.
- Added viewport translucency for clear and smoke variants; this is a visual approximation, not a physical TPU material specification.
- The selected finish is applied together to camera isolation inserts, front bumper, motor protectors, LiPo pad, rear VTX / ELRS antenna holders, and flexible side guards.
- Preserved the legacy Yellow and Grey choices so old saved designs load unchanged.
- Colour changes remain view-only: no changes to part geometry, mass estimates, TPU export files or CNC manufacturing output.
- Updated the Help and Installation guides and added regression coverage.

## v0.90.20 — Detailed propeller colours

- Added realistic commercial FPV propeller finishes to Finishing > Detailed references, with swatches and transparency for clear/smoke props.
- All four detailed props update together; palette changes only the display and preserve cached geometry, assembly checks, and exports.
- Existing JSON/FCStd settings stay compatible.

## 0.90.19 — front bumper STEP rebuilt from STL mesh

- Generate the front-bumper STL **before** creating its STEP variants, then reconstruct both STEP files from the very same watertight triangle mesh used for that STL.
- Export the print STEP at the STL print origin; translate the second, assembled STEP into its original frame position.
- Validate single closed solid, bounding dimensions and volume before writing STEP, and stage both files until both writes finish.
- Restrict changes to the front bumper: preserve all other STEP/STL and CNC exports. If conversion fails, keep the successful STL and full export package, omit faulty bumper STEP files and write `FlexibleParts/FrontBumper_STEP_WARNING.txt` plus an export warning.
- These two STEP outputs are faceted (triangle surfaces), not smooth editable parametric solids; native FreeCAD testing is still required.

## 0.90.18 — restore full export after front bumper regression

- Remove v0.90.17's mandatory front-bumper STEP round-trip, mesh closure and strict print-origin gates, which could abort otherwise successful exports.
- Restore the previously working print-placement geometry and normal STL export path for every flexible component.
- When a front bumper contains a single valid solid plus stray non-solid faces, optionally export only that solid; otherwise fall back to the previously working STEP writer without failing a valid export.
- Keep every feature introduced up through v0.90.16, including analog/digital VTX and antenna references.
- Add portable regression tests for normal export, optional cleanup and its failure fallback. STEP/slicer verification remains a recommended external check; no claim is made that all source-geometry problems are resolved.

## 0.90.17 — front bumper print STEP export repair

- Extract the front bumper's single printable solid before placing it at the print origin. Prevent any auxiliary faces or edges left by a Boolean compound from entering STEP or STL export.
- Verify assembled and print STEP files by re-importing them as closed, valid, single solids with the original volume and bounding dimensions. Retry with conservative splitter cleanup when needed; reject a broken STEP rather than silently leaving an unusable file.
- Verify the print pose is at Z=0 and add native/portable regression checks. The bumper shape, user settings and other TPU exports are unchanged.

## 0.90.16 — commercial VTX reference overhaul

- Default analog VTX now resembles an enclosed commercial FPV video transmitter: shallow dark metal housing, surface ridges, status LEDs, button, five-contact front header and single rear RF socket.
- New **Analog enclosed** override; existing **Exposed PCB** and **Finned enclosure** options remain valid. Automatic chooses commercial analog or digital based on video system.
- The exposed analog option has PCB-mounted components and RF shield: former vertical gaps beneath components, status lights and connector hardware were removed.
- Digital air-unit geometry is now a separate exclusive branch, without inherited analog PCB, copper mounting rings, chips or analog can.
- Face materials are reset fully on appearance changes to eliminate stale colouring.
- VTX dimensions, hole clearance, TPU attachments, antennas, cutting output and mass estimation are unchanged.

## 0.90.15 — detailed VTX geometry repair

- Rebuilt analog and digital VTX references with more realistic component proportions and lower-profile assembly details.
- Digital: dark, compact ribbed air-unit enclosure with 12 shallow crosswise cooling ribs, fastener openings, front header and dual rear RF sockets.
- Analog: low-profile RF shield, PA package, SMD parts, test pads, status LEDs and rear-facing RF socket instead of oversized heatsink details.
- Cut all decorative geometry clear of selected mounting holes for 20 mm, 25.5 mm and dual patterns; preserve VTX envelope and display-only operation.
- Update user guide with the new analog/digital appearance reference. Existing settings, TPU mounts, frame solids, CG and CNC exports are unchanged.

## 0.90.14 — VTX transmitter appearance

- Detailed VTX reference reworked to resemble a real FPV transmitter, with separate analog exposed-PCB and enclosed heatsink styles. Automatic picks the style from the selected video system.
- More realistic material colors, RF shields, fin array, screw-hole rings, RF sockets, discrete passives and front wiring header.
- Reference appearance never modifies VTX mounting geometry, the collision envelope, weight/CG or CNC exports.

# v0.90.13 - automatic ELRS lead clearance and antenna finishes

- Automatically end the ELRS T-reference coax at least 3 mm ahead of the modelled VTX board rear boundary. Never run the visual feed into the VTX; omit it when the T centre is already inside/beyond the safe gap. Recompute with VTX and mount changes.
- Remove manual feed-length controls from the Finishing editor; keep their older JSON values readable but ignored for presentation geometry.
- Give the VTX antenna head independent matte black, charcoal grey, white, red, orange and blue finishes, while retaining separate dark coax, strain relief and metallic accents.
- Make the ELRS T housing, centre junction and coax near-black; update the Help PDF and tests.

# v0.90.12 - commercial-style antenna geometry and length presets

- Replace long, thick VTX reference cylinders with slim leads, connector relief, short widened antenna radomes and rounded tips. Retain the existing mount pose, tilt, count and splay.
- Offer common nominal lollipop lengths (60, 85, 95, 100, 150, 165 mm), Walksnail Avatar V2 (105 mm, 15 mm head), and a custom dimension mode. Catalog lengths are not universal standards.
- Draw the ELRS T with a centre junction, realistic thinner horizontal arms, and a separate forward coax lead. Choose 50/51 mm compact T or theoretical 62.5 mm dipole spans, 40/70/85/95 mm feed lengths or custom values.
- Preserve v0.90.11 custom dimensions when importing older saved JSON. Keep all antenna references display-only and outside manufacturing, mass, and solid collision checks.
- Update the in-workbench Help and unit/native smoke tests.

# v0.90.11 - optional VTX and ELRS antenna references

- Add independent 3D visualization toggles for rear VTX antennas and a horizontal ELRS T antenna.
- Place them from the existing TPU holder/hook layout, including dual VTX tilt and splay.
- Expose editable antenna body length, diameter, T-antenna span, and centre leg length.
- Keep visual antenna references out of physical validation, weight/CG and manufacture exports.
- Update the Finishing editor, JSON persistence, native FreeCAD objects and Help PDF.

# v0.90.10 - flush rear grip stack

- Seat VTX grips against the top plate and ELRS grips on the bottom/mid carrier by default.
- Fill the remaining rear standoff height with side-guard grips when either antenna mount is enabled.
- Add Top plate gap, VTX to side-guard gap and ELRS to side-guard gap, all defaulting to zero. Retain ELRS height above plate as the lower plate gap.
- Remove fixed vertical clearances from mount seating and rear grip reliefs. Preserve minimum guard bearing and collision checks.

# v0.90.9 - flat VTX tube underside

- Trim u.FL/MMCX tube and clip roots flush with the carrier underside. Preserve upper sleeves and pigtail tabs.

# v0.90.8 - preview and layout performance

- Reuse vector preview drawings during zoom and pan; invalidate on design, mode, size and mass-overlay changes.
- Memoize arm layouts while preserving dependency tracking and caller-owned results.
- Locate side-guard stations with exact boundary intersections instead of face booleans.
- Audit all 374 documented controls against the current editor, correct ten labels and add missing rear-antenna navigation entries.

# v0.90.7 - full-section ELRS hook connections

- Extend the equal-width/height ELRS support bars into the hook body instead of joining through a rounded tip.
- Retain rounded edges, clear hook bores and upward insertion openings.
- Update the ELRS preview and Help illustration. VTX geometry is unchanged.

# v0.90.6 - smoother rear antenna mounts

- Slim ELRS hook extensions to equal width and height, limited by hook width and available grip height; round their edges.
- Remove the added VTX rear brace. Keep front-facing openings through the full axial thickness at the clips, while preserving the remote carrier.
- Update editor schematics and Help illustrations. Existing settings remain compatible.

# v0.90.5 - independent ELRS hook reach and full VTX entry channels

- Add ELRS hook rearward offset independent of the main bar reach, with two connecting ribs.
- Add an adjustable centre pass-through through the ELRS bar, with minimum surrounding material checks.
- Turn u.FL/MMCX side-entry slots toward frame front and extend them through all supporting stock.
- Add rear bracing so the full entry channels do not separate the standoff grips from the holders.
- Update schematics, persistence tests and Help illustrations.

# v0.90.4 - side-entry VTX clips and lower ELRS mount

- Add Closed tube / Side-entry clip choice for u.FL/MMCX stems, with adjustable retaining lips and flared entry channels. Preserve closed tubes as the default and keep SMA/RP-SMA tabs unchanged.
- Add an independently enabled ELRS T-antenna mount below the rear guard grips, with two open hooks and a connecting bar.
- Adjust ELRS rearward reach, height above the carrier, grip size/fit, bar shape/width, hook spacing/width, antenna diameter, wall and retaining lip.
- Cap ELRS grip height to available space and relieve the guards locally without changing their mounting band.
- Retain actual-solid collision checks, cached unchanged guards, native/JSON persistence and separate printable exports.
- Update the editor schematic, integrated Help and CAD regression coverage.

# v0.90.3 - rear mount performance and SMA pigtail tabs

- Keep the rear VTX antenna mount as an integrated workbench feature.
- Extrude the curved bar from a single outline; use single-face capsule ribs.
- Reuse unchanged side guards when antenna length, tilt, offset or connector changes.
- Reuse pure layout calculations across edits of unrelated parameters while preserving cache dependencies.
- Use bounded/cached exact collision checks; retain real plate and guard protection.
- Give SMA/RP-SMA rounded bulkhead tabs with independent 2-5 mm thickness and nut/washer access; retain u.FL/MMCX sleeves.
- Update controls, preview, Help and regression coverage.

# v0.90.2 - independent antenna sleeve length and offset

- Limit only the standoff grips to the upper rear standoff space.
- Lengthen antenna sleeves outward along their axes from fixed roots; keep the guard seat independent of sleeve dimensions.
- Add signed Holder fore/aft offset, separate from connecting-bar reach.
- Allow sleeves above the top plate behind the frame while checking actual bottom/mid/top plate and guard collisions.
- Update preview, persistence and both Help copies.

# v0.90.1 - antenna and side-guard fit

- Seat antenna grips directly on resized rear side-guard sleeves, with at least 4 mm of guard bearing.
- Reserve mount clearance in the guard walls instead of trimming away antenna grips.
- Add a direct standoff-hole diameter override, independent of antenna bore diameter.
- Add 0-90 degree antenna elevation, default 60 degrees above horizontal; keep symmetric dual outward yaw.
- Update native angle properties, editor control limits, saved settings and both Help copies.

# v0.90.0 - experimental rear VTX antenna mount

- Add TPU > Rear antenna, disabled by default.
- SMA/RP-SMA bulkhead bores; u.FL/MMCX stem holders with measured diameter/length overrides.
- Fixed 30 degree elevation and dual outward yaw; curved, triangle and rectangle bars.
- Adjustable reach, spacing, bar width, grip height, grip wall and fit; cap to available space and relieve guard interference.
- Integrate preview, persistence, mass, collision checks, caching and STEP/STL export.
- Update both Help copies and document all 352 visible controls.

# v0.89.6 — Help correction

- Synchronize both packaged Help PDFs, including the copy opened by FreeCAD.
- Update section navigation, bottom search, preview zoom, Airflow workspace and saved hardware guidance. Remove the outdated editor screenshot.
- Validate all 339 visible controls against current defaults and choices during guide generation.

# v0.89.6 — saved reference hardware (2026-11-04)

- Save reference-hardware choices with RotorForge settings JSON and exported FrameParameters.json: selected groups, retaining hardware, engagement, whether references were created, and their visibility.
- Restore saved reference hardware automatically when Create/Update builds a loaded design. Loading or cancelling the editor does not modify the existing frame.
- Preserve explicitly hidden hardware and per-owner visibility; preserve loaded preferences when saving again before creating a frame.
- Continue accepting legacy JSON files without hardware preferences. Create/Refresh the desired references and save again once to add the missing preferences.

# v0.89.5 — editor workspace improvements (2026-11-03)

- Place the seven upright category icons in a vertical rail on the left.
- Wrap subsection buttons into visible rows; TPU fits two rows at the minimum editor size in the tested environment.
- Move control search beside the bottom Create/Update, Maximize and Cancel actions.
- Add pointer-centred wheel zoom, drag-to-pan, double-click reset and Fit view to the overall/parts preview.
- Give Airflow / outlines a full-width workspace: saved patterns, editing controls and preview side by side, with adjustable column widths. All existing cutout actions remain available. Guidance is available through How to use cutouts.
- Keep maximize/restore, saved settings, geometry generation and manufacturing export behavior.

# v0.89.4 — editor category icons (2026-11-03)

- Use icon tabs for the seven main sections inside the complete editor: Frame, Arms, Hardware, Battery, FPV, TPU and Finishing. Hover shows each section name.
- Keep subsection text tabs, search navigation, live preview and all existing editing behavior.
- Frame geometry, saved settings and build/render pipeline are unchanged.

# 0.89.3

- Enlarged press-nut mounting pads around the complete bore, shank and flange/counterbore footprint, using the configured minimum material with a 1 mm floor. FC stack inserts receive the same support.
- Automatic tangent fillets add material at mounting-extension junctions on arms and plates even with general edge fillets disabled.
- General plate fillets and final insert checks protect the full flange bearing margin.

# 0.89.2

Based on the restored 0.89.1 release.

- Arm roots automatically add connected rounded stock around displaced mounting screws.
- Receiving plates and standoff mounts gain local supporting extensions, retaining the requested fixing coordinates and minimum material.
- Extensions recalculate on every edit and disappear when no longer needed. CAD, previews and cutting exports share the same support layout.
- Hole spacing, fitted joints, reliefs and assembly collision checks remain active.

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

- Redesign the combined rear mount around one open, shared low yoke with local VTX gussets and two ELRS handles per crossbar.
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

- Focus the editor on supported two- and three-plate frames.
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

- Corrected Squashed X to widen the motor pattern left–right, with a clear width/front–rear aspect label.
- Added front and rear standoff controls with common-size shortcuts and custom lengths in the Standoffs tab.
- Link both height controls so the top stays level: three-plate fronts span bottom-to-top; rears span mid-to-top. Two-plate pairs stay equal.
- Show both standoff lengths in the editor summary and verify selected lengths in manufacturing exports.
- Preserved old configurations and normalize older wide Squashed X ratio values.

## 0.2.0

- Added a two-plate / three-plate selector in the Layout tab.
- Give the three-plate bottom an adjustable front extension.
- Replaced the duplicated mid outline with a stack-to-rear body and small front arm clamping tabs.
- Added independent mid front/rear reach controls.
- Use bottom-mounted front standoffs and mid-mounted rear standoffs in three-plate mode; calculate and export the required lengths.
- Mount arms below the bottom in two-plate mode, with no mid geometry, mass, STEP solid, or cutting profile.
- Updated live preview, validation, exports, presets, and example documents.
- Added support for updating existing 0.1 documents and presets.

## v0.93.43
- Balanced studio lighting so the drone front no longer renders darker than the rear on some look presets.
- Added a subtle automatic front-balance light that preserves dramatic looks without flattening them.
