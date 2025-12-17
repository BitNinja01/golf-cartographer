#!/usr/bin/env python3
"""
Color Utilities Module - Shared color detection for Golf Yardage Book Extension Suite

This module provides centralized color detection and categorization utilities
used across the yardage book extension pipeline. It ensures consistent color
matching between Stage 1 (Flatten SVG) and Stage 2 (Group Hole) tools.

Color Detection Strategy:
All golf course elements are identified by their fill or stroke colors from
OpenStreetMap exports. Fuzzy matching with configurable tolerance handles
color variations from different OSM data sources and color space conversions.

Author: Golf Yardage Book Extension Suite
License: MIT
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Tuple, Dict, Any

import inkex

if TYPE_CHECKING:
    from inkex import BaseElement

# Configure module logger
logger = logging.getLogger(__name__)


# Type alias for RGB tuple
RGB = Tuple[int, int, int]

# Type alias for color definition dictionary
ColorDefinition = Dict[str, Any]

# Golf course color definitions with RGB values
# Each color has a name, RGB tuple, and default tolerance
COLORS: Dict[str, ColorDefinition] = {
    "green": {
        "rgb": (135, 222, 189),  # #87debd - Golf course greens
        "tolerance": 8,
        "style_attr": "fill",
    },
    "fairway": {
        "rgb": (204, 235, 176),  # #ccebb0 - Fairway areas
        "tolerance": 8,
        "style_attr": "fill",
    },
    "bunker": {
        "rgb": (245, 232, 197),  # #f5e8c5 - Bunkers/sand hazards
        "tolerance": 8,
        "style_attr": "fill",
    },
    "water": {
        "rgb": (168, 209, 222),  # #a8d1de - Water features (lakes, ponds)
        "tolerance": 8,
        "style_attr": "fill",
    },
    "tree": {
        "rgb": (143, 191, 122),  # #8fbf7a - Trees/grass areas
        "tolerance": 8,
        "style_attr": "fill",
    },
    "mapping_line": {
        "rgb": (102, 102, 102),  # #666666 - Hole mapping lines (neutral gray)
        "tolerance": 8,
        "style_attr": "stroke",
        "requires_no_fill": True,  # Must have fill:none
    },
    "path_line": {
        "rgb": (250, 127, 112),  # #fa7f70 - Cart/walking paths (coral/salmon)
        "tolerance": 8,
        "style_attr": "stroke",
    },
}


def parse_color(color_string: str) -> Optional[RGB]:
    """
    Parse a color string into RGB tuple.

    Handles multiple color formats:
    - Hex colors: #RGB, #RRGGBB
    - RGB function: rgb(R, G, B)
    - Named colors: red, blue, green, etc.

    Args:
        color_string: Color string in any supported format

    Returns:
        Tuple of (R, G, B) integers (0-255), or None if parsing fails

    Examples:
        >>> parse_color("#87debd")
        (135, 222, 189)
        >>> parse_color("rgb(135, 222, 189)")
        (135, 222, 189)
        >>> parse_color("red")
        (255, 0, 0)
    """
    if not color_string or color_string == "none":
        return None

    try:
        color = inkex.Color(color_string)
        if hasattr(color, "red") and hasattr(color, "green") and hasattr(color, "blue"):
            return (color.red, color.green, color.blue)
    except (ValueError, AttributeError) as e:
        logger.debug("Failed to parse color '%s': %s", color_string, e)

    return None


def check_color_match(
    style: Optional[inkex.Style],
    style_attr: str,
    target_rgb: RGB,
    tolerance: int = 8,
) -> bool:
    """
    Check if a style attribute color matches target RGB within tolerance.

    Color Matching Algorithm:
    Each RGB channel is checked independently against the target value
    with the specified tolerance. A match requires ALL channels to be
    within the tolerance range.

    Tolerance Calculation:
    For target value T and tolerance TOL, the acceptable range is [T-TOL, T+TOL].
    For example, with T=135 and TOL=8, values from 127 to 143 are accepted.

    Args:
        style: inkex.Style object from an SVG element
        style_attr: Style attribute to check ('fill' or 'stroke')
        target_rgb: Target RGB tuple (R, G, B) with values 0-255
        tolerance: Maximum deviation per channel (default 8)

    Returns:
        True if the style attribute color matches target within tolerance

    Examples:
        >>> style = element.style
        >>> check_color_match(style, 'fill', (135, 222, 189), tolerance=8)
        True  # If fill is #87debd or similar
    """
    if style is None:
        return False

    color_value = style.get(style_attr)
    if color_value is None:
        return False

    try:
        # Parse color (may be string or Color object)
        if isinstance(color_value, str):
            color = inkex.Color(color_value)
        else:
            color = color_value

        # Validate color has RGB components
        if not (
            hasattr(color, "red") and hasattr(color, "green") and hasattr(color, "blue")
        ):
            return False

        r, g, b = color.red, color.green, color.blue
        target_r, target_g, target_b = target_rgb

        # Check each channel within tolerance range
        r_match = (target_r - tolerance) <= r <= (target_r + tolerance)
        g_match = (target_g - tolerance) <= g <= (target_g + tolerance)
        b_match = (target_b - tolerance) <= b <= (target_b + tolerance)

        return r_match and g_match and b_match

    except (ValueError, AttributeError, inkex.colors.ColorIdError) as e:
        logger.debug("Color match check failed for '%s': %s", style_attr, e)
        return False


def is_color_category(element: BaseElement, category: str) -> bool:
    """
    Check if an element matches a specific color category.

    This is a convenience function that combines color definition lookup
    with the color matching check. It handles special cases like
    mapping_line which requires fill:none.

    Args:
        element: SVG element to check
        category: Color category name from COLORS dictionary

    Returns:
        True if element matches the specified color category

    Raises:
        KeyError: If category is not defined in COLORS dictionary
    """
    if category not in COLORS:
        raise KeyError(f"Unknown color category: {category}")

    color_def = COLORS[category]
    style = element.style

    if style is None:
        return False

    # Handle special case: mapping_line requires fill:none
    if color_def.get("requires_no_fill", False):
        fill = style.get("fill")
        if fill is not None and fill != "none":
            return False

    return check_color_match(
        style,
        color_def["style_attr"],
        color_def["rgb"],
        color_def["tolerance"],
    )


def categorize_element_by_color(element: BaseElement) -> str:
    """
    Categorize an element based on its color.

    This function checks the element against all defined color categories
    in a specific order optimized for golf course elements. The order
    matters because some colors may overlap and we want specific matches
    to take precedence.

    Categorization Order:
    1. mapping_line - Checked first (requires fill:none + gray stroke)
    2. path_line - Cart/walking paths (distinctive coral stroke)
    3. green - Golf course greens
    4. fairway - Fairway areas
    5. bunker - Sand hazards
    6. water - Water features
    7. tree - Trees/grass areas
    8. other - Default for uncategorized elements

    Args:
        element: SVG element to categorize

    Returns:
        Category string: 'green', 'fairway', 'bunker', 'water', 'tree',
                        'mapping_line', 'path_line', or 'other'
    """
    # Check in priority order - mapping_line and path_line first
    # because they use stroke instead of fill
    if is_color_category(element, "mapping_line"):
        return "mapping_line"

    if is_color_category(element, "path_line"):
        return "path_line"

    # Check fill-based categories
    if is_color_category(element, "green"):
        return "green"

    if is_color_category(element, "fairway"):
        return "fairway"

    if is_color_category(element, "bunker"):
        return "bunker"

    if is_color_category(element, "water"):
        return "water"

    if is_color_category(element, "tree"):
        return "tree"

    return "other"


def get_color_rgb(category: str) -> Optional[RGB]:
    """
    Get the RGB values for a color category.

    Args:
        category: Color category name from COLORS dictionary

    Returns:
        RGB tuple (R, G, B) or None if category not found
    """
    if category in COLORS:
        return COLORS[category]["rgb"]
    return None


def get_color_hex(category: str) -> Optional[str]:
    """
    Get the hex color code for a category.

    Args:
        category: Color category name from COLORS dictionary

    Returns:
        Hex color string (e.g., '#87debd') or None if category not found
    """
    rgb = get_color_rgb(category)
    if rgb:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    return None
