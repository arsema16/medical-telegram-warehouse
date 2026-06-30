#!/usr/bin/env python3
"""
Run YOLO object detection on all images.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.yolo_detect import main

if __name__ == "__main__":
    main()