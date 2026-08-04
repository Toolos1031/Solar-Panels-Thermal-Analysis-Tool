# ui_theme.py

DARK_THEME = """

/* Optional: Make the Start Card slightly transparent so the image peeks through */
QGroupBox#startCard {
    background-color: rgba(24, 24, 37, 220); /* 220 is the opacity (0-255) */
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 20px;
}

/* Global Widget Styles */
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}

/* Primary Button Styling */
QPushButton {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 8px 16px;
    font-weight: bold;
    color: #cdd6f4;
}

QPushButton:hover {
    background-color: #45475a;
    border-color: #585b70;
}

QPushButton:pressed {
    background-color: #585b70;
}

/* Special ID for High-Priority Buttons (Like 'Load Project') */
QPushButton#primaryBtn {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
}

QPushButton#primaryBtn:hover {
    background-color: #b4befe;
}

/* Inputs and Dropdowns */
QLineEdit, QComboBox {
    background-color: #11111b;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 6px;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    selection-color: #11111b;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #89b4fa;
}

/* Toolbars */
QToolBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 5px;
    spacing: 10px;
}

QToolButton {
    background-color: transparent;
    padding: 6px 10px;
    border-radius: 5px;
    color: #cdd6f4;
}

QToolButton:hover {
    background-color: #313244;
}

QToolButton:checked {
    background-color: #89b4fa;
    color: #11111b;
    font-weight: bold;
}

/* Graphics View (The Image Canvas) */
QGraphicsView {
    background-color: #11111b;
    border: 1px solid #313244;
    border-radius: 5px;
}

/* Group Boxes (Cards) */
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 20px;
    background-color: #181825;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 10px;
    color: #89b4fa;
    font-weight: bold;
    font-size: 16px;
}
"""