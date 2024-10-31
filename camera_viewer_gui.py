from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QLabel,
    QFrame,
    QTextEdit,
    QProgressBar,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap


class CameraViewerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Viewer App")
        self.showMaximized()

        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left side: Camera view and controls
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 3)

        # Camera selection and connect button
        control_layout = QHBoxLayout()
        self.camera_combo = QComboBox()
        control_layout.addWidget(self.camera_combo)

        self.connect_button = QPushButton("Connect")
        control_layout.addWidget(self.connect_button)

        left_layout.addLayout(control_layout)

        # Camera feed display
        self.camera_frame = QFrame()
        self.camera_frame.setFrameShape(QFrame.Box)
        self.camera_frame.setLineWidth(2)
        camera_frame_layout = QVBoxLayout(self.camera_frame)

        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        camera_frame_layout.addWidget(self.camera_label)

        left_layout.addWidget(self.camera_frame, 1)

        # Log section
        self.log_frame = QFrame()
        self.log_frame.setFrameShape(QFrame.Box)
        self.log_frame.setLineWidth(2)
        log_layout = QVBoxLayout(self.log_frame)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        left_layout.addWidget(self.log_frame)

        # Right side: Settings
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 1)

        settings_frame = QFrame()
        settings_frame.setFrameShape(QFrame.Box)
        settings_frame.setLineWidth(2)
        settings_layout = QVBoxLayout(settings_frame)

        settings_label = QLabel("Settings")
        settings_label.setAlignment(Qt.AlignCenter)
        settings_layout.addWidget(settings_label)

        self.start_button = QPushButton("Start Analyzing")
        settings_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Analyzing")
        self.stop_button.setEnabled(False)
        settings_layout.addWidget(self.stop_button)

        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        settings_layout.addWidget(self.progress_bar)

        settings_layout.addStretch(1)
        right_layout.addWidget(settings_frame)

    def update_camera_frame(self, pixmap):
        scaled_pixmap = pixmap.scaled(
            self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.camera_label.setPixmap(scaled_pixmap)

    def set_progress(self, value):
        self.progress_bar.setValue(value)

    def show_progress_bar(self, visible):
        self.progress_bar.setVisible(visible)

    def append_log(self, message):
        self.log_text.append(message)
