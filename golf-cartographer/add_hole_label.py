#!/usr/bin/env python3
"""
Add Hole Label Tool - Stage 4 of Golf Cartographer Extension Suite

This extension adds hole number circles, par text, and tee box yardages to positioned holes.
Creates visual labels with customizable fonts and supports up to 6 tee boxes per course.

Stage 4 - Hole Labeling:
- Creates circle at fixed page coordinates (top-right area)
- Adds hole number text centered in circle
- Adds par text below circle
- Adds tee box yardages in bottom-right corner (optional, up to 6 tees)
- Groups all elements with inverse transforms for consistent positioning

Pipeline Context:
- Input: SVG with positioned holes (output from Tool #3 / Stage 3)
- Output: Holes with visual labels (hole number + par + tee yardages)
- Next Stage: Tool #5 will export PDFs

Author: Golf Cartographer Extension Suite
License: MIT
"""
from __future__ import annotations

import argparse
import logging
from typing import Optional

import inkex
from inkex import Circle, TextElement, Tspan, Group, Style, Transform

from glyph_library import GlyphLibrary

# Configure module logger
logger = logging.getLogger(__name__)


class AddHoleLabel(inkex.EffectExtension):
    """
    Adds hole number, par labels, and tee box yardages to yardage book pages.

    This tool is designed to be run 18 times (once per hole), similar to the
    Group Hole tool. Each execution creates:
    - Label group (nested in hole group with inverse transform):
      - Circle element at fixed page coordinates (top-right)
      - Hole number text centered in the circle
      - Par text positioned below the circle
    - Tee yardages group (added to document root):
      - Tee box yardages in bottom-right corner (optional, up to 6 tees)

    The labels use inverse transforms to maintain fixed positions despite being
    nested in transformed hole groups. Tee yardages are added directly to root
    for simpler positioning.
    """

    # Consistent margin from bounding box edges for all positioned elements
    BOUNDING_BOX_MARGIN: float = 0.092  # inches - standard margin for circle badge and tee yardages

    # Fixed position for hole label circle (top-right area of page)
    # Top area from auto_place_holes.py BOUNDING_BOX: x=0.257", y=0.247", w=3.736", h=6.756"
    # Top-right corner: (0.257 + 3.736, 0.247) = (3.993", 0.247")
    # Coordinates define the bounding box upper-left corner with margin applied
    # (Circle centers are calculated from this + radius offset)
    CIRCLE_DIAMETER: float = 0.506  # inches
    CIRCLE_BBOX_UL_X: float = 3.993 - CIRCLE_DIAMETER - BOUNDING_BOX_MARGIN  # 3.395" inches
    CIRCLE_BBOX_UL_Y: float = 0.247 + BOUNDING_BOX_MARGIN  # 0.339" inches

    # Calculate circle center from bounding box upper-left
    CIRCLE_CENTER_X: float = CIRCLE_BBOX_UL_X + (CIRCLE_DIAMETER / 2)  # 3.648"
    CIRCLE_CENTER_Y: float = CIRCLE_BBOX_UL_Y + (CIRCLE_DIAMETER / 2)  # 0.592"

    # Text positioning
    PAR_TEXT_OFFSET: float = 0.1  # inches below circle
    PAR_TEXT_FONT_SIZE: int = 4  # Fixed font size for par text in points

    # Tee box yardage positioning (anchored to lower right of top area)
    # Lower right corner: (0.257 + 3.736, 0.247 + 6.756) = (3.993", 7.003")
    # Three-element layout: name (right-aligned) : yardage (left-aligned)
    TEE_YARDAGE_ANCHOR_X: float = 3.993 - BOUNDING_BOX_MARGIN  # inches - 0.092" padding from right edge = 3.901"
    TEE_YARDAGE_ANCHOR_Y: float = 7.003 - BOUNDING_BOX_MARGIN  # inches - 0.092" padding from bottom = 6.911"
    TEE_YARDAGE_FONT_SIZE: int = 5  # points
    TEE_YARDAGE_ELEMENT_SPACING: float = 5.0  # user units - horizontal space between name, colon, yardage
    TEE_YARDAGE_LINE_SPACING: float = 5.0  # user units - vertical space between tee lines

    def add_arguments(self, pars: argparse.ArgumentParser) -> None:
        """Add command-line arguments."""
        pars.add_argument("--notebook", type=str, default="label",
                         help="Active notebook tab")
        pars.add_argument("--hole_number", type=int, default=1,
                         help="Hole number (1-18)")
        pars.add_argument("--par", type=int, default=4,
                         help="Par value (3-6)")
        # Tee box yardages (6 tee boxes supported)
        pars.add_argument("--tee1_name", type=str, default="Red",
                         help="Tee box 1 name")
        pars.add_argument("--tee1_yardage", type=int, default=0,
                         help="Tee box 1 yardage")
        pars.add_argument("--tee2_name", type=str, default="White",
                         help="Tee box 2 name")
        pars.add_argument("--tee2_yardage", type=int, default=0,
                         help="Tee box 2 yardage")
        pars.add_argument("--tee3_name", type=str, default="Blue",
                         help="Tee box 3 name")
        pars.add_argument("--tee3_yardage", type=int, default=0,
                         help="Tee box 3 yardage")
        pars.add_argument("--tee4_name", type=str, default="Gold",
                         help="Tee box 4 name")
        pars.add_argument("--tee4_yardage", type=int, default=0,
                         help="Tee box 4 yardage")
        pars.add_argument("--tee5_name", type=str, default="Black",
                         help="Tee box 5 name")
        pars.add_argument("--tee5_yardage", type=int, default=0,
                         help="Tee box 5 yardage")
        pars.add_argument("--tee6_name", type=str, default="Green",
                         help="Tee box 6 name")
        pars.add_argument("--tee6_yardage", type=int, default=0,
                         help="Tee box 6 yardage")
        # Spacing options
        pars.add_argument("--element_spacing", type=int, default=5,
                         help="Horizontal spacing between elements (user units/px)")
        pars.add_argument("--line_spacing", type=int, default=5,
                         help="Vertical spacing between tee lines (user units/px)")
        pars.add_argument("--font_size", type=int, default=6,
                         help="Font size in points")
        pars.add_argument("--font_weight", type=str, default="bold",
                         help="Font weight (bold or normal)")
        pars.add_argument("--font_family", type=str, default="JetBrainsMono Nerd Font",
                         help="Glyph library font name (without .svg extension)")

    def effect(self) -> None:
        """
        Main execution method for Add Hole Label Tool.

        Execution Flow:
        1. Check if we're on the "List Fonts" tab - if so, show available fonts and exit
        2. Validate parameters (hole number, par, font size)
        3. Load glyph library for accurate text measurements
        4. Validate that hole group exists (from Stage 3)
        5. Check for duplicate labels (remove if exists)
        6. Create label group with circle and text elements
        7. Add label group to hole group with inverse transform
        8. Create and add tee yardages to document root (if specified)

        Validation ensures Stage 3 (Auto-Place Holes) has been run before
        attempting to add labels.
        """
        # Check which tab is active
        if self.options.notebook == "list_fonts":
            self.show_available_fonts()
            return  # Exit after showing fonts

        root = self.document.getroot()
        hole_num = self.options.hole_number
        par = self.options.par

        # Load glyph library for accurate text measurements
        import os
        font_name = self.options.font_family.strip()
        library_path = os.path.join(
            os.path.dirname(__file__),
            'glyph_libraries',
            f'{font_name}.svg'
        )

        # Check if library file exists
        if not os.path.exists(library_path):
            logger.error("Glyph library not found: %s", library_path)
            inkex.errormsg(f"Error: Glyph library font '{font_name}' not found!")
            inkex.errormsg(f"Expected file: {library_path}")
            inkex.errormsg("")
            inkex.errormsg("Use the 'List Fonts' tab to see available fonts.")
            return

        try:
            self.glyph_library = GlyphLibrary(library_path)
            logger.info("Loaded glyph library from: %s", library_path)
        except Exception as e:
            logger.error("Failed to load glyph library: %s", e)
            inkex.errormsg(f"Error: Could not load glyph library: {e}")
            inkex.errormsg("")
            inkex.errormsg(f"Font: {font_name}")
            inkex.errormsg(f"Path: {library_path}")
            return

        # Parameter validation
        if not 1 <= hole_num <= 18:
            logger.error("Invalid hole number: %d (must be 1-18)", hole_num)
            inkex.errormsg(f"Error: Hole number must be 1-18, got {hole_num}")
            return

        if not 3 <= par <= 6:
            logger.error("Invalid par value: %d (must be 3-6)", par)
            inkex.errormsg(f"Error: Par must be 3-6, got {par}")
            return

        if not 4 <= self.options.font_size <= 72:
            logger.error("Invalid font size: %d (must be 4-72pt)", self.options.font_size)
            inkex.errormsg(f"Error: Font size must be 4-72pt, got {self.options.font_size}")
            return

        # Validation: Check if hole_XX group exists
        hole_id = f"hole_{hole_num:02d}"
        hole_group = self._find_hole_group(root, hole_id)

        if hole_group is None:
            logger.warning("Hole %d group not found. Cannot create label.", hole_num)
            inkex.errormsg(
                f"Error: Hole {hole_num} group not found. "
                f"Please run Stage 3 (Auto-Place Holes) before adding labels."
            )
            return

        # Remove existing label if present (prevents duplicate IDs)
        label_id = f"hole_label_{hole_num:02d}"
        existing_label = root.getElementById(label_id)

        if existing_label is not None:
            logger.info("Removing existing label for hole %d", hole_num)
            parent = existing_label.getparent()
            if parent is not None:
                parent.remove(existing_label)

        # Create and add label group
        label_group = self._create_hole_label_group(hole_num, par)
        if label_group is None:
            logger.error("Failed to create label group for hole %d", hole_num)
            return

        # Apply inverse transform so label appears at fixed position despite being nested in hole group
        # The hole group has transforms (rotation, scaling, position) from Stage 3
        # We need to cancel those out so the label stays at the fixed page coordinates
        hole_transform = hole_group.composed_transform()
        if hole_transform:
            inverse_transform = -hole_transform
            label_group.transform = inverse_transform
            logger.info("Applied inverse transform to label for hole %d", hole_num)

        # Add label to the hole group (not root) so it's nested properly
        hole_group.append(label_group)
        logger.info("Successfully added label for hole %d (par %d) to hole group", hole_num, par)

        # Create and add tee yardages to root (separate from hole group)
        tee_yardages = self._create_tee_yardages(hole_num)
        if tee_yardages is not None:
            # Remove existing tee yardages if present
            tee_id = f'tee_yardages_{hole_num:02d}'
            existing_tee = root.getElementById(tee_id)
            if existing_tee is not None:
                logger.info("Removing existing tee yardages for hole %d", hole_num)
                tee_parent = existing_tee.getparent()
                if tee_parent is not None:
                    tee_parent.remove(existing_tee)

            # Add tee yardages to root (no inverse transform needed)
            root.append(tee_yardages)
            logger.info("Successfully added tee yardages for hole %d to root", hole_num)

    def _find_hole_group(self, root: inkex.SvgDocumentElement, hole_id: str) -> Optional[Group]:
        """
        Find hole group by ID or label.

        Searches for hole groups created by Stage 2 (Group Hole) and positioned
        by Stage 3 (Auto-Place Holes). Tries ID lookup first, then falls back to
        label-based search.

        Args:
            root: SVG document root element
            hole_id: Hole identifier (e.g., "hole_01")

        Returns:
            Hole group if found, None otherwise
        """
        # Try by ID first (most reliable)
        element = root.getElementById(hole_id)
        if element is not None and isinstance(element, Group):
            return element

        # Try by label (fallback for inconsistent IDs)
        for elem in root.iter():
            if isinstance(elem, Group):
                label = elem.label
                if label and label.lower() == hole_id.lower():
                    return elem

        return None

    def _create_hole_label_group(self, hole_num: int, par: int) -> Optional[Group]:
        """
        Create hole label group with circle and text elements.

        Creates a grouped structure containing:
        - Circle element at fixed page position (top-right)
        - Hole number text centered in circle
        - Par text positioned below circle

        Note: Tee box yardages are created separately and added to document root.

        All elements use the same coordinate system (document root), so they
        appear at consistent positions across all pages when exported to PDF.

        Args:
            hole_num: Hole number (1-18)
            par: Par value (3-6)

        Returns:
            Group containing circle and text elements, or None if conversion fails
        """
        # Create group
        label_group = Group()
        label_group.set('id', f'hole_label_{hole_num:02d}')
        label_group.label = f'hole_label_{hole_num:02d}'

        # Convert positions from inches to user units with error handling
        try:
            cx_uu = self.svg.unittouu(f"{self.CIRCLE_CENTER_X}in")
            cy_uu = self.svg.unittouu(f"{self.CIRCLE_CENTER_Y}in")
            radius_uu = self.svg.unittouu(f"{self.CIRCLE_DIAMETER / 2}in")
        except (ValueError, AttributeError) as e:
            logger.error("Failed to convert units: %s", e)
            inkex.errormsg(f"Error: Unit conversion failed: {e}")
            return None

        # Create circle
        circle = self._create_circle(cx_uu, cy_uu, radius_uu)

        # Create hole number text and center it in the circle
        hole_number_text = self._create_centered_hole_number(hole_num, cx_uu, cy_uu)

        # Create par text
        par_text = self._create_par_text(par, cx_uu, cy_uu, radius_uu)

        # Assemble group
        label_group.append(circle)
        label_group.append(hole_number_text)
        label_group.append(par_text)

        return label_group

    def _create_circle(self, cx_uu: float, cy_uu: float, radius_uu: float) -> Circle:
        """
        Create circle element with black stroke and no fill.

        Args:
            cx_uu: Circle center X in user units
            cy_uu: Circle center Y in user units
            radius_uu: Circle radius in user units

        Returns:
            Circle element with 0.5px black stroke
        """
        circle = Circle(cx=str(cx_uu), cy=str(cy_uu), r=str(radius_uu))
        circle.style = Style({
            'fill': 'none',
            'stroke': '#000000',
            'stroke-width': '0.5px'  # 50% of original 1px stroke
        })
        return circle

    def _create_centered_hole_number(self, hole_num: int, circle_cx: float, circle_cy: float) -> Group:
        """
        Create hole number as glyph-based text and center it precisely in the circle.

        Uses GlyphLibrary for accurate measurements and positioning. Calculates the
        position offset to center the text bounding box within the circle.

        Args:
            hole_num: Hole number (1-18)
            circle_cx: Circle center X in user units
            circle_cy: Circle center Y in user units

        Returns:
            Group containing glyph paths for hole number, centered in circle
        """
        logger.info("Creating centered hole number %d at circle center (%.2f, %.2f)",
                   hole_num, circle_cx, circle_cy)

        # Compose text using glyph library to get accurate dimensions
        # Note: We'll position at (0, 0) first to get dimensions, then reposition
        text_group, width, height = self.glyph_library.compose_text(
            str(hole_num),
            x=0,
            y=0,
            font_size=self.options.font_size,
            spacing=0  # No extra spacing for single/double digit numbers
        )

        # Calculate position to center the text bounding box in the circle
        # Text is positioned by bottom-left corner, so:
        # - Horizontal centering: x = circle_cx - (width / 2)
        # - Vertical centering: y = circle_cy + (height / 2)
        centered_x = circle_cx - (width / 2)
        centered_y = circle_cy + (height / 2)

        logger.info("Text dimensions: %.2f × %.2f mm, centered at (%.2f, %.2f)",
                   width, height, centered_x, centered_y)

        # Recompose at the centered position
        text_group, width, height = self.glyph_library.compose_text(
            str(hole_num),
            x=centered_x,
            y=centered_y,
            font_size=self.options.font_size,
            spacing=0
        )

        logger.info("Successfully created centered hole number %d with glyph library", hole_num)

        return text_group

    def _create_par_text(self, par: int, cx_uu: float, cy_uu: float, radius_uu: float) -> Group:
        """
        Create par text positioned below circle.

        Text is positioned with a small offset below the circle's bottom edge
        and uses a fixed smaller font size for visual hierarchy.

        Args:
            par: Par value (3-6)
            cx_uu: Circle center X in user units
            cy_uu: Circle center Y in user units
            radius_uu: Circle radius in user units

        Returns:
            Group containing glyph paths for par text
        """
        # First compose to get dimensions for centering
        text_group, width, height = self.glyph_library.compose_text(
            str(par),
            x=0,
            y=0,
            font_size=self.PAR_TEXT_FONT_SIZE,
            spacing=0
        )

        # Position below circle with offset
        offset_uu = self.svg.unittouu(f"{self.PAR_TEXT_OFFSET}in")
        # Center horizontally under the circle
        text_x = cx_uu - (width / 2)
        # Position below circle bottom edge + offset (use bottom-left positioning)
        text_y = cy_uu + radius_uu + offset_uu

        # Recompose at final position
        text_group, width, height = self.glyph_library.compose_text(
            str(par),
            x=text_x,
            y=text_y,
            font_size=self.PAR_TEXT_FONT_SIZE,
            spacing=0
        )

        logger.info("Created par text '%s' (%.2f × %.2f mm) at (%.2f, %.2f)",
                   par, width, height, text_x, text_y)

        return text_group

    def _create_tee_text_element(
        self,
        text_content: str,
        x_uu: float,
        y_uu: float
    ) -> tuple[Group, float, float]:
        """
        Create a glyph-based text element for tee yardage display.

        Uses GlyphLibrary for accurate measurements and consistent rendering.

        Args:
            text_content: The text to display
            x_uu: X position in user units (bottom-left corner)
            y_uu: Y position in user units (bottom-left corner)

        Returns:
            Tuple of (text_group, width, height) with accurate measurements
        """
        text_group, width, height = self.glyph_library.compose_text(
            text_content,
            x=x_uu,
            y=y_uu,
            font_size=self.TEE_YARDAGE_FONT_SIZE,
            spacing=0
        )

        return text_group, width, height

    def _create_tee_yardages(self, hole_num: int) -> Optional[Group]:
        """
        Create tee box yardage display with three-element formatting and bottom-up positioning.

        Uses GlyphLibrary for accurate text measurements and precise positioning. Unlike the
        previous font-based approximations, this provides exact dimensions for perfect alignment.

        Each line displays: "TeeName : 325" using three separate glyph groups:
        1. Tee name (right-aligned before colon using actual width)
        2. Colon (positioned at pivot point with measured width)
        3. Yardage (left-aligned after colon with spacing)

        Positioning strategy:
        - Anchor to lower right corner of top area bounding box (with margin)
        - Measure actual colon width from glyph library (not approximated)
        - Measure each tee name width for precise right-alignment
        - Start with bottom-most tee (last in list)
        - Position subsequent tees upward using user-configurable line spacing

        Args:
            hole_num: Hole number (1-18) for unique group ID

        Returns:
            Group containing tee yardage glyph groups, or None if no tees specified
        """
        # Collect tee boxes with non-zero yardages
        tees: list[tuple[str, int]] = []
        for i in range(1, 7):  # 6 tee boxes
            name: str = getattr(self.options, f'tee{i}_name', '')
            yardage: int = getattr(self.options, f'tee{i}_yardage', 0)

            if yardage > 0 and name and name.strip():  # Only include if yardage > 0 and name exists
                tees.append((name.strip(), yardage))

        # Return None if no tees specified
        if not tees:
            logger.info("No tee box yardages specified (all zeros)")
            return None

        # Convert anchor positions to user units and get user-configurable spacing
        try:
            colon_x_uu = self.svg.unittouu(f"{self.TEE_YARDAGE_ANCHOR_X}in")
            base_y_uu = self.svg.unittouu(f"{self.TEE_YARDAGE_ANCHOR_Y}in")
            # Get spacing from user options (already in user units)
            element_spacing_uu = float(self.options.element_spacing)
            line_spacing_uu = float(self.options.line_spacing)

        except (ValueError, AttributeError) as e:
            logger.error("Failed to convert tee yardage units: %s", e)
            return None

        logger.info(
            "Tee yardage layout: anchor=(%.2f\", %.2f\"), colon_x=%.2f\", font=%dpt, element_spacing=%dpx, line_spacing=%dpx",
            self.TEE_YARDAGE_ANCHOR_X, self.TEE_YARDAGE_ANCHOR_Y,
            self.TEE_YARDAGE_ANCHOR_X, self.TEE_YARDAGE_FONT_SIZE,
            int(element_spacing_uu), int(line_spacing_uu)
        )

        # Debug output for Inkscape UI
        inkex.utils.debug(f"=== TEE YARDAGE DEBUG (GLYPH LIBRARY) ===")
        inkex.utils.debug(f"Anchor point: ({self.TEE_YARDAGE_ANCHOR_X:.2f}\", {self.TEE_YARDAGE_ANCHOR_Y:.2f}\")")
        inkex.utils.debug(f"Anchor in user units: colon_x={colon_x_uu:.2f}px, base_y={base_y_uu:.2f}px")
        inkex.utils.debug(f"Element spacing: {element_spacing_uu:.2f}px (horizontal)")
        inkex.utils.debug(f"Line spacing: {line_spacing_uu:.2f}px (vertical)")
        inkex.utils.debug(f"Processing {len(tees)} tees in reverse order (bottom-up)")

        # STEP 1: Measure actual colon width using glyph library
        inkex.utils.debug(f"\n--- STEP 1: Measuring colon width with glyph library ---")

        # Get actual colon width from glyph library (no approximations!)
        _, colon_width_uu, colon_height_uu = self._create_tee_text_element(
            ':', 0, 0
        )

        inkex.utils.debug(f"Font size: {self.TEE_YARDAGE_FONT_SIZE}pt")
        inkex.utils.debug(f"Measured colon width: {colon_width_uu:.2f}px (actual, not estimated)")
        inkex.utils.debug(f"Using line spacing: {line_spacing_uu:.2f}px")
        logger.info("Measured colon width: %.2fpx (actual measurement)", colon_width_uu)

        # Calculate yardage position (colon position is anchor, yardage starts after)
        # Layout: [name] <element_spacing> [:] <element_spacing> [yardage]
        # Note: Name position will be calculated per-line based on actual name width
        yardage_x_uu = colon_x_uu + colon_width_uu + element_spacing_uu  # Yardage starts after colon

        inkex.utils.debug(f"\nFixed element positions:")
        inkex.utils.debug(f"  Colon x: {colon_x_uu:.2f}px (anchor point, {colon_width_uu:.2f}px wide)")
        inkex.utils.debug(f"  Yardage x: {yardage_x_uu:.2f}px (left-aligned, {element_spacing_uu:.0f}px gap from colon)")

        # STEP 2: Create all elements at their correct positions with accurate measurements
        inkex.utils.debug(f"\n--- STEP 2: Creating {len(tees)} tee lines (bottom-up positioning) ---")
        created_elements: list[tuple[Group, Group, Group]] = []
        current_y_uu = base_y_uu

        # Process tees in reverse order (bottom to top)
        # This ensures Tee 1 appears at top, Tee 6 at bottom (conventional yardage book order)
        for idx, (name, yardage) in enumerate(reversed(tees)):
            inkex.utils.debug(f"\n--- Tee line {idx} (from bottom): '{name}' : {yardage} ---")
            inkex.utils.debug(f"Creating at y={current_y_uu:.2f}px")

            # Measure name width to calculate right-aligned position
            _, name_width_uu, _ = self._create_tee_text_element(name, 0, 0)

            # Position name so its right edge is at (colon_x - spacing)
            name_x_uu = colon_x_uu - element_spacing_uu - name_width_uu

            inkex.utils.debug(f"  Name '{name}' width: {name_width_uu:.2f}px")
            inkex.utils.debug(f"  Name x: {name_x_uu:.2f}px (right-aligned with {element_spacing_uu:.0f}px gap to colon)")

            # Create the three elements for this line with measured positions
            tee_name_elem, _, _ = self._create_tee_text_element(
                name, name_x_uu, current_y_uu
            )
            colon_elem, _, _ = self._create_tee_text_element(
                ':', colon_x_uu, current_y_uu
            )
            yardage_elem, _, _ = self._create_tee_text_element(
                str(yardage), yardage_x_uu, current_y_uu
            )

            # Store elements for grouping
            created_elements.append((tee_name_elem, colon_elem, yardage_elem))

            logger.debug(
                "Tee line %d (from bottom): '%s' : %d at y=%.2f (name_x=%.2f, colon_x=%.2f, yardage_x=%.2f)",
                idx, name, yardage, current_y_uu, name_x_uu, colon_x_uu, yardage_x_uu
            )

            # Position next line above this one
            old_y = current_y_uu
            current_y_uu -= line_spacing_uu
            inkex.utils.debug(f"Next position: {old_y:.2f}px - {line_spacing_uu:.2f}px = {current_y_uu:.2f}px (moving upward)")

        # Create final group and add elements to it
        inkex.utils.debug(f"\n--- Finalizing Group ---")
        inkex.utils.debug(f"Creating group: tee_yardages_{hole_num:02d}")
        tee_group = Group()
        tee_group.set('id', f'tee_yardages_{hole_num:02d}')
        tee_group.label = f'tee_yardages_{hole_num:02d}'

        # Add elements to group (reverse to maintain top-to-bottom order in XML)
        inkex.utils.debug(f"Adding {len(created_elements)} lines (3 glyph groups each) to group")
        for tee_name_elem, colon_elem, yardage_elem in reversed(created_elements):
            tee_group.append(tee_name_elem)
            tee_group.append(colon_elem)
            tee_group.append(yardage_elem)

        inkex.utils.debug(f"✓ Complete! Created {len(tees)} tee lines with glyph library (accurate measurements)")
        inkex.utils.debug(f"=== END TEE YARDAGE DEBUG ===\n")

        logger.info(
            "Created tee yardage display with %d tees (bottom-up, glyph-based with accurate widths)",
            len(tees)
        )
        return tee_group

    def show_available_fonts(self) -> None:
        """
        Show all available glyph library fonts in the glyph_libraries folder.

        Lists all .svg files in the glyph_libraries directory and displays them
        using Inkscape's error message system. Users can copy these exact names
        (without .svg extension) into the Glyph Library Font field.
        """
        import os
        from pathlib import Path

        # Get glyph_libraries folder path
        glyph_dir = Path(os.path.dirname(__file__)) / 'glyph_libraries'

        if not glyph_dir.exists():
            inkex.errormsg("=" * 60)
            inkex.errormsg("ERROR: glyph_libraries folder not found!")
            inkex.errormsg("=" * 60)
            inkex.errormsg(f"Expected location: {glyph_dir}")
            inkex.errormsg("")
            inkex.errormsg("Please create the glyph_libraries folder and add")
            inkex.errormsg("glyph library .svg files using the Prepare Glyph Library tool.")
            inkex.errormsg("=" * 60)
            return

        # Find all .svg files (excluding TEMPLATE.svg and README.md)
        svg_files = sorted([
            f.stem for f in glyph_dir.glob('*.svg')
            if f.name not in ['TEMPLATE.svg']
        ])

        if not svg_files:
            inkex.errormsg("=" * 60)
            inkex.errormsg("NO GLYPH LIBRARY FONTS FOUND")
            inkex.errormsg("=" * 60)
            inkex.errormsg(f"Folder: {glyph_dir}")
            inkex.errormsg("")
            inkex.errormsg("Please create glyph libraries using:")
            inkex.errormsg("Extensions → Golf Cartographer → Prepare Glyph Library")
            inkex.errormsg("=" * 60)
            return

        # Display available fonts
        inkex.errormsg("=" * 60)
        inkex.errormsg(f"AVAILABLE GLYPH LIBRARY FONTS ({len(svg_files)} found)")
        inkex.errormsg("=" * 60)
        inkex.errormsg(f"Location: {glyph_dir}")
        inkex.errormsg("")

        for font_name in svg_files:
            inkex.errormsg(f"  • {font_name}")

        inkex.errormsg("")
        inkex.errormsg("=" * 60)
        inkex.errormsg("USAGE:")
        inkex.errormsg("1. Copy the exact font name from the list above")
        inkex.errormsg("2. Go to the 'Add Label' tab")
        inkex.errormsg("3. Paste the name into the 'Glyph Library Font' field")
        inkex.errormsg("4. Do NOT include the .svg extension")
        inkex.errormsg("=" * 60)

        logger.info("Listed %d available glyph library fonts", len(svg_files))


if __name__ == '__main__':
    AddHoleLabel().run()
