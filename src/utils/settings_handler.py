import json
import os

DEFAULT_SETTINGS = {
    "Resolution": {"camera_width": 640, "camera_height": 640},
    "Trailing": {
        "trail_length": 10,
        "landmark_size": 2,
        "alpha": 0.6,
        "opacity": 0.6,
        "black_background": False,
        "alpha_fade": True,
    },
    "Heatmap": {
        "radius": 30,
        "opacity": 0.6,
        "color_map": "jet",
        "blur_amount": 15,
        "black_background": False,
        "accumulate": True,
    },
    "ViewSettings": {
        "original_realtime": True,
        "trailed_realtime": True,
        "heatmap_realtime": True,
    },
}


class SettingsHandler:
    def __init__(self):
        self.settings_file = "settings.json"
        self.settings = self.load_settings()
        if self.settings is None:
            # Only use defaults if no settings file exists
            self.settings = DEFAULT_SETTINGS.copy()
            self.save_settings()
        else:
            # Validate and only add missing settings
            self.validate_settings()

    def validate_settings(self):
        """Ensure all required settings exist, only add missing ones"""
        # Add any missing top-level groups
        for group in DEFAULT_SETTINGS:
            if group not in self.settings:
                self.settings[group] = DEFAULT_SETTINGS[group].copy()
            else:
                # Only add missing keys in existing groups
                for key in DEFAULT_SETTINGS[group]:
                    if key not in self.settings[group]:
                        self.settings[group][key] = DEFAULT_SETTINGS[group][key]

        # Save if any changes were made
        self.save_settings()

    def is_valid_resolution(self, width, height):
        if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
            return False

        if width < 320 or width > 1920 or height < 240 or height > 1080:
            return False

        # Allow 1:1 ratio along with 16:9 and 4:3
        aspect_ratio = width / height if height != 0 else 0
        return (
            (1.7 <= aspect_ratio <= 1.8)
            or (1.3 <= aspect_ratio <= 1.4)
            or (0.95 <= aspect_ratio <= 1.05)
        )

    def is_valid_trailing(
        self, trail_length, landmark_size, alpha, opacity, black_background, alpha_fade
    ):
        """Validate trailing settings"""
        try:
            # Type checks
            if not isinstance(trail_length, (int, float)):
                print("Trail length must be a number")
                return False
            if not isinstance(landmark_size, (int, float)):
                print("Landmark size must be a number")
                return False
            if not isinstance(alpha, (int, float)):
                print("Alpha must be a number")
                return False
            if not isinstance(opacity, (int, float)):
                print("Opacity must be a number")
                return False
            if not isinstance(black_background, bool):
                print("Black background must be a boolean")
                return False
            if not isinstance(alpha_fade, bool):
                print("Alpha fade must be a boolean")
                return False

            # Range checks
            if not (1 <= trail_length <= 100):
                print("Trail length must be between 1 and 100")
                return False
            if not (1 <= landmark_size <= 10):
                print("Landmark size must be between 1 and 10")
                return False
            if not (0.1 <= alpha <= 1.0):
                print("Alpha must be between 0.1 and 1.0")
                return False

            return True
        except Exception as e:
            print(f"Error validating trailing settings: {e}")
            return False

    def is_valid_heatmap(
        self, radius, opacity, color_map, blur_amount, black_background, accumulate
    ):
        """Validate heatmap settings"""
        try:
            # Type checks
            if not isinstance(radius, (int, float)):
                print("Radius must be a number")
                return False
            if not isinstance(opacity, (int, float)):
                print("Opacity must be a number")
                return False
            if not isinstance(color_map, str):
                print("Color map must be a string")
                return False
            if not isinstance(blur_amount, (int, float)):
                print("Blur amount must be a number")
                return False
            if not isinstance(black_background, bool):
                print("Black background must be a boolean")
                return False
            if not isinstance(accumulate, bool):
                print("Accumulate must be a boolean")
                return False

            # Range checks
            if not (1 <= radius <= 100):
                print("Radius must be between 1 and 100")
                return False
            if not (0.1 <= opacity <= 1.0):
                print("Opacity must be between 0.1 and 1.0")
                return False
            if not (1 <= blur_amount <= 50):
                print("Blur amount must be between 1 and 50")
                return False

            # Valid color maps
            valid_color_maps = [
                "jet",
                "hot",
                "cool",
                "spring",
                "summer",
                "autumn",
                "winter",
                "bone",
                "copper",
                "gray",
            ]
            if color_map not in valid_color_maps:
                print(f"Color map must be one of: {', '.join(valid_color_maps)}")
                return False

            return True
        except Exception as e:
            print(f"Error validating heatmap settings: {e}")
            return False

    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
        return None

    def save_settings(self):
        """Save current settings to file"""
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_setting(self, group, key):
        """Get a setting value, return None if not found"""
        try:
            return self.settings[group][key]
        except KeyError:
            return None

    def set_setting(self, group, key, value):
        """Set a setting value"""
        if group not in self.settings:
            self.settings[group] = {}
        self.settings[group][key] = value
