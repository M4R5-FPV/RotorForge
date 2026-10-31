"""CAD checks for touching roots, joint gaps, compact keys and service access."""
from dataclasses import replace
from itertools import combinations
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
from freecad.rotorforge.parameters import (Parameters, arm_layouts, plate_levels, stack_holes,
    keystone_active, stack_mounting_role, require_valid)
from freecad.rotorforge.geometry import build_shapes, carbon_roles, physical_roles, cylinder, flat_plate_shape
from freecad.rotorforge.document import create_frame, update_frame, read_parameters
from freecad.rotorforge.exporters import export_package, profile_entities

output=Path(os.environ.get('ROTORFORGE_TEST_OUTPUT',tempfile.mkdtemp(prefix='rotorforge-fitted-')))
output.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[],'configurations':[],'export_folders':[],'examples':[]}

def check(condition,label):
    if not condition:raise AssertionError(label)
    report['checks'].append(label)

def base(**changes):
    return replace(Parameters(ArmRootFit='Fitted miters',ArmRootY=8,RootInset=17,
        RootExtension=20,RootBoltSpacing=8,StandoffHeight=35,Wheelbase=270),**changes)

def verify(p,tag,contacts=True):
    s=build_shapes(p);z=plate_levels(p)['arm_z']+p.ArmThickness/2
    arms=arm_layouts(p);roles=['Arm'+a['name'] for a in arms]
    for role in carbon_roles(p):check(s[role].isValid() and len(s[role].Solids)==1,tag+': connected '+role)
    for a,b in combinations(roles,2):check(s[a].common(s[b]).Volume<1e-6,tag+': no overlap '+a+'/'+b)
    if contacts:
        for a,b in zip(roles,roles[1:]+roles[:1]):
            check(abs(s[a].distToShape(s[b])[0]-p.ArmJointClearance)<1e-6,tag+': complete joint gap '+a+'/'+b)
            if p.ArmJointClearance==0:
                axis='X' if ('Right' in a)!=('Right' in b) else 'Y'
                faces_a=[f for f in s[a].Faces if getattr(f.BoundBox,axis+'Length')<1e-7 and abs(getattr(f.CenterOfMass,axis.lower()))<1e-7]
                faces_b=[f for f in s[b].Faces if getattr(f.BoundBox,axis+'Length')<1e-7 and abs(getattr(f.CenterOfMass,axis.lower()))<1e-7]
                area=sum(f.common(g).Area for f in faces_a for g in faces_b)
                check(area>p.ArmThickness,tag+': finite touching face '+a+'/'+b)
    for arm in arms:
        entities=profile_entities(flat_plate_shape(s['Arm'+arm['name']],'Arm'+arm['name'],p))
        for point in arm['bolts']:
            check(any(e[0]=='CIRCLE' and math.dist((e[1],e[2]),point)<1e-7 and abs(e[3]-p.RootHoleDiameter/2)<1e-7 for e in entities),tag+': complete root bore '+arm['name'])
        for point in arm['motor_holes']:
            check(any(e[0]=='CIRCLE' and math.dist((e[1],e[2]),point)<1e-7 and abs(e[3]-p.MotorHoleDiameter/2)<1e-7 for e in entities),tag+': unchanged motor bore '+arm['name'])
    if keystone_active(p):
        key=s['ArmKeystone']
        for role in roles:check(abs(key.distToShape(s[role])[0]-p.KeystoneClearance)<1e-5,tag+': key seats '+role)
        check(abs(key.BoundBox.XLength-p.KeystoneWidth)<1e-6 and abs(key.BoundBox.YLength-p.KeystoneLength)<1e-6,tag+': exact compact key dimensions')
    if p.PlateDesign=='3 plates' or p.ArmBracesEnabled:
        carrier=stack_mounting_role(p);low=min(s[r].BoundBox.ZMin for r in carbon_roles(p));top=s[carrier].BoundBox.ZMin
        for point in stack_holes(p):
            passage=cylinder(*point,p.StackAccessDiameter/2,low-.1,top-low+.1)
            for role in carbon_roles(p):
                if role!=carrier:check(s[role].common(passage).Volume<1e-6,tag+': full stack service path '+role)
    report['configurations'].append(tag)
    return s

try:
    configurations=[]
    for layout in ('True X','Stretched X','Deadcat'):
        for design,position in [('3 plates','Below bottom plate'),('2 plates','Below bottom plate'),('2 plates','Above bottom plate')]:
            for key in (False,True):
                for gap in (0.,.2):
                    p=base(Layout=layout,PlateDesign=design,TwoPlateArmPosition=position,
                        ArmBracesEnabled=design=='2 plates',KeystoneEnabled=key,ArmJointClearance=gap)
                    tag='/'.join(map(str,(layout,design,position,key,gap)))
                    verify(p,tag);configurations.append(p)
    for shape in ('Round','Rounded square','Chamfered square','Four-lobe','Tapered nose','Arrowhead'):
        verify(base(MotorPadShape=shape,KeystoneEnabled=True),'Motor outline '+shape)
    asymmetric=base(BottomCentreWidth=58,CentreSectionY=8,CentreSectionLength=8,CentreShoulderLength=4,
        StackSpacing=30.5,MidFrontReach=26,KeystoneEnabled=True)
    verify(asymmetric,'Unequal front/rear root widths',False)
    access=base(BodyWidth=100,ArmRootY=35,RootInset=15,RootExtension=50,KeystoneWidth=70,KeystoneLength=70,
        KeystoneEnabled=True,MidFrontReach=30)
    verify(access,'Keystone with open stack access',False)
    for design in ('3 plates','2 plates'):
        shared=base(BodyWidth=70,TopWidth=70,ArmRootY=25,RootInset=15,RootExtension=50,KeystoneEnabled=True,
            PlateDesign=design,ArmBracesEnabled=design=='2 plates',StandoffCount='8 (4 pairs)',
            StandoffFrontMount='Arm outer hole',StandoffRearMount='Arm outer hole',
            StandoffPair3Mount='Front arm inner hole',StandoffPair4Mount='Rear arm inner hole')
        verify(shared,design+' eight shared arm standoffs',False)
    for changes,label in [({'RootInset':22},'Unsafe root bolt edge'),({'KeystoneEnabled':True,'KeystoneWidth':20,'KeystoneLength':20},'Unsafe key pocket'),
                          ({'KeystoneEnabled':True,'ArmRootY':30,'RootInset':10,'RootExtension':8},'Key does not reach all arms')]:
        try:build_shapes(base(**changes))
        except ValueError:check(True,label+' rejected')
        else:raise AssertionError(label+' was accepted')
    for p in [base(KeystoneEnabled=True),base(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,ArmJointClearance=.2)]:
        settings=create_frame(p)
        folder=Path(export_package(settings,output/'exports'));report['export_folders'].append(str(folder))
        info=json.loads((folder/'ExportInfo.json').read_text())
        check(info['arm_mounting']['root_fit']=='Fitted miters','Export records the fitted joints')
        check(info['arm_mounting']['keystone']['profile']=='Compact diamond','Export records the compact key')
        assembly=Part.read(str(folder/'FrameAssembly.step'))
        check(assembly.isValid() and len(assembly.Solids)==len(physical_roles(p))-1+len(__import__('rotorforge.parameters',fromlist=['standoff_holes']).standoff_holes(p)), 'STEP assembly reimports with every physical part')
        check((folder/'CuttingProfiles/ArmFrontRight.dxf').exists(),'Fitted arm cutting file is included')
        App.closeDocument(settings.Document.Name)
    examples=[('Example_FittedRoots_3_plates.FCStd',base()),
              ('Example_CompactKeystone_3_plates.FCStd',base(KeystoneEnabled=True)),
              ('Example_CompactKeystone_Below_2_plates.FCStd',base(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,ArmJointClearance=.15))]
    for name,p in examples:
        settings=create_frame(p);doc=settings.Document;doc.UndoMode=1
        filename=output/name;doc.recompute();doc.saveAs(str(filename));App.closeDocument(doc.Name)
        doc=App.openDocument(str(filename));settings=doc.getObject('FrameParameters');doc.recompute();doc.UndoMode=1
        check(read_parameters(settings)==p,name+': native parameters persist')
        check(settings.getEnumerationsOfProperty('ArmRootFit')==['Independent','Fitted miters'],name+': native enum choices')
        update_frame(settings,replace(p,ArmJointClearance=.25));doc.undo();doc.recompute()
        check(read_parameters(settings)==p,name+': Undo restores the joint fit')
        App.closeDocument(doc.Name);report['examples'].append(str(filename))
    earlier=Path(__file__).resolve().parents[1]/'examples/Example_FourLobe_MotorEnds.FCStd'
    doc=App.openDocument(str(earlier));settings=doc.getObject('FrameParameters');doc.recompute();doc.UndoMode=1
    original=read_parameters(settings)
    check(original.ArmRootFit=='Independent','Earlier native document retains independent roots')
    check(settings.getEnumerationsOfProperty('ArmRootFit')==['Independent','Fitted miters'],'Earlier native document gains the root-fit choices')
    update_frame(settings,base(MotorPadShape='Four-lobe',KeystoneEnabled=True))
    check(read_parameters(settings).ArmRootFit=='Fitted miters','Earlier document can switch to fitted roots')
    doc.undo();doc.recompute();check(read_parameters(settings)==original,'Undo restores the earlier root layout')
    App.closeDocument(doc.Name)
    previous_root=os.environ.get('ROTORFORGE_PREVIOUS_MODULE')
    if previous_root:
        path=Path(previous_root)
        spec=importlib.util.spec_from_file_location('rotorforge_previous',path/'__init__.py',submodule_search_locations=[str(path)])
        package=importlib.util.module_from_spec(spec);sys.modules[spec.name]=package;spec.loader.exec_module(package)
        from rotorforge_previous.parameters import Parameters as OldParameters
        from rotorforge_previous.geometry import build_shapes as old_build
        cases=[Parameters(),Parameters(KeystoneEnabled=True)]
        cases += [Parameters(PlateDesign='2 plates',ArmBracesEnabled=True,KeystoneEnabled=True,TwoPlateArmPosition=position)
                  for position in ('Below bottom plate','Above bottom plate')]
        cases += [Parameters(Layout=layout,Wheelbase=270) for layout in ('Stretched X','Deadcat')]
        for i,p in enumerate(cases):
            data=p.to_dict()
            for name in ('ArmRootFit','ArmJointClearance','KeystoneWidth','KeystoneLength'):data.pop(name)
            before=old_build(OldParameters.from_dict(data));after=build_shapes(p)
            for role in carbon_roles(p):
                check(before[role].cut(after[role]).Volume+after[role].cut(before[role]).Volume<1e-5,'Independent geometry unchanged '+str(i)+'/'+role)
    report['status']='passed'
except Exception:
    report['status']='failed';report['error']=traceback.format_exc();print(report['error'],flush=True)
finally:
    for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
    (output/'test_report.json').write_text(json.dumps(report,indent=2))
    print('FITTED ROOTS',report['status'],len(report['checks']),flush=True)
