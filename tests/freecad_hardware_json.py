"""Run in FreeCAD GUI to exercise the actual Save/Load/Create path."""
import FreeCAD as App
import sys,os,json,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
checks=[];report={}
try:
 from freecad.rotorforge.parameters import Parameters
 from freecad.rotorforge import document as doc,hardware_refs as hw
 from freecad.rotorforge.gui import FrameDialog,QtWidgets
 from freecad.rotorforge.exporters import export_package
 p=Parameters(ArmNutMount='M3 press nut',StackPressNuts=True)
 f=doc.create_frame(p,App.newDocument('HardwareJSON'))
 opts=dict(groups=['Arm bolts','Motor screws','Stack hardware'],nuts=True,engagement=4.5)
 hw.refresh(f,opts)
 hidden=hw.objects(f)[0];hidden.ViewObject.Visibility=False
 expected=hw.saved_preferences(f)
 path=out/'frame.json'
 QtWidgets.QFileDialog.getSaveFileName=lambda *a,**k:(str(path),'')
 QtWidgets.QFileDialog.getOpenFileName=lambda *a,**k:(str(path),'')
 def fail_message(*a,**k):raise AssertionError(str(a))
 QtWidgets.QMessageBox.warning=fail_message
 win=FrameDialog(f);win.save();win.reject()
 raw=json.loads(path.read_text());assert raw['hardware_references']==expected
 checks.append('Save settings includes chosen groups, engagement, nuts and individual visibility')
 win=FrameDialog();before=len(f.Document.Objects);win.load()
 assert len(f.Document.Objects)==before
 assert win.values()==p and win._loaded_hardware_preferences==expected
 win.save();assert json.loads(path.read_text())['hardware_references']==expected
 checks.append('Load is non-mutating and Save before Create preserves loaded preferences')
 win.apply();new=win.settings
 assert new!=f and doc.read_parameters(new)==p
 assert hw.saved_preferences(new)==expected
 assert hw.objects(new) and all(not o.Shape.isNull() and o.Shape.isValid() for o in hw.objects(new))
 assert any(s.get('press') and s['nut'] for s in hw.hardware_layout(p,hw.options(new)))
 checks.append('Create from JSON restores valid screws and press nuts without manual refresh')
 hw.set_visible(new,False);expected=hw.saved_preferences(new)
 win=FrameDialog(new);win.save();win.reject()
 win=FrameDialog();win.load();win.apply();hiddenframe=win.settings
 assert hw.objects(hiddenframe) and all(not o.ViewObject.Visibility for o in hw.objects(hiddenframe))
 assert hw.saved_preferences(hiddenframe)==expected
 checks.append('Explicitly hidden hardware remains hidden after loading and creating')
 folder=export_package(new,out/'export')
 assert json.loads((folder/'FrameParameters.json').read_text())['hardware_references']==expected
 checks.append('Exported FrameParameters.json includes the same hardware preferences')
 off=hw.saved_preferences(None);hw.restore_preferences(new,off)
 assert not hw.objects(new) and not hw.existing_settings(new).ReferencesCreated
 checks.append('Explicit no-hardware preference removes old references on an existing frame')
 raw.pop('hardware_references');path.write_text(json.dumps(raw))
 win=FrameDialog();win.load();assert win._loaded_hardware_preferences is None
 win.apply();assert not hw.objects(win.settings)
 checks.append('Legacy JSON continues to build without opting into hardware')
 report={'status':'passed','checks':checks,'FreeCAD':App.Version()}
except Exception:report={'status':'failed','checks':checks,'error':traceback.format_exc()}
(out/'hardware_json.json').write_text(json.dumps(report,indent=2))
os._exit(0 if report['status']=='passed' else 1)
