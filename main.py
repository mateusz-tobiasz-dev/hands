import sys
from PyQt5.QtWidgets import QApplication
from src.core.hand_tracking_app import CameraViewerApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraViewerApp()
    window.show()
    sys.exit(app.exec_())
