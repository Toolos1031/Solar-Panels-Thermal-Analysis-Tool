import os
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from models.model import ConversionWorker, ExifWorker, JsonWorker, SegmentationWorker

class LogEmitter(QObject):
    log_signal = pyqtSignal(str)

class GUILogHandler(logging.Handler):
    def __init__(self, emitter):
        super().__init__()
        self.emitter = emitter

    def emit(self, record):
        msg = self.format(record)
        self.emitter.log_signal.emit(msg)

class DJIThermalConverterController:
    def __init__(self, view):
        self.view = view
        self.worker = None

        # Setup Logging
        self.log_emitter = LogEmitter()
        self.log_emitter.log_signal.connect(self.view.append_log)
        self.setup_logging()

        # Connect View buttons
        self.view.btn_in.clicked.connect(self.browse_input)
        self.view.btn_out.clicked.connect(self.browse_output)
        self.view.btn_json.clicked.connect(self.browse_project_data)
        self.view.btn_irp.clicked.connect(self.browse_irp)
        self.view.btn_exif.clicked.connect(self.browse_exiftool)

        self.view.start_btn.clicked.connect(self.start_conversion)
        self.view.exif_btn.clicked.connect(self.extract_exif_data)
        self.view.generate_json_btn.clicked.connect(self.generate_project_json)
        self.view.segmentation_btn.clicked.connect(self.run_segmentation)

    def setup_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.handlers = []
        
        c_handler = logging.StreamHandler()
        c_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(c_handler)
        
        g_handler = GUILogHandler(self.log_emitter)
        g_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(g_handler)

    # --- Directory Browsers ---
    def browse_input(self):
        path = self.view.browse_directory("Select Input Directory", self.view.input_dir_edit.text())
        if path: self.view.input_dir_edit.setText(path)

    def browse_output(self):
        path = self.view.browse_directory("Select Output Directory", self.view.output_dir_edit.text())
        if path: self.view.output_dir_edit.setText(path)

    def browse_project_data(self):
        path = self.view.browse_file("Select Project Data JSON", os.path.dirname(self.view.project_data_edit.text()), "JSON Files (*.json);;All Files (*.*)")
        if path: self.view.project_data_edit.setText(path)

    def browse_irp(self):
        path = self.view.browse_file("Select dji_irp.exe", os.path.dirname(self.view.irp_path_edit.text()), "Executable Files (*.exe);;All Files (*.*)")
        if path: self.view.irp_path_edit.setText(path)

    def browse_exiftool(self):
        path = self.view.browse_file("Select Exiftool", os.path.dirname(self.view.exiftool_path_edit.text()), "Executable Files (*.exe);;All Files (*.*)")
        if path: self.view.exiftool_path_edit.setText(path)

    # --- Actions ---
    def on_task_finished(self, msg):
        self.view.set_gui_state(True)
        self.view.progress_bar.setValue(100)
        self.view.show_message("Success", msg)

    def on_task_error(self, err_msg):
        self.view.set_gui_state(True)
        self.view.show_message("Error", err_msg, is_error=True)

    def start_conversion(self):
        if not os.path.isdir(self.view.input_dir_edit.text()):
            self.view.show_message("Warning", "Invalid input directory.", is_error=True)
            return

        self.view.set_gui_state(False)
        self.worker = ConversionWorker(
            self.view.input_dir_edit.text(), self.view.output_dir_edit.text(),
            self.view.irp_path_edit.text(), self.view.exiftool_path_edit.text(),
            self.view.emissivity_spin.value(), self.view.distance_spin.value(),
            self.view.humidity_spin.value(), self.view.reflection_spin.value()
        )
        self.worker.progress.connect(self.view.progress_bar.setValue)
        self.worker.finished.connect(lambda: self.on_task_finished("Conversion completed."))
        self.worker.error.connect(self.on_task_error)
        self.worker.start()

    def extract_exif_data(self):
        if not os.path.isdir(self.view.output_dir_edit.text()):
            self.view.show_message("Warning", "Invalid output directory.", is_error=True)
            return

        self.view.set_gui_state(False)
        self.worker = ExifWorker(self.view.output_dir_edit.text(), self.view.exiftool_path_edit.text())
        self.worker.finished.connect(lambda: self.on_task_finished("EXIF extraction completed."))
        self.worker.error.connect(self.on_task_error)
        self.worker.start()

    def generate_project_json(self):
        if not os.path.isdir(self.view.output_dir_edit.text()):
            self.view.show_message("Warning", "Invalid output directory.", is_error=True)
            return

        self.view.set_gui_state(False)
        self.worker = JsonWorker(self.view.output_dir_edit.text(), self.view.project_data_edit.text())
        self.worker.progress.connect(self.view.progress_bar.setValue)
        self.worker.finished.connect(lambda: self.on_task_finished("JSON Generation completed."))
        self.worker.error.connect(self.on_task_error)
        self.worker.start()

    def run_segmentation(self):
        if not os.path.isdir(self.view.output_dir_edit.text()):
            self.view.show_message("Warning", "Invalid output directory.", is_error=True)
            return

        self.view.set_gui_state(False)

        self.worker = SegmentationWorker(self.view.input_dir_edit.text(), project_data_path = self.view.project_data_edit.text(), model_path = "best.pt")

        self.worker.progress.connect(self.view.progress_bar.setValue)
        self.worker.finished.connect(lambda: self.on_task_finished("Segmentation completed."))
        self.worker.error.connect(self.on_task_error)

        self.worker.start()