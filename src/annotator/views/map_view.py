import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGraphicsView, QGraphicsScene, QHBoxLayout, QGraphicsEllipseItem, QGraphicsItem
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QPen, QBrush, QColor

class MapView(QWidget):

    # Initialize global signals
    clicked_back = pyqtSignal()
    photo_clicked = pyqtSignal(str) 

    def __init__(self, project_model):
        super().__init__()
        self.project_model = project_model

        # Connect the project_loaded signal to the _load_ortho_map method to load the orthophoto map when the project is loaded
        # Workaround. This method is called when the project is loaded, ensuring that the orthophoto map is displayed in the MapView.
        self.project_model.project_loaded.connect(self._load_ortho_map)
        self.project_model.project_loaded.connect(self._show_photos)

        self._init_ui()
        self.resize(800, 600)

        self.photo_markers = []

    def _init_ui(self):

        # Initialize the UI components for the MapView
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        map_label = QLabel("Map View")
        map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        map_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(map_label)

        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        main_layout.addWidget(self.view)

        btn_layout = QHBoxLayout()
        
        back_btn = QPushButton("Back to Start")
        back_btn.clicked.connect(self._on_back_clicked)
        btn_layout.addWidget(back_btn)

        self.show_btn = QPushButton("Hide Photos")
        self.show_btn.setCheckable(True)
        self.show_btn.setChecked(True)
        self.show_btn.clicked.connect(self._on_toggle_photos)
        btn_layout.addWidget(self.show_btn)

        self.scene.selectionChanged.connect(self._on_marker_selected)

        main_layout.addLayout(btn_layout)

    def _on_back_clicked(self): # Emit the clicked_back signal to navigate back to the StartView
        self.clicked_back.emit()

    def _load_ortho_map(self): # Load the orthophoto map from the project model and display it in the QGraphicsView
        ortho_file_path = self.project_model.ortho_path

        if ortho_file_path:
            pixmap = QPixmap(ortho_file_path)
            self.pixmap_size = pixmap.size()
            self.scene.clear()
            self.scene.addPixmap(pixmap)
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _on_toggle_photos(self, checked: bool): # Show or hide photo markers on the orthophoto map based on the state of the show_btn
        if checked:
            self.show_btn.setText("Hide Photos")
            self._show_photos()
        else:
            self.show_btn.setText("Show Photos")
            self._clear_photos()

    def _clear_photos(self): # Clear all photo markers from the QGraphicsScene and reset the photo_markers list
        for marker in self.photo_markers:
            self.scene.removeItem(marker)

        self.photo_markers.clear()

    def _show_photos(self): # Show photo markers on the orthophoto map based on the translated image coordinates
        self._clear_photos()

        translated_points = self.project_model.translate_points_to_image_coords(self.pixmap_size.width(), self.pixmap_size.height())

        marker_radius = 4

        for point_name, point_data in translated_points.items():
            lat_new = point_data["latitude"]
            lon_new = point_data["longitude"]

            marker = QGraphicsEllipseItem(
                lon_new - marker_radius,
                lat_new - marker_radius,
                marker_radius * 10,
                marker_radius * 10
            )

            # Set colors based on assessed flag
            assessed = self.project_model.project_data["images"].get(point_name, {}).get("assessed", False)

            if assessed:
                pen = QPen(Qt.GlobalColor.green)
                brush = QBrush(QColor(0, 255, 0, 127))  # Semi-transparent green
            else:
                pen = QPen(Qt.GlobalColor.red)
                brush = QBrush(QColor(255, 0, 0, 127))  # Semi-transparent red

            marker.setPen(pen)
            marker.setBrush(brush)

            marker.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            marker.setToolTip(f"Photo: {point_name}")

            marker.setData(0, point_name)

            self.scene.addItem(marker)
            self.photo_markers.append(marker)

    def _on_marker_selected(self): # Handle the selection of a photo marker in the QGraphicsScene and emit the photo_clicked signal with the selected photo ID
        selected_items = self.scene.selectedItems()

        if not selected_items:
            return

        clicked_marker = selected_items[0]
        photo_id = clicked_marker.data(0)

        if photo_id:
            clicked_marker.setBrush(QBrush(QColor(255, 255, 0, 127)))

            self.photo_clicked.emit(photo_id)
