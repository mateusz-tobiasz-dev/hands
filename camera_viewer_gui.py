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
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSlider,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QStandardItemModel, QStandardItem


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

        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget, 3)

        # Tab 1: Camera view and controls
        camera_tab = QWidget()
        camera_layout = QVBoxLayout(camera_tab)

        # Camera selection and connect button
        control_layout = QHBoxLayout()
        self.camera_combo = QComboBox()
        control_layout.addWidget(self.camera_combo)

        self.connect_button = QPushButton("Connect")
        control_layout.addWidget(self.connect_button)

        camera_layout.addLayout(control_layout)

        # Camera feed display
        self.camera_frame = QFrame()
        self.camera_frame.setFrameShape(QFrame.Box)
        self.camera_frame.setLineWidth(2)
        camera_frame_layout = QVBoxLayout(self.camera_frame)

        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.camera_label.setMinimumSize(640, 480)  # Set minimum size
        camera_frame_layout.addWidget(self.camera_label)

        camera_layout.addWidget(self.camera_frame, 1)

        # Log section
        self.log_frame = QFrame()
        self.log_frame.setFrameShape(QFrame.Box)
        self.log_frame.setLineWidth(2)
        log_layout = QVBoxLayout(self.log_frame)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        camera_layout.addWidget(self.log_frame)

        self.tab_widget.addTab(camera_tab, "Camera View")

        # Tab 2: Recorded images and analysis
        recorded_tab = QWidget()
        recorded_layout = QVBoxLayout(recorded_tab)

        # Recording selection and analyze button
        selection_layout = QHBoxLayout()
        self.recording_combo = QComboBox()
        selection_layout.addWidget(self.recording_combo)
        self.analyze_button = QPushButton("Analyze")
        selection_layout.addWidget(self.analyze_button)
        recorded_layout.addLayout(selection_layout)

        # Analyzed image display
        self.analyzed_frame = QFrame()
        self.analyzed_frame.setFrameShape(QFrame.Box)
        self.analyzed_frame.setLineWidth(2)
        analyzed_frame_layout = QVBoxLayout(self.analyzed_frame)
        self.analyzed_label = QLabel()
        self.analyzed_label.setAlignment(Qt.AlignCenter)
        self.analyzed_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.analyzed_label.setMinimumSize(640, 480)  # Set minimum size
        analyzed_frame_layout.addWidget(self.analyzed_label)
        recorded_layout.addWidget(self.analyzed_frame, 1)  # Give it more vertical space

        # Playback controls
        playback_layout = QHBoxLayout()
        self.start_play_button = QPushButton("Start")
        self.pause_play_button = QPushButton("Pause")
        self.stop_play_button = QPushButton("Stop")
        playback_layout.addWidget(self.start_play_button)
        playback_layout.addWidget(self.pause_play_button)
        playback_layout.addWidget(self.stop_play_button)
        recorded_layout.addLayout(playback_layout)

        # Frame slider and frame number
        slider_layout = QHBoxLayout()
        self.frame_slider = QSlider(Qt.Horizontal)
        slider_layout.addWidget(self.frame_slider, 9)
        self.frame_number_label = QLabel("Frame: 0")
        slider_layout.addWidget(self.frame_number_label, 1)
        recorded_layout.addLayout(slider_layout)

        # Analyzed data frames
        analyzed_layout = QHBoxLayout()

        self.left_landmarks_table = QTableWidget()
        self.left_landmarks_table.setStyleSheet("QTableView { font-size: 10pt; }")
        self.left_landmarks_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        analyzed_layout.addWidget(self.left_landmarks_table)

        self.right_landmarks_table = QTableWidget()
        self.right_landmarks_table.setStyleSheet("QTableView { font-size: 10pt; }")
        self.right_landmarks_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        analyzed_layout.addWidget(self.right_landmarks_table)

        self.stats_table = QTableWidget()
        self.stats_table.setStyleSheet("QTableView { font-size: 10pt; }")
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stats_table.setHorizontalHeaderLabels(["Stat Name", "Left", "Right"])
        analyzed_layout.addWidget(self.stats_table)

        recorded_layout.addLayout(analyzed_layout)

        self.tab_widget.addTab(recorded_tab, "Recorded Images")

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

        self.start_analyze_button = QPushButton("Start Analyzing")
        settings_layout.addWidget(self.start_analyze_button)

        self.stop_analyze_button = QPushButton("Stop Analyzing")
        self.stop_analyze_button.setEnabled(False)
        settings_layout.addWidget(self.stop_analyze_button)

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

    def update_analyzed_frame(self, pixmap):
        if pixmap:
            scaled_pixmap = pixmap.scaled(
                self.analyzed_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.analyzed_label.setPixmap(scaled_pixmap)
        else:
            self.analyzed_label.clear()

    def set_progress(self, value):
        self.progress_bar.setValue(value)

    def show_progress_bar(self, visible):
        self.progress_bar.setVisible(visible)

    def append_log(self, message):
        self.log_text.append(message)

    def update_landmarks_table(self, table, landmarks):
        table.setRowCount(len(landmarks))
        for row, (name, x, y) in enumerate(landmarks):
            table.setItem(row, 0, QTableWidgetItem(name))
            table.setItem(row, 1, QTableWidgetItem(str(x)))
            table.setItem(row, 2, QTableWidgetItem(str(y)))

    def update_stats_table(self, stats):
        self.stats_table.setRowCount(len(stats))
        for row, (name, left, right) in enumerate(stats):
            self.stats_table.setItem(row, 0, QTableWidgetItem(name))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(left)))
            self.stats_table.setItem(row, 2, QTableWidgetItem(str(right)))

    def set_frame_slider_range(self, min_value, max_value):
        self.frame_slider.setRange(min_value, max_value)

    def get_current_frame(self):
        return self.frame_slider.value()

    def set_current_frame(self, frame):
        self.frame_slider.setValue(frame)
        self.frame_number_label.setText(f"Frame: {frame}")

    def clear_analysis_data(self):
        self.update_analyzed_frame(None)
        self.left_landmarks_table.setRowCount(0)
        self.right_landmarks_table.setRowCount(0)
        self.stats_table.setRowCount(0)
        self.set_frame_slider_range(0, 0)
        self.frame_number_label.setText("Frame: 0")
