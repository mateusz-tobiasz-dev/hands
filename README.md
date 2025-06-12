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
<br><em>Trailing effect visualization (GIF preview)</em>
</td>
<td width="40%">

**Key Features:**
- Motion path tracking
- Customizable trail length
- Adjustable opacity
- Color-coded fingers

[▶ Watch Full Demo (MP4)](docs/demos/trailing/demo.mp4)
</td>
</tr>
</table>

#### Heatmap Generation
<table>
<tr>
<td width="60%">
<img src="docs/demos/heatmap/demo.gif" alt="Heatmap Demo">
<br><em>Heatmap visualization (GIF preview)</em>
</td>
<td width="40%">

**Key Features:**
- Movement intensity mapping
- Multiple color schemes
- Adjustable radius
- Blur control

[▶ Watch Full Demo (MP4)](docs/demos/heatmap/demo.mp4)
</td>
</tr>
</table>

#### Real-time Analysis
<table>
<tr>
<td width="60%">
<img src="docs/demos/realtime/demo.gif" alt="Real-time Analysis Demo">
<br><em>Real-time hand tracking (GIF preview)</em>
</td>
<td width="40%">

**Key Features:**
- Live hand detection
- Multiple hand tracking
- Instant visualization
- Performance metrics

[▶ Watch Full Demo (MP4)](docs/demos/realtime/demo.mp4)
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

- **User-friendly Interface**
  - Intuitive controls
  - Real-time preview
  - Customizable settings
  - Progress tracking

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

For detailed instructions, see [Installation Guide](INSTALL.md)

## Documentation

- [Technical Documentation](TECHNICAL.md) - Detailed project structure and implementation details
- [Installation Guide](INSTALL.md) - Setup instructions and usage examples

## Project Structure

```
hands/
├── src/
│   ├── core/          # Core application logic
│   ├── data/          # Data processing and storage (git-ignored)
│   ├── gui/           # User interface components
│   ├── managers/      # System management modules
│   └── utils/         # Utility functions
└── docs/              # Documentation resources
    ├── screenshots/   # Interface and feature screenshots
    │   ├── main_interface.png
    │   ├── second_tab_interface.png
    │   ├── trailing_demo.png
    │   ├── heatmap_demo.png
    │   ├── real_time_demo.png
    │   └── real_time_demo_v2.png
    └── demos/         # Feature demonstration videos
        ├── trailing/  # Trailing effect demos
        │   ├── demo.mp4
        │   └── demo.gif
        ├── heatmap/   # Heatmap visualization demos
        │   ├── demo.mp4
        │   └── demo.gif
        └── realtime/  # Real-time analysis demos
            ├── demo.mp4
            └── demo.gif
```

See [Technical Documentation](TECHNICAL.md) for detailed structure.

## Requirements

- Python 3.8+
- OpenCV with contrib modules
- PyQt5
- Other dependencies listed in requirements.txt

## Acknowledgments

- MediaPipe for hand tracking technology
- OpenCV community for computer vision tools
- PyQt team for GUI framework
