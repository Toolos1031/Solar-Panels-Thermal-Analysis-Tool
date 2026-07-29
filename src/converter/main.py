import sys
import warnings
from PyQt6.QtWidgets import QApplication
from views.view import DJIThermalConverterView
from controllers.controller import DJIThermalConverterController

warnings.filterwarnings("ignore")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Initialize MVC components
    view = DJIThermalConverterView()
    controller = DJIThermalConverterController(view)
    
    view.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()