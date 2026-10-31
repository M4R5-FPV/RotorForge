"""FreeCAD: vertical screw paths, digital width, native migration and exports."""
from pathlib import Path
from dataclasses import replace
import sys,os,math,json,traceback,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from freecad.rotorforge.parameters import Parameters,PLATE_DESIGNS,load_parameters
from freecad.rotorforge.fpv import camera_mounts,camera_body_centre,CAMERA_TILT_MECHANISMS
from freecad.rotorforge.geometry import build_shapes,carbon_roles,flat_plate_shape
from freecad.rotorforge.document import create_frame,update_frame,read_parameters,component_objects
from freecad.rotorforge.exporters import export_package,profile_entities

output=Path(os.environ.get('ROTORFORGE_TEST_OUTPUT',tempfile.mkdtemp(prefix='rotorforge-vertical-')))
output.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[],'export_folders':[],'freecad_version':'.'.join(App.Version()[:3])}
def check(ok,message):
    if not ok:raise AssertionError(message)
    report['checks'].append(message)

try:
    for mode in PLATE_DESIGNS:
        for mechanism in CAMERA_TILT_MECHANISMS+('Fixed','Single pivot'):
            p=Parameters(PlateDesign=mode,FPVEnabled=True,CameraWidth=22,CameraHeight=22,
                         CameraSideBoltSpacing=6.5,StandoffHeight=40,CameraTiltMax=60)
            if mechanism=='Fixed':p=replace(p,CameraMountMode='Fixed',CameraTilt=0)
            elif mechanism=='Single pivot':p=replace(p,CameraSideBoltSpacing=0)
            else:p=replace(p,CameraTiltMechanism=mechanism)
            tag=mode+'/'+mechanism;shapes=build_shapes(p)
            for role in carbon_roles(p):
                check(shapes[role].isValid() and len(shapes[role].Solids)==1,tag+': connected '+role)
            for mount in camera_mounts(p):
                shape=shapes[mount['role']];xmin,xmax=mount['plate_x'];thickness=xmax-xmin
                angles=(0,) if mechanism=='Fixed' else range(0,61,3)
                for tilt in angles:
                    cy,cz=camera_body_centre(p,tilt);a=math.radians(tilt)
                    for offset in ((0.,) if mechanism=='Single pivot' else (-3.25,3.25)):
                        y,z=cy-offset*math.sin(a),cz+offset*math.cos(a)
                        screw=Part.makeCylinder(p.CameraSideHoleDiameter/2,thickness+.2,
                            App.Vector(xmin-.1,y,z),App.Vector(1,0,0))
                        check(screw.common(shape).Volume<1e-6,tag+f': side screw clears at {tilt} degrees')
                if mechanism=='Fixed':
                    lower,upper=mount['side_holes']
                    check(abs(lower[0]-upper[0])<1e-9 and abs(upper[1]-lower[1]-6.5)<1e-9,
                          tag+': level pair is vertical with 6.5 mm pitch')
                flat=flat_plate_shape(shape,mount['role']);entities=profile_entities(flat)
                if mechanism=='Fixed':
                    circles=[e for e in entities if e[0]=='CIRCLE']
                    check(len(circles)==2 and abs(circles[0][1]-circles[1][1])<1e-7 and
                          abs(abs(circles[0][2]-circles[1][2])-6.5)<1e-7,
                          tag+': flat cutting profile retains vertical 6.5 mm pitch')
                if mechanism in CAMERA_TILT_MECHANISMS:
                    check(any(e[0]=='ARC' for e in entities),tag+': exact circular arcs in flat profile')
            settings=create_frame(p);doc=settings.Document
            folder=export_package(settings,output/'exports');report['export_folders'].append(str(folder))
            info=json.loads((folder/'ExportInfo.json').read_text())['fpv']
            check(info['camera_vertical_screw_pitch_mm']==p.CameraSideBoltSpacing,tag+': pitch in export metadata')
            check(info['camera_side_screw_pattern']==('Single pivot' if not p.CameraSideBoltSpacing else 'Vertical pair'),tag+': pattern in export metadata')
            for role in ('CameraMountLeft','CameraMountRight'):
                check((folder/'CuttingProfiles'/(role+'.dxf')).exists(),tag+': camera DXF '+role)
                check((folder/'CameraPlates'/(role+'.stl')).exists(),tag+': camera STL '+role)
            target=output/(str(len(report['export_folders']))+'.FCStd');doc.saveAs(str(target));App.closeDocument(doc.Name)
            doc=App.openDocument(str(target));settings=doc.getObject('FrameParameters');doc.recompute()
            check(settings.Status.startswith('Valid') and read_parameters(settings)==p,tag+': native reopen')
            App.closeDocument(doc.Name)
    # Restore an existing enumeration that has the earlier pivot choice saved.
    settings=create_frame(Parameters(FPVEnabled=True,StandoffHeight=40));doc=settings.Document
    settings.CameraTiltMechanism=['Dual arc slots','Front pivot + rear arc']
    settings.CameraTiltMechanism='Front pivot + rear arc'
    p=read_parameters(settings);update_frame(settings,p)
    check(settings.CameraTiltMechanism=='Upper pivot + lower arc','Existing document selects the upper pivot')
    check(settings.getEnumerationsOfProperty('CameraTiltMechanism')==list(CAMERA_TILT_MECHANISMS),'Existing document gains current choices')
    App.closeDocument(doc.Name)
    report['status']='passed'
except Exception:
    report['status']='failed';report['error']=traceback.format_exc();print(report['error'],flush=True)
finally:
    for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
    (output/'test_report.json').write_text(json.dumps(report,indent=2))
    print('ROTORFORGE VERTICAL CAMERA',report['status'],len(report['checks']),flush=True)
