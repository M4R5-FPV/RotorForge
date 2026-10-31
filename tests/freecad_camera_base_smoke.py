"""FreeCAD: extended camera seating, captured slots, screw paths and exports."""
from dataclasses import replace
from pathlib import Path
import json
import math
import os
import sys
import tempfile
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
import Part
from rotorforge import __version__
from freecad.rotorforge.parameters import Parameters,PLATE_DESIGNS,load_parameters,top_bounds,bottom_bounds
from freecad.rotorforge.fpv import CAMERA_TILT_MECHANISMS,camera_mounts,camera_body_centre,camera_screw_offsets
from freecad.rotorforge.geometry import build_shapes,carbon_roles,physical_roles,flat_plate_shape
from freecad.rotorforge.document import create_frame,update_frame,read_parameters
from freecad.rotorforge.exporters import export_package,profile_entities

output=Path(os.environ.get('ROTORFORGE_TEST_OUTPUT',tempfile.mkdtemp(prefix='rotorforge-camera-base-')))
output.mkdir(parents=True,exist_ok=True)
report={'status':'running','checks':[],'export_folders':[],'freecad_version':'.'.join(App.Version()[:3])}


def check(ok,message):
    if not ok:raise AssertionError(message)
    report['checks'].append(message)


try:
    for design in PLATE_DESIGNS:
        for mechanism in CAMERA_TILT_MECHANISMS+('Fixed','Single pivot'):
            base=Parameters(PlateDesign=design,FPVEnabled=True,StandoffHeight=35,
                            TopReachMode='Custom',TopFrontReach=60,TopRearReach=100)
            if mechanism=='Fixed':base=replace(base,CameraMountMode='Fixed')
            elif mechanism=='Single pivot':base=replace(base,CameraSideBoltSpacing=0)
            else:base=replace(base,CameraTiltMechanism=mechanism)
            p=replace(base,CameraBaseMode='Custom',CameraBaseFrontExtension=6,CameraBaseRearExtension=10)
            tag=design+'/'+mechanism;shapes=build_shapes(p);baseline=build_shapes(base)
            for role in carbon_roles(p):
                check(shapes[role].isValid() and len(shapes[role].Solids)==1,tag+': connected '+role)
            check(abs(shapes['TopPlate'].BoundBox.YMax-60)<1e-7,tag+': short top reach is exact')
            check(shapes['TopPlate'].isSame(baseline['TopPlate']) or
                  shapes['TopPlate'].common(baseline['TopPlate']).Volume>=shapes['TopPlate'].Volume-1e-6,
                  tag+': top attachment geometry unchanged')
            for mount in camera_mounts(p):
                role=mount['role'];shape=shapes[role];xmin,xmax=mount['plate_x'];thickness=xmax-xmin
                check(mount['bottom_length']==36 and mount['top_length']==20,tag+': independent contact lengths')
                for key,plate,z,depth in (('tabs_y','BottomPlate',0,p.BottomThickness),
                                         ('top_tabs_y','TopPlate',mount['z1'],p.TopThickness)):
                    for y in mount[key]:
                        tongue=Part.makeBox(thickness,p.CameraTabLength,depth,App.Vector(xmin,y-p.CameraTabLength/2,z))
                        check(abs(tongue.common(shape).Volume-tongue.Volume)<1e-6,tag+': retained tongue '+key)
                        check(tongue.common(shapes[plate]).Volume<1e-6,tag+': matching receiving slot '+plate)
                        for x in (xmin-p.CameraTabClearance-.2,xmax+p.CameraTabClearance+.2):
                            check(shapes[plate].isInside(App.Vector(x,y,z+depth/2),1e-7,True),tag+': material beside slot '+plate)
                # A tiny interference move measures contact against the actual
                # slotted deck, rather than only comparing outline dimensions.
                seated=shape.copy();seated.translate(App.Vector(0,0,-.01))
                original=baseline[role].copy();original.translate(App.Vector(0,0,-.01))
                contact=seated.common(shapes['BottomPlate']).Volume
                old_contact=original.common(baseline['BottomPlate']).Volume
                check(contact>old_contact+.3,tag+': longer actual seating area '+role)
                check(shape.common(shapes['BottomPlate']).Volume<1e-6,tag+': no bottom interference '+role)
                check(shape.common(shapes['TopPlate']).Volume<1e-6,tag+': no top interference '+role)
                for other in physical_roles(p):
                    if other!=role:check(shape.common(shapes[other]).Volume<1e-6,tag+': clears '+other)
                angles=(p.CameraTilt,) if p.CameraMountMode=='Fixed' else range(0,46,5)
                for angle in angles:
                    cy,cz=camera_body_centre(p,angle)
                    for dy,dz in camera_screw_offsets(p,angle):
                        screw=Part.makeCylinder(p.CameraSideHoleDiameter/2,thickness+.2,
                                                App.Vector(xmin-.1,cy+dy,cz+dz),App.Vector(1,0,0))
                        check(screw.common(shape).Volume<1e-6,tag+': screw clears at '+str(angle))
                flat=flat_plate_shape(shape,role)
                check(abs(flat.BoundBox.ZLength-p.CameraBracketThickness)<1e-7,tag+': correct flat stock '+role)
                check(bool(profile_entities(flat)),tag+': actual flat cutting contours '+role)
            settings=create_frame(p);doc=settings.Document;folder=export_package(settings,output/'exports')
            report['export_folders'].append(str(folder))
            info=json.loads((folder/'ExportInfo.json').read_text())
            check(info['generator_version']==__version__,tag+': current export version')
            check(info['fpv']['camera_lower_attachment_mode']=='Custom',tag+': base mode metadata')
            check(info['fpv']['camera_lower_extensions_mm']=={'front':6,'rear':10},tag+': extension metadata')
            check(info['fpv']['camera_side_plates'][0]['bottom_length']==36,tag+': contact length metadata')
            for role in ('CameraMountLeft','CameraMountRight'):
                for extension in ('dxf','svg'):
                    check((folder/'CuttingProfiles'/(role+'.'+extension)).stat().st_size>100,tag+': cutting file '+role+extension)
                check((folder/'CameraPlates'/(role+'.step')).stat().st_size>1000,tag+': STEP '+role)
            path=output/('CameraBase_'+design[0]+'_'+str(len(report['export_folders']))+'.FCStd')
            doc.saveAs(str(path));App.closeDocument(doc.Name);doc=App.openDocument(str(path))
            settings=doc.getObject('FrameParameters');doc.recompute();doc.UndoMode=1
            check(read_parameters(settings)==p,tag+': all dimensions persist on reopen')
            check(settings.Status.startswith('Valid'),tag+': valid reopened document')
            update_frame(settings,replace(p,CameraBaseMode='Automatic'))
            check(read_parameters(settings).CameraBaseFrontExtension==6,tag+': extensions retained in Automatic')
            check(camera_mounts(read_parameters(settings))[0]['bottom_length']==20,tag+': Automatic restores original base')
            doc.undo();doc.recompute();check(read_parameters(settings)==p,tag+': Undo restores custom base')
            App.closeDocument(doc.Name)
    report['status']='passed'
except Exception:
    report['status']='failed';report['error']=traceback.format_exc();print(report['error'],flush=True)
finally:
    for doc in list(App.listDocuments().values()):App.closeDocument(doc.Name)
    (output/'test_report.json').write_text(json.dumps(report,indent=2))
    print('CAMERA BASE',report['status'],len(report['checks']),flush=True)
