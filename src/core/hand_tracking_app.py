import sys
import cv2
import os
import csv
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from src.gui.camera_viewer_gui import CameraViewerGUI
from src.core.hand_analyzer import HandAnalyzer
from src.utils.utils import save_to_csv, save_raw_movie, log_message
from src.core.hand_landmarks import LANDMARK_DICT, STATS_DICT
from datetime import datetime
import numpy as np
from src.utils.drawing_utils import get_hand_colors, get_finger_idx
from src.managers.camera_manager import CameraManager
from src.managers.recording_manager import RecordingManager
from src.managers.playback_manager import PlaybackManager
from src.managers.analysis_manager import AnalysisManager
from src.managers.visualization_manager import VisualizationManager


class CameraViewerApp(CameraViewerGUI):
    def __init__(self):
        super().__init__()
        
        self.camera_manager = CameraManager()
        self.recording_manager = RecordingManager()
        self.analysis_manager = AnalysisManager()
        self.playback_manager = PlaybackManager()
        self.visualization_manager = VisualizationManager(self.settings_handler)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_frame)
        
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
        
        # Recording controls
        self.recording_combo.currentIndexChanged.connect(self.update_recording_selection)
        self.refresh_button.clicked.connect(self.refresh_recordings)
        
        # Playback controls
        self.start_play_button.clicked.connect(self.start_playing)
        self.pause_play_button.clicked.connect(self.pause_playing)
        self.stop_play_button.clicked.connect(self.stop_playing)
        self.frame_slider.valueChanged.connect(self.update_frame_from_slider)

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
            width, height = self.get_save_resolution()
            
            if self.camera_manager.connect_camera(camera_index, width, height):
                self.connect_button.setText("Disconnect")
                self.timer.start(30)
                self.start_analyze_button.setEnabled(True)
                self.log("Camera connected")
            else:
                self.log("Failed to open camera")
        else:
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
        if self.playback_manager.frames and self.playback_manager.analyzed_data:
            if self.playback_manager.start_playback(self.playback_timer):
                self.start_play_button.setEnabled(False)
                self.pause_play_button.setEnabled(True)
                self.stop_play_button.setEnabled(True)
                self.log("Started playback")
        else:
            self.log("Cannot play: No recording loaded or analyzed")

    def pause_playing(self):
        if self.playback_manager.pause_playback(self.playback_timer):
            if self.playback_manager.paused:
                self.pause_play_button.setText("Resume")
                self.log("Paused playback")
            else:
                self.pause_play_button.setText("Pause")
                self.log("Resumed playback")

    def stop_playing(self):
        self.playback_manager.stop_playback(self.playback_timer)
        self.set_current_frame(0)
        self.update_analysis_display()
        self.start_play_button.setEnabled(True)
        self.pause_play_button.setEnabled(False)
        self.stop_play_button.setEnabled(False)
        self.pause_play_button.setText("Pause")
        self.log("Playback stopped")

    def analyze_selected_recording(self):
        """Analyze the currently selected recording when Analyze button is clicked"""
        recording_name = self.recording_combo.currentText()
        if not recording_name:
            self.log("No recording selected")
            return

        # Check if CSV file already exists
        timestamp = recording_name[10:-4]  # Remove "raw_movie_" prefix and ".mp4" suffix
        csv_filename = f"csv_{timestamp}.csv"
        csv_path = os.path.join("src/data/csv_data", csv_filename)
        
        if os.path.exists(csv_path):
            # Try to load existing analysis first
            try:
                self.load_csv_data(recording_name)
                if self.playback_manager.analyzed_data:
                    # Ask user if they want to overwrite
                    reply = QMessageBox.question(
                        self,
                        "Analysis Exists",
                        "Analysis data already exists for this recording. Do you want to analyze again?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.No:
                        # Load the recording and display existing analysis
                        self.log(f"Loading existing analysis for: {recording_name}")
                        self.load_recording(recording_name)
                        self.update_frame_slider_range()
                        self.update_analysis_display()
                        
                        # Enable playback controls
                        if self.playback_manager.frames and self.playback_manager.analyzed_data:
                            self.start_play_button.setEnabled(True)
                            self.pause_play_button.setEnabled(False)
                            self.stop_play_button.setEnabled(False)
                            self.pause_play_button.setText("Pause")
                            self.log(f"Loaded existing analysis: {recording_name}")
                        return
            except Exception as e:
                self.log(f"Error loading existing analysis: {str(e)}")
                # Continue with new analysis if loading fails
        
        # Proceed with new analysis
        self.log(f"Starting analysis of: {recording_name}")
        self.show_progress_bar(True)
        self.set_progress(0)
        
        # Load the recording first
        self.load_recording(recording_name)
        
        # Analyze the frames
        if self.playback_manager.frames:
            self.analysis_manager.analyze_frames(self.playback_manager.frames, self.set_progress)
            
            # Save analysis with timestamp from recording name
            if self.analysis_manager.save_analysis(timestamp, self.log):
                # Load the analysis data
                self.load_csv_data(recording_name)
                self.update_frame_slider_range()
                self.update_analysis_display()
                
                # Enable playback controls if we have data
                if self.playback_manager.frames and self.playback_manager.analyzed_data:
                    self.start_play_button.setEnabled(True)
                    self.pause_play_button.setEnabled(False)
                    self.stop_play_button.setEnabled(False)
                    self.pause_play_button.setText("Pause")
                    self.log(f"Analysis completed successfully: {recording_name}")
                else:
                    self.log(f"Failed to load analysis data: {recording_name}")
            else:
                self.log(f"Failed to save analysis: {recording_name}")
        else:
            self.log(f"Failed to load recording: {recording_name}")
        
        self.show_progress_bar(False)

    def load_recording(self, recording_name):
        self.playback_manager.frames = []
        cap = cv2.VideoCapture(os.path.join("src/data/raw_movie", recording_name))
        
        # Get video metadata
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            self.playback_manager.frames.append(frame)
        cap.release()
        
        # Update resolution and FPS display
        self.original_resolution_label.setText(f"Original: {width}x{height} | FPS: {fps:.1f}")
        self.trailed_resolution_label.setText(f"Original: {width}x{height} | FPS: {fps:.1f}")
        self.heatmap_resolution_label.setText(f"Original: {width}x{height} | FPS: {fps:.1f}")
        
        self.log(f"Loaded {recording_name} ({width}x{height} @ {fps:.1f} FPS)")

    def load_csv_data(self, recording_name):
        # Remove "raw_movie_" prefix and ".mp4" suffix
        timestamp = recording_name[10:-4]
        csv_filename = f"csv_{timestamp}.csv"
        csv_path = os.path.join("src/data/csv_data", csv_filename)
        self.playback_manager.analyzed_data = []
        try:
            with open(csv_path, "r") as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    self.playback_manager.analyzed_data.append(row)
            self.log(f"Loaded CSV data from {csv_path}")
        except FileNotFoundError:
            self.log(f"CSV file not found: {csv_path}")
            self.clear_analysis_data()
        except Exception as e:
            self.log(f"Error loading CSV data: {str(e)}")
            self.clear_analysis_data()

    def update_frame_slider_range(self):
        if self.playback_manager.frames and self.playback_manager.analyzed_data:
            max_frames = min(len(self.playback_manager.frames), len(self.playback_manager.analyzed_data))
            self.set_frame_slider_range(0, max_frames - 1)
        else:
            self.set_frame_slider_range(0, 0)
            self.log("No frames or analyzed data available")

    def update_playback_frame(self):
        if (self.playback_manager.frames and 
            self.playback_manager.analyzed_data and 
            self.playback_manager.playing and 
            not self.playback_manager.paused):
            
            max_frames = min(len(self.playback_manager.frames), 
                           len(self.playback_manager.analyzed_data))
            
            if self.playback_manager.current_frame_index < max_frames - 1:
                self.playback_manager.current_frame_index += 1
                self.set_current_frame(self.playback_manager.current_frame_index)
                self.update_analysis_display()
            else:
                self.stop_playing()

    def update_frame_from_slider(self):
        self.playback_manager.current_frame_index = self.get_current_frame()
        self.update_analysis_display()

    def update_analysis_display(self):
        if self.playback_manager.frames and self.playback_manager.analyzed_data:
            if (0 <= self.playback_manager.current_frame_index < 
                min(len(self.playback_manager.frames), 
                    len(self.playback_manager.analyzed_data))):
                
                frame = self.playback_manager.frames[self.playback_manager.current_frame_index]
                frame_data = self.playback_manager.analyzed_data[self.playback_manager.current_frame_index]
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
                    frame, 
                    self.playback_manager.analyzed_data,
                    self.playback_manager.current_frame_index
                )
                trailed_rgb = cv2.cvtColor(trailed_frame, cv2.COLOR_BGR2RGB)
                trailed_qt = QImage(
                    trailed_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
                )
                self.update_trailed_frame(QPixmap.fromImage(trailed_qt), original_size)
                
                # Update heatmap frame
                heatmap_frame = self.visualization_manager.generate_heatmap_frame(
                    frame,
                    self.playback_manager.analyzed_data,
                    self.playback_manager.current_frame_index
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
                self.log(f"Invalid frame index: {self.playback_manager.current_frame_index}")
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraViewerApp()
    window.show()
    sys.exit(app.exec_())
