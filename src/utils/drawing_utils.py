import cv2
import time


def get_finger_idx(idx):
    if idx <= 4:  # THUMB_TIP
        return 0  # Thumb
    elif idx <= 8:  # INDEX_FINGER_TIP
        return 1  # Index
    elif idx <= 12:  # MIDDLE_FINGER_TIP
        return 2  # Middle
    elif idx <= 16:  # RING_FINGER_TIP
        return 3  # Ring
    else:
        return 4  # Pinky


def get_hand_colors(is_left_hand):
    if is_left_hand:
        return [
            (255, 0, 0),  # Thumb (Blue)
            (0, 255, 0),  # Index (Green)
            (0, 255, 255),  # Middle (Yellow)
            (0, 128, 255),  # Ring (Orange)
            (0, 0, 255),  # Pinky (Red)
        ]
    else:
        return [
            (255, 0, 255),  # Thumb (Magenta)
            (255, 0, 128),  # Index (Pink)
            (128, 0, 255),  # Middle (Purple)
            (255, 128, 0),  # Ring (Light Blue)
            (128, 255, 0),  # Pinky (Lime)
        ]
