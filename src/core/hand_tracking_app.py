import sys
import cv2
import os
import csv
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from src.gui.camera_viewer_gui import CameraViewerGUI
from src.utils.utils import log_message
from src.core.hand_landmarks import LANDMARK_DICT, STATS_DICT
from src.managers.camera_manager import CameraManager
from src.managers.recording_manager import RecordingManager
from src.managers.playback_manager import PlaybackManager
from src.managers.analysis_manager import AnalysisManager
from src.managers.visualization_manager import VisualizationManager
import time
from datetime import datetime


class CameraViewerApp(CameraViewerGUI):
    def __init__(self):
        super().__init__()
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_frame)

        self.camera_manager = CameraManager()
        self.recording_manager = RecordingManager()
        self.analysis_manager = AnalysisManager()
        self.playback_manager = PlaybackManager()
        self.visualization_manager = VisualizationManager(self.settings_handler)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_frame)

        # FPS calculation
        self.frame_times = []
        self.fps_update_interval = 1.0  # Update FPS every second
        self.last_fps_update = time.time()

        self.connect_signals()
        self.populate_camera_list()
        self.populate_recording_list()
        self.clear_analysis_data()

    def connect_signals(self):
        # Camera controls
        self.connect_button.clicked.connect(self.toggle_camera)
        self.camera_combo.currentIndexChanged.connect(self.populate_camera_list)
        self.refresh_button.clicked.connect(self.on_refresh_clicked)

        # Analysis controls
        self.start_analyze_button.clicked.connect(self.start_analyzing)
        self.stop_analyze_button.clicked.connect(self.stop_analyzing)
        self.analyze_button.clicked.connect(self.analyze_recording)
        self.load_button.clicked.connect(self.load_recording_only)

        # Generate controls
        self.generate_trailing_button.clicked.connect(self.generate_full_trailing)
        self.generate_heatmap_button.clicked.connect(self.generate_full_heatmap)

        # Recording controls
        self.recording_combo.currentIndexChanged.connect(
            self.update_recording_selection
        )
        self.refresh_button.clicked.connect(self.refresh_recordings)

        # Playback controls
        self.start_play_button.clicked.connect(self.start_playing)
        self.pause_play_button.clicked.connect(self.pause_playing)
        self.stop_play_button.clicked.connect(self.stop_playing)
        self.frame_slider.valueChanged.connect(self.update_frame_from_slider)
        self.min_frame_spin.valueChanged.connect(self.update_range_from_spin)
        self.max_frame_spin.valueChanged.connect(self.update_range_from_spin)

        # Save controls
        self.save_part_button.clicked.connect(self.save_part_of_movie)
        self.save_part_trailing_button.clicked.connect(self.save_part_of_trailing)
        self.save_part_heatmap_button.clicked.connect(self.save_part_of_heatmap)
        self.save_part_csv_button.clicked.connect(self.save_part_of_csv)

    def populate_camera_list(self):
        camera_list = self.camera_manager.get_camera_list()
        self.camera_combo.addItems(camera_list)

    def populate_recording_list(self):
        recording_list = self.recording_manager.get_recording_list()
        self.recording_combo.clear()
        self.recording_combo.addItem("Select mp4...")  # Add placeholder
        self.recording_combo.addItems(recording_list)

        # Disable all buttons initially
        self.analyze_button.setEnabled(False)
        self.load_button.setEnabled(False)
        self.start_play_button.setEnabled(False)
        self.pause_play_button.setEnabled(False)
        self.stop_play_button.setEnabled(False)
        self.save_part_button.setEnabled(False)
        self.save_part_trailing_button.setEnabled(False)
        self.save_part_heatmap_button.setEnabled(False)
        self.save_part_csv_button.setEnabled(False)
        self.generate_trailing_button.setEnabled(False)
        self.generate_heatmap_button.setEnabled(False)

    def refresh_recordings(self):
        """Refresh the list of available recordings"""
        # Store current selection
        current_selection = self.recording_combo.currentText()

        # Clear and disable buttons
        self.recording_combo.clear()
        self.analyze_button.setEnabled(False)
        self.start_play_button.setEnabled(False)
        self.pause_play_button.setEnabled(False)
        self.stop_play_button.setEnabled(False)
        self.save_part_button.setEnabled(False)
        self.save_part_trailing_button.setEnabled(False)
        self.save_part_heatmap_button.setEnabled(False)
        self.save_part_csv_button.setEnabled(False)
        self.generate_trailing_button.setEnabled(False)
        self.generate_heatmap_button.setEnabled(False)

        # Get list of MP4 files
        raw_movie_dir = "src/data/raw_movie"
        if not os.path.exists(raw_movie_dir):
            os.makedirs(raw_movie_dir)
            self.log(f"Created directory: {raw_movie_dir}")
            return

        mp4_files = [f for f in os.listdir(raw_movie_dir) if f.endswith(".mp4")]
        if not mp4_files:
            self.log("No recordings found")
            return

        # Update combo box
        sorted_files = sorted(mp4_files)
        self.recording_combo.addItems(sorted_files)

        # Restore previous selection if it still exists
        if current_selection in sorted_files:
            self.recording_combo.setCurrentText(current_selection)

        self.log(f"Found {len(mp4_files)} recordings")

    def toggle_camera(self):
        if not self.camera_manager.camera:
            camera_index = int(self.camera_combo.currentText().split()[-1])
            width, height = self.get_camera_resolution()

            if self.camera_manager.connect_camera(camera_index, width, height):
                actual_width, actual_height = (
                    self.camera_manager.get_actual_resolution()
                )
                self.log(
                    f"Camera connected with resolution: {actual_width}x{actual_height} (requested: {width}x{height})"
                )
                self.connect_button.setText("Disconnect")
                self.timer.start(30)
                self.start_analyze_button.setEnabled(True)
            else:
                self.log("Failed to open camera")
        else:
            if self.recording_manager.is_recording:
                self.stop_analyzing()
            self.timer.stop()
            self.camera_manager.disconnect_camera()
            self.connect_button.setText("Connect")
            self.camera_label.clear()
            self.start_analyze_button.setEnabled(False)
            self.stop_analyze_button.setEnabled(False)
            self.log("Camera disconnected")

    def update_frame(self):
        ret, frame = self.camera_manager.read_frame()
        if ret:
            # Calculate FPS
            current_time = time.time()
            self.frame_times.append(current_time)

            # Remove frames older than 1 second
            while self.frame_times and self.frame_times[0] < current_time - 1.0:
                self.frame_times.pop(0)

            # Update FPS display every second
            if current_time - self.last_fps_update >= self.fps_update_interval:
                fps = len(self.frame_times)
                actual_width, actual_height = (
                    self.camera_manager.get_actual_resolution()
                )
                self.update_resolution_display(actual_width, actual_height, fps)
                self.last_fps_update = current_time

            if self.recording_manager.is_recording:
                self.recording_manager.add_frame(frame)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            convert_to_qt_format = QImage(
                frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
            )
            pixmap = QPixmap.fromImage(convert_to_qt_format)
            self.update_camera_frame(pixmap)

    def start_analyzing(self):
        if not self.camera_manager.camera:
            self.log("Cannot start recording: Camera is not connected")
            return

        self.recording_manager.start_recording()
        self.start_analyze_button.setEnabled(False)
        self.stop_analyze_button.setEnabled(True)
        self.log("Started recording")

    def stop_analyzing(self):
        self.recording_manager.stop_recording()
        self.start_analyze_button.setEnabled(True)
        self.stop_analyze_button.setEnabled(False)
        self.log("Stopped recording")

        # Save recording with timestamp
        self.recording_manager.save_recording()
        self.populate_recording_list()
        self.log("Recording saved successfully")

    def start_playing(self):
        """Start video playback"""
        if not self.playback_manager.is_playback_ready():
            self.log("Cannot play: No recording loaded")
            return

        # Set initial frame to the start of the selected range
        self.playback_manager.current_frame_index = self.frame_slider.low()

        # Start playback timer if not already started
        if not hasattr(self, "playback_timer"):
            self.playback_timer = QTimer()
            self.playback_timer.timeout.connect(self.update_playback_frame)

        if self.playback_timer.isActive():
            return

        # Start the timer
        self.playback_timer.start(30)  # 30ms for ~30fps
        self.playback_manager.playing = True
        self.playback_manager.paused = False

        # Update button states
        self.start_play_button.setEnabled(False)
        self.pause_play_button.setEnabled(True)
        self.stop_play_button.setEnabled(True)
        self.log("Playback started")

        # Force initial frame update
        self.update_frame_display()
        self.update_frame_labels()

    def pause_playing(self):
        """Pause/resume video playback"""
        if not self.playback_manager.is_playback_ready() or not hasattr(
            self, "playback_timer"
        ):
            return

        if self.playback_manager.playing:
            self.playback_manager.paused = not self.playback_manager.paused
            if self.playback_manager.paused:
                self.playback_timer.stop()
                self.pause_play_button.setText("Resume")
                self.log("Playback paused")
            else:
                self.playback_timer.start(30)
                self.pause_play_button.setText("Pause")
                self.log("Playback resumed")

    def stop_playing(self):
        """Stop video playback"""
        if not self.playback_manager.is_playback_ready() or not hasattr(
            self, "playback_timer"
        ):
            return

        self.playback_manager.playing = False
        self.playback_manager.paused = False
        self.playback_manager.current_frame_index = 0
        self.playback_timer.stop()

        # Update button states
        self.start_play_button.setEnabled(True)
        self.pause_play_button.setEnabled(False)
        self.stop_play_button.setEnabled(False)
        self.pause_play_button.setText("Pause")

        # Update display
        self.update_frame_labels()
        self.update_frame_display()
        self.log("Playback stopped")

    def analyze_recording(self):
        """Analyze the currently loaded recording"""
        recording_name = self.recording_combo.currentText()
        if not recording_name or recording_name == "Select mp4...":
            return

        # If video is not loaded, load it first
        if not self.playback_manager.is_playback_ready():
            if not self.load_recording_only():
                return

        # Check if CSV exists
        timestamp = recording_name[
            10:-4
        ]  # Remove "raw_movie_" prefix and ".mp4" suffix
        csv_filename = f"csv_{timestamp}.csv"
        csv_path = os.path.join("src/data/csv_data", csv_filename)

        if os.path.exists(csv_path):
            reply = QMessageBox.question(
                self,
                "Analysis Exists",
                "Analysis data already exists. Would you like to:\n\n"
                "Yes - Use existing analysis data\n"
                "No - Analyze again",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                # Use existing CSV data
                if not self.load_csv_data(recording_name):
                    self.log("Failed to load analyzed data")
                    return
                self.log(f"Loaded existing analysis data")
                # Enable all visualization tabs and buttons after loading analysis
                self.enable_analysis_features()
            else:
                # Reanalyze video
                self.perform_analysis(recording_name)
        else:
            # First time analysis
            self.perform_analysis(recording_name)

        # Store that this recording has been analyzed
        self.playback_manager.is_analyzed = True

    def enable_analysis_features(self):
        """Enable all features that require analysis data"""
        # Enable all visualization tabs
        for i in range(self.visualization_tabs.count()):
            self.visualization_tabs.setTabEnabled(i, True)

        # Enable all playback controls
        self.start_play_button.setEnabled(True)
        self.pause_play_button.setEnabled(False)
        self.stop_play_button.setEnabled(False)

        # Enable all save and generate buttons
        self.save_part_button.setEnabled(True)
        self.save_part_trailing_button.setEnabled(True)
        self.save_part_heatmap_button.setEnabled(True)
        self.save_part_csv_button.setEnabled(True)
        self.generate_trailing_button.setEnabled(True)
        self.generate_heatmap_button.setEnabled(True)

        # Update display with analyzed data
        self.update_frame_display()
        self.log("Analysis complete - All features enabled")

    def perform_analysis(self, recording_name):
        """Perform analysis on the video"""
        self.show_progress_bar(True)
        self.set_progress(0)
        try:
            # Analyze video and save CSV directly
            csv_path = self.analysis_manager.analyze_video(
                os.path.join("src/data/raw_movie", recording_name),
                progress_callback=self.set_progress,
            )
            self.log(f"Analysis completed: {csv_path}")

            # Load the new CSV data
            if not self.load_csv_data(recording_name):
                self.log("Failed to load analyzed data")
                return

            # Enable all features after successful analysis
            self.enable_analysis_features()

        except Exception as e:
            self.log(f"Error during analysis: {str(e)}")
            QMessageBox.critical(self, "Error", f"Analysis failed: {str(e)}")
        finally:
            self.show_progress_bar(False)
            self.set_progress(0)

    def load_recording(self, recording_name):
        """Load a recording for playback"""
        if not recording_name:
            return False

        recording_path = os.path.join("src/data/raw_movie", recording_name)
        if not os.path.exists(recording_path):
            self.log(f"Recording not found: {recording_path}")
            return False

        self.log(f"Loading recording from: {recording_path}")

        # Load video file
        if not self.playback_manager.load_recording(recording_path):
            self.log(f"Failed to load recording: {recording_name}")
            return False

        total_frames = self.playback_manager.get_total_frames()
        self.log(f"Successfully loaded video with {total_frames} frames")

        # Get video metadata
        cap = cv2.VideoCapture(recording_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        # Update display info
        self.original_resolution_label.setText(
            f"Original: {width}x{height} | FPS: {fps:.1f}"
        )
        self.trailed_resolution_label.setText(
            f"Original: {width}x{height} | FPS: {fps:.1f}"
        )
        self.heatmap_resolution_label.setText(
            f"Original: {width}x{height} | FPS: {fps:.1f}"
        )

        # Load CSV data
        if not self.load_csv_data(recording_name):
            self.log("Failed to load analyzed data")
            return False

        self.log(
            f"Loaded {len(self.playback_manager.analyzed_data)} frames of analyzed data"
        )

        # Update UI
        self.update_frame_slider_range()
        self.update_frame_display()

        # Enable playback controls if everything is ready
        if self.playback_manager.is_playback_ready():
            self.start_play_button.setEnabled(True)
            self.pause_play_button.setEnabled(False)
            self.stop_play_button.setEnabled(False)
            self.log(f"Loaded {recording_name} - Ready for playback")
        else:
            self.log(f"Loaded {recording_name} but playback not ready")

        return True

    def update_frame_display(self):
        """Update the frame display"""
        if not self.playback_manager.is_playback_ready():
            return

        frame = self.playback_manager.get_frame(
            self.playback_manager.current_frame_index
        )
        if frame is None:
            return

        # Convert frame to RGB for display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        original_size = (w, h)

        # Calculate target sizes for mixed view based on aspect ratio
        aspect_ratio = w / h
        if aspect_ratio > 16 / 9:  # Wider than 16:9
            mixed_small_w = 640
            mixed_small_h = int(640 / aspect_ratio)
        else:  # Taller than or equal to 16:9
            mixed_small_h = 360
            mixed_small_w = int(360 * aspect_ratio)

        mixed_large_w = mixed_small_w * 2
        mixed_large_h = mixed_small_h * 2

        small_size = (mixed_small_w, mixed_small_h)
        large_size = (mixed_large_w, mixed_large_h)

        # Always show original frame in Original tab and mixed view
        convert_to_qt_format = QImage(
            frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
        )
        pixmap = QPixmap.fromImage(convert_to_qt_format)
        self.update_analyzed_frame(pixmap, original_size)
        self.update_mixed_frame(self.mixed_original_label, pixmap, small_size)

        # Only update analysis-dependent views if we have analysis data
        if self.playback_manager.is_analysis_ready():
            # Update trailed frame if real-time is enabled
            if self.settings_handler.get_setting("ViewSettings", "trailed_realtime"):
                trailed_frame = self.visualization_manager.generate_trailed_frame(
                    frame_rgb.copy(),
                    self.playback_manager.analyzed_data,
                    self.playback_manager.current_frame_index,
                )
                trailed_rgb = cv2.cvtColor(trailed_frame, cv2.COLOR_BGR2RGB)
                trailed_qt = QImage(
                    trailed_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
                )
                trailed_pixmap = QPixmap.fromImage(trailed_qt)
                self.update_trailed_frame(trailed_pixmap, original_size)
                self.update_mixed_frame(
                    self.mixed_trailed_label, trailed_pixmap, small_size
                )

            # Update heatmap frame if real-time is enabled
            if self.settings_handler.get_setting("ViewSettings", "heatmap_realtime"):
                trail_length = self.settings_handler.settings["Trailing"][
                    "trail_length"
                ]
                start_frame = max(
                    0, self.playback_manager.current_frame_index - trail_length
                )

                heatmap_frame = self.visualization_manager.generate_heatmap_frame(
                    frame_rgb.copy(),
                    self.playback_manager.analyzed_data,
                    self.playback_manager.current_frame_index,
                    start_frame=start_frame,
                    end_frame=self.playback_manager.current_frame_index,
                )
                heatmap_rgb = cv2.cvtColor(heatmap_frame, cv2.COLOR_BGR2RGB)
                heatmap_qt = QImage(
                    heatmap_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
                )
                heatmap_pixmap = QPixmap.fromImage(heatmap_qt)
                self.update_heatmap_frame(heatmap_pixmap, original_size)
                self.update_mixed_frame(
                    self.mixed_heatmap_label, heatmap_pixmap, large_size
                )

            # Update landmarks and stats
            frame_data = self.playback_manager.analyzed_data[
                self.playback_manager.current_frame_index
            ]
            left_landmarks = self.parse_landmarks(frame_data, "left")
            right_landmarks = self.parse_landmarks(frame_data, "right")
            self.update_landmarks_table(self.left_landmarks_table, left_landmarks)
            self.update_landmarks_table(self.right_landmarks_table, right_landmarks)

            # Update stats table
            stats = self.parse_stats(frame_data)
            self.update_stats_table(stats)

        # Always update frame labels
        self.update_frame_labels()

    def update_playback_frame(self):
        """Update frame during playback"""
        if not self.playback_manager.is_playback_ready():
            return

        if self.playback_manager.playing and not self.playback_manager.paused:
            next_frame = self.playback_manager.current_frame_index + 1
            end_frame = self.frame_slider.high()
            start_frame = self.frame_slider.low()

            if next_frame > end_frame:
                next_frame = start_frame

            self.playback_manager.current_frame_index = next_frame
            self.update_frame_display()
            self.update_frame_labels()

    def load_csv_data(self, recording_name):
        """Load analyzed data from CSV file"""
        # Remove "raw_movie_" prefix and ".mp4" suffix
        timestamp = recording_name[10:-4]
        csv_filename = f"csv_{timestamp}.csv"
        csv_path = os.path.join("src/data/csv_data", csv_filename)

        if not os.path.exists(csv_path):
            self.log(f"No analyzed data found for {recording_name}")
            self.playback_manager.analyzed_data = []
            return False

        try:
            # Initialize empty list for analyzed data
            analyzed_data = []

            # Read CSV file
            with open(csv_path, mode="r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Convert string values to float where needed
                    converted_row = {}
                    for key, value in row.items():
                        try:
                            if key != "frame":  # Keep frame as string/int
                                converted_row[key] = float(value) if value else None
                            else:
                                converted_row[key] = int(value)
                        except (ValueError, TypeError):
                            converted_row[key] = value
                    analyzed_data.append(converted_row)

            # Store the data in playback manager
            self.playback_manager.analyzed_data = analyzed_data
            self.log(f"Loaded {len(analyzed_data)} frames of analyzed data")

            # Enable playback controls
            self.start_play_button.setEnabled(True)
            self.pause_play_button.setEnabled(False)
            self.stop_play_button.setEnabled(False)

            return True

        except Exception as e:
            self.log(f"Error loading analyzed data: {str(e)}")
            self.playback_manager.analyzed_data = []
            return False

    def update_frame_slider_range(self):
        """Update the frame slider range based on the loaded recording"""
        total_frames = self.playback_manager.get_total_frames()
        if total_frames > 0:
            self.set_frame_slider_range(0, total_frames - 1)
            self.update_frame_labels()

    def update_range_from_spin(self):
        """Update slider range when spin boxes change"""
        min_val = self.min_frame_spin.value()
        max_val = self.max_frame_spin.value()

        # Ensure min is not greater than max
        if min_val > max_val:
            if self.min_frame_spin == self.sender():
                self.min_frame_spin.setValue(max_val)
            else:
                self.max_frame_spin.setValue(min_val)
            return

        # Update slider range
        self.frame_slider.setLow(min_val)
        self.frame_slider.setHigh(max_val)
        self.update_frame_labels()

    def update_frame_from_slider(self):
        """Update frame when slider moves"""
        frame_index = self.frame_slider.low()  # Use low value for current frame
        self.playback_manager.current_frame_index = frame_index
        self.update_frame_display()
        self.update_frame_labels()
        # Generate heatmap when slider moves
        self.generate_and_display_heatmap()

    def update_frame_labels(self):
        """Update the frame range and current frame labels"""
        start_frame = self.frame_slider.low()
        end_frame = self.frame_slider.high()
        current_frame = self.playback_manager.current_frame_index

        # Update spin boxes to match slider
        self.min_frame_spin.setValue(start_frame)
        self.max_frame_spin.setValue(end_frame)

        # Update label text
        self.frame_number_label.setText(
            f"Range: {start_frame}-{end_frame} | Current: {current_frame}"
        )

    def update_analysis_display(self):
        if self.playback_manager.frames and self.playback_manager.analyzed_data:
            if (
                0
                <= self.playback_manager.current_frame_index
                < min(
                    len(self.playback_manager.frames),
                    len(self.playback_manager.analyzed_data),
                )
            ):
                frame = self.playback_manager.frames[
                    self.playback_manager.current_frame_index
                ]
                frame_data = self.playback_manager.analyzed_data[
                    self.playback_manager.current_frame_index
                ]
                original_size = (frame.shape[1], frame.shape[0])

                # Update original frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                convert_to_qt_format = QImage(
                    frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
                )
                pixmap = QPixmap.fromImage(convert_to_qt_format)
                self.update_analyzed_frame(pixmap, original_size)

                # Update trailed frame
                trailed_frame = self.visualization_manager.generate_trailed_frame(
                    frame_rgb.copy(),  # Use a copy to keep original frame intact
                    self.playback_manager.analyzed_data,
                    self.playback_manager.current_frame_index,
                )
                trailed_rgb = cv2.cvtColor(trailed_frame, cv2.COLOR_BGR2RGB)
                trailed_qt = QImage(
                    trailed_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
                )
                self.update_trailed_frame(QPixmap.fromImage(trailed_qt), original_size)

                # Update heatmap frame
                heatmap_frame = self.visualization_manager.generate_heatmap_frame(
                    frame_rgb.copy(),
                    self.playback_manager.analyzed_data,
                    self.playback_manager.current_frame_index,
                )
                heatmap_rgb = cv2.cvtColor(heatmap_frame, cv2.COLOR_BGR2RGB)
                heatmap_qt = QImage(
                    heatmap_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
                )
                self.update_heatmap_frame(QPixmap.fromImage(heatmap_qt), original_size)

                # Update landmarks
                left_landmarks = self.parse_landmarks(frame_data, "left")
                right_landmarks = self.parse_landmarks(frame_data, "right")
                self.update_landmarks_table(self.left_landmarks_table, left_landmarks)
                self.update_landmarks_table(self.right_landmarks_table, right_landmarks)

                # Update stats table
                stats = self.parse_stats(frame_data)
                self.update_stats_table(stats)
            else:
                self.log(
                    f"Invalid frame index: {self.playback_manager.current_frame_index}"
                )
        else:
            self.log("No frames or analyzed data available for display")

    def parse_stats(self, frame_data):
        parsed_data = {"frame": frame_data.get("frame", 0), "left": {}, "right": {}}

        for hand in ["left", "right"]:
            for stat_key, stat_name in STATS_DICT.items():
                value = frame_data.get(f"{hand}_{stat_key}", None)
                if value is not None:
                    try:
                        if isinstance(value, (int, float)):
                            parsed_data[hand][stat_name] = float(value)
                        else:
                            parsed_data[hand][stat_name] = value
                    except ValueError:
                        self.log(f"Error parsing stat {stat_name} for {hand} hand")
                        parsed_data[hand][stat_name] = None
                else:
                    parsed_data[hand][stat_name] = None

        return parsed_data

    def parse_landmarks(self, frame_data, hand):
        landmarks = []
        frame = frame_data.get("frame", 0)
        landmarks.append(("FRAME", float(frame)))
        for item in LANDMARK_DICT.values():
            x = frame_data.get(f"{hand}_{item}_x", 0.0)
            y = frame_data.get(f"{hand}_{item}_y", 0.0)
            z = frame_data.get(f"{hand}_{item}_z", 0.0)
            if x and y and z:
                try:
                    landmarks.append((f"{item}", float(x), float(y), float(z)))
                except ValueError:
                    self.log(f"Error parsing landmark {item} for {hand} hand")
        return landmarks

    def update_recording_selection(self):
        """Just update the selected recording name without starting analysis"""
        recording_name = self.recording_combo.currentText()
        if recording_name and recording_name != "Select mp4...":
            self.log(f"Selected recording: {recording_name}")
            self.clear_analysis_data()
            self.analyze_button.setEnabled(True)
            self.load_button.setEnabled(True)
        else:
            self.log("No recording selected")
            self.analyze_button.setEnabled(False)
            self.load_button.setEnabled(False)
            self.start_play_button.setEnabled(False)
            self.pause_play_button.setEnabled(False)
            self.stop_play_button.setEnabled(False)
            self.save_part_button.setEnabled(False)
            self.save_part_trailing_button.setEnabled(False)
            self.save_part_heatmap_button.setEnabled(False)
            self.save_part_csv_button.setEnabled(False)
            self.generate_trailing_button.setEnabled(False)
            self.generate_heatmap_button.setEnabled(False)

    def log(self, message):
        log_msg = log_message(message)
        self.append_log(log_msg)
        print(log_msg)

    def clear_analysis_data(self):
        self.playback_manager.frames = []
        self.playback_manager.analyzed_data = []
        self.playback_manager.current_frame_index = 0
        self.playback_manager.playing = False
        self.playback_manager.paused = False

        self.set_current_frame(0)
        self.set_frame_slider_range(0, 0)
        self.start_play_button.setEnabled(False)
        self.pause_play_button.setEnabled(False)
        self.stop_play_button.setEnabled(False)
        self.pause_play_button.setText("Pause")

        super().clear_analysis_data()
        self.update_analyzed_frame(None)
        self.update_landmarks_table(self.left_landmarks_table, [])
        self.update_landmarks_table(self.right_landmarks_table, [])
        self.update_stats_table(None)

    def get_frame_range_string(self):
        """Get the frame range string in the format start-end"""
        start_frame = self.frame_slider.low()
        end_frame = self.frame_slider.high()
        return f"{start_frame:03d}-{end_frame:03d}"

    def get_timestamp_string(self):
        """Get the current timestamp string from the recording name or generate new one"""
        recording_name = self.recording_combo.currentText()
        if recording_name and recording_name.startswith("raw_movie_"):
            # Extract timestamp from recording name (format: raw_movie_[timestamp].mp4)
            return recording_name[10:-4]  # Remove "raw_movie_" prefix and ".mp4" suffix
        else:
            # Generate new timestamp
            return datetime.now().strftime("%d-%H%M%S")

    def save_part_of_movie(self):
        """Save a portion of the movie based on slider range"""
        try:
            # Generate filename
            timestamp = self.get_timestamp_string()
            frame_range = self.get_frame_range_string()
            filename = f"partial_{timestamp}_frames_{frame_range}.mp4"
            output_path = os.path.join("src/data/partial_movie", filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Get resolution settings
            use_original = self.settings_handler.get_setting(
                "SaveResolution", "use_original", True
            )
            if use_original:
                save_width = int(
                    self.playback_manager.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                )
                save_height = int(
                    self.playback_manager.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                )
            else:
                save_width = self.settings_handler.get_setting(
                    "SaveResolution", "width", 1920
                )
                save_height = self.settings_handler.get_setting(
                    "SaveResolution", "height", 1080
                )

            # Set up video writer with proper resolution
            fps = self.playback_manager.cap.get(cv2.CAP_PROP_FPS)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps, (save_width, save_height))

            # Get frame range
            start_frame = self.frame_slider.low()
            end_frame = self.frame_slider.high()
            total_frames = end_frame - start_frame + 1

            self.show_progress_bar(True)
            try:
                # Process frames
                for i in range(start_frame, end_frame + 1):
                    frame = self.playback_manager.get_frame(i)
                    if frame is None:
                        continue

                    # Resize if needed
                    if frame.shape[:2] != (save_height, save_width):
                        frame = cv2.resize(frame, (save_width, save_height))

                    out.write(frame)
                    progress = int(((i - start_frame + 1) / total_frames) * 100)
                    self.set_progress(progress)

                self.log(f"Saved partial movie to: {output_path}")

            finally:
                out.release()
                self.show_progress_bar(False)
                self.set_progress(0)

        except Exception as e:
            self.log(f"Error saving partial movie: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save movie: {str(e)}")
            self.show_progress_bar(False)
            self.set_progress(0)

    def save_part_of_trailing(self):
        """Save a portion of the trailed video based on slider range"""
        try:
            # Generate filename
            timestamp = self.get_timestamp_string()
            frame_range = self.get_frame_range_string()
            filename = f"partial_trailing_{timestamp}_frames_{frame_range}.mp4"
            output_path = os.path.join("src/data/partial_trailing", filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Get resolution settings
            use_original = self.settings_handler.get_setting(
                "SaveResolution", "use_original", True
            )
            if use_original:
                save_width = int(
                    self.playback_manager.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                )
                save_height = int(
                    self.playback_manager.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                )
            else:
                save_width = self.settings_handler.get_setting(
                    "SaveResolution", "width", 1920
                )
                save_height = self.settings_handler.get_setting(
                    "SaveResolution", "height", 1080
                )

            # Set up video writer
            fps = self.playback_manager.cap.get(cv2.CAP_PROP_FPS)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps, (save_width, save_height))

            # Get frame range
            start_frame = self.frame_slider.low()
            end_frame = self.frame_slider.high()
            total_frames = end_frame - start_frame + 1

            self.show_progress_bar(True)
            try:
                # Process frames
                for i in range(start_frame, end_frame + 1):
                    frame = self.playback_manager.get_frame(i)
                    if frame is None:
                        continue

                    # Generate trailed frame
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    trailed_frame = self.visualization_manager.generate_trailed_frame(
                        frame_rgb.copy(), self.playback_manager.analyzed_data, i
                    )
                    trailed_frame = cv2.cvtColor(trailed_frame, cv2.COLOR_RGB2BGR)

                    # Resize if needed
                    if trailed_frame.shape[:2] != (save_height, save_width):
                        trailed_frame = cv2.resize(
                            trailed_frame, (save_width, save_height)
                        )

                    out.write(trailed_frame)
                    progress = int(((i - start_frame + 1) / total_frames) * 100)
                    self.set_progress(progress)

                self.log(f"Saved partial trailing video to: {output_path}")

            finally:
                out.release()
                self.show_progress_bar(False)
                self.set_progress(0)

        except Exception as e:
            self.log(f"Error saving trailing video: {str(e)}")
            QMessageBox.critical(
                self, "Error", f"Failed to save trailing video: {str(e)}"
            )
            self.show_progress_bar(False)
            self.set_progress(0)

    def save_part_of_heatmap(self):
        """Save a portion of the heatmap video based on slider range"""
        try:
            # Generate filename
            timestamp = self.get_timestamp_string()
            frame_range = self.get_frame_range_string()
            filename = f"partial_heatmap_{timestamp}_frames_{frame_range}.mp4"
            output_path = os.path.join("src/data/partial_heatmap", filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Get resolution settings
            use_original = self.settings_handler.get_setting(
                "SaveResolution", "use_original", True
            )
            if use_original:
                save_width = int(
                    self.playback_manager.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                )
                save_height = int(
                    self.playback_manager.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                )
            else:
                save_width = self.settings_handler.get_setting(
                    "SaveResolution", "width", 1920
                )
                save_height = self.settings_handler.get_setting(
                    "SaveResolution", "height", 1080
                )

            # Set up video writer
            fps = self.playback_manager.cap.get(cv2.CAP_PROP_FPS)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps, (save_width, save_height))

            # Get frame range
            start_frame = self.frame_slider.low()
            end_frame = self.frame_slider.high()
            total_frames = end_frame - start_frame + 1

            self.show_progress_bar(True)
            try:
                # Process frames
                for i in range(start_frame, end_frame + 1):
                    # Get frame directly using OpenCV like in full heatmap
                    self.playback_manager.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                    ret, frame = self.playback_manager.cap.read()
                    if not ret:
                        continue

                    # Generate heatmap frame (keeping BGR color space)
                    heatmap_frame = self.visualization_manager.generate_heatmap_frame(
                        frame, self.playback_manager.analyzed_data, i
                    )

                    # Resize if needed
                    if heatmap_frame.shape[:2] != (save_height, save_width):
                        heatmap_frame = cv2.resize(
                            heatmap_frame, (save_width, save_height)
                        )

                    out.write(heatmap_frame)
                    progress = int(((i - start_frame + 1) / total_frames) * 100)
                    self.set_progress(progress)

                self.log(f"Saved partial heatmap video to: {output_path}")

            finally:
                out.release()
                self.show_progress_bar(False)
                self.set_progress(0)

        except Exception as e:
            self.log(f"Error saving heatmap video: {str(e)}")
            QMessageBox.critical(
                self, "Error", f"Failed to save heatmap video: {str(e)}"
            )
            self.show_progress_bar(False)
            self.set_progress(0)

    def save_part_of_csv(self):
        """Save a portion of the CSV data based on slider range"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            frame_range = self.get_frame_range_string()
            filename = f"partial_csv_{timestamp}_frames_{frame_range}.csv"
            output_path = os.path.join("src/data/partial_csv", filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Get frame range
            start_frame = self.frame_slider.low()
            end_frame = self.frame_slider.high()

            # Get the original CSV data
            recording_name = self.recording_combo.currentText()
            if not recording_name:
                self.log("No recording selected")
                return

            # If we're in raw mode (no analysis), create a basic CSV with frame numbers
            if not self.playback_manager.is_analysis_ready():
                self.show_progress_bar(True)
                self.set_progress(0)

                try:
                    with open(output_path, mode="w", newline="") as outfile:
                        writer = csv.writer(outfile)
                        # Write header
                        writer.writerow(["frame"])

                        # Write frame numbers
                        total_frames = end_frame - start_frame + 1
                        for i, frame_num in enumerate(
                            range(start_frame, end_frame + 1)
                        ):
                            writer.writerow([frame_num])
                            progress = int(((i + 1) / total_frames) * 100)
                            self.set_progress(progress)

                    self.log(f"Saved partial raw CSV data to: {output_path}")
                    return
                finally:
                    self.show_progress_bar(False)
                    self.set_progress(0)

            # If we have analysis data, save the analyzed CSV portion
            timestamp = recording_name[
                10:-4
            ]  # Remove "raw_movie_" prefix and ".mp4" suffix
            csv_filename = f"csv_{timestamp}.csv"
            csv_path = os.path.join("src/data/csv_data", csv_filename)

            if not os.path.exists(csv_path):
                self.log("CSV data not found")
                return

            self.show_progress_bar(True)
            self.set_progress(0)

            try:
                # Read and write CSV data for the selected range
                with (
                    open(csv_path, mode="r") as infile,
                    open(output_path, mode="w", newline="") as outfile,
                ):
                    reader = csv.reader(infile)
                    writer = csv.writer(outfile)

                    # Write header
                    header = next(reader)
                    writer.writerow(header)

                    # Skip to start frame
                    for _ in range(start_frame):
                        next(reader, None)

                    # Write selected frames
                    total_frames = end_frame - start_frame + 1
                    for i in range(total_frames):
                        try:
                            row = next(reader)
                            writer.writerow(row)
                            progress = int(((i + 1) / total_frames) * 100)
                            self.set_progress(progress)
                        except StopIteration:
                            break

                self.log(f"Saved partial analyzed CSV data to: {output_path}")

            finally:
                self.show_progress_bar(False)
                self.set_progress(0)

        except Exception as e:
            self.log(f"Error saving CSV data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save CSV data: {str(e)}")
            self.show_progress_bar(False)
            self.set_progress(0)

    def generate_full_trailing(self):
        """Generate full trailing video"""
        recording_name = self.recording_combo.currentText()
        if not recording_name:
            self.log("No recording selected")
            return

        # Check if CSV exists
        timestamp = recording_name[10:-4]
        csv_filename = f"csv_{timestamp}.csv"
        csv_path = os.path.join("src/data/csv_data", csv_filename)

        if not os.path.exists(csv_path):
            QMessageBox.warning(
                self,
                "Warning",
                "CSV data not found. Please analyze the recording first.",
            )
            return

        # Create output directory
        output_dir = "src/data/trailed_movie"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"trailed_{timestamp}.mp4")

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
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Load CSV data
            analyzed_data = []
            with open(csv_path, mode="r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    analyzed_data.append(row)

            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            # Process all frames
            for frame_idx in range(total_frames):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break

                # Generate trailed frame
                trailed_frame = self.visualization_manager.generate_trailed_frame(
                    frame, analyzed_data, frame_idx
                )
                out.write(trailed_frame)

                # Update progress
                progress = int(((frame_idx + 1) / total_frames) * 100)
                self.set_progress(progress)

            cap.release()
            out.release()
            self.log(f"Generated full trailing video: {output_path}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to generate trailing video: {str(e)}"
            )
        finally:
            self.show_progress_bar(False)
            self.set_progress(0)

    def generate_full_heatmap(self):
        """Generate full heatmap video"""
        recording_name = self.recording_combo.currentText()
        if not recording_name:
            self.log("No recording selected")
            return

        # Check if CSV exists
        timestamp = recording_name[10:-4]
        csv_filename = f"csv_{timestamp}.csv"
        csv_path = os.path.join("src/data/csv_data", csv_filename)

        if not os.path.exists(csv_path):
            QMessageBox.warning(
                self,
                "Warning",
                "CSV data not found. Please analyze the recording first.",
            )
            return

        # Create output directory
        output_dir = "src/data/heatmap_movie"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"heatmap_{timestamp}.mp4")

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
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Load CSV data
            analyzed_data = []
            with open(csv_path, mode="r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    analyzed_data.append(row)

            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            # Process all frames
            for frame_idx in range(total_frames):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break

                # Generate heatmap frame
                heatmap_frame = self.visualization_manager.generate_heatmap_frame(
                    frame, analyzed_data, frame_idx
                )
                out.write(heatmap_frame)

                # Update progress
                progress = int(((frame_idx + 1) / total_frames) * 100)
                self.set_progress(progress)

            cap.release()
            out.release()
            self.log(f"Generated full heatmap video: {output_path}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to generate heatmap video: {str(e)}"
            )
        finally:
            self.show_progress_bar(False)
            self.set_progress(0)

    def generate_and_display_heatmap(self):
        """Generate and display the heatmap for the current frame"""
        if not self.playback_manager.is_playback_ready():
            return

        frame = self.playback_manager.get_frame(
            self.playback_manager.current_frame_index
        )
        if frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w

            # Calculate target sizes for mixed view based on aspect ratio
            aspect_ratio = w / h
            if aspect_ratio > 16 / 9:  # Wider than 16:9
                mixed_large_w = 1280
                mixed_large_h = int(1280 / aspect_ratio)
            else:  # Taller than or equal to 16:9
                mixed_large_h = 720
                mixed_large_w = int(720 * aspect_ratio)

            # Use the same logic as realtime display
            trail_length = self.settings_handler.settings["Trailing"]["trail_length"]
            start_frame = max(
                0, self.playback_manager.current_frame_index - trail_length
            )

            # Generate heatmap for the current frame range
            heatmap_frame = self.visualization_manager.generate_heatmap_frame(
                frame_rgb.copy(),
                self.playback_manager.analyzed_data,
                self.playback_manager.current_frame_index,
                start_frame=start_frame,
                end_frame=self.playback_manager.current_frame_index,
            )

            # Convert and display heatmap
            heatmap_rgb = cv2.cvtColor(heatmap_frame, cv2.COLOR_BGR2RGB)
            heatmap_qt = QImage(
                heatmap_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
            )
            self.heatmap_label.setPixmap(QPixmap.fromImage(heatmap_qt))

            # Update mixed view heatmap
            heatmap_pixmap = QPixmap.fromImage(heatmap_qt)
            self.update_mixed_frame(
                self.mixed_heatmap_label, heatmap_pixmap, (mixed_large_w, mixed_large_h)
            )

    def on_camera_connected(self):
        """Handle camera connection"""
        # Enable recording resolution controls
        self.record_preset_combo.setEnabled(True)
        self.record_resolution_combo.setEnabled(True)
        self.apply_camera_res_button.setEnabled(True)

        # Update camera resolution
        width = self.settings_handler.get_setting("Resolution", "camera_width")
        height = self.settings_handler.get_setting("Resolution", "camera_height")
        self.camera_manager.set_resolution(width, height)

    def on_camera_disconnected(self):
        """Handle camera disconnection"""
        # Disable recording resolution controls
        self.record_preset_combo.setEnabled(False)
        self.record_resolution_combo.setEnabled(False)
        self.apply_camera_res_button.setEnabled(False)

    def get_save_path(self, title, extension):
        """Get save path from user with file dialog"""
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self, title, "", f"Video Files (*.{extension})", options=options
        )
        return filename if filename else None

    def load_recording_only(self):
        """Load a recording without analyzing it"""
        recording_name = self.recording_combo.currentText()
        if not recording_name or recording_name == "Select mp4...":
            return False

        # Check if the same recording is already loaded
        if self.playback_manager.is_playback_ready():
            current_path = self.playback_manager.current_recording_path
            new_path = os.path.join("src/data/raw_movie", recording_name)
            if current_path == new_path:
                QMessageBox.warning(
                    self,
                    "Already Loaded",
                    "This recording is already loaded. No need to load it again.",
                )
                return False

        recording_path = os.path.join("src/data/raw_movie", recording_name)
        if not os.path.exists(recording_path):
            self.log(f"Recording not found: {recording_path}")
            return False

        self.log(f"Loading recording from: {recording_path}")

        # Show progress bar
        self.show_progress_bar(True)
        self.set_progress(0)

        try:
            # Get video properties
            cap = cv2.VideoCapture(recording_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()

            # Update save resolution to match original if use_original is enabled
            if self.settings_handler.get_setting(
                "SaveResolution", "use_original", True
            ):
                self.settings_handler.set_setting("SaveResolution", "width", width)
                self.settings_handler.set_setting("SaveResolution", "height", height)
                resolution_text = f"{width}x{height}"
                index = self.save_resolution_combo.findText(resolution_text)
                if index >= 0:
                    self.save_resolution_combo.setCurrentIndex(index)
                self.settings_handler.save_settings()

            # Load video file for playback
            if not self.playback_manager.load_recording(recording_path):
                self.log(f"Failed to load recording: {recording_name}")
                return False

            # Store the current recording path
            self.playback_manager.current_recording_path = recording_path

            # Clear any existing analysis data
            self.playback_manager.analyzed_data = []
            self.playback_manager.is_analyzed = False

            # Update display info
            self.original_resolution_label.setText(
                f"Original: {width}x{height} | FPS: {fps:.1f}"
            )
            self.trailed_resolution_label.setText(
                f"Original: {width}x{height} | FPS: {fps:.1f}"
            )
            self.heatmap_resolution_label.setText(
                f"Original: {width}x{height} | FPS: {fps:.1f}"
            )

            # Update UI state for raw video mode
            self.update_frame_slider_range()

            # Switch to Original tab in visualization tabs and disable analysis-dependent tabs
            self.visualization_tabs.setCurrentIndex(0)  # Switch to Original tab
            for i in range(1, self.visualization_tabs.count()):
                self.visualization_tabs.setTabEnabled(i, False)

            # Enable raw video controls
            self.analyze_button.setEnabled(True)
            self.start_play_button.setEnabled(True)
            self.pause_play_button.setEnabled(False)
            self.stop_play_button.setEnabled(False)
            self.save_part_button.setEnabled(True)
            self.save_part_csv_button.setEnabled(True)  # Enable CSV save in raw mode

            # Disable analysis-dependent buttons
            self.save_part_trailing_button.setEnabled(False)
            self.save_part_heatmap_button.setEnabled(False)
            self.generate_trailing_button.setEnabled(False)
            self.generate_heatmap_button.setEnabled(False)

            # Show first frame
            self.playback_manager.current_frame_index = 0
            self.update_frame_display()

            # Start playback timer if not already started
            if not hasattr(self, "playback_timer"):
                self.playback_timer = QTimer()
                self.playback_timer.timeout.connect(self.update_playback_frame)

            self.set_progress(100)
            self.log(f"Loaded {recording_name} - Ready for playback or analysis")
            return True

        except Exception as e:
            self.log(f"Error loading recording: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load recording: {str(e)}")
            return False

        finally:
            self.show_progress_bar(False)
            self.set_progress(0)

    def update_raw_frame_display(self):
        """Update the frame display for raw video playback"""
        if not self.playback_manager.is_playback_ready():
            return

        frame = self.playback_manager.get_frame(
            self.playback_manager.current_frame_index
        )

        if frame is not None:
            # Update frame display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            original_size = (w, h)

            # Show original frame
            convert_to_qt_format = QImage(
                frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
            )
            pixmap = QPixmap.fromImage(convert_to_qt_format)
            self.update_analyzed_frame(pixmap, original_size)

            # Update frame labels
            self.update_frame_labels()

    def on_refresh_clicked(self):
        """Handle refresh button click based on current tab"""
        current_tab = self.tab_widget.currentWidget()
        if current_tab == self.camera_tab:
            self.populate_camera_list()  # Refresh cameras
            self.log("Refreshed camera list")
        else:
            self.refresh_recordings()  # Refresh recordings
            self.log("Refreshed recording list")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraViewerApp()
    window.show()
    sys.exit(app.exec_())
