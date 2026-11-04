"""ELRS T-antenna controls, dimensions in mm."""
FIELDS={
 'FlexELRSEnabled':(False,'ELRS T-antenna mount','Separate TPU mount on the rear upper standoffs below the side-guard grips.'),
 'FlexELRSBarShape':('Curved','ELRS bar shape','Connecting bar joining both rear grips.',('Curved','Triangle','Rectangle')),
 'FlexELRSReach':(20.,'ELRS rearward reach','Distance rearward from the standoff row to the antenna axis. Moves both hooks and the bar together.'),
 'FlexELRSHeightOffset':(0.,'ELRS height above plate','Raise the mount from the lower carrier: bottom plate in two-plate frames, mid plate in three-plate frames. The grip must remain below the guard grip.'),
 'FlexELRSGripHeight':(6.,'ELRS grip height','Requested grip height, capped to the available space below the guard grips. At least 4 mm must remain.'),
 'FlexELRSGripWall':(3.,'ELRS grip wall','Radial TPU around the standoff hole. Minimum 1.2 mm.'),
 'FlexELRSStandoffBore':(0.,'ELRS standoff hole','Finished hole diameter. Zero uses standoff diameter plus fit allowance. Must not be smaller than the standoff.'),
 'FlexELRSFit':(.2,'ELRS standoff fit allowance','Diametral clearance when ELRS standoff hole is zero.'),
 'FlexELRSBarWidth':(6.,'ELRS bar width','Fore/aft connecting rib width, at least 4 mm.'),
 'FlexELRSHookSpacing':(16.,'ELRS hook spacing','Centre-to-centre spacing across the two hooks. Leave room between them for the T junction and coax.'),
 'FlexELRSAntennaDiameter':(3.,'ELRS antenna diameter','Finished bore for the insulated horizontal antenna housing. Measure your T-antenna; this is not a connector diameter.'),
 'FlexELRSHookWidth':(4.,'ELRS hook width','Contact length of each hook along the horizontal antenna.'),
 'FlexELRSHookWall':(1.5,'ELRS hook wall','Radial TPU around the antenna. Minimum 1.2 mm.'),
 'FlexELRSRetainingLip':(.4,'ELRS retaining lip','Per-side retention. Upward opening equals antenna diameter minus twice this lip. Snap in from above or slide in along the antenna axis; test the fit in your TPU.')}

FIELDS.update({'FlexELRSHookReach':(0.,'ELRS hook rearward offset','Additional rearward movement of the hooks only. The main bar and grips stay in place; two ribs connect the hooks to the bar.'),'FlexELRSPassThroughDiameter':(3.,'ELRS antenna pass-through diameter','Front-to-back hole through the centre of the connecting bar for the T-antenna centre leg/coax. Measure the part that must pass through. Zero disables it; retain at least 1 mm above and below the hole.')})

FIELDS.update({'FlexELRSGuardGap': (0.0, 'ELRS to side-guard gap', 'Vertical gap above the ELRS grips. Zero gives direct contact with side-guard grips.')})
