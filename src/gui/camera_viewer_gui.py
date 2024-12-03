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
    QDoubleSpinBox,
    QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QStandardItemModel, QStandardItem
from src.utils.settings_handler import SettingsHandler
from src.utils.utils import save_raw_movie
from src.gui.table_view import TableView
import os
import datetime
import time
import cv2
import csv
from PyQt5.QtCore import Qt, QTimer
from src.utils.slider import RangeSlider


class CameraViewerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Viewer App")
        self.showMaximized()
        
        self.settings_handler = SettingsHandler()
        self.resolution_presets = {
            "1:1 Ratio": [
                ("640x640", 320, 320),
                ("640x640", 640, 640),
                ("800x800", 800, 800),
                ("1024x1024", 1024, 1024)
            ],
            "4:3 Ratio": [
                ("320x240", 320, 240),
                ("640x480", 640, 480),
                ("800x600", 800, 600),
                ("1024x768", 1024, 768),
                ("1600x1200", 1600, 1200)
            ],
            "16:9 Ratio": [
                ("640x360", 640, 360),
                ("1280x720", 1280, 720),
                ("1600x900", 1600, 900),
                ("1920x1080", 1920, 1080)
            ]
        }
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

        self.camera_resolution_label = QLabel("Resolution: --x-- | FPS: --")
        self.camera_resolution_label.setAlignment(Qt.AlignCenter)
        camera_frame_layout.addWidget(self.camera_resolution_label)

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
        self.original_resolution_label = QLabel("Original: --x-- | FPS: --")
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
        self.trailed_resolution_label = QLabel("Original: --x-- | FPS: --")
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
        self.heatmap_resolution_label = QLabel("Original: --x-- | FPS: --")
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
        
        self.min_frame_spin = QSpinBox()
        self.min_frame_spin.setMinimum(0)
        self.min_frame_spin.valueChanged.connect(self.on_min_frame_changed)
        slider_layout.addWidget(self.min_frame_spin)
        self.max_frame_spin = QSpinBox()
        self.max_frame_spin.setMinimum(0)
        self.max_frame_spin.valueChanged.connect(self.on_max_frame_changed)
        slider_layout.addWidget(self.max_frame_spin)

        self.frame_slider = RangeSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(0)
        self.frame_slider.sliderMoved.connect(self.on_slider_moved)
        slider_layout.addWidget(self.frame_slider, 9)
        self.frame_number_label = QLabel("Frames: 0-0")
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
        
        self.start_analyze_button = QPushButton("Start Recording")
        analysis_layout.addWidget(self.start_analyze_button)
        
        self.stop_analyze_button = QPushButton("Stop Recording")
        self.stop_analyze_button.setEnabled(False)
        analysis_layout.addWidget(self.stop_analyze_button)
        
        analysis_group.setLayout(analysis_layout)
        settings_layout.addWidget(analysis_group)
        
        # Resolution Settings Group
        resolution_group = QGroupBox("Resolution")
        resolution_layout = QGridLayout()
        
        # Resolution presets
        resolution_layout.addWidget(QLabel("Presets:"), 0, 0)
        self.preset_combo = QComboBox()
        for ratio in self.resolution_presets:
            self.preset_combo.addItem(ratio)
        resolution_layout.addWidget(self.preset_combo, 0, 1)
        
        self.resolution_combo = QComboBox()
        self.resolution_combo.currentTextChanged.connect(self.on_preset_selected)
        resolution_layout.addWidget(self.resolution_combo, 0, 2)
        
        # Manual resolution inputs
        resolution_layout.addWidget(QLabel("Custom Width:"), 1, 0)
        self.camera_width_input = QSpinBox()
        self.camera_width_input.setRange(320, 1920)
        self.camera_width_input.setValue(self.settings_handler.get_setting("Resolution", "camera_width"))
        resolution_layout.addWidget(self.camera_width_input, 1, 1)
        
        resolution_layout.addWidget(QLabel("Custom Height:"), 2, 0)
        self.camera_height_input = QSpinBox()
        self.camera_height_input.setRange(240, 1080)
        self.camera_height_input.setValue(self.settings_handler.get_setting("Resolution", "camera_height"))
        resolution_layout.addWidget(self.camera_height_input, 2, 1)
        
        resolution_group.setLayout(resolution_layout)
        settings_layout.addWidget(resolution_group)
        
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
        
        self.black_background_checkbox = QCheckBox("Black Background")
        self.black_background_checkbox.setChecked(self.settings_handler.get_setting("Trailing", "black_background"))
        trailing_layout.addWidget(self.black_background_checkbox, 3, 0, 1, 2)
        
        self.alpha_fade_checkbox = QCheckBox("Fade Trail Effect")
        self.alpha_fade_checkbox.setChecked(self.settings_handler.get_setting("Trailing", "alpha_fade"))
        trailing_layout.addWidget(self.alpha_fade_checkbox, 4, 0, 1, 2)
        self.save_trailed_movie_button = QPushButton("Save Trailed Movie")
        self.save_trailed_movie_button.clicked.connect(self.save_trailed_movie)
        trailing_layout.addWidget(self.save_trailed_movie_button, 5, 0, 1, 2)
        trailing_group.setLayout(trailing_layout)
        
        self.save_partial_csv_button = QPushButton("Save Partial CSV")
        self.save_partial_csv_button.clicked.connect(self.save_partial_csv)

        # Add save settings button
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self.save_settings)
        
        # Add groups to settings layout
        settings_layout.addWidget(trailing_group)
        settings_layout.addWidget(self.save_partial_csv_button)
        settings_layout.addWidget(self.save_settings_button)
        settings_layout.addStretch()
        
        self.settings_widget.setLayout(settings_layout)

    def on_preset_selected(self, text):
        if not text:
            return
        width, height = map(int, text.split('x'))
        self.camera_width_input.setValue(width)
        self.camera_height_input.setValue(height)

    def connect_resolution_signals(self):
        self.preset_combo.currentTextChanged.connect(self.update_resolution_presets)
        
    def update_resolution_presets(self, ratio):
        self.resolution_combo.clear()
        if ratio in self.resolution_presets:
            for preset in self.resolution_presets[ratio]:
                self.resolution_combo.addItem(preset[0])

    def update_resolution_display(self, width, height, fps):
        self.camera_resolution_label.setText(f"Resolution: {width}x{height} | FPS: {fps:.1f}")

    def save_settings(self):
        if not self.validate_resolution():
            QMessageBox.warning(self, "Invalid Resolution", 
                              "Please use a valid resolution ratio (1:1, 16:9, or 4:3) within range 320x240 to 1920x1080")
            return False

        # Save all settings
        self.settings_handler.set_setting("Resolution", "camera_width", self.camera_width_input.value())
        self.settings_handler.set_setting("Resolution", "camera_height", self.camera_height_input.value())
        
        self.settings_handler.set_setting("Trailing", "trail_length", self.trail_length_input.value())
        self.settings_handler.set_setting("Trailing", "landmark_size", self.landmark_size_input.value())
        self.settings_handler.set_setting("Trailing", "alpha", self.alpha_input.value())
        self.settings_handler.set_setting("Trailing", "black_background", self.black_background_checkbox.isChecked())
        self.settings_handler.set_setting("Trailing", "alpha_fade", self.alpha_fade_checkbox.isChecked())

        self.settings_handler.save_settings()
        
        # Reconnect camera if it's currently connected
        if hasattr(self, 'camera_manager') and self.camera_manager.camera:
            self.log("Settings saved, reconnecting camera...")
            self.toggle_camera()  # Disconnect
            self.toggle_camera()  # Connect with new resolution
        else:
            self.log("Settings saved successfully")
            
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully!")
        return True

    def validate_resolution(self):
        camera_width = self.camera_width_input.value()
        camera_height = self.camera_height_input.value()
        
        # Basic range check
        if not (320 <= camera_width <= 1920 and 240 <= camera_height <= 1080):
            return False
            
        # Check aspect ratios (1:1, 16:9, 4:3)
        ratio = camera_width / camera_height
        allowed_ratios = [1.0, 16/9, 4/3]  # 1:1, 16:9, 4:3
        ratio_tolerance = 0.01  # Allow small deviation
        
        return any(abs(ratio - allowed) < ratio_tolerance for allowed in allowed_ratios)

    def validate_and_update_resolution(self):
        if not self.validate_resolution():
            self.camera_width_input.setValue(640)
            self.camera_height_input.setValue(640)
            self.validate_resolution()

    def get_camera_resolution(self):
        return (self.camera_width_input.value(), self.camera_height_input.value())

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
                current_text = self.original_resolution_label.text()
                fps_text = " | FPS: --" if " | FPS: " not in current_text else current_text[current_text.find(" | FPS: "):]
                self.original_resolution_label.setText(f"Original: {original_size[0]}x{original_size[1]}{fps_text}")
        else:
            self.analyzed_label.clear()
            self.original_resolution_label.setText("Original: --x-- | FPS: --")

    def update_trailed_frame(self, pixmap, original_size=None):
        if pixmap:
            label_size = self.trailed_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.trailed_label.setPixmap(scaled_pixmap)
            if original_size:
                current_text = self.trailed_resolution_label.text()
                fps_text = " | FPS: --" if " | FPS: " not in current_text else current_text[current_text.find(" | FPS: "):]
                self.trailed_resolution_label.setText(f"Original: {original_size[0]}x{original_size[1]}{fps_text}")
        else:
            self.trailed_label.clear()
            self.trailed_resolution_label.setText("Original: --x-- | FPS: --")

    def update_heatmap_frame(self, pixmap, original_size=None):
        if pixmap:
            label_size = self.heatmap_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.heatmap_label.setPixmap(scaled_pixmap)
            if original_size:
                current_text = self.heatmap_resolution_label.text()
                fps_text = " | FPS: --" if " | FPS: " not in current_text else current_text[current_text.find(" | FPS: "):]
                self.heatmap_resolution_label.setText(f"Original: {original_size[0]}x{original_size[1]}{fps_text}")
        else:
            self.heatmap_label.clear()
            self.heatmap_resolution_label.setText("Original: --x-- | FPS: --")

    def set_progress(self, value):
        self.progress_bar.setValue(value)

    def show_progress_bar(self, visible):
        self.progress_bar.setVisible(visible)

    def append_log(self, message):
        self.log_text.append(message)

    def set_frame_slider_range(self, min_val, max_val):
        """Set the range of the frame slider"""
        self.frame_slider.setMinimum(min_val)
        self.frame_slider.setMaximum(max_val)
        self.frame_slider.setLow(min_val)
        self.frame_slider.setHigh(max_val)
        # Update spinboxes
        self.min_frame_spin.setRange(min_val, max_val)
        self.max_frame_spin.setRange(min_val, max_val)
        self.min_frame_spin.setValue(min_val)
        self.max_frame_spin.setValue(max_val)
        self.frame_number_label.setText(f"Frames: {min_val}-{max_val}")

    def get_current_frame(self):
        """Get current frame from slider"""
        return self.frame_slider.low()

    def set_current_frame(self, frame):
        """Set current frame in slider"""
        self.frame_slider.setLow(frame)
        self.frame_number_label.setText(f"Frames: {frame}-{self.frame_slider.high()}")

    def on_slider_moved(self, low, high):
        """Handle range slider movement"""
        self.frame_number_label.setText(f"Frames: {low}-{high}")
        self.update_frame_from_slider()  # This will call the app's method through inheritance

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
    
    def save_trailed_movie(self):
        """Save a movie with trailed landmarks using current settings and selected frame range"""
        recording_name = self.recording_combo.currentText()
        if not recording_name:
            self.log("No recording selected")
            return
        
        # Get frame range from slider
        start_frame = self.frame_slider.low()
        end_frame = self.frame_slider.high()
        
        # Create output directory
        output_dir = "src/data/trailed_movie"
        os.makedirs(output_dir, exist_ok=True)
        
        # Get current recording name and check for CSV data
        timestamp = recording_name[10:-4]  # Remove "raw_movie_" prefix and ".mp4" suffix
        csv_filename = f"csv_{timestamp}.csv"
        csv_path = os.path.join("src/data/csv_data", csv_filename)
        
        if not os.path.exists(csv_path):
            QMessageBox.warning(self, "Warning", "CSV data not found. Please analyze the recording first.")
            return
            
        # Add frame range to output filename
        output_path = os.path.join(output_dir, f"trailed_{timestamp}_frames_{start_frame}-{end_frame}.mp4")
        
        if os.path.exists(output_path):
            reply = QMessageBox.question(self, "File exists", 
                                    "A file with this name already exists. Do you want to replace it?",
                                    QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        try:
            self.show_progress_bar(True)
            self.set_progress(0)
            
            # Load the recording
            recording_path = os.path.join("src/data/raw_movie", recording_name)
            cap = cv2.VideoCapture(recording_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Load CSV data
            analyzed_data = []
            with open(csv_path, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    analyzed_data.append(row)
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Process frames in selected range
            total_frames = end_frame - start_frame + 1
            for frame_idx in range(start_frame, end_frame + 1):
                # Read the original frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Generate trailed frame using current settings
                trailed_frame = self.visualization_manager.generate_trailed_frame(
                    frame,
                    analyzed_data,
                    frame_idx
                )
                out.write(trailed_frame)
                
                # Update progress
                progress = int((frame_idx - start_frame + 1) / total_frames * 100)
                self.set_progress(progress)
                
            cap.release()
            out.release()
            self.log(f"Saved trailed movie: {output_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save trailed movie: {str(e)}")
        finally:
            self.show_progress_bar(False)
            self.set_progress(0)
            
    def on_min_frame_changed(self, value):
        """Handle minimum frame spinbox change"""
        if value <= self.frame_slider.high():
            self.frame_slider.setLow(value)
            self.frame_number_label.setText(f"Frames: {value}-{self.frame_slider.high()}")
            self.update_frame_from_slider()

    def on_max_frame_changed(self, value):
        """Handle maximum frame spinbox change"""
        if value >= self.frame_slider.low():
            self.frame_slider.setHigh(value)
            self.frame_number_label.setText(f"Frames: {self.frame_slider.low()}-{value}")
            
    def save_partial_csv(self):
        """Save CSV data for the selected frame range"""
        recording_name = self.recording_combo.currentText()
        if not recording_name:
            self.log("No recording selected")
            return
            
        # Get frame range from slider
        start_frame = self.frame_slider.low()
        end_frame = self.frame_slider.high()
        
        # Create output directory
        output_dir = "src/data/part_csv"
        os.makedirs(output_dir, exist_ok=True)
        
        # Get current recording name and check for CSV data
        timestamp = recording_name[10:-4]  # Remove "raw_movie_" prefix and ".mp4" suffix
        csv_filename = f"csv_{timestamp}.csv"
        csv_path = os.path.join(output_dir, csv_filename)
        
        if not os.path.exists(csv_path):
            QMessageBox.warning(self, "Warning", "CSV data not found. Please analyze the recording first.")
            return
            
        # Create output filename with frame range
        output_filename = f"csv_{timestamp}_frames_{start_frame}-{end_frame}.csv"
        output_path = os.path.join(output_dir, output_filename)
        
        if os.path.exists(output_path):
            reply = QMessageBox.question(self, "File exists", 
                                    "A file with this name already exists. Do you want to replace it?",
                                    QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        try:
            # Load original CSV data
            analyzed_data = []
            with open(csv_path, mode='r') as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames
                for row in reader:
                    analyzed_data.append(row)
            
            # Extract selected frame range
            selected_data = analyzed_data[start_frame:end_frame + 1]
            
            # Write selected data to new CSV
            with open(output_path, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for row in selected_data:
                    writer.writerow(row)
            
            self.log(f"Saved partial CSV: {output_path}")
            QMessageBox.information(self, "Success", f"Saved partial CSV with {len(selected_data)} frames")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save partial CSV: {str(e)}")