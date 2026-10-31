"""Run in FreeCAD/FreeCADCmd. Set ROTORFORGE_TEST_OUTPUT for a fixed output folder."""
from dataclasses import replace
from itertools import combinations
import csv
import json
import os
from pathlib import Path
import sys
import tempfile
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from rotorforge import __version__
from freecad.rotorforge.parameters import Parameters, PLATE_DESIGNS, plate_levels, STANDOFF_COUNTS, standoff_layouts
from tests.frame_cases import FRAME_CASES, FPV_CASES
from freecad.rotorforge.geometry import carbon_roles, build_shapes
from freecad.rotorforge.document import create_frame, update_frame, read_parameters, component_objects
from freecad.rotorforge.exporters import export_package, profile_entities

output = Path(os.environ.get("ROTORFORGE_TEST_OUTPUT", tempfile.mkdtemp(prefix="rotorforge-test-")))
output.mkdir(parents=True, exist_ok=True)
report = {"freecad_version": ".".join(App.Version()[:3]), "checks": [], "status": "running", "export_folders": []}


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    report["checks"].append(message)


def top_face(shape):
    return max((face for face in shape.Faces if abs(face.normalAt(0,0).z) > .999999), key=lambda f:f.CenterOfMass.z)


try:
    for name, preset in FRAME_CASES.items():
        for mode in PLATE_DESIGNS:
            p = replace(preset, PlateDesign=mode)
            roles, shapes = carbon_roles(p), build_shapes(p)
            tag = name + " / " + mode
            check(all(shapes[r].isValid() and len(shapes[r].Solids)==1 for r in roles),tag+": connected carbon solids")
            check(len(shapes["Standoffs"].Solids)==4,tag+": four standoffs")
            check(len(top_face(shapes["BottomPlate"]).Wires)==13+sum(s["mount"]!="Mid plate" for s in standoff_layouts(p)),tag+": 16 bottom holes")
            check(len(top_face(shapes["TopPlate"]).Wires)==9,tag+": top holes and strap slots")
            check(all(len(top_face(shapes[r]).Wires)==8 for r in roles if r.startswith("Arm")),tag+": arm holes")
            for a,b in combinations(roles,2):
                check(shapes[a].common(shapes[b]).Volume<1e-6,tag+": no carbon overlap "+a+"/"+b)
            for role in roles:
                check(shapes[role].common(shapes["Standoffs"]).Volume<1e-6,tag+": standoffs clear "+role)
                check(len(profile_entities(shapes[role]))==len(top_face(shapes[role]).Edges),tag+": cutting edges "+role)
            levels=plate_levels(p)
            check(abs(shapes["TopPlate"].BoundBox.ZMin-levels["top_z"])<1e-8,tag+": top height")
            check(all(abs(s.BoundBox.ZMax-levels["top_z"])<1e-8 for s in shapes["Standoffs"].Solids),tag+": standoffs meet top")
            if mode=="3 plates":
                check(len(top_face(shapes["MidPlate"]).Wires)==15,tag+": 14 mid holes")
                check(shapes["BottomPlate"].BoundBox.YMax>max(shapes["MidPlate"].BoundBox.YMax,shapes["TopPlate"].BoundBox.YMax),tag+": projecting bottom nose")
                check(not shapes["MidPlate"].isInside(App.Vector(0,35,levels["mid_z"]+p.ClampThickness/2),1e-7,True),tag+": mid main body stops at stack")
                check({round(s.BoundBox.ZLength,5) for s in shapes["Standoffs"].Solids}=={p.StandoffHeight,p.StandoffHeight+p.ArmThickness+p.ClampThickness},tag+": front/rear standoff lengths")
            else:
                check(shapes["MidPlate"].isNull() and len(roles)==6,tag+": no mid solid")
                check(abs(shapes["ArmFrontRight"].BoundBox.ZMax)<1e-8,tag+": arms below bottom")
            if p.Layout=='Stretched X':
                bore = next(e for e in profile_entities(shapes['ArmFrontRight']) if e[0]=='CIRCLE' and abs(e[3]-p.MotorCenterDiameter/2)<1e-7)
                check(bore[1]>bore[2],tag+': actual motor bore is spread laterally')
    for name, preset in FRAME_CASES.items():
        for mode in PLATE_DESIGNS:
            for count, number in zip(STANDOFF_COUNTS[1:], (6, 8)):
                p=replace(preset,PlateDesign=mode,StandoffCount=count)
                shapes=build_shapes(p)
                roles=carbon_roles(p)
                tag=f'{name} / {mode} / {number} standoffs'
                stands=standoff_layouts(p)
                check(all(shapes[r].isValid() and len(shapes[r].Solids)==1 for r in roles),tag+': connected carbon solids')
                check(shapes['Standoffs'].isValid() and len(shapes['Standoffs'].Solids)==number,tag+': selected hardware count')
                check(len(top_face(shapes['BottomPlate']).Wires)==13+sum(s['mount']!='Mid plate' for s in stands),tag+': matching bottom holes')
                check(len(top_face(shapes['TopPlate']).Wires)==5+number,tag+': matching top holes')
                if mode=='3 plates':
                    mid_count=sum(s['mount']=='Mid plate' for s in stands)
                    check(len(top_face(shapes['MidPlate']).Wires)==13+mid_count,tag+': only mid-mounted standoffs pierce the mid')
                for role in roles:
                    check(shapes[role].common(shapes['Standoffs']).Volume<1e-6,tag+': hardware clear of '+role)
                for a,b in combinations(shapes['Standoffs'].Solids,2):
                    check(a.common(b).Volume<1e-6,tag+': standoffs do not overlap')
                for solid in shapes['Standoffs'].Solids:
                    c=solid.CenterOfMass
                    stand=min(stands,key=lambda s:(s['point'][0]-c.x)**2+(s['point'][1]-c.y)**2)
                    check(abs(solid.BoundBox.ZMin-stand['base'])<1e-7 and
                          abs(solid.BoundBox.ZLength-stand['length'])<1e-7 and
                          abs(solid.BoundBox.ZMax-plate_levels(p)['top_z'])<1e-7,tag+': correct mounting face and level top')
    # A positive-Y pair can still sit on the mid body: mounting must use its outline.
    p=replace(Parameters(),StandoffCount=STANDOFF_COUNTS[1],StandoffPair3Y=5)
    shapes=build_shapes(p)
    check(len(top_face(shapes['MidPlate']).Wires)==17,'Positive-Y extra pair has matching mid holes')
    check(all(s['mount']=='Mid plate' and s['length']==25 for s in standoff_layouts(p) if s['position']=='Pair 3'),
          'Positive-Y extra pair uses the mid mounting face')
    for height in (22,25,30):
        for mode in PLATE_DESIGNS:
            p=replace(Parameters(),PlateDesign=mode,StandoffHeight=height)
            shapes=build_shapes(p)
            top=shapes['TopPlate'].BoundBox.ZMin
            for solid in shapes['Standoffs'].Solids:
                front=solid.CenterOfMass.y>0
                expected_base=p.BottomThickness if front or mode=='2 plates' else p.BottomThickness+p.ArmThickness+p.ClampThickness
                expected_length=height+(p.ArmThickness+p.ClampThickness if front and mode=='3 plates' else 0)
                check(abs(solid.BoundBox.ZMin-expected_base)<1e-7,f'{mode} / {height} mm: correct standoff mounting face')
                check(abs(solid.BoundBox.ZLength-expected_length)<1e-7,f'{mode} / {height} mm: actual standoff length')
                check(abs(solid.BoundBox.ZMax-top)<1e-7,f'{mode} / {height} mm: level top supported')
    doc=App.newDocument("RotorForgeSmoke02")
    doc.UndoMode=1
    settings=create_frame(doc=doc)
    parts=component_objects(settings)
    mass_three=settings.CarbonMassGrams
    update_frame(settings,replace(Parameters(),PlateDesign="2 plates"))
    check(parts["MidPlate"].Shape.isNull(),"Switch existing frame to two plates")
    check(settings.CarbonMassGrams<mass_three,"Mass excludes inactive mid and front extension")
    doc.undo(); doc.recompute()
    check(read_parameters(settings).PlateDesign=="3 plates" and not parts["MidPlate"].Shape.isNull(),"Undo restores three plates")
    for mode in PLATE_DESIGNS:
        update_frame(settings,replace(Parameters(),PlateDesign=mode))
        folder=export_package(settings,output)
        report["export_folders"].append(str(folder))
        roles=carbon_roles(read_parameters(settings))
        loaded=Part.read(str(folder/"FrameAssembly.step"))
        check(loaded.isValid() and len(loaded.Solids)==len(roles)+4,mode+": STEP physical solid count")
        check((folder/"CuttingProfiles/MidPlate.dxf").exists()==(mode=="3 plates"),mode+": correct mid profile presence")
        check(len(list((folder/"CuttingProfiles").glob("*.dxf")))==len(roles)+1,mode+": cutting file count")
        rows=list(csv.DictReader((folder/"PartsList.csv").open()))
        stands={r["Part"]:float(r["Thickness_mm"]) for r in rows if "standoffs" in r["Part"]}
        check(stands==({"Front standoffs":33,"Rear standoffs":25} if mode=="3 plates" else {"Front standoffs":25,"Rear standoffs":25}),mode+": parts list standoff lengths")
        path=output/("Example_"+mode.replace(" ","_")+".FCStd")
        doc.saveAs(str(path))
        name=settings.Name
        App.closeDocument(doc.Name)
        doc=App.openDocument(str(path))
        settings=doc.getObject(name)
        doc.recompute()
        check(settings.Status.startswith("Valid") and read_parameters(settings).PlateDesign==mode,mode+": native reopen")
        settings.Wheelbase=270; doc.recompute()
        check(settings.Status.startswith("Valid"),mode+": reopened parameters remain editable")
    settings.Wheelbase=100; doc.recompute()
    check(settings.Status.startswith("Invalid") and component_objects(settings)["BottomPlate"].Shape.isNull(),"Invalid edit clears obsolete solids")
    update_frame(settings,Parameters())
    check(settings.Status.startswith("Valid"),"Corrected inputs rebuild geometry")
    for mode,height in (('3 plates',22),('2 plates',30)):
        update_frame(settings,replace(Parameters(),PlateDesign=mode,StandoffHeight=height))
        folder=export_package(settings,output)
        report['export_folders'].append(str(folder))
        rows=list(csv.DictReader((folder/'PartsList.csv').open()))
        actual={r['Part']:float(r['Thickness_mm']) for r in rows if 'standoffs' in r['Part']}
        expected_front=height+(8 if mode=='3 plates' else 0)
        check(actual=={'Front standoffs':expected_front,'Rear standoffs':height},f'{mode}: selected hardware sizes in parts list')
    for mode in PLATE_DESIGNS:
        for count, number in zip(STANDOFF_COUNTS[1:],(6,8)):
            p=replace(Parameters(),PlateDesign=mode,StandoffCount=count)
            update_frame(settings,p)
            check(read_parameters(settings)==p,f'{mode} / {number}: native properties retain requested signed positions')
            check(len(component_objects(settings)['Standoffs'].Shape.Solids)==number,f'{mode}: editor update to {number} standoffs')
            folder=export_package(settings,output)
            report['export_folders'].append(str(folder))
            loaded=Part.read(str(folder/'FrameAssembly.step'))
            check(loaded.isValid() and len(loaded.Solids)==len(carbon_roles(p))+number,f'{mode} / {number}: STEP hardware count')
            rows=list(csv.DictReader((folder/'PartsList.csv').open()))
            hardware=[r for r in rows if 'standoffs' in r['Part']]
            check(sum(int(r['Quantity']) for r in hardware)==number,f'{mode} / {number}: BOM quantities')
            check({(r['Part'].removesuffix(' standoffs'),float(r['Thickness_mm'])) for r in hardware}==
                  {(s['position'],s['length']) for s in standoff_layouts(p)},f'{mode} / {number}: BOM pair lengths')
            info=json.loads((folder/'ExportInfo.json').read_text())
            check(info['standoff_count']==number and len(info['standoffs'])==number,f'{mode} / {number}: export metadata')
            path=output/f'Example_{mode.replace(" ","_")}_{number}_standoffs.FCStd'
            doc.saveAs(str(path))
            name=settings.Name
            App.closeDocument(doc.Name)
            doc=App.openDocument(str(path))
            settings=doc.getObject(name)
            doc.recompute()
            check(read_parameters(settings)==p and len(component_objects(settings)['Standoffs'].Shape.Solids)==number,
                  f'{mode} / {number}: native count and pair coordinates persist')
    legacy=App.openDocument(str(Path(__file__).resolve().parent/"fixtures/Legacy_0.1.FCStd"))
    old=legacy.getObject("FrameParameters")
    legacy.recompute()
    update_frame(old,read_parameters(old))
    check("StandoffCount" in old.PropertiesList and old.GeneratorVersion==__version__ and
          read_parameters(old).StandoffCount==STANDOFF_COUNTS[0],"Legacy document gains new parameters and retains four standoffs")
    check(old.Status.startswith("Valid") and not legacy.getObject("ClampPlate").Shape.isNull(),"Legacy clamp regenerates as mid")
    update_frame(old,replace(read_parameters(old),PlateDesign="2 plates"))
    check(legacy.getObject("ClampPlate").Shape.isNull(),"Legacy frame switches to two plates")
    update_frame(old,replace(read_parameters(old),PlateDesign="3 plates"))
    check(not legacy.getObject("ClampPlate").Shape.isNull(),"Legacy frame switches back to three plates")
    report["status"]="passed"
except Exception:
    report["status"]="failed"
    report["error"]=traceback.format_exc()
    raise
finally:
    (output/"test_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ROTORFORGE TESTS",report["status"],len(report["checks"]),str(output),flush=True)
