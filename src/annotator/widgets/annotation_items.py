from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsItem, QDialog, QVBoxLayout, QComboBox, QPushButton, QLabel, QHBoxLayout, QGraphicsTextItem
from PyQt6.QtGui import QPen, QBrush, QColor
from PyQt6.QtCore import Qt

class FaultDialog(QDialog):
    # A popup dialog to select the fault type
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Label Anomaly")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select the type of fault:"))

        self.combo = QComboBox()
        self.combo.addItems(["Diode Failure", "Offline String", "Hot Spot", "PID", "Glass Breakage"])
        layout.addWidget(self.combo)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Save Label")
        self.cancel_btn = QPushButton("Cancel")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def get_fault_type(self) -> str:
        return self.combo.currentText()

class RectHandle(QGraphicsEllipseItem):
    # A draggable corner handle for the bounding box
    def __init__(self, cursor_shape, parent_item):
        super().__init__(-4, -4, 8, 8, parent_item)
        self.setBrush(QBrush(QColor("magenta")))
        self.setPen(QPen(Qt.PenStyle.NoPen))

        # Make it draggable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setCursor(cursor_shape)

        self.is_updating = False

    def itemChange(self, change, value):
        # Notify the parent rectangle when this handle is dragged
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and not self.is_updating:
            self.parentItem().update_from_handle(self, value)
        return super().itemChange(change, value)

class EditableRectItem(QGraphicsRectItem):
    # A resizable bounding box with a fault label attached
    def __init__(self, x, y, w, h, fault_type: str):
        super().__init__(x, y, w, h)
        self.fault_type = fault_type

        self.setPen(QPen(QColor("magenta"), 2))
        self.setBrush(QBrush(QColor(255, 0, 255, 50)))  # Semi-transparent magenta

        # Allow the user to drag the entire box around by clicking the center
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        # Create 4 corner handles
        self.tl = RectHandle(Qt.CursorShape.SizeFDiagCursor, self)
        self.tr = RectHandle(Qt.CursorShape.SizeBDiagCursor, self)
        self.bl = RectHandle(Qt.CursorShape.SizeBDiagCursor, self)
        self.br = RectHandle(Qt.CursorShape.SizeFDiagCursor, self)

        # Crete the text label
        self.text = QGraphicsTextItem(fault_type, self)
        self.text.setDefaultTextColor(QColor("magenta"))

        self._sync_handles()

    def _sync_handles(self):
        # Aligns handles to the corners of rectangles
        r = self.rect()

        # Temporarily block handle signals so they dont trigger infinite loops
        for h in (self.tl, self.tr, self.bl, self.br):
            h.is_updating = True

        self.tl.setPos(r.topLeft())
        self.tr.setPos(r.topRight())
        self.bl.setPos(r.bottomLeft())
        self.br.setPos(r.bottomRight())
        self.text.setPos(r.left(), r.top() - 25)

        for h in (self.tl, self.tr, self.bl, self.br):
            h.is_updating = False

    def update_from_handle(self, handle, new_pos):
        # called by a handle when it is dragged to resize the box

        r = self.rect()

        if handle == self.tl:
            r.setTopLeft(new_pos)
        elif handle == self.tr:
            r.setTopRight(new_pos)
        elif handle == self.bl:
            r.setBottomLeft(new_pos)
        elif handle == self.br:
            r.setBottomRight(new_pos)

        self.setRect(r.normalized())  # Normalize to avoid negative width/height
        self._sync_handles()