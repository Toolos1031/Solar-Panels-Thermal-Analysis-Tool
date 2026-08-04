from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QStackedWidget, QStatusBar
import sys
from views.start_view import StartView
from views.map_view import MapView
from views.photo_view import PhotoView
from models.project_model import ProjectModel
from ui_theme import DARK_THEME


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize the project model
        self.project_model = ProjectModel()

        self.setWindowTitle("Thermal Annotator")

        screen_geometry = QApplication.primaryScreen().geometry()
        window_width = int(screen_geometry.width() * 0.8)
        window_height = int(screen_geometry.height() * 0.8)

        self.resize(window_width, window_height)

        x_position = (screen_geometry.width() - window_width) // 2
        y_position = (screen_geometry.height() - window_height) // 2
        self.move(x_position, y_position)

        self.setStatusBar(QStatusBar(self))
        self.setStyleSheet(DARK_THEME)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize the views and add them to the stacked widget
        self.start_view = StartView(self.project_model)
        self.map_view = MapView(self.project_model)
        self.photo_view = PhotoView(self.project_model)
        self.stacked_widget.addWidget(self.start_view)
        self.stacked_widget.addWidget(self.map_view)
        self.stacked_widget.addWidget(self.photo_view)

        # Setup signal connections for navigation between views
        self._setup_signal_connections()

    def _setup_signal_connections(self): # Connect signals for navigation between views
        self.start_view.project_loaded.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        self.map_view.clicked_back.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        self.map_view.photo_clicked.connect(self.open_annotation_workspace)

        self.photo_view.clicked_back.connect(lambda: self.stacked_widget.setCurrentIndex(1))

    def open_annotation_workspace(self, photo_id: str): # Open the annotation workspace for the selected photo
        self.photo_view.load_photo(photo_id)
        self.stacked_widget.setCurrentIndex(2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())