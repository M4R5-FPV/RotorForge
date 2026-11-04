import sys,os,json,traceback,time
from pathlib import Path
import tempfile
base=Path(tempfile.mkdtemp(prefix='rotorforge-sma-'));root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
import FreeCAD as App,Part
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes,overlap_volume
from freecad.rotorforge.antenna_layout import antenna_layout
from freecad.rotorforge.dependency_cache import COMPONENTS
results=[]
for connector in ('SMA','RP-SMA','u.FL','MMCX'):
 for count in ('1 antenna','2 antennas'):
  for tilt in (0.,60.,90.):
   p=replace(Parameters(),FlexRearAntenna=True,FlexSideGuards=True,FlexAntennaConnector=connector,FlexAntennaCount=count,FlexAntennaTilt=tilt,FlexAntennaHolderOffset=12.)
   try:
    t=time.perf_counter();s=build_shapes(p);m=s['RearAntennaMount'];a=antenna_layout(p)
    assert m.isValid() and len(m.Solids)==1
    if a['bulkhead']:
     for holder in a['holders']:
      start=App.Vector(*holder['start']);axis=App.Vector(*holder['axis'])
      hole=Part.makeCylinder(a['bore']/2-.01,a['length']+20,start-axis*10,axis)
      assert overlap_volume(m,hole)<1e-6,'Blocked pigtail bore'
      for pos in (start-axis*3,start+axis*(a['length']+.01)):
       washer=Part.makeCylinder(4.99,2.99,pos,axis)
       assert overlap_volume(m,washer)<1e-6,'Blocked nut/washer access'
    results.append({'case':[connector,count,tilt],'ok':True,'seconds':time.perf_counter()-t,'events':[e for e in COMPONENTS.events if e['role'] in ('RearAntennaMount','ElectronicsGuardLeft','ElectronicsGuardRight')]})
    if connector=='SMA' and count=='2 antennas' and tilt==60:
     vs,fs=m.tessellate(.12);(base/'sma_mesh.json').write_text(json.dumps({'vertices':[list(v) for v in vs],'faces':fs}));m.exportStep(str(base/'sma.step'))
   except Exception:results.append({'case':[connector,count,tilt],'ok':False,'error':traceback.format_exc()})
   (base/'sma_checks.json').write_text(json.dumps(results,indent=2))
os._exit(0 if all(r['ok'] for r in results) else 1)
