#!/usr/bin/env python3
"""
Add Hole Label Tool - Stage 3.5 of Golf Yardage Book Extension Suite

This extension adds hole number circles and par text to positioned holes.
Creates visual labels in the top-right corner of each yardage book page.

Stage 3.5 - Hole Labeling:
- Creates circle at fixed page coordinates (top-right area)
- Adds hole number text centered in circle
- Adds par text below circle
- Groups all elements for easy management

Pipeline Context:
- Input: SVG with positioned holes (output from Tool #3 / Stage 3)
- Output: Holes with visual labels (hole number + par)
- Next Stage: Tool #4 will export PDFs

Author: Golf Yardage Book Extension Suite
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
    Adds hole number and par labels to yardage book pages.

    This tool is designed to be run 18 times (once per hole), similar to the
    Group Hole tool. Each execution creates a label group with:
    - Circle element at fixed page coordinates
    - Hole number text centered in the circle
    - Par text positioned below the circle

    The label is positioned at a fixed location on the page (top-right area),
    not relative to the hole group transforms, since each hole will be exported
    to its own PDF page in Stage 4.
    """

    # Fixed position for hole label circle (top-right area of page)
    # Coordinates define the bounding box upper-left corner
    # (Circle centers are calculated from this + radius offset)
    CIRCLE_BBOX_UL_X: float = 3.395  # inches
    CIRCLE_BBOX_UL_Y: float = 0.339  # inches
    CIRCLE_DIAMETER: float = 0.506  # inches

    # Calculate circle center from bounding box upper-left
    CIRCLE_CENTER_X: float = CIRCLE_BBOX_UL_X + (CIRCLE_DIAMETER / 2)  # 3.648"
    CIRCLE_CENTER_Y: float = CIRCLE_BBOX_UL_Y + (CIRCLE_DIAMETER / 2)  # 0.592"

    # Text positioning
    PAR_TEXT_OFFSET: float = 0.1  # inches below circle
    PAR_TEXT_FONT_SIZE: int = 4  # Fixed font size for par text in points

    def add_arguments(self, pars: argparse.ArgumentParser) -> None:
        """Add command-line arguments."""
        pars.add_argument("--hole_number", type=int, default=1,
                         help="Hole number (1-18)")
        pars.add_argument("--par", type=int, default=4,
                         help="Par value (3-6)")
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
        1. Validate parameters (hole number, par, font size, color)
        2. Validate that hole group exists (from Stage 3)
        3. Check for duplicate labels (remove if exists)
        4. Create label group with circle and text elements
        5. Add label group to document root

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
        - Circle element at fixed page position
        - Hole number text centered in circle
        - Par text positioned below circle

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


if __name__ == '__main__':
    AddHoleLabel().run()
