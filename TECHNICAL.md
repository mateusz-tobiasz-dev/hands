# Technical Documentation

## Project Structure
```
hands/
├── src/
│   ├── core/
│   │   ├── hand_landmarks.py      # Hand tracking point definitions
│   │   └── hand_tracking_app.py   # Main application class
│   ├── data/                      # Data processing and storage (git-ignored)
│   │   ├── raw_movie/            # Original video recordings
│   │   ├── csv_data/             # Analysis data in CSV format
│   │   ├── trailed_movie/        # Generated trailing videos
│   │   └── heatmap_movie/        # Generated heatmap visualization
│   ├── gui/
│   │   ├── camera_viewer_gui.py  # Main GUI implementation
│   │   └── slider.py             # Custom slider widget
│   ├── managers/
│   │   ├── camera_manager.py     # Camera/video input handling
│   │   ├── playback_manager.py   # Video playback control
│   │   ├── visualization_manager.py # Visualization generation
│   │   └── settings_handler.py   # Settings management
│   └── utils/
│       ├── drawing_utils.py      # Drawing helper functions
│       └── settings_handler.py   # Settings utilities
├── docs/                         # Documentation resources
│   ├── screenshots/              # Interface and feature screenshots
│   │   ├── main_interface.png    # Main application view
│   │   ├── second_tab_interface.png # Secondary interface view
│   │   ├── trailing_demo.png     # Trailing effect example
│   │   ├── heatmap_demo.png      # Heatmap visualization example
│   │   ├── real_time_demo.png    # Real-time tracking view
│   │   └── real_time_demo_v2.png # Alternative tracking view
│   └── demos/                    # Feature demonstration videos
│       ├── trailing/             # Trailing effect demos
│       ├── heatmap/              # Heatmap visualization demos
│       └── realtime/             # Real-time analysis demos
├── main.py                      # Application entry point
├── requirements.txt             # Project dependencies
└── settings.json               # Application configuration
```

## Directory Overview

### src/core/
Core application logic and hand tracking functionality.

- **hand_landmarks.py**: Defines landmark points for hand tracking
- **hand_tracking_app.py**: Main application class integrating all components

### src/data/
Data storage directories for processing and analysis. All directories are git-ignored.

- **raw_movie/**: Original video recordings
- **csv_data/**: Analyzed hand tracking data in CSV format
- **trailed_movie/**: Generated trailing visualization videos
- **heatmap_movie/**: Generated heatmap visualization videos

### src/gui/
User interface components and widgets.

#### camera_viewer_gui.py
Main GUI class implementing the application interface.
- Methods:
  - `setup_ui()`: Initializes the main UI components
  - `setup_settings_ui()`: Creates settings panel
  - `update_analyzed_frame()`: Updates original video frame
  - `update_trailed_frame()`: Updates trailing visualization
  - `update_heatmap_frame()`: Updates heatmap visualization
  - Various event handlers for UI controls

#### slider.py
Custom range slider implementation for video frame selection.
- Methods:
  - `setLow()`: Sets lower bound
  - `setHigh()`: Sets upper bound
  - `low()`: Gets lower bound
  - `high()`: Gets upper bound

### src/managers/
Management classes for different application components.

#### camera_manager.py
Handles camera operations and video capture.
- Methods:
  - `get_camera_list()`: Lists available cameras
  - `start_capture()`: Starts video capture
  - `stop_capture()`: Stops video capture
  - `get_frame()`: Retrieves current frame

#### playback_manager.py
Manages video playback and frame handling.
- Methods:
  - `load_video()`: Loads video file
  - `play()`: Starts playback
  - `pause()`: Pauses playback
  - `stop()`: Stops playback
  - `get_frame()`: Gets frame at specific index

#### visualization_manager.py
Handles different visualization types (trailing, heatmap).
- Methods:
  - `generate_trailed_frame()`: Creates trailing visualization
  - `generate_heatmap_frame()`: Creates heatmap visualization

### src/utils/
Utility functions and handlers.

#### drawing_utils.py
Utilities for drawing and color handling.
- Methods:
  - `get_hand_colors()`: Returns color scheme for hand landmarks
  - `get_finger_idx()`: Maps landmark to finger index

#### settings_handler.py
Manages application settings and persistence.
- Methods:
  - `load_settings()`: Loads settings from file
  - `save_settings()`: Saves settings to file
  - `get_setting()`: Retrieves specific setting
  - `set_setting()`: Updates specific setting

### docs/
Documentation resources.

#### screenshots/
Application interface images showing different features and views:
- **main_interface.png**: Main application interface with controls
- **second_tab_interface.png**: Secondary interface with additional settings
- **trailing_demo.png**: Example of trailing effect visualization
- **heatmap_demo.png**: Example of heatmap visualization
- **real_time_demo.png**: Real-time hand tracking demonstration
- **real_time_demo_v2.png**: Alternative view of real-time tracking

#### demos/
Pre-recorded demonstration videos showing application features:
- **trailing/**: Examples of trailing effect in action
- **heatmap/**: Examples of heatmap visualization features
- **realtime/**: Demonstrations of real-time analysis capabilities

Note: The demos directory contains only documentation examples, not user data.

## Main Application Files

### main.py
Application entry point.
- Creates QApplication instance
- Initializes main application window
- Starts event loop

### settings.json
Configuration file storing application settings:
- Resolution settings
- Trailing visualization settings
- Heatmap visualization settings
- View settings

### requirements.txt
Project dependencies and versions. 