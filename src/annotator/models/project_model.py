import os
import json
import numpy as np
import cv2
import math
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

class ProjectModel(QObject):

    # Initialize global signals
    project_loaded = pyqtSignal()
    photo_clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()


        # Initialize file paths and project data
        self.image_dir = ""
        self.rgb_dir = ""
        self.ortho_path = ""
        self.json_path = ""

        self.project_data = {
            "images": {},
            "annotations": {}
        }

    def load_project(self, image_dir: str, rgb_dir: str, ortho_path: str, json_path: str): # Load the project data from the specified paths and emit a signal when the project is loaded

        self.image_dir = image_dir
        self.rgb_dir = rgb_dir
        self.ortho_path = ortho_path
        self.json_path = json_path

        if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
            with open(json_path, 'r') as f:
                self.project_data = json.load(f)
        else:
            self._initialize_empty_state()

        self.project_loaded.emit()

    def _initialize_empty_state(self): # If JSON does not exist or is empty, initialize an empty project state and save it to the JSON file
        self.project_data = {
            "images": {},
            "annotations": {}
        }

        self.save_state()
        
    def save_state(self): # Save the current project state to the JSON file
        if not self.json_path:
            return

        with open(self.json_path, 'w') as f:
            json.dump(self.project_data, f, indent=4)

    def get_rgb_photo_path(self, base_pixmap: QPixmap, photo_id: str) -> QPixmap: # Get the path to the RGB photo corresponding to the selected photo ID
        photo_name = self.project_data.get("images", {}).get(photo_id, {}).get("thermal_path", "").split("/")[-1]
        rgb_path = os.path.join(self.rgb_dir, photo_name.replace("_T.tif", "_V.JPG"))

        jpg_pixmap = QPixmap(rgb_path)

        scaled_jpg = jpg_pixmap.scaled(
            base_pixmap.size(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        return scaled_jpg
        
    def _get_image_coordinates(self) -> dict: # Get the coordinates of images from the project data
        points = {}

        images = self.project_data.get("images", {})
        for image_name, image_data in images.items():
            rtk_data = image_data.get("rtk_data")

            lat = rtk_data.get("GPSLatitude")
            lon = rtk_data.get("GPSLongitude")

            if lat is not None and lon is not None:
                points[image_name] = {
                    "latitude": lat,
                    "longitude": lon,
                    "assessed": image_data.get("assessed", False),
                    "preprocessed_flag": image_data.get("preprocessed_flag", False)
                }
        return points

    def translate_points_to_image_coords(self, image_width: int, image_height: int) -> dict: # Translate geographic coordinates to image coordinates based on ortho bounds

        ortho_bounds = self._get_ortho_bounds(image_width, image_height)
        points = self._get_image_coordinates()

        translated_points = {}
        for image_name, point_data in points.items():

            lat_new = (((ortho_bounds["left_top_northing"] - point_data["latitude"]) / (ortho_bounds["right_bottom_northing"] - ortho_bounds["left_top_northing"])) * image_height) * -1
            lon_new = ((point_data["longitude"] - ortho_bounds["left_top_easting"]) / (ortho_bounds["right_bottom_easting"] - ortho_bounds["left_top_easting"])) * image_width

            translated_points[image_name] = {
                "longitude": lon_new,
                "latitude": lat_new,
                "assessed": point_data.get("assessed", False),
                "preprocessed_flag": point_data.get("preprocessed_flag", False)
            }

        return translated_points

    def _get_ortho_bounds(self, width: int, height: int) -> dict: # Get the geographic bounds of the ortho image based on its world file

        tfw_path = os.path.splitext(self.ortho_path)[0] + ".jgw"

        world_file_data = self._read_world_file(tfw_path)

        ortho_bounds = {
            "pixel_width": world_file_data["pixel_width"],
            "pixel_height": world_file_data["pixel_height"],
            "left_top_easting": world_file_data["left_top_easting"],
            "left_top_northing": world_file_data["left_top_northing"],
            "right_bottom_easting": (world_file_data["pixel_width"] * width) + world_file_data["left_top_easting"],
            "right_bottom_northing": (world_file_data["pixel_height"] * height) + world_file_data["left_top_northing"]
        }

        return ortho_bounds

    def _read_world_file(self, tfw_path: str) -> dict: # Read the world file and return its parameters

        with open(tfw_path, "r") as f:
            lines = f.readlines()

        values = [float(line.strip()) for line in lines]

        world_file_data = {
            "pixel_width": values[0],
            "rotation_x": values[1],
            "rotation_y": values[2],
            "pixel_height": values[3],
            "left_top_easting": values[4],
            "left_top_northing": values[5]
        }

        return world_file_data

    def load_raw_thermal_data(self, tiff_path: str) -> np.ndarray: # Load the raw thermal data from the specified TIFF file and return it as a NumPy array
        raw_thermal_data = cv2.imread(tiff_path, cv2.IMREAD_UNCHANGED)

        return raw_thermal_data

    def create_thermal_pixmap(self, raw_thermal_data: np.ndarray) -> QPixmap: # Create a QPixmap from the raw thermal data by normalizing it to 0-255 and converting it to a grayscale image

        min_temp = np.min(raw_thermal_data)
        max_temp = np.max(raw_thermal_data)

        if max_temp == min_temp:
            normalized = np.zeros(raw_thermal_data.shape, dtype=np.uint8)
        else:
            normalized = (255 * (raw_thermal_data - min_temp) / (max_temp - min_temp)).astype(np.uint8)

        height, width = normalized.shape
        bytes_per_line = width

        q_img = QImage(
            normalized.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8
        )

        return QPixmap.fromImage(q_img)

    def get_temperature_at_pixel(self, raw_thermal_data: np.ndarray, x: int, y: int) -> float: # Get the temperature at a specific pixel in the raw thermal data
        if raw_thermal_data is not None and 0 <= x < raw_thermal_data.shape[1] and 0 <= y < raw_thermal_data.shape[0]:
            return float(raw_thermal_data[y, x])
        return 0.0

    def get_temperature_stats_in_box(self, raw_thermal_data: np.ndarray, x: int, y: int, w: int, h: int) -> dict: # Get the temperature statistics (min, max, mean) within a specified box in the raw thermal data
        if raw_thermal_data is None:
            return {"min": 0.0, "max": 0.0}

        # Ensure the slice stays within the array boundaries
        height, width = raw_thermal_data.shape
        x_start, x_end = max(0, x), min(width, x + w)
        y_start, y_end = max(0, y), min(height, y + h)

        # Slice the numpy array to get the region of interest
        roi = raw_thermal_data[y_start:y_end, x_start:x_end]

        if roi.size == 0:
            return {"min": 0.0, "max": 0.0}

        # Find the 1D index of the min and max values
        min_idx = np.argmin(roi)
        max_idx = np.argmax(roi)

        # Convert 1D index to 2D coordinates
        min_y_local , min_x_local = np.unravel_index(min_idx, roi.shape)
        max_y_local , max_x_local = np.unravel_index(max_idx, roi.shape)

        # Convert local coordinates to global coordinates
        min_pos_global = (x_start + min_x_local, y_start + min_y_local)
        max_pos_global = (x_start + max_x_local, y_start + max_y_local)

        # Calculate stats
        return {
            "min": float(np.min(roi)),
            "max": float(np.max(roi)),
            "min_pos": min_pos_global,
            "max_pos": max_pos_global
        }

    def get_previous_photo(self, current_photo_id: str) -> str: # Get the previous photo ID in the project data based on the current photo ID. Returns None if there is no previous photo.
        photo_ids = list(self.project_data.get("images", {}).keys())
        current_index = photo_ids.index(current_photo_id)

        if current_index > 0:
            return photo_ids[current_index - 1]
        else:
            return None

    def get_next_photo(self, current_photo_id: str) -> str: # Get the next photo ID in the project data based on the current photo ID. Returns None if there is no next photo.
        photo_ids = list(self.project_data.get("images", {}).keys())
        current_index = photo_ids.index(current_photo_id)

        if current_index < len(photo_ids) - 1:
            return photo_ids[current_index + 1]
        else:
            return None

    def update_annotations(self, photo_id: str, annotations: list):
        # Overwrites the annotations for a specific photo and saves to disk

        # Ensure the annotations dict exists
        if "annotations" not in self.project_data:
            self.project_data["annotations"] = {}

        # When annotation is not empty, save and change "assessed" to True
        if annotations:
            self.project_data["images"][photo_id]["assessed"] = True
        else:
            self.project_data["images"][photo_id]["assessed"] = False

        self.project_data["annotations"][photo_id] = annotations
        self.save_state()

    def get_annotations(self, photo_id: str) -> list:
        # Retrives the list of annotations for a specific photo
        return self.project_data.get("annotations", {}).get(photo_id, [])

    def get_spatial_neighbors(self, current_photo_id: str, coverage_multiplier: float = 0.75) -> list:
        # Finds spatial neighbors based on search radius that is coupled to coverage multiplier and height

        # 1 Get current photo data
        current_data = self.project_data.get("images", {}).get(current_photo_id, {})
        if not current_data or "rtk_data" not in current_data:
            return []

        cur_rtk = current_data["rtk_data"]
        cur_lat = cur_rtk.get("GPSLatitude", 0)
        cur_lon = cur_rtk.get("GPSLongitude", 0)
        cur_alt = cur_rtk.get("RelativeAltitude", 0)

        if cur_lat is None or cur_lon is None or cur_alt is None or math.isnan(cur_alt):
            return []

        # Dorky dynamic radius
        dynamic_search_radius = cur_alt * coverage_multiplier

        neighbors = []

        LAT_TO_METERS = 111320.0
        LON_TO_METERS = 111320.0 * math.cos(math.radians(cur_lat))

        for photo_id, data in self.project_data.get("images", {}).items():
            if photo_id == current_photo_id:
                continue

            n_rtk = data.get("rtk_data", {})
            n_lat = n_rtk.get("GPSLatitude", 0)
            n_lon = n_rtk.get("GPSLongitude", 0)

            if n_lat is None or n_lon is None:
                continue

            # Calculate delta in meters (approximate)
            delta_y = (n_lat - cur_lat) * LAT_TO_METERS
            delta_x = (n_lon - cur_lon) * LON_TO_METERS
            distance = math.sqrt(delta_x**2 + delta_y**2)

            if distance <= dynamic_search_radius:
                neighbors.append(photo_id)

        return neighbors

        
    def get_projected_neighbor_labels(self, current_photo_id: str, image_width: int, image_height: int) -> list:
        # Finds labels from previous and next photos
        # roughly projects them onto the current photo

        projected_labels = []

        # 1 Get current photo data
        current_data = self.project_data.get("images", {}).get(current_photo_id, {})
        if not current_data or "rtk_data" not in current_data:
            return []

        cur_rtk = current_data["rtk_data"]
        cur_lat = cur_rtk.get("GPSLatitude", 0)
        cur_lon = cur_rtk.get("GPSLongitude", 0)
        cur_yaw = cur_rtk.get("FlightYawDegree", 0)


        # Some dorky constants to translate label positions
        PPM_X = 32.0
        PPM_Y = 29.0

        # Grab the neighbors
        spatial_neighbors = self.get_spatial_neighbors(current_photo_id, coverage_multiplier=1.5)

        for neighbor_id in filter(None, spatial_neighbors):
            neighbor_labels = self.get_annotations(neighbor_id)
            if not neighbor_labels:
                continue

            neighbor_rtk = self.project_data["images"][neighbor_id].get("rtk_data", {})
            n_lat = neighbor_rtk.get("GPSLatitude", 0)
            n_lon = neighbor_rtk.get("GPSLongitude", 0)

            # Calculate delta in meters (approximate)

            LAT_TO_METERS = 111320.0
            LON_TO_METERS = 111320.0 * math.cos(math.radians(cur_lat))

            delta_y_meters = (n_lat - cur_lat) * LAT_TO_METERS
            delta_x_meters = (n_lon - cur_lon) * LON_TO_METERS

            # Rotate the delta based on current yaw
            yaw_rad = math.radians(cur_yaw)
            rot_x = delta_x_meters * math.cos(yaw_rad) - delta_y_meters * math.sin(yaw_rad)
            rot_y = delta_x_meters * math.sin(yaw_rad) + delta_y_meters * math.cos(yaw_rad)

            # Convert to pixel shift
            pixel_shift_x = rot_x * PPM_X
            pixel_shift_y = -rot_y * PPM_Y

            # Apply shift to all labels from neighbors
            for label in neighbor_labels:
                new_x = label["x"] + pixel_shift_x
                new_y = label["y"] + pixel_shift_y
                w = label["w"]
                h = label["h"]

                if (new_x + w < 0) or (new_x > image_width) or (new_y + h < 0) or (new_y > image_height):
                    continue

                projected_labels.append({
                    "fault_type": label["fault_type"] + " (Neighbor)",
                    "x": new_x,
                    "y": new_y,
                    "w": w,
                    "h": h,
                    "is_neighbor": True
                })

        return projected_labels
