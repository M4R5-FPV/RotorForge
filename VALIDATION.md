# RotorForge 0.89.1 validation

- All 471 portable tests pass without skips, including new checks for face contact, the full wall thickness inside each edge, mirrored placement, inward clearance and plan previews.
- Twenty-five native FreeCAD checks pass. Actual face-to-face contact area is measured for two/three plates, zero/positive setback and a tapered/filleted top. Strap slots and one/two outline cutouts retain a 2 mm passage below the top plate. The original wrap geometry matches 0.89.0 exactly for both plate arrangements. An old 0.89.0 Between plates frame regenerates inward and retains the new contact after save/reopen; the disk cache restores the corrected solids.
- The retained native cases also cover both arm positions and a clamp, vents, high USB access, separate guard straps, a stepped mid-plate, camera closure, wide VTX openings in both modes, fit switches, STEP/STL and manufacturing exports. Exact part/electronics collision checks remain active.
- Four native editor checks pass; the Help inventory matches all 339 controls. The Help is 101 pages and Installation is two pages. All pages were rendered, changed pages reviewed at readable size, and text remains within page bounds. The requested Windows Explorer path is retained.
- Runtime: FreeCAD 1.1.4 / Python 3.11 / OpenCASCADE 7.8.1 on Linux, with an offscreen editor. Hardware OpenGL, Windows installation and physical print compression/fit were not tested. Plate contact in CAD is nominal, without an intentional interference allowance. Previous load optimizations remain in place; this release makes no new speed claim.

# RotorForge 0.89.0 validation

- All 467 portable tests pass without skips. Twelve new tests cover legacy defaults, inner-face bounds, one joined wire span, side selection, stepped edges, camera closure, automatic/custom VTX dimensions, signed offsets, invalid openings, continued mounting support and live previews.
- Nineteen native FreeCAD checks pass: seven between-plate configurations (two/three plates, both arm positions, clamp, top strap cutouts, vent/USB/guard straps, stepped mid, camera closure and zero clearance); four wide-VTX combinations; saved-frame switches/reopen; STEP/STL/CNC exports; two exact 0.88.0 geometry and document-migration comparisons; independent left/right openings; base-wall reuse; persistent cache restoration. Enabled guards remain valid connected solids and clear the tested carbon and VTX envelopes.
- Four offscreen native editor checks pass: mode selection restores saved wire-pair choices, VTX options retain their settings, the actual Load action reproduces settings and preview, and Help metadata matches all 339 visible controls.
- The illustrated Help is 100 pages; Installation remains two pages with the requested Windows Explorer path `%APPDATA%\FreeCAD\v1-1\Mod`. All pages were rendered, changed pages reviewed in detail, and all text stays within page bounds.
- Native runtime: FreeCAD 1.1.4 / Python 3.11 / OpenCASCADE 7.8.1, Linux. Hardware OpenGL, Windows installation and physical print fit were not exercised. Existing 0.88.0 performance improvements are retained; no new speed benchmark is claimed for this release.

# RotorForge 0.88.0 validation

- All 455 portable tests pass with no skips. New checks cover immutable snapshots, changed/unchanged dependency tracking, validation-result isolation, supplied BRep reuse, exact cache identities, runtime mismatch, payload corruption, invalid metadata, unavailable storage and cache size/count limits.
- Nine native FreeCAD checks pass: disk-restored solids are exact equivalents, real parameter changes invalidate dependent parts, invalid inputs remain rejected, corrupt archives regenerate, modified document Shapes are repaired, direct property edits are read, saved files reopen/update, and STEP/DXF/SVG/flexible exports complete. All physical parts and mass/CG match the unmodified 0.87.2 baseline, including both side guards.
- Three GUI checks pass: the actual Load settings action preserves values and paints correctly; invalid JSON leaves prior controls intact; detailed motor/prop/USB stack references display and hide correctly. Fresh-process cached creation completes with display triangulation prepared before assigning parts.
- Benchmark on FreeCAD 1.1.4 / Python 3.11 / OpenCASCADE 7.8.1, Linux offscreen GUI, using a three-plate frame with guards and strap outline cutouts:

| Operation | 0.87.2 | 0.88.0 |
| --- | ---: | ---: |
| Read and validate settings JSON | 0.184 s | 0.141 s |
| Populate editor from parsed settings | 0.186 s | 0.013 s |
| Create same saved design in fresh process | 22.531 s | 8.784 s |
| Update unchanged frame | 2.197 s | 0.598 s |

The 0.88.0 creation result uses a cache from an earlier successful build. New uncached designs still need exact generation. Timings are illustrative, not a guarantee for another computer or configuration. The offscreen GUI does not test a hardware OpenGL viewport or Windows installation.

- Audited all 331 visible Help control entries against the current parameter schema, choices and defaults; no retired control remains in that inventory. Corrected changed feature descriptions and rebuilt the illustrated 99-page guide and 2-page installation guide. Rendered pages and changed-page details were reviewed; all text remains inside page bounds. The requested Windows path `%APPDATA%\FreeCAD\v1-1\Mod` is retained.

# RotorForge 0.87.2 validation

- All 446 portable tests pass in isolated batches. Four new tests cover one/two straps, both guards, unchanged carbon cutouts, slots/disabled modes, and widened/tapered/filleted/custom outlines.
- Nine native FreeCAD geometry configurations pass: both plate arrangements with one/two straps, widened and tapered/filleted top plates, camera-side closure, positive clearance with separate guard strap windows, and an unrelated custom edge notch. Both guards remain valid connected solids and match the guard envelope without top-plate strap notches. No guard material occupies the removed carbon strap area.
- Both guards produce closed STL meshes in the selected basic, tapered/filleted and separate-opening cases. Strap movement, resizing and enable/disable updates keep the passages open. Saved frames, assembled guard STEP files and the complete assembly STEP preserve the geometry and expected volume.
- Three native editor/migration checks pass using an older saved frame that reproduced 138.94 cubic millimetres of guard material inside the strap openings. Updating removes that material, the editor preview renders correctly, and save/reopen preserves the clear passages.
- The illustrated 100-page Help covers 331 controls. Changed pages were rendered and visually reviewed; all text blocks remain within the page bounds. The native editor check used an offscreen platform, not a hardware OpenGL viewport.

# RotorForge 0.87.1 validation

- All 442 portable tests pass in isolated batches, including six new single-clamp tests covering role selection, thickness/grip, stack access, arm nut seats, shared standoffs and disabled configurations.

- Twelve native FreeCAD checks pass across both arm positions, with/without a keystone, shared/custom standoff mounts, hex/press-nut seats, and disabled/three-plate configurations. Each active clamp is one valid solid and contacts the arms; inactive clamp shapes are empty.
- Native save/reopen, above/below toggles, STEP volume and parts-list checks confirm only the active clamp is exported. Below-bottom stack screws mount in the bottom plate and arm screws span the single lower sandwich.
- Thirteen arm-outline regression cases pass across True X, Stretched X and Deadcat, independent/fitted roots, both positions, preview sampling, STEP roundtrips, incremental updates and saved frames.
- Three native editor checks pass: active thickness/preview controls and migration of both old upper-only and double-clamp files made with 0.87.0. Updating clears and hides the old upper solid, creates the lower clamp, moves the stack onto the bottom, and preserves the result after save/reopen.
- The 99-page Help covers 331 controls. Changed pages were rendered and visually reviewed; all text blocks remain inside the page bounds. The new root-section diagram shows the single clamp and the correct FC carrier in both arrangements.
- Native editor checks used an offscreen platform; they do not exercise a hardware OpenGL viewport. Existing projects and older bundled FCStd examples need Update frame and a fresh manufacturing export after installation.

# RotorForge 0.87.0 validation

- Thirteen native checks pass across True X, Stretched X and Deadcat, both arm mounting positions, independent and fitted roots, upper/lower clamp solids, preview sampling, STEP exports and saved-frame restoration.
- Six additional native cases pass with 14/24/36 mm roots, rounded/chamfered clamp outlines and 1 mm edge fillets.
- Focused portable checks cover trimmed ends, bolt/stack support, preview outlines and local standoff pads. Full regression runs returned successfully but did not retain a complete summary; no full-suite count is asserted for this release.
- Illustrated Help updated and visually reviewed. Install, update the frame and re-export both affected clamp plates.

# RotorForge 0.86.0 validation

- All 433 portable tests pass. Updated the startup test to compare against package metadata instead of a stale hard-coded release number.
- Fifteen native FreeCAD checks pass: both plate layouts, five elevated USB positions each, connected guard solids and closed STL meshes, single-strap slots/outline cutouts and STEP exports, and FCStd save/reopen.
- Native editor checks pass for the two-item style dropdown, one/two strap enable rules, negative single-strap positions, previews, and migration of old None settings to disabled slots.
- The illustrated Help was rebuilt and changed pages visually reviewed. Near-top USB openings continue through the top edge when remaining stock would be thinner than the wall; lower-wall and bearing-sleeve safeguards remain active.

## Previous release validation

# RotorForge 0.85.0 validation

- 429 portable tests pass, including legacy slot defaults, opening mode persistence, notch symmetry, local plate widths, mounting/web protection, USB placement, and cutout preview removal.
- 14 native FreeCAD 1.1.4 checks pass: hollow USB shells on both sides and both stack patterns; PCB seating and retained grommet contact; connected top plates in both frame layouts; STEP roundtrips; widened/tapered/FPV outlines; and FCStd restoration.
- The 19 native presentation regression checks also pass, including unchanged mass/carbon geometry and exclusion of references from manufacturing STEP.
- Native offscreen editor checks pass for mode enable rules, signed USB offsets, summary alignment coordinates, CAD-free preview interaction, per-face materials, and USB-only rebuilding of the stack reference. Offscreen rendering cannot exercise a hardware OpenGL viewport.
- Illustrated Help updated and changed pages visually reviewed. Reference models remain generic; the USB protrusion is visual and is not added to the simple stack collision envelope. Real cable clearance must be allowed when sizing guard openings.

## Previous release validation

# RotorForge 0.84.0 validation

- All 424 portable tests pass. The revised four-test strap group also passes after final preview changes, covering migration, automatic/custom positions, limits/grip conflicts and visible edge notches.
- Twenty native power/strap checks pass. FC/ESC grommets meet at all four screw positions for both supported stack patterns and three stack heights; the FC neck extends farther down than above its PCB. Upper grommet faces remain at the selected stack height.
- Detailed VTX and LiPo references are valid, have complete colour mappings, preserve nominal body envelopes and mass estimates, and rebuild independently of carbon. LiPo top/bottom placement and rotation pass. Its schematic leads extend beyond the pack body.
- One/two-strap openings on top/bottom guard edges pass for two- and three-plate frames. Both guards remain one connected solid, remove material and produce closed STL meshes using the existing conservative seam repair. Strap edits reuse carbon and the guard base.
- New flags and negative custom strap offsets survive FCStd save/reopen. Manufacturing STEP excludes the detailed power references.
- Three native GUI checks pass: all new controls and side previews work without CAD construction; materials cover every face; disabling detail restores simple VTX/LiPo references and transparency.
- The existing nineteen native presentation checks also pass, including motor/prop assemblies, stack sizes, independent rebuilds and manufacturing export exclusion.
- The updated 97-page Help describes 325 parameter controls. New images use exact reference meshes and shared diagram styles; changed pages were visually reviewed and all pages pass text-bounds checks. The original cover screenshot is unchanged.

Reference electronics and battery leads are generic presentation geometry. Their dimensions and routing must be checked against real parts; manufacturing exports contain the physical frame and printable parts only.
