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
│   │   ├── heatmap_movie/        # Generated heatmap visualization
│   │   ├── partial_movie/        # Partial video exports
│   │   ├── partial_trailing/     # Partial trailing exports
│   │   ├── partial_heatmap/      # Partial heatmap exports
│   │   └── partial_csv/          # Partial CSV exports
│   ├── gui/
│   │   ├── camera_viewer_gui.py  # Main GUI implementation
│   │   └── slider.py             # Custom slider widget
│   ├── managers/
│   │   ├── camera_manager.py     # Camera/video input handling
│   │   ├── playback_manager.py   # Video playback control
│   │   ├── visualization_manager.py # Visualization generation
│   │   └── settings_handler.py   # Settings management
│   └── utils/
│       └── drawing_utils.py      # Drawing helper functions
├── docs/                         # Documentation resources
│   ├── screenshots/              # Interface and feature screenshots
│   └── demos/                    # Feature demonstration videos
├── main.py                      # Application entry point
├── requirements.txt             # Project dependencies
└── settings.json               # Application configuration
```

## Application States and Button Behavior

### Video Loading States
1. **Initial State**
   - Load button enabled
   - Analyze button disabled
   - Save controls disabled
   - Only Original tab enabled

2. **Raw Video Loaded**
   - Load button enabled (warns if loading new video)
   - Analyze button enabled
   - Basic playback controls enabled
   - Only Original tab and raw video features enabled
   - Can save partial raw video and basic CSV

3. **Analysis Complete**
   - Load button enabled (warns if loading new video)
   - Analyze button enabled
   - All tabs enabled
   - All save features enabled
   - Full visualization controls available

### Recording States
1. **Camera Available**
   - Connect button enabled
   - Record resolution controls enabled
   - Record button disabled

2. **Camera Connected**
   - Record button enabled
   - Resolution can be changed
   - Live preview active

3. **Recording Active**
   - Most controls disabled
   - Stop recording button enabled
   - Live preview with indicators

## Manager Classes

### PlaybackManager
Controls video playback and analysis state.
- Methods:
  - `load_video(path)`: Loads video without analysis
  - `analyze_video(path)`: Loads and analyzes video
  - `is_playback_ready()`: Checks if video is loaded
  - `is_analysis_ready()`: Checks if analysis is complete
  - `get_frame(index)`: Retrieves frame by index
  - `play()`, `pause()`, `stop()`: Playback controls

### SettingsHandler
Manages application settings and persistence.
- Settings Categories:
  - Resolution: Camera and save resolution presets
  - Trailing: Trail length, opacity, colors
  - Heatmap: Radius, blur, colormap
  - SaveResolution: Output video dimensions
- Methods:
  - `load_settings()`: Loads from settings.json
  - `save_settings()`: Persists to settings.json
  - `get_setting(category, name)`: Retrieves setting
  - `set_setting(category, name, value)`: Updates setting
  - `get_default_settings()`: Returns defaults

### VisualizationManager
Handles visualization generation.
- Methods:
  - `generate_trailed_frame()`: Creates trailing effect
    - Uses trail length and opacity settings
    - Supports color-coded fingers
    - Alpha fade option
  - `generate_heatmap_frame()`: Creates heatmap
    - Supports multiple colormaps
    - Adjustable radius and blur
    - Accumulation options

## Data Export Features

### Full Exports
- Complete video analysis
- All frames included
- Settings from visualization panels applied

### Partial Exports
- Frame range selection via slider
- Available in both raw and analyzed modes
- Types:
  1. Raw Video: Just the selected frames
  2. CSV: Frame data or analysis data
  3. Trailing: Visualization with current settings
  4. Heatmap: Visualization with current settings

## Progress Tracking
- Progress bars for long operations
- Shown during:
  1. Video analysis
  2. Full video generation
  3. Partial exports
  4. CSV operations
- Proper cleanup in try/finally blocks

## Settings Management

### Resolution Settings
- Recording presets (4:3, 16:9, 1:1)
- Save resolution options
- Original resolution toggle
- Live preview updates

### Visualization Settings
1. **Trailing Settings**
   - Trail length
   - Landmark size
   - Opacity
   - Background options
   - Alpha fade

2. **Heatmap Settings**
   - Radius
   - Blur amount
   - Color scheme
   - Opacity
   - Background options
   - Accumulation mode

### Settings Persistence
- Automatic saving on changes
- Loaded at startup
- Separate sections in settings.json
- Default fallbacks 