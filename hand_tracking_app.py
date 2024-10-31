import sys
import cv2
import csv
import numpy as np
import mediapipe as mp
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QLabel,
    QFrame,
    QDesktopWidget,
    QTextEdit,
    QProgressBar,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from hand_classes import Hands
import os
from datetime import datetime


class CameraViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Viewer App")
        self.showMaximized()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left side: Camera view and controls
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 3)

        # Camera selection and connect button
        control_layout = QHBoxLayout()
        self.camera_combo = QComboBox()
        self.populate_camera_list()
        control_layout.addWidget(self.camera_combo)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_camera)
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

        left_layout.addWidget(self.camera_frame, 1)  # Add stretch factor

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
        self.start_button.clicked.connect(self.start_analyzing)
        settings_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Analyzing")
        self.stop_button.clicked.connect(self.stop_analyzing)
        self.stop_button.setEnabled(False)
        settings_layout.addWidget(self.stop_button)

        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        settings_layout.addWidget(self.progress_bar)

        settings_layout.addStretch(1)
        right_layout.addWidget(settings_frame)

        # Camera and timer setup
        self.camera = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # MediaPipe and analysis setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands()
        self.hands_data = Hands()
        self.analyzing = False
        self.frames = []

    def populate_camera_list(self):
        camera_list = []
        for i in range(10):  # Check first 10 camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                camera_list.append(f"Camera {i}")
                cap.release()
        self.camera_combo.addItems(camera_list)

    def toggle_camera(self):
        if self.camera is None:  # Connect to camera
            camera_index = int(self.camera_combo.currentText().split()[-1])
            self.camera = cv2.VideoCapture(camera_index)
            if self.camera.isOpened():
                self.connect_button.setText("Disconnect")
                self.timer.start(30)  # Update every 30 ms (approx. 33 fps)
                self.start_button.setEnabled(True)
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
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
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

            # Scale the pixmap to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.camera_label.setPixmap(scaled_pixmap)

    def start_analyzing(self):
        self.analyzing = True
        self.frames = []
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log("Started analyzing")

    def stop_analyzing(self):
        self.analyzing = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log("Stopped analyzing")
        self.analyze_frames()
        self.save_raw_movie()

    def analyze_frames(self):
        analyzed_data = []
        total_frames = len(self.frames)
        for frame_idx, frame in enumerate(self.frames):
            results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_data = {"frame": frame_idx}
            if results.multi_hand_landmarks:
                self.hands_data.update_landmarks(
                    results.multi_hand_landmarks, results.multi_handedness
                )
                frame_data.update(self.hands_data.get_data())

                # Flip hand tags to correct mirroring
                flipped_data = {}
                for key, value in frame_data.items():
                    if key.startswith("left_"):
                        flipped_data["right_" + key[5:]] = value
                    elif key.startswith("right_"):
                        flipped_data["left_" + key[6:]] = value
                    else:
                        flipped_data[key] = value
                frame_data = flipped_data
            else:
                # Add zeros for frames without hand detection
                for hand in ["left", "right"]:
                    for landmark in self.hands_data.left_hand.landmarks.keys():
                        frame_data[f"{hand}_{landmark}"] = np.zeros(3)
            analyzed_data.append(frame_data)

            # Update progress bar every 10 frames
            if frame_idx % 10 == 0:
                progress = int((frame_idx + 1) / total_frames * 100)
                self.progress_bar.setValue(progress)
                QApplication.processEvents()  # Ensure GUI updates

        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self.save_to_csv(analyzed_data)

    def save_to_csv(self, data):
        if not data:
            self.log("No data to save")
            return

        # Create csv_data folder if it doesn't exist
        os.makedirs("csv_data", exist_ok=True)

        # Generate filename with current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"csv_data/csv_{timestamp}.csv"

        fieldnames = ["frame"] + sorted(list(data[0].keys() - {"frame"}))

        with open(filename, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

        self.log(f"Data saved to {filename}")

    def save_raw_movie(self):
        if not self.frames:
            self.log("No frames to save as movie")
            return

        # Create raw_movie folder if it doesn't exist
        os.makedirs("raw_movie", exist_ok=True)

        # Generate filename with current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raw_movie/raw_movie_{timestamp}.mp4"

        # Get video properties
        height, width, _ = self.frames[0].shape
        fps = 30  # Assuming 30 fps, adjust if needed

        # Create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

        total_frames = len(self.frames)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        for i, frame in enumerate(self.frames):
            out.write(frame)

            # Update progress bar every 10 frames
            if i % 10 == 0:
                progress = int((i + 1) / total_frames * 100)
                self.progress_bar.setValue(progress)
                QApplication.processEvents()  # Ensure GUI updates

        out.release()
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self.log(f"Raw movie saved to {filename}")

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_text.append(log_message)
        print(log_message)  # Also print to console for debugging


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraViewerApp()
    window.show()
    sys.exit(app.exec_())
