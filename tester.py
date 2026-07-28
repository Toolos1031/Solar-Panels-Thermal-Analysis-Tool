import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGraphicsView, QGraphicsScene, QHBoxLayout, QMainWindow, QApplication, QGraphicsEllipseItem, QStatusBar
from PyQt6.QtGui import QPixmap, QPen, QBrush, QColor
from PyQt6.QtCore import Qt
import sys
import json
from widgets.annotation_toolbar import AnnotationToolbar


class Tester(QMainWindow):
    def __init__(self):
        super().__init__()

        toolbar = AnnotationToolbar()
        self.addToolBar(toolbar)

        self.setStatusBar(QStatusBar(self))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Tester()
    window.show()
    sys.exit(app.exec())
