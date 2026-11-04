"""Wrapping subsection buttons: no hidden tabs or horizontal arrow navigation."""
try:
    from PySide import QtCore, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtWidgets
    except ImportError:
        from PySide6 import QtCore, QtWidgets


class WrappingSections(QtWidgets.QWidget):
    currentChanged = QtCore.Signal(int)

    def __init__(self):
        super().__init__()
        self.buttons = []
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.header = QtWidgets.QWidget()
        self.grid = QtWidgets.QGridLayout(self.header)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(3)
        layout.addWidget(self.header)
        self.stack = QtWidgets.QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.stack.currentChanged.connect(self._changed)

    def addTab(self, widget, text):
        return self.insertTab(self.count(), widget, text)

    def insertTab(self, index, widget, text):
        button = QtWidgets.QPushButton(text)
        button.setCheckable(True)
        button.setAutoDefault(False)
        button.setStyleSheet('QPushButton { padding: 3px 8px; } QPushButton:checked { background: #c7e8df; color: #163b32; }')
        button.clicked.connect(lambda checked=False, page=widget: self.setCurrentWidget(page))
        self.buttons.insert(index, button)
        self.stack.insertWidget(index, widget)
        self._changed(self.currentIndex())
        self.reflow()
        return index

    def reflow(self):
        while self.grid.count():
            self.grid.takeAt(0)
        width = max(100, self.width())
        rows = [[]]
        used = 0
        for button in self.buttons:
            size = button.sizeHint().width()
            if rows[-1] and used + size + 3 > width:
                rows.append([])
                used = 0
            rows[-1].append(button)
            used += size + 3
        # Each row has its own layout so long labels do not stretch columns
        # in other rows. Reuse buttons; discard only old row containers.
        for child in getattr(self, '_rows', []):
            child.deleteLater()
        self._rows = []
        for row_index, buttons in enumerate(rows):
            row = QtWidgets.QWidget(self.header)
            line = QtWidgets.QHBoxLayout(row)
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(3)
            for button in buttons:
                button.setParent(row)
                line.addWidget(button)
                button.show()
            line.addStretch()
            self.grid.addWidget(row, row_index, 0)
            self._rows.append(row)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()

    def _changed(self, index):
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)
        self.currentChanged.emit(index)

    def count(self): return self.stack.count()
    def currentIndex(self): return self.stack.currentIndex()
    def currentWidget(self): return self.stack.currentWidget()
    def widget(self, index): return self.stack.widget(index)
    def indexOf(self, widget): return self.stack.indexOf(widget)
    def tabText(self, index): return self.buttons[index].text()
    def setCurrentIndex(self, index): self.stack.setCurrentIndex(index)
    def setCurrentWidget(self, widget): self.stack.setCurrentWidget(widget)


class CategorySections(QtWidgets.QWidget):
    """Vertical icon rail with upright artwork and accessible section names."""
    currentChanged = QtCore.Signal(int)

    def __init__(self):
        super().__init__()
        self.buttons = []
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        rail = QtWidgets.QWidget()
        self.rail_layout = QtWidgets.QVBoxLayout(rail)
        self.rail_layout.setContentsMargins(0, 0, 0, 0)
        self.rail_layout.setSpacing(3)
        self.rail_layout.addStretch()
        layout.addWidget(rail)
        self.stack = QtWidgets.QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.stack.currentChanged.connect(self._changed)

    def addTab(self, widget, icon, text):
        button = QtWidgets.QToolButton()
        button.setIcon(icon)
        button.setIconSize(QtCore.QSize(32, 32))
        button.setFixedSize(46, 46)
        button.setCheckable(True)
        button.setStyleSheet('QToolButton:checked { background: #c7e8df; border: 2px solid #36a98b; border-radius: 4px; }')
        button.clicked.connect(lambda checked=False, page=widget: self.setCurrentWidget(page))
        self.buttons.append(button)
        self.rail_layout.insertWidget(len(self.buttons)-1, button)
        index = self.stack.addWidget(widget)
        self._changed(self.currentIndex())
        return index

    def _changed(self, index):
        for i, button in enumerate(self.buttons):button.setChecked(i == index)
        self.currentChanged.emit(index)

    def setTabToolTip(self, index, text):
        self.buttons[index].setToolTip(text)
        self.buttons[index].setAccessibleName(text)
    def setTabWhatsThis(self, index, text):self.buttons[index].setWhatsThis(text)
    def tabToolTip(self, index):return self.buttons[index].toolTip()
    def tabIcon(self, index):return self.buttons[index].icon()
    def tabText(self, index):return ''
    def currentIndex(self):return self.stack.currentIndex()
    def currentWidget(self):return self.stack.currentWidget()
    def setCurrentIndex(self, index):self.stack.setCurrentIndex(index)
    def setCurrentWidget(self, widget):self.stack.setCurrentWidget(widget)
