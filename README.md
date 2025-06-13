# Hand Movement Analysis and Visualization Tool

A powerful application for analyzing and visualizing hand movements in video recordings. This tool provides real-time hand tracking, movement trail visualization, and heatmap generation capabilities.

## Visual Demonstrations

### Main Interface
![Main Application Interface](docs/screenshots/main_interface.png)
*Main application interface with controls and visualization*

![Second Interface Tab](docs/screenshots/second_tab_interface.png)
*Secondary interface view with additional controls*

### Feature Demonstrations

#### Trailing Effect Visualization
<table>
<tr>
<td width="60%">
<img src="docs/demos/trailing/demo.gif" alt="Trailing Effect Demo">
<br><em>Trailing effect visualization</em>
</td>
<td width="40%">

**Key Features:**
- Motion path tracking
- Customizable trail length
- Adjustable opacity
- Color-coded fingers
</td>
</tr>
</table>

#### Heatmap Generation
<table>
<tr>
<td width="60%">
<img src="docs/demos/heatmap/demo.gif" alt="Heatmap Demo">
<br><em>Heatmap visualization</em>
</td>
<td width="40%">

**Key Features:**
- Movement intensity mapping
- Multiple color schemes
- Adjustable radius
- Blur control
</td>
</tr>
</table>

### Additional Screenshots

<table>
<tr>
<td width="50%">
<img src="docs/screenshots/real_time_demo.png" alt="Real-time Analysis View">
<br><em>Real-time tracking interface</em>
</td>
<td width="50%">
<img src="docs/screenshots/real_time_demo_v2.png" alt="Alternative Analysis View">
<br><em>Alternative tracking view with metrics</em>
</td>
</tr>
</table>

## Features

- **Real-time Hand Tracking**
  - Accurate hand landmark detection
  - Support for multiple hands
  - Live camera preview

- **Movement Visualization**
  - Trailing effect with customizable parameters
  - Heatmap generation with various color schemes
  - Adjustable opacity and blending options

- **Video Management**
  - Record from camera
  - Import existing videos
  - Export full or partial visualizations
  - Save analysis data in CSV format
  - Partial video/data export with frame range selection

- **User-friendly Interface**
  - Intuitive controls with state-aware buttons
  - Real-time preview
  - Customizable settings with persistent storage
  - Progress tracking for long operations
  - Frame range selection for partial exports

- **Settings Management**
  - Persistent settings storage
  - Resolution presets for recording and saving
  - Customizable visualization parameters
  - Separate settings for different visualization modes

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

## Documentation

- [Technical Documentation](TECHNICAL.md) - Detailed project structure and implementation details
- [Installation Guide](INSTALL.md) - Setup instructions and usage examples

## Project Structure

```
hands/
├── src/
│   ├── core/          # Core application logic
│   ├── data/          # Data processing and storage (git-ignored)
│   │   ├── raw_movie/         # Original video recordings
│   │   ├── csv_data/          # Analysis data in CSV format
│   │   ├── trailed_movie/     # Generated trailing videos
│   │   ├── heatmap_movie/     # Generated heatmap visualization
│   │   ├── partial_movie/     # Partial video exports
│   │   ├── partial_trailing/  # Partial trailing exports
│   │   ├── partial_heatmap/   # Partial heatmap exports
│   │   └── partial_csv/       # Partial CSV exports
│   ├── gui/           # User interface components
│   ├── managers/      # System management modules
│   │   ├── camera_manager.py     # Camera/video input handling
│   │   ├── playback_manager.py   # Video playback control
│   │   ├── visualization_manager.py # Visualization generation
│   │   └── settings_handler.py   # Settings management
│   └── utils/         # Utility functions
└── docs/              # Documentation resources
    ├── screenshots/   # Interface and feature screenshots
    └── demos/         # Feature demonstration videos
```

## Requirements

- Python 3.8+
- OpenCV with contrib modules
- PyQt5
- Other dependencies listed in requirements.txt

## Acknowledgments

- MediaPipe for hand tracking technology
- OpenCV community for computer vision tools
- PyQt team for GUI framework
