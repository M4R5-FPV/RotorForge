import sys,os,json,traceback,time
from pathlib import Path
import tempfile
base=Path(tempfile.mkdtemp(prefix='rotorforge-antenna094-'));root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
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
for plates in ('2 plates','3 plates'):
 for fit in ('Off','Plate-edge wrap','Between plates'):
  for connector in ('u.FL','MMCX','SMA'):
   p=replace(Parameters(),PlateDesign=plates,FlexSideGuards=fit!='Off',FlexGuardFitMode=fit if fit!='Off' else 'Plate-edge wrap',FlexRearAntenna=True,FlexAntennaConnector=connector,FlexAntennaHolderStyle='Side-entry clip',FlexAntennaCount='2 antennas',FlexELRSEnabled=True)
   try:
    t=time.perf_counter();s=build_shapes(p)
    for role in ('RearAntennaMount','ELRSAntennaMount'):assert s[role].isValid() and len(s[role].Solids)==1
    a=elrs_layout(p);assert a['z0']+a['height']<=a['top']+1e-6
    for role in ('BottomPlate','MidPlate','TopPlate','ElectronicsGuardLeft','ElectronicsGuardRight','RearAntennaMount'):assert overlap_volume(s['ELRSAntennaMount'],s[role])<1e-6
    save({'case':[plates,fit,connector],'ok':True,'seconds':time.perf_counter()-t})
    if plates=='3 plates' and fit=='Between plates' and connector=='u.FL':
     meshes={}
     for role in ('RearAntennaMount','ELRSAntennaMount','ElectronicsGuardLeft','ElectronicsGuardRight','Standoffs'):
      vs,fs=s[role].tessellate(.12);meshes[role]={'vertices':[list(v) for v in vs],'faces':fs}
     (base/'meshes.json').write_text(json.dumps(meshes))
   except Exception:save({'case':[plates,fit,connector],'ok':False,'error':traceback.format_exc()})
os._exit(0 if all(r['ok'] for r in results) else 1)
