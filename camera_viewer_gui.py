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
    QSpinBox,
    QMessageBox,
    QProgressDialog,
    QGroupBox,
    QGridLayout,
    QDoubleSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QStandardItemModel, QStandardItem
from settings_handler import SettingsHandler
from utils import save_raw_movie
import os
import datetime
import time

class TableView(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QTableView { font-size: 10pt; }")
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def update_data(self, data, row_labels=None, column_labels=None):
        self.clear()
        if not data:
            return

        if isinstance(data[0], list):  # 2D data
            self.setRowCount(len(data))
            self.setColumnCount(len(data[0]))
        else:  # 1D data
            self.setRowCount(1)
            self.setColumnCount(len(data))

        for i, row in enumerate(data):
            if isinstance(row, list):
                for j, value in enumerate(row):
                    self.setItem(i, j, QTableWidgetItem(str(value)))
            else:
                self.setItem(0, i, QTableWidgetItem(str(row)))

        if row_labels:
            self.setVerticalHeaderLabels(row_labels)
        if column_labels:
            self.setHorizontalHeaderLabels(column_labels)

    def clear_data(self):
        self.clear()
        self.setRowCount(0)
        self.setColumnCount(0)


class CameraViewerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Viewer App")
        self.showMaximized()
        
        self.settings_handler = SettingsHandler()
        self.setup_ui()
        self.connect_resolution_signals()
        self.validate_and_update_resolution()

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

        self.resolution_label = QLabel("Resolution: --x-- | FPS: --")
        self.resolution_label.setAlignment(Qt.AlignCenter)
        camera_frame_layout.addWidget(self.resolution_label)

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

        # Recording selection, analyze button, and refresh button
        selection_layout = QHBoxLayout()
        self.recording_combo = QComboBox()
        selection_layout.addWidget(self.recording_combo)
        self.analyze_button = QPushButton("Analyze")
        selection_layout.addWidget(self.analyze_button)
        self.refresh_button = QPushButton("Refresh")
        selection_layout.addWidget(self.refresh_button)
        recorded_layout.addLayout(selection_layout)

        # Analyzed image display
        self.analyzed_frame = QFrame()
        self.analyzed_frame.setFrameShape(QFrame.Box)
        self.analyzed_frame.setLineWidth(2)
        analyzed_frame_layout = QVBoxLayout(self.analyzed_frame)
        
        # Create visualization tabs
        self.visualization_tabs = QTabWidget()
        analyzed_frame_layout.addWidget(self.visualization_tabs)
        
        # Original tab
        original_tab = QWidget()
        original_layout = QVBoxLayout(original_tab)
        self.analyzed_label = QLabel()
        self.analyzed_label.setAlignment(Qt.AlignCenter)
        self.analyzed_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.analyzed_label.setMinimumSize(320, 240)  # Smaller minimum size
        self.original_resolution_label = QLabel("Original: --x--")
        self.original_resolution_label.setAlignment(Qt.AlignCenter)
        original_layout.addWidget(self.analyzed_label)
        original_layout.addWidget(self.original_resolution_label)
        self.visualization_tabs.addTab(original_tab, "Original")
        
        # Trailed tab
        trailed_tab = QWidget()
        trailed_layout = QVBoxLayout(trailed_tab)
        self.trailed_label = QLabel()
        self.trailed_label.setAlignment(Qt.AlignCenter)
        self.trailed_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.trailed_label.setMinimumSize(320, 240)  # Smaller minimum size
        self.trailed_resolution_label = QLabel("Original: --x--")
        self.trailed_resolution_label.setAlignment(Qt.AlignCenter)
        trailed_layout.addWidget(self.trailed_label)
        trailed_layout.addWidget(self.trailed_resolution_label)
        self.visualization_tabs.addTab(trailed_tab, "Trailed")
        
        # Heatmap tab
        heatmap_tab = QWidget()
        heatmap_layout = QVBoxLayout(heatmap_tab)
        self.heatmap_label = QLabel()
        self.heatmap_label.setAlignment(Qt.AlignCenter)
        self.heatmap_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.heatmap_label.setMinimumSize(320, 240)  # Smaller minimum size
        self.heatmap_resolution_label = QLabel("Original: --x--")
        self.heatmap_resolution_label.setAlignment(Qt.AlignCenter)
        heatmap_layout.addWidget(self.heatmap_label)
        heatmap_layout.addWidget(self.heatmap_resolution_label)
        self.visualization_tabs.addTab(heatmap_tab, "Heatmap")
        
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

        self.left_landmarks_table = TableView()
        analyzed_layout.addWidget(self.left_landmarks_table)

        self.right_landmarks_table = TableView()
        analyzed_layout.addWidget(self.right_landmarks_table)

        self.stats_table = TableView()
        analyzed_layout.addWidget(self.stats_table)

        recorded_layout.addLayout(analyzed_layout)

        self.tab_widget.addTab(recorded_tab, "Recorded Images")

        # Right side: Settings
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 1)

        self.settings_widget = QWidget()
        self.setup_settings_ui()
        right_layout.addWidget(self.settings_widget)

        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        right_layout.addStretch(1)

    def setup_settings_ui(self):
        settings_layout = QVBoxLayout()
        
        # Analysis Buttons
        analysis_group = QGroupBox("Analysis Control")
        analysis_layout = QVBoxLayout()
        
        self.start_analyze_button = QPushButton("Start Analyzing")
        analysis_layout.addWidget(self.start_analyze_button)
        
        self.stop_analyze_button = QPushButton("Stop Analyzing")
        self.stop_analyze_button.setEnabled(False)
        analysis_layout.addWidget(self.stop_analyze_button)
        
        analysis_group.setLayout(analysis_layout)
        settings_layout.addWidget(analysis_group)
        
        # Resolution Settings Group
        resolution_group = QGroupBox("Resolution")
        resolution_layout = QGridLayout()
        
        self.save_width_input = QSpinBox()
        self.save_width_input.setRange(320, 1920)
        self.save_width_input.setValue(self.settings_handler.get_setting("Resolution", "save_width"))
        
        self.save_height_input = QSpinBox()
        self.save_height_input.setRange(240, 1080)
        self.save_height_input.setValue(self.settings_handler.get_setting("Resolution", "save_height"))
        
        self.camera_width_input = QSpinBox()
        self.camera_width_input.setRange(320, 1920)
        self.camera_width_input.setValue(self.settings_handler.get_setting("Resolution", "camera_width"))
        
        self.camera_height_input = QSpinBox()
        self.camera_height_input.setRange(240, 1080)
        self.camera_height_input.setValue(self.settings_handler.get_setting("Resolution", "camera_height"))
        
        resolution_layout.addWidget(QLabel("Save Width:"), 0, 0)
        resolution_layout.addWidget(self.save_width_input, 0, 1)
        resolution_layout.addWidget(QLabel("Save Height:"), 1, 0)
        resolution_layout.addWidget(self.save_height_input, 1, 1)
        resolution_layout.addWidget(QLabel("Camera Width:"), 2, 0)
        resolution_layout.addWidget(self.camera_width_input, 2, 1)
        resolution_layout.addWidget(QLabel("Camera Height:"), 3, 0)
        resolution_layout.addWidget(self.camera_height_input, 3, 1)
        
        resolution_group.setLayout(resolution_layout)
        
        # Trailing Settings Group
        trailing_group = QGroupBox("Trailing")
        trailing_layout = QGridLayout()
        
        self.trail_length_input = QSpinBox()
        self.trail_length_input.setRange(1, 100)
        self.trail_length_input.setValue(self.settings_handler.get_setting("Trailing", "trail_length"))
        
        self.landmark_size_input = QSpinBox()
        self.landmark_size_input.setRange(1, 10)
        self.landmark_size_input.setValue(self.settings_handler.get_setting("Trailing", "landmark_size"))
        
        self.alpha_input = QDoubleSpinBox()
        self.alpha_input.setRange(0.1, 1.0)
        self.alpha_input.setSingleStep(0.1)
        self.alpha_input.setValue(self.settings_handler.get_setting("Trailing", "alpha"))
        
        trailing_layout.addWidget(QLabel("Trail Length:"), 0, 0)
        trailing_layout.addWidget(self.trail_length_input, 0, 1)
        trailing_layout.addWidget(QLabel("Landmark Size:"), 1, 0)
        trailing_layout.addWidget(self.landmark_size_input, 1, 1)
        trailing_layout.addWidget(QLabel("Trail Opacity:"), 2, 0)
        trailing_layout.addWidget(self.alpha_input, 2, 1)
        
        trailing_group.setLayout(trailing_layout)
        
        # Add save settings button
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self.save_settings)
        
        # Add groups to settings layout
        settings_layout.addWidget(resolution_group)
        settings_layout.addWidget(trailing_group)
        settings_layout.addWidget(self.save_settings_button)
        settings_layout.addStretch()
        
        self.settings_widget.setLayout(settings_layout)

    def connect_resolution_signals(self):
        self.save_width_input.valueChanged.connect(self.validate_resolution)
        self.save_height_input.valueChanged.connect(self.validate_resolution)
        self.camera_width_input.valueChanged.connect(self.validate_resolution)
        self.camera_height_input.valueChanged.connect(self.validate_resolution)

    def validate_and_update_resolution(self):
        # Validate loaded settings
        if not self.validate_resolution():
            # If invalid, reset to default 16:9 resolution
            self.save_width_input.setValue(1280)
            self.save_height_input.setValue(720)
            self.camera_width_input.setValue(1280)
            self.camera_height_input.setValue(720)

    def get_save_resolution(self):
        return (self.save_width_input.value(), self.save_height_input.value())

    def get_camera_resolution(self):
        return (self.camera_width_input.value(), self.camera_height_input.value())

    def save_settings(self):
        if not self.validate_resolution():
            QMessageBox.warning(self, "Invalid Resolution", 
                              "Please ensure the resolution has a valid aspect ratio (16:9 or 4:3)")
            return

        self.settings_handler.settings["Resolution"]["save_width"] = self.save_width_input.value()
        self.settings_handler.settings["Resolution"]["save_height"] = self.save_height_input.value()
        self.settings_handler.settings["Resolution"]["camera_width"] = self.camera_width_input.value()
        self.settings_handler.settings["Resolution"]["camera_height"] = self.camera_height_input.value()
        
        self.settings_handler.settings["Trailing"]["trail_length"] = self.trail_length_input.value()
        self.settings_handler.settings["Trailing"]["landmark_size"] = self.landmark_size_input.value()
        self.settings_handler.settings["Trailing"]["alpha"] = self.alpha_input.value()
        
        if self.settings_handler.save_settings():
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully!")
        else:
            QMessageBox.warning(self, "Save Error", "Failed to save settings. Please try again.")

    def validate_resolution(self):
        width = self.save_width_input.value()
        height = self.save_height_input.value()

        # Validate aspect ratio (roughly 16:9 or 4:3)
        aspect_ratio = width / height
        is_valid = (1.7 <= aspect_ratio <= 1.8) or (1.3 <= aspect_ratio <= 1.4)

        # Update spinbox styling based on validation
        style = "" if is_valid else "background-color: #FFEBEE;"  # Light red for invalid
        self.save_width_input.setStyleSheet(style)
        self.save_height_input.setStyleSheet(style)
        
        return is_valid

    def update_camera_frame(self, pixmap):
        scaled_pixmap = pixmap.scaled(
            self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.camera_label.setPixmap(scaled_pixmap)

    def update_analyzed_frame(self, pixmap, original_size=None):
        if pixmap:
            # Calculate scaling to maintain aspect ratio
            label_size = self.analyzed_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.analyzed_label.setPixmap(scaled_pixmap)
            if original_size:
                self.original_resolution_label.setText(f"Original: {original_size[0]}x{original_size[1]}")
        else:
            self.analyzed_label.clear()
            self.original_resolution_label.setText("Original: --x--")

    def update_trailed_frame(self, pixmap, original_size=None):
        if pixmap:
            label_size = self.trailed_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.trailed_label.setPixmap(scaled_pixmap)
            if original_size:
                self.trailed_resolution_label.setText(f"Original: {original_size[0]}x{original_size[1]}")
        else:
            self.trailed_label.clear()
            self.trailed_resolution_label.setText("Original: --x--")

    def update_heatmap_frame(self, pixmap, original_size=None):
        if pixmap:
            label_size = self.heatmap_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.heatmap_label.setPixmap(scaled_pixmap)
            if original_size:
                self.heatmap_resolution_label.setText(f"Original: {original_size[0]}x{original_size[1]}")
        else:
            self.heatmap_label.clear()
            self.heatmap_resolution_label.setText("Original: --x--")

    def set_progress(self, value):
        self.progress_bar.setValue(value)

    def show_progress_bar(self, visible):
        self.progress_bar.setVisible(visible)

    def append_log(self, message):
        self.log_text.append(message)

    def set_frame_slider_range(self, min_value, max_value):
        self.frame_slider.setRange(min_value, max_value)

    def get_current_frame(self):
        return self.frame_slider.value()

    def set_current_frame(self, frame):
        self.frame_slider.setValue(frame)
        self.frame_number_label.setText(f"Frame: {frame}")

    def clear_analysis_data(self):
        self.update_analyzed_frame(None)
        self.update_trailed_frame(None)
        self.update_heatmap_frame(None)
        self.left_landmarks_table.clear_data()
        self.right_landmarks_table.clear_data()
        self.stats_table.clear_data()
        self.set_frame_slider_range(0, 0)
        self.frame_number_label.setText("Frame: 0")

    def update_recording_combo(self, mp4_files):
        self.recording_combo.clear()
        self.recording_combo.addItems(mp4_files)

    def format_value(self, value):
        try:
            num_value = float(value)
            return f"{num_value:.5f}"
        except (ValueError, TypeError):
            return str(value)

    def update_landmarks_table(self, table, landmarks):
        data = []
        column_labels = []
        for landmark in landmarks:
            if landmark[0] == "FRAME":
                column_labels.append(landmark[0])
                data.append(str(landmark[1]))
            else:
                column_labels.append(landmark[0])
                data.append(
                    f"x: {self.format_value(landmark[1])}\ny: {self.format_value(landmark[2])}\nz: {self.format_value(landmark[3])}"
                )
        table.update_data(data, column_labels=column_labels)
        table.resizeRowsToContents()

    def update_stats_table(self, parsed_data):
        if parsed_data is None or (
            isinstance(parsed_data, list) and len(parsed_data) == 0
        ):
            self.stats_table.clear_data()
            return

        data = []
        row_labels = list(parsed_data.get("left", {}).keys())
        column_labels = ["FRAME", "LEFT", "RIGHT"]

        frame_number = (
            parsed_data.get("frame", 0) if isinstance(parsed_data, dict) else 0
        )

        for stat_name in row_labels:
            left_value = parsed_data.get("left", {}).get(stat_name, "N/A")
            right_value = parsed_data.get("right", {}).get(stat_name, "N/A")
            data.append(
                [
                    str(frame_number),
                    self.format_value(left_value),
                    self.format_value(right_value),
                ]
            )

        self.stats_table.update_data(
            data, row_labels=row_labels, column_labels=column_labels
        )

    def update_resolution_label(self, frame):
        if frame is not None:
            height, width = frame.shape[:2]
            fps = self.get_fps()
            resolution_text = f"Resolution: {width}x{height} | FPS: {fps:.1f}"
            self.resolution_label.setText(resolution_text)
            
    def get_fps(self):
        current_time = time.time()
        if not hasattr(self, 'last_frame_time'):
            self.last_frame_time = current_time
            return 0.0
        
        fps = 1.0 / (current_time - self.last_frame_time)
        self.last_frame_time = current_time
        return fps

    def save_raw_movie(self):
        if not self.frames:
            QMessageBox.warning(self, "Save Error", "No frames available to save")
            return
            
        # Create output directory if it doesn't exist
        os.makedirs("raw_movie", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"raw_movie/raw_movie_{timestamp}.mp4"
        
        # Get current resolution settings
        width, height = self.get_save_resolution()
        
        # Show progress dialog
        progress = QProgressDialog("Saving video...", None, 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setValue(0)
        
        # Process frames and update progress
        try:
            total_frames = len(self.frames)
            progress.setMaximum(total_frames)
            
            success, message = save_raw_movie(self.frames, output_path, fps=30, 
                                            width=width, height=height)
            
            if success:
                QMessageBox.information(self, "Success", message)
                self.log_message(message)
            else:
                QMessageBox.warning(self, "Save Error", message)
                self.log_message(f"Error saving video: {message}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save video: {str(e)}")
            self.log_message(f"Critical error saving video: {str(e)}")
        finally:
            progress.close()
