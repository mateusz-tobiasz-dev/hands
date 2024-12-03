from PyQt5.QtCore import QTimer
import cv2

class PlaybackManager:
    def __init__(self):
        self.cap = None
        self.analyzed_data = []
        self.current_frame_index = 0
        self.playing = False
        self.paused = False

    def load_recording(self, video_path):
        """Load a video recording"""
        try:
            if self.cap is not None:
                self.cap.release()
            
            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                print(f"Failed to open video: {video_path}")
                return False
                
            # Set initial position
            self.current_frame_index = 0
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            return True
        except Exception as e:
            print(f"Error loading video: {str(e)}")
            return False

    def get_frame(self, frame_index):
        """Get a specific frame from the video"""
        if self.cap is None:
            return None
                
        try:
            # Check if we need to seek to the frame
            current_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            if current_pos != frame_index:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            
            ret, frame = self.cap.read()
            if ret:
                # Reset position if we reached the end
                if frame_index >= self.get_total_frames() - 1:
                    self.current_frame_index = 0
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                else:
                    self.current_frame_index = frame_index
                return frame
            else:
                print(f"Failed to read frame {frame_index}")
                return None
        except Exception as e:
            print(f"Error getting frame: {str(e)}")
            return None

    def get_total_frames(self):
        """Get total number of frames in video"""
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) if self.cap else 0
        
    def is_playback_ready(self):
        """Check if playback is ready (both video and analysis data available)"""
        return self.cap is not None and len(self.analyzed_data) > 0

    def start_playback(self, timer):
        """Start playback with given timer"""
        if self.cap is not None and self.analyzed_data:
            self.playing = True
            self.paused = False
            timer.start(30)  # 30ms for ~30fps
            return True
        return False

    def pause_playback(self, timer):
        """Pause/resume playback"""
        if self.playing:
            self.paused = not self.paused
            if self.paused:
                timer.stop()
            else:
                timer.start(30)
            return True
        return False

    def stop_playback(self, timer):
        """Stop playback"""
        self.playing = False
        self.paused = False
        self.current_frame_index = 0
        timer.stop()
        return True

    def __del__(self):
        """Clean up video capture object"""
        if self.cap is not None:
            self.cap.release()