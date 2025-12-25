"""
Shared constants and configuration dictionaries for Golf Yardage Book Extension Suite.

This module centralizes configuration values used across multiple tools to ensure
consistency and provide a single point of update.
"""
from typing import Dict

# Bounding box for hole placement in "top" area (units in inches)
# Matches top_target_box in target_boxes.svg
BOUNDING_BOX_TOP: Dict[str, float] = {
    'x': 0.250,
    'y': 0.250,
    'width': 3.750,
    'height': 6.750,
}

# Target bounding box for scaled greens in "bottom" area (units in inches)
# Matches bottom_target_box in target_boxes.svg
BOUNDING_BOX_BOTTOM: Dict[str, float] = {
    'x': 0.250,
    'y': 7.000,
    'width': 3.750,
    'height': 3.750,
}

# Derived convenience values (calculated from BOUNDING_BOX_TOP)
TOP_RIGHT_X: float = BOUNDING_BOX_TOP['x'] + BOUNDING_BOX_TOP['width']   # 4.000"
TOP_RIGHT_Y: float = BOUNDING_BOX_TOP['y']                               # 0.250"
BOTTOM_RIGHT_X: float = BOUNDING_BOX_TOP['x'] + BOUNDING_BOX_TOP['width']  # 4.000"
BOTTOM_RIGHT_Y: float = BOUNDING_BOX_TOP['y'] + BOUNDING_BOX_TOP['height']  # 7.000"
