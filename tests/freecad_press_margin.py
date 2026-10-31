import os
import sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge import nut_geometry as n
p=Parameters();out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];fail=[]
try:
 seat=dict(mode='M3 press nut',point=(0.,0.),z=3.,axis=1,thickness=3.,bore=3.2,depth=0.)
 original=n.seats;n.seats=lambda p,role:[seat]
 r=p.PressNutFlangeDiameter/2
 sh=Part.makeCylinder(r+1.,3).cut(Part.makeCylinder(1.6,3));assert n.apply_seats(sh,p,'MidPlate').isValid()
 try:n.apply_seats(Part.makeCylinder(r+.99,3).cut(Part.makeCylinder(1.6,3)),p,'MidPlate');raise AssertionError('0.99 mm rim was accepted')
 except ValueError:pass
 n.seats=original;checks.append('Exactly 1.00 mm flange material margin accepted; 0.99 mm rejected')
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'clearance071.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print(checks,fail)
