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
        black_background = self.settings_handler.settings["Trailing"][
            "black_background"
        ]
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
        for hand in ["left", "right"]:
            is_left_hand = hand == "left"
            hand_colors = get_hand_colors(is_left_hand)

            for frame_idx, trail_frame in enumerate(trail_data):
                # Calculate fade factor if alpha fade is enabled
                if alpha_fade:
                    fade_factor = (frame_idx + 1) / len(
                        trail_data
                    )  # Newer frames have higher alpha
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
                                x_float = float(
                                    str(x).split(".")[0] + "." + str(x).split(".")[1]
                                )
                                y_float = float(
                                    str(y).split(".")[0] + "." + str(y).split(".")[1]
                                )

                                pos_x = int(x_float * frame.shape[1])
                                pos_y = int(y_float * frame.shape[0])

                                # Ensure coordinates are within frame bounds
                                if (
                                    0 <= pos_x < frame.shape[1]
                                    and 0 <= pos_y < frame.shape[0]
                                ):
                                    # Get finger color based on landmark index
                                    finger_idx = get_finger_idx(landmark_idx)
                                    color = tuple(
                                        int(c * frame_alpha)
                                        for c in hand_colors[finger_idx]
                                    )
                                    cv2.circle(
                                        frame, (pos_x, pos_y), landmark_size, color, -1
                                    )
                            except (ValueError, IndexError):
                                continue
                    except Exception as e:
                        print(
                            f"Error processing coordinates for {hand}_{landmark}: {e}"
                        )
                        continue

        return frame

    def generate_heatmap_frame(
        self,
        current_frame,
        analyzed_data,
        current_frame_index,
        start_frame=None,
        end_frame=None,
    ):
        frame = current_frame.copy()
        heatmap = np.zeros(frame.shape[:2], dtype=np.float32)

        # Get settings
        alpha = self.settings_handler.settings["Trailing"]["alpha"]
        landmark_size = self.settings_handler.settings["Trailing"]["landmark_size"]

        # Determine frame range
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = current_frame_index

        # Create a list of coordinates for all landmarks
        coordinates = []
        for frame_dict in analyzed_data[start_frame : end_frame + 1]:
            for hand in ["left", "right"]:
                for landmark in LANDMARK_DICT.values():
                    x = frame_dict.get(f"{hand}_{landmark}_x")
                    y = frame_dict.get(f"{hand}_{landmark}_y")
                    if x is not None and y is not None:
                        try:
                            x_float = float(
                                str(x).split(".")[0] + "." + str(x).split(".")[1]
                            )
                            y_float = float(
                                str(y).split(".")[0] + "." + str(y).split(".")[1]
                            )
                            pos_x = int(x_float * heatmap.shape[1])
                            pos_y = int(y_float * heatmap.shape[0])
                            if (
                                0 <= pos_x < heatmap.shape[1]
                                and 0 <= pos_y < heatmap.shape[0]
                            ):
                                coordinates.append((pos_x, pos_y))
                        except (ValueError, IndexError):
                            continue

        # Draw all circles with optimized parameters for real-time display
        kernel_size = landmark_size * 2  # Smaller kernel for better performance
        for pos_x, pos_y in coordinates:
            cv2.circle(heatmap, (pos_x, pos_y), kernel_size, 1, -1)

        # Apply optimized Gaussian blur
        blur_size = min(kernel_size * 2 + 1, 15)  # Cap blur size for performance
        heatmap = cv2.GaussianBlur(heatmap, (blur_size, blur_size), blur_size / 4)

        # Normalize and apply colormap
        if np.max(heatmap) > 0:
            # Normalize to 0-255
            heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(
                np.uint8
            )

            # Apply JET colormap directly for better performance
            heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

            # Increase contrast
            heatmap_colored = cv2.addWeighted(
                heatmap_colored, 1.5, heatmap_colored, 0, 0
            )

            # Blend with original frame
            result = cv2.addWeighted(frame, 1 - alpha, heatmap_colored, alpha, 0)
            return result

        return frame
