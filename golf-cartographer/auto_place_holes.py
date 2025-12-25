#!/usr/bin/env python3
"""
Auto-Place Holes Tool - Stage 3 of Golf Yardage Book Extension Suite

This extension automatically positions and scales all 18 hole groups, then scales
their greens for the yardage book template. It performs both hole placement and
green scaling in a single operation.

Hole Placement:
- Rotates each hole so its green faces toward the top
- Scales holes to maximize space usage within bounding box
- Positions holes in the "top" area of yardage book template

Green Scaling:
- Duplicates green elements from positioned holes
- Scales greens to fit target box (3.75" x 3.75")
- Centers greens in the "bottom" area of yardage book template

Pipeline Context:
- Input: SVG with 18 hole groups (output from Tool #2 / Stage 2)
- Output: Holes positioned in "top" area + scaled greens in "bottom" area
- Next Stage: Tool #4 (Add Hole Label) will add labels to each hole

Author: Golf Yardage Book Extension Suite
License: MIT
"""
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional, Any

import inkex
from inkex import Group, Transform

# Import shared utilities
from transform_utils import (
    SimpleBoundingBox,
    get_cumulative_scale,
    set_stroke_recursive,
    measure_elements_via_temp_group,
)
from geometry_utils import (
    Centroid,
    calculate_centroid,
    calculate_rotation_angle,
)

if TYPE_CHECKING:
    from inkex import BaseElement

# Configure module logger
logger = logging.getLogger(__name__)

# Type aliases
TerrainElement = Tuple["BaseElement", Group, int]  # (element, original_parent, original_index)


class AutoPlaceHoles(inkex.EffectExtension):
    """
    Auto-Place Holes tool - combines Stages 3 & 4 of the pipeline.
    """

    # Stage 3: Hardcoded bounding box for hole placement in "top" area (units in inches)
    BOUNDING_BOX: Dict[str, float] = {
        'x': 0.257,
        'y': 0.247,
        'width': 3.736,
        'height': 6.756
    }

    # Stage 4: Target bounding box for scaled greens in "bottom" area (units in inches)
    TARGET_BOX: Dict[str, float] = {
        'x': 0.250,
        'y': 7.000,
        'width': 3.750,
        'height': 3.750,
    }

    # Green positioning reference: top-left corner (in inches)
    GREEN_POSITION: Dict[str, float] = {
        'x': 0.802,
        'y': 7.416,
    }

    # Edge buffer for greens: 80% = 20% margin
    GREEN_EDGE_BUFFER: float = 0.80

    def effect(self) -> None:
        """
        Main execution method for the Auto-Place Holes Tool (Stage 3).

        This stage performs two operations:
        1. Position and scale holes in "top" area
        2. Scale greens in "bottom" area
        """
        root = self.document.getroot()
        processed_holes = []
        failed_holes = []

        # Process all 18 holes in sequence
        for hole_num in range(1, 19):
            hole_id = f"hole_{hole_num:02d}"
            hole_group = self._find_hole_group(root, hole_id)

            if hole_group is None:
                failed_holes.append(f"{hole_id} (not found)")
                continue

            try:
                self._process_hole(hole_group, hole_num)
                processed_holes.append(hole_id)
            except Exception as e:
                failed_holes.append(f"{hole_id} (error: {str(e)})")

        # Move all processed holes to 'top' group
        top_group = None
        for elem in root.iter():
            if isinstance(elem, Group):
                label = elem.get(inkex.addNS('label', 'inkscape'))
                if label and label.lower() == 'top':
                    top_group = elem
                    break

        if top_group is not None:
            for hole_id in processed_holes:
                hole_group = self._find_hole_group(root, hole_id)
                if hole_group is not None:
                    parent = hole_group.getparent()
                    if parent is not None:
                        parent.remove(hole_group)
                    top_group.append(hole_group)

        # Move 'other' groups to top of each hole group (end of DOM = top of visual stack)
        for hole_num in range(1, 19):
            hole_id = f"hole_{hole_num:02d}"
            hole_group = self._find_hole_group(root, hole_id)

            if hole_group is None:
                continue

            other_group = None
            for child in list(hole_group):
                if isinstance(child, Group):
                    label = child.get(inkex.addNS('label', 'inkscape'))
                    if label and label.lower() == 'other':
                        other_group = child
                        break

            if other_group is not None:
                hole_group.remove(other_group)
                hole_group.append(other_group)

        # ==== Stage 4: Scale greens in "bottom" area ====

        # Find bottom group
        bottom_group = self._find_bottom_group(root)
        if bottom_group is None:
            inkex.errormsg("Could not find 'bottom' group. Skipping green scaling.")
            greens_processed = 0
        else:
            # Find greens_guide group to determine insertion point
            greens_guide_index = None
            for i, child in enumerate(bottom_group):
                if isinstance(child, Group):
                    label = child.get(inkex.addNS('label', 'inkscape'))
                    if label and label.lower() == 'greens_guide':
                        greens_guide_index = i
                        break

            # Process each hole's green
            greens_processed = 0
            insertion_index = greens_guide_index  # Track current insertion point
            for hole_num in range(1, 19):
                green, hole_group = self._find_green_with_parent(root, hole_num)
                if green is not None and hole_group is not None:
                    # Duplicate green and preserve hole identification
                    green_copy = green.copy()
                    green_copy.set('id', f'green_{hole_num:02d}_bottom')
                    green_copy.label = f'green_{hole_num:02d}_bottom'

                    # Get the inherited transform from the hole group
                    hole_group_transform = hole_group.transform if hole_group.transform is not None else Transform()

                    # Add green copy to bottom group BEFORE greens_guide
                    # This ensures greens are between 'cover' and 'greens_guide' in the stack
                    if insertion_index is not None:
                        bottom_group.insert(insertion_index, green_copy)
                        insertion_index += 1  # Increment for next green to maintain order
                    else:
                        # Fallback: append to end if greens_guide not found
                        bottom_group.append(green_copy)

                    # Position and scale using temp group measurement
                    self._position_and_scale_green(green_copy, hole_group_transform, hole_num)

                    greens_processed += 1
                else:
                    logger.debug("Hole %02d: green element not found for scaling", hole_num)

        # ==== Stage 5: Apply strokes to all terrain elements ====
        # Applied after hole positioning and green scaling to ensure consistency
        # Using full scale compensation (no vector-effect) for all elements
        TARGET_STROKE_MM = 0.25

        # Apply strokes to holes in "top" area
        for hole_num in range(1, 19):
            hole_id = f"hole_{hole_num:02d}"
            hole_group = self._find_hole_group(root, hole_id)

            if hole_group is None:
                continue

            green_id = f"green_{hole_num:02d}"

            for child in hole_group:
                child_id = child.get('id')
                should_set_stroke = False

                if child_id == green_id:
                    should_set_stroke = True

                if isinstance(child, Group):
                    label = child.get(inkex.addNS('label', 'inkscape'))
                    if label and label.lower() in ('fairways', 'bunkers', 'other'):
                        should_set_stroke = True
                    # Also apply to yardage lines (label contains 'yardage')
                    if label and 'yardage' in label.lower():
                        should_set_stroke = True

                if should_set_stroke:
                    # Apply scale compensation to achieve target stroke width
                    cumulative_scale = get_cumulative_scale(child)
                    if cumulative_scale <= 0:
                        cumulative_scale = 1.0
                    compensated_stroke_mm = TARGET_STROKE_MM / cumulative_scale
                    set_stroke_recursive(child, compensated_stroke_mm)

        # Apply strokes to greens in "bottom" area
        if bottom_group is not None:
            for child in bottom_group:
                child_id = child.get('id')
                # Target green_XX_bottom elements
                if child_id and child_id.startswith('green_') and child_id.endswith('_bottom'):
                    # Apply scale compensation to achieve target stroke width
                    cumulative_scale = get_cumulative_scale(child)
                    if cumulative_scale <= 0:
                        cumulative_scale = 1.0
                    compensated_stroke_mm = TARGET_STROKE_MM / cumulative_scale
                    set_stroke_recursive(child, compensated_stroke_mm)

        # Report results
        if len(processed_holes) > 0:
            inkex.utils.debug(f"Stage 3: Successfully processed {len(processed_holes)} holes")
        if greens_processed > 0:
            inkex.utils.debug(f"Stage 4: Successfully scaled {greens_processed} greens")
        if len(failed_holes) > 0:
            inkex.errormsg(f"Failed to process {len(failed_holes)} holes: {', '.join(failed_holes)}")

    def _find_hole_group(self, root: inkex.SvgDocumentElement, hole_id: str) -> Optional[Group]:
        """Find a hole group by its ID or label."""
        element = root.getElementById(hole_id)
        if element is not None and isinstance(element, Group):
            return element

        for elem in root.iter():
            if isinstance(elem, Group):
                label = elem.label
                if label and label.lower() == hole_id.lower():
                    return elem

        return None

    def _process_hole(self, hole_group: Group, hole_num: int) -> None:
        """Process a single hole: rotate, scale, and position within bounding box."""
        # Clear existing transforms for idempotent calculations
        hole_group.transform = Transform()

        # Find green element
        green_element = self._find_green_element(hole_group, hole_num)
        if green_element is None:
            raise ValueError(f"Green element not found")

        # Calculate green centroid
        green_centroid = calculate_centroid([green_element])
        if green_centroid is None:
            raise ValueError(f"Could not calculate green centroid")

        # Calculate hole bounding box from terrain elements only
        hole_bbox = self._get_terrain_bounding_box(hole_group, hole_num)
        if hole_bbox is None:
            raise ValueError(f"Could not calculate hole bounding box")

        # Calculate hole center
        hole_center_x = (hole_bbox.left + hole_bbox.right) / 2.0
        hole_center_y = (hole_bbox.top + hole_bbox.bottom) / 2.0

        # Calculate rotation angle
        rotation_angle = calculate_rotation_angle(
            green_centroid,
            (hole_center_x, hole_center_y),
            target_direction='up'
        )

        # Build rotation transform
        rotation_transform = Transform(translate=(hole_center_x, hole_center_y))
        rotation_transform @= Transform(rotate=rotation_angle)
        rotation_transform @= Transform(translate=(-hole_center_x, -hole_center_y))

        # Apply rotation only first
        hole_group.transform = rotation_transform

        # Measure terrain bbox via temporary root-level group
        measured_bbox = self._measure_terrain_via_temp_group(hole_group, hole_num)

        if measured_bbox:
            # Get target bounding box dimensions in user units
            bbox_width = self.svg.unittouu(f"{self.BOUNDING_BOX['width']}in")
            bbox_height = self.svg.unittouu(f"{self.BOUNDING_BOX['height']}in")

            # Calculate scale factors
            scale_x = bbox_width / measured_bbox.width if measured_bbox.width > 0 else 1.0
            scale_y = bbox_height / measured_bbox.height if measured_bbox.height > 0 else 1.0

            # Use minimum with edge buffer
            EDGE_BUFFER = 0.90
            calculated_scale = min(scale_x, scale_y) * EDGE_BUFFER

            # Apply scale around measured center
            measured_center_x = (measured_bbox.left + measured_bbox.right) / 2.0
            measured_center_y = (measured_bbox.top + measured_bbox.bottom) / 2.0

            scale_transform = Transform(translate=(measured_center_x, measured_center_y))
            scale_transform @= Transform(scale=calculated_scale)
            scale_transform @= Transform(translate=(-measured_center_x, -measured_center_y))

            final_transform = scale_transform @ hole_group.transform
            hole_group.transform = final_transform

            # Measure scaled bbox and translate to target center
            scaled_bbox = self._measure_terrain_via_temp_group(hole_group, hole_num)

            if scaled_bbox:
                current_center_x = (scaled_bbox.left + scaled_bbox.right) / 2.0
                current_center_y = (scaled_bbox.top + scaled_bbox.bottom) / 2.0

                target_x = self.svg.unittouu(f"{self.BOUNDING_BOX['x']}in")
                target_y = self.svg.unittouu(f"{self.BOUNDING_BOX['y']}in")
                target_center_x = target_x + bbox_width / 2.0
                target_center_y = target_y + bbox_height / 2.0

                translate_x = target_center_x - current_center_x
                translate_y = target_center_y - current_center_y

                translate_transform = Transform(translate=(translate_x, translate_y))
                final_transform = translate_transform @ hole_group.transform
                hole_group.transform = final_transform

                # Left-justify within target bounding box
                centered_bbox = self._measure_terrain_via_temp_group(hole_group, hole_num)

                if centered_bbox:
                    LEFT_BUFFER_INCHES = 0.5
                    left_buffer_uu = self.svg.unittouu(f"{LEFT_BUFFER_INCHES}in")
                    target_left_with_buffer = target_x + left_buffer_uu
                    left_shift = target_left_with_buffer - centered_bbox.left

                    left_justify_transform = Transform(translate=(left_shift, 0))
                    final_transform = left_justify_transform @ hole_group.transform
                    hole_group.transform = final_transform

    def _find_green_element(self, hole_group: Group, hole_num: int) -> Optional[BaseElement]:
        """Find the green element within a hole group."""
        green_id = f"green_{hole_num:02d}"

        for child in hole_group:
            if child.get('id') == green_id:
                return child
            child_id = child.get('id')
            if child_id and child_id.startswith(green_id):
                return child

        for child in hole_group:
            child_id = child.get('id')
            if child_id and 'green' in child_id.lower():
                return child

        return None

    def _get_terrain_bounding_box(self, hole_group: Group, hole_num: int) -> SimpleBoundingBox:
        """Calculate combined bounding box from only golf terrain elements."""
        green_id = f"green_{hole_num:02d}"
        green = None
        for child in hole_group:
            if child.get('id') == green_id:
                green = child
                break

        if green is None:
            raise ValueError(f"Green element '{green_id}' not found in hole {hole_num}")

        fairways = None
        for child in hole_group:
            if isinstance(child, Group):
                label = child.get(inkex.addNS('label', 'inkscape'))
                if label and label.lower() == 'fairways':
                    fairways = child
                    break

        bunkers = None
        for child in hole_group:
            if isinstance(child, Group):
                label = child.get(inkex.addNS('label', 'inkscape'))
                if label and label.lower() == 'bunkers':
                    bunkers = child
                    break

        bboxes = []

        green_bbox = green.bounding_box()
        if green_bbox is not None:
            bboxes.append(green_bbox)

        if fairways is not None:
            fairways_bbox = fairways.bounding_box()
            if fairways_bbox is not None:
                bboxes.append(fairways_bbox)

        if bunkers is not None:
            bunkers_bbox = bunkers.bounding_box()
            if bunkers_bbox is not None:
                bboxes.append(bunkers_bbox)

        if len(bboxes) == 0:
            raise ValueError(f"Could not calculate bounding box for hole {hole_num}")

        min_x = min(bbox.left if hasattr(bbox, 'left') else bbox.x.minimum for bbox in bboxes)
        min_y = min(bbox.top if hasattr(bbox, 'top') else bbox.y.minimum for bbox in bboxes)
        max_x = max(bbox.right if hasattr(bbox, 'right') else bbox.x.maximum for bbox in bboxes)
        max_y = max(bbox.bottom if hasattr(bbox, 'bottom') else bbox.y.maximum for bbox in bboxes)

        width = max_x - min_x
        height = max_y - min_y
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid bounding box dimensions for hole {hole_num}")

        return SimpleBoundingBox(left=min_x, right=max_x, top=min_y, bottom=max_y)

    def _measure_terrain_via_temp_group(
        self,
        hole_group: Group,
        hole_num: int,
    ) -> Optional[SimpleBoundingBox]:
        """Measure terrain bounding box by temporarily moving elements to root.

        Adapter method that collects terrain elements and calls the generic
        measure_elements_via_temp_group utility function.
        """
        root = self.document.getroot()
        green_id = f"green_{hole_num:02d}"

        # Collect terrain elements (green, fairways, bunkers)
        terrain_elements = []
        for child in list(hole_group):
            child_id = child.get('id')
            is_terrain = False

            if child_id == green_id:
                is_terrain = True

            if isinstance(child, Group):
                label = child.get(inkex.addNS('label', 'inkscape'))
                if label and label.lower() in ('fairways', 'bunkers'):
                    is_terrain = True

            if is_terrain:
                terrain_elements.append(child)

        # Use generic utility function for measurement
        return measure_elements_via_temp_group(
            elements=terrain_elements,
            document_root=root,
            parent_transform=hole_group.transform,
            temp_group_id=f'_temp_terrain_measure_{hole_num:02d}'
        )

    # ==== Stage 4 Methods (Green Scaling) ====

    def _find_bottom_group(self, root: inkex.SvgDocumentElement) -> Optional[Group]:
        """
        Find the 'bottom' group in the document.

        Args:
            root: SVG root element

        Returns:
            Group or None: Bottom group if found
        """
        for element in root.iter():
            if isinstance(element, Group):
                label = element.label
                if label and label.lower() == 'bottom':
                    return element

        return None

    def _find_green_with_parent(
        self,
        root: inkex.SvgDocumentElement,
        hole_number: int,
    ) -> Tuple[Optional[BaseElement], Optional[Group]]:
        """
        Find green element for a specific hole, along with its parent hole group.

        In Stage 2, greens are placed at the top level of hole groups with ID green_XX.
        We need the parent group to get its transform for accurate measurement.

        Args:
            root: SVG root element
            hole_number: Hole number (1-18)

        Returns:
            Tuple of (green element, hole group) or (None, None) if not found
        """
        hole_label = f"hole_{hole_number:02d}"
        green_id = f"green_{hole_number:02d}"

        # Search for hole group
        for element in root.iter():
            if isinstance(element, Group) and element.label == hole_label:
                # Found hole group, search for green element at top level
                # Greens are now at top level with ID green_XX (not in a subgroup)
                for child in element:
                    # Check for element with green ID
                    element_id = child.get('id')
                    if element_id and element_id == green_id:
                        return (child, element)
                    # Also check for green_XX_01, green_XX_02 pattern (multiple greens)
                    if element_id and element_id.startswith(green_id):
                        return (child, element)

        return (None, None)

    def _measure_green_via_temp_group(
        self,
        green_element: BaseElement,
        hole_group_transform: Transform,
        hole_num: int,
    ) -> Optional[SimpleBoundingBox]:
        """
        Measure green bounding box by temporarily moving to root-level group.

        Adapter method that calls the generic measure_elements_via_temp_group utility.

        Args:
            green_element: Green element to measure
            hole_group_transform: Transform from parent hole group
            hole_num: Hole number for logging

        Returns:
            SimpleBoundingBox or None if measurement fails
        """
        root = self.document.getroot()

        # Use generic utility function for measurement
        return measure_elements_via_temp_group(
            elements=[green_element],
            document_root=root,
            parent_transform=hole_group_transform,
            temp_group_id=f'_temp_green_measure_{hole_num:02d}'
        )

    def _position_and_scale_green(
        self,
        green_copy: BaseElement,
        hole_group_transform: Transform,
        hole_num: int,
    ) -> None:
        """
        Position and scale green element to fit target box.

        Strategy:
        1. Measure via temporary root-level group
        2. Calculate scale to fit target box with margin
        3. Apply scale transform
        4. Measure again to verify
        5. Translate to target center
        6. Apply stroke compensation

        Args:
            green_copy: Copied green element (not yet positioned)
            hole_group_transform: Transform from parent hole group
            hole_num: Hole number for logging
        """
        # Convert target box to user units
        target_x = self.svg.unittouu(f"{self.TARGET_BOX['x']}in")
        target_y = self.svg.unittouu(f"{self.TARGET_BOX['y']}in")
        target_width = self.svg.unittouu(f"{self.TARGET_BOX['width']}in")
        target_height = self.svg.unittouu(f"{self.TARGET_BOX['height']}in")

        # Apply hole group transform to the green copy first
        green_copy.transform = hole_group_transform @ green_copy.transform

        # Measure via temporary root-level group
        bbox = self._measure_green_via_temp_group(green_copy, Transform(), hole_num)
        if bbox is None:
            logger.warning("Could not measure bounding box for green %d", hole_num)
            return

        bbox_left, bbox_right, bbox_top, bbox_bottom = bbox.left, bbox.right, bbox.top, bbox.bottom
        bbox_width = bbox.width
        bbox_height = bbox.height

        # Calculate current center of the green (before scaling)
        current_center_x = (bbox_left + bbox_right) / 2.0
        current_center_y = (bbox_top + bbox_bottom) / 2.0

        # Calculate scale factors
        scale_x = target_width / bbox_width if bbox_width > 0 else 1.0
        scale_y = target_height / bbox_height if bbox_height > 0 else 1.0

        # Use minimum scale with edge buffer
        scale_factor = min(scale_x, scale_y) * self.GREEN_EDGE_BUFFER

        # Apply scale transform around measured center
        scale_transform = Transform(translate=(current_center_x, current_center_y))
        scale_transform @= Transform(scale=scale_factor)
        scale_transform @= Transform(translate=(-current_center_x, -current_center_y))

        green_copy.transform = scale_transform @ green_copy.transform

        # Measure scaled bbox
        scaled_bbox = self._measure_green_via_temp_group(green_copy, Transform(), hole_num)
        if scaled_bbox is None:
            logger.warning("Could not measure scaled bounding box for green %d", hole_num)
            return

        scaled_left, scaled_right, scaled_top, scaled_bottom = scaled_bbox.left, scaled_bbox.right, scaled_bbox.top, scaled_bbox.bottom
        scaled_center_x = (scaled_left + scaled_right) / 2.0
        scaled_center_y = (scaled_top + scaled_bottom) / 2.0

        # Translate to target center
        target_center_x = target_x + target_width / 2.0
        target_center_y = target_y + target_height / 2.0

        translate_x = target_center_x - scaled_center_x
        translate_y = target_center_y - scaled_center_y

        translate_transform = Transform(translate=(translate_x, translate_y))
        green_copy.transform = translate_transform @ green_copy.transform


if __name__ == '__main__':
    AutoPlaceHoles().run()
