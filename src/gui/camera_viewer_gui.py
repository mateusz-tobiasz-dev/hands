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
    QSizePolicy,
    QSpinBox,
    QMessageBox,
    QGroupBox,
    QGridLayout,
    QDoubleSpinBox,
    QCheckBox,
)
from PyQt5.QtCore import Qt
from src.utils.settings_handler import SettingsHandler
from src.gui.table_view import TableView
import os
import time
import cv2
import csv
from src.utils.slider import RangeSlider
from PyQt5.QtGui import QPixmap, QPainter


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
                ("1024x1024", 1024, 1024),
            ],
            "4:3 Ratio": [
                ("320x240", 320, 240),
                ("640x480", 640, 480),
                ("800x600", 800, 600),
                ("1024x768", 1024, 768),
                ("1600x1200", 1600, 1200),
            ],
            "16:9 Ratio": [
                ("640x360", 640, 360),
                ("1280x720", 1280, 720),
                ("1600x900", 1600, 900),
                ("1920x1080", 1920, 1080),
            ],
        }
        self.setup_ui()
        self.connect_resolution_signals()
        self.validate_and_update_resolution()

    def setup_ui(self):
        # Initialize checkboxes as None to avoid attribute errors
        self.original_realtime_checkbox = None
        self.mixed_original_realtime_checkbox = None
        self.settings_original_realtime_checkbox = None

        self.trailed_realtime_checkbox = None
        self.mixed_trailed_realtime_checkbox = None
        self.settings_trailed_realtime_checkbox = None

        self.heatmap_realtime_checkbox = None
        self.mixed_heatmap_realtime_checkbox = None
        self.settings_heatmap_realtime_checkbox = None

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
        self.original_realtime_checkbox = QCheckBox("Real-time Update")
        self.original_realtime_checkbox.setChecked(
            self.settings_handler.get_setting("ViewSettings", "original_realtime")
        )
        original_layout.addWidget(self.analyzed_label)
        original_layout.addWidget(self.original_resolution_label)
        original_layout.addWidget(self.original_realtime_checkbox)
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
        self.trailed_realtime_checkbox = QCheckBox("Real-time Update")
        self.trailed_realtime_checkbox.setChecked(
            self.settings_handler.get_setting("ViewSettings", "trailed_realtime")
        )
        trailed_layout.addWidget(self.trailed_label)
        trailed_layout.addWidget(self.trailed_resolution_label)
        trailed_layout.addWidget(self.trailed_realtime_checkbox)
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
        self.heatmap_realtime_checkbox = QCheckBox("Real-time Update")
        self.heatmap_realtime_checkbox.setChecked(
            self.settings_handler.get_setting("ViewSettings", "heatmap_realtime")
        )
        heatmap_layout.addWidget(self.heatmap_label)
        heatmap_layout.addWidget(self.heatmap_resolution_label)
        heatmap_layout.addWidget(self.heatmap_realtime_checkbox)
        self.visualization_tabs.addTab(heatmap_tab, "Heatmap")

        # Mixed tab
        mixed_tab = QWidget()
        mixed_layout = QGridLayout(mixed_tab)

        # Original view
        mixed_original_group = QGroupBox("Original")
        mixed_original_layout = QVBoxLayout(mixed_original_group)
        self.mixed_original_label = QLabel()
        self.mixed_original_label.setAlignment(Qt.AlignCenter)
        self.mixed_original_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.mixed_original_label.setMinimumSize(320, 240)
        self.mixed_original_realtime_checkbox = QCheckBox("Real-time Update")
        self.mixed_original_realtime_checkbox.setChecked(
            self.settings_handler.get_setting("ViewSettings", "original_realtime")
        )
        mixed_original_layout.addWidget(self.mixed_original_label)
        mixed_original_layout.addWidget(self.mixed_original_realtime_checkbox)
        mixed_layout.addWidget(mixed_original_group, 0, 0)

        # Trailed view
        mixed_trailed_group = QGroupBox("Trailed")
        mixed_trailed_layout = QVBoxLayout(mixed_trailed_group)
        self.mixed_trailed_label = QLabel()
        self.mixed_trailed_label.setAlignment(Qt.AlignCenter)
        self.mixed_trailed_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.mixed_trailed_label.setMinimumSize(320, 240)
        self.mixed_trailed_realtime_checkbox = QCheckBox("Real-time Update")
        self.mixed_trailed_realtime_checkbox.setChecked(
            self.settings_handler.get_setting("ViewSettings", "trailed_realtime")
        )
        mixed_trailed_layout.addWidget(self.mixed_trailed_label)
        mixed_trailed_layout.addWidget(self.mixed_trailed_realtime_checkbox)
        mixed_layout.addWidget(mixed_trailed_group, 0, 1)

        # Heatmap view
        mixed_heatmap_group = QGroupBox("Heatmap")
        mixed_heatmap_layout = QVBoxLayout(mixed_heatmap_group)
        self.mixed_heatmap_label = QLabel()
        self.mixed_heatmap_label.setAlignment(Qt.AlignCenter)
        self.mixed_heatmap_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.mixed_heatmap_label.setMinimumSize(320, 240)
        self.mixed_heatmap_realtime_checkbox = QCheckBox("Real-time Update")
        self.mixed_heatmap_realtime_checkbox.setChecked(
            self.settings_handler.get_setting("ViewSettings", "heatmap_realtime")
        )
        mixed_heatmap_layout.addWidget(self.mixed_heatmap_label)
        mixed_heatmap_layout.addWidget(self.mixed_heatmap_realtime_checkbox)
        mixed_layout.addWidget(mixed_heatmap_group, 1, 0, 1, 2)

        self.visualization_tabs.addTab(mixed_tab, "Mixed")

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

        # Create tabs for hand data
        self.hand_data_tabs = QTabWidget()
        analyzed_layout.addWidget(self.hand_data_tabs)

        # Overall stats tab
        overall_stats_tab = QWidget()
        overall_stats_layout = QVBoxLayout(overall_stats_tab)
        self.overall_stats_table = TableView()
        overall_stats_layout.addWidget(self.overall_stats_table)
        self.hand_data_tabs.addTab(overall_stats_tab, "Overall Stats")

        # Left hand landmarks tab
        left_hand_tab = QWidget()
        left_hand_layout = QVBoxLayout(left_hand_tab)
        self.left_landmarks_table = TableView()
        left_hand_layout.addWidget(self.left_landmarks_table)
        self.hand_data_tabs.addTab(left_hand_tab, "Left Hand")

        # Right hand landmarks tab
        right_hand_tab = QWidget()
        right_hand_layout = QVBoxLayout(right_hand_tab)
        self.right_landmarks_table = TableView()
        right_hand_layout.addWidget(self.right_landmarks_table)
        self.hand_data_tabs.addTab(right_hand_tab, "Right Hand")

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

        # Connect all checkbox signals after all UI elements are created
        self.original_realtime_checkbox.stateChanged.connect(
            self.on_original_realtime_changed
        )
        self.mixed_original_realtime_checkbox.stateChanged.connect(
            self.on_original_realtime_changed
        )
        self.settings_original_realtime_checkbox.stateChanged.connect(
            self.on_original_realtime_changed
        )

        self.trailed_realtime_checkbox.stateChanged.connect(
            self.on_trailed_realtime_changed
        )
        self.mixed_trailed_realtime_checkbox.stateChanged.connect(
            self.on_trailed_realtime_changed
        )
        self.settings_trailed_realtime_checkbox.stateChanged.connect(
            self.on_trailed_realtime_changed
        )

        self.heatmap_realtime_checkbox.stateChanged.connect(
            self.on_heatmap_realtime_changed
        )
        self.mixed_heatmap_realtime_checkbox.stateChanged.connect(
            self.on_heatmap_realtime_changed
        )
        self.settings_heatmap_realtime_checkbox.stateChanged.connect(
            self.on_heatmap_realtime_changed
        )

    def setup_settings_ui(self):
        settings_layout = QVBoxLayout()

        # Analysis controls
        analysis_group = QGroupBox("Analysis Control")
        analysis_controls = QHBoxLayout()
        self.start_analyze_button = QPushButton("Start Recording")
        self.stop_analyze_button = QPushButton("Stop Recording")
        self.stop_analyze_button.setEnabled(False)
        analysis_controls.addWidget(self.start_analyze_button)
        analysis_controls.addWidget(self.stop_analyze_button)
        analysis_group.setLayout(analysis_controls)
        settings_layout.addWidget(analysis_group)

        # Display controls
        display_group = QGroupBox("Display Settings")
        display_layout = QVBoxLayout()

        # Real-time update controls
        realtime_group = QGroupBox("Real-time Updates")
        realtime_layout = QVBoxLayout()

        # Settings panel checkboxes
        self.settings_original_realtime_checkbox = QCheckBox("Original View")
        self.settings_original_realtime_checkbox.setChecked(
            self.settings_handler.get_setting("ViewSettings", "original_realtime")
        )
        self.settings_trailed_realtime_checkbox = QCheckBox("Trailed View")
        self.settings_trailed_realtime_checkbox.setChecked(
            self.settings_handler.get_setting("ViewSettings", "trailed_realtime")
        )
        self.settings_heatmap_realtime_checkbox = QCheckBox("Heatmap View")
        self.settings_heatmap_realtime_checkbox.setChecked(
            self.settings_handler.get_setting("ViewSettings", "heatmap_realtime")
        )

        realtime_layout.addWidget(self.settings_original_realtime_checkbox)
        realtime_layout.addWidget(self.settings_trailed_realtime_checkbox)
        realtime_layout.addWidget(self.settings_heatmap_realtime_checkbox)
        realtime_group.setLayout(realtime_layout)
        display_layout.addWidget(realtime_group)

        # Trailing options group
        trailing_group = QGroupBox("Trailing Options")
        trailing_layout = QGridLayout()

        # Trail length
        trailing_layout.addWidget(QLabel("Trail Length:"), 0, 0)
        self.trail_length_input = QSpinBox()
        self.trail_length_input.setRange(1, 100)
        self.trail_length_input.setValue(
            self.settings_handler.get_setting("Trailing", "trail_length")
        )
        self.trail_length_input.valueChanged.connect(self.on_trail_length_changed)
        trailing_layout.addWidget(self.trail_length_input, 0, 1)

        # Landmark size
        trailing_layout.addWidget(QLabel("Landmark Size:"), 1, 0)
        self.landmark_size_input = QSpinBox()
        self.landmark_size_input.setRange(1, 10)
        self.landmark_size_input.setValue(
            self.settings_handler.get_setting("Trailing", "landmark_size")
        )
        self.landmark_size_input.valueChanged.connect(self.on_landmark_size_changed)
        trailing_layout.addWidget(self.landmark_size_input, 1, 1)

        # Alpha value
        trailing_layout.addWidget(QLabel("Alpha:"), 2, 0)
        self.alpha_input = QDoubleSpinBox()
        self.alpha_input.setRange(0.1, 1.0)
        self.alpha_input.setSingleStep(0.1)
        self.alpha_input.setValue(
            self.settings_handler.get_setting("Trailing", "alpha")
        )
        self.alpha_input.valueChanged.connect(self.on_alpha_changed)
        trailing_layout.addWidget(self.alpha_input, 2, 1)

        # Opacity value
        trailing_layout.addWidget(QLabel("Opacity:"), 3, 0)
        self.trailing_opacity_input = QDoubleSpinBox()
        self.trailing_opacity_input.setRange(0.1, 1.0)
        self.trailing_opacity_input.setSingleStep(0.1)
        self.trailing_opacity_input.setValue(
            self.settings_handler.get_setting("Trailing", "opacity")
        )
        self.trailing_opacity_input.valueChanged.connect(
            self.on_trailing_opacity_changed
        )
        trailing_layout.addWidget(self.trailing_opacity_input, 3, 1)

        # Black background checkbox
        self.black_background_checkbox = QCheckBox("Black Background")
        self.black_background_checkbox.setChecked(
            self.settings_handler.get_setting("Trailing", "black_background")
        )
        self.black_background_checkbox.stateChanged.connect(
            self.on_black_background_changed
        )
        trailing_layout.addWidget(self.black_background_checkbox, 4, 0, 1, 2)

        # Alpha fade checkbox
        self.alpha_fade_checkbox = QCheckBox("Alpha Fade")
        self.alpha_fade_checkbox.setChecked(
            self.settings_handler.get_setting("Trailing", "alpha_fade")
        )
        self.alpha_fade_checkbox.stateChanged.connect(self.on_alpha_fade_changed)
        trailing_layout.addWidget(self.alpha_fade_checkbox, 5, 0, 1, 2)

        trailing_group.setLayout(trailing_layout)
        display_layout.addWidget(trailing_group)

        # Heatmap options group
        heatmap_group = QGroupBox("Heatmap Options")
        heatmap_layout = QGridLayout()

        # Radius
        heatmap_layout.addWidget(QLabel("Radius:"), 0, 0)
        self.heatmap_radius_input = QSpinBox()
        self.heatmap_radius_input.setRange(1, 100)
        self.heatmap_radius_input.setValue(
            self.settings_handler.get_setting("Heatmap", "radius")
        )
        self.heatmap_radius_input.valueChanged.connect(self.on_heatmap_radius_changed)
        heatmap_layout.addWidget(self.heatmap_radius_input, 0, 1)

        # Opacity
        heatmap_layout.addWidget(QLabel("Opacity:"), 1, 0)
        self.heatmap_opacity_input = QDoubleSpinBox()
        self.heatmap_opacity_input.setRange(0.1, 1.0)
        self.heatmap_opacity_input.setSingleStep(0.1)
        self.heatmap_opacity_input.setValue(
            self.settings_handler.get_setting("Heatmap", "opacity")
        )
        self.heatmap_opacity_input.valueChanged.connect(self.on_heatmap_opacity_changed)
        heatmap_layout.addWidget(self.heatmap_opacity_input, 1, 1)

        # Color map
        heatmap_layout.addWidget(QLabel("Color Map:"), 2, 0)
        self.heatmap_colormap_combo = QComboBox()
        color_maps = [
            "jet",
            "hot",
            "rainbow",
            "ocean",
            "viridis",
            "plasma",
            "magma",
            "inferno",
        ]
        self.heatmap_colormap_combo.addItems(color_maps)
        current_colormap = self.settings_handler.get_setting("Heatmap", "color_map")
        self.heatmap_colormap_combo.setCurrentText(current_colormap)
        self.heatmap_colormap_combo.currentTextChanged.connect(
            self.on_heatmap_colormap_changed
        )
        heatmap_layout.addWidget(self.heatmap_colormap_combo, 2, 1)

        # Blur amount
        heatmap_layout.addWidget(QLabel("Blur Amount:"), 3, 0)
        self.heatmap_blur_input = QSpinBox()
        self.heatmap_blur_input.setRange(1, 50)
        self.heatmap_blur_input.setValue(
            self.settings_handler.get_setting("Heatmap", "blur_amount")
        )
        self.heatmap_blur_input.valueChanged.connect(self.on_heatmap_blur_changed)
        heatmap_layout.addWidget(self.heatmap_blur_input, 3, 1)

        # Black background checkbox
        self.heatmap_black_background_checkbox = QCheckBox("Black Background")
        self.heatmap_black_background_checkbox.setChecked(
            self.settings_handler.get_setting("Heatmap", "black_background")
        )
        self.heatmap_black_background_checkbox.stateChanged.connect(
            self.on_heatmap_black_background_changed
        )
        heatmap_layout.addWidget(self.heatmap_black_background_checkbox, 4, 0, 1, 2)

        # Accumulate checkbox
        self.heatmap_accumulate_checkbox = QCheckBox("Accumulate")
        self.heatmap_accumulate_checkbox.setChecked(
            self.settings_handler.get_setting("Heatmap", "accumulate")
        )
        self.heatmap_accumulate_checkbox.stateChanged.connect(
            self.on_heatmap_accumulate_changed
        )
        heatmap_layout.addWidget(self.heatmap_accumulate_checkbox, 5, 0, 1, 2)

        heatmap_group.setLayout(heatmap_layout)
        display_layout.addWidget(heatmap_group)

        display_group.setLayout(display_layout)
        settings_layout.addWidget(display_group)

        # Generate controls
        generate_group = QGroupBox("Generate Full Videos")
        generate_layout = QVBoxLayout()
        self.generate_trailing_button = QPushButton("Generate Full Trailing")
        self.generate_heatmap_button = QPushButton("Generate Full Heatmap")
        generate_layout.addWidget(self.generate_trailing_button)
        generate_layout.addWidget(self.generate_heatmap_button)
        generate_group.setLayout(generate_layout)
        settings_layout.addWidget(generate_group)

        # Save controls
        save_group = QGroupBox("Save Parts")
        save_layout = QVBoxLayout()
        self.save_part_button = QPushButton("Save Part of Movie")
        self.save_part_trailing_button = QPushButton("Save Part of Trailing")
        self.save_part_heatmap_button = QPushButton("Save Part of Heatmap")
        self.save_part_csv_button = QPushButton("Save Part of CSV")
        save_layout.addWidget(self.save_part_button)
        save_layout.addWidget(self.save_part_trailing_button)
        save_layout.addWidget(self.save_part_heatmap_button)
        save_layout.addWidget(self.save_part_csv_button)
        save_group.setLayout(save_layout)
        settings_layout.addWidget(save_group)

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
        self.camera_width_input.setValue(
            self.settings_handler.get_setting("Resolution", "camera_width")
        )
        resolution_layout.addWidget(self.camera_width_input, 1, 1)

        resolution_layout.addWidget(QLabel("Custom Height:"), 2, 0)
        self.camera_height_input = QSpinBox()
        self.camera_height_input.setRange(240, 1080)
        self.camera_height_input.setValue(
            self.settings_handler.get_setting("Resolution", "camera_height")
        )
        resolution_layout.addWidget(self.camera_height_input, 2, 1)

        resolution_group.setLayout(resolution_layout)
        settings_layout.addWidget(resolution_group)

        self.settings_widget.setLayout(settings_layout)

    def on_preset_selected(self, text):
        if not text:
            return
        width, height = map(int, text.split("x"))
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
        self.camera_resolution_label.setText(
            f"Resolution: {width}x{height} | FPS: {fps:.1f}"
        )

    def save_settings(self):
        if not self.validate_resolution():
            QMessageBox.warning(
                self,
                "Invalid Resolution",
                "Please use a valid resolution ratio (1:1, 16:9, or 4:3) within range 320x240 to 1920x1080",
            )
            return False

        # Save all settings
        self.settings_handler.set_setting(
            "Resolution", "camera_width", self.camera_width_input.value()
        )
        self.settings_handler.set_setting(
            "Resolution", "camera_height", self.camera_height_input.value()
        )

        self.settings_handler.set_setting(
            "Trailing", "trail_length", self.trail_length_input.value()
        )
        self.settings_handler.set_setting(
            "Trailing", "landmark_size", self.landmark_size_input.value()
        )
        self.settings_handler.set_setting("Trailing", "alpha", self.alpha_input.value())
        self.settings_handler.set_setting(
            "Trailing", "black_background", self.black_background_checkbox.isChecked()
        )
        self.settings_handler.set_setting(
            "Trailing", "alpha_fade", self.alpha_fade_checkbox.isChecked()
        )

        self.settings_handler.set_setting(
            "Heatmap", "radius", self.heatmap_radius_input.value()
        )
        self.settings_handler.set_setting(
            "Heatmap", "opacity", self.heatmap_opacity_input.value()
        )
        self.settings_handler.set_setting(
            "Heatmap", "color_map", self.heatmap_colormap_combo.currentText()
        )
        self.settings_handler.set_setting(
            "Heatmap", "blur_amount", self.heatmap_blur_input.value()
        )
        self.settings_handler.set_setting(
            "Heatmap",
            "black_background",
            self.heatmap_black_background_checkbox.isChecked(),
        )
        self.settings_handler.set_setting(
            "Heatmap", "accumulate", self.heatmap_accumulate_checkbox.isChecked()
        )

        self.settings_handler.save_settings()

        # Reconnect camera if it's currently connected
        if hasattr(self, "camera_manager") and self.camera_manager.camera:
            self.log("Settings saved, reconnecting camera...")
            self.toggle_camera()  # Disconnect
            self.toggle_camera()  # Connect with new resolution
        else:
            self.log("Settings saved successfully")

        QMessageBox.information(
            self, "Settings Saved", "Settings have been saved successfully!"
        )
        return True

    def validate_resolution(self):
        camera_width = self.camera_width_input.value()
        camera_height = self.camera_height_input.value()

        # Basic range check
        if not (320 <= camera_width <= 1920 and 240 <= camera_height <= 1080):
            return False

        # Check aspect ratios (1:1, 16:9, 4:3)
        ratio = camera_width / camera_height
        allowed_ratios = [1.0, 16 / 9, 4 / 3]  # 1:1, 16:9, 4:3
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
                label_size.width(),
                label_size.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

            # Center the pixmap in the label
            x = (label_size.width() - scaled_pixmap.width()) // 2
            y = (label_size.height() - scaled_pixmap.height()) // 2

            # Create a new pixmap with the label's size and fill with black
            final_pixmap = QPixmap(label_size)
            final_pixmap.fill(Qt.black)

            # Draw the scaled image in the center
            painter = QPainter(final_pixmap)
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()

            self.analyzed_label.setPixmap(final_pixmap)

            if original_size:
                current_text = self.original_resolution_label.text()
                fps_text = (
                    " | FPS: --"
                    if " | FPS: " not in current_text
                    else current_text[current_text.find(" | FPS: ") :]
                )
                self.original_resolution_label.setText(
                    f"Original: {original_size[0]}x{original_size[1]}{fps_text}"
                )
        else:
            self.analyzed_label.clear()
            self.original_resolution_label.setText("Original: --x-- | FPS: --")

    def update_trailed_frame(self, pixmap, original_size=None):
        if pixmap:
            # Calculate scaling to maintain aspect ratio
            label_size = self.trailed_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size.width(),
                label_size.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

            # Center the pixmap in the label
            x = (label_size.width() - scaled_pixmap.width()) // 2
            y = (label_size.height() - scaled_pixmap.height()) // 2

            # Create a new pixmap with the label's size and fill with black
            final_pixmap = QPixmap(label_size)
            final_pixmap.fill(Qt.black)

            # Draw the scaled image in the center
            painter = QPainter(final_pixmap)
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()

            self.trailed_label.setPixmap(final_pixmap)

            if original_size:
                current_text = self.trailed_resolution_label.text()
                fps_text = (
                    " | FPS: --"
                    if " | FPS: " not in current_text
                    else current_text[current_text.find(" | FPS: ") :]
                )
                self.trailed_resolution_label.setText(
                    f"Original: {original_size[0]}x{original_size[1]}{fps_text}"
                )
        else:
            self.trailed_label.clear()
            self.trailed_resolution_label.setText("Original: --x-- | FPS: --")

    def update_heatmap_frame(self, pixmap, original_size=None):
        if pixmap:
            # Calculate scaling to maintain aspect ratio
            label_size = self.heatmap_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size.width(),
                label_size.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

            # Center the pixmap in the label
            x = (label_size.width() - scaled_pixmap.width()) // 2
            y = (label_size.height() - scaled_pixmap.height()) // 2

            # Create a new pixmap with the label's size and fill with black
            final_pixmap = QPixmap(label_size)
            final_pixmap.fill(Qt.black)

            # Draw the scaled image in the center
            painter = QPainter(final_pixmap)
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()

            self.heatmap_label.setPixmap(final_pixmap)

            if original_size:
                current_text = self.heatmap_resolution_label.text()
                fps_text = (
                    " | FPS: --"
                    if " | FPS: " not in current_text
                    else current_text[current_text.find(" | FPS: ") :]
                )
                self.heatmap_resolution_label.setText(
                    f"Original: {original_size[0]}x{original_size[1]}{fps_text}"
                )
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
        self.overall_stats_table.clear_data()
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
        if not landmarks:
            table.clear_data()
            return

        # Extract frame number
        frame_number = (
            landmarks[0][1] if landmarks and landmarks[0][0] == "FRAME" else 0
        )
        landmarks = landmarks[1:]  # Remove frame entry from landmarks

        # Prepare data for table
        data = []
        column_labels = ["Frame", "X", "Y", "Z"]
        row_labels = []

        for landmark in landmarks:
            name, x, y, z = landmark
            row_labels.append(name)
            data.append(
                [
                    str(frame_number),
                    self.format_value(x),
                    self.format_value(y),
                    self.format_value(z),
                ]
            )

        table.update_data(data, row_labels=row_labels, column_labels=column_labels)
        table.resizeRowsToContents()

    def update_stats_table(self, parsed_data):
        if parsed_data is None or (
            isinstance(parsed_data, list) and len(parsed_data) == 0
        ):
            self.overall_stats_table.clear_data()
            return

        # Prepare data for overall stats table
        data = []
        row_labels = list(parsed_data.get("left", {}).keys())
        column_labels = ["LEFT", "RIGHT"]

        for stat_name in row_labels:
            left_value = parsed_data.get("left", {}).get(stat_name, "N/A")
            right_value = parsed_data.get("right", {}).get(stat_name, "N/A")
            data.append([self.format_value(left_value), self.format_value(right_value)])

        self.overall_stats_table.update_data(
            data, row_labels=row_labels, column_labels=column_labels
        )
        self.overall_stats_table.resizeRowsToContents()

    def update_resolution_label(self, frame):
        if frame is not None:
            height, width = frame.shape[:2]
            fps = self.get_fps()
            resolution_text = f"Resolution: {width}x{height} | FPS: {fps:.1f}"
            self.resolution_label.setText(resolution_text)

    def get_fps(self):
        current_time = time.time()
        if not hasattr(self, "last_frame_time"):
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
        timestamp = recording_name[
            10:-4
        ]  # Remove "raw_movie_" prefix and ".mp4" suffix
        csv_filename = f"csv_{timestamp}.csv"
        csv_path = os.path.join("src/data/csv_data", csv_filename)

        if not os.path.exists(csv_path):
            QMessageBox.warning(
                self,
                "Warning",
                "CSV data not found. Please analyze the recording first.",
            )
            return

        # Add frame range to output filename
        output_path = os.path.join(
            output_dir, f"trailed_{timestamp}_frames_{start_frame}-{end_frame}.mp4"
        )

        if os.path.exists(output_path):
            reply = QMessageBox.question(
                self,
                "File exists",
                "A file with this name already exists. Do you want to replace it?",
                QMessageBox.Yes | QMessageBox.No,
            )
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
            with open(csv_path, mode="r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    analyzed_data.append(row)

            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
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
                    frame, analyzed_data, frame_idx
                )
                out.write(trailed_frame)

                # Update progress
                progress = int((frame_idx - start_frame + 1) / total_frames * 100)
                self.set_progress(progress)

            cap.release()
            out.release()
            self.log(f"Saved trailed movie: {output_path}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save trailed movie: {str(e)}"
            )
        finally:
            self.show_progress_bar(False)
            self.set_progress(0)

    def on_min_frame_changed(self, value):
        """Handle minimum frame spinbox change"""
        if value <= self.frame_slider.high():
            self.frame_slider.setLow(value)
            self.frame_number_label.setText(
                f"Frames: {value}-{self.frame_slider.high()}"
            )
            self.update_frame_from_slider()

    def on_max_frame_changed(self, value):
        """Handle maximum frame spinbox change"""
        if value >= self.frame_slider.low():
            self.frame_slider.setHigh(value)
            self.frame_number_label.setText(
                f"Frames: {self.frame_slider.low()}-{value}"
            )

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
        timestamp = recording_name[
            10:-4
        ]  # Remove "raw_movie_" prefix and ".mp4" suffix
        csv_filename = f"csv_{timestamp}.csv"
        csv_path = os.path.join(
            "src/data/csv_data", csv_filename
        )  # Read from csv_data directory

        if not os.path.exists(csv_path):
            QMessageBox.warning(
                self,
                "Warning",
                "CSV data not found. Please analyze the recording first.",
            )
            return

        # Create output filename with frame range
        output_filename = f"csv_{timestamp}_frames_{start_frame}-{end_frame}.csv"
        output_path = os.path.join(output_dir, output_filename)

        if os.path.exists(output_path):
            reply = QMessageBox.question(
                self,
                "File exists",
                "A file with this name already exists. Do you want to replace it?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        try:
            # Load original CSV data
            analyzed_data = []
            with open(csv_path, mode="r") as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames
                for row in reader:
                    analyzed_data.append(row)

            # Extract selected frame range
            selected_data = analyzed_data[start_frame : end_frame + 1]

            # Write selected data to new CSV
            with open(output_path, mode="w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for row in selected_data:
                    writer.writerow(row)

            self.log(f"Saved partial CSV: {output_path}")
            QMessageBox.information(
                self, "Success", f"Saved partial CSV with {len(selected_data)} frames"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save partial CSV: {str(e)}")

    def on_original_realtime_changed(self, state):
        """Handle changes to original view real-time checkbox"""
        is_checked = bool(state)
        # Prevent infinite recursion by checking if the state actually changed
        if self.original_realtime_checkbox.isChecked() != is_checked:
            self.original_realtime_checkbox.setChecked(is_checked)
        if self.mixed_original_realtime_checkbox.isChecked() != is_checked:
            self.mixed_original_realtime_checkbox.setChecked(is_checked)
        if self.settings_original_realtime_checkbox.isChecked() != is_checked:
            self.settings_original_realtime_checkbox.setChecked(is_checked)
        self.settings_handler.set_setting(
            "ViewSettings", "original_realtime", is_checked
        )
        self.settings_handler.save_settings()

    def on_trailed_realtime_changed(self, state):
        """Handle changes to trailed view real-time checkbox"""
        is_checked = bool(state)
        if self.trailed_realtime_checkbox.isChecked() != is_checked:
            self.trailed_realtime_checkbox.setChecked(is_checked)
        if self.mixed_trailed_realtime_checkbox.isChecked() != is_checked:
            self.mixed_trailed_realtime_checkbox.setChecked(is_checked)
        if self.settings_trailed_realtime_checkbox.isChecked() != is_checked:
            self.settings_trailed_realtime_checkbox.setChecked(is_checked)
        self.settings_handler.set_setting(
            "ViewSettings", "trailed_realtime", is_checked
        )
        self.settings_handler.save_settings()

    def on_heatmap_realtime_changed(self, state):
        """Handle changes to heatmap view real-time checkbox"""
        is_checked = bool(state)
        if self.heatmap_realtime_checkbox.isChecked() != is_checked:
            self.heatmap_realtime_checkbox.setChecked(is_checked)
        if self.mixed_heatmap_realtime_checkbox.isChecked() != is_checked:
            self.mixed_heatmap_realtime_checkbox.setChecked(is_checked)
        if self.settings_heatmap_realtime_checkbox.isChecked() != is_checked:
            self.settings_heatmap_realtime_checkbox.setChecked(is_checked)
        self.settings_handler.set_setting(
            "ViewSettings", "heatmap_realtime", is_checked
        )
        self.settings_handler.save_settings()

    def on_trail_length_changed(self, value):
        """Handle changes to trail length"""
        self.settings_handler.set_setting("Trailing", "trail_length", value)
        self.settings_handler.save_settings()

    def on_landmark_size_changed(self, value):
        """Handle changes to landmark size"""
        self.settings_handler.set_setting("Trailing", "landmark_size", value)
        self.settings_handler.save_settings()

    def on_alpha_changed(self, value):
        """Handle changes to alpha"""
        self.settings_handler.set_setting("Trailing", "alpha", value)
        self.settings_handler.save_settings()

    def on_black_background_changed(self, state):
        """Handle changes to black background checkbox"""
        self.settings_handler.set_setting("Trailing", "black_background", state)
        self.settings_handler.save_settings()

    def on_alpha_fade_changed(self, state):
        """Handle changes to alpha fade checkbox"""
        self.settings_handler.set_setting("Trailing", "alpha_fade", state)
        self.settings_handler.save_settings()

    def on_heatmap_radius_changed(self, value):
        """Handle changes to heatmap radius"""
        self.settings_handler.set_setting("Heatmap", "radius", value)
        self.settings_handler.save_settings()

    def on_heatmap_opacity_changed(self, value):
        """Handle changes to heatmap opacity"""
        self.settings_handler.set_setting("Heatmap", "opacity", value)
        self.settings_handler.save_settings()

    def on_heatmap_colormap_changed(self, value):
        """Handle changes to heatmap color map"""
        self.settings_handler.set_setting("Heatmap", "color_map", value)
        self.settings_handler.save_settings()

    def on_heatmap_blur_changed(self, value):
        """Handle changes to heatmap blur amount"""
        self.settings_handler.set_setting("Heatmap", "blur_amount", value)
        self.settings_handler.save_settings()

    def on_heatmap_black_background_changed(self, state):
        """Handle changes to heatmap black background checkbox"""
        self.settings_handler.set_setting("Heatmap", "black_background", bool(state))
        self.settings_handler.save_settings()

    def on_heatmap_accumulate_changed(self, state):
        """Handle changes to heatmap accumulate checkbox"""
        self.settings_handler.set_setting("Heatmap", "accumulate", bool(state))
        self.settings_handler.save_settings()

    def on_trailing_opacity_changed(self, value):
        """Handle changes to trailing opacity"""
        self.settings_handler.set_setting("Trailing", "opacity", value)
        self.settings_handler.save_settings()
