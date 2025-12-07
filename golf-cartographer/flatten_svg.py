#!/usr/bin/env python3
"""
Flatten SVG Tool - Stage 1 of Golf Yardage Book Extension Suite

This extension flattens nested SVG groups by moving all elements to the top level
of the document hierarchy. It organizes greens, fairways, bunkers, mapping lines,
paths, water, and tree/grass elements into structured groups while removing empty
groups, uncategorized elements, and off-canvas elements. Applies clipping to keep
all elements within canvas bounds.

Author: Golf Yardage Book Extension Suite
License: MIT
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Tuple, Optional

import inkex

from color_utils import categorize_element_by_color

if TYPE_CHECKING:
    from inkex import BaseElement
    from inkex.transforms import BoundingBox

# Configure module logger
logger = logging.getLogger(__name__)

# Type aliases
CanvasBounds = Tuple[float, float, float, float]  # (x_min, y_min, x_max, y_max)
ElementWithTransform = Tuple["BaseElement", Optional[inkex.Transform]]


class FlattenSVG(inkex.EffectExtension):
    """
    Flattens SVG structure by moving all elements to document root level
    and organizing them into appropriate groups.
    """

    def effect(self) -> None:
        """
        Main execution method for the extension.
        """
        root = self.document.getroot()

        # Collect all elements to flatten (excluding root-level elements initially)
        elements_to_flatten = []
        groups_to_remove = []

        # First pass: collect all path elements from nested groups
        self._collect_elements(root, elements_to_flatten, groups_to_remove)

        # Get canvas dimensions from viewBox or width/height
        canvas_bounds = self._get_canvas_bounds()

        # Filter out elements completely off-canvas before categorization
        elements_to_flatten = self._filter_offcanvas_elements(elements_to_flatten, canvas_bounds)

        # Create organizational structure
        other_group = inkex.Group()
        other_group.label = "other"

        trees_group = inkex.Group()
        trees_group.label = "trees"

        water_group = inkex.Group()
        water_group.label = "water"

        paths_group = inkex.Group()
        paths_group.label = "paths"

        mapping_lines_group = inkex.Group()
        mapping_lines_group.label = "mapping_lines"

        # Root-level groups for golf course elements
        greens_group = inkex.Group()
        greens_group.label = "greens"

        fairways_group = inkex.Group()
        fairways_group.label = "fairways"

        bunkers_group = inkex.Group()
        bunkers_group.label = "bunkers"

        # Sort elements into appropriate groups (delete uncategorized)
        elements_to_delete = []
        for element, accumulated_transform in elements_to_flatten:
            # Apply accumulated transform to element
            if accumulated_transform is not None and accumulated_transform != inkex.Transform():
                # Compose with existing transform
                element.transform = accumulated_transform @ element.transform

            # Categorize element using shared color utilities
            category = categorize_element_by_color(element)
            is_path = False

            if category == "mapping_line":
                mapping_lines_group.append(element)
            elif category == "path_line":
                paths_group.append(element)
                is_path = True  # Don't apply stroke to paths
            elif category == "green":
                greens_group.append(element)
            elif category == "fairway":
                fairways_group.append(element)
            elif category == "bunker":
                bunkers_group.append(element)
            elif category == "water":
                water_group.append(element)
            elif category == "tree":
                trees_group.append(element)
            else:
                # Mark element for deletion (uncategorized)
                elements_to_delete.append(element)
                continue

            # Apply 1px stroke to all categorized elements except paths
            if not is_path:
                self._apply_stroke(element)

        # Delete uncategorized elements
        for element in elements_to_delete:
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)

        # Add root-level groups
        if len(greens_group) > 0:
            root.append(greens_group)
        if len(fairways_group) > 0:
            root.append(fairways_group)
        if len(bunkers_group) > 0:
            root.append(bunkers_group)

        # Only add subgroups to 'other' if they contain elements
        if len(trees_group) > 0:
            other_group.append(trees_group)
        if len(water_group) > 0:
            other_group.append(water_group)
        if len(paths_group) > 0:
            other_group.append(paths_group)
        if len(mapping_lines_group) > 0:
            other_group.append(mapping_lines_group)

        # Only add other group if it has subgroups
        if len(other_group) > 0:
            root.append(other_group)

        # Apply clipping path to keep all elements within canvas bounds
        self._apply_canvas_clipping(root, canvas_bounds)

        # Remove empty groups (in reverse to avoid index issues)
        for group in reversed(groups_to_remove):
            parent = group.getparent()
            if parent is not None and len(group) == 0:
                parent.remove(group)

        # Clean up any remaining empty groups at root level
        for child in list(root):
            if isinstance(child, inkex.Group) and len(child) == 0:
                root.remove(child)

    def _collect_elements(
        self,
        parent: BaseElement,
        elements_list: List[ElementWithTransform],
        groups_list: List[inkex.Group],
        accumulated_transform: Optional[inkex.Transform] = None,
    ) -> None:
        """
        Recursively collect elements from nested groups.
        """
        # Process children (iterate over a copy to avoid modification during iteration)
        for child in list(parent):
            if isinstance(child, inkex.Group):
                # Calculate accumulated transform for this group
                current_transform = accumulated_transform
                if current_transform is None:
                    current_transform = child.transform
                else:
                    current_transform = current_transform @ child.transform

                # Recursively process group contents
                self._collect_elements(child, elements_list, groups_list, current_transform)

                # Mark group for removal
                groups_list.append(child)

            elif isinstance(child, (inkex.PathElement, inkex.ShapeElement)):
                # Add element with its accumulated transform
                elements_list.append((child, accumulated_transform))

    def _apply_stroke(self, element: BaseElement) -> None:
        """
        Apply 1px black stroke to element for visual clarity.

        Args:
            element: SVG element to apply stroke to
        """
        if element.style is None:
            element.style = inkex.Style()

        element.style['stroke'] = '#000000'        # Black stroke
        element.style['stroke-width'] = '1px'      # 1 pixel width
        element.style['stroke-opacity'] = '1'      # Full opacity

    def _get_canvas_bounds(self) -> CanvasBounds:
        """
        Get canvas boundaries from document viewBox or width/height attributes.

        Returns:
            tuple: (x_min, y_min, x_max, y_max) canvas bounds in document units
        """
        root = self.document.getroot()

        # Try to get viewBox first (most reliable approach)
        viewbox = root.get('viewBox')
        if viewbox:
            parts = viewbox.strip().split()
            if len(parts) == 4:
                x, y, w, h = map(float, parts)
                return (x, y, x + w, y + h)

        # Fall back to width/height attributes if viewBox not present
        width = root.get('width')
        height = root.get('height')
        if width and height:
            # Convert to user units (handles units like '100px', '10in', etc.)
            w = self.svg.unittouu(width)
            h = self.svg.unittouu(height)
            return (0, 0, w, h)

        # Default fallback (usually only reached for malformed SVG)
        return (0, 0, 1000, 1000)

    def _filter_offcanvas_elements(
        self,
        elements_list: List[ElementWithTransform],
        canvas_bounds: CanvasBounds,
    ) -> List[ElementWithTransform]:
        """
        Filter out elements completely off-canvas from the collection.
        """
        x_min, y_min, x_max, y_max = canvas_bounds
        filtered_elements = []

        for element, accumulated_transform in elements_list:
            try:
                bbox = element.bounding_box()
                if bbox is not None:
                    # Check if element bounding box intersects with canvas bounds
                    # Element is off-canvas if it doesn't intersect in either dimension
                    if not (bbox.right < x_min or bbox.left > x_max or
                            bbox.bottom < y_min or bbox.top > y_max):
                        # Element is at least partially on canvas, keep it
                        filtered_elements.append((element, accumulated_transform))
                    else:
                        # Element is completely off-canvas, remove it immediately
                        parent = element.getparent()
                        if parent is not None:
                            parent.remove(element)
                else:
                    # Can't determine bounds, keep element (safe default)
                    filtered_elements.append((element, accumulated_transform))
            except (AttributeError, TypeError, ValueError) as e:
                # Skip elements that can't calculate bounding box, but keep them
                # (safe default to avoid losing data)
                logger.debug(
                    "Could not calculate bounding box for element %s: %s",
                    element.get('id', 'unknown'),
                    e,
                )
                filtered_elements.append((element, accumulated_transform))

        return filtered_elements

    def _apply_canvas_clipping(self, root: inkex.SvgDocumentElement, canvas_bounds: CanvasBounds) -> None:
        """
        Create and apply clipping path to keep elements within canvas bounds.

        Args:
            root: SVG root element
            canvas_bounds: tuple (x_min, y_min, x_max, y_max)

        Side Effects:
            - Modifies root element's defs section
            - Adds clip-path attribute to all root-level groups
        """
        x_min, y_min, x_max, y_max = canvas_bounds

        # Get or create defs section (where clipPath elements belong)
        defs = root.find('.//{http://www.w3.org/2000/svg}defs')
        if defs is None:
            defs = inkex.Defs()
            root.insert(0, defs)

        # Create clip path element
        clip_path = inkex.ClipPath()
        clip_path.set('id', 'canvas-clip')

        # Create rectangle that matches canvas bounds (clipping region)
        rect = inkex.Rectangle()
        rect.set('x', str(x_min))
        rect.set('y', str(y_min))
        rect.set('width', str(x_max - x_min))
        rect.set('height', str(y_max - y_min))

        clip_path.append(rect)
        defs.append(clip_path)

        # Apply clip path to all root-level groups (golf course elements)
        for child in root:
            if isinstance(child, inkex.Group):
                child.set('clip-path', 'url(#canvas-clip)')


if __name__ == '__main__':
    FlattenSVG().run()
