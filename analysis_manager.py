import os
import csv
from hand_analyzer import HandAnalyzer
from utils import save_to_csv

class AnalysisManager:
    def __init__(self):
        self.hand_analyzer = HandAnalyzer()
        self.analyzed_data = []
        
    def analyze_frames(self, frames, progress_callback=None):
        total_frames = len(frames)
        self.analyzed_data = []
        
        for frame_idx, frame in enumerate(frames):
            frame_data = self.hand_analyzer.analyze_frame(frame, frame_idx)
            self.analyzed_data.append(frame_data)
            
            if progress_callback:
                progress = int((frame_idx + 1) / total_frames * 100)
                progress_callback(progress)
                
        return self.analyzed_data
    
    def save_analysis(self, timestamp, logger=None):
        if not self.analyzed_data:
            if logger:
                logger("No data to save")
            return False
            
        os.makedirs("csv_data", exist_ok=True)
        filename = os.path.join("csv_data", f"csv_{timestamp}.csv")
        
        # Collect all unique keys from all data items
        all_keys = set()
        for item in self.analyzed_data:
            all_keys.update(item.keys())
            
        fieldnames = ["frame"] + sorted(list(all_keys - {"frame"}))
        
        with open(filename, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.analyzed_data:
                # Use a dictionary comprehension to ensure all fields are present
                row_data = {field: row.get(field, None) for field in fieldnames}
                writer.writerow(row_data)
                
        if logger:
            logger(f"Data saved to {filename}")
        return True
