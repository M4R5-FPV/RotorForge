import os
import sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets
from freecad.rotorforge.gui import FrameDialog
from freecad.rotorforge.parameters import Parameters,stack_reference_z,plate_levels,require_valid
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];fail=[]
try:
 app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([]);Gui.getMainWindow=lambda:None
 dialog=FrameDialog();p=Parameters(StackPressNuts=True,PlateDesign='2 plates',ArmBracesEnabled=True);dialog.set_values(p);dialog.refresh();assert 'VTXNutMount' not in dialog.controls;assert dialog.values().StackPressNuts
 assert 'actual 1.50 mm' in dialog.field_labels['StackMountHeight'].text()
 assert not dialog.controls['StackMountHeight'].isEnabled()
 dialog.fit_stack();q=dialog.values();require_valid(q)
 from freecad.rotorforge.hardware_layout import SIZES,metric_size
 assert plate_levels(q)['top_z'] >= stack_reference_z(q)+q.StackHeight+SIZES[metric_size(q.StackHoleDiameter)][5]+.2
 dialog.show();app.processEvents();dialog.grab().save(str(out/'Editor.png'));dialog.close();checks.append('Stack option and actual height label round-trip; Fit stack height includes upper nuts; VTX nut option removed')
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'gui071.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print(checks,fail)
