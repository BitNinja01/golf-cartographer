#!/usr/bin/env python3
"""
Prepare Glyph Library - Inkscape Extension

Creates text elements for glyph library preparation with proper spacing and grouping.
Outputs digits (0-9), capitals (A-Z), lowercases (a-z), and symbols (space, :.,- etc.)
as individual text elements.
Visual order is left-to-right (0→9, A→Z, a→z, symbols), but DOM order is reversed for
proper stacking after conversion to paths.
Each character is pre-assigned the correct glyph ID (glyph-0, glyph-A, glyph-:, etc.)
so they're ready for reference after Path → Object to Path conversion.
Removes all existing layers to ensure a clean document.

Part of Golf Cartographer extension suite.
"""

import inkex
from inkex import TextElement, Group
import subprocess
import os
from pathlib import Path


class PrepareGlyphLibrary(inkex.EffectExtension):
    """Creates prepared text elements for glyph library conversion."""

    def add_arguments(self, pars):
        """Add command line arguments."""
        pars.add_argument("--notebook", type=str, default="prepare", help="Active notebook tab")
        pars.add_argument("--font_family", type=str, default="Arial", help="Font family name")
        pars.add_argument("--font_style", type=str, default="normal", help="Font style")

    def effect(self):
        """Main execution method."""
        # Check which tab is active
        if self.options.notebook == "show_fonts":
            self.show_available_fonts()
            return  # Exit after showing fonts

        # Otherwise, proceed with glyph preparation
        # Get font parameters
        font_family = self.options.font_family
        font_style = self.options.font_style

        # Character sets (in normal order for left-to-right display)
        digits = "0123456789"
        capitals = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        lowercases = "abcdefghijklmnopqrstuvwxyz"
        symbols = ".:,-'\"()/"  # Period, colon, comma, hyphen, quotes, parens, slash

        # Starting position and spacing (in mm, converted to user units)
        start_x_mm = 5
        start_y_mm = 15  # Baseline position (first row)
        spacing_mm = 7  # 7mm between characters horizontally
        row_spacing_mm = 10  # 10mm between rows vertically
        font_size_pt = 24

        # Convert mm and pt to user units
        start_x = self.svg.unittouu(f"{start_x_mm}mm")
        start_y = self.svg.unittouu(f"{start_y_mm}mm")
        spacing = self.svg.unittouu(f"{spacing_mm}mm")
        font_size_uu = self.svg.unittouu(f"{font_size_pt}pt")

        # Create groups for each character set
        digits_group = self.create_character_group(
            digits,
            font_family,
            font_style,
            font_size_uu,
            start_x,
            start_y,
            spacing,
            "digits"
        )

        # Position capitals below digits
        capitals_start_y = start_y + self.svg.unittouu(f"{row_spacing_mm}mm")
        capitals_group = self.create_character_group(
            capitals,
            font_family,
            font_style,
            font_size_uu,
            start_x,
            capitals_start_y,
            spacing,
            "capitals"
        )

        # Position lowercases below capitals
        lowercases_start_y = capitals_start_y + self.svg.unittouu(f"{row_spacing_mm}mm")
        lowercases_group = self.create_character_group(
            lowercases,
            font_family,
            font_style,
            font_size_uu,
            start_x,
            lowercases_start_y,
            spacing,
            "lowercases"
        )

        # Position symbols below lowercases
        symbols_start_y = lowercases_start_y + self.svg.unittouu(f"{row_spacing_mm}mm")
        symbols_group = self.create_character_group(
            symbols,
            font_family,
            font_style,
            font_size_uu,
            start_x,
            symbols_start_y,
            spacing,
            "symbols"
        )

        # Add groups to document
        self.svg.append(digits_group)
        self.svg.append(capitals_group)
        self.svg.append(lowercases_group)
        self.svg.append(symbols_group)

        # Remove any existing layers from the document
        self.remove_all_layers()

        # Resize canvas to fit content with padding
        self.resize_canvas_to_content(padding_mm=5)

    def get_char_name(self, char):
        """
        Get the name to use for a character in glyph IDs.

        Special characters use descriptive names (e.g., 'colon' for ':')
        to create valid XML IDs. Regular alphanumeric characters use themselves.

        Args:
            char: Single character

        Returns:
            String name for use in glyph ID (e.g., 'colon', 'A', '5')
        """
        # Map special characters to descriptive names
        special_chars = {
            ':': 'colon',
            '.': 'period',
            ',': 'comma',
            '-': 'dash',
            "'": 'apostrophe',
            '"': 'quote',
            '(': 'lparen',
            ')': 'rparen',
            '/': 'slash',
            ' ': 'space',
        }
        return special_chars.get(char, char)

    def create_character_group(self, characters, font_family, font_style, font_size_uu,
                                start_x, start_y, spacing, group_name):
        """
        Create a group of text elements for a character set.

        Args:
            characters: String of characters to create
            font_family: Font family name
            font_style: Font style (normal, bold, italic, bold italic)
            font_size_uu: Font size in user units (converted from 24pt)
            start_x: Starting X position in user units
            start_y: Y position (baseline) in user units
            spacing: Horizontal spacing between characters in user units
            group_name: Name/ID for the group

        Returns:
            Group element containing all text elements
        """
        group = Group()
        group.set('id', f'glyph-prep-{group_name}')
        group.label = f'Glyph Prep: {group_name.capitalize()}'

        current_x = start_x
        text_elements = []  # Collect elements to reverse order

        for char in characters:
            # Create text element
            text_elem = TextElement()
            text_elem.text = char

            # Set position
            text_elem.set('x', str(current_x))
            text_elem.set('y', str(start_y))

            # Build font style string
            font_weight = 'bold' if 'bold' in font_style else 'normal'
            font_style_prop = 'italic' if 'italic' in font_style else 'normal'

            # Set text styling (font-size in user units, no unit suffix)
            text_elem.style = {
                'font-family': font_family,
                'font-size': f'{font_size_uu}px',
                'font-weight': font_weight,
                'font-style': font_style_prop,
                'fill': '#000000',
                'text-anchor': 'start',
            }

            # Set unique ID using glyph naming convention
            # Special characters use descriptive names (glyph-colon, glyph-period, etc.)
            # Regular characters use the character itself (glyph-A, glyph-0, etc.)
            char_name = self.get_char_name(char)
            char_id = f"glyph-{char_name}"
            text_elem.set('id', char_id)

            # Collect element
            text_elements.append(text_elem)

            # Advance position
            current_x += spacing

        # Add elements in reverse order to group (for proper stacking)
        # Visual order: left-to-right (0-9, A-Z, a-z)
        # DOM order: reversed (9-0, Z-A, z-a) for better selection/stacking
        for text_elem in reversed(text_elements):
            group.append(text_elem)

        return group

    def set_canvas_dimensions(self, width_mm, height_mm):
        """
        Set the canvas (page) dimensions.

        Args:
            width_mm: Width in millimeters
            height_mm: Height in millimeters
        """
        # Convert mm to user units
        width_uu = self.svg.unittouu(f"{width_mm}mm")
        height_uu = self.svg.unittouu(f"{height_mm}mm")

        # Set viewBox and width/height attributes
        self.svg.set('viewBox', f'0 0 {width_uu} {height_uu}')
        self.svg.set('width', f'{width_mm}mm')
        self.svg.set('height', f'{height_mm}mm')

    def resize_canvas_to_content(self, padding_mm=5):
        """
        Resize the canvas to fit all content with specified padding.

        Args:
            padding_mm: Padding to add around content in millimeters
        """
        # Get bounding box of all content in the document
        bbox = None
        for element in self.svg:
            try:
                elem_bbox = element.bounding_box()
                if elem_bbox is not None:
                    if bbox is None:
                        bbox = elem_bbox
                    else:
                        bbox += elem_bbox
            except:
                # Some elements might not have bounding boxes
                pass

        if bbox is None:
            # Fallback to default size if no content found
            self.set_canvas_dimensions(width_mm=200, height_mm=60)
            return

        # Convert padding to user units
        padding_uu = self.svg.unittouu(f"{padding_mm}mm")

        # Add extra padding for top and right to account for text rendering quirks
        # Text bounding boxes don't always include full ascenders/descenders
        padding_top_uu = self.svg.unittouu(f"{padding_mm + 3}mm")  # Extra 3mm on top
        padding_right_uu = self.svg.unittouu(f"{padding_mm + 2}mm")  # Extra 2mm on right

        # Calculate canvas dimensions with asymmetric padding
        width_uu = bbox.width + padding_uu + padding_right_uu  # left + right
        height_uu = bbox.height + padding_top_uu + padding_uu  # top + bottom

        # Convert back to mm for setting attributes
        width_mm = self.svg.uutounit(width_uu, 'mm')
        height_mm = self.svg.uutounit(height_uu, 'mm')

        # Adjust viewBox to start at content origin minus padding
        viewbox_x = bbox.left - padding_uu
        viewbox_y = bbox.top - padding_top_uu

        # Set viewBox and dimensions
        self.svg.set('viewBox', f'{viewbox_x} {viewbox_y} {width_uu} {height_uu}')
        self.svg.set('width', f'{width_mm}mm')
        self.svg.set('height', f'{height_mm}mm')

    def remove_all_layers(self):
        """
        Remove all layer elements from the document.

        Layers are <g> elements with inkscape:groupmode="layer" attribute.
        This ensures a clean document with only the glyph preparation groups.
        """
        # Find all layers (groups with groupmode="layer")
        layers = self.svg.findall('.//{http://www.w3.org/2000/svg}g[@{http://www.inkscape.org/namespaces/inkscape}groupmode="layer"]')

        # Remove each layer
        for layer in layers:
            layer.getparent().remove(layer)

    def show_available_fonts(self):
        """
        Show all available fonts using Inkscape's debug message system.

        Uses fontconfig (fc-list) on Linux, which is the same system
        Inkscape uses to enumerate fonts.
        """
        fonts = self.get_system_fonts()

        # Print header
        inkex.errormsg("=" * 60)
        inkex.errormsg(f"AVAILABLE SYSTEM FONTS ({len(fonts)} found)")
        inkex.errormsg("=" * 60)
        inkex.errormsg("")

        # Print all fonts in alphabetical order
        for font in sorted(fonts):
            inkex.errormsg(f"  {font}")

        inkex.errormsg("")
        inkex.errormsg("=" * 60)
        inkex.errormsg("NOTES:")
        inkex.errormsg("- Font names are case-sensitive")
        inkex.errormsg("- Use these exact names in the Font Family field")
        inkex.errormsg("- Select style (Regular/Bold/Italic) using Font Style dropdown")
        inkex.errormsg("=" * 60)

    def get_system_fonts(self):
        """
        Get list of available font families from the system.

        Returns:
            set: Set of unique font family names
        """
        fonts = set()

        # Try fontconfig (fc-list) - standard on Linux, what Inkscape uses
        try:
            result = subprocess.run(
                ['fc-list', ':', 'family'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse fc-list output
                # Format: "Font Family,Alternative Name:style=Regular"
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line:
                        # Extract family name (before colon or comma)
                        family = line.split(':')[0].split(',')[0].strip()
                        if family:
                            fonts.add(family)

                return fonts

        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Fallback: try to find common font directories
        font_dirs = [
            Path.home() / '.fonts',
            Path.home() / '.local' / 'share' / 'fonts',
            Path('/usr/share/fonts'),
            Path('/usr/local/share/fonts'),
        ]

        for font_dir in font_dirs:
            if font_dir.exists():
                # Find all font files
                for ext in ['*.ttf', '*.otf', '*.TTF', '*.OTF']:
                    for font_file in font_dir.rglob(ext):
                        # Extract family name from filename (rough approximation)
                        name = font_file.stem
                        # Remove common style suffixes
                        for suffix in ['-Regular', '-Bold', '-Italic', '-BoldItalic',
                                      'Regular', 'Bold', 'Italic', 'BoldItalic']:
                            if name.endswith(suffix):
                                name = name[:-len(suffix)]
                        fonts.add(name.strip())

        # If still no fonts found, return common defaults
        if not fonts:
            fonts = {
                'Arial', 'Helvetica', 'Times New Roman', 'Courier New',
                'DejaVu Sans', 'DejaVu Serif', 'Liberation Sans',
                'Liberation Serif', 'Ubuntu', 'Roboto'
            }

        return fonts


if __name__ == '__main__':
    PrepareGlyphLibrary().run()
