import cv2
from PyQt5.QtCore import QTimer

class CameraManager:
    def __init__(self):
        self.camera = None
        self.frame_timer = QTimer()
        
    def get_camera_list(self):
        camera_list = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                camera_list.append(f"Camera {i}")
                cap.release()
        return camera_list
    
    def connect_camera(self, camera_index, width, height):
        self.camera = cv2.VideoCapture(camera_index)
        if self.camera.isOpened():
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            return True
        return False
    
    def disconnect_camera(self):
        if self.camera:
            self.camera.release()
            self.camera = None
    
    def read_frame(self):
        if self.camera:
            return self.camera.read()
        return False, None
