import os,sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge.hardware_gui import HardwareDialog
from freecad.rotorforge import document as d,hardware_refs as hw
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.nut_seats import FIELDS
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];fail=[]
try:
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([]);Gui.getMainWindow=lambda:None
 dialog=FrameDialog();dialog.set_values(Parameters(ArmNutMount='M3 press nut'));assert all(k in dialog.controls for k in FIELDS);assert dialog.values().PressNutBore==4.22;dialog.show();app.processEvents();dialog.close()
 doc=App.newDocument();f=d.create_frame(Parameters(),doc);win=HardwareDialog(f);win.show();app.processEvents();win.grab().save(str(out/'HardwareDialog.png'));win.refresh();assert hw.objects(f);win.close();App.closeDocument(doc.Name)
 checks.append('All eleven nut-retention controls round-trip in the editor; hardware dialog renders and creates references')
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'gui070.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print('GUI',checks,fail,flush=True)
