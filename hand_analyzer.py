import cv2
import numpy as np
import mediapipe as mp
from hand_classes import Hands
from scipy.spatial import ConvexHull


class HandAnalyzer:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands()
        self.hands_data = Hands()
        self.prev_landmarks = {"left": None, "right": None}
        self.prev_time = None

    def calculate_velocity(self, current_landmarks, prev_landmarks, dt):
        if prev_landmarks is None:
            return np.zeros(3)
        return (current_landmarks["WRIST"] - prev_landmarks["WRIST"]) / dt

    def calculate_thumb_index_middle_angle(self, landmarks):
        thumb_tip = landmarks["THUMB_TIP"]
        index_tip = landmarks["INDEX_FINGER_TIP"]
        middle_tip = landmarks["MIDDLE_FINGER_TIP"]
        v1 = thumb_tip - index_tip
        v2 = middle_tip - index_tip
        return np.degrees(
            np.arccos(
                np.clip(
                    np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)),
                    -1.0,
                    1.0,
                )
            )
        )

    def calculate_bounding_box_size(self, landmarks):
        points = np.array(list(landmarks.values()))
        min_coords = np.min(points, axis=0)
        max_coords = np.max(points, axis=0)
        return np.linalg.norm(max_coords - min_coords)

    def calculate_movement_direction(self, current_landmarks, prev_landmarks):
        if prev_landmarks is None:
            return np.zeros(3)
        return current_landmarks["WRIST"] - prev_landmarks["WRIST"]

    def calculate_thumb_index_distance(self, landmarks):
        return np.linalg.norm(landmarks["THUMB_TIP"] - landmarks["INDEX_FINGER_TIP"])

    def calculate_convex_hull_area(self, landmarks):
        try:
            points = np.array([landmark[:2] for landmark in landmarks.values()])
            unique_points = np.unique(points, axis=0)
            if len(unique_points) < 3:
                return 0.0
            hull = ConvexHull(unique_points)
            return hull.area
        except Exception as e:
            print(f"Error calculating convex hull: {e}")
            return 0.0

    def analyze_frame(self, frame, frame_idx):
        results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        frame_data = {"frame": frame_idx}
        current_time = frame_idx / 30  # Assuming 30 fps

        if results.multi_hand_landmarks:
            self.hands_data.update_landmarks(
                results.multi_hand_landmarks, results.multi_handedness
            )
            frame_data.update(self.hands_data.get_data())

            for hand in ["left", "right"]:
                hand_obj = (
                    self.hands_data.left_hand
                    if hand == "left"
                    else self.hands_data.right_hand
                )
                landmarks = hand_obj.landmarks

                dt = current_time - self.prev_time if self.prev_time is not None else 0
                velocity = self.calculate_velocity(
                    landmarks, self.prev_landmarks[hand], dt
                )
                thumb_index_middle_angle = self.calculate_thumb_index_middle_angle(
                    landmarks
                )
                bounding_box_size = self.calculate_bounding_box_size(landmarks)
                movement_direction = self.calculate_movement_direction(
                    landmarks, self.prev_landmarks[hand]
                )
                thumb_index_distance = self.calculate_thumb_index_distance(landmarks)
                convex_hull_area = self.calculate_convex_hull_area(landmarks)

                frame_data.update(
                    {
                        f"{hand}_velocity": velocity,
                        f"{hand}_thumb_index_middle_angle": thumb_index_middle_angle,
                        f"{hand}_bounding_box_size": bounding_box_size,
                        f"{hand}_movement_direction": movement_direction,
                        f"{hand}_thumb_index_distance": thumb_index_distance,
                        f"{hand}_convex_hull_area": convex_hull_area,
                        f"{hand}_movement_label": "",  # Placeholder for movement_label
                        f"{hand}_direction_changes": 0,  # Placeholder for direction_changes
                        f"{hand}_distance": 0.0,  # Placeholder for distance
                        f"{hand}_duration": dt,
                        f"{hand}_speed": np.linalg.norm(velocity),
                        f"{hand}_confidence": results.multi_handedness[0]
                        .classification[0]
                        .score
                        if results.multi_handedness
                        else 0.0,
                    }
                )

                self.prev_landmarks[hand] = landmarks.copy()

            self.prev_time = current_time

            # Flip hand tags to correct mirroring
            flipped_data = {}
            for key, value in frame_data.items():
                if key.startswith("left_"):
                    flipped_data["right_" + key[5:]] = value
                elif key.startswith("right_"):
                    flipped_data["left_" + key[6:]] = value
                else:
                    flipped_data[key] = value
            frame_data = flipped_data
        else:
            # Add zeros for frames without hand detection
            for hand in ["left", "right"]:
                for landmark in self.hands_data.left_hand.landmarks.keys():
                    frame_data[f"{hand}_{landmark}"] = np.zeros(3)
                frame_data.update(
                    {
                        f"{hand}_velocity": np.zeros(3),
                        f"{hand}_thumb_index_middle_angle": 0,
                        f"{hand}_bounding_box_size": 0,
                        f"{hand}_movement_direction": np.zeros(3),
                        f"{hand}_thumb_index_distance": 0,
                        f"{hand}_convex_hull_area": 0,
                        f"{hand}_movement_label": "",
                        f"{hand}_direction_changes": 0,
                        f"{hand}_distance": 0.0,
                        f"{hand}_duration": 0.0,
                        f"{hand}_speed": 0.0,
                        f"{hand}_confidence": 0.0,
                    }
                )

        return frame_data

    def analyze_frames(self, frames):
        analyzed_data = []
        for frame_idx, frame in enumerate(frames):
            frame_data = self.analyze_frame(frame, frame_idx)
            analyzed_data.append(frame_data)
        return analyzed_data
