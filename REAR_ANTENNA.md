# Rear VTX antenna mount - v0.90.10

Integrated TPU mount with one or two antennas, 0-90 degree elevation, dual outward yaw, curved/triangle/rectangle connecting bars, adjustable grips and holder offset.

SMA/RP-SMA use rounded bulkhead tabs. Insert a pigtail through the mounting hole and clamp with its nut and washer. Set SMA bulkhead tab thickness to match the available thread (2.4 mm default, 2-5 mm range). Both faces clear 10 mm diameter hardware; measure the actual connector, washer and nut. Sleeve length is saved but inactive in these modes.

u.FL/MMCX retain the measured antenna stem in a tube, not the small PCB connector. Holder length extends outward independently of the grip seat. Positive holder offset moves rearward. Real plate and guard intersections remain blocked.

The mount is original geometry informed by commercial DFR pigtail mounts and TBS bulkhead retention. It is not physically test-printed. The complete antenna, pigtail/coax and connector hardware are not modeled: check cable bend radius and assembly clearance.

Performance: curved bar uses a single profile; unchanged guards and numerical layouts are reused. Exact CAD checks remain on Create/Update and explicit analysis, not on every editor change.

## Side-entry stem holders

For u.FL/MMCX, choose Closed tube or Side-entry clip. Clips open toward frame front through the full axial thickness at the clip, without an additional rear brace and have a flared entry; the per-side retaining lip narrows the opening. Closed tube is the default for existing settings. The bore holds the antenna stem, not the PCB connector. Tune the fit in the intended TPU.

## ELRS T-antenna mount

TPU > ELRS antenna independently enables a separate lower mount. Its grips fit between the rear side-guard grips and the lower carrier (mid in three-plate frames). Adjust height, grip dimensions and hole fit. Choose curved, triangle or rectangle bar shape and set rearward reach.

Two upward-opening hooks hold the horizontal insulated antenna housing. Adjust diameter, hook spacing, width, wall and retaining lip. Keep the centre junction and coax between the hooks. Full antenna/coax envelopes and snap forces are not simulated; physically test retention and prop clearance.

References: https://brain3d.com/products/elrs-ep1-horizontal-antenna-mount-1 and https://rotorvillage.ca/rvs-dual-direct-tpu-antenna-mount-o4-avatar/ . Original geometry; no downloaded STL reuse.

ELRS hook rearward offset moves only the hooks, extending two rounded square-section ribs from the fixed bar. ELRS antenna pass-through diameter sets the centre front-to-back hole for the T junction leg/coax; zero disables it. Keep at least 1 mm above and below the hole.

At zero tilt, a single horizontal rearward VTX stem has no front-facing radial direction, so its side opening points upward; its axial end already faces front.

Hook connector width and height both follow the smaller of hook width and available grip height. Rounded edges soften their transitions. Clip mouths clear the holder wall while preserving the remote carrier.

Hook extension ends are embedded in the hook body, giving a full-section joint instead of a small rounded contact. The hook bore and top entry are cut after fusion.
