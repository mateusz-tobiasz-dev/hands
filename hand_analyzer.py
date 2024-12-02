import cv2
import numpy as np
import mediapipe as mp
from hand_classes import Hands
from scipy.spatial import ConvexHull
from hand_landmarks import LANDMARK_DICT


class HandAnalyzer:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        # Configure MediaPipe Hands for better performance with higher resolutions
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1  # Use more complex model for better accuracy
        )
        self.hands_data = Hands()
        self.prev_landmarks = {"left": None, "right": None}
        self.prev_time = None
        self.start_times = {"left": None, "right": None}
        self.last_positions = {"left": None, "right": None}
        self.last_directions = {"left": None, "right": None}
        self.previous_hand_centers = {"left": None, "right": None}
        self.stats = {"left": self.init_hand_stats(), "right": self.init_hand_stats()}

    def init_hand_stats(self):
        return {
            "speed": 0,
            "distance": 0,
            "direction_changes": 0,
            "duration": 0,
            "bbox_size": 0,
            "confidence": 0,
            "convex_hull_area": 0,
            "movement_label": "unknown",
            "relative_distances": {"thumb_index": 0},
            "joint_angles": {"thumb_index_middle": 0},
            "velocity": 0,
            "movement_direction": "unknown",
        }

    def analyze_frame(self, frame, frame_idx):
        # Resize frame if it's too large for better performance
        h, w = frame.shape[:2]
        if max(h, w) > 1280:
            scale = 1280 / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h))
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        frame_data = {"frame": frame_idx}
        current_time = frame_idx / 30  # Assuming 30 fps

        # Initialize landmark data with default values
        landmark_data = self.get_default_landmark_data()

        if results.multi_hand_landmarks:
            self.hands_data.update_landmarks(
                results.multi_hand_landmarks, results.multi_handedness
            )
            landmark_data.update(self.get_landmark_data())

            for hand in ["left", "right"]:
                hand_obj = (
                    self.hands_data.left_hand
                    if hand == "left"
                    else self.hands_data.right_hand
                )
                landmarks = hand_obj.landmarks
                if landmarks:
                    self.update_hand_stats(hand, landmarks, current_time)
                else:
                    self.reset_hand_stats(hand)
                self.update_frame_data(frame_data, hand)

            # Correct mirroring
            frame_data = self.correct_mirroring(frame_data)
            landmark_data = self.correct_mirroring(landmark_data)
        else:
            for hand in ["left", "right"]:
                self.reset_hand_stats(hand)
                self.update_frame_data(frame_data, hand)

        frame_data.update(landmark_data)
        self.prev_time = current_time
        return frame_data

    def get_default_landmark_data(self):
        landmark_data = {}
        for hand in ["left", "right"]:
            for label in LANDMARK_DICT.values():
                landmark_data[f"{hand}_{label}_x"] = 0.0
                landmark_data[f"{hand}_{label}_y"] = 0.0
                landmark_data[f"{hand}_{label}_z"] = 0.0
        return landmark_data

    def get_landmark_data(self):
        landmark_data = {}
        for hand in ["left", "right"]:
            hand_obj = (
                self.hands_data.left_hand
                if hand == "left"
                else self.hands_data.right_hand
            )
            if hand_obj.landmarks:
                for label, coords in hand_obj.landmarks.items():
                    landmark_data[f"{hand}_{label}_x"] = coords[0]
                    landmark_data[f"{hand}_{label}_y"] = coords[1]
                    landmark_data[f"{hand}_{label}_z"] = coords[2]
            else:
                for label in LANDMARK_DICT.values():
                    landmark_data[f"{hand}_{label}_x"] = 0.0
                    landmark_data[f"{hand}_{label}_y"] = 0.0
                    landmark_data[f"{hand}_{label}_z"] = 0.0
        return landmark_data

    def update_hand_stats(self, hand, landmarks, current_time):
        wrist = landmarks["WRIST"]
        self.update_duration(hand, current_time)
        self.update_distance_and_speed(hand, wrist)
        self.update_direction_changes(hand, wrist)
        self.update_bbox_size(hand, landmarks)
        self.update_confidence(hand)
        self.update_convex_hull(hand, landmarks)
        self.update_relative_distances(hand, landmarks)
        self.update_joint_angles(hand, landmarks)
        self.update_velocity(hand, wrist)
        self.update_movement_label(hand)
        self.update_movement_direction(hand, wrist)

        self.last_positions[hand] = (wrist[0], wrist[1])
        self.last_directions[hand] = self.calculate_direction(hand, wrist)

    def update_movement_direction(self, hand, wrist):
        hand_center = np.array([wrist[0], wrist[1]])

        if self.previous_hand_centers[hand] is None:
            self.previous_hand_centers[hand] = hand_center
            self.stats[hand]["movement_direction"] = "Not moving"
            return

        dx = hand_center[0] - self.previous_hand_centers[hand][0]
        dy = hand_center[1] - self.previous_hand_centers[hand][1]

        threshold = 0.01  # Adjust this value to change sensitivity

        if abs(dx) < threshold and abs(dy) < threshold:
            direction = "Not moving"
        else:
            angle = np.arctan2(dy, dx) * 180 / np.pi
            if -22.5 <= angle < 22.5:
                direction = "Right"
            elif 22.5 <= angle < 67.5:
                direction = "Down-Right"
            elif 67.5 <= angle < 112.5:
                direction = "Down"
            elif 112.5 <= angle < 157.5:
                direction = "Down-Left"
            elif 157.5 <= angle <= 180 or -180 <= angle < -157.5:
                direction = "Left"
            elif -157.5 <= angle < -112.5:
                direction = "Up-Left"
            elif -112.5 <= angle < -67.5:
                direction = "Up"
            else:  # -67.5 <= angle < -22.5
                direction = "Up-Right"

        self.stats[hand]["movement_direction"] = direction
        self.previous_hand_centers[hand] = hand_center

    def update_relative_distances(self, hand, landmarks):
        self.stats[hand]["relative_distances"]["thumb_index"] = np.linalg.norm(
            np.array(landmarks["THUMB_TIP"]) - np.array(landmarks["INDEX_FINGER_TIP"])
        )

    def update_joint_angles(self, hand, landmarks):
        self.stats[hand]["joint_angles"]["thumb_index_middle"] = self.calculate_angle(
            landmarks["THUMB_TIP"],
            landmarks["INDEX_FINGER_TIP"],
            landmarks["MIDDLE_FINGER_TIP"],
        )

    def update_velocity(self, hand, wrist):
        if self.last_positions[hand] is not None:
            dx = wrist[0] - self.last_positions[hand][0]
            dy = wrist[1] - self.last_positions[hand][1]
            self.stats[hand]["velocity"] = np.sqrt(dx**2 + dy**2) / (
                1 / 30
            )  # Assuming 30 fps

    def update_convex_hull(self, hand, landmarks):
        try:
            points = np.array(list(landmarks.values()))[:, :2]
            hull = ConvexHull(points)
            self.stats[hand]["convex_hull_area"] = hull.area
        except Exception as e:
            print(f"Error calculating convex hull: {e}")
            self.stats[hand]["convex_hull_area"] = 0

    def update_movement_label(self, hand):
        if self.stats[hand]["velocity"] > 0.1:
            self.stats[hand]["movement_label"] = "fast"
        elif self.stats[hand]["velocity"] > 0.05:
            self.stats[hand]["movement_label"] = "medium"
        else:
            self.stats[hand]["movement_label"] = "slow"

    def calculate_angle(self, point1, point2, point3):
        vector1 = np.array(point1[:2]) - np.array(point2[:2])
        vector2 = np.array(point3[:2]) - np.array(point2[:2])
        angle = np.arctan2(np.cross(vector1, vector2), np.dot(vector1, vector2))
        return np.degrees(angle)

    def update_frame_data(self, frame_data, hand):
        frame_data[f"{hand}_speed"] = self.stats[hand]["speed"]
        frame_data[f"{hand}_distance"] = self.stats[hand]["distance"]
        frame_data[f"{hand}_direction_changes"] = self.stats[hand]["direction_changes"]
        frame_data[f"{hand}_duration"] = self.stats[hand]["duration"]
        frame_data[f"{hand}_bounding_box_size"] = self.stats[hand]["bbox_size"]
        frame_data[f"{hand}_confidence"] = self.stats[hand]["confidence"]
        frame_data[f"{hand}_convex_hull_area"] = self.stats[hand]["convex_hull_area"]
        frame_data[f"{hand}_movement_label"] = self.stats[hand]["movement_label"]
        frame_data[f"{hand}_velocity"] = self.stats[hand]["velocity"]
        frame_data[f"{hand}_thumb_index_distance"] = self.stats[hand][
            "relative_distances"
        ]["thumb_index"]
        frame_data[f"{hand}_thumb_index_middle_angle"] = self.stats[hand][
            "joint_angles"
        ]["thumb_index_middle"]
        frame_data[f"{hand}_movement_direction"] = self.stats[hand][
            "movement_direction"
        ]

    def reset_hand_stats(self, hand):
        self.stats[hand] = self.init_hand_stats()
        self.last_positions[hand] = None
        self.last_directions[hand] = None
        self.start_times[hand] = None
        self.previous_hand_centers[hand] = None

    def update_duration(self, hand, current_time):
        if self.start_times[hand] is None:
            self.start_times[hand] = current_time
        self.stats[hand]["duration"] = current_time - self.start_times[hand]

    def update_distance_and_speed(self, hand, wrist):
        if self.last_positions[hand] is not None:
            distance = np.linalg.norm(
                np.array([wrist[0], wrist[1]]) - np.array(self.last_positions[hand])
            )
            self.stats[hand]["distance"] += distance
            self.stats[hand]["speed"] = (
                self.stats[hand]["distance"] / self.stats[hand]["duration"]
                if self.stats[hand]["duration"] > 0
                else 0
            )

    def update_direction_changes(self, hand, wrist):
        current_direction = self.calculate_direction(hand, wrist)
        if self.last_directions[hand] is not None and current_direction is not None:
            angle_diff = abs(current_direction - self.last_directions[hand])
            if angle_diff > np.pi / 4:
                self.stats[hand]["direction_changes"] += 1

    def calculate_direction(self, hand, wrist):
        if self.last_positions[hand] is not None:
            dx = wrist[0] - self.last_positions[hand][0]
            dy = wrist[1] - self.last_positions[hand][1]
            return np.arctan2(dy, dx)
        return None

    def update_bbox_size(self, hand, landmarks):
        x_coords = [lm[0] for lm in landmarks.values()]
        y_coords = [lm[1] for lm in landmarks.values()]
        bbox_width = max(x_coords) - min(x_coords)
        bbox_height = max(y_coords) - min(y_coords)
        self.stats[hand]["bbox_size"] = bbox_width * bbox_height

    def update_confidence(self, hand):
        # Assuming confidence is not available in the current implementation
        self.stats[hand]["confidence"] = 1.0

    def correct_mirroring(self, data):
        corrected_data = {}
        for key, value in data.items():
            if key.startswith("left_"):
                corrected_data["right_" + key[5:]] = value
            elif key.startswith("right_"):
                corrected_data["left_" + key[6:]] = value
            else:
                corrected_data[key] = value
        return corrected_data

    def analyze_frames(self, frames):
        analyzed_data = []
        for frame_idx, frame in enumerate(frames):
            frame_data = self.analyze_frame(frame, frame_idx)
            analyzed_data.append(frame_data)
        return analyzed_data
