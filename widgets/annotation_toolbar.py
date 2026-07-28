from PyQt6.QtWidgets import QToolBar
from PyQt6.QtGui import QAction, QIcon, QActionGroup
from PyQt6.QtCore import Qt, pyqtSignal

class AnnotationToolbar(QToolBar):

    # Initialize global signals
    spot_temp_toggled = pyqtSignal(bool)
    box_temp_toggled = pyqtSignal(bool)
    clear_temp_triggered = pyqtSignal()
    label_toggled = pyqtSignal(bool)
    delete_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)

        self.label_action = QAction("Add Label", self)
        self.label_action.setCheckable(True)
        self.label_action.triggered.connect(lambda checked: self.label_toggled.emit(checked))
        self.tool_group.addAction(self.label_action)
        self.addAction(self.label_action)

        self.spot_temp_action = QAction("Spot Temperature", self)
        self.spot_temp_action.setCheckable(True)
        self.spot_temp_action.triggered.connect(self._on_toggled)
        self.tool_group.addAction(self.spot_temp_action)
        self.addAction(self.spot_temp_action)

        self.box_temp_action = QAction("Box Temperature", self)
        self.box_temp_action.setCheckable(True)
        self.box_temp_action.triggered.connect(self._on_box_toggled)
        self.tool_group.addAction(self.box_temp_action)
        self.addAction(self.box_temp_action)

        self.clear_temp_action = QAction("Clear Spot Temperature", self)
        self.clear_temp_action.triggered.connect(self._on_clear_temp)
        self.addAction(self.clear_temp_action)

        self.addSeparator()

        self.delete_action = QAction("Delete Selected", self)
        self.delete_action.triggered.connect(self.delete_requested.emit)
        self.addAction(self.delete_action)

        # set the tool button style to display the icon and text beside each other
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

    def _on_toggled(self, checked: bool): # Emit a signal when the Spot Temperature button is toggled
        self.spot_temp_toggled.emit(checked)

    def _on_box_toggled(self, checked: bool): # Emit a signal when the Box Temperature button is toggled
        self.box_temp_toggled.emit(checked)

    def reset_tools(self): # Reset the state of the tools in the toolbar
        self.spot_temp_action.setChecked(False)
        self.box_temp_action.setChecked(False)
        self.label_action.setChecked(False)

    def _on_clear_temp(self): # Emit a signal to clear the spot temperature markers
        self.clear_temp_triggered.emit()