from PyQt6.QtWidgets import QGraphicsRectItem, QHBoxLayout, QWidget, QVBoxLayout, QPushButton, QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QPen, QColor, QShortcut, QKeySequence
from widgets.linked_graphics_view import SyncGraphicsView
from widgets.annotation_toolbar import AnnotationToolbar
from widgets.annotation_items import FaultDialog, EditableRectItem

class PhotoView(QWidget):

    # Initialize global signals
    clicked_back = pyqtSignal()
    photo_clicked = pyqtSignal(str)
    clear_temp_triggered = pyqtSignal()
    hide_flagged_toggled = pyqtSignal(bool)

    def __init__(self, project_model):
        super().__init__()
        self.project_model = project_model

        # Initial state for variables
        self.current_thermal_data = None
        self.current_photo_id = None
        self.temporary_measurements = []
        self.flagged_panels = []

        self.clahe_enabled = False
        self.thermal_pixmap_item = None

        self.setWindowTitle("Photo View")

        self._init_ui()
        self._link_views()

    def _init_ui(self): # UI components for the PhotoView

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.back_btn = QPushButton("Back to Map")
        self.back_btn.clicked.connect(self._on_back_clicked)
        layout.addWidget(self.back_btn)

        self.toolbar = AnnotationToolbar()
        layout.addWidget(self.toolbar)

        image_layout = QHBoxLayout()

        self.rgb_scene = QGraphicsScene()
        self.rgb_view = SyncGraphicsView(self.rgb_scene)
        self.thermal_scene = QGraphicsScene()
        self.thermal_view = SyncGraphicsView(self.thermal_scene)

        image_layout.addWidget(self.rgb_view)
        image_layout.addWidget(self.thermal_view)
        layout.addLayout(image_layout)

        btn_layout = QHBoxLayout()

        self.prev_btn = QPushButton("Previous Photo")
        self.prev_btn.clicked.connect(self._on_prev_clicked)
        btn_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next Photo")
        self.next_btn.clicked.connect(self._on_next_clicked)
        btn_layout.addWidget(self.next_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self._setup_connections()

    def _setup_connections(self):
        # Spot temp tool
        self.toolbar.spot_temp_toggled.connect(lambda checked: self.thermal_view.set_active_tool("spot" if checked else None))
        self.thermal_view.coordinate_clicked.connect(self._draw_spot_temperature)

        # Box temp tool
        self.toolbar.box_temp_toggled.connect(lambda checked: self.thermal_view.set_active_tool("box" if checked else None))
        self.thermal_view.box_drawn.connect(self._draw_box_temperature)

        # Clear temperature markers when the toolbar button is clicked
        self.toolbar.clear_temp_triggered.connect(self._clear_temperature_markers)

        # Connect label tool
        self.toolbar.label_toggled.connect(lambda checked: self.thermal_view.set_active_tool("label_box" if checked else None))
        self.thermal_view.label_drawn.connect(self._on_label_drawn)

        # Connect delete action
        self.toolbar.delete_requested.connect(self._delete_selected_items)

        # Connect hide flagged toggled action
        self.toolbar.hide_flagged_toggled.connect(self._toggle_flagged_panels)

        # Bind H to toggle hide/show flagged detections
        self.hide_flagged_shortcut = QShortcut(QKeySequence(Qt.Key.Key_H), self)
        self.hide_flagged_shortcut.activated.connect(self.toolbar.hide_flagged_action.trigger)

        # Bind DEL to the same function
        self.del_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        self.del_shortcut.activated.connect(self._delete_selected_items)

        # Bind right arrow to next photo
        self.next_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.next_shortcut.activated.connect(self._on_next_clicked)

        # Bind left arrow to previous photo
        self.prev_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.prev_shortcut.activated.connect(self._on_prev_clicked)

        # Bind C to clear temporary measurements
        self.clear_temp_shortcut = QShortcut(QKeySequence(Qt.Key.Key_C), self)
        self.clear_temp_shortcut.activated.connect(self._clear_temperature_markers)

        # Bind S to toggle spot temperature tool
        self.spot_temp_shortcut = QShortcut(QKeySequence(Qt.Key.Key_S), self)
        self.spot_temp_shortcut.activated.connect(self.toolbar.spot_temp_action.trigger)

        # Bind B to toggle box temperature tool
        self.box_temp_shortcut = QShortcut(QKeySequence(Qt.Key.Key_B), self)
        self.box_temp_shortcut.activated.connect(self.toolbar.box_temp_action.trigger)

        # Bind L to toggle label tool
        self.label_shortcut = QShortcut(QKeySequence(Qt.Key.Key_L), self)
        self.label_shortcut.activated.connect(self.toolbar.label_action.trigger)

        # Bind D to delete selected items
        self.delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_D), self)
        self.delete_shortcut.activated.connect(self._delete_selected_items)

        # Bind ESC to go back to the map view
        self.back_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.back_shortcut.activated.connect(self._on_back_clicked)

        # Bind T to toggle CLAHE
        self.clahe_shortcut = QShortcut(QKeySequence(Qt.Key.Key_T), self)
        self.clahe_shortcut.activated.connect(self.toggle_CLAHE)

    def _link_views(self): # Link the RGB and thermal views for synchronized panning and zooming

        # 1. Sync panning
        # Link RGB to Thermal
        self.rgb_view.verticalScrollBar().valueChanged.connect(self.thermal_view.verticalScrollBar().setValue)
        self.rgb_view.horizontalScrollBar().valueChanged.connect(self.thermal_view.horizontalScrollBar().setValue)

        # Link Thermal to RGB
        self.thermal_view.verticalScrollBar().valueChanged.connect(self.rgb_view.verticalScrollBar().setValue)
        self.thermal_view.horizontalScrollBar().valueChanged.connect(self.rgb_view.horizontalScrollBar().setValue)

        # 2. Sync zooming
        self.rgb_view.zoom_triggered.connect(self.thermal_view.apply_external_zoom)
        self.thermal_view.zoom_triggered.connect(self.rgb_view.apply_external_zoom)

    def resizeEvent(self, event):
        """Automatically scales both photos to fit the window when resized."""
        super().resizeEvent(event)

        # Scale the thermal view if it has content
        if self.thermal_scene.sceneRect().isValid() and not self.thermal_scene.sceneRect().isEmpty():
            self.thermal_view.fitInView(self.thermal_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
        # Scale the RGB view if it has content
        if self.rgb_scene.sceneRect().isValid() and not self.rgb_scene.sceneRect().isEmpty():
            self.rgb_view.fitInView(self.rgb_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def showEvent(self, event):
        """Ensures the photos are scaled correctly the moment this view becomes visible."""
        super().showEvent(event)

        # Fit thermal view
        if self.thermal_scene.sceneRect().isValid() and not self.thermal_scene.sceneRect().isEmpty():
            self.thermal_view.fitInView(self.thermal_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
        # Fit RGB view
        if self.rgb_scene.sceneRect().isValid() and not self.rgb_scene.sceneRect().isEmpty():
            self.rgb_view.fitInView(self.rgb_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def load_photo(self, photo_id: str): # Load the selected photo and its thermal data. Controlled by main.py
        self.current_photo_id = photo_id

        # Get the thermal path from the project data and load the thermal data
        thermal_path = self.project_model.project_data.get("images", {}).get(photo_id, {}).get("thermal_path")
        self.current_thermal_data = self.project_model.load_raw_thermal_data(thermal_path)

        # Pass the current CLAHE state and all YOLO detections to the pixmap generator
        all_detections = self.project_model.get_all_detections(photo_id)
        pixmap = self.project_model.create_thermal_pixmap(self.current_thermal_data, apply_clahe=self.clahe_enabled, detections=all_detections)

        self.thermal_scene.clear()
        self.thermal_pixmap_item = self.thermal_scene.addPixmap(pixmap)

        # Lock the canvas size
        self.thermal_scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())

        # Reset zoom and pan and fit into view
        self.thermal_view.resetTransform()
        self.thermal_view.fitInView(self.thermal_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

        # Render saved labels onto the thermal view
        self._load_existing_annotations(photo_id)
        self._load_flagged_detections(photo_id)

        self.load_rgb_photo(pixmap, photo_id)  # Load the corresponding RGB photo

    def load_rgb_photo(self, thermal_pixmap, photo_id: str): # Load the RGB photo corresponding to the selected photo ID and display it in the QLabel

        pixmap = self.project_model.get_rgb_photo_path(thermal_pixmap, photo_id)
        self.rgb_scene.clear()
        self.rgb_scene.addPixmap(pixmap)

        # Reset zoom and pan and fit into view
        self.rgb_view.resetTransform()
        self.rgb_view.fitInView(self.rgb_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _on_back_clicked(self): # Emit the clicked_back signal to navigate back to the MapView
        self._save_current_annotations()
        self.clicked_back.emit()

    def _on_prev_clicked(self): # Navigate to the previous photo in the project data
        self._save_current_annotations()  # Save current annotations before navigating
        prev_photo_id = self.project_model.get_previous_photo(self.current_photo_id)

        if prev_photo_id is not None:
            self.load_photo(prev_photo_id)

    def _on_next_clicked(self): # Navigate to the next photo in the project data
        self._save_current_annotations()  # Save current annotations before navigating
        next_photo_id = self.project_model.get_next_photo(self.current_photo_id)

        if next_photo_id is not None:
            self.load_photo(next_photo_id)

    def _draw_spot_temperature(self, x: float, y: float): # Draw a spot temperature marker on the thermal view and display the temperature in the status bar

        # Fetch the temperature from 32bit TIFF array
        temp_value = self.project_model.get_temperature_at_pixel(self.current_thermal_data, int(x), int(y))

        # Draw a red dot at the click location
        dot = QGraphicsEllipseItem(x - 5, y - 5, 10, 10)
        dot.setBrush(QBrush(QColor("red")))
        dot.setPen(QPen(Qt.PenStyle.NoPen))
        self.thermal_scene.addItem(dot)

        # Draw temperature text right next to the dot
        text = QGraphicsTextItem(f"{temp_value:.1f} °C")
        text.setDefaultTextColor(QColor("white"))
        text.setPos(x + 5, y - 10)
        self.thermal_scene.addItem(text)

        # Store references so we can delete them later
        self.temporary_measurements.append((dot, text))

        # Disengage the toolbar's spot temperature mode after one click
        self.toolbar.reset_tools()
        self.thermal_view.set_active_tool(None)

    def _draw_box_temperature(self, x: float, y: float, w: float, h: float): # Draw a box temperature rectangle on the thermal view
        # Fetch stats from model using array slicing
        stats = self.project_model.get_temperature_stats_in_box(self.current_thermal_data, int(x), int(y), int(w), int(h))

        # Draw the permament bounding box
        rect = QGraphicsRectItem(x, y, w, h)
        rect.setPen(QPen(QColor("yellow"), 2))
        self.thermal_scene.addItem(rect)

        # Draw the stats text above the box
        text = QGraphicsTextItem()
        
        # Use HTML/CSS to set the text, color, and background safely
        html_content = f"""
        <div style='background-color: rgba(0, 0, 0, 150); color: yellow; padding: 2px;'>
            Max: {stats['max']:.1f}°C<br>Min: {stats['min']:.1f}°C
        </div>
        """
        text.setHtml(html_content)
        text.setPos(x, y - 45)
        
        self.thermal_scene.addItem(text)

        # Draw the max temp dot
        max_x, max_y = stats['max_pos']
        max_dot = QGraphicsEllipseItem(max_x - 3, max_y - 3, 6, 6)
        max_dot.setBrush(QBrush(QColor("red")))
        max_dot.setPen(QPen(Qt.PenStyle.NoPen))
        self.thermal_scene.addItem(max_dot)

        # Draw the min temp dot
        min_x, min_y = stats['min_pos']
        min_dot = QGraphicsEllipseItem(min_x - 3, min_y - 3, 6, 6)
        min_dot.setBrush(QBrush(QColor("blue")))
        min_dot.setPen(QPen(Qt.PenStyle.NoPen))
        self.thermal_scene.addItem(min_dot)

        # Store references so we can delete them later
        self.temporary_measurements.append((rect, text, max_dot, min_dot))

        # Disengage the tool
        self.toolbar.reset_tools()
        self.thermal_view.set_active_tool(None)

    def _clear_temperature_markers(self): # Clear all spot temperature markers from the thermal view
        for items in self.temporary_measurements:
            for item in items:
                self.thermal_scene.removeItem(item)

        self.temporary_measurements.clear()

    def _on_label_drawn(self, x: float, y: float, w: float, h: float):
        # Triggered whem the user finished dragging a label box

        # Open a popup dialog
        dialog = FaultDialog(self)
        if dialog.exec():
            fault_type = dialog.get_fault_type()

            # Add the editable boundng box to the thermal scene
            label_item = EditableRectItem(x, y, w, h, fault_type)
            self.thermal_scene.addItem(label_item)

        # Reset the tool
        self.toolbar.reset_tools()
        self.thermal_view.set_active_tool(None)

    def _delete_selected_items(self):
        # Removes the selected label from the scene

        # Get all selected items in the scnee
        selected_items = self.thermal_scene.selectedItems()

        for item in selected_items:
            # Check if the item is an EditableRectItem
            if isinstance(item, EditableRectItem):
                self.thermal_scene.removeItem(item)

    def _save_current_annotations(self):
        # scan the canvas for labels and save them before navigating

        if not self.current_photo_id:
            return  # No photo loaded, nothing to save

        annotations_to_save = []

        # loop through all items in the scene
        for item in self.thermal_scene.items():
            if isinstance(item, EditableRectItem):

                # Map local corners to global coordinates
                scene_tl = item.mapToScene(item.rect().topLeft())
                scene_br = item.mapToScene(item.rect().bottomRight())

                annotations_to_save.append({
                    "fault_type": item.fault_type,
                    "x": scene_tl.x(),
                    "y": scene_tl.y(),
                    "w": scene_br.x() - scene_tl.x(),
                    "h": scene_br.y() - scene_tl.y()
                })

        # Update the project model with the new annotations
        self.project_model.update_annotations(self.current_photo_id, annotations_to_save)

    def _load_existing_annotations(self, photo_id: str):
        # fetches existing annotations for the current photo and displays them on the thermal view

        # Load actual annotations for this photo
        annotations = self.project_model.get_annotations(photo_id)

        for ann in annotations:
            label_item = EditableRectItem(ann["x"], ann["y"], ann["w"], ann["h"], ann["fault_type"])
            self.thermal_scene.addItem(label_item)

        # Load projected neigbor annotations
        pixmap_size = self.thermal_scene.sceneRect().size()
        image_width = pixmap_size.width()
        image_height = pixmap_size.height()

        neighbor_annotations = self.project_model.get_projected_neighbor_labels(photo_id, image_width, image_height)

        for ann in neighbor_annotations:

            # QGraphicsRectItem so user cannot interract with it
            rect = QGraphicsRectItem(ann["x"], ann["y"], ann["w"], ann["h"])

            # Style it differentyl
            rect.setPen(QPen(QColor(255, 255, 0, 150), 2, Qt.PenStyle.DashLine))
            rect.setBrush(QBrush(QColor(255, 255, 0, 30)))
            self.thermal_scene.addItem(rect)
            
            # Add small text
            text = QGraphicsTextItem(ann["fault_type"])
            text.setDefaultTextColor(QColor(255, 255, 0, 150))
            text.setPos(ann["x"], ann["y"] - 25)
            self.thermal_scene.addItem(text)

    def _load_flagged_detections(self, photo_id: str):
        self.flagged_panels.clear()  # Clear any existing flagged panels

        if self.project_model.project_data.get("images", {}).get(photo_id, {}).get("preprocessed_flag", False):
            detections = self.project_model.get_flagged_detections(photo_id)

            for det in detections:
                rect = QGraphicsRectItem(det["x"], det["y"], det["w"], det["h"])
                rect.setPen(QPen(QColor(0, 0, 255, 150), 2, Qt.PenStyle.DashLine))
                rect.setBrush(QBrush(QColor(0, 0, 255, 30)))
                self.thermal_scene.addItem(rect)

                text = QGraphicsTextItem(str(det["panel_delta"]))
                text.setDefaultTextColor(QColor(0, 0, 255, 150))
                text.setPos(det["x"], det["y"] - 25)
                self.thermal_scene.addItem(text)

                # Store the flagged panel for toggle
                self.flagged_panels.append((rect, text))

    def _toggle_flagged_panels(self, show: bool):
        for rect, text in self.flagged_panels:
            rect.setVisible(show)
            text.setVisible(show)

    def toggle_CLAHE(self):
        # toggles clahe on off and reloads the thermal pixmap
        if self.current_thermal_data is None or not self.current_photo_id:
            return  # No photo loaded, nothing to toggle

        # flip the state
        self.clahe_enabled = not self.clahe_enabled

        # Fetch boxes and regenerate the image based on new state
        all_detections = self.project_model.get_all_detections(self.current_photo_id)
        new_pixmap = self.project_model.create_thermal_pixmap(
            self.current_thermal_data, 
            apply_clahe=self.clahe_enabled, 
            detections=all_detections
        )

        # Swap the image
        if self.thermal_pixmap_item is not None:
            self.thermal_pixmap_item.setPixmap(new_pixmap)