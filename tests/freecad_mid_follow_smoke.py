"""Check real mid overhang, mounting support, width changes and exports."""
from dataclasses import replace
from pathlib import Path
import importlib.util
import json
import math
import os
import sys
import tempfile
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from freecad.rotorforge.parameters import arm_layouts,plate_levels,mid_bounds,plate_holes
from freecad.rotorforge.geometry import build_shapes,carbon_roles,cylinder,profiled_plate,flat_plate_shape
from freecad.rotorforge.document import create_frame,update_frame,read_parameters
from freecad.rotorforge.exporters import export_package,profile_entities
from test_mid_follow import matched_mid

out=Path(os.environ.get('ROTORFORGE_TEST_OUTPUT',tempfile.mkdtemp(prefix='rotorforge-mid-follow-')));out.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[],'configurations':[],'examples':[],'overhang_removed_mm2':[]}
def check(ok,label):
    if not ok:raise AssertionError(label)
    report['checks'].append(label)

def footprint(shape,z,height):
    top=max((f for f in shape.Faces if abs(f.normalAt(0,0).z)>.999),key=lambda f:f.CenterOfMass.z)
    top=top.copy();top.translate(App.Vector(0,0,z-top.CenterOfMass.z))
    return top.extrude(App.Vector(0,0,height))

try:
    previous=os.environ.get('ROTORFORGE_PREVIOUS_MODULE');old_build=None
    if previous:
        path=Path(previous);spec=importlib.util.spec_from_file_location('rotorforge_previous',path/'__init__.py',submodule_search_locations=[str(path)])
        package=importlib.util.module_from_spec(spec);sys.modules[spec.name]=package;spec.loader.exec_module(package)
        from rotorforge_previous.parameters import Parameters as OldParameters
        from rotorforge_previous.geometry import build_shapes as old_build
    cases=[]
    for layout in ('True X','Stretched X','Deadcat'):
        for width in (14,24,36):
            for mode in ('Along arm','Custom coordinates'):
                cases.append((f'{layout}/{width}/{mode}',matched_mid(Layout=layout,ArmRootWidth=width,RootBoltLayout=mode)))
        for width in (14,24):
            cases.append((f'{layout}/{width}/Independent',matched_mid(Layout=layout,ArmRootWidth=width,ArmRootFit='Independent',RootExtension=8,KeystoneEnabled=False)))
        cases.append((layout+'/offset pair',matched_mid(Layout=layout,RootBolt1X=-5,RootBolt1Y=-2,RootBolt2X=5,RootBolt2Y=2)))
    cases.append(('Wider plate centres',matched_mid(BottomCentreWidth=100,MidCentreWidth=100)))
    for tag,p in cases:
        shapes=build_shapes(p);z=plate_levels(p)['mid_z'];height=p.ClampThickness
        main=profiled_plate(p,'MidPlate',p.BodyWidth,*mid_bounds(p),p.CornerRadius,z,height)
        roots=[footprint(shapes['Arm'+a['name']],z,height) for a in arm_layouts(p) if a['root'][1]>0]
        extension=shapes['MidPlate'].cut(main)
        check(extension.cut(Part.makeCompound(roots)).Volume<1e-6,tag+' zero overhang beyond physical front arms')
        for role in carbon_roles(p):check(shapes[role].isValid() and len(shapes[role].Solids)==1,tag+' one connected '+role)
        for point,radius,name in plate_holes(p,'MidPlate'):
            ring=cylinder(*point,radius+p.MinimumWeb,z,height).cut(cylinder(*point,radius,z-.1,height+.2))
            check(abs(ring.common(shapes['MidPlate']).Volume-ring.Volume)<1e-5,tag+' full bolt support '+name)
        entities=profile_entities(flat_plate_shape(shapes['MidPlate'],'MidPlate',p))
        for arm in arm_layouts(p)[:2]:
            for point in arm['bolts']:
                check(any(e[0]=='CIRCLE' and math.dist((e[1],e[2]),point)<1e-7 and abs(e[3]-p.RootHoleDiameter/2)<1e-7 for e in entities),tag+' complete aligned front bore')
        if old_build:
            old=old_build(OldParameters.from_dict(p.to_dict()))
            removed=old['MidPlate'].cut(shapes['MidPlate']).Volume/height
            check(shapes['MidPlate'].cut(old['MidPlate']).Volume<1e-6,tag+' mid only trims excess material')
            for role in carbon_roles(p):
                if role!='MidPlate':check(old[role].cut(shapes[role]).Volume+shapes[role].cut(old[role]).Volume<1e-5,tag+' other component unchanged '+role)
            before,after=old['MidPlate'].common(main),shapes['MidPlate'].common(main)
            check(before.cut(after).Volume+after.cut(before).Volume<1e-5,tag+' stack/rear body unchanged')
            report['overhang_removed_mm2'].append({'configuration':tag,'area':removed})
        report['configurations'].append(tag);print('MID FOLLOW',tag,flush=True)
    if old_build:check(any(r['area']>5 for r in report['overhang_removed_mm2']),'Previously protruding mid material is removed')
    p=matched_mid();settings=create_frame(p);doc=settings.Document;doc.UndoMode=1
    path=out/'Example_ArmMatchedMid_3_plates.FCStd';doc.saveAs(str(path));App.closeDocument(doc.Name)
    doc=App.openDocument(str(path));settings=doc.getObject('FrameParameters');doc.recompute();doc.UndoMode=1
    check(read_parameters(settings)==p,'Native arm-matched mid parameters persist')
    update_frame(settings,replace(p,ArmRootWidth=36));doc.undo();doc.recompute();check(read_parameters(settings)==p,'Undo restores width and matching mid')
    folder=Path(export_package(settings,out/'exports'));info=json.loads((folder/'ExportInfo.json').read_text())
    check(info['mid_front_tabs']['profile']=='Clipped to front arm roots','Export records matched mid tabs')
    exported=Part.read(str(folder/'FrameAssembly.step'));check(exported.isValid(),'STEP geometry reimports')
    check((folder/'CuttingProfiles/MidPlate.dxf').exists(),'Matched mid DXF included')
    App.closeDocument(doc.Name);report['examples'].append(str(path));report['status']='passed'
except Exception:
    report['status']='failed';report['error']=traceback.format_exc();print(report['error'],flush=True)
finally:
    for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
    (out/'test_report.json').write_text(json.dumps(report,indent=2));print('MID FOLLOW',report['status'],len(report['checks']),flush=True)
