#!/usr/bin/env python3
"""
Geometry Utilities Module - Golf Yardage Book Extension Suite

Provides shared utilities for geometric calculations including centroid
computation, rotation angles, and canvas bounds handling.

This module implements algorithms for analyzing SVG geometry including
the shoelace formula for polygon centroids and canvas boundary detection.

Author: Golf Yardage Book Extension Suite
License: MIT
"""
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, List, Tuple, Optional

import inkex

if TYPE_CHECKING:
    from inkex import BaseElement

# Configure module logger
logger = logging.getLogger(__name__)

# Type aliases
Centroid = Tuple[float, float]  # (x, y)

# Constants
# Threshold for detecting degenerate polygons (~0.001mm² in typical user units)
CENTROID_AREA_EPSILON: float = 0.0001


def calculate_centroid(elements: List[BaseElement]) -> Optional[Centroid]:
    """
    Calculate true geometric centroid using polygon shoelace formula.

    Three-Level Fallback Strategy:

    1. Shoelace Formula (Preferred):
       Calculates the true geometric centroid of an irregular polygon.
       More accurate than bounding box center for non-rectangular shapes
       like golf greens (kidney beans, dog-legs, etc.).

       Mathematical formula for centroid (Cx, Cy):
         Area = 1/2 * Σ(x_i * y_i+1 - x_i+1 * y_i)
         Cx = 1/(6*Area) * Σ((x_i + x_i+1) * (x_i * y_i+1 - x_i+1 * y_i))
         Cy = 1/(6*Area) * Σ((y_i + y_i+1) * (x_i * y_i+1 - x_i+1 * y_i))

    2. Vertex Average:
       If shoelace produces area < 0.0001 (degenerate polygon),
       falls back to simple arithmetic mean of vertices.

    3. Bounding Box Center:
       If vertex extraction fails, uses average of bounding box centers.

    Args:
        elements: List of SVG elements (expected to be path elements)

    Returns:
        (x, y) coordinates of geometric centroid, or None if all methods fail

    Examples:
        >>> green_centroid = calculate_centroid([green_element])
        >>> # Use for positioning
        >>> yardage_lines.transform = Transform(translate=green_centroid)
    """
    all_points: List[Tuple[float, float]] = []

    # Level 1: Try to extract vertices from path elements
    for element in elements:
        try:
            if isinstance(element, inkex.PathElement):
                path = element.path.to_absolute()
                for segment in path:
                    if hasattr(segment, 'x') and hasattr(segment, 'y'):
                        all_points.append((float(segment.x), float(segment.y)))
        except (AttributeError, TypeError, ValueError) as e:
            logger.debug(
                "Could not extract path vertices for centroid from element %s: %s",
                element.get('id', 'unknown'),
                e,
            )

    # If we have 3+ vertices, use shoelace formula
    if len(all_points) >= 3:
        try:
            area = 0.0
            cx = 0.0
            cy = 0.0

            # Sum over all edges (closing the polygon)
            for i in range(len(all_points)):
                x1, y1 = all_points[i]
                x2, y2 = all_points[(i + 1) % len(all_points)]
                cross = x1 * y2 - x2 * y1
                area += cross
                cx += (x1 + x2) * cross
                cy += (y1 + y2) * cross

            area /= 2.0

            if abs(area) > CENTROID_AREA_EPSILON:
                # Normal case: valid polygon area
                cx = cx / (6.0 * area)
                cy = cy / (6.0 * area)
                return (cx, cy)
            else:
                # Degenerate polygon: fall back to vertex average
                logger.debug("Polygon area near zero, using vertex average for centroid")
                cx = sum(p[0] for p in all_points) / len(all_points)
                cy = sum(p[1] for p in all_points) / len(all_points)
                return (cx, cy)
        except (ZeroDivisionError, ArithmeticError) as e:
            logger.debug("Shoelace centroid calculation failed: %s", e)

    # Level 2: Fallback to bounding box center averaging
    total_x = 0.0
    total_y = 0.0
    count = 0

    for element in elements:
        try:
            bbox = element.bounding_box()
            if bbox is not None:
                center_x = (bbox.left + bbox.right) / 2.0
                center_y = (bbox.top + bbox.bottom) / 2.0
                total_x += center_x
                total_y += center_y
                count += 1
        except (AttributeError, TypeError, ValueError) as e:
            logger.debug(
                "Could not calculate bounding box for centroid fallback from element %s: %s",
                element.get('id', 'unknown'),
                e,
            )

    if count == 0:
        return None

    return (total_x / count, total_y / count)


def calculate_rotation_angle(
    target_point: Centroid,
    center_point: Centroid,
    target_direction: str = 'up',
) -> float:
    """
    Calculate rotation angle to orient a point toward a target direction.

    This calculates the angle needed to rotate around center_point such that
    target_point faces the specified direction.

    Args:
        target_point: Point to orient (e.g., green centroid)
        center_point: Point to rotate around (e.g., hole center)
        target_direction: Direction to face ('up', 'down', 'left', 'right')

    Returns:
        Rotation angle in degrees

    Examples:
        >>> # Orient green toward top of bounding box
        >>> angle = calculate_rotation_angle(green_centroid, hole_center, 'up')
        >>> rotation = Transform(rotate=(angle, center_x, center_y))
    """
    dx = target_point[0] - center_point[0]
    dy = target_point[1] - center_point[1]

    # Calculate current angle from center to target
    angle_to_target = math.atan2(dy, dx)

    # Define target angles for each direction
    # In SVG coordinate system: +X is right, +Y is down
    direction_angles = {
        'up': -math.pi / 2.0,    # -90 degrees (negative Y direction)
        'down': math.pi / 2.0,    # 90 degrees (positive Y direction)
        'left': math.pi,          # 180 degrees (negative X direction)
        'right': 0.0,             # 0 degrees (positive X direction)
    }

    if target_direction not in direction_angles:
        logger.warning("Unknown direction '%s', defaulting to 'up'", target_direction)
        target_direction = 'up'

    target_angle = direction_angles[target_direction]
    rotation_radians = target_angle - angle_to_target
    rotation_degrees = math.degrees(rotation_radians)

    return rotation_degrees


def get_canvas_bounds(
    document_root: inkex.SvgDocumentElement,
    svg_context: inkex.SvgDocumentElement,
) -> Tuple[float, float, float, float]:
    """
    Get canvas boundaries from document viewBox or width/height attributes.

    Canvas bounds are determined in the following order of preference:
    1. viewBox attribute (most reliable for coordinate system)
    2. width/height attributes (fallback if viewBox not present)
    3. Default 1000x1000 (last resort)

    Args:
        document_root: Document root element
        svg_context: SVG context for unit conversion

    Returns:
        Tuple of (x_min, y_min, x_max, y_max) canvas bounds in document units

    Examples:
        >>> bounds = get_canvas_bounds(root, svg)
        >>> x_min, y_min, x_max, y_max = bounds
        >>> # Use for clipping operations
        >>> if x < x_min or x > x_max:
        ...     # Element is outside canvas
    """
    # Try to get viewBox first (most reliable approach)
    viewbox = document_root.get('viewBox')
    if viewbox:
        parts = viewbox.strip().split()
        if len(parts) == 4:
            try:
                x, y, w, h = map(float, parts)
                return (x, y, x + w, y + h)
            except (ValueError, TypeError) as e:
                logger.debug("Failed to parse viewBox '%s': %s", viewbox, e)

    # Fall back to width/height attributes if viewBox not present
    width = document_root.get('width')
    height = document_root.get('height')
    if width and height:
        try:
            # Convert to user units (handles units like '100px', '10in', etc.)
            w = svg_context.unittouu(width)
            h = svg_context.unittouu(height)
            return (0, 0, w, h)
        except (ValueError, TypeError) as e:
            logger.debug("Failed to parse width/height: %s", e)

    # Default fallback (usually only reached for malformed SVG)
    logger.warning("Could not determine canvas bounds, using default 1000x1000")
    return (0, 0, 1000, 1000)
