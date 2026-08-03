import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QGroupBox, QLabel, QLineEdit, QPushButton, QDoubleSpinBox, 
    QProgressBar, QPlainTextEdit, QFileDialog, QMessageBox
)

class DJIThermalConverterView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DJI Thermal Converter")
        self.resize(720, 750)
        self.setMinimumSize(700, 650)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # --- Directories Frame ---
        dir_group = QGroupBox("Directories")
        dir_layout = QGridLayout()
        dir_group.setLayout(dir_layout)
        
        self.input_dir_edit = QLineEdit(os.path.abspath('input_images'))
        self.output_dir_edit = QLineEdit(os.path.abspath('output_images'))
        self.project_data_edit = QLineEdit(os.path.abspath('project_data.json'))

        self.btn_in = QPushButton("Browse")
        self.btn_out = QPushButton("Browse")
        self.btn_json = QPushButton("Browse")

        dir_layout.addWidget(QLabel("Input Folder:"), 0, 0)
        dir_layout.addWidget(self.input_dir_edit, 0, 1)
        dir_layout.addWidget(self.btn_in, 0, 2)
        dir_layout.addWidget(QLabel("Output Folder:"), 1, 0)
        dir_layout.addWidget(self.output_dir_edit, 1, 1)
        dir_layout.addWidget(self.btn_out, 1, 2)
        dir_layout.addWidget(QLabel("Project data JSON file:"), 2, 0)
        dir_layout.addWidget(self.project_data_edit, 2, 1)
        dir_layout.addWidget(self.btn_json, 2, 2)
        main_layout.addWidget(dir_group)

        # --- Settings Frame ---
        settings_group = QGroupBox("Executable Paths")
        settings_layout = QGridLayout()
        settings_group.setLayout(settings_layout)

        self.irp_path_edit = QLineEdit(os.path.abspath('dji_thermal_sdk/utility/bin/windows/release_x64/dji_irp.exe'))
        self.exiftool_path_edit = QLineEdit('exiftool')
        self.btn_irp = QPushButton("Browse")
        self.btn_exif = QPushButton("Browse")

        settings_layout.addWidget(QLabel("dji_irp.exe Path:"), 0, 0)
        settings_layout.addWidget(self.irp_path_edit, 0, 1)
        settings_layout.addWidget(self.btn_irp, 0, 2)
        settings_layout.addWidget(QLabel("Exiftool Path:"), 1, 0)
        settings_layout.addWidget(self.exiftool_path_edit, 1, 1)
        settings_layout.addWidget(self.btn_exif, 1, 2)
        main_layout.addWidget(settings_group)

        # --- Environmental Parameters Frame ---
        env_group = QGroupBox("Environmental Parameters (Overrides)")
        env_layout = QGridLayout()
        env_group.setLayout(env_layout)

        self.emissivity_spin = QDoubleSpinBox()
        self.emissivity_spin.setRange(0.1, 1.0)
        self.emissivity_spin.setValue(0.85)

        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(0.0, 10000.0)
        self.distance_spin.setValue(5.0)

        self.humidity_spin = QDoubleSpinBox()
        self.humidity_spin.setRange(0.0, 100.0)
        self.humidity_spin.setValue(70.0)

        self.reflection_spin = QDoubleSpinBox()
        self.reflection_spin.setRange(-100.0, 500.0)
        self.reflection_spin.setValue(25.0)

        env_layout.addWidget(QLabel("Emissivity (0.1-1.0):"), 0, 0)
        env_layout.addWidget(self.emissivity_spin, 0, 1)
        env_layout.addWidget(QLabel("Distance (m):"), 0, 2)
        env_layout.addWidget(self.distance_spin, 0, 3)
        env_layout.addWidget(QLabel("Humidity (%):"), 1, 0)
        env_layout.addWidget(self.humidity_spin, 1, 1)
        env_layout.addWidget(QLabel("Reflection (°C):"), 1, 2)
        env_layout.addWidget(self.reflection_spin, 1, 3)
        main_layout.addWidget(env_group)

        # --- Action Buttons & Progress ---
        action_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Batch Conversion")
        self.exif_btn = QPushButton("Extract EXIF Data")
        self.generate_json_btn = QPushButton("Generate Project JSON")
        self.segmentation_btn = QPushButton("Run Segmentation")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        action_layout.addWidget(self.start_btn)
        action_layout.addWidget(self.exif_btn)
        action_layout.addWidget(self.generate_json_btn)
        action_layout.addWidget(self.segmentation_btn)
        action_layout.addWidget(self.progress_bar)
        main_layout.addLayout(action_layout)

        # --- Log Console ---
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.log_console = QPlainTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas; font-size: 9pt;")
        log_layout.addWidget(self.log_console)
        main_layout.addWidget(log_group)

    # --- View Updaters ---
    def append_log(self, text):
        self.log_console.appendPlainText(text)
        
    def set_gui_state(self, state):
        self.start_btn.setEnabled(state)
        self.exif_btn.setEnabled(state)
        self.generate_json_btn.setEnabled(state)
        self.segmentation_btn.setEnabled(state)
        if not state:
            self.progress_bar.setValue(0)
            self.log_console.clear()

    def show_message(self, title, msg, is_error=False):
        if is_error:
            QMessageBox.critical(self, title, msg)
        else:
            QMessageBox.information(self, title, msg)
            
    def browse_directory(self, title, current_dir):
        return QFileDialog.getExistingDirectory(self, title, current_dir)

    def browse_file(self, title, current_dir, filters):
        path, _ = QFileDialog.getOpenFileName(self, title, current_dir, filters)
        return path