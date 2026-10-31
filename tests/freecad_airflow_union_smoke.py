"""Exact new profiles, overlapping unions, retained clearances and manufacturing."""
from pathlib import Path
from dataclasses import replace
import importlib.util,json,math,os,sys,traceback
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)]
import FreeCAD as App
import Part
from freecad.rotorforge.cutouts import CUTOUT_TYPES,PATTERN_DEFAULTS,encode_patterns
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.airflow_geometry import profile_tool,apply_cutouts
from freecad.rotorforge.geometry import build_shapes,carbon_roles,flat_plate_shape
from freecad.rotorforge.document import create_frame,read_parameters,update_frame
from freecad.rotorforge.exporters import profile_entities,export_package,write_dxf,write_svg

out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[],'shapes':[],'exports':[]}
def check(ok,label):
    if not ok:raise AssertionError(label)
    report['checks'].append(label)
def pattern(**kw):return dict(PATTERN_DEFAULTS,**kw)
def rejected(items,label,plate=None):
    try:apply_cutouts(replace(Parameters(),CutoutPatterns=encode_patterns(items)),'TopPlate',plate or blank)
    except ValueError:check(True,label)
    else:raise AssertionError(label)
try:
    blank=Part.makeBox(80,100,2,App.Vector(-40,-50,0))
    for shape in CUTOUT_TYPES:
        for angle in (0,37):
            item=pattern(shape=shape,width=8,length=12,rotation=angle)
            p=Parameters(CutoutPatterns=encode_patterns([item]));actual=apply_cutouts(p,'TopPlate',blank)
            tool=profile_tool(item,-1,4)
            check(actual.isValid() and len(actual.Solids)==1,shape+'/'+str(angle)+': connected')
            tolerance=max(1e-6,tool.Volume*2e-6) if shape=='Ellipse' else 1e-6
            check(abs(blank.Volume-actual.Volume-tool.Volume/2)<tolerance,shape+'/'+str(angle)+': removed volume within kernel tolerance')
            entities=profile_entities(actual)
            check(bool(entities),shape+'/'+str(angle)+': cutting profile supported')
            if shape=='Ellipse':check(any(e[0]=='ELLIPSE' for e in entities),shape+'/'+str(angle)+': analytic ellipse')
        report['shapes'].append(shape)
    combos=[
        [pattern(shape='Slot',width=4,length=18),pattern(shape='Slot',width=4,length=18,rotation=90)],
        [pattern(shape='Ellipse',width=8,length=14,rotation=31),pattern(shape='Diamond',width=12,length=8,x=2)],
        [pattern(shape='Circle',width=6,columns=4,pitch_x=3)],
        [pattern(shape='Circle',width=10),pattern(shape='Circle',width=4)],
        [pattern(shape='Triangle',width=12,length=14),pattern(shape='Chevron',width=12,length=14,rotation=180)],
        [pattern(shape='Ellipse',width=9,length=14,x=-2,rotation=30),pattern(shape='Ellipse',width=10,length=6,x=2,rotation=-25)],
        [pattern(shape='Circle',width=6,x=-5),pattern(shape='Circle',width=6,x=5),pattern(shape='Rectangle',width=8,length=3)],
        [pattern(shape='Rectangle',width=10,length=10),pattern(shape='Rectangle',width=10,length=10)],
        [pattern(shape='Ellipse',width=8,length=12,rotation=37)]]
    from freecad.rotorforge.cutouts import pattern_instances
    for index,items in enumerate(combos):
        p=Parameters(CutoutPatterns=encode_patterns(items));actual=apply_cutouts(p,'TopPlate',blank)
        tools=[profile_tool(i,0,2) for item in items for i in pattern_instances(item)]
        union=tools[0].multiFuse(tools[1:]).removeSplitter() if len(tools)>1 else tools[0];expected=blank.cut(union).removeSplitter()
        check(actual.isValid() and len(actual.Solids)==1,f'Union {index}: connected')
        check(actual.cut(expected).Volume+expected.cut(actual).Volume<1e-6,f'Union {index}: exact boolean union')
        reversed_result=apply_cutouts(replace(p,CutoutPatterns=encode_patterns(list(reversed(items)))),'TopPlate',blank)
        check(actual.cut(reversed_result).Volume+reversed_result.cut(actual).Volume<1e-6,f'Union {index}: independent of order')
        entities=profile_entities(actual)
        write_dxf(out/f'Union_{index}.dxf',[('TopPlate',entities)])
        write_svg(out/f'Union_{index}.svg',[('TopPlate',entities)],80,100)
        actual.exportBrep(str(out/f'Union_{index}.brep'))
        report['exports'].append(f'Union_{index}')
    for width,pitch,label in [(4,4,'Tangent cuts rejected'),(4,4.5,'Thin web between separate cuts rejected')]:
        rejected([pattern(shape='Circle',width=width,columns=2,pitch_x=pitch)],label)
    rejected([pattern(shape='Rectangle',width=80,length=6)],'Outer edge crossing rejected')
    rejected([pattern(shape='Circle',width=5,x=37)],'Outer edge web protected')
    rejected([pattern(shape='Circle',width=4,x=17,y=46)],'Standoff footprint protected')
    hole=Part.makeCylinder(2,4,App.Vector(0,0,-1));with_hole=blank.cut(hole)
    rejected([pattern(shape='Rectangle',width=4,length=10)],'Existing hole protected',with_hole)
    ring=[pattern(shape='Circle',width=7,x=8*math.cos(i*math.pi/4),y=8*math.sin(i*math.pi/4)) for i in range(8)]
    rejected(ring,'Union that isolates a carbon island rejected')
    items=[pattern(shape='Slot',width=4,length=16),pattern(shape='Slot',width=4,length=16,rotation=90),
           pattern(shape='Ellipse',width=8,length=10,y=28),pattern(shape='Diamond',width=7,length=12,y=28,rotation=20),
           pattern(shape='Circle',width=5,y=-28,columns=3,pitch_x=3)]
    for design in ('3 plates','2 plates'):
        p=Parameters(PlateDesign=design,CutoutPatterns=encode_patterns(items));shapes=build_shapes(p)
        check(all(shapes[r].isValid() and len(shapes[r].Solids)==1 for r in carbon_roles(p)),design+': full frame valid')
        settings=create_frame(p);doc=settings.Document;doc.UndoMode=1
        path=out/('Example_CombinedAirflow_'+design[0]+'_plates.FCStd');doc.saveAs(str(path));App.closeDocument(doc.Name)
        doc=App.openDocument(str(path));settings=doc.getObject('FrameParameters');doc.recompute();doc.UndoMode=1
        check(read_parameters(settings)==p and settings.Status.startswith('Valid'),design+': native restore')
        update_frame(settings,replace(p,CutoutPatterns='[]'));doc.undo();doc.recompute()
        check(read_parameters(settings)==p,design+': Undo restores combined patterns')
        folder=export_package(settings,out/'exports');info=json.loads((folder/'ExportInfo.json').read_text())
        check(info['airflow_patterns']==json.loads(p.CutoutPatterns),design+': exact pattern metadata')
        check(Part.read(str(folder/'FrameAssembly.step')).isValid(),design+': STEP reimport')
        report['exports'].append(str(folder));App.closeDocument(doc.Name)
    camera=Parameters(FPVEnabled=True,CameraSideBoltSpacing=8,CameraTiltMax=55,StandoffHeight=35,CameraTiltMechanism='Upper pivot + lower arc')
    camitems=[pattern(role='CameraMountLeft',shape='Ellipse',width=1.5,length=2,x=-5,y=5),pattern(role='CameraMountLeft',shape='Ellipse',width=1.5,length=2,x=-5,y=5.4)]
    check(build_shapes(replace(camera,CutoutPatterns=encode_patterns(camitems)))['CameraMountLeft'].isValid(),'Camera-local overlapping ellipses valid')
    # Earlier non-overlapping patterns keep their exact carbon geometry.
    oldpath=Path(os.environ['ROTORFORGE_PREVIOUS_SOURCE'])
    spec=importlib.util.spec_from_file_location('rotorforge_previous',oldpath/'__init__.py',submodule_search_locations=[str(oldpath)])
    pkg=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pkg;spec.loader.exec_module(pkg)
    from rotorforge_previous.parameters import Parameters as OldParameters
    from rotorforge_previous.geometry import build_shapes as old_build
    for shape in CUTOUT_TYPES[:4]:
        p=Parameters(CutoutPatterns=encode_patterns([pattern(shape=shape,width=4,length=8,columns=2,pitch_x=12)]))
        data=p.to_dict();data['CutoutPatterns']=json.dumps([{k:v for k,v in item.items() if k!='mode'} for item in json.loads(p.CutoutPatterns)])
        now=build_shapes(p);old=old_build(OldParameters.from_dict(data))
        for role in carbon_roles(p):check(now[role].cut(old[role]).Volume+old[role].cut(now[role]).Volume<1e-6,shape+': unchanged original '+role)
    report['status']='passed'
except Exception:report.update(status='failed',error=traceback.format_exc());print(report['error'],flush=True)
finally:
    for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
    (out/'test_report.json').write_text(json.dumps(report,indent=2));print('AIRFLOW UNION',report['status'],len(report['checks']),flush=True)
