from PyQt5.QtCore import QTimer

class PlaybackManager:
    def __init__(self):
        self.playing = False
        self.paused = False
        self.current_frame_index = 0
        self.frames = []
        self.analyzed_data = []
        
    def load_recording(self, frames, analyzed_data):
        self.frames = frames
        self.analyzed_data = analyzed_data
        self.current_frame_index = 0
        
    def start_playback(self, timer):
        if self.frames and self.analyzed_data:
            self.playing = True
            self.paused = False
            timer.start(33)  # ~30 fps
            return True
        return False
    
    def pause_playback(self, timer):
        if self.playing:
            self.paused = not self.paused
            if self.paused:
                timer.stop()
            else:
                timer.start(33)
            return True
        return False
    
    def stop_playback(self, timer):
        self.playing = False
        self.paused = False
        timer.stop()
        self.current_frame_index = 0
