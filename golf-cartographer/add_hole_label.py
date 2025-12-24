#!/usr/bin/env python3
"""
Add Hole Label Tool - Stage 4 of Golf Cartographer Extension Suite

This extension adds hole number circles, par text, and tee box yardages to positioned holes.
Creates visual labels with customizable fonts and supports up to 6 tee boxes per course.

Stage 4 - Hole Labeling:
- Creates circle at fixed page coordinates (top-right area)
- Adds hole number text centered in circle (user-configurable font size)
- Adds par text below circle (user-configurable font size)
- Adds tee box yardages in bottom-right corner (user-configurable font size)
- Groups all elements with inverse transforms for consistent positioning

Font Sizing and Spacing:
- Hole number: user's font_size parameter (letter spacing: 5% for double-digit numbers)
- Par text: user's par_font_size parameter (offset below circle: 35% of par font size)
- Tee yardages: user's tee_font_size parameter (element spacing: 20%, line spacing: 35%, letter spacing: 5%)

Pipeline Context:
- Input: SVG with positioned holes (output from Tool #3 / Stage 3)
- Output: Holes with visual labels (hole number + par + tee yardages)
- Next Stage: Tool #5 (Export PDFs) will create the final yardage book PDFs

Author: Golf Cartographer Extension Suite
License: MIT
"""
from __future__ import annotations

import argparse
import logging
from typing import Optional

import inkex
from inkex import Circle, Group, Rectangle, Style, TextElement, Transform, Tspan

from glyph_library import GlyphLibrary

# Configure module logger
logger = logging.getLogger(__name__)


class AddHoleLabel(inkex.EffectExtension):
    """
    Adds hole number, par labels, and tee box yardages to yardage book pages.

    This tool is designed to be run 18 times (once per hole), similar to the
    Group Hole tool. Each execution creates:
    - Label group (with inverse transform):
      - Circle element at fixed page coordinates (top-right)
      - Hole number text centered in the circle
      - Par text positioned below the circle
    - Tee yardages group (with inverse transform):
      - Tee box yardages in bottom-right corner (optional, up to 6 tees)

    Group Structure (to avoid clip issues):
    The tool restructures the hole groups to prevent labels from being clipped:
    - Original: top/hole_XX (with clip applied to all children)
    - Restructured: top/hole_XX/geo_XX (clip applies here) + tee_yardages_XX + hole_label_XX

    This restructuring happens automatically on first run. The geo_XX group contains
    the clipped geometry, while labels are siblings (not children) so they aren't clipped.
    Both labels use inverse transforms to maintain fixed positions despite the geo_XX
    group having rotation, scaling, and positioning transforms from Stage 3.
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

    # Text positioning and sizing
    # Font sizes are user-configurable (font_size, par_font_size, tee_font_size)
    # Spacing is proportional to respective font sizes:
    # - Hole number letter spacing: 5% of hole number font size
    # - Par text offset below circle: 35% of par font size
    # - Tee line spacing (vertical): 35% of tee font size
    # - Tee element spacing (horizontal): 20% of tee font size
    # - Tee letter spacing: 5% of tee font size
    HOLE_NUMBER_LETTER_SPACING_SCALE: float = 0.05  # Letter spacing as % of hole number font size
    PAR_TEXT_OFFSET_SCALE: float = 0.35  # Par text offset as % of par font size
    TEE_LINE_SPACING_SCALE: float = 0.35  # Tee line spacing as % of tee font size
    TEE_ELEMENT_SPACING_SCALE: float = 0.20  # Element spacing as % of tee font size
    TEE_LETTER_SPACING_SCALE: float = 0.05  # Letter spacing as % of tee font size

    # Tee box yardage positioning (anchored to lower right of top area)
    # Lower right corner: (0.257 + 3.736, 0.247 + 6.756) = (3.993", 7.003")
    # Three-element layout: name (right-aligned) : yardage (right-aligned to boundary)
    # TEE_YARDAGE_ANCHOR_X represents the RIGHT EDGE of the entire yardage group
    TEE_YARDAGE_ANCHOR_X: float = 3.993 - BOUNDING_BOX_MARGIN  # inches - 0.092" padding from right edge = 3.901" (right boundary)
    TEE_YARDAGE_ANCHOR_Y: float = 7.003 - BOUNDING_BOX_MARGIN  # inches - 0.092" padding from bottom = 6.911"

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
        # Font options
        pars.add_argument("--font_size", type=int, default=6,
                         help="Hole number font size in points")
        pars.add_argument("--par_font_size", type=int, default=4,
                         help="Par text font size in points")
        pars.add_argument("--tee_font_size", type=int, default=4,
                         help="Tee yardage font size in points")
        pars.add_argument("--font_weight", type=str, default="bold",
                         help="Font weight (bold or normal)")
        pars.add_argument("--font_family", type=str, default="JetBrainsMono Nerd Font",
                         help="Glyph library font name (without .svg extension)")

    def _generate_terrain_mask(self, hole_num: int, wrapper_group: Group, geo_group: Group) -> None:
        """
        Generate white mask for right third of top area, inserted inside geo_XX.

        Creates a white rectangle covering the right third of the TOP bounding box,
        inserted between 'other' and 'bunkers' groups inside geo_XX. The mask uses
        an inverse transform to appear at the correct page position despite geo_XX's
        rotation/scale/translation.

        Algorithm:
        1. Check/reorder geo_XX children to ensure: other → bunkers → fairways → green_XX → yardage_lines
        2. Create white rectangle (right third of TOP area) in page coordinates
        3. Apply inverse of geo_transform so mask appears correctly
        4. Insert mask between 'other' and 'bunkers' inside geo_XX
        5. Create clip-path to exclude mask area from yardage lines

        Args:
            hole_num: Hole number (1-18)
            wrapper_group: The hole_XX wrapper group (has identity transform)
            geo_group: The geo_XX group containing terrain (has transforms from Stage 3)

        Side Effects:
            - May reorder children in geo_group
            - Inserts mask element in geo_group
        """
        # Remove existing mask if present
        mask_id = f'terrain_mask_{hole_num:02d}'
        existing_mask = None
        for child in list(geo_group):
            if child.get('id') == mask_id:
                existing_mask = child
                break
        if existing_mask is not None:
            geo_group.remove(existing_mask)
            logger.info(f"Removed existing terrain mask for hole {hole_num}")

        # ===== STEP 1: Check and reorder geo_XX children =====
        # Expected order (bottom to top): other → bunkers → fairways → green_XX
        self._ensure_geo_child_order(geo_group, hole_num)

        # ===== STEP 2: Create BOTH rectangles (left 2/3 and right 1/3 of TOP area) =====
        # TOP BOUNDING_BOX: x=0.257", y=0.247", w=3.736", h=6.756"
        top_x = 0.257
        top_y = 0.247
        top_width = 3.736
        top_height = 6.756

        # LEFT 2/3 calculation (for clip-path):
        left_two_thirds_x = top_x  # 0.257"
        left_two_thirds_y = top_y  # 0.247"
        left_two_thirds_width = top_width * 2.0 / 3.0  # 2.491"
        left_two_thirds_height = top_height  # 6.756"

        # RIGHT 1/3 calculation (for visual white mask):
        right_third_x = top_x + left_two_thirds_width  # 2.748"
        right_third_y = top_y  # 0.247"
        right_third_width = top_width / 3.0  # 1.245"
        right_third_height = top_height  # 6.756"

        # Convert to user units (page coordinates)
        left_x_uu = self.svg.unittouu(f"{left_two_thirds_x}in")
        left_y_uu = self.svg.unittouu(f"{left_two_thirds_y}in")
        left_w_uu = self.svg.unittouu(f"{left_two_thirds_width}in")
        left_h_uu = self.svg.unittouu(f"{left_two_thirds_height}in")

        right_x_uu = self.svg.unittouu(f"{right_third_x}in")
        right_y_uu = self.svg.unittouu(f"{right_third_y}in")
        right_w_uu = self.svg.unittouu(f"{right_third_width}in")
        right_h_uu = self.svg.unittouu(f"{right_third_height}in")

        # Create right 1/3 white mask rectangle
        mask = Rectangle()
        mask.set('id', mask_id)
        mask.set('x', str(right_x_uu))
        mask.set('y', str(right_y_uu))
        mask.set('width', str(right_w_uu))
        mask.set('height', str(right_h_uu))
        mask.style = Style({'fill': '#ffffff', 'stroke': 'none'})

        # ===== STEP 3: Apply inverse transform to mask =====
        # Mask is a child of geo_group, so it needs inverse transform
        # to appear at the correct page coordinates despite geo_group's transforms.
        geo_transform = geo_group.transform or Transform()
        if geo_transform:
            inverse_transform = -geo_transform  # inkex Transform supports negation for inverse
            mask.transform = inverse_transform

        # ===== STEP 4: Insert mask at appropriate z-order position =====
        # terrain_mask (white, right 1/3): between 'other' and 'bunkers' to cover terrain

        # Remove any existing clip rectangle from previous runs (cleanup)
        clip_rect_id = f'clip_rect_{hole_num:02d}'
        for child in list(geo_group):
            if child.get('id') == clip_rect_id:
                geo_group.remove(child)
                logger.info(f"Removed obsolete clip rectangle for hole {hole_num}")
                break

        # Find insertion points
        bunkers_index = None
        last_yardage_index = None
        for idx, child in enumerate(geo_group):
            if isinstance(child, Group):
                label = child.label
                if label:
                    if label.lower() == 'bunkers':
                        bunkers_index = idx
                    elif 'yardage' in label.lower():
                        last_yardage_index = idx  # Track the last yardage group

        # Insert terrain_mask (white) between 'other' and 'bunkers'
        if bunkers_index is not None:
            geo_group.insert(bunkers_index, mask)
            logger.info(f"Inserted terrain mask for hole {hole_num} before bunkers (index {bunkers_index})")
            # Adjust last_yardage_index since we inserted before it
            if last_yardage_index is not None and last_yardage_index >= bunkers_index:
                last_yardage_index += 1
        else:
            # No bunkers group - find 'other' and insert after it
            other_index = None
            for idx, child in enumerate(geo_group):
                if isinstance(child, Group):
                    label = child.label
                    if label and label.lower() == 'other':
                        other_index = idx
                        break

            if other_index is not None:
                geo_group.insert(other_index + 1, mask)
                logger.info(f"Inserted terrain mask for hole {hole_num} after other (index {other_index + 1})")
                # Adjust last_yardage_index
                if last_yardage_index is not None and last_yardage_index > other_index:
                    last_yardage_index += 1
            else:
                geo_group.insert(0, mask)
                logger.info(f"Inserted terrain mask for hole {hole_num} at beginning")
                if last_yardage_index is not None:
                    last_yardage_index += 1

        logger.info(f"Successfully generated terrain mask for hole {hole_num}")

        # ===== STEP 5: Create clip-path with pre-transformed coordinates =====
        # The clipPath is in <defs> at document root. When referenced by yardage_group
        # (inside geo_group) with userSpaceOnUse, the clip coordinates are interpreted
        # in the FULL TRANSFORM CHAIN from page root to yardage_group.
        #
        # KEY INSIGHT: We must use composed_transform() to get the complete transform
        # chain, not just geo_group.transform. There may be transforms on ancestors
        # (top, hole_XX) or on yardage_group itself.
        #
        # To clip at page rectangle P:
        #   1. Page corners are known: (left_x, left_y), etc.
        #   2. Get full_transform = composed_transform() of yardage_group
        #   3. Local corners = inverse(full_transform).apply_to_point(page_corner)
        #   4. Create path with explicit local corner coordinates (NO transform attr)
        from inkex import Defs, ClipPath, PathElement

        # Find yardage line groups in geo_XX
        yardage_groups = []
        for child in geo_group:
            if isinstance(child, Group):
                label = child.label
                if label and 'yardage' in label.lower():
                    yardage_groups.append(child)

        if yardage_groups:
            # Get or create defs section
            root = self.document.getroot()
            defs = root.find('.//{http://www.w3.org/2000/svg}defs')
            if defs is None:
                defs = Defs()
                root.insert(0, defs)

            # Create clip-path element
            clip_id = f'yardage_clip_{hole_num:02d}'

            # Remove existing clip-path if present
            existing_clip = root.find(f'.//{{{inkex.NSS["svg"]}}}clipPath[@id="{clip_id}"]')
            if existing_clip is not None:
                existing_clip.getparent().remove(existing_clip)

            clip_path_elem = ClipPath()
            clip_path_elem.set('id', clip_id)

            # Define page corners of the clip rectangle (left 2/3 of top area)
            page_corners = [
                (left_x_uu, left_y_uu),                          # top-left
                (left_x_uu + left_w_uu, left_y_uu),              # top-right
                (left_x_uu + left_w_uu, left_y_uu + left_h_uu),  # bottom-right
                (left_x_uu, left_y_uu + left_h_uu),              # bottom-left
            ]

            # Use the FIRST yardage group to get the full transform chain
            # (all yardage groups should have the same transform chain since they're
            # siblings inside geo_group)
            target_yardage_group = yardage_groups[0]

            # Get the COMPLETE transform chain from page root to yardage_group
            # This includes any transforms on: top → hole_XX → geo_XX → yardage_group
            full_transform = target_yardage_group.composed_transform()
            full_inverse = -full_transform  # inkex Transform supports negation for inverse

            # Transform page corners to local coordinate system using FULL inverse
            # Local = full_inverse(Page)
            # When full_transform is applied to local, we get back to page coords
            local_corners = []
            for px, py in page_corners:
                lx, ly = full_inverse.apply_to_point((px, py))
                local_corners.append((lx, ly))

            # Create path with local corner coordinates
            # M = moveto, L = lineto, Z = close path
            path_d = f"M {local_corners[0][0]},{local_corners[0][1]} "
            path_d += f"L {local_corners[1][0]},{local_corners[1][1]} "
            path_d += f"L {local_corners[2][0]},{local_corners[2][1]} "
            path_d += f"L {local_corners[3][0]},{local_corners[3][1]} Z"

            clip_path = PathElement()
            clip_path.set('d', path_d)
            # NO transform attribute - coordinates are already in local space
            clip_path_elem.append(clip_path)

            defs.append(clip_path_elem)

            # Apply clip-path to each yardage line group
            for yg in yardage_groups:
                yg.set('clip-path', f'url(#{clip_id})')

            logger.info(f"Applied clip-path to {len(yardage_groups)} yardage line group(s)")

    def _ensure_geo_child_order(self, geo_group: Group, hole_num: int) -> None:
        """
        Ensure geo_XX children are in correct z-order: other → bunkers → fairways → green_XX → yardage_lines.

        If children are out of order (e.g., from older Stage 2 output), this method
        reorders them to match the expected order. Also handles migration of yardage
        lines from inside 'other' group (old Stage 2) to above green_XX (new Stage 2).

        Args:
            geo_group: The geo_XX group to check/reorder
            hole_num: Hole number for logging
        """
        # Collect children by type
        other_group = None
        bunkers_group = None
        fairways_group = None
        green_elements = []
        yardage_elements = []  # Yardage line groups (should be above green_XX)
        other_elements = []  # Elements that don't match known categories

        for child in list(geo_group):
            if isinstance(child, Group):
                # Use .label property for consistency with Stage 2
                label = child.label
                if label:
                    label_lower = label.lower()
                    if label_lower == 'other':
                        other_group = child
                    elif label_lower == 'bunkers':
                        bunkers_group = child
                    elif label_lower == 'fairways':
                        fairways_group = child
                    elif 'yardage' in label_lower:
                        # Yardage line group detected (should be above green_XX)
                        yardage_elements.append(child)
                    else:
                        other_elements.append(child)
                else:
                    other_elements.append(child)
            else:
                # Check if it's a green element
                child_id = child.get('id') or ''
                if child_id.startswith(f'green_{hole_num:02d}'):
                    green_elements.append(child)
                else:
                    other_elements.append(child)

        # MIGRATION LOGIC: Extract yardage lines from 'other' group if present (old Stage 2)
        # In old Stage 2, yardage lines were placed inside the 'other' group
        # In new Stage 2, they should be siblings to green_XX (above it in z-order)
        if other_group is not None:
            yardage_children_to_migrate = []
            for child in list(other_group):
                if isinstance(child, Group):
                    child_label = child.label
                    if child_label and 'yardage' in child_label.lower():
                        # Found yardage lines inside 'other' group - need to migrate
                        yardage_children_to_migrate.append(child)
                        logger.info(f"Found yardage lines inside 'other' group (old Stage 2 structure) - will migrate to above green_XX")

            # Remove yardage lines from 'other' group and add to yardage_elements
            for yardage_child in yardage_children_to_migrate:
                other_group.remove(yardage_child)
                yardage_elements.append(yardage_child)
                logger.info(f"Migrated yardage lines from 'other' group to above green_XX (new Stage 2 structure)")

        # Check if reordering is needed by comparing current order to expected
        current_order = list(geo_group)
        expected_order = []

        # Expected z-order (bottom to top): other → bunkers → fairways → green_XX → yardage_lines → other_elements
        if other_group is not None:
            expected_order.append(other_group)
        if bunkers_group is not None:
            expected_order.append(bunkers_group)
        if fairways_group is not None:
            expected_order.append(fairways_group)
        expected_order.extend(green_elements)
        expected_order.extend(yardage_elements)  # Yardage lines above green_XX
        expected_order.extend(other_elements)

        # Compare - only reorder if different
        needs_reorder = False
        if len(current_order) == len(expected_order):
            for curr, exp in zip(current_order, expected_order):
                if curr is not exp:
                    needs_reorder = True
                    break
        else:
            needs_reorder = True

        if needs_reorder:
            # Remove all children
            for child in list(geo_group):
                geo_group.remove(child)

            # Re-add in correct order (bottom to top z-order)
            if other_group is not None:
                geo_group.append(other_group)
            if bunkers_group is not None:
                geo_group.append(bunkers_group)
            if fairways_group is not None:
                geo_group.append(fairways_group)
            for elem in green_elements:
                geo_group.append(elem)
            for elem in yardage_elements:
                geo_group.append(elem)  # Yardage lines above green_XX
            for elem in other_elements:
                geo_group.append(elem)

            logger.info(f"Reordered geo_{hole_num:02d} children to correct z-order")

    def validate_font_family(self, font_family: str) -> str:
        """
        Validate font family and fallback to JetBrains Mono Nerd Font if invalid.

        Checks if the glyph library .svg file exists in the glyph_libraries folder.
        Falls back to JetBrains Mono Nerd Font if the specified font is not found.

        Args:
            font_family: Font family name to validate

        Returns:
            Valid font family name (original or fallback)

        Raises:
            inkex.AbortExtension: If neither provided font nor JetBrains Mono Nerd Font are available
        """
        import os

        # Check if font_family is empty or just whitespace
        if not font_family or not font_family.strip():
            inkex.errormsg("No font family provided. Using fallback: JetBrainsMono Nerd Font")
            font_family = "JetBrainsMono Nerd Font"

        # Get path to glyph_libraries folder
        glyph_dir = os.path.join(os.path.dirname(__file__), 'glyph_libraries')

        # Check if provided font library exists
        library_path = os.path.join(glyph_dir, f'{font_family}.svg')
        if os.path.exists(library_path):
            return font_family

        # Font library not found - try fallback to JetBrainsMono Nerd Font
        fallback_font = "JetBrainsMono Nerd Font"
        if font_family != fallback_font:
            # User specified a different font that wasn't found
            fallback_path = os.path.join(glyph_dir, f'{fallback_font}.svg')
            if os.path.exists(fallback_path):
                inkex.errormsg(f"Glyph library '{font_family}.svg' not found. Using fallback: {fallback_font}")
                return fallback_font

        # Neither the requested font nor JetBrainsMono Nerd Font are available
        raise inkex.AbortExtension(
            f"ERROR: Glyph library '{font_family}.svg' not found.\n"
            f"Please create 'JetBrainsMono Nerd Font.svg' using the Prepare Glyph Library tool,\n"
            f"or specify a valid font that exists in the glyph_libraries folder.\n"
            f"Use the 'List Fonts' tab to see available glyph library fonts."
        )

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
        8. Create and add tee yardages to hole group with inverse transform (if specified)

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

        # Validate font family and fallback to JetBrains Mono Nerd Font if invalid
        import os
        font_name = self.validate_font_family(self.options.font_family.strip())

        # Load glyph library for accurate text measurements
        # Note: validate_font_family() already verified the file exists
        library_path = os.path.join(
            os.path.dirname(__file__),
            'glyph_libraries',
            f'{font_name}.svg'
        )

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

        # Validation: Check if hole_XX or geo_XX group exists
        # (geo_XX exists if this tool has already been run and restructured the groups)
        hole_id = f"hole_{hole_num:02d}"
        geo_id = f"geo_{hole_num:02d}"

        # Check if geo_XX exists (restructuring already done)
        geo_group = self._find_hole_group(root, geo_id)
        already_restructured = geo_group is not None

        if already_restructured:
            # Restructuring already done - find the wrapper and geo group
            logger.info("Hole %d already restructured - geo_%02d exists", hole_num, hole_num)
            hole_group = geo_group  # Use geo_XX for transform calculation
            wrapper_group = self._find_hole_group(root, hole_id)
            if wrapper_group is None:
                logger.error("Found geo_%02d but not hole_%02d wrapper", hole_num, hole_num)
                inkex.errormsg(f"Error: Inconsistent structure for hole {hole_num}")
                return
        else:
            # First time - find hole_XX (will be renamed to geo_XX)
            hole_group = self._find_hole_group(root, hole_id)
            if hole_group is None:
                logger.warning("Hole %d group not found. Cannot create label.", hole_num)
                inkex.errormsg(
                    f"Error: Hole {hole_num} group not found. "
                    f"Please run Stage 3 (Auto-Place Holes) before adding labels."
                )
                return
            wrapper_group = None  # Will be created later

        # Remove existing label if present (prevents duplicate IDs)
        label_id = f"hole_label_{hole_num:02d}"
        existing_label = root.getElementById(label_id)

        if existing_label is not None:
            logger.info("Removing existing label for hole %d", hole_num)
            parent = existing_label.getparent()
            if parent is not None:
                parent.remove(existing_label)

        # Create label group and tee yardages
        label_group = self._create_hole_label_group(hole_num, par)
        if label_group is None:
            logger.error("Failed to create label group for hole %d", hole_num)
            return

        # Create tee yardages group
        tee_yardages = self._create_tee_yardages(hole_num)

        # Remove existing tee yardages if present
        if tee_yardages is not None:
            tee_id = f'tee_yardages_{hole_num:02d}'
            existing_tee = root.getElementById(tee_id)
            if existing_tee is not None:
                logger.info("Removing existing tee yardages for hole %d", hole_num)
                tee_parent = existing_tee.getparent()
                if tee_parent is not None:
                    tee_parent.remove(existing_tee)

        # RESTRUCTURE GROUPS TO AVOID CLIP ISSUES (only if not already done)
        # The hole_XX group has a clip applied which clips our labels
        # Solution: Create wrapper hierarchy: hole_XX/geo_XX (clipped) + tee_yardages_XX (not clipped)

        if not already_restructured:
            # Step 1: Find the 'top' group (parent of hole_XX)
            top_group = hole_group.getparent()
            if top_group is None:
                logger.error("Cannot find 'top' group - hole_%02d has no parent", hole_num)
                inkex.errormsg(f"Error: Hole {hole_num} group has no parent (expected 'top' group)")
                return

            # Step 2: Remember the original position in top group (for preserving outliner order)
            original_index = list(top_group).index(hole_group)
            logger.info("Found hole_%02d at index %d in 'top' group", hole_num, original_index)

            # Step 3: Rename hole_XX to geo_XX
            logger.info("Renaming hole_%02d to %s", hole_num, geo_id)
            hole_group.set('id', geo_id)
            hole_group.set('inkscape:label', geo_id)

            # Step 4: Remove geo_XX from top (will be moved into wrapper)
            top_group.remove(hole_group)
            logger.info("Removed %s from 'top' (will add to wrapper in correct z-order)", geo_id)

            # Step 5: Create new hole_XX wrapper and insert at same position
            wrapper_group = Group()
            wrapper_group.set('id', hole_id)
            wrapper_group.set('inkscape:label', hole_id)
            top_group.insert(original_index, wrapper_group)
            logger.info("Created new %s wrapper group at index %d in 'top' (preserving outliner order)", hole_id, original_index)
        else:
            logger.info("Skipping restructure - hole %d already has wrapper structure", hole_num)

        # Step 6: Add elements to hole_XX wrapper in correct z-order
        #
        # Transform logic:
        # - Labels are created with content at absolute page coordinates (e.g., CIRCLE_CENTER_X)
        # - wrapper_group (hole_XX) has identity transform (no rotation/scaling/position)
        # - geo_XX (inside wrapper) has the transforms from Stage 3, but labels are NOT children of geo_XX
        # - Since labels are children of wrapper (identity), they need NO inverse transform
        # - Label world position = wrapper_transform * label_content = identity * P = P ✓
        #
        # The inverse transform is only needed when labels are children of the transformed group,
        # but here they are siblings to the transformed group (geo_XX), both under wrapper (identity).
        #
        # Z-order (painting order, bottom to top):
        # 1. geo_XX (bottom layer - geometry with clip)
        # 2. tee_yardages (middle layer)
        # 3. hole_label (top layer)
        #
        # In SVG/DOM, later elements paint on top, so append in this order:

        logger.info("Adding elements to %s wrapper (identity transform) - no inverse needed", hole_id)

        # Ensure correct z-order: geo_XX → tee_yardages → hole_label
        # On subsequent runs, geo_XX is already in wrapper at the beginning

        if already_restructured:
            # geo_XX already in wrapper (at beginning) - append labels after it
            if tee_yardages is not None:
                wrapper_group.append(tee_yardages)
                logger.info("Added tee_yardages_%02d after %s (middle layer)", hole_num, geo_id)

            wrapper_group.append(label_group)
            logger.info("Added hole_label_%02d after %s (top layer)", hole_num, geo_id)
        else:
            # First run - append in order: geo_XX → tee_yardages → hole_label
            wrapper_group.append(hole_group)  # hole_group is geo_XX at this point
            logger.info("Added %s to %s wrapper (bottom layer)", geo_id, hole_id)

            if tee_yardages is not None:
                wrapper_group.append(tee_yardages)
                logger.info("Added tee_yardages_%02d to %s wrapper (middle layer)", hole_num, hole_id)

            wrapper_group.append(label_group)
            logger.info("Added hole_label_%02d to %s wrapper (top layer)", hole_num, hole_id)

        # ==== Generate terrain mask (white box with terrain cut out) ====
        # This prevents terrain features in right third from interfering with labels
        # Note: hole_group is geo_XX (renamed earlier in the method)
        try:
            self._generate_terrain_mask(hole_num, wrapper_group, hole_group)
        except Exception as e:
            logger.warning(f"Could not generate terrain mask for hole {hole_num}: {e}")

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

        Note: Tee box yardages are created separately and added to the hole group.

        All elements use the same coordinate system (document root), and inverse
        transforms ensure they appear at consistent positions across all pages
        when exported to PDF.

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
            Circle element with 0.125mm black stroke (half of standard 0.25mm)
        """
        circle = Circle(cx=str(cx_uu), cy=str(cy_uu), r=str(radius_uu))
        circle.style = Style({
            'fill': 'none',
            'stroke': '#000000',
            'stroke-width': '0.125mm'  # Half of standard 0.25mm stroke
        })
        return circle

    def _create_centered_hole_number(self, hole_num: int, circle_cx: float, circle_cy: float) -> Group:
        """
        Create hole number as glyph-based text and center it precisely in the circle.

        Uses GlyphLibrary for accurate measurements and positioning. Calculates the
        position offset to center the text bounding box within the circle.
        Font size is scaled to 90% of the user's font_size parameter.

        Args:
            hole_num: Hole number (1-18)
            circle_cx: Circle center X in user units
            circle_cy: Circle center Y in user units

        Returns:
            Group containing glyph paths for hole number, centered in circle
        """
        logger.info("Creating centered hole number %d at circle center (%.2f, %.2f)",
                   hole_num, circle_cx, circle_cy)

        # Use user's font_size parameter directly for hole number
        hole_number_font_size = int(self.options.font_size)

        # Add letter spacing: 5% of the font size for proper spacing between digits
        letter_spacing = hole_number_font_size * self.HOLE_NUMBER_LETTER_SPACING_SCALE

        logger.info(
            "Hole number font: %dpt, letter_spacing: %.2fpx (5%% of font size)",
            hole_number_font_size, letter_spacing
        )

        # Compose text using glyph library to get accurate dimensions
        # Note: We'll position at (0, 0) first to get dimensions, then reposition
        text_group, width, height = self.glyph_library.compose_text(
            str(hole_num),
            x=0,
            y=0,
            font_size=hole_number_font_size,
            spacing=letter_spacing  # 5% spacing between digits (e.g., "1 0" for hole 10)
        )

        logger.info(
            "Hole number '%s' composed: width=%.2fpx, height=%.2fpx",
            str(hole_num), width, height
        )

        # Calculate position to center the text bounding box in the circle
        # Text is positioned by bottom-left corner, so:
        # - Horizontal centering: x = circle_cx - (width / 2)
        # - Vertical centering: y = circle_cy + (height / 2)
        centered_x = circle_cx - (width / 2)
        centered_y = circle_cy + (height / 2)

        logger.info(
            "Centering in circle: circle_center=(%.2fpx, %.2fpx), text_size=(%.2fpx × %.2fpx), final_position=(%.2fpx, %.2fpx)",
            circle_cx, circle_cy, width, height, centered_x, centered_y
        )

        # Recompose at the centered position
        text_group, width, height = self.glyph_library.compose_text(
            str(hole_num),
            x=centered_x,
            y=centered_y,
            font_size=hole_number_font_size,
            spacing=letter_spacing
        )

        logger.info("Successfully created centered hole number %d at %dpt",
                   hole_num, hole_number_font_size)

        return text_group

    def _create_par_text(self, par: int, cx_uu: float, cy_uu: float, radius_uu: float) -> Group:
        """
        Create par text positioned below circle.

        Text is positioned with a proportional offset (35% of par font size) below
        the circle's bottom edge and scaled to 65% of the user's font_size parameter
        for visual hierarchy.

        Args:
            par: Par value (3-6)
            cx_uu: Circle center X in user units
            cy_uu: Circle center Y in user units
            radius_uu: Circle radius in user units

        Returns:
            Group containing glyph paths for par text
        """
        # Use user's par_font_size parameter directly
        par_font_size = int(self.options.par_font_size)

        # First compose to get dimensions for centering
        text_group, width, height = self.glyph_library.compose_text(
            str(par),
            x=0,
            y=0,
            font_size=par_font_size,
            spacing=0
        )

        # Position below circle with proportional offset (35% of par font size)
        offset_uu = par_font_size * self.PAR_TEXT_OFFSET_SCALE
        # Center horizontally under the circle
        text_x = cx_uu - (width / 2)
        # Position below circle bottom edge + offset (use bottom-left positioning)
        text_y = cy_uu + radius_uu + offset_uu

        # Recompose at final position
        text_group, width, height = self.glyph_library.compose_text(
            str(par),
            x=text_x,
            y=text_y,
            font_size=par_font_size,
            spacing=0
        )

        logger.info("Created par text '%s' at %dpt (65%% of %dpt base), offset=%.2fpx (35%% of font), size=(%.2f × %.2f) at (%.2f, %.2f)",
                   par, par_font_size, self.options.font_size, offset_uu, width, height, text_x, text_y)

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
        Font size is scaled to 65% of the user's font_size parameter.
        Letter spacing is set to 5% of the font size for improved readability.

        Args:
            text_content: The text to display
            x_uu: X position in user units (bottom-left corner)
            y_uu: Y position in user units (bottom-left corner)

        Returns:
            Tuple of (text_group, width, height) with accurate measurements
        """
        # Use user's tee_font_size parameter directly
        tee_font_size = int(self.options.tee_font_size)

        # Add letter spacing: 5% of the font size for better readability
        letter_spacing = tee_font_size * self.TEE_LETTER_SPACING_SCALE

        text_group, width, height = self.glyph_library.compose_text(
            text_content,
            x=x_uu,
            y=y_uu,
            font_size=tee_font_size,
            spacing=letter_spacing
        )

        return text_group, width, height

    def _create_tee_yardages(self, hole_num: int) -> Optional[Group]:
        """
        Create tee box yardage display with three-element formatting and bottom-up positioning.

        Uses GlyphLibrary for accurate text measurements and precise positioning. Unlike the
        previous font-based approximations, this provides exact dimensions for perfect alignment.

        Each line displays: "TeeName : 325" using three separate glyph groups:
        1. Tee name (right-aligned before colon using actual width)
        2. Colon (positioned with measured width)
        3. Yardage (right-aligned to boundary - each yardage aligns independently)

        Positioning strategy:
        - Anchor to lower right corner of top area bounding box (with margin)
        - Measure widest yardage to determine layout
        - Calculate positions working BACKWARDS from right boundary
        - Each yardage number is individually right-aligned (ensuring alignment regardless of width)
        - Measure actual colon width and tee name widths from glyph library
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

        # Convert anchor positions to user units
        try:
            colon_x_uu = self.svg.unittouu(f"{self.TEE_YARDAGE_ANCHOR_X}in")
            base_y_uu = self.svg.unittouu(f"{self.TEE_YARDAGE_ANCHOR_Y}in")

        except (ValueError, AttributeError) as e:
            logger.error("Failed to convert tee yardage units: %s", e)
            return None

        # Use user's tee_font_size parameter directly
        tee_font_size = int(self.options.tee_font_size)

        # Calculate proportional spacing as % of tee yardage font size
        element_spacing_uu = tee_font_size * self.TEE_ELEMENT_SPACING_SCALE  # 20% of tee font
        line_spacing_uu = tee_font_size * self.TEE_LINE_SPACING_SCALE  # 35% of tee font

        logger.info(
            "Tee yardage layout: anchor=(%.2f\", %.2f\"), font=%dpt, element_spacing=%.2fpx (20%% of font), line_spacing=%.2fpx (35%% of font)",
            self.TEE_YARDAGE_ANCHOR_X, self.TEE_YARDAGE_ANCHOR_Y,
            tee_font_size,
            element_spacing_uu, line_spacing_uu
        )

        # STEP 1: Measure actual colon width and find widest yardage using glyph library

        # Get actual colon width from glyph library (no approximations!)
        _, colon_width_uu, colon_height_uu = self._create_tee_text_element(
            ':', 0, 0
        )

        logger.info("Measured colon width: %.2fpx (actual measurement at %dpt)", colon_width_uu, tee_font_size)

        # Find the widest yardage to determine right edge alignment
        max_yardage_width_uu = 0.0
        for _, yardage in tees:
            _, yardage_width_uu, _ = self._create_tee_text_element(str(yardage), 0, 0)
            max_yardage_width_uu = max(max_yardage_width_uu, yardage_width_uu)

        logger.info("Widest yardage: %.2fpx", max_yardage_width_uu)

        # Calculate positions by working BACKWARDS from the anchor point (right edge)
        # The anchor point (colon_x_uu from constants) represents the RIGHT EDGE of the group
        # Layout: [name] <element_spacing> [:] <element_spacing> [yardage]
        # We want: right edge of yardage = anchor point
        right_edge_uu = colon_x_uu  # This is actually the right boundary (3.901")
        yardage_x_uu = right_edge_uu - max_yardage_width_uu  # Yardage right-aligns to boundary
        colon_x_uu = yardage_x_uu - element_spacing_uu - colon_width_uu  # Colon before yardage

        # STEP 2: Create all elements at their correct positions with accurate measurements
        created_elements: list[tuple[Group, Group, Group]] = []
        current_y_uu = base_y_uu

        # Process tees in reverse order (bottom to top)
        # This ensures Tee 1 appears at top, Tee 6 at bottom (conventional yardage book order)
        for idx, (name, yardage) in enumerate(reversed(tees)):
            # Measure name width to calculate right-aligned position
            _, name_width_uu, _ = self._create_tee_text_element(name, 0, 0)

            # Position name so its right edge is at (colon_x - spacing)
            name_x_uu = colon_x_uu - element_spacing_uu - name_width_uu

            # Measure THIS yardage's width to calculate right-aligned position
            _, this_yardage_width_uu, _ = self._create_tee_text_element(str(yardage), 0, 0)

            # Position yardage so its right edge aligns with the right boundary
            # This ensures all yardages are right-aligned regardless of their width
            this_yardage_x_uu = right_edge_uu - this_yardage_width_uu

            # Create the three elements for this line with measured positions
            tee_name_elem, _, _ = self._create_tee_text_element(
                name, name_x_uu, current_y_uu
            )
            colon_elem, _, _ = self._create_tee_text_element(
                ':', colon_x_uu, current_y_uu
            )
            yardage_elem, _, _ = self._create_tee_text_element(
                str(yardage), this_yardage_x_uu, current_y_uu
            )

            # Store elements for grouping
            created_elements.append((tee_name_elem, colon_elem, yardage_elem))

            logger.debug(
                "Tee line %d (from bottom): '%s' : %d at y=%.2f (name_x=%.2f, colon_x=%.2f, yardage_x=%.2f)",
                idx, name, yardage, current_y_uu, name_x_uu, colon_x_uu, this_yardage_x_uu
            )

            # Position next line above this one
            current_y_uu -= line_spacing_uu

        # Create final group and add elements to it
        tee_group = Group()
        tee_group.set('id', f'tee_yardages_{hole_num:02d}')
        tee_group.label = f'tee_yardages_{hole_num:02d}'

        # Add elements to group (reverse to maintain top-to-bottom order in XML)
        for tee_name_elem, colon_elem, yardage_elem in reversed(created_elements):
            tee_group.append(tee_name_elem)
            tee_group.append(colon_elem)
            tee_group.append(yardage_elem)

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
