"""User-selected RotorForge export outputs. No export begins before acceptance."""
try:
    from PySide import QtWidgets, QtCore
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore
    except ImportError:
        from PySide6 import QtWidgets, QtCore
from .export_options import DEFAULT_EXPORT_OPTIONS, normalize_export_options


class ExportSelectionDialog(QtWidgets.QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle('RotorForge — Export frame')
        self.setMinimumWidth(510)
        layout=QtWidgets.QVBoxLayout(self)
        description=QtWidgets.QLabel('Choose what RotorForge should export. 3D CAM solids are placed in the current FreeCAD project; the other selections create files in the destination folder.')
        description.setWordWrap(True)
        layout.addWidget(description)
        self.checks={}
        project=QtWidgets.QGroupBox('Current FreeCAD project')
        pl=QtWidgets.QVBoxLayout(project)
        self._check(pl,'cam_solids','Create / refresh 3D CAM cutting layout (carbon plates and arms)')
        self._check(pl,'remove_existing_cam_layout','Remove an earlier RotorForge CAM cutting layout')
        self.checks['remove_existing_cam_layout'].setToolTip('Only removes RotorForge-generated CAM layout objects, not the assembled frame. Existing CAM jobs using these objects may lose their references.')
        layout.addWidget(project)
        file_group=QtWidgets.QGroupBox('External files')
        fl=QtWidgets.QVBoxLayout(file_group)
        self._check(fl,'assembly_step','STEP assembly (assembled frame)')
        self._check(fl,'carbon_dxf','DXF cutting profiles (individual parts and stock sheets)')
        self._check(fl,'carbon_svg','SVG cutting profiles (individual parts and stock sheets)')
        self._check(fl,'carbon_stl','STL carbon plates and arms (individual 3D solids in CuttingProfiles)')
        self._check(fl,'carbon_step','STEP carbon plates and arms (individual 3D solids in CuttingProfiles)')
        self._check(fl,'printed_parts','Printable part STL / STEP files (TPU, camera mounts, LiPo pad)')
        self._check(fl,'reports','Frame settings, machining instructions, parts list and export reports')
        layout.addWidget(file_group)
        note=QtWidgets.QLabel('DXF / SVG contain through-cut contours. Individual STEP / STL files contain each flattened carbon part at its full thickness, including blind machining features; STL is a mesh, STEP retains CAD geometry.')
        note.setWordWrap(True);layout.addWidget(note)
        self.checks['cam_solids'].toggled.connect(self._sync)
        self._sync()
        buttons=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _check(self,layout,key,label):
        widget=QtWidgets.QCheckBox(label)
        widget.setChecked(DEFAULT_EXPORT_OPTIONS[key]);self.checks[key]=widget
        layout.addWidget(widget)

    def _sync(self,*unused):
        included=self.checks['cam_solids'].isChecked()
        self.checks['remove_existing_cam_layout'].setEnabled(not included)
        if included:self.checks['remove_existing_cam_layout'].setChecked(False)

    def choices(self):
        return normalize_export_options({key:widget.isChecked() for key,widget in self.checks.items()})

    def _accept_selection(self):
        try:self.choices()
        except (TypeError,ValueError) as exc:
            QtWidgets.QMessageBox.warning(self,'RotorForge',str(exc))
            return
        self.accept()
