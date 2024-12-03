import os
from datetime import datetime
from src.utils.utils import save_raw_movie

class RecordingManager:
    def __init__(self):
        self.frames = []
        self.analyzed_data = []
        self.current_recording = None
        self.current_frame_index = 0
        self.is_recording = False
        self.current_timestamp = None
        
    def start_recording(self):
        self.frames = []
        self.analyzed_data = []
        self.is_recording = True
        self.current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def stop_recording(self):
        self.is_recording = False
        
    def add_frame(self, frame):
        if self.is_recording:
            self.frames.append(frame)
    
    def get_recording_list(self):
        return [f for f in os.listdir("src/data/raw_movie") if f.endswith(".mp4")]
    
    def save_recording(self):
        if not self.frames:
            return None
            
        # Create output directory
        os.makedirs("src/data/raw_movie", exist_ok=True)
        
        # Use the timestamp from start_recording
        if not self.current_timestamp:
            self.current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        output_path = os.path.join("src/data/raw_movie", f"raw_movie_{self.current_timestamp}.mp4")
        return save_raw_movie(self.frames, output_path)
    
    def get_current_timestamp(self):
        return self.current_timestamp
