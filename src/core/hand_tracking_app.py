import sys
import cv2
import os
import csv
from PyQt5.QtWidgets import QApplication, QMessageBox
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
        self.refresh_button.clicked.connect(self.populate_camera_list)

        # Analysis controls
        self.start_analyze_button.clicked.connect(self.start_analyzing)
        self.stop_analyze_button.clicked.connect(self.stop_analyzing)
        self.analyze_button.clicked.connect(self.analyze_selected_recording)

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
        self.update_recording_combo(recording_list)

    def refresh_recordings(self):
        self.populate_recording_list()
        self.log("Refreshed recording list")

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
            self.log("Cannot play: No recording loaded or analyzed")
            return

        # Set initial frame to the start of the selected range
        self.playback_manager.current_frame_index = self.frame_slider.low()

        if self.playback_manager.start_playback(self.playback_timer):
            self.start_play_button.setEnabled(False)
            self.pause_play_button.setEnabled(True)
            self.stop_play_button.setEnabled(True)
            self.log("Playback started")
            # Force initial frame update
            self.update_frame_display()
            self.update_frame_labels()

    def pause_playing(self):
        """Pause/resume video playback"""
        if self.playback_manager.pause_playback(self.playback_timer):
            paused = self.playback_manager.paused
            self.pause_play_button.setText("Resume" if paused else "Pause")
            self.log("Playback paused" if paused else "Playback resumed")

    def stop_playing(self):
        """Stop video playback"""
        if self.playback_manager.stop_playback(self.playback_timer):
            self.start_play_button.setEnabled(True)
            self.pause_play_button.setEnabled(False)
            self.stop_play_button.setEnabled(False)
            self.pause_play_button.setText("Pause")
            self.update_frame_labels()  # Update labels without moving slider
            self.update_frame_display()
            self.log("Playback stopped")

    def analyze_selected_recording(self):
        recording_name = self.recording_combo.currentText()
        if not recording_name:
            self.log("No recording selected")
            return

        # Check if CSV exists
        timestamp = recording_name[10:-4]
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
                self.load_recording(recording_name)
                return

        self.show_progress_bar(True)
        self.set_progress(0)

        try:
            recording_path = os.path.join("src/data/raw_movie", recording_name)

            # Analyze video and save CSV directly
            csv_path = self.analysis_manager.analyze_video(
                recording_path, progress_callback=self.set_progress
            )

            self.log(f"Analysis completed: {csv_path}")

            # Load the video file for playback
            self.load_recording(recording_name)

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
            self.log("No recording loaded or analyzed")
            return

        self.log(
            f"Attempting to display frame {self.playback_manager.current_frame_index}"
        )
        frame = self.playback_manager.get_frame(
            self.playback_manager.current_frame_index
        )

        if frame is not None:
            # Update frame display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w

            # Show original frame if real-time is enabled
            if self.settings_handler.get_setting("ViewSettings", "original_realtime"):
                convert_to_qt_format = QImage(
                    frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
                )
                pixmap = QPixmap.fromImage(convert_to_qt_format)
                self.analyzed_label.setPixmap(pixmap)

                # Update mixed view original
                small_w = w // 2
                small_h = h // 2
                small_original = pixmap.scaled(
                    small_w, small_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.mixed_original_label.setPixmap(small_original)

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
                self.trailed_label.setPixmap(QPixmap.fromImage(trailed_qt))

                # Update mixed view trailed
                small_w = w // 2
                small_h = h // 2
                small_trailed = QPixmap.fromImage(trailed_qt).scaled(
                    small_w, small_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.mixed_trailed_label.setPixmap(small_trailed)

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
                self.heatmap_label.setPixmap(QPixmap.fromImage(heatmap_qt))

                # Update mixed view heatmap
                small_w = w // 2
                small_h = h // 2
                small_heatmap = QPixmap.fromImage(heatmap_qt).scaled(
                    small_w, small_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.mixed_heatmap_label.setPixmap(small_heatmap)

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

            # Update frame labels
            self.update_frame_labels()
            self.log(
                f"Successfully displayed frame {self.playback_manager.current_frame_index}"
            )

        else:
            self.log(
                f"Failed to read frame {self.playback_manager.current_frame_index}"
            )

    def update_playback_frame(self):
        if self.playback_manager.playing and not self.playback_manager.paused:
            next_frame = self.playback_manager.current_frame_index + 1
            end_frame = self.frame_slider.high()
            start_frame = self.frame_slider.low()

            if next_frame > end_frame:
                next_frame = start_frame

            self.playback_manager.current_frame_index = next_frame
            self.update_frame_display()  # This will update all visualizations
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
            self.frame_slider.setRange(0, total_frames - 1)
            self.min_frame_spin.setRange(0, total_frames - 1)
            self.max_frame_spin.setRange(0, total_frames - 1)
            self.frame_slider.setLow(0)
            self.frame_slider.setHigh(total_frames - 1)
            self.min_frame_spin.setValue(0)
            self.max_frame_spin.setValue(total_frames - 1)
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
                self.analyzed_label.setPixmap(pixmap)

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
                self.trailed_label.setPixmap(QPixmap.fromImage(trailed_qt))

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
                self.heatmap_label.setPixmap(QPixmap.fromImage(heatmap_qt))

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
        if recording_name:
            self.log(f"Selected recording: {recording_name}")
            self.clear_analysis_data()
            self.analyze_button.setEnabled(True)
        else:
            self.log("No recording selected")
            self.analyze_button.setEnabled(False)

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

    def save_part_of_movie(self):
        """Save a portion of the video based on slider range"""
        recording_name = self.recording_combo.currentText()
        if not recording_name:
            self.log("No recording selected")
            return

        # Get frame range from slider
        start_frame = self.frame_slider.low()
        end_frame = self.frame_slider.high()

        # Create output directory
        output_dir = "src/data/partial_movie"
        os.makedirs(output_dir, exist_ok=True)

        # Get current recording name
        timestamp = recording_name[
            10:-4
        ]  # Remove "raw_movie_" prefix and ".mp4" suffix
        output_path = os.path.join(
            output_dir, f"partial_{timestamp}_frames_{start_frame}-{end_frame}.mp4"
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

            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            # Process frames in selected range
            total_frames = end_frame - start_frame + 1
            for frame_idx in range(start_frame, end_frame + 1):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)

                # Update progress
                progress = int((frame_idx - start_frame + 1) / total_frames * 100)
                self.set_progress(progress)

            cap.release()
            out.release()
            self.log(f"Saved partial movie: {output_path}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save partial movie: {str(e)}"
            )
        finally:
            self.show_progress_bar(False)

    def save_part_of_heatmap(self):
        """Save a portion of the heatmap video based on slider range"""
        recording_name = self.recording_combo.currentText()
        if not recording_name:
            self.log("No recording selected")
            return

        # Get frame range from slider
        start_frame = self.frame_slider.low()
        end_frame = self.frame_slider.high()

        # Create output directory
        output_dir = "src/data/partial_heatmap"
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

        output_path = os.path.join(
            output_dir,
            f"partial_heatmap_{timestamp}_frames_{start_frame}-{end_frame}.mp4",
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
                progress = int((frame_idx - start_frame + 1) / total_frames * 100)
                self.set_progress(progress)

            cap.release()
            out.release()
            self.log(f"Saved partial heatmap: {output_path}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save partial heatmap: {str(e)}"
            )
        finally:
            self.show_progress_bar(False)

    def save_part_of_trailing(self):
        """Save a portion of the trailed video based on slider range"""
        recording_name = self.recording_combo.currentText()
        if not recording_name:
            self.log("No recording selected")
            return

        # Get frame range from slider
        start_frame = self.frame_slider.low()
        end_frame = self.frame_slider.high()

        # Create output directory
        output_dir = "src/data/partial_trailing"
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

        output_path = os.path.join(
            output_dir,
            f"partial_trailing_{timestamp}_frames_{start_frame}-{end_frame}.mp4",
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
            self.log(f"Saved partial trailing: {output_path}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save partial trailing: {str(e)}"
            )
        finally:
            self.show_progress_bar(False)

    def save_part_of_csv(self):
        """Save a portion of the CSV data based on slider range"""
        recording_name = self.recording_combo.currentText()
        if not recording_name:
            self.log("No recording selected")
            return

        # Get frame range from slider
        start_frame = self.frame_slider.low()
        end_frame = self.frame_slider.high()

        # Create output directory
        output_dir = "src/data/partial_csv"
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

        output_path = os.path.join(
            output_dir, f"partial_csv_{timestamp}_frames_{start_frame}-{end_frame}.csv"
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

            # Read all CSV data
            analyzed_data = []
            with open(csv_path, mode="r") as file:
                reader = csv.DictReader(file)
                analyzed_data = list(reader)

            # Extract data for the selected frame range
            partial_data = analyzed_data[start_frame : end_frame + 1]

            # Write partial data to new CSV
            if partial_data:
                with open(output_path, mode="w", newline="") as file:
                    writer = csv.DictWriter(file, fieldnames=partial_data[0].keys())
                    writer.writeheader()
                    writer.writerows(partial_data)

                self.log(f"Saved partial CSV: {output_path}")
            else:
                self.log("No data in selected frame range")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save partial CSV: {str(e)}")
        finally:
            self.show_progress_bar(False)

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
                progress = int((frame_idx + 1) / total_frames * 100)
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
                progress = int((frame_idx + 1) / total_frames * 100)
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
            small_w = w // 2
            small_h = h // 2
            small_heatmap = QPixmap.fromImage(heatmap_qt).scaled(
                small_w, small_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.mixed_heatmap_label.setPixmap(small_heatmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraViewerApp()
    window.show()
    sys.exit(app.exec_())
