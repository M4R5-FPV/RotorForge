# Editor navigation — v0.89.5

Main sections run from top to bottom on the left. Hover over an icon for its name. Subsections keep text buttons and wrap into extra rows instead of hiding behind arrows; TPU fits two rows at the tested 950 × 650 window size. Display scaling and platform fonts can require more space. Maximize/Restore window remains available.

Find a control is now beside Create/Update frame, Maximize and Cancel at the bottom. Search still opens the correct section and brings the control into view.

## Main preview

- Scroll the wheel to zoom toward the pointer, anywhere in the preview.
- Drag with the left or middle mouse button to pan.
- Double-click or click Fit view to reset.
- Zoom works in the overall frame view and individual/all-part views. Changing preview mode resets the view; dimension edits keep it.

This changes the editor preview, not FreeCAD's separate 3D viewport or frame generation speed.

## Airflow / outlines

Opening this subsection gives it the editor's full width. The ordinary frame preview returns when you leave it.

- Left: capacity, pattern search/filter, saved patterns, removal and How to use cutouts.
- Centre: part, cutout type/mode, dimensions, position, pattern grid, rotation and enabled state; Add, Apply, Discard, Copy to other camera side and Check plate cuts in CAD.
- Right: cutout preview, pattern numbers, Zoom to selected, Fit plate and status messages.

Drag the column dividers to adjust their widths. The outer page fits without scrolling at 950 × 650 in the tested Linux Qt environment; the saved-pattern list scrolls as needed for longer lists. A scroll fallback remains for larger fonts, display scaling or long status messages so controls cannot become inaccessible. Existing selection, overlapping-pattern cycling, validation and unapplied-change protection are retained.

The included Help PDF remains the reference for all settings and cutout behavior; its navigation instructions describe the current arrangement.


## Saving reference hardware — v0.89.6

Create or refresh your chosen screws and retaining hardware in Hardware references, then use Save settings in the frame editor. The JSON now stores the chosen hardware groups, nominal engagement, retaining-hardware option and visibility. Press-nut geometry continues to follow Hardware > Nut retention.

After loading this JSON, click Create frame (or Update frame). The reference hardware is restored automatically; it does not require a separate Create/Refresh command. Hidden references remain hidden. Loading settings or cancelling the editor does not change the current document. Saving a loaded design before building also retains its hardware preferences. Exported FrameParameters.json includes the same information.

Older settings JSON files lack this information. For each older design, create/refresh the desired reference hardware once and save the settings again with v0.89.6. Existing FreeCAD document saving remains supported. The Help PDF now describes this workflow.
