import os
import subprocess
import logging
from matplotlib.pyplot import box
import numpy as np
import tifffile
from datetime import datetime, timezone
import pandas as pd
import json
import re
from ultralytics import YOLO

from PyQt6.QtCore import QThread, pyqtSignal

class ConversionWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, input_dir, output_dir, irp_path, exiftool_path, emissivity, distance, humidity, reflection):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.irp_path = irp_path
        self.exiftool_path = exiftool_path
        self.emissivity = emissivity
        self.distance = distance
        self.humidity = humidity
        self.reflection = reflection

    def run(self):
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            input_files = [f for f in os.listdir(self.input_dir) if f.upper().endswith('_T.JPG')]
            total_files = len(input_files)
            
            if total_files == 0:
                logging.warning("No thermal images (*_T.JPG) found in the input directory.")
                self.finished.emit()
                return

            logging.info(f"Found {total_files} thermal files. Starting processing...")
            
            for i, file in enumerate(input_files):
                try:
                    self.process_single_image(file)
                    logging.info(f"[{i + 1}/{total_files}] Successfully processed {file}")
                except Exception as e:
                    logging.error(f"Error on {file}: {e}")
                
                progress_val = int(((i + 1) / total_files) * 100)
                self.progress.emit(progress_val)

            logging.info("Batch conversion finished!")
            self.finished.emit()
            
        except Exception as e:
            logging.error(f"Critical Error: {e}")
            self.error.emit(str(e))

    def process_single_image(self, filename):
        filepath = os.path.join(self.input_dir, filename).replace('\\', '/')
        print(filepath)
        out_filepath = os.path.join(self.output_dir, filename.replace('.JPG', '.tif')).replace('.jpg', '.tif').replace('\\', '/')
        temp_raw = os.path.join(self.output_dir, f"{filename}_temp.raw").replace('\\', '/')

        cmd = [
            self.irp_path, "-s", filepath, "-a", "measure", "-o", temp_raw,
            "--measurefmt", "float32", "--emissivity", str(self.emissivity),
            "--distance", str(self.distance), "--humidity", str(self.humidity),
            "--reflection", str(self.reflection)
        ]
        
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not os.path.isfile(temp_raw):
            raise Exception(f"Failed to generate raw array for {filename}")

        raw_data = np.fromfile(temp_raw, dtype=np.float32)
        if raw_data.size == 327680:      
            temperature_array = raw_data.reshape((512, 640))
        elif raw_data.size == 49152:     
            temperature_array = raw_data.reshape((192, 256))
        else:
            os.remove(temp_raw)
            raise Exception(f"Unknown resolution found in {filename} ({raw_data.size} pixels)")

        tifffile.imwrite(out_filepath, temperature_array)
        os.remove(temp_raw)

        subprocess.run(
            [self.exiftool_path, '-tagsfromfile', filepath, '-xmp', '-exif:all', '-overwrite_original', out_filepath],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

class ExifWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, output_dir, exiftool_path):
        super().__init__()
        self.output_dir = output_dir
        self.exiftool_path = exiftool_path

    def run(self):
        try:
            output_csv = os.path.join(self.output_dir, "exif_data.csv")
            logging.info(f"Extracting EXIF data from images in {self.output_dir}. Please wait...")

            cmd = [
                self.exiftool_path, "-csv", "-GPSLatitude", "-GPSLongitude", 
                "-RelativeAltitude", "-GimbalPitchDegree", "-FlightYawDegree", 
                self.output_dir
            ]
            with open(output_csv, 'w', encoding='utf-8') as f:
                subprocess.run(cmd, stdout=f, stderr=subprocess.DEVNULL)

            logging.info(f"EXIF data extracted to {output_csv}")
            self.finished.emit()

        except Exception as e:
            logging.error(f"Error during EXIF extraction: {e}")
            self.error.emit(str(e))

class JsonWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, output_dir, project_data_path):
        super().__init__()
        self.output_dir = output_dir
        self.project_data_path = project_data_path

    def run(self):
        try:
            logging.info("Generating project JSON...")
            data = {
                "project_metadata": {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "image_dir": os.path.abspath(self.output_dir),
                    "ortho_path": None,
                },
                "images": {}, "annotations": {}
            }

            rtk_data_folder = os.path.join(self.output_dir, "exif_data.csv")
            if not os.path.isfile(rtk_data_folder):
                raise FileNotFoundError("exif_data.csv not found. Run EXIF extraction first.")
                
            rtk_data = pd.read_csv(rtk_data_folder)
            filenames = [f for f in os.listdir(self.output_dir) if f.upper().endswith('.TIF')]
            total_files = len(filenames)

            for i, filename in enumerate(filenames):
                base_name = os.path.splitext(filename)[0]
                matching_row = rtk_data[rtk_data['SourceFile'].str.contains(base_name, case=False)]

                if not matching_row.empty:
                    row = matching_row.iloc[0]
                    data["images"][filename] = {
                        "thermal_path": os.path.join(self.output_dir, filename).replace('\\', '/'),
                        "assessed": False, "preprocessed_flag": False, "preprocessed_max_delta_t": 0.0,
                        "table_id": "Unknown", "row_id": "Unknown",
                        "rtk_data": {
                            "GPSLatitude": self.dms_to_decimal(str(row.get("GPSLatitude"))),
                            "GPSLongitude": self.dms_to_decimal(str(row.get("GPSLongitude"))),
                            "RelativeAltitude": row.get("RelativeAltitude"),
                            "GimbalPitchDegree": row.get("GimbalPitchDegree"),
                            "FlightYawDegree": row.get("FlightYawDegree")
                        }
                    }
                    data["annotations"][filename] = []
                else:
                    logging.warning(f"No EXIF data found for {filename}")

                self.progress.emit(int(((i + 1) / total_files) * 100))

            with open(self.project_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)

            logging.info(f"Project JSON generated at {self.project_data_path}")
            self.finished.emit()

        except Exception as e:
            logging.error(f"Error during JSON Generation: {e}")
            self.error.emit(str(e))

    def dms_to_decimal(self, dms_str):
        if str(dms_str) == 'nan' or not dms_str:
            return 0.0
        match = re.search(r"(\d+)\s*deg\s*(\d+)'\s*([\d.]+)\"\s*([NSEW])", dms_str)
        if not match:
            try: return float(dms_str) 
            except ValueError: raise ValueError(f"Invalid GPS format: {dms_str}")
        
        degrees, minutes, seconds = float(match.group(1)), float(match.group(2)), float(match.group(3))
        decimal_degrees = degrees + (minutes / 60.0) + (seconds / 3600.0)
        return -decimal_degrees if match.group(4) in ['S', 'W'] else decimal_degrees

class SegmentationWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, input_dir, project_data_path, model_path = "best.pt"):
        super().__init__()
        self.input_dir = input_dir
        self.project_data_path = project_data_path
        self.model_path = model_path

    def run(self):
        try:
            logging.info(f"Loading YOLO model from {self.model_path}...")
            model = YOLO(self.model_path)

            if not os.path.isfile(self.project_data_path):
                raise FileNotFoundError("project_data.json not found. Run JSON generation first.")

            with open(self.project_data_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            if "segmentation" not in project_data:
                project_data["segmentation"] = {}

            # All files that end with JPG and have _V in their name (case insensitive)
            filenames = [f for f in os.listdir(self.input_dir) if f.upper().endswith('.JPG') and '_V' in f.upper()]
            total_files = len(filenames)

            if total_files == 0:
                logging.warning("No visible images (*_V.JPG) found in the input directory.")
                self.finished.emit()
                return

            logging.info(f"Found {total_files} visible files. Starting segmentation...")

            for i, filename in enumerate(filenames):
                filepath = os.path.join(self.input_dir, filename)

                tif_filename = filename.replace('.JPG', '.tif').replace('.jpg', '.tif')

                project_data["segmentation"][tif_filename] = []

                results = model.predict(source = filepath, conf = 0.5, verbose = False, save = False)

                for result in results:
                    if result.masks is not None:
                        for idx, polygon in enumerate(result.masks.xy):
                            cls_id = int(result.boxes.cls[idx].item())
                            class_name = result.names[cls_id]

                            x1, y1, x2, y2 = result.boxes.xyxy[idx].tolist()
                            w = x2 - x1
                            h = y2 - y1

                            poly_points = polygon.tolist()

                            segmentation_item = {
                                "detection_class": class_name,
                                "points": poly_points,
                                "x": x1,
                                "y": y1,
                                "w": w,
                                "h": h
                            }

                            project_data["segmentation"][tif_filename].append(segmentation_item)

                self.progress.emit(int(((i + 1) / total_files) * 100))

            with open(self.project_data_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=4)

            logging.info("Segmentation finished!")
            self.finished.emit()

        except Exception as e:
            logging.error(f"Error during segmentation: {e}")
            self.error.emit(str(e))