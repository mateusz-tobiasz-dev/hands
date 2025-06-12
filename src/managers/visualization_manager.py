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
        opacity = self.settings_handler.settings["Trailing"]["opacity"]
        black_background = self.settings_handler.settings["Trailing"][
            "black_background"
        ]
        alpha_fade = self.settings_handler.settings["Trailing"]["alpha_fade"]

        # Create frame based on background setting
        if black_background:
            frame = np.zeros_like(current_frame)
        else:
            frame = current_frame.copy()

        # Create an overlay for the trails
        overlay = np.zeros_like(frame)

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
                    # Older frames should be more transparent
                    fade_factor = (frame_idx + 1) / len(trail_data)
                else:
                    fade_factor = 1.0

                frame_alpha = alpha * fade_factor

                for landmark_idx, landmark in enumerate(LANDMARK_DICT.values()):
                    try:
                        x = trail_frame.get(f"{hand}_{landmark}_x", None)
                        y = trail_frame.get(f"{hand}_{landmark}_y", None)
                        if x is not None and y is not None:
                            try:
                                x_float = float(
                                    str(x).split(".")[0] + "." + str(x).split(".")[1]
                                )
                                y_float = float(
                                    str(y).split(".")[0] + "." + str(y).split(".")[1]
                                )
                                pos_x = int(x_float * frame.shape[1])
                                pos_y = int(y_float * frame.shape[0])

                                if (
                                    0 <= pos_x < frame.shape[1]
                                    and 0 <= pos_y < frame.shape[0]
                                ):
                                    # Get finger color based on landmark index
                                    finger_idx = get_finger_idx(landmark_idx)
                                    # Apply fade factor to the color intensity
                                    color = tuple(
                                        int(c * frame_alpha)
                                        for c in hand_colors[finger_idx]
                                    )
                                    cv2.circle(
                                        overlay,
                                        (pos_x, pos_y),
                                        landmark_size,
                                        color,
                                        -1,
                                    )
                            except (ValueError, IndexError):
                                continue
                    except Exception as e:
                        print(
                            f"Error processing coordinates for {hand}_{landmark}: {e}"
                        )
                        continue

        # Blend with the frame using opacity
        result = cv2.addWeighted(frame, opacity, overlay, 1.0, 0)
        return result

    def generate_heatmap_frame(
        self,
        current_frame,
        analyzed_data,
        current_frame_index,
        start_frame=None,
        end_frame=None,
    ):
        # Get heatmap settings
        radius = self.settings_handler.settings["Heatmap"]["radius"]
        opacity = self.settings_handler.settings["Heatmap"]["opacity"]
        color_map = self.settings_handler.settings["Heatmap"]["color_map"]
        blur_amount = self.settings_handler.settings["Heatmap"]["blur_amount"]
        black_background = self.settings_handler.settings["Heatmap"]["black_background"]
        accumulate = self.settings_handler.settings["Heatmap"]["accumulate"]

        # Create frame based on background setting
        if black_background:
            frame = np.zeros_like(current_frame)
        else:
            frame = current_frame.copy()

        # Create heatmap overlay
        heatmap = np.zeros(frame.shape[:2], dtype=np.float32)

        # Determine frame range
        if start_frame is None:
            start_frame = 0 if accumulate else current_frame_index
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

        # Draw all circles with the specified radius
        for pos_x, pos_y in coordinates:
            cv2.circle(heatmap, (pos_x, pos_y), radius, 1, -1)

        # Apply Gaussian blur with specified amount
        if blur_amount > 0:
            heatmap = cv2.GaussianBlur(
                heatmap, (blur_amount * 2 + 1, blur_amount * 2 + 1), 0
            )

        # Normalize and apply colormap
        if np.max(heatmap) > 0:
            # Normalize to 0-255
            heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(
                np.uint8
            )

            # Apply selected colormap
            colormap_dict = {
                "jet": cv2.COLORMAP_JET,
                "hot": cv2.COLORMAP_HOT,
                "rainbow": cv2.COLORMAP_RAINBOW,
                "ocean": cv2.COLORMAP_OCEAN,
                "viridis": cv2.COLORMAP_VIRIDIS,
                "plasma": cv2.COLORMAP_PLASMA,
                "magma": cv2.COLORMAP_MAGMA,
                "inferno": cv2.COLORMAP_INFERNO,
            }
            colormap_value = colormap_dict.get(color_map, cv2.COLORMAP_JET)
            heatmap_colored = cv2.applyColorMap(heatmap, colormap_value)

            # Blend with original frame using specified opacity
            result = cv2.addWeighted(frame, 1 - opacity, heatmap_colored, opacity, 0)
            return result

        return frame
