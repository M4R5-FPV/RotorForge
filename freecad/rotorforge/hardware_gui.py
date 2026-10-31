"""Hardware display controls. Nut seats are editable under Hardware / Nut retention."""
import FreeCAD as App,FreeCADGui as Gui
from PySide import QtWidgets,QtCore
from . import hardware_refs as refs
from .hardware_layout import HARDWARE_GROUPS
class HardwareDialog(QtWidgets.QDialog):
 def __init__(self,frame):
  super().__init__(Gui.getMainWindow());self.frame=frame;self.setWindowTitle('RotorForge — Hardware references');self.resize(540,420)
  l=QtWidgets.QVBoxLayout(self);label=QtWidgets.QLabel('Simplified low-profile round button-head screws. Retention settings and real plate cuts are on Hardware → Nut retention in the frame editor. Optional FC press nuts sit below the raised stack; conventional upper nuts stay above it. VTX screws have no retaining nuts.');label.setWordWrap(True);l.addWidget(label)
  self.o=refs.options(frame);self.groups={}
  for name in HARDWARE_GROUPS:
   w=QtWidgets.QCheckBox(name);w.setChecked(name in self.o['groups']);self.groups[name]=w;l.addWidget(w)
  self.nuts=QtWidgets.QCheckBox('Show arm retaining hardware');self.nuts.setChecked(self.o['nuts']);l.addWidget(self.nuts)
  form=QtWidgets.QFormLayout();self.eng=QtWidgets.QDoubleSpinBox();self.eng.setRange(.5,10);self.eng.setValue(self.o['engagement']);self.eng.setSuffix(' mm');form.addRow('Nominal threaded engagement',self.eng);l.addLayout(form)
  self.status=QtWidgets.QLabel('References are excluded from manufacturing exports and do not add a second weight estimate.');self.status.setWordWrap(True);l.addWidget(self.status)
  for title,fn in [('Create / refresh references',self.refresh),('Hide references',lambda:self.visible(False)),('Show references',lambda:self.visible(True)),('Close',self.close)]:
   b=QtWidgets.QPushButton(title);b.clicked.connect(lambda checked=False,fn=fn:self.run(fn));l.addWidget(b)
 def run(self,fn):
  try:fn()
  except Exception as e:QtWidgets.QMessageBox.warning(self,'RotorForge',str(e))
 def visible(self,on):
  refs.set_visible(self.frame,on)
  if on:refs.sync_refs(self.frame)
 def refresh(self):
  self.o.update(groups=[n for n,w in self.groups.items() if w.isChecked()],nuts=self.nuts.isChecked(),engagement=self.eng.value());s=refs.refresh(self.frame,self.o);self.status.setText(f'{len(s)} nominal button-head fasteners. Verify real screw lengths, head clearance and purchased inserts.')
class HardwareCommand:
 def GetResources(self):
  from .paths import icon_path
  return dict(Pixmap=icon_path(),MenuText='Hardware references…',ToolTip='Show low-profile round screws and joint retention hardware')
 def IsActive(self):return App.ActiveDocument is not None
 def Activated(self):
  from .document import find_parameters
  try:
   dialog=HardwareDialog(find_parameters(Gui.Selection.getSelection()))
   dialog.exec() if hasattr(dialog,'exec') else dialog.exec_()
  except Exception as e:QtWidgets.QMessageBox.warning(Gui.getMainWindow(),'RotorForge',str(e))
