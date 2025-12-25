#!/usr/bin/env python3
"""
Transform Utilities Module - Golf Yardage Book Extension Suite

Provides shared utilities for SVG transforms, bounding box measurement,
and stroke width management used across the yardage book pipeline.

This module handles the complexities of SVG transform matrices, cumulative
scaling, and the temporary group measurement pattern that enables accurate
bounding box calculations with nested transforms.

Author: Golf Yardage Book Extension Suite
License: MIT
"""
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, List, Tuple, Optional, Union

import inkex
from inkex import Transform, Group

if TYPE_CHECKING:
    from inkex import BaseElement

# Configure module logger
logger = logging.getLogger(__name__)

# Type aliases
BoundingBoxData = Tuple[float, float, float, float]  # (left, right, top, bottom)

# Constants
TARGET_STROKE_MM: float = 0.25  # Target rendered stroke width in millimeters


class SimpleBoundingBox:
    """
    Simple bounding box class that mimics inkex.BoundingBox interface.

    This is used when we need to create a combined bounding box from multiple
    elements, since inkex.BoundingBox doesn't expose a constructor we can use.

    Attributes:
        left: Left edge x-coordinate
        right: Right edge x-coordinate
        top: Top edge y-coordinate
        bottom: Bottom edge y-coordinate
        width: Width (right - left)
        height: Height (bottom - top)

    Examples:
        >>> bbox = SimpleBoundingBox(0, 100, 0, 50)
        >>> bbox.width
        100.0
        >>> bbox.height
        50.0
    """

    def __init__(self, left: float, right: float, top: float, bottom: float) -> None:
        """
        Initialize bounding box with edge coordinates.

        Args:
            left: Left edge x-coordinate
            right: Right edge x-coordinate
            top: Top edge y-coordinate
            bottom: Bottom edge y-coordinate
        """
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.width = right - left
        self.height = bottom - top

    def __repr__(self) -> str:
        return f"SimpleBoundingBox(left={self.left}, right={self.right}, top={self.top}, bottom={self.bottom})"

    @classmethod
    def from_tuple(cls, bbox_tuple: BoundingBoxData) -> SimpleBoundingBox:
        """
        Create SimpleBoundingBox from a tuple.

        Args:
            bbox_tuple: Tuple of (left, right, top, bottom)

        Returns:
            SimpleBoundingBox instance

        Examples:
            >>> bbox = SimpleBoundingBox.from_tuple((0, 100, 0, 50))
        """
        left, right, top, bottom = bbox_tuple
        return cls(left, right, top, bottom)

    def to_tuple(self) -> BoundingBoxData:
        """
        Convert to tuple format.

        Returns:
            Tuple of (left, right, top, bottom)
        """
        return (self.left, self.right, self.top, self.bottom)


def get_cumulative_scale(element: BaseElement, return_components: bool = False) -> float | tuple[float, float, float]:
    """
    Calculate the cumulative scale factor from an element's transform chain.

    This walks up the element hierarchy and extracts the scale component from
    each transform matrix by calculating the magnitude of the basis vectors.

    The scale is extracted from the transform matrix by computing:
    - scale_x = sqrt(a² + b²)  where [a, b] is the x-basis vector
    - scale_y = sqrt(c² + d²)  where [c, d] is the y-basis vector
    - scale = (scale_x + scale_y) / 2

    Args:
        element: Element to calculate cumulative scale for
        return_components: If True, return (scale_x, scale_y, average) instead of just average

    Returns:
        Cumulative scale factor (1.0 if no scaling), or tuple of (scale_x, scale_y, average) if return_components=True

    Examples:
        >>> scale = get_cumulative_scale(my_element)
        >>> # Use for stroke compensation
        >>> compensated_stroke = target_stroke / scale
    """
    cumulative_scale = 1.0
    cumulative_scale_x = 1.0
    cumulative_scale_y = 1.0
    current: Optional[BaseElement] = element

    while current is not None:
        transform = current.transform
        if transform is not None and str(transform) != str(Transform()):
            matrix = transform.matrix

            try:
                # Extract scale from transform matrix
                # Matrix format varies by inkex version
                if hasattr(matrix, '__len__') and len(matrix) == 6:
                    # Flat tuple format: (a, b, c, d, e, f)
                    a, b, c, d = matrix[0], matrix[1], matrix[2], matrix[3]
                else:
                    # 2D matrix format (row-major): [[a, c, e], [b, d, f]]
                    # Standard SVG matrix: [a c e; b d f] maps (x,y) → (ax+cy+e, bx+dy+f)
                    a, b = matrix[0][0], matrix[1][0]
                    c, d = matrix[0][1], matrix[1][1]

                # Scale is the magnitude of the basis vectors
                scale_x = math.sqrt(a * a + b * b)
                scale_y = math.sqrt(c * c + d * d)
                scale = (scale_x + scale_y) / 2.0
                cumulative_scale *= scale
                cumulative_scale_x *= scale_x
                cumulative_scale_y *= scale_y
            except (IndexError, TypeError, ValueError) as e:
                logger.debug(
                    "Could not extract scale from transform for element %s: %s",
                    element.get('id', 'unknown'),
                    e,
                )

        current = current.getparent()

    if return_components:
        return (cumulative_scale_x, cumulative_scale_y, cumulative_scale)
    return cumulative_scale


def set_stroke_recursive(
    element: BaseElement,
    stroke_width_mm: Union[str, float],
    use_vector_effect: bool = False,
) -> None:
    """
    Set stroke properties on an element and all its descendants in millimeters.

    This recursively walks the element tree and applies stroke properties
    to all shape elements (path, rect, circle, ellipse, polygon, polyline, line).
    The stroke width is always specified with 'mm' units for consistent print output.

    By default, uses scale compensation (calculates inverse stroke width) rather than
    vector-effect, as vector-effect doesn't work reliably with element transforms.

    Sets stroke properties:
    - stroke: #000000 (black)
    - stroke-width: specified value with 'mm' units
    - stroke-opacity: 1 (full opacity)
    - vector-effect: non-scaling-stroke (optional, controlled by use_vector_effect)

    Args:
        element: Element to set stroke properties on
        stroke_width_mm: Stroke width in millimeters (will be converted to string with 'mm' suffix)
        use_vector_effect: Whether to apply vector-effect: non-scaling-stroke (default False)

    Examples:
        >>> # Set compensated stroke (standard approach)
        >>> compensated = 0.25 / get_cumulative_scale(element)
        >>> set_stroke_recursive(element, compensated)
        >>>
        >>> # Set stroke with vector-effect (only for parent transforms)
        >>> set_stroke_recursive(my_group, 0.25, use_vector_effect=True)
    """
    # Convert to float if string
    if isinstance(stroke_width_mm, str):
        # Remove any existing units for clean conversion
        stroke_width_mm = stroke_width_mm.rstrip('mmpxtin ')
        stroke_width_mm = float(stroke_width_mm)

    # IMPORTANT: Store as unitless value (user units), NOT with 'mm' suffix
    # When stroke-width has explicit units (e.g., "1.378mm"), Inkscape applies
    # an incorrect conversion factor (~1.459x) when rendering transformed elements.
    # Storing as unitless user units avoids this issue and renders correctly.
    stroke_width_str = f'{stroke_width_mm}'
    shape_tags = ['path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline', 'line']
    local_tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag

    if local_tag in shape_tags:
        try:
            style = element.style
            style['stroke'] = '#000000'                      # Black stroke
            style['stroke-width'] = stroke_width_str         # Width in mm
            style['stroke-opacity'] = '1'                    # Full opacity
            if use_vector_effect:
                style['vector-effect'] = 'non-scaling-stroke'    # Prevent scaling
            element.style = style
        except (AttributeError, TypeError, KeyError) as e:
            logger.debug(
                "Could not set stroke properties for element %s: %s",
                element.get('id', 'unknown'),
                e,
            )

    for child in element:
        set_stroke_recursive(child, stroke_width_mm, use_vector_effect)


def apply_stroke_compensation(
    element: BaseElement,
    target_stroke_mm: float = TARGET_STROKE_MM,
    svg_context: Optional[inkex.SvgDocumentElement] = None,
    use_vector_effect: bool = False,
) -> None:
    """
    Apply stroke width to scaled elements in millimeters.

    By default, calculates cumulative scale and applies compensated stroke width
    to achieve the target rendered stroke. This works reliably for all transform
    scenarios (parent transforms and element transforms).

    Args:
        element: Element to apply stroke to
        target_stroke_mm: Target stroke width in millimeters (default 0.25mm)
        svg_context: SVG document element (unused, kept for API compatibility)
        use_vector_effect: Whether to use vector-effect instead of compensation (default False)

    Examples:
        >>> # Apply compensated stroke (standard approach)
        >>> apply_stroke_compensation(scaled_element)
        >>>
        >>> # Apply with vector-effect (only for parent transforms)
        >>> apply_stroke_compensation(element, use_vector_effect=True)
    """
    if use_vector_effect:
        # Apply target stroke directly - vector-effect prevents scaling
        set_stroke_recursive(element, target_stroke_mm, use_vector_effect=True)
    else:
        # Calculate compensated stroke for all transforms
        cumulative_scale = get_cumulative_scale(element)
        if cumulative_scale <= 0:
            cumulative_scale = 1.0
        compensated_mm = target_stroke_mm / cumulative_scale
        set_stroke_recursive(element, compensated_mm, use_vector_effect=False)


def measure_elements_via_temp_group(
    elements: List[BaseElement],
    document_root: inkex.SvgDocumentElement,
    parent_transform: Optional[Transform] = None,
    temp_group_id: Optional[str] = None,
) -> Optional[SimpleBoundingBox]:
    """
    Measure bounding box by temporarily moving elements to document root.

    This method temporarily moves elements to a root-level group to get
    accurate bounding box measurements that account for transforms.
    Uses try/finally to guarantee element restoration even if an exception occurs.

    Strategy:
    1. Create temporary group at document root
    2. Apply parent transform to temp group
    3. Move elements to temp group
    4. Measure bounding box of temp group
    5. Restore elements to original positions (always, even if error)
    6. Remove temp group

    Args:
        elements: List of elements to measure
        document_root: Document root element
        parent_transform: Transform to apply to temp group (default: identity)
        temp_group_id: ID for temp group (default: auto-generated)

    Returns:
        SimpleBoundingBox or None if measurement fails

    Examples:
        >>> # Measure single element
        >>> bbox = measure_elements_via_temp_group(
        ...     [green_element],
        ...     root,
        ...     parent_transform=hole_group.transform
        ... )
        >>>
        >>> # Measure multiple terrain elements
        >>> bbox = measure_elements_via_temp_group(
        ...     [green, fairway, bunker],
        ...     root,
        ...     temp_group_id='_temp_measure_hole_01'
        ... )
    """
    if not elements:
        return None

    if parent_transform is None:
        parent_transform = Transform()

    if temp_group_id is None:
        temp_group_id = f'_temp_measure_{id(elements[0])}'

    # Store original parent and index for each element
    element_origins: List[Tuple[BaseElement, Optional[BaseElement], int]] = []
    for element in elements:
        original_parent = element.getparent()
        original_index = list(original_parent).index(element) if original_parent is not None else 0
        element_origins.append((element, original_parent, original_index))

    # Create temporary group for measurement
    temp_group = Group()
    temp_group.set('id', temp_group_id)
    temp_group.transform = parent_transform
    document_root.append(temp_group)

    result_bbox = None
    try:
        # Move elements to temp group for measurement
        for element, _, _ in element_origins:
            original_parent = element.getparent()
            if original_parent is not None:
                original_parent.remove(element)
            temp_group.append(element)

        # Perform the measurement
        temp_bbox = temp_group.bounding_box()
        if temp_bbox:
            result_bbox = SimpleBoundingBox(
                left=temp_bbox.left,
                right=temp_bbox.right,
                top=temp_bbox.top,
                bottom=temp_bbox.bottom
            )
    finally:
        # Always restore elements to their original positions
        # Process in original order - insert() handles positioning correctly
        for element, original_parent, original_index in element_origins:
            # Only remove if element is still in temp_group
            if element.getparent() is temp_group:
                temp_group.remove(element)
            if original_parent is not None:
                original_parent.insert(original_index, element)

        # Always remove the temp group from the document
        if temp_group.getparent() is not None:
            document_root.remove(temp_group)

    return result_bbox
