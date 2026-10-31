"""An extra bottom-mounted pair retains its bearing material after rear trimming."""
from pathlib import Path
import json,os,sys,traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_mid_follow import matched_mid
from freecad.rotorforge.parameters import standoff_layouts,plate_levels
from freecad.rotorforge.geometry import build_shapes,carbon_roles,cylinder
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[]}
def check(ok,label):
    if not ok:raise AssertionError(label)
    report['checks'].append(label)
try:
    p=matched_mid(BottomCentreWidth=140,RootInset=50,TopWidth=140,StandoffCount='6 (3 pairs)',StandoffPair3Width=104,StandoffPair3Y=-41,BottomBodyRearReach=46)
    shapes=build_shapes(p)
    for role in carbon_roles(p):check(shapes[role].isValid() and len(shapes[role].Solids)==1,'Connected '+role)
    stands=[s for s in standoff_layouts(p) if s['point'][1]==-41]
    check(len(stands)==2 and all(s['mount']=='Bottom plate' for s in stands),'Extra rearward pair mounts to bottom')
    for s in stands:
        pt=s['point'];ring=cylinder(*pt,p.StandoffDiameter/2+p.MinimumWeb,0,p.BottomThickness).cut(cylinder(*pt,p.StandoffHoleDiameter/2,-.1,p.BottomThickness+.2))
        check(abs(ring.common(shapes['BottomPlate']).Volume-ring.Volume)<1e-5,'Full standoff bearing material '+str(pt))
        check(s['base']==p.BottomThickness,'Standoff seats on bottom '+str(pt))
        check(s['base']+s['length']==plate_levels(p)['top_z'],'Standoff reaches top '+str(pt))
    report['status']='passed'
except Exception:report.update(status='failed',error=traceback.format_exc());print(report['error'],flush=True)
finally:
    (out/'test_report.json').write_text(json.dumps(report,indent=2));print('BOTTOM STANDOFF',report['status'],len(report['checks']),flush=True)
