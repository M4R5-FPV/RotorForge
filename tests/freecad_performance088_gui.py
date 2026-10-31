"""Actual Load settings action, error preservation and reference display checks."""
import os,sys,json,traceback,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
import FreeCAD as App
from PySide import QtWidgets
from unittest.mock import patch
from dataclasses import replace
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge import document as d
from freecad.rotorforge.parameters import load_parameters
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];failures=[]
try:
 path=os.environ['ROTORFORGE_TEST_SETTINGS'];p=load_parameters(path);win=FrameDialog();warnings=[]
 with patch.object(QtWidgets.QFileDialog,'getOpenFileName',return_value=(path,'')),patch.object(QtWidgets.QMessageBox,'warning',side_effect=lambda *args:warnings.append(args[-1])):win.load()
 assert not warnings,warnings
 assert win.values()==p and win.generate.isEnabled()
 win.preview.grab().save(str(out/'LoadedSettings.png'));assert win.preview.last_error is None
 checks.append('Load settings uses current settings and draws the correct preview')
 with tempfile.TemporaryDirectory() as t:
  bad=Path(t)/'invalid.json';bad.write_text('{"schema":"wrong","units":"inch"}')
  with patch.object(QtWidgets.QFileDialog,'getOpenFileName',return_value=(str(bad),'')),patch.object(QtWidgets.QMessageBox,'warning',side_effect=lambda *args:warnings.append(args[-1])):win.load()
 assert warnings and win.values()==p
 win.close();checks.append('Invalid settings report an error and preserve existing controls')
 detailed=load_parameters(os.environ['ROTORFORGE_DETAILED_SETTINGS']);frame=d.create_frame(detailed,App.newDocument('Detailed088'))
 for role in ('MotorEnvelopes','PropellerDiscs','StackEnvelope'):
  shape=d.component_objects(frame)[role].Shape;assert not shape.isNull() and shape.isValid(),role
 d.update_frame(frame,replace(detailed,ShowReferences=False))
 for role in ('MotorEnvelopes','PropellerDiscs','StackEnvelope'):assert d.component_objects(frame)[role].Shape.isNull(),role
 checks.append('Detailed motor/prop/USB stack display and reference visibility updates work')
 App.closeDocument(frame.Document.Name)
except Exception:failures.append(traceback.format_exc())
(out/'checks.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2))
os._exit(1 if failures else 0)
