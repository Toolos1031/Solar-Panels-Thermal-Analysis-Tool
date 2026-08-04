```markdown
# Thermal PV Inspection Suite

A complete, end-to-end processing and inspection pipeline for DJI thermal drone imagery of solar photovoltaic (PV) farms. 

This repository contains a two-part software suite built with PyQt6:
1. **The Converter:** Automates radiometric TIFF generation, RTK EXIF extraction, and YOLO-based solar panel segmentation.
2. **The Annotator:** A dual-canvas, hardware-accelerated GUI for inspecting synchronized RGB and Thermal images, projecting spatial annotations, and measuring exact radiometric temperatures.

---

## ✨ Suite Features

### 1. DJI Thermal Converter (Preprocessing Pipeline)
* **Batch Radiometric Conversion:** Uses the DJI Thermal SDK (`dji_irp.exe`) to convert standard `_T.JPG` images into 32-bit float radiometric `.tif` arrays, allowing for precise environmental overrides (Emissivity, Distance, Humidity, Reflection).
* **RTK & Metadata Extraction:** Leverages `exiftool` to build a database of drone coordinates (Latitude, Longitude, Relative Altitude, Gimbal Pitch, Flight Yaw).
* **AI Segmentation & Pre-flagging:** Runs a YOLOv8 model (`best.pt`) on RGB images to segment solar panels, maps them to the thermal array, calculates $\Delta T$ (Max-Min temperature), and automatically flags panels exceeding a 10°C threshold.
* **JSON Generation:** Compiles all spatial, thermal, and segmentation data into a single `project_data.json` file.

### 2. Thermal PV Annotator (Inspection GUI)
* **Synchronized Dual-Canvas Viewing:** Pan and zoom synchronously across RGB and Thermal images.
* **Radiometric Temperature Analysis:** Extract real temperature data directly from the 32-bit TIFFs.
  * **Spot Tool (Shortcut `S`):** Click any pixel to get its exact temperature.
  * **Box Tool (Shortcut `B`):** Draw a bounding box to automatically calculate Min/Max temperatures and locate the exact hottest/coldest pixels.
* **Intelligent Neighbor Projection:** Uses drone RTK coordinates to mathematically project bounding box labels from adjacent photos onto the current frame, maintaining spatial awareness across flight lines.
* **Localized CLAHE Enhancement (Shortcut `T`):** Dynamically applies Contrast Limited Adaptive Histogram Equalization *only* inside YOLO-segmented bounding boxes, highlighting thermal anomalies without blowing out the background terrain.
* **Interactive Map View:** Visualizes the entire drone flight path on an orthophoto, color-coding assessed vs. pre-flagged photos.

---

## 🚀 Installation & Prerequisites

### 1. Python Dependencies
Ensure you have Python 3.9+ installed. Install the required packages:
```bash
pip install PyQt6 opencv-python numpy tifffile pandas ultralytics

```

### 2. External Tools Required

To run the **Converter**, you must download two external command-line tools:

1. **[ExifTool](https://exiftool.org/):** Ensure `exiftool.exe` is either in your system PATH or located in the project directory.
2. **[DJI Thermal SDK](https://www.google.com/search?q=https://developer.dji.com/thermal-sdk/):** You must provide the path to `dji_irp.exe` in the Converter UI to process radiometric data.

---

## 📁 Repository Structure

```text
Thermal_tool/
├── README.md
└── src/
    ├── annotator/              # The Inspection GUI
    │   ├── main.py             # Entry point for Annotator
    │   ├── ui_theme.py         # Global Dark Theme QSS
    │   ├── assets/             # UI Graphics & Logos
    │   ├── models/             # Project Data & Spatial Logic
    │   ├── views/              # Start, Map, and Photo Views
    │   └── widgets/            # Custom Toolbars & Canvas Items
    │
    └── converter/              # The Preprocessing Pipeline
        ├── main.py             # Entry point for Converter
        ├── best.pt             # YOLOv8 Weights for Panel Segmentation
        ├── controllers/        # UI to Worker logic mapping
        ├── models/             # QThread Workers (Conversion, Exif, YOLO)
        └── views/              # Converter GUI Layout

```

---

## 🖥️ Usage Guide

### Phase 1: Preprocessing

Run the Converter to prepare your raw DJI drone data:

```bash
python src/converter/main.py

```

1. Select your input directory (raw `_T.JPG` and `_V.JPG` files) and an output directory.
2. Set the path to `dji_irp.exe` and `exiftool`.
3. Run the processing steps in order: **Convert** -> **Extract EXIF** -> **Generate JSON** -> **Run Segmentation**.

### Phase 2: Inspection & Annotation

Run the Annotator to review the processed data:

```bash
python src/annotator/main.py

```

1. Load the Output Directory, RGB Directory, Orthophoto, and the generated `project_data.json`.
2. Click **Load Project** to view the interactive map.
3. Click any marker on the map to begin inspecting the thermal signatures.

### ⌨️ Annotator Keyboard Shortcuts

| Key | Action |
| --- | --- |
| `S` | Toggle Spot Temperature Tool |
| `B` | Toggle Box Temperature Tool |
| `L` | Toggle Labeling Tool |
| `T` | Toggle Localized CLAHE Enhancement |
| `C` | Clear temporary temperature markers |
| `Del` / `D` | Delete selected annotation |
| `Left Arrow` | Previous Photo |
| `Right Arrow` | Next Photo |
| `Esc` | Return to Map View |

---

*Built for advanced photogrammetry and PV thermography workflows.*

```

```