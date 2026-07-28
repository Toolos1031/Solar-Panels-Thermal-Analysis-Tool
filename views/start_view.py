import os
from PyQt6.QtWidgets import(
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QGroupBox, 
    QFormLayout, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

class StartView(QWidget):

    # Initialize global signals
    project_loaded = pyqtSignal()

    def __init__(self, project_model):
        super().__init__()
        self.project_model = project_model
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Container Card (Centers UI content on screen)
        card = QGroupBox("Start New Project")
        card.setFixedWidth(700)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)

        # Form inputs
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Image directory picker
        self.img_dir_input = QLineEdit()
        self.img_dir_input.setText(r"D:\orlen_fotowoltaika\Wloclawek\1\Thermal_TIFFs")
        self.img_dir_btn = QPushButton("Browse...")
        self.img_dir_btn.clicked.connect(self._select_img_dir)
        form_layout.addRow("Thermal Image Directory:", self._create_input_row(self.img_dir_input, self.img_dir_btn))

        # RGB Image directory picker
        self.rgb_dir_input = QLineEdit()
        self.rgb_dir_input.setText(r"D:\orlen_fotowoltaika\Wloclawek\1\DJI_202408291301_002_UAV-Create-Area-Route1")
        self.rgb_dir_btn = QPushButton("Browse...")
        self.rgb_dir_btn.clicked.connect(self._select_rgb_dir)
        form_layout.addRow("RGB Image Directory:", self._create_input_row(self.rgb_dir_input, self.rgb_dir_btn))

        # Ortophoto file picker
        self.ortho_input = QLineEdit()
        self.ortho_input.setText(r"D:\orlen_fotowoltaika\test_orto.jpg")
        self.ortho_btn = QPushButton("Browse...")
        self.ortho_btn.clicked.connect(self._select_ortho_file)
        form_layout.addRow("Orthophoto File:", self._create_input_row(self.ortho_input, self.ortho_btn))

        # Project data file picker
        self.project_data_input = QLineEdit()
        self.project_data_input.setText(r"D:\orlen_fotowoltaika\project_data.json")
        self.project_data_btn = QPushButton("Browse...")
        self.project_data_btn.clicked.connect(self._select_project_data_file)
        form_layout.addRow("Project Data File:", self._create_input_row(self.project_data_input, self.project_data_btn))

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.btn_load = QPushButton("Load Project")
        self.btn_load.setStyleSheet("font-weight: bold; padding: 10px; background-color: #2b5b84; color: white;")
        self.btn_load.clicked.connect(self._load_project)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_load)

        card_layout.addLayout(form_layout)
        card_layout.addLayout(btn_layout)
        main_layout.addWidget(card)


    def _create_input_row(self, line_edit:QLineEdit, button:QPushButton) -> QWidget: # Create a horizontal layout for the input row with a QLineEdit and a QPushButton
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(line_edit)
        layout.addWidget(button)
        return container

    def _select_img_dir(self): # Open a QFileDialog to select the thermal image directory and set the selected path in the QLineEdit
        folder = QFileDialog.getExistingDirectory(self, "Select Thermal Image Directory")
        if folder:
            self.img_dir_input.setText(folder)

    def _select_rgb_dir(self): # Open a QFileDialog to select the RGB image directory and set the selected path in the QLineEdit
        folder = QFileDialog.getExistingDirectory(self, "Select RGB Image Directory")
        if folder:
            self.rgb_dir_input.setText(folder)

    def _select_ortho_file(self): # Open a QFileDialog to select the orthophoto file and set the selected path in the QLineEdit
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Orthophoto File", "", "Image Files (*.png *.jpg *.jpeg *.tif *.tiff)")
        if file_path:
            self.ortho_input.setText(file_path)

    def _select_project_data_file(self): # Open a QFileDialog to select the project data JSON file and set the selected path in the QLineEdit
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Project Data File", "", "JSON Files (*.json)")
        if file_path:
            self.project_data_input.setText(file_path)

    def _load_project(self): # Load the project data from the specified paths and emit a signal when the project is loaded. Validate inputs before loading.
        img_dir = self.img_dir_input.text().strip()
        rgb_dir = self.rgb_dir_input.text().strip()
        ortho_path = self.ortho_input.text().strip()
        json_path = self.project_data_input.text().strip()

        # Validate inputs
        if not os.path.isdir(img_dir):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid thermal image directory.")
            return

        if not os.path.isdir(rgb_dir):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid RGB image directory.")
            return

        if not os.path.isfile(ortho_path):
            QMessageBox.warning(self, "Invalid File", "Please select a valid orthophoto file.")
            return
        
        if not os.path.isfile(json_path):
            QMessageBox.warning(self, "Invalid File", "Please select a valid project data file.")
            return
        
        # If validation passes, emit signal to indicate project is loaded
        try:
            self.project_model.load_project(
                image_dir = img_dir,
                rgb_dir = rgb_dir,
                ortho_path = ortho_path,
                json_path = json_path
            )
            self.project_loaded.emit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading the project: {str(e)}")
