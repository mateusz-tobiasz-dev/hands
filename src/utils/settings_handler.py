import json
import os

DEFAULT_SETTINGS = {
    "Resolution": {
        "camera_width": 640,
        "camera_height": 640
    },
    "Trailing": {
        "trail_length": 10,
        "landmark_size": 2,
        "alpha": 0.6,
        "black_background": False
    }
}

class SettingsHandler:
    def __init__(self):
        self.settings_file = "settings.json"
        self.settings = self.load_settings()
        if self.settings is None:
            self.settings = DEFAULT_SETTINGS.copy()
            self.save_settings()
        self.validate_settings()

    def validate_settings(self):
        # Ensure all required settings groups exist
        for group in DEFAULT_SETTINGS:
            if group not in self.settings:
                self.settings[group] = DEFAULT_SETTINGS[group].copy()
            else:
                # Ensure all keys in each group exist
                for key in DEFAULT_SETTINGS[group]:
                    if key not in self.settings[group]:
                        self.settings[group][key] = DEFAULT_SETTINGS[group][key]
        
        # Validate resolution values
        camera_width = self.settings["Resolution"]["camera_width"]
        camera_height = self.settings["Resolution"]["camera_height"]
        
        if not self.is_valid_resolution(camera_width, camera_height):
            self.settings["Resolution"]["camera_width"] = DEFAULT_SETTINGS["Resolution"]["camera_width"]
            self.settings["Resolution"]["camera_height"] = DEFAULT_SETTINGS["Resolution"]["camera_height"]
        
        # Validate trailing values
        trail_length = self.settings["Trailing"]["trail_length"]
        landmark_size = self.settings["Trailing"]["landmark_size"]
        alpha = self.settings["Trailing"]["alpha"]
        black_background = self.settings["Trailing"]["black_background"]
        
        if not self.is_valid_trailing(trail_length, landmark_size, alpha, black_background):
            self.settings["Trailing"] = DEFAULT_SETTINGS["Trailing"].copy()
        
        # Save validated settings
        self.save_settings()

    def is_valid_resolution(self, width, height):
        if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
            return False
        
        if width < 320 or width > 1920 or height < 240 or height > 1080:
            return False
        
        # Allow 1:1 ratio along with 16:9 and 4:3
        aspect_ratio = width / height if height != 0 else 0
        return (1.7 <= aspect_ratio <= 1.8) or (1.3 <= aspect_ratio <= 1.4) or (0.95 <= aspect_ratio <= 1.05)

    def is_valid_trailing(self, trail_length, landmark_size, alpha, black_background):
        if not isinstance(trail_length, (int, float)) or not isinstance(landmark_size, (int, float)) or not isinstance(alpha, (int, float)) or not isinstance(black_background, bool):
            return False
        
        if trail_length < 1 or trail_length > 100 or landmark_size < 1 or landmark_size > 10 or alpha < 0 or alpha > 1:
            return False
        
        return True

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            return DEFAULT_SETTINGS.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return DEFAULT_SETTINGS.copy()

    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get_setting(self, group, key, default=None):
        try:
            return self.settings[group][key]
        except (KeyError, TypeError):
            if default is not None:
                return default
            return DEFAULT_SETTINGS[group][key]

    def set_setting(self, group, key, value):
        if group not in self.settings:
            self.settings[group] = {}
        self.settings[group][key] = value
