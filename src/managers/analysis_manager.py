import os
import csv
from src.core.hand_analyzer import HandAnalyzer
import cv2


class AnalysisManager:
    def __init__(self):
        self.hand_analyzer = HandAnalyzer()

    def analyze_video(self, video_path, progress_callback=None):
        """Analyze video frame by frame and save directly to CSV"""
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Create CSV file
        os.makedirs("src/data/csv_data", exist_ok=True)
        timestamp = os.path.basename(video_path)[10:-4]
        csv_path = os.path.join("src/data/csv_data", f"csv_{timestamp}.csv")

        with open(csv_path, mode="w", newline="") as csvfile:
            writer = None  # Will be initialized after first frame

            for frame_idx in range(total_frames):
                # Read and analyze single frame
                ret, frame = cap.read()
                if not ret:
                    break

                frame_data = self.hand_analyzer.analyze_frame(frame, frame_idx)

                # Initialize writer with fields from first frame
                if writer is None and frame_data:
                    fieldnames = ["frame"] + sorted(
                        [k for k in frame_data.keys() if k != "frame"]
                    )
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                # Write frame data immediately
                if writer is not None:
                    writer.writerow(frame_data)

                # Update progress
                if progress_callback:
                    progress = int((frame_idx + 1) / total_frames * 100)
                    progress_callback(progress)

                # Clear frame from memory
                frame = None

        cap.release()
        return csv_path
