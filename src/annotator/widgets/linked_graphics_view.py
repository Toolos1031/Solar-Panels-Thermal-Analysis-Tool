from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QPen


class SyncGraphicsView(QGraphicsView):

    zoom_triggered = pyqtSignal(float)  # Signal to emit zoom factor
    coordinate_clicked = pyqtSignal(float, float)  # Signal to emit clicked coordinates
    box_drawn = pyqtSignal(float, float, float, float)  # Signal to emit box coordinates (x1, y1, x2, y2)
    label_drawn = pyqtSignal(float, float, float, float) 

    def __init__(self, scene: QGraphicsScene = None):
        super().__init__(scene)

        # Enable dragging to pan
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Make zooming center arround the mouse cursor
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Flag to indicate if measurement mode is active
        #self.measurement_mode = False  

        self.active_tool = None  # Track the currently active tool (spot or box temperature)

        # Variables for drawing the box temperature rectangle
        self.drag_start_pos = None
        self.temp_rect_item = None

    def set_active_tool(self, tool_name: str):
        # Pass None, "spot" or "box"

        self.active_tool = tool_name
        if tool_name:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.unsetCursor()  # Reset to default cursor

    def wheelEvent(self, event):

        if event.angleDelta().y() > 0:
            zoom_factor = 1.25
        else:
            zoom_factor = 1 / 1.15

        # Apply zoom to this view
        self.scale(zoom_factor, zoom_factor)

        # Broadcast the zoom factor to the linked view
        self.zoom_triggered.emit(zoom_factor)

    def apply_external_zoom(self, zoom_factor):
        # Apply zoom from the linked view
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())

            if self.active_tool == "spot":
                # Emit the clicked coordinates for spot temperature
                self.coordinate_clicked.emit(scene_pos.x(), scene_pos.y())
                return
            elif self.active_tool in ["box", "label_box"]:
                self.drag_start_pos = scene_pos
                # Create a temporary rectangle outline on the canvas while dragging
                self.temp_rect_item = QGraphicsRectItem()
                color = "yellow" if self.active_tool == "box" else "magenta"
                self.temp_rect_item.setPen(QPen(QColor(color), 2, Qt.PenStyle.DashLine))
                self.scene().addItem(self.temp_rect_item)
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Update the size of the temporary rectangle while dragging for box temperature
        if self.active_tool in ["box", "label_box"] and self.drag_start_pos and self.temp_rect_item:
            current_pos = self.mapToScene(event.pos())

            x = min(self.drag_start_pos.x(), current_pos.x())
            y = min(self.drag_start_pos.y(), current_pos.y())
            w = abs(self.drag_start_pos.x() - current_pos.x())
            h = abs(self.drag_start_pos.y() - current_pos.y())

            self.temp_rect_item.setRect(x, y, w, h)
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.active_tool in ["box", "label_box"] and self.drag_start_pos:
            current_pos = self.mapToScene(event.pos())

            x = min(self.drag_start_pos.x(), current_pos.x())
            y = min(self.drag_start_pos.y(), current_pos.y())
            w = abs(self.drag_start_pos.x() - current_pos.x())
            h = abs(self.drag_start_pos.y() - current_pos.y())

            # Clean up the temporary rectangle
            if self.temp_rect_item:
                self.scene().removeItem(self.temp_rect_item)
                self.temp_rect_item = None
            self.drag_start_pos = None

            # Only emit if it is an actual box (not a click)
            if w > 5 and h > 5:
                if self.active_tool == "box":
                    self.box_drawn.emit(x, y, w, h)
                elif self.active_tool == "label_box":
                    self.label_drawn.emit(x, y, w, h)
            return

        super().mouseReleaseEvent(event)