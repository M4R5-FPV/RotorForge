"""Restore suppression must not disable actual parametric edits or recovery."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge import geometry,document
from freecad.rotorforge.parameters import Parameters
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];failures=[]
try:
 p=Parameters();d=App.newDocument('Dependency061');settings=document.create_frame(p,d);path=out/'Dependency061.FCStd';d.saveAs(str(path));App.closeDocument(d.Name)
 geometry._build.cache_clear();d=App.openDocument(str(path));settings=d.getObject('FrameParameters');before=d.getObject('ArmFrontRight').Shape.Volume
 misses=geometry._build.cache_info().misses;settings.Wheelbase=p.Wheelbase+10;d.recompute()
 assert str(settings.Status).startswith('Valid');assert settings.Proxy._restored_signature is None
 assert geometry._build.cache_info().misses-misses==1,'Dependent objects repeated the native builder'
 assert d.getObject('ArmFrontRight').Shape.Volume>before
 checks.append('Direct parameter edit after restore performs one real native build and changes the arm')
 original=geometry._build;attempts=[]
 def fail(signature):attempts.append(signature);raise ValueError('Controlled native failure')
 geometry._build=fail;settings.ArmThickness=p.ArmThickness+1;d.recompute()
 assert len(attempts)==1,len(attempts);assert str(settings.Status).startswith('Invalid')
 geometry._build=original;settings.ArmThickness=p.ArmThickness;d.recompute()
 assert str(settings.Status).startswith('Valid');assert d.getObject('ArmFrontRight').Shape.Volume>0
 checks.append('Failed direct edit attempts geometry once across dependents and recovers on correction')
 App.closeDocument(d.Name)
except Exception:failures.append(dict(name='Dependency/recovery',error=traceback.format_exc()));traceback.print_exc()
(out/'dependencies061.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
