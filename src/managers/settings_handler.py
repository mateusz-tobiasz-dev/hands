import json


class SettingsHandler:
    def __init__(self):
        self.settings_file = "settings.json"
        self.settings = self.load_settings()

    def is_valid_resolution(self, width, height):
        """Validate resolution settings"""
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
                "rainbow",  # Added rainbow as it's in our defaults
            ]
            if color_map not in valid_color_maps:
                print(f"Color map must be one of: {', '.join(valid_color_maps)}")
                return False

            return True
        except Exception as e:
            print(f"Error validating heatmap settings: {e}")
            return False

    def get_default_settings(self):
        """Get default settings"""
        return {
            "Resolution": {
                "camera_width": 1920,
                "camera_height": 1080,
                "selected_resolution": "1920x1080",
            },
            "SaveResolution": {
                "width": 1920,
                "height": 1080,
                "use_original": True,
                "selected_resolution": "1920x1080",
            },
            "Trailing": {
                "trail_length": 50,
                "landmark_size": 6,
                "alpha": 0.8,
                "opacity": 0.3,
                "black_background": True,
                "alpha_fade": True,
            },
            "Heatmap": {
                "intensity": 1.5,
                "blur_size": 5,
                "threshold": 0.15,
                "radius": 5,
                "opacity": 1.0,
                "color_map": "rainbow",
                "blur_amount": 20,
                "black_background": True,
                "accumulate": False,
            },
            "ViewSettings": {
                "original_realtime": True,
                "trailed_realtime": True,
                "heatmap_realtime": True,
            },
        }

    def load_settings(self):
        """Load settings from file or create with defaults if not exists"""
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
                # Update with any missing default settings
                default_settings = self.get_default_settings()
                for section, values in default_settings.items():
                    if section not in settings:
                        settings[section] = values
                    else:
                        for key, value in values.items():
                            if key not in settings[section]:
                                settings[section][key] = value
                return settings
        except FileNotFoundError:
            settings = self.get_default_settings()
            self.save_settings(settings)
            return settings

    def save_settings(self, settings=None):
        """Save settings to file"""
        if settings is None:
            settings = self.settings
        with open(self.settings_file, "w") as f:
            json.dump(settings, f, indent=4)

    def get_setting(self, section, key, default=None):
        """Get a setting value with optional default

        Args:
            section (str): Settings section name
            key (str): Setting key
            default: Default value if setting not found (default: None)

        Returns:
            Setting value or default if not found
        """
        try:
            return self.settings[section][key]
        except KeyError:
            return (
                default
                if default is not None
                else self.get_default_settings().get(section, {}).get(key)
            )

    def set_setting(self, section, key, value):
        """Set a setting value"""
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value
