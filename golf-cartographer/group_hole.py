#!/usr/bin/env python3
"""
Group Hole Tool - Stage 2 of Golf Yardage Book Extension Suite

This extension organizes selected elements into hierarchical hole groups with
color-based categorization. Creates:
  hole_XX/
    ├── other/ (uncategorized elements, terrain features)
    ├── bunkers/ (bunker elements #f5e8c5)
    ├── fairways/ (fairway elements #ccebb0)
    ├── green_XX (green elements directly at top level - #87debd)
    └── (yardage lines positioned above green)

Duplicates yardage line templates (assumes original is hidden), makes the clone
visible, and positions them at the center of each green.

Author: Golf Yardage Book Extension Suite
License: MIT
"""
from __future__ import annotations

import argparse
import logging
from typing import TYPE_CHECKING, List, Tuple, Optional

import inkex
from inkex import Group, PathElement, Transform, Defs, ClipPath, Rectangle

from color_utils import categorize_element_by_color

if TYPE_CHECKING:
    from inkex import BaseElement

# Configure module logger
logger = logging.getLogger(__name__)

# Type aliases
CanvasBounds = Tuple[float, float, float, float]  # (x_min, y_min, x_max, y_max)
Centroid = Tuple[float, float]  # (x, y)


class GroupHole(inkex.EffectExtension):
    """
    Groups selected elements into hierarchical hole structure based on colors.
    """

    def add_arguments(self, pars: argparse.ArgumentParser) -> None:
        """Add command-line arguments."""
        pars.add_argument("--hole_number", type=int, default=1,
                         help="Hole number (1-18)")
        pars.add_argument("--yardage_line_group", type=str, default="",
                         help="ID of yardage line group to duplicate")

    def effect(self) -> None:
        """
        Main execution method for the Group Hole Tool (Stage 2).

        Pipeline Context:
        This tool is the second stage in the yardage book creation pipeline, following
        the Flatten SVG Tool. It takes a user selection of elements representing a single
        hole and organizes them into a hierarchical structure suitable for subsequent
        processing stages.

        Execution Flow:
        1. Validate that elements are selected (user error if not)
        2. Analyze selected elements and categorize by color (reusing flatten_svg logic)
        3. Create hierarchical hole_XX group with:
           - other/ subgroup (uncategorized elements and root 'other' group copy)
           - bunkers/ subgroup (bunker elements #f5e8c5 - flat structure)
           - fairways/ subgroup (fairway elements #ccebb0)
           - Green elements directly at top level with ID green_XX (for later positioning)
           - Yardage lines positioned above green elements (top layer)
        4. Duplicate yardage line template (assumes template is hidden in document)
        5. Make cloned yardage lines visible (sets display:inline and visibility:visible)
        6. Calculate geometric centroid of green elements
        7. Position yardage line clone at green centroid (works regardless of template location)
        8. Copy contents from root-level 'other' group (water, trees, paths, mapping lines from Stage 1)
        9. Assign ID to green elements to reflect hole number (green_01, green_02, etc.)
        10. Add completed hole group to document root

        Iteration Pattern:
        This tool is designed to be run 18 times (once per hole), with the hole_number
        parameter incremented each time. Each execution creates a new hole_XX group.

        Green Element Positioning:
        Green elements are placed directly at the top level of the hole group (not in a
        subgroup) to allow later stages (especially Stage 4: Scale Greens) to easily
        locate and manipulate them individually.

        Yardage Line Positioning Strategy:
        The tool calculates the geometric centroid (true center) of green elements using
        the shoelace formula for accuracy. Yardage lines are positioned at this centroid
        by calculating the offset from the template's center and applying a translation.
        This approach allows the yardage line template to be positioned anywhere in the
        source SVG and still end up correctly positioned at the green center.
        """
        if not self.svg.selected:
            inkex.errormsg("Please select elements for the hole")
            return

        root = self.document.getroot()
        hole_num = self.options.hole_number

        # Create main hole group
        hole_group = Group()
        hole_group.label = f"hole_{hole_num:02d}"

        # Create subgroups
        fairways_group = Group()
        fairways_group.label = "fairways"

        bunkers_group = Group()
        bunkers_group.label = "bunkers"

        other_group = Group()
        other_group.label = "other"

        # Categorize selected elements using shared color utilities
        green_elements = []
        fairway_elements = []
        bunker_elements = []
        other_elements = []

        for element in self.svg.selected.values():
            category = categorize_element_by_color(element)

            if category == "green":
                green_elements.append(element)
            elif category == "fairway":
                fairway_elements.append(element)
            elif category == "bunker":
                bunker_elements.append(element)
            else:
                other_elements.append(element)

        # Populate fairways group
        for element in fairway_elements:
            fairways_group.append(element)

        # Populate bunkers group (flat, no subgroups)
        for element in bunker_elements:
            bunkers_group.append(element)

        # Handle yardage lines (template duplication and positioning)
        yardage_clone = None  # Will be set if yardage template is found
        yardage_template = self._find_yardage_template()
        if yardage_template is not None:
            # Clone yardage template group (assumes original is hidden in SVG)
            yardage_clone = yardage_template.copy()

            # Make the cloned yardage lines visible in this hole
            # (Original template group remains hidden for reuse in other holes)
            if yardage_clone.style is None:
                yardage_clone.style = inkex.Style()
            yardage_clone.style['display'] = 'inline'
            yardage_clone.style['visibility'] = 'visible'

            # Calculate green centroid and position yardage lines there
            if len(green_elements) > 0:
                # Get the true geometric centroid of green elements
                centroid = self._calculate_centroid(green_elements)

                # Get current position of yardage template
                template_bbox = yardage_clone.bounding_box()
                if template_bbox is not None:
                    # Calculate center of yardage template's bounding box
                    template_center_x = (template_bbox.left + template_bbox.right) / 2
                    template_center_y = (template_bbox.top + template_bbox.bottom) / 2

                    # Calculate offset needed to move template center to green centroid
                    # This calculation allows the template to be positioned anywhere
                    # in the SVG and still be positioned correctly at the green center
                    offset_x = centroid[0] - template_center_x
                    offset_y = centroid[1] - template_center_y

                    # Apply translation transform to move template
                    # The composition order (translate @ transform) ensures the template
                    # moves to the target position regardless of existing transforms
                    yardage_clone.transform = Transform(translate=(offset_x, offset_y)) @ yardage_clone.transform
                else:
                    # Fallback: if bounding box fails, translate directly to centroid
                    # (assumes template was originally at 0,0)
                    yardage_clone.transform = Transform(translate=centroid) @ yardage_clone.transform

            # Yardage lines will be added to hole_group above green elements (not to other_group)
            # This is done later after green elements are added

        # Add uncategorized elements to other group
        for element in other_elements:
            other_group.append(element)

        # Copy contents from root-level 'other' group (if it exists)
        # This includes water, trees, and paths from Stage 1
        # NOTE: Explicitly excludes 'mapping_lines' subgroup as these are layout guides
        # that should not be duplicated per hole
        root_other_group = self._find_root_other_group()
        if root_other_group is not None:
            # Clone children from the root 'other' group, excluding 'mapping_lines'
            for child in root_other_group:
                # Skip 'mapping_lines' subgroup (case-insensitive)
                if isinstance(child, Group):
                    child_label = child.label
                    if child_label and child_label.lower() == 'mapping_lines':
                        continue  # Skip this child

                # Copy all other children
                child_clone = child.copy()
                other_group.append(child_clone)

        # Assemble hole group with correct z-order (bottom to top in DOM):
        # other → bunkers → fairways → green_XX → yardage_lines
        # This order ensures yardage lines render on top of all elements, and allows
        # terrain mask insertion between 'other' and 'bunkers' in Stage 4.

        # Add subgroups first (bottom layers)
        if len(other_group) > 0:
            hole_group.append(other_group)
        if len(bunkers_group) > 0:
            hole_group.append(bunkers_group)
        if len(fairways_group) > 0:
            hole_group.append(fairways_group)

        # Green elements go directly at top level of hole group (not in subgroup)
        # This allows Stage 4 (Scale Greens Tool) to easily locate them via XPath queries
        for i, element in enumerate(green_elements):
            # Assign ID based on hole number for later identification
            # Standard format: green_XX (e.g., green_01, green_02, etc.)
            element.set('id', f"green_{hole_num:02d}")

            # If multiple green elements exist for this hole (rare but possible),
            # append an index to distinguish them (e.g., green_01_01, green_01_02)
            if len(green_elements) > 1:
                element.set('id', f"green_{hole_num:02d}_{i+1:02d}")

            # Append green element directly to hole group (top layer)
            hole_group.append(element)

        # Add yardage lines above green elements (top-most layer)
        # This ensures yardage lines render on top of all other hole elements
        if yardage_clone is not None:
            hole_group.append(yardage_clone)

        # Apply canvas clipping to hole group (matches Stage 1 behavior)
        canvas_bounds = self._get_canvas_bounds()
        self._ensure_canvas_clip(root, canvas_bounds)
        hole_group.set('clip-path', 'url(#canvas-clip)')

        # Add hole group to document
        root.append(hole_group)

    def _get_canvas_bounds(self) -> CanvasBounds:
        """
        Get canvas boundaries from document viewBox or width/height attributes.

        Canvas bounds are determined in the following order of preference:
        1. viewBox attribute (most reliable for coordinate system)
        2. width/height attributes (fallback if viewBox not present)
        3. Default 1000x1000 (last resort)

        The viewBox approach is preferred because it directly defines the coordinate
        system for the entire document, whereas width/height may be in different units.

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

    def _ensure_canvas_clip(
        self,
        root: inkex.SvgDocumentElement,
        canvas_bounds: CanvasBounds,
    ) -> None:
        """
        Create clipping path to keep elements within canvas bounds.

        This method ensures that a canvas clipping path exists in the document.
        If the clipPath element with ID 'canvas-clip' already exists (from Stage 1),
        it will be reused. Otherwise, a new one is created.

        Clipping Strategy:
        The clip path is a rectangle matching the canvas bounds, ensuring that any
        elements extending beyond the canvas are visually clipped.

        Args:
            root: SVG root element
            canvas_bounds: tuple (x_min, y_min, x_max, y_max)

        Side Effects:
            - May modify root element's defs section if clip path doesn't exist
        """
        x_min, y_min, x_max, y_max = canvas_bounds

        # Get or create defs section (where clipPath elements belong)
        defs = root.find('.//{http://www.w3.org/2000/svg}defs')
        if defs is None:
            defs = Defs()
            root.insert(0, defs)

        # Check if canvas-clip already exists (from Stage 1 or previous holes)
        existing_clip = root.find('.//{http://www.w3.org/2000/svg}clipPath[@id="canvas-clip"]')
        if existing_clip is not None:
            # Clip path already exists, reuse it
            return

        # Create new clip path element
        clip_path = ClipPath()
        clip_path.set('id', 'canvas-clip')

        # Create rectangle that matches canvas bounds (clipping region)
        rect = Rectangle()
        rect.set('x', str(x_min))
        rect.set('y', str(y_min))
        rect.set('width', str(x_max - x_min))
        rect.set('height', str(y_max - y_min))

        clip_path.append(rect)
        defs.append(clip_path)

    def _find_yardage_template(self) -> Optional[Group]:
        """
        Find yardage line template group.

        Returns:
            Group or None: Yardage line template group if found
        """
        # Try to find by provided ID
        if self.options.yardage_line_group:
            element = self.svg.getElementById(self.options.yardage_line_group)
            if element is not None:
                return element

        # Try to find by label
        root = self.document.getroot()
        for element in root.iter():
            if isinstance(element, Group):
                label = element.label
                if label and 'yardage' in label.lower():
                    return element

        # No yardage template found
        inkex.errormsg("Yardage line template not found. Continuing without yardage lines.")
        return None

    def _find_root_other_group(self) -> Optional[Group]:
        """
        Find the root-level 'other' group created by Stage 1 (Flatten SVG Tool).

        This group typically contains:
        - other/mapping_lines/ - Hole mapping lines
        - other/paths/ - Cart/walking paths
        - other/water/ - Water feature paths
        - other/trees/ - Tree/grass elements

        Returns:
            Group or None: Root-level 'other' group if found
        """
        root = self.document.getroot()

        # Search direct children of root for a group labeled 'other'
        for child in root:
            if isinstance(child, Group):
                label = child.label
                if label and label.lower() == 'other':
                    return child

        # No root-level 'other' group found - this is okay if Stage 1 wasn't run
        # or if there were no 'other' elements to categorize
        return None

    def _calculate_centroid(self, elements: List[BaseElement]) -> Centroid:
        """
        Calculate true geometric centroid using polygon shoelace formula.

        Centroid Calculation Strategy:
        This method implements a three-level fallback approach for maximum robustness:

        Level 1: Polygon Centroid (Shoelace Formula) - Preferred for regular shapes
        =========================================================================
        The shoelace formula calculates the geometric centroid of an irregular polygon
        by treating all vertices equally. This is MORE ACCURATE than bounding box centers
        for non-rectangular shapes like golf course greens (kidney beans, dog-legs, etc.).

        Mathematical Formula:
        The centroid (Cx, Cy) of a polygon with vertices (x_i, y_i) is calculated as:

            Area = 1/2 * Σ(x_i * y_i+1 - x_i+1 * y_i)

            Cx = 1/(6 * Area) * Σ((x_i + x_i+1) * (x_i * y_i+1 - x_i+1 * y_i))
            Cy = 1/(6 * Area) * Σ((y_i + y_i+1) * (x_i * y_i+1 - x_i+1 * y_i))

        where the sum is over all polygon edges, and vertices wrap around (vertex n+1 = vertex 0).

        The cross product (x_i * y_i+1 - x_i+1 * y_i) represents twice the signed area of
        the triangle formed by the origin and the edge from vertex i to i+1.

        Algorithm Implementation:
        1. Extract all path vertices from green elements
        2. Iterate through consecutive vertex pairs (closing the polygon)
        3. Calculate cross product for each edge
        4. Accumulate area and centroid components
        5. Divide by accumulated area to get final centroid

        Level 2: Simple Vertex Average - For degenerate polygons
        =======================================================
        If the shoelace formula produces an area < 0.0001 (essentially zero or self-intersecting),
        fall back to simple arithmetic mean of all vertices. This handles edge cases where:
        - Polygon has zero area (line or point)
        - Path coordinates are numerical errors
        - Polygon is self-intersecting

        Level 3: Bounding Box Center - For non-path elements
        ===================================================
        If vertex extraction fails or elements are not paths, calculate bounding box
        center for each element and average them. This is less accurate but works
        for rectangles, circles, and other closed shapes.

        Args:
            elements: List of SVG elements (expected to be green shapes)

        Returns:
            tuple: (x, y) coordinates of the geometric centroid

        Accuracy Notes:
        - Shoelace method: Most accurate for irregular polygons (kidney bean greens)
        - Simple average: Reasonable for small deviations or vertex clouds
        - Bounding box: Acceptable for regular shapes but may be off-center for kidney beans
        """
        all_points = []

        # Level 1: Try to extract vertices from path elements
        for element in elements:
            try:
                if isinstance(element, inkex.PathElement):
                    path = element.path.to_absolute()

                    # Extract vertices from path - collect all endpoint coordinates
                    for segment in path:
                        # Different segment types store endpoints differently
                        if hasattr(segment, 'x') and hasattr(segment, 'y'):
                            # Direct x,y attributes (most common)
                            all_points.append((float(segment.x), float(segment.y)))
            except (AttributeError, TypeError, ValueError) as e:
                # Skip elements that can't be parsed (non-path or corrupted)
                logger.debug(
                    "Could not extract path vertices from element %s: %s",
                    element.get('id', 'unknown'),
                    e,
                )

        # If we successfully extracted 3+ vertices, use shoelace formula
        if len(all_points) >= 3:
            try:
                # Shoelace formula for polygon centroid
                area = 0.0
                cx = 0.0
                cy = 0.0

                # Sum over all edges (closing the polygon by wrapping around)
                for i in range(len(all_points)):
                    x1, y1 = all_points[i]
                    x2, y2 = all_points[(i + 1) % len(all_points)]

                    # Calculate cross product (signed area of triangle with origin)
                    cross = x1 * y2 - x2 * y1
                    area += cross
                    cx += (x1 + x2) * cross
                    cy += (y1 + y2) * cross

                # Divide area by 2 to get actual area
                area /= 2.0

                # Avoid division by zero for degenerate polygons
                if abs(area) > 0.0001:
                    cx = cx / (6.0 * area)
                    cy = cy / (6.0 * area)
                    return (cx, cy)
                else:
                    # Area is too small - polygon is degenerate (line or point)
                    # Fall back to simple arithmetic mean of vertices
                    cx = sum(p[0] for p in all_points) / len(all_points)
                    cy = sum(p[1] for p in all_points) / len(all_points)
                    return (cx, cy)
            except (ZeroDivisionError, ArithmeticError) as e:
                # Shoelace calculation failed - continue to fallback
                logger.debug("Shoelace centroid calculation failed: %s", e)

        # Level 3: Fallback to bounding box center averaging
        # (Used for non-path elements or if vertex extraction failed)
        total_x = 0.0
        total_y = 0.0
        count = 0

        for element in elements:
            try:
                bbox = element.bounding_box()
                if bbox is not None:
                    # Calculate bounding box center
                    center_x = (bbox.left + bbox.right) / 2.0
                    center_y = (bbox.top + bbox.bottom) / 2.0
                    total_x += center_x
                    total_y += center_y
                    count += 1
            except (AttributeError, TypeError, ValueError) as e:
                logger.debug(
                    "Could not calculate bounding box for element %s: %s",
                    element.get('id', 'unknown'),
                    e,
                )

        if count == 0:
            # No elements could be processed - return origin
            return (0, 0)

        # Return average of bounding box centers
        return (total_x / count, total_y / count)


if __name__ == '__main__':
    GroupHole().run()
