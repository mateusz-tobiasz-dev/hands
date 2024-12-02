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

    # Collect all unique keys from all data items
    all_keys = set()
    for item in data:
        all_keys.update(item.keys())

    fieldnames = ["frame"] + sorted(list(all_keys - {"frame"}))

    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            # Use a dictionary comprehension to ensure all fields are present
            row_data = {field: row.get(field, None) for field in fieldnames}
            writer.writerow(row_data)

    log_callback(f"Data saved to {filename}")


def save_raw_movie(frames, output_path, fps=30, width=None, height=None):
    """
    Save frames as a movie file with optional resolution adjustment.
    
    Args:
        frames: List of frames to save
        output_path: Path to save the movie file
        fps: Frames per second (default: 30)
        width: Optional target width for resizing
        height: Optional target height for resizing
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        if not frames:
            return False, "No frames to save"
            
        # Get original dimensions
        orig_h, orig_w = frames[0].shape[:2]
        
        # Use original dimensions if not specified
        if width is None:
            width = orig_w
        if height is None:
            height = orig_h
            
        # Validate dimensions
        if width <= 0 or height <= 0:
            return False, "Invalid resolution specified"
            
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            return False, "Failed to create video writer"
        
        # Process and write frames
        total_frames = len(frames)
        for i, frame in enumerate(frames):
            if frame.shape[:2] != (height, width):
                frame = cv2.resize(frame, (width, height))
            out.write(frame)
            
        out.release()
        
        # Verify file was created and has size
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return False, "Failed to write video file"
            
        return True, f"Successfully saved {total_frames} frames to {output_path}"
        
    except Exception as e:
        return False, f"Error saving video: {str(e)}"


def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] {message}"
