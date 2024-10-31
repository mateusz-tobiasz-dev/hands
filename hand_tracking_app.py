import sys
import cv2
import os
import csv
from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QLabel
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from camera_viewer_gui import CameraViewerGUI
from hand_analyzer import HandAnalyzer
from utils import save_to_csv, save_raw_movie, log_message
from hand_landmarks import LANDMARK_DICT, STATS_DICT


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
        self.recording_combo.addItems(recording_list)

    def toggle_camera(self):
        if self.camera is None:  # Connect to camera
            camera_index = int(self.camera_combo.currentText().split()[-1])
            self.camera = cv2.VideoCapture(camera_index)
            if self.camera.isOpened():
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
        self.log(f"Analysis data saved to {csv_file}")
        self.populate_recording_list()

    def save_raw_movie(self):
        raw_movie_file = save_raw_movie(self.frames, self.log, self.set_progress)
        self.log(f"Raw movie saved to {raw_movie_file}")
        self.show_progress_bar(False)
        self.populate_recording_list()

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

                # Update analyzed image
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                convert_to_qt_format = QImage(
                    frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888
                )
                pixmap = QPixmap.fromImage(convert_to_qt_format)
                self.update_analyzed_frame(pixmap)

                # Update landmarks
                left_landmarks = self.parse_landmarks(frame_data, "left")
                right_landmarks = self.parse_landmarks(frame_data, "right")
                self.update_landmarks_table(self.left_landmarks_table, left_landmarks)
                self.update_landmarks_table(self.right_landmarks_table, right_landmarks)

                # Update stats table
                stats = self.parse_stats(frame_data)
                self.update_stats_table(self.stats_table, stats)
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

    def update_stats_table(self, table, parsed_data):
        if parsed_data is None or (
            isinstance(parsed_data, list) and len(parsed_data) == 0
        ):
            table.setRowCount(0)
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["FRAME", "LEFT", "RIGHT"])
            return

        num_stats = len(STATS_DICT)
        table.setRowCount(num_stats)
        table.setColumnCount(3)  # FRAME, LEFT, RIGHT

        table.setHorizontalHeaderLabels(["FRAME", "LEFT", "RIGHT"])

        vertical_headers = list(STATS_DICT.values())
        table.setVerticalHeaderLabels(vertical_headers)

        frame_number = (
            parsed_data.get("frame", 0) if isinstance(parsed_data, dict) else 0
        )

        for row, stat_name in enumerate(STATS_DICT.values()):
            table.setItem(row, 0, QTableWidgetItem(str(frame_number)))

            left_value = (
                parsed_data.get("left", {}).get(stat_name, "N/A")
                if isinstance(parsed_data, dict)
                else "N/A"
            )
            left_item = QTableWidgetItem(self.format_value(left_value))
            table.setItem(row, 1, left_item)

            right_value = (
                parsed_data.get("right", {}).get(stat_name, "N/A")
                if isinstance(parsed_data, dict)
                else "N/A"
            )
            right_item = QTableWidgetItem(self.format_value(right_value))
            table.setItem(row, 2, right_item)

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

    def update_landmarks_table(self, table, landmarks):
        table.setColumnCount(len(landmarks))
        table.setRowCount(1)

        headers = []
        for idx, landmark in enumerate(landmarks):
            headers.append(landmark[0])
            if landmark[0] == "FRAME":
                value_str = str(landmark[1])
            else:
                value_str = f"x: {self.format_value(landmark[1])}\ny: {self.format_value(landmark[2])}\nz: {self.format_value(landmark[3])}"
            table.setItem(0, idx, QTableWidgetItem(value_str))

        table.setHorizontalHeaderLabels(headers)
        table.resizeRowsToContents()

    def format_value(self, value):
        try:
            num_value = float(value)
            return f"{num_value:.5f}"
        except (ValueError, TypeError):
            return str(value)

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
        self.update_stats_table(self.stats_table, [])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraViewerApp()
    window.show()
    sys.exit(app.exec_())
