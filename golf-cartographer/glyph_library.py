#!/usr/bin/env python3
"""
Glyph Library System for Inkscape Extensions

Loads pre-converted glyph paths from SVG libraries and composes text by
positioning cloned glyphs. Provides precise, measurable text layout that
isn't possible with native TextElements in the inkex API.

Architecture:
- Each character is stored as a path element with id="glyph-X" in an SVG file
- Library glyphs are ALWAYS at 24pt font size
- Glyphs are copied as new path elements and positioned on-demand to compose text
- Bottom-left alignment ensures consistent baseline positioning
- Simple scaling: scale_factor = desired_font_size / 24.0

Usage:
    library = GlyphLibrary('glyph_libraries/arial_24pt.svg')
    text_group, width, height = library.compose_text(
        "350", x=100, y=100, font_size=24, spacing=2
    )
"""

import os
from inkex import Transform, Group, PathElement, load_svg


class GlyphLibrary:
    """Loads and manages a glyph library from an SVG file."""

    def __init__(self, library_path):
        """
        Load glyph library from SVG file.

        Args:
            library_path: Path to SVG file containing glyph paths (relative to extension dir)
        """
        self.library_path = library_path
        self.glyphs = {}  # Cache: {char: path_element}
        self._load_library()

    def _load_library(self):
        """Parse SVG file and extract all glyph path elements."""
        # Get absolute path relative to this script's location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, self.library_path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Glyph library not found: {full_path}")

        # Parse SVG file
        svg = load_svg(full_path)
        root = svg.getroot()

        # Find all path elements with glyph IDs
        for element in root.iter():
            if isinstance(element, PathElement):
                elem_id = element.get('id', '')
                if elem_id.startswith('glyph-'):
                    # Extract character from ID (e.g., "glyph-A" -> "A")
                    char = elem_id.replace('glyph-', '', 1)

                    # Handle special character names (must match prepare_glyph_library.py)
                    special_names = {
                        'colon': ':',
                        'period': '.',
                        'comma': ',',
                        'dash': '-',
                        'apostrophe': "'",
                        'quote': '"',
                        'lparen': '(',
                        'rparen': ')',
                        'slash': '/',
                        'space': ' ',
                    }
                    char = special_names.get(char, char)

                    # Store the path element
                    self.glyphs[char] = element

    def get_glyph(self, char):
        """
        Get glyph path element for a character.

        Args:
            char: Single character to get glyph for

        Returns:
            PathElement or None if character not found in library
        """
        return self.glyphs.get(char)

    def compose_text(self, text, x, y, font_size=24, spacing=2):
        """
        Compose text by positioning glyph copies with bottom-left alignment.

        Each glyph is positioned so that:
        - Bottom edges are aligned (same baseline)
        - Left edge of each glyph follows the right edge of the previous glyph
        - Spacing is added between glyphs

        Args:
            text: String to compose
            x: Starting x position (left edge of first glyph) in user units
            y: Baseline y position (bottom edge of all glyphs) in user units
            font_size: Target font size in POINTS (library is always 24pt)
            spacing: Horizontal spacing between glyphs (in user units)

        Returns:
            tuple: (group_element, total_width, total_height)
                - group_element: Group containing all positioned glyphs
                - total_width: Total width of composed text in user units
                - total_height: Total height of composed text in user units
        """
        # SIMPLE: Library is always 24pt, scale accordingly
        scale_factor = font_size / 24.0

        # Create group to hold all glyphs
        group = Group()
        group.label = f"text-{text}"

        current_x = x
        max_height = 0
        baseline_y = y

        for char in text:
            # Handle space character with fixed width
            if char == ' ':
                # Space width: at 24pt (native), typical char width is ~4mm, space is ~40% = 1.6mm
                # Scale proportionally for target font size
                space_width = scale_factor * 1.6
                current_x += space_width
                # Space height: at 24pt (native), typical glyph height is ~6.3mm
                # Scale proportionally for target font size
                space_height = scale_factor * 6.3
                max_height = max(max_height, space_height)
                continue

            glyph = self.get_glyph(char)
            if glyph is None:
                # Character not in library - warn and skip it
                import inkex
                inkex.utils.debug(f"WARNING: Character '{char}' not found in glyph library '{self.library_path}'")
                continue

            # Get the glyph's bounding box (in library's coordinate system)
            bbox = glyph.bounding_box()
            if bbox is None or bbox.width == 0:
                # Skip empty/invalid glyphs
                continue

            # Create NEW path element (don't clone across documents - that doesn't work!)
            new_path = PathElement()

            # Copy the path data
            new_path.set('d', glyph.get('d'))

            # Copy style
            if glyph.get('style'):
                new_path.set('style', glyph.get('style'))

            # Calculate dimensions after scaling
            glyph_height = bbox.height * scale_factor
            glyph_width = bbox.width * scale_factor

            # Calculate position with bottom-left alignment
            # The bbox tells us where the glyph is positioned in the library
            # We need to:
            # 1. Cancel out the library position (bbox.left, bbox.bottom)
            # 2. Move to our target position (current_x, baseline_y)
            # 3. Account for scaling

            final_x = current_x - (bbox.left * scale_factor)
            final_y = baseline_y - (bbox.bottom * scale_factor)

            # Apply transform: translate to position, then scale
            new_path.transform = Transform(f"translate({final_x}, {final_y}) scale({scale_factor})")

            # Add to group
            group.add(new_path)

            # Update position for next glyph
            current_x += glyph_width + spacing
            max_height = max(max_height, glyph_height)

        # Calculate total dimensions
        total_width = current_x - x - spacing if len(group) > 0 else 0
        total_height = max_height

        return group, total_width, total_height

    def get_available_chars(self):
        """
        Get list of available characters in this library.

        Returns:
            list: Sorted list of available characters
        """
        return sorted(self.glyphs.keys())


# Convenience function for quick text composition
def compose_text(library_path, text, x, y, font_size=24, spacing=2):
    """
    Quick utility function to compose text without explicitly creating a GlyphLibrary instance.

    Args:
        library_path: Path to glyph library SVG file
        text: String to compose
        x, y: Position
        font_size: Font size (library is always 24pt)
        spacing: Glyph spacing

    Returns:
        tuple: (group_element, total_width, total_height)
    """
    library = GlyphLibrary(library_path)
    return library.compose_text(text, x, y, font_size, spacing)
