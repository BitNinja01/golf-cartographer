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
        pars.add_argument("--font_family", type=str, default="Arial, Liberation Sans, sans-serif",
                         help="Font family for text")

    def effect(self) -> None:
        """
        Main execution method for Add Hole Label Tool.

        Execution Flow:
        1. Validate parameters (hole number, par, font size)
        2. Validate that hole group exists (from Stage 3)
        3. Check for duplicate labels (remove if exists)
        4. Create label group with circle and text elements
        5. Add label group to hole group with inverse transform
        6. Create and add tee yardages to document root (if specified)

        Validation ensures Stage 3 (Auto-Place Holes) has been run before
        attempting to add labels.
        """
        root = self.document.getroot()
        hole_num = self.options.hole_number
        par = self.options.par

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

    def _create_centered_hole_number(self, hole_num: int, circle_cx: float, circle_cy: float) -> TextElement:
        """
        Create hole number as text and center it precisely in the circle.

        Uses SVG's text-anchor and dominant-baseline properties to center text
        at the specified point. This is the standard SVG approach for text centering
        and is simpler than transform-based positioning.

        Args:
            hole_num: Hole number (1-18)
            circle_cx: Circle center X in user units
            circle_cy: Circle center Y in user units

        Returns:
            TextElement with hole number, centered in circle
        """
        logger.info("Creating centered hole number %d at circle center (%.2f, %.2f)",
                   hole_num, circle_cx, circle_cy)

        # Small vertical offset to fine-tune centering (approximately 0.25mm down)
        vertical_offset = 0.9  # user units

        # Create text element at circle center with centering styles
        text = TextElement()
        text.set('x', str(circle_cx))
        text.set('y', str(circle_cy + vertical_offset))
        text.style = Style({
            'font-size': f'{self.options.font_size}pt',
            'font-family': self.options.font_family,
            'font-weight': self.options.font_weight,
            'fill': '#000000',                 # Black text color
            'stroke': 'none',                  # Ensure no stroke is applied
            'text-anchor': 'middle',           # Center horizontally at x position
            'dominant-baseline': 'middle'      # Center vertically at y position
        })

        tspan = Tspan()
        tspan.text = str(hole_num)
        text.append(tspan)

        logger.info("Successfully created centered hole number %d", hole_num)

        return text

    def _create_par_text(self, par: int, cx_uu: float, cy_uu: float, radius_uu: float) -> TextElement:
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
            TextElement containing par information
        """
        text = TextElement()

        # Position below circle with offset
        offset_uu = self.svg.unittouu(f"{self.PAR_TEXT_OFFSET}in")
        text.set('x', str(cx_uu))
        text.set('y', str(cy_uu + radius_uu + offset_uu))

        # Fixed font size for par text (independent of hole number font size)
        text.style = Style({
            'font-size': f'{self.PAR_TEXT_FONT_SIZE}pt',
            'font-family': self.options.font_family,
            'font-weight': 'normal',
            'fill': '#000000',                 # Black text color
            'stroke': 'none',                  # Ensure no stroke is applied
            'text-anchor': 'middle',
            'dominant-baseline': 'hanging'
        })

        tspan = Tspan()
        tspan.text = str(par)
        text.append(tspan)

        return text

    def _create_tee_text_element(
        self,
        text_content: str,
        x_uu: float,
        y_uu: float,
        text_anchor: str
    ) -> TextElement:
        """
        Create a styled text element for tee yardage display.

        Args:
            text_content: The text to display
            x_uu: X position in user units
            y_uu: Y position in user units
            text_anchor: SVG text-anchor value ('start', 'middle', or 'end')

        Returns:
            Configured TextElement with standard tee yardage styling
        """
        text = TextElement()
        text.set('x', str(x_uu))
        text.set('y', str(y_uu))
        text.style = Style({
            'font-size': f'{self.TEE_YARDAGE_FONT_SIZE}pt',
            'font-family': self.options.font_family,
            'font-weight': 'normal',
            'fill': '#000000',
            'stroke': 'none',
            'text-anchor': text_anchor,
            'dominant-baseline': 'hanging'
        })

        tspan = Tspan()
        tspan.text = text_content
        text.append(tspan)

        return text

    def _create_tee_yardages(self, hole_num: int) -> Optional[Group]:
        """
        Create tee box yardage display with three-element formatting and bottom-up positioning.

        Uses font-based calculations for reliable spacing. Text element bounding boxes are
        unreliable until after layout/rendering, so dimensions are calculated from font metrics.

        Each line displays: "TeeName : 325" using three separate text elements:
        1. Tee name (right-aligned before colon)
        2. Colon (left-aligned at pivot point, ~40% of font size width)
        3. Yardage (left-aligned after colon with spacing)

        Positioning strategy:
        - Anchor to lower right corner of top area bounding box (with margin)
        - Calculate colon width as 40% of font size (reliable for proportional fonts)
        - Start with bottom-most tee (last in list)
        - Position subsequent tees upward using user-configurable line spacing

        Args:
            hole_num: Hole number (1-18) for unique group ID

        Returns:
            Group containing tee yardage text elements, or None if no tees specified
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
        inkex.utils.debug(f"=== TEE YARDAGE DEBUG ===")
        inkex.utils.debug(f"Anchor point: ({self.TEE_YARDAGE_ANCHOR_X:.2f}\", {self.TEE_YARDAGE_ANCHOR_Y:.2f}\")")
        inkex.utils.debug(f"Anchor in user units: colon_x={colon_x_uu:.2f}px, base_y={base_y_uu:.2f}px")
        inkex.utils.debug(f"Element spacing: {element_spacing_uu:.2f}px (horizontal)")
        inkex.utils.debug(f"Line spacing: {line_spacing_uu:.2f}px (vertical)")
        inkex.utils.debug(f"Processing {len(tees)} tees in reverse order (bottom-up)")

        # STEP 1: Calculate colon width from font metrics
        inkex.utils.debug(f"\n--- STEP 1: Calculating element spacing from font metrics ---")

        # Text elements don't have reliable bounding box measurements until after layout/rendering.
        # Calculate colon width from font size: for proportional fonts, colon is ~40% of font size
        font_size_uu = self.svg.unittouu(f"{self.TEE_YARDAGE_FONT_SIZE}pt")
        colon_width_uu = font_size_uu * 0.4  # Approximately 2-3px for 5pt font

        inkex.utils.debug(f"Font size: {self.TEE_YARDAGE_FONT_SIZE}pt = {font_size_uu:.2f}px")
        inkex.utils.debug(f"Calculated colon width: {colon_width_uu:.2f}px (40% of font size)")
        inkex.utils.debug(f"Using fixed line spacing: {line_spacing_uu:.2f}px")
        logger.info("Calculated colon width: %.2fpx from font size %.2fpx", colon_width_uu, font_size_uu)

        # Calculate element positions with configurable spacing
        # Layout: [name] <element_spacing> [:] <element_spacing> [yardage]
        name_x_uu = colon_x_uu - element_spacing_uu  # Name ends before colon
        yardage_x_uu = colon_x_uu + colon_width_uu + element_spacing_uu  # Yardage starts after colon

        inkex.utils.debug(f"\nElement positions:")
        inkex.utils.debug(f"  Name x: {name_x_uu:.2f}px (right-aligned, {element_spacing_uu:.0f}px gap to colon)")
        inkex.utils.debug(f"  Colon x: {colon_x_uu:.2f}px (left-aligned, {colon_width_uu:.2f}px wide)")
        inkex.utils.debug(f"  Yardage x: {yardage_x_uu:.2f}px (left-aligned, {element_spacing_uu:.0f}px gap from colon)")

        # STEP 2: Create all elements at their correct positions
        inkex.utils.debug(f"\n--- STEP 2: Creating {len(tees)} tee lines (bottom-up positioning) ---")
        created_elements: list[tuple[TextElement, TextElement, TextElement]] = []
        current_y_uu = base_y_uu

        # Process tees in reverse order (bottom to top)
        # This ensures Tee 1 appears at top, Tee 6 at bottom (conventional yardage book order)
        for idx, (name, yardage) in enumerate(reversed(tees)):
            inkex.utils.debug(f"\n--- Tee line {idx} (from bottom): '{name}' : {yardage} ---")
            inkex.utils.debug(f"Creating at y={current_y_uu:.2f}px")

            # Create the three elements for this line with proper spacing
            tee_name_elem = self._create_tee_text_element(
                name, name_x_uu, current_y_uu, 'end'
            )
            colon_elem = self._create_tee_text_element(
                ':', colon_x_uu, current_y_uu, 'start'
            )
            yardage_elem = self._create_tee_text_element(
                str(yardage), yardage_x_uu, current_y_uu, 'start'
            )

            # Store elements for grouping (no DOM manipulation needed - using calculated dimensions)
            created_elements.append((tee_name_elem, colon_elem, yardage_elem))

            logger.debug(
                "Tee line %d (from bottom): '%s' : %d at y=%.2f (colon_x=%.2f, yardage_x=%.2f)",
                idx, name, yardage, current_y_uu, colon_x_uu, yardage_x_uu
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
        inkex.utils.debug(f"Adding {len(created_elements)} lines (3 elements each) to group")
        for tee_name_elem, colon_elem, yardage_elem in reversed(created_elements):
            tee_group.append(tee_name_elem)
            tee_group.append(colon_elem)
            tee_group.append(yardage_elem)

        inkex.utils.debug(f"✓ Complete! Created {len(tees)} tee lines with bottom-up calculated spacing")
        inkex.utils.debug(f"=== END TEE YARDAGE DEBUG ===\n")

        logger.info(
            "Created tee yardage display with %d tees (bottom-up, font-based spacing)",
            len(tees)
        )
        return tee_group


if __name__ == '__main__':
    AddHoleLabel().run()
