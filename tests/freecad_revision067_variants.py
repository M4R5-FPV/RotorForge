"""Cross-check representative arm locks, plate modes and finishing paths."""
import sys,os,json,traceback,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.parameters import load_parameters
root=Path(__file__).resolve().parents[1];out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];failures=[]
spec=importlib.util.spec_from_file_location('freecad.rotorforge._baseline067variants',os.environ['ROTORFORGE_BASELINE_SOURCE']);baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
names=['Example_ClampKeystone_Above_2_plates.FCStd','Example_ClampKeystone_Below_2_plates.FCStd','Example_CompactKeystone_3_plates.FCStd','Example_ArmFillets.json','Example_CombinedAirflow_3_plates.FCStd']
for name in names:
 try:
  path=root/'examples'/name
  if path.suffix=='.json':p=load_parameters(str(path))
  else:
   doc=App.openDocument(str(path));settings=next(o for o in doc.Objects if 'GeneratorVersion' in o.PropertiesList);p=d.read_parameters(settings);App.closeDocument(doc.Name)
  g.clear_build_caches();current=g.build_shapes(p);old=baseline.build_shapes(p)
  for role,x in current.items():
   y=old[role];assert x.isNull()==y.isNull(),role
   if not x.isNull():assert x.isValid() and len(x.Solids)==len(y.Solids) and abs(x.Volume-y.Volume)<1e-5 and x.cut(y).Volume<1e-5 and y.cut(x).Volume<1e-5,role
  checks.append(name);print('PASS',name,flush=True)
 except Exception:failures.append(dict(name=name,error=traceback.format_exc()));traceback.print_exc()
(out/'variants067.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
