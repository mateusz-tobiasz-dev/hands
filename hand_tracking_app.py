import sys
import cv2
import os
import csv
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from camera_viewer_gui import CameraViewerGUI
from hand_analyzer import HandAnalyzer
from utils import save_to_csv, save_raw_movie, log_message
from hand_landmarks import LANDMARK_DICT, STATS_DICT
from datetime import datetime
import numpy as np
from drawing_utils import get_hand_colors, get_finger_idx


class CameraViewerApp(CameraViewerGUI):
    def __init__(self):
        super().__init__()

        self.camera = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_frame)

        self.hand_analyzer = HandAnalyzer()
        self.analyzing = False
        self.playing = False
        self.paused = False
        self.frames = []
        self.analyzed_data = []
        self.current_recording = None
        self.current_frame_index = 0

        self.connect_signals()
        self.populate_camera_list()
        self.populate_recording_list()
        self.clear_analysis_data()

    def connect_signals(self):
        self.connect_button.clicked.connect(self.toggle_camera)
        self.start_analyze_button.clicked.connect(self.start_analyzing)
        self.stop_analyze_button.clicked.connect(self.stop_analyzing)
        self.start_play_button.clicked.connect(self.start_playing)
        self.pause_play_button.clicked.connect(self.pause_playing)
        self.stop_play_button.clicked.connect(self.stop_playing)
        self.analyze_button.clicked.connect(self.analyze_selected_recording)
        self.frame_slider.valueChanged.connect(self.update_frame_from_slider)
        self.recording_combo.currentIndexChanged.connect(self.update_selected_recording)
        self.refresh_button.clicked.connect(self.refresh_recordings)

    def populate_camera_list(self):
        camera_list = []
        for i in range(10):  # Check first 10 camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                camera_list.append(f"Camera {i}")
                cap.release()
        self.camera_combo.addItems(camera_list)

    def populate_recording_list(self):
        recording_list = [f for f in os.listdir("raw_movie") if f.endswith(".mp4")]
        self.update_recording_combo(recording_list)

    def refresh_recordings(self):
        self.populate_recording_list()
        self.log("Refreshed recording list")

    def toggle_camera(self):
        if self.camera is None:  # Connect to camera
            camera_index = int(self.camera_combo.currentText().split()[-1])
            self.camera = cv2.VideoCapture(camera_index)
            if self.camera.isOpened():
                # Get resolution settings from GUI
                width, height = self.get_save_resolution()
                
                # Set camera resolution
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                # Verify if resolution was set
                actual_width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
                actual_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
                self.log(f"Camera resolution set to {actual_width}x{actual_height}")
                
                self.connect_button.setText("Disconnect")
                self.timer.start(30)  # Update every 30 ms (approx. 33 fps)
                self.start_analyze_button.setEnabled(True)
                self.log("Camera connected")
            else:
                self.camera = None
                self.log("Failed to open camera")
        else:  # Disconnect from camera
            self.timer.stop()
            self.camera.release()
            self.camera = None
            self.connect_button.setText("Connect")
            self.camera_label.clear()
            self.start_analyze_button.setEnabled(False)
            self.stop_analyze_button.setEnabled(False)
            self.log("Camera disconnected")

    def update_frame(self):
        ret, frame = self.camera.read()
        if ret:
            if self.analyzing:
                self.frames.append(frame)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            convert_to_qt_format = QImage(
                frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
            )
            pixmap = QPixmap.fromImage(convert_to_qt_format)
            self.update_camera_frame(pixmap)

    def start_analyzing(self):
        if self.camera is None or not self.camera.isOpened():
            self.log("Cannot start analysis: Camera is not connected")
            return

        self.analyzing = True
        self.frames = []
        self.analyzed_data = []
        self.start_analyze_button.setEnabled(False)
        self.stop_analyze_button.setEnabled(True)
        self.show_progress_bar(True)
        self.set_progress(0)
        self.log("Started analyzing")

    def stop_analyzing(self):
        self.analyzing = False
        self.start_analyze_button.setEnabled(True)
        self.stop_analyze_button.setEnabled(False)
        self.log("Stopped analyzing")
        self.analyze_frames()
        self.save_raw_movie()

    def start_playing(self):
        if self.current_recording and self.frames and self.analyzed_data:
            self.playing = True
            self.paused = False
            self.playback_timer.start(33)  # ~30 fps
            self.start_play_button.setEnabled(False)
            self.pause_play_button.setEnabled(True)
            self.stop_play_button.setEnabled(True)
            self.log("Started playback")
        else:
            self.log("Cannot play: No recording loaded or analyzed")

    def pause_playing(self):
        if self.playing:
            if self.paused:
                self.paused = False
                self.playback_timer.start(33)
                self.pause_play_button.setText("Pause")
                self.log("Resumed playback")
            else:
                self.paused = True
                self.playback_timer.stop()
                self.pause_play_button.setText("Resume")
                self.log("Paused playback")

    def stop_playing(self):
        self.playing = False
        self.paused = False
        self.playback_timer.stop()
        self.current_frame_index = 0
        self.set_current_frame(self.current_frame_index)
        self.update_analysis_display()
        self.start_play_button.setEnabled(True)
        self.pause_play_button.setEnabled(False)
        self.stop_play_button.setEnabled(False)
        self.pause_play_button.setText("Pause")
        self.log("Playback stopped")

    def analyze_frames(self):
        total_frames = len(self.frames)
        self.analyzed_data = []
        for frame_idx, frame in enumerate(self.frames):
            # Analyze each frame
            frame_data = self.hand_analyzer.analyze_frame(frame, frame_idx)
            self.analyzed_data.append(frame_data)

            # Update progress bar
            progress = int((frame_idx + 1) / total_frames * 100)
            self.set_progress(progress)
            QApplication.processEvents()  # Allow GUI to update

        self.set_progress(100)
        self.show_progress_bar(False)
        csv_file = save_to_csv(self.analyzed_data, self.log)
        self.log("Analysis data saved")
        self.populate_recording_list()

    def save_raw_movie(self):
        """
        Save the recorded frames as a movie file using the configured resolution.
        """
        if not self.frames:
            self.log("No frames available to save")
            return
            
        # Get resolution settings from camera viewer
        width, height = self.get_save_resolution()
        
        # Create output directory
        os.makedirs("raw_movie", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"raw_movie/raw_movie_{timestamp}.mp4"
        
        try:
            success, message = save_raw_movie(
                self.frames,
                output_path,
                fps=30,
                width=width,
                height=height
            )
            
            if success:
                self.log(message)
            else:
                self.log(f"Error: {message}")
                
        except Exception as e:
            self.log(f"Failed to save video: {str(e)}")

    def analyze_selected_recording(self):
        self.current_recording = self.recording_combo.currentText()
        if self.current_recording:
            self.current_frame_index = 0
            self.load_recording(self.current_recording)
            self.load_csv_data(self.current_recording)
            self.update_frame_slider_range()
            self.update_analysis_display()
        else:
            self.log("No recording selected")
            self.clear_analysis_data()

    def load_recording(self, recording_name):
        self.frames = []
        cap = cv2.VideoCapture(os.path.join("raw_movie", recording_name))
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            self.frames.append(frame)
        cap.release()
        self.log(f"Loaded {recording_name}")

    def load_csv_data(self, recording_name):
        # Remove "raw_movie_" prefix and ".mp4" suffix
        timestamp = recording_name[10:-4]
        csv_filename = f"csv_{timestamp}.csv"
        csv_path = os.path.join("csv_data", csv_filename)
        self.analyzed_data = []
        try:
            with open(csv_path, "r") as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    self.analyzed_data.append(row)
            self.log(f"Loaded CSV data from {csv_path}")
        except FileNotFoundError:
            self.log(f"CSV file not found: {csv_path}")
            self.clear_analysis_data()
        except Exception as e:
            self.log(f"Error loading CSV data: {str(e)}")
            self.clear_analysis_data()

    def update_frame_slider_range(self):
        if self.frames and self.analyzed_data:
            max_frames = min(len(self.frames), len(self.analyzed_data))
            self.set_frame_slider_range(0, max_frames - 1)
        else:
            self.set_frame_slider_range(0, 0)
            self.log("No frames or analyzed data available")

    def update_playback_frame(self):
        if self.frames and self.analyzed_data and not self.paused:
            if (
                self.current_frame_index
                < min(len(self.frames), len(self.analyzed_data)) - 1
            ):
                self.current_frame_index += 1
                self.set_current_frame(self.current_frame_index)
                self.update_analysis_display()
            else:
                self.stop_playing()
        elif self.paused:
            self.update_analysis_display()

    def update_frame_from_slider(self):
        self.current_frame_index = self.get_current_frame()
        self.update_analysis_display()

    def update_analysis_display(self):
        if self.frames and self.analyzed_data:
            if (
                0
                <= self.current_frame_index
                < min(len(self.frames), len(self.analyzed_data))
            ):
                frame = self.frames[self.current_frame_index]
                frame_data = self.analyzed_data[self.current_frame_index]
                original_size = (frame.shape[1], frame.shape[0])  # width, height

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
                trailed_frame = self.generate_trailed_frame(frame, frame_data)
                trailed_rgb = cv2.cvtColor(trailed_frame, cv2.COLOR_BGR2RGB)
                trailed_qt = QImage(
                    trailed_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
                )
                self.update_trailed_frame(QPixmap.fromImage(trailed_qt), original_size)
                
                # Update heatmap frame
                heatmap_frame = self.generate_heatmap_frame(frame)
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
                self.log(f"Invalid frame index: {self.current_frame_index}")
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

    def update_selected_recording(self):
        self.clear_analysis_data()

    def log(self, message):
        log_msg = log_message(message)
        self.append_log(log_msg)
        print(log_msg)  # Also print to console for debugging

    def clear_analysis_data(self):
        super().clear_analysis_data()
        self.update_analyzed_frame(None)
        self.update_landmarks_table(self.left_landmarks_table, [])
        self.update_landmarks_table(self.right_landmarks_table, [])
        self.update_stats_table(None)

    def generate_trailed_frame(self, current_frame, frame_data, trail_length=None):
        frame = current_frame.copy()
        
        # Get settings
        trail_length = trail_length or self.settings_handler.settings["Trailing"]["trail_length"]
        landmark_size = self.settings_handler.settings["Trailing"]["landmark_size"]
        alpha = self.settings_handler.settings["Trailing"]["alpha"]
        
        # Get previous frames' data
        start_idx = max(0, self.current_frame_index - trail_length)
        trail_data = self.analyzed_data[start_idx:self.current_frame_index]
        
        # Draw trails for each hand
        for hand in ['left', 'right']:
            is_left_hand = hand == 'left'
            hand_colors = get_hand_colors(is_left_hand)
            
            for trail_frame in trail_data:
                for landmark_idx, landmark in enumerate(LANDMARK_DICT.values()):
                    try:
                        x = trail_frame.get(f"{hand}_{landmark}_x", None)
                        y = trail_frame.get(f"{hand}_{landmark}_y", None)
                        if x is not None and y is not None:
                            # Convert coordinates to float and handle potential string format issues
                            try:
                                x_float = float(str(x).split('.')[0] + '.' + str(x).split('.')[1])
                                y_float = float(str(y).split('.')[0] + '.' + str(y).split('.')[1])
                                
                                pos_x = int(x_float * frame.shape[1])
                                pos_y = int(y_float * frame.shape[0])
                                
                                # Ensure coordinates are within frame bounds
                                if 0 <= pos_x < frame.shape[1] and 0 <= pos_y < frame.shape[0]:
                                    # Get finger color based on landmark index
                                    finger_idx = get_finger_idx(landmark_idx)
                                    color = tuple(int(c * alpha) for c in hand_colors[finger_idx])
                                    cv2.circle(frame, (pos_x, pos_y), landmark_size, color, -1)
                            except (ValueError, IndexError):
                                continue
                    except Exception as e:
                        self.log(f"Error processing coordinates for {hand}_{landmark}: {e}")
                        continue
                        
        return frame
        
    def generate_heatmap_frame(self, current_frame):
        frame = current_frame.copy()
        heatmap = np.zeros(frame.shape[:2], dtype=np.float32)
        
        # Get settings
        alpha = self.settings_handler.settings["Trailing"]["alpha"]
        landmark_size = self.settings_handler.settings["Trailing"]["landmark_size"]
        
        # Accumulate positions for heatmap
        for frame_data in self.analyzed_data[:self.current_frame_index + 1]:
            for hand in ['left', 'right']:
                for landmark_idx, landmark in enumerate(LANDMARK_DICT.values()):
                    try:
                        x = frame_data.get(f"{hand}_{landmark}_x", None)
                        y = frame_data.get(f"{hand}_{landmark}_y", None)
                        if x is not None and y is not None:
                            # Convert coordinates to float and handle potential string format issues
                            try:
                                x_float = float(str(x).split('.')[0] + '.' + str(x).split('.')[1])
                                y_float = float(str(y).split('.')[0] + '.' + str(y).split('.')[1])
                                
                                pos_x = int(x_float * frame.shape[1])
                                pos_y = int(y_float * frame.shape[0])
                                
                                # Ensure coordinates are within frame bounds
                                if 0 <= pos_x < frame.shape[1] and 0 <= pos_y < frame.shape[0]:
                                    # Use landmark size from settings for heatmap intensity
                                    cv2.circle(heatmap, (pos_x, pos_y), landmark_size * 2, 1, -1)
                            except (ValueError, IndexError):
                                continue
                    except Exception as e:
                        self.log(f"Error processing coordinates for {hand}_{landmark}: {e}")
                        continue
        
        # Normalize heatmap
        if np.max(heatmap) > 0:  # Only normalize if we have any data
            heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX)
            heatmap = heatmap.astype(np.uint8)
            
            # Apply colormap
            heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            
            # Blend with original frame using alpha from settings
            result = cv2.addWeighted(frame, 1 - alpha, heatmap_colored, alpha, 0)
            
            return result
        
        return frame  # Return original frame if no heatmap data


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraViewerApp()
    window.show()
    sys.exit(app.exec_())
