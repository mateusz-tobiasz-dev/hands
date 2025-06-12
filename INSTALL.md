# Installation and Usage Guide

## Prerequisites
- Python 3.8 or higher
- OpenCV with contrib modules
- PyQt5
- Git (for cloning the repository)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hands.git
cd hands
```

2. Create and activate a virtual environment (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Setup

1. Create required data directories:
```bash
# Create data processing directories (these will be git-ignored)
mkdir -p src/data/{raw_movie,csv_data,trailed_movie,heatmap_movie}
```

2. Ensure settings.json exists (will be created automatically on first run with default values)

## Usage

### Running the Application
```bash
python main.py
```

### Working with Videos

#### Recording New Videos
1. Select camera from the dropdown list
2. Click "Connect" to start camera preview
3. Click "Start Recording" to begin recording
4. Click "Stop Recording" to end recording
- Recorded videos are saved in `src/data/raw_movie/`

#### Analyzing Videos
1. Select a video from the recordings dropdown
2. Click "Analyze" to process the video
- Analysis results are saved in `src/data/csv_data/`

#### Visualization Options

##### Trailing Visualization
Shows hand movement trails with customizable settings:
- Trail Length: Number of previous frames to show
- Landmark Size: Size of trail points
- Alpha: Trail transparency
- Opacity: Background visibility
- Black Background: Toggle dark mode
- Alpha Fade: Gradual trail fade

##### Heatmap Visualization
Shows movement intensity with customizable settings:
- Radius: Size of heat points
- Opacity: Blend with background
- Color Map: Different color schemes
- Blur Amount: Smoothing effect
- Black Background: Toggle dark mode
- Accumulate: Show all points or recent only

### Example Workflow

1. Record or Import Video:
```
Place your MP4 video in src/data/raw_movie/
```

2. Analyze the Video:
- Select video from dropdown
- Click "Analyze"
- Wait for analysis to complete

3. Generate Visualizations:
- Use real-time preview in different tabs
- Adjust settings in right panel
- Generate full videos using "Generate" buttons

Note: All data directories are git-ignored. Your videos and analysis data will be stored locally and not tracked by git.

### Tips
- Keep original videos in src/data/raw_movie folder
- Back up CSV files as they contain analysis data
- Adjust settings in real-time for best results
- All generated data is stored in src/data/ and is git-ignored 