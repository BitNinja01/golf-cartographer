#!/usr/bin/env python3
"""
Test script to demonstrate coordinate system behavior when cloning elements
from one SVG into another.

This will:
1. Load the glyph library SVG
2. Clone all glyph paths
3. Position duplicates 50mm below the originals
"""

import inkex
from inkex import load_svg, PathElement, Transform
import os


class TestImportClone(inkex.EffectExtension):
    """Test importing and cloning SVG elements."""

    def effect(self):
        """Test importing glyphs and positioning them."""
        inkex.utils.debug("=== SIMPLE GLYPH IMPORT TEST ===")
        inkex.utils.debug("")
        inkex.utils.debug("This test demonstrates:")
        inkex.utils.debug("1. Library glyphs are always 24pt")
        inkex.utils.debug("2. Both documents use millimeters (1 user unit = 1mm)")
        inkex.utils.debug("3. Glyphs import at their native size")
        inkex.utils.debug("4. We only need to cancel baked-in positions")
        inkex.utils.debug("")

        # Load the glyph library
        script_dir = os.path.dirname(os.path.abspath(__file__))
        library_path = os.path.join(script_dir, 'glyph_libraries/JetBrainsMono Nerd Font.svg')

        library_svg = load_svg(library_path)
        library_root = library_svg.getroot()

        current_layer = self.svg.get_current_layer()

        # Import the first 10 digits and position them at (100, 100)
        inkex.utils.debug("--- Importing Digits 0-9 at (100, 100) ---")
        target_x = 100
        target_y = 100
        current_x = target_x

        for digit in "0123456789":
            glyph_id = f"glyph-{digit}"

            # Find the glyph in library
            for element in library_root.iter():
                if isinstance(element, PathElement) and element.get('id') == glyph_id:
                    bbox = element.bounding_box()
                    if bbox:
                        # Create new path
                        new_path = PathElement()
                        new_path.set('d', element.get('d'))
                        if element.get('style'):
                            new_path.set('style', element.get('style'))
                        new_path.set('id', f"{glyph_id}_test")

                        # Position at target location
                        # Cancel out library position (bbox.left, bbox.top)
                        final_x = current_x - bbox.left
                        final_y = target_y - bbox.top

                        new_path.transform = Transform(f"translate({final_x}, {final_y})")

                        current_layer.append(new_path)

                        # Move to next position
                        current_x += bbox.width + 2  # 2mm spacing

                        inkex.utils.debug(f"  '{digit}': {bbox.width:.2f}mm × {bbox.height:.2f}mm")
                    break

        inkex.utils.debug("")
        inkex.utils.debug(f"✓ Imported digits at native 24pt size")
        inkex.utils.debug(f"✓ Positioned at ({target_x}, {target_y})")
        inkex.utils.debug("")
        inkex.utils.debug("Visual check:")
        inkex.utils.debug("  - Digits should appear at (100mm, 100mm) from top-left")
        inkex.utils.debug("  - Each digit should be ~6mm tall (24pt)")
        inkex.utils.debug("  - No scaling applied (scale_factor = 1.0)")


if __name__ == '__main__':
    TestImportClone().run()
