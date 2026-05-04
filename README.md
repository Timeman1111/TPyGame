# 🎮 TPyGame

A high-performance, pixel-level terminal rendering library for Python. Display images and videos in your terminal with up to double the resolution of standard terminal rendering.

## ✨ Features

- **Double Terminal Resolution** - Render content at 2x terminal height for higher quality visuals
- **Fast & Efficient** - Optimized frame buffering and pixel-level rendering
- **Video Playback** - Play video files or live camera feeds in the terminal
- **Easy to Use** - Simple, intuitive API for rendering images and videos
- **Parallel Processing** - Optional multi-threaded/multi-process rendering for performance
- **Bitrate Control** - Manage rendering performance with configurable update rates

## 📋 Requirements

- **Python** >= 3.14
- **NumPy** >= 2.4.4
- **OpenCV (opencv-python)** >= 4.13.0.92

## 🚀 Quick Start

### Installation

```bash
pip install tpygame
```

### Basic Usage

Create a screen and render an image:

```python
import tpygame as tpy
import cv2

# Initialize the terminal screen
screen = tpy.render.screen.Screen()

# Load an image
image = cv2.imread("path/to/image.jpg")

# Create a video/image surface
video = tpy.render.video.Video(
    x=0, y=0,
    width=100,
    height=50,
    source="path/to/video.mp4"
)

# Render frames
while video.next_frame():
    video.draw(screen)
    video.refresh(screen)
```

### Playing Videos

Display video files or camera feeds:

```python
import tpygame as tpy

screen = tpy.render.screen.Screen()

# Play a video file
video = tpy.render.video.Video(
    source="video.mp4",
    bitrate=99999999  # pixels per frame to update
)

while video.next_frame():
    video.draw(screen)
    video.refresh(screen)
```

### Auto-Resizing

Automatically adjust rendering to terminal dimensions:

```python
video = tpy.render.video.Video(
    source="video.mp4",
    auto_resize=True  # Resizes to match terminal
)
```

## 📦 Project Structure

```
TPyGame/
├── pyproject.toml
├── README.md
├── src/
│   └── tpygame/
│       ├── __init__.py
│       ├── file/
│       │   ├── fm.py          # FileManager I/O, directory, asset, and logger helpers
│       │   └── whitelist.py   # Normalized path whitelist checks
│       └── render/
│           ├── screen.py      # Terminal screen management and rendering
│           ├── frame.py       # Frame buffering
│           ├── image.py       # Image surface rendering
│           ├── video.py       # Video playback and processing
│           ├── parallel.py    # Parallel processing configuration
│           └── term_utils.py  # Terminal utility functions
├── tests/
│   ├── test_file/
│   └── test_render/
└── scripts/
    ├── fileio/
    ├── graphics/
    └── test_files/
```

## 🗂️ File Utilities

The `tpygame.file.FileManager` helper includes safe wrappers for:

- text/bytes read and write
- JSON save/load
- directory creation/list/delete
- extension block/unblock policy
- session cleanup for created files
- asset directory loading helpers
- file-backed loggers for terminal-safe debug output

## 💡 Examples

Several example scripts are included:

- **`bouncing_circles.py`** - Renders animated bouncing circles
- **`random_video_player.py`** - Play videos with automatic download
- **`resizable_video_player.py`** - Handle terminal resizing during playback
- **`profile_video.py`** - Performance profiling utilities

## 🔧 Advanced Features

### Parallel Processing

Enable multi-threaded rendering for better performance:

```python
from tpygame.render.parallel import ParallelConfig

screen = tpy.render.screen.Screen(
    parallel=ParallelConfig(enabled=True)
)
```

### Bitrate Control

Manage rendering performance by limiting pixels updated per frame:

```python
video = tpy.render.video.Video(
    source="video.mp4",
    bitrate=50000  # Update max 50k pixels per frame
)
```

## 📝 License

MIT

## 🔗 Links

- [GitHub Repository](https://github.com/Timeman1111/TPyGame)
