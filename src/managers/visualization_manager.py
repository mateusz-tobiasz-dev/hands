import cv2
import numpy as np
from src.utils.drawing_utils import get_hand_colors, get_finger_idx
from src.core.hand_landmarks import LANDMARK_DICT

class VisualizationManager:
    def __init__(self, settings_handler):
        self.settings_handler = settings_handler

    def generate_trailed_frame(self, current_frame, analyzed_data, current_frame_index):
        # Get settings
        trail_length = self.settings_handler.settings["Trailing"]["trail_length"]
        landmark_size = self.settings_handler.settings["Trailing"]["landmark_size"]
        alpha = self.settings_handler.settings["Trailing"]["alpha"]
        black_background = self.settings_handler.settings["Trailing"]["black_background"]
        alpha_fade = self.settings_handler.settings["Trailing"]["alpha_fade"]
        
        # Create frame based on background setting
        if black_background:
            frame = np.zeros_like(current_frame)
        else:
            frame = current_frame.copy()
        
        # Get previous frames' data
        start_idx = max(0, current_frame_index - trail_length)
        trail_data = analyzed_data[start_idx:current_frame_index]
        
        # Draw trails for each hand
        for hand in ['left', 'right']:
            is_left_hand = hand == 'left'
            hand_colors = get_hand_colors(is_left_hand)
            
            for frame_idx, trail_frame in enumerate(trail_data):
                # Calculate fade factor if alpha fade is enabled
                if alpha_fade:
                    fade_factor = (frame_idx + 1) / len(trail_data)  # Newer frames have higher alpha
                else:
                    fade_factor = 1.0
                
                frame_alpha = alpha * fade_factor
                
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
                                    color = tuple(int(c * frame_alpha) for c in hand_colors[finger_idx])
                                    cv2.circle(frame, (pos_x, pos_y), landmark_size, color, -1)
                            except (ValueError, IndexError):
                                continue
                    except Exception as e:
                        print(f"Error processing coordinates for {hand}_{landmark}: {e}")
                        continue
                        
        return frame
        
    def generate_heatmap_frame(self, current_frame, analyzed_data, current_frame_index):
        frame = current_frame.copy()
        heatmap = np.zeros(frame.shape[:2], dtype=np.float32)
        
        # Get settings
        alpha = self.settings_handler.settings["Trailing"]["alpha"]
        landmark_size = self.settings_handler.settings["Trailing"]["landmark_size"]
        
        # Accumulate positions for heatmap
        for frame_data in analyzed_data[:current_frame_index + 1]:
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
                        print(f"Error processing coordinates for {hand}_{landmark}: {e}")
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
