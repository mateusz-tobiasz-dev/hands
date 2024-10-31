import os
import csv
import cv2
from datetime import datetime


def save_to_csv(data, log_callback):
    if not data:
        log_callback("No data to save")
        return

    os.makedirs("csv_data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"csv_data/csv_{timestamp}.csv"

    fieldnames = ["frame"] + sorted(list(data[0].keys() - {"frame"}))

    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    log_callback(f"Data saved to {filename}")


def save_raw_movie(frames, log_callback, progress_callback):
    if not frames:
        log_callback("No frames to save as movie")
        return

    os.makedirs("raw_movie", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"raw_movie/raw_movie_{timestamp}.mp4"

    height, width, _ = frames[0].shape
    fps = 30  # Assuming 30 fps, adjust if needed

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

    total_frames = len(frames)

    for i, frame in enumerate(frames):
        out.write(frame)

        if i % 10 == 0:
            progress = int((i + 1) / total_frames * 100)
            progress_callback(progress)

    out.release()
    progress_callback(100)
    log_callback(f"Raw movie saved to {filename}")


def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] {message}"
