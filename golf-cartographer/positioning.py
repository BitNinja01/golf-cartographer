#!/usr/bin/env python3
"""
Positioning Utility Tool for Golf Cartographer

This is a placeholder utility tool for positioning-related operations.
Provides various positioning modes and alignment options for yardage book elements.

Part of the Golf Cartographer Inkscape Extension Suite.
"""

import inkex
from inkex import Transform


class PositioningTool(inkex.EffectExtension):
    """
    Positioning utility tool for golf yardage book elements.

    This tool provides placeholder functionality for positioning operations including:
    - Absolute/relative positioning
    - Alignment options (9 positions)
    - Grid snapping
    - Batch positioning of multiple elements
    """

    def add_arguments(self, pars):
        """Define command-line arguments matching the .inx file."""
        # No arguments needed - tool runs without user input
        pass

    def effect(self):
        """
        Test the Glyph Library system - loading glyphs and composing text.
        """
        from glyph_library import GlyphLibrary
        from inkex import Rectangle

        inkex.utils.debug("=== GLYPH LIBRARY TEST ===")
        inkex.utils.debug("Testing JetBrainsMono Nerd Font glyph library")
        inkex.utils.debug("")

        current_layer = self.svg.get_current_layer()

        try:
            # Test 1: Load the glyph library
            inkex.utils.debug("--- Test 1: Loading Glyph Library ---")
            library = GlyphLibrary('glyph_libraries/JetBrainsMono Nerd Font.svg')
            inkex.utils.debug(f"✓ Library loaded successfully")
            inkex.utils.debug(f"  Available characters: {len(library.glyphs)}")

            # Show first 20 characters
            available = library.get_available_chars()
            inkex.utils.debug(f"  Sample chars: {' '.join(available[:20])}")
            inkex.utils.debug("")

            # DIAGNOSTIC: Measure actual glyph dimensions
            inkex.utils.debug("--- DIAGNOSTIC: Raw Glyph Dimensions (24pt) ---")
            test_chars = ['0', '3', '5', 'A', 'H']
            for char in test_chars:
                glyph = library.get_glyph(char)
                if glyph is not None:
                    bbox = glyph.bounding_box()
                    if bbox is not None:
                        inkex.utils.debug(f"  '{char}': width={bbox.width:.4f}, height={bbox.height:.4f}")
            inkex.utils.debug("")

            # Test 2: Compose simple text at 24pt
            inkex.utils.debug("--- Test 2: Simple Text at 24pt ---")
            inkex.utils.debug(f"  Scale factor: 24/24 = 1.0 (no scaling)")

            text1, width1, height1 = library.compose_text(
                "350", x=20, y=40, font_size=24, spacing=2
            )
            current_layer.append(text1)

            # VALIDATION: Add marker at specified position and check actual bbox
            self._add_position_marker(current_layer, 20, 40, "green")
            actual_bbox = text1.bounding_box()
            inkex.utils.debug(f"✓ Composed '350' at (20, 40)")
            inkex.utils.debug(f"  Width: {width1:.2f} units, Height: {height1:.2f} units")
            inkex.utils.debug(f"  Actual bbox: left={actual_bbox.left:.2f}, bottom={actual_bbox.bottom:.2f}, top={actual_bbox.top:.2f}")
            inkex.utils.debug(f"  Expected: left=20, bottom=40")
            inkex.utils.debug("")

            # Test 3: Compose text at 18pt (smaller)
            inkex.utils.debug("--- Test 3: Text at 18pt ---")
            inkex.utils.debug(f"  Scale factor: 18/24 = 0.75 (75% size)")
            text2, width2, height2 = library.compose_text(
                "Par 4", x=20, y=60, font_size=18, spacing=2
            )
            current_layer.append(text2)

            # VALIDATION: Add marker at specified position and check actual bbox
            self._add_position_marker(current_layer, 20, 60, "green")
            actual_bbox2 = text2.bounding_box()
            inkex.utils.debug(f"✓ Composed 'Par 4' at (20, 60)")
            inkex.utils.debug(f"  Width: {width2:.2f} units, Height: {height2:.2f} units")
            inkex.utils.debug(f"  Actual bbox: left={actual_bbox2.left:.2f}, bottom={actual_bbox2.bottom:.2f}, top={actual_bbox2.top:.2f}")
            inkex.utils.debug(f"  Expected: left=20, bottom=60")
            inkex.utils.debug("")

            # Test 4: Bottom alignment verification
            inkex.utils.debug("--- Test 4: Bottom Alignment Test ---")
            # Create three strings at same baseline (y=100)
            baseline_y = 100

            text3a, width3a, height3a = library.compose_text(
                "ABC", x=20, y=baseline_y, font_size=24, spacing=2
            )
            current_layer.append(text3a)
            self._add_position_marker(current_layer, 20, baseline_y, "green")

            text3b, width3b, height3b = library.compose_text(
                "xyz", x=70, y=baseline_y, font_size=24, spacing=2
            )
            current_layer.append(text3b)
            self._add_position_marker(current_layer, 70, baseline_y, "green")

            text3c, width3c, height3c = library.compose_text(
                "123", x=120, y=baseline_y, font_size=24, spacing=2
            )
            current_layer.append(text3c)
            self._add_position_marker(current_layer, 120, baseline_y, "green")

            # Draw baseline reference line
            from inkex import Line
            baseline = Line()
            baseline.set('x1', '10')
            baseline.set('y1', str(baseline_y))
            baseline.set('x2', '180')
            baseline.set('y2', str(baseline_y))
            baseline.style = {'stroke': '#ff0000', 'stroke-width': '0.5', 'stroke-dasharray': '2,2'}
            current_layer.append(baseline)

            # VALIDATION: Check actual bottom positions
            bbox3a = text3a.bounding_box()
            bbox3b = text3b.bounding_box()
            bbox3c = text3c.bounding_box()

            inkex.utils.debug(f"✓ Created three text groups on baseline y={baseline_y}")
            inkex.utils.debug(f"  'ABC' at x=20: {width3a:.2f}×{height3a:.2f}, actual bottom={bbox3a.bottom:.2f}")
            inkex.utils.debug(f"  'xyz' at x=70: {width3b:.2f}×{height3b:.2f}, actual bottom={bbox3b.bottom:.2f}")
            inkex.utils.debug(f"  '123' at x=120: {width3c:.2f}×{height3c:.2f}, actual bottom={bbox3c.bottom:.2f}")
            inkex.utils.debug(f"  Red dashed line shows shared baseline (green markers at each specified position)")
            inkex.utils.debug("")

            # Test 5: Right-align test (now possible with accurate measurements!)
            inkex.utils.debug("--- Test 5: Right Alignment Test ---")
            right_edge = 180
            # Compose at x=0 first to get width, then position
            temp_group, temp_width, temp_height = library.compose_text(
                "RIGHT", x=0, y=0, font_size=24, spacing=2
            )
            # Now create it at the correct position
            text4, width4, height4 = library.compose_text(
                "RIGHT", x=right_edge - temp_width, y=140, font_size=24, spacing=2
            )
            current_layer.append(text4)

            # Draw right edge reference line
            from inkex import Line
            right_line = Line()
            right_line.set('x1', str(right_edge))
            right_line.set('y1', '125')
            right_line.set('x2', str(right_edge))
            right_line.set('y2', '155')
            right_line.style = {'stroke': '#0000ff', 'stroke-width': '0.5', 'stroke-dasharray': '2,2'}
            current_layer.append(right_line)

            inkex.utils.debug(f"✓ Right-aligned 'RIGHT' to x={right_edge}")
            inkex.utils.debug(f"  Text width: {width4:.2f} units")
            inkex.utils.debug(f"  Starting x: {right_edge - width4:.2f}")
            inkex.utils.debug(f"  Blue dashed line shows right edge")
            inkex.utils.debug("")

            # Test 6: Text at 48pt (double size)
            inkex.utils.debug("--- Test 6: Text at 48pt ---")
            inkex.utils.debug(f"  Scale factor: 48/24 = 2.0 (200% size)")
            text5, width5, height5 = library.compose_text(
                "BIG", x=20, y=200, font_size=48, spacing=3
            )
            current_layer.append(text5)

            # VALIDATION: Add marker at specified position and check actual bbox
            self._add_position_marker(current_layer, 20, 200, "green")
            actual_bbox5 = text5.bounding_box()
            inkex.utils.debug(f"✓ Composed 'BIG' at (20, 200)")
            inkex.utils.debug(f"  Width: {width5:.2f} units, Height: {height5:.2f} units")
            inkex.utils.debug(f"  Actual bbox: left={actual_bbox5.left:.2f}, bottom={actual_bbox5.bottom:.2f}, top={actual_bbox5.top:.2f}")
            inkex.utils.debug(f"  Expected: left=20, bottom=200")
            inkex.utils.debug("")

            inkex.utils.debug("=== ALL TESTS COMPLETE ===")
            inkex.utils.debug("✓ Glyph library system is working!")
            inkex.utils.debug("")
            inkex.utils.debug("Visual checks:")
            inkex.utils.debug("  1. All text should be readable and properly formed")
            inkex.utils.debug("  2. ABC, xyz, 123 should align on red baseline")
            inkex.utils.debug("  3. 'RIGHT' should align to blue vertical line")
            inkex.utils.debug("  4. Font sizes should be visibly different")

        except FileNotFoundError as e:
            inkex.utils.debug(f"✗ ERROR: {e}")
            inkex.utils.debug("")
            inkex.utils.debug("Make sure the glyph library file exists:")
            inkex.utils.debug("  golf-cartographer/glyph_libraries/JetBrainsMono Nerd Font.svg")

        except Exception as e:
            inkex.utils.debug(f"✗ UNEXPECTED ERROR: {e}")
            import traceback
            inkex.utils.debug(traceback.format_exc())

    def _get_target_elements(self):
        """Get elements to process based on apply_to option."""
        if self.options.apply_to == "selection":
            # Use selected elements
            elements = list(self.svg.selection.values())
        elif self.options.apply_to == "layer":
            # Use all elements in current layer
            current_layer = self.svg.get_current_layer()
            if current_layer is not None:
                elements = list(current_layer.iter())
            else:
                elements = []
        else:  # "all"
            # Use all elements in document
            elements = list(self.svg.descendants())

        return elements

    def _snap_to_grid(self, value, grid_size):
        """Snap a coordinate value to the nearest grid point."""
        return round(value / grid_size) * grid_size

    def _position_element(self, element, target_x, target_y, index):
        """
        Apply positioning to a single element (placeholder implementation).

        Args:
            element: The SVG element to position
            target_x: Target X coordinate in user units
            target_y: Target Y coordinate in user units
            index: Element index for debug output
        """
        # Get element bounding box
        try:
            bbox = element.bounding_box()
            if bbox is None:
                return
        except Exception:
            return

        # Calculate offset based on alignment
        offset_x, offset_y = self._calculate_alignment_offset(bbox)

        # Calculate final position
        final_x = target_x - offset_x
        final_y = target_y - offset_y

        # Apply position based on mode
        if self.options.position_mode == "absolute":
            # Absolute positioning (placeholder - would set absolute coordinates)
            inkex.utils.debug(f"  Element {index}: Would move to absolute ({final_x:.2f}, {final_y:.2f})")
        elif self.options.position_mode == "relative":
            # Relative positioning (placeholder - would offset from current position)
            inkex.utils.debug(f"  Element {index}: Would move relative by ({final_x:.2f}, {final_y:.2f})")
        else:  # auto
            # Auto positioning (placeholder - would use smart positioning logic)
            inkex.utils.debug(f"  Element {index}: Would auto-position near ({final_x:.2f}, {final_y:.2f})")

    def _calculate_alignment_offset(self, bbox):
        """
        Calculate offset based on alignment anchor point.

        Args:
            bbox: Element bounding box

        Returns:
            Tuple of (offset_x, offset_y) for the chosen alignment
        """
        # Alignment mapping
        alignment_map = {
            "top-left": (0, 0),
            "top-center": (bbox.width / 2, 0),
            "top-right": (bbox.width, 0),
            "center-left": (0, bbox.height / 2),
            "center": (bbox.width / 2, bbox.height / 2),
            "center-right": (bbox.width, bbox.height / 2),
            "bottom-left": (0, bbox.height),
            "bottom-center": (bbox.width / 2, bbox.height),
            "bottom-right": (bbox.width, bbox.height),
        }

        return alignment_map.get(self.options.alignment, (0, 0))

    def _add_position_marker(self, layer, x, y, color):
        """
        Add a crosshair marker at the specified position for validation.

        Args:
            layer: The layer to add the marker to
            x: X coordinate
            y: Y coordinate
            color: Color for the marker (e.g., 'green', 'red')
        """
        from inkex import Circle

        # Create a small circle at the position
        marker = Circle()
        marker.set('cx', str(x))
        marker.set('cy', str(y))
        marker.set('r', '1.5')  # 1.5mm radius
        marker.style = {
            'fill': color,
            'fill-opacity': '0.7',
            'stroke': 'black',
            'stroke-width': '0.2'
        }
        layer.append(marker)


if __name__ == '__main__':
    PositioningTool().run()
