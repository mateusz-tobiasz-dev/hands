import numpy as np
from hand_landmarks import LANDMARK_DICT


class Hand:
    def __init__(self):
        self.landmarks = {name: np.zeros(3) for name in LANDMARK_DICT.values()}
        self.velocity = np.zeros(3)
        self.thumb_index_middle_angle = 0.0
        self.movement_label = ""
        self.bounding_box_size = 0.0
        self.direction_changes = 0
        self.movement_direction = np.zeros(3)
        self.distance = 0.0
        self.thumb_index_distance = 0.0
        self.duration = 0.0
        self.speed = 0.0
        self.convex_hull_area = 0.0
        self.confidence = 0.0

    def update_landmarks(self, landmarks):
        for idx, landmark in enumerate(landmarks):
            name = LANDMARK_DICT[idx]
            self.landmarks[name] = np.array([landmark.x, landmark.y, landmark.z])

    def get_data(self):
        data = {f"{name}": self.landmarks[name] for name in LANDMARK_DICT.values()}
        data.update(
            {
                "velocity": self.velocity,
                "thumb_index_middle_angle": self.thumb_index_middle_angle,
                "movement_label": self.movement_label,
                "bounding_box_size": self.bounding_box_size,
                "direction_changes": self.direction_changes,
                "movement_direction": self.movement_direction,
                "distance": self.distance,
                "thumb_index_distance": self.thumb_index_distance,
                "duration": self.duration,
                "speed": self.speed,
                "convex_hull_area": self.convex_hull_area,
                "confidence": self.confidence,
            }
        )
        return data


class LeftHand(Hand):
    def __init__(self):
        super().__init__()
        self.hand_type = "left"

    def get_data(self):
        return {f"left_{name}": value for name, value in super().get_data().items()}


class RightHand(Hand):
    def __init__(self):
        super().__init__()
        self.hand_type = "right"

    def get_data(self):
        return {f"right_{name}": value for name, value in super().get_data().items()}


class Hands:
    def __init__(self):
        self.left_hand = LeftHand()
        self.right_hand = RightHand()

    def update_landmarks(self, multi_hand_landmarks, multi_handedness):
        for hand_landmarks, handedness in zip(multi_hand_landmarks, multi_handedness):
            if handedness.classification[0].label == "Left":
                self.left_hand.update_landmarks(hand_landmarks.landmark)
            else:
                self.right_hand.update_landmarks(hand_landmarks.landmark)

    def get_data(self):
        return {**self.left_hand.get_data(), **self.right_hand.get_data()}
