import sys
import cv2
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from camera_viewer_gui import CameraViewerGUI
from hand_analyzer import HandAnalyzer
from utils import save_to_csv, save_raw_movie, log_message


class CameraViewerApp(CameraViewerGUI):
    def __init__(self):
        super().__init__()

        self.camera = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.hand_analyzer = HandAnalyzer()
        self.analyzing = False
        self.frames = []

        self.connect_signals()
        self.populate_camera_list()

    def connect_signals(self):
        self.connect_button.clicked.connect(self.toggle_camera)
        self.start_button.clicked.connect(self.start_analyzing)
        self.stop_button.clicked.connect(self.stop_analyzing)

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
            self.update_camera_frame(pixmap)

    def start_analyzing(self):
        self.analyzing = True
        self.frames = []
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.show_progress_bar(True)
        self.set_progress(0)
        self.log("Started analyzing")

    def stop_analyzing(self):
        self.analyzing = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log("Stopped analyzing")
        self.analyze_frames()
        self.save_raw_movie()

    def analyze_frames(self):
        analyzed_data = self.hand_analyzer.analyze_frames(self.frames)
        total_frames = len(self.frames)
        for frame_idx, _ in enumerate(analyzed_data):
            if frame_idx % 10 == 0:
                progress = int((frame_idx + 1) / total_frames * 100)
                self.set_progress(progress)
                QApplication.processEvents()

        self.set_progress(100)
        self.show_progress_bar(False)
        save_to_csv(analyzed_data, self.log)

    def save_raw_movie(self):
        save_raw_movie(self.frames, self.log, self.set_progress)
        self.show_progress_bar(False)

    def log(self, message):
        log_msg = log_message(message)
        self.append_log(log_msg)
        print(log_msg)  # Also print to console for debugging


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraViewerApp()
    window.show()
    sys.exit(app.exec_())
