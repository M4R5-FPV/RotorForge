import sys,os,json,traceback,time
from pathlib import Path
import tempfile
base=Path(tempfile.mkdtemp(prefix='rotorforge-flush0910-'));root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
import FreeCAD as App,Part
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes,overlap_volume
from freecad.rotorforge.elrs_layout import elrs_layout
from freecad.rotorforge.antenna_layout import antenna_layout
from freecad.rotorforge.dependency_cache import COMPONENTS
results=[]
def save(x):
 results.append(x);(base/'cad.json').write_text(json.dumps(results,indent=2))
from freecad.rotorforge.mount_bands import rear_mount_seats
from freecad.rotorforge.parameters import plate_levels
out=[]
for plates in ('2 plates','3 plates'):
 for fit in ('Plate-edge wrap','Between plates'):
  for vtx,elrs,gap in ((True,False,0.),(False,True,0.),(True,True,0.),(True,True,.5)):
   p=replace(Parameters(),PlateDesign=plates,FlexSideGuards=True,FlexGuardFitMode=fit,FlexRearAntenna=vtx,FlexELRSEnabled=elrs,FlexAntennaTopGap=gap,FlexAntennaGuardGap=gap,FlexELRSGuardGap=gap,FlexELRSHeightOffset=gap)
   try:
    s=build_shapes(p);a=rear_mount_seats(p);basez=plate_levels(p)['deck_z'];top=plate_levels(p)['top_z']
    def plane(z):return Part.makePlane(1000,1000,App.Vector(-500,-500,z))
    def contact(a,b,z):return a.common(plane(z)).common(b.common(plane(z))).Area
    if vtx:
     m=s['RearAntennaMount'];assert m.common(plane(top-gap)).Area>1
     if not gap:assert contact(m,s['TopPlate'],top)>1,'Missing top contact'
    if elrs:
     m=s['ELRSAntennaMount'];assert m.common(plane(basez+gap)).Area>1
     if not gap:assert contact(m,s['MidPlate' if plates=='3 plates' else 'BottomPlate'],basez)>1,'Missing lower contact'
    for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
     g=s[role]
     if vtx and not gap:assert contact(g,s['RearAntennaMount'],a['guard_high'])>1,'Missing VTX/guard contact'
     if elrs and not gap:assert contact(g,s['ELRSAntennaMount'],a['guard_low'])>1,'Missing ELRS/guard contact'
     if not vtx:assert contact(g,s['TopPlate'],top)>1,'Missing guard/top contact'
     if not elrs:assert contact(g,s['MidPlate' if plates=='3 plates' else 'BottomPlate'],basez)>1,'Missing guard/lower contact'
     if gap:
      assert g.common(plane(a['guard_low'])).Area>1 and g.common(plane(a['guard_high'])).Area>1
    out.append({'case':[plates,fit,vtx,elrs,gap],'ok':True})
   except Exception:out.append({'case':[plates,fit,vtx,elrs,gap],'ok':False,'error':traceback.format_exc()})
   (base/'contact.json').write_text(json.dumps(out,indent=2))
os._exit(0 if all(x['ok'] for x in out) else 1)
