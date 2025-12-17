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
        Test the simplest possible thing: can we measure EXISTING text elements?
        """
        from inkex import TextElement

        inkex.utils.debug("=== SIMPLE BBOX TEST ===")
        inkex.utils.debug("\nLet's test if we can measure EXISTING text in the document...")

        # Find all existing text elements in the document
        existing_texts = list(self.svg.findall('.//text', namespaces=inkex.NSS))

        inkex.utils.debug(f"\nFound {len(existing_texts)} existing text elements in document")

        if existing_texts:
            for i, text_elem in enumerate(existing_texts[:3]):  # Test first 3
                inkex.utils.debug(f"\n--- Text element {i+1} ---")
                inkex.utils.debug(f"  ID: {text_elem.get('id', 'no-id')}")
                inkex.utils.debug(f"  Text content: {text_elem.text or '(in tspan)'}")

                # Try to get bbox
                try:
                    bbox = text_elem.bounding_box()
                    if bbox:
                        inkex.utils.debug(f"  ✓ bounding_box() SUCCESS!")
                        inkex.utils.debug(f"    Width: {bbox.width:.4f} user units")
                        inkex.utils.debug(f"    Height: {bbox.height:.4f} user units")
                        inkex.utils.debug(f"    Left: {bbox.left:.4f}, Top: {bbox.top:.4f}")
                        inkex.utils.debug(f"    Right: {bbox.right:.4f}, Bottom: {bbox.bottom:.4f}")
                    else:
                        inkex.utils.debug(f"  ✗ bounding_box() returned None")
                except Exception as e:
                    inkex.utils.debug(f"  ✗ Exception: {e}")
        else:
            inkex.utils.debug("\n⚠ No existing text found. Let's test with DIFFERENT coordinates...")

            # Create TWO text elements at DIFFERENT positions
            # If bbox is returning actual dimensions, they should be SAME size
            # If bbox is returning coordinates, they'll be DIFFERENT
            from inkex import TextElement, Tspan

            current_layer = self.svg.get_current_layer()

            # Text #1: Position at (100, 100)
            text1 = TextElement()
            text1.set('x', '100')
            text1.set('y', '100')
            text1.style = {'font-size': '24pt', 'font-family': 'Arial'}
            tspan1 = Tspan()
            tspan1.text = 'Hello World'
            text1.append(tspan1)
            current_layer.append(text1)

            # Text #2: SAME content, DIFFERENT position (200, 300)
            text2 = TextElement()
            text2.set('x', '200')
            text2.set('y', '300')
            text2.style = {'font-size': '24pt', 'font-family': 'Arial'}
            tspan2 = Tspan()
            tspan2.text = 'Hello World'
            text2.append(tspan2)
            current_layer.append(text2)

            inkex.utils.debug("\nCreated TWO identical text elements at DIFFERENT positions:")
            inkex.utils.debug("  Text #1: 'Hello World' at (100, 100), 24pt Arial")
            inkex.utils.debug("  Text #2: 'Hello World' at (200, 300), 24pt Arial")
            inkex.utils.debug("\n⚠ CRITICAL TEST:")
            inkex.utils.debug("  If bbox returns REAL dimensions → both should be ~same size")
            inkex.utils.debug("  If bbox returns coordinates → they'll be different")

            # Measure both
            bbox1 = text1.bounding_box()
            bbox2 = text2.bounding_box()

            inkex.utils.debug("\n--- Text #1 Bounding Box ---")
            if bbox1:
                inkex.utils.debug(f"  Width: {bbox1.width:.4f}, Height: {bbox1.height:.4f}")
                inkex.utils.debug(f"  Left: {bbox1.left:.4f}, Top: {bbox1.top:.4f}")
            else:
                inkex.utils.debug(f"  Result: None")

            inkex.utils.debug("\n--- Text #2 Bounding Box ---")
            if bbox2:
                inkex.utils.debug(f"  Width: {bbox2.width:.4f}, Height: {bbox2.height:.4f}")
                inkex.utils.debug(f"  Left: {bbox2.left:.4f}, Top: {bbox2.top:.4f}")
            else:
                inkex.utils.debug(f"  Result: None")

            # Analysis
            if bbox1 and bbox2:
                inkex.utils.debug("\n=== VERDICT ===")
                if abs(bbox1.width - bbox2.width) < 1.0 and abs(bbox1.height - bbox2.height) < 1.0:
                    inkex.utils.debug("✓ SAME dimensions → bbox is returning ACTUAL TEXT SIZE!")
                    inkex.utils.debug("  This means we CAN measure text reliably!")
                else:
                    inkex.utils.debug("✗ DIFFERENT dimensions → bbox is returning POSITION, not size")
                    inkex.utils.debug("  Text #1: {:.1f}x{:.1f}".format(bbox1.width, bbox1.height))
                    inkex.utils.debug("  Text #2: {:.1f}x{:.1f}".format(bbox2.width, bbox2.height))
                    inkex.utils.debug("  This confirms text bbox measurements are NOT reliable")

            # NEW TEST: Try converting text to path element
            inkex.utils.debug("\n\n=== NEW APPROACH: TEXT TO PATH CONVERSION ===")
            inkex.utils.debug("Instead of measuring text, let's convert to a path and measure THAT...")

            # Create a fresh text element for path conversion
            from inkex import PathElement

            text_for_path = TextElement()
            text_for_path.set('x', '50')
            text_for_path.set('y', '50')
            text_for_path.style = {'font-size': '24pt', 'font-family': 'Arial'}
            tspan_path = Tspan()
            tspan_path.text = 'ABC'
            text_for_path.append(tspan_path)
            current_layer.append(text_for_path)

            inkex.utils.debug("\nCreated text: 'ABC' at (50, 50), 24pt Arial")

            # Try multiple path conversion approaches
            inkex.utils.debug("\n--- Approach 1: to_path_element() ---")
            try:
                path_elem = text_for_path.to_path_element()
                if path_elem is not None:
                    inkex.utils.debug(f"  Path created! Type: {type(path_elem)}")
                    inkex.utils.debug(f"  Path 'd' attribute length: {len(path_elem.get('d', ''))}")
                    inkex.utils.debug(f"  Path 'd' content: {path_elem.get('d', '(empty)')[:100]}...")

                    # Try to measure the path
                    path_bbox = path_elem.bounding_box()
                    if path_bbox:
                        inkex.utils.debug(f"  ✓ PATH BBOX SUCCESS!")
                        inkex.utils.debug(f"    Width: {path_bbox.width:.4f}")
                        inkex.utils.debug(f"    Height: {path_bbox.height:.4f}")
                    else:
                        inkex.utils.debug(f"  ✗ Path bbox returned None")
                else:
                    inkex.utils.debug(f"  ✗ to_path_element() returned None")
            except Exception as e:
                inkex.utils.debug(f"  ✗ Exception: {e}")

            inkex.utils.debug("\n--- Approach 2: Create PathElement manually ---")
            try:
                # Try to get path data using get_path()
                path_data = text_for_path.get_path()
                if path_data:
                    inkex.utils.debug(f"  get_path() returned: {type(path_data)}")
                    inkex.utils.debug(f"  Path data: {str(path_data)[:100]}...")

                    # Create a path element manually
                    manual_path = PathElement()
                    manual_path.set('d', str(path_data))
                    manual_path.style = text_for_path.style
                    current_layer.append(manual_path)

                    # Measure it
                    manual_bbox = manual_path.bounding_box()
                    if manual_bbox:
                        inkex.utils.debug(f"  ✓ MANUAL PATH BBOX SUCCESS!")
                        inkex.utils.debug(f"    Width: {manual_bbox.width:.4f}")
                        inkex.utils.debug(f"    Height: {manual_bbox.height:.4f}")
                    else:
                        inkex.utils.debug(f"  ✗ Manual path bbox returned None")
                else:
                    inkex.utils.debug(f"  ✗ get_path() returned None")
            except Exception as e:
                inkex.utils.debug(f"  ✗ Exception: {e}")

        inkex.utils.debug("\n\n=== FINAL CONCLUSION ===")
        inkex.utils.debug("Can we convert text to paths and measure those?")
        inkex.utils.debug("If YES → we have a reliable measurement system!")
        inkex.utils.debug("If NO → font-based calculations are the only option")

        return

        # Step 6: Calculate offset to align to bottom-right corner
        # We want bbox.right = canvas_width and bbox.bottom = canvas_height
        offset_x = canvas_width - path_bbox.right
        offset_y = canvas_height - path_bbox.bottom

        inkex.utils.debug(f"\nStep 5: Calculating position adjustment for bottom-right alignment")
        inkex.utils.debug(f"  Target: bbox.right = {canvas_width:.4f}, bbox.bottom = {canvas_height:.4f}")
        inkex.utils.debug(f"  Current: bbox.right = {path_bbox.right:.4f}, bbox.bottom = {path_bbox.bottom:.4f}")
        inkex.utils.debug(f"  Offset needed: dx = {offset_x:.4f}, dy = {offset_y:.4f}")

        # Step 7: Apply transform to move path
        from inkex import Transform
        transform = Transform(f"translate({offset_x}, {offset_y})")
        path.transform = transform @ path.transform

        inkex.utils.debug(f"\nStep 6: Applied transform to path")
        inkex.utils.debug(f"  Transform: translate({offset_x:.4f}, {offset_y:.4f})")

        # Step 8: Verify final position
        final_bbox = path.bounding_box()
        inkex.utils.debug(f"\nFinal Bounding Box (after repositioning):")
        inkex.utils.debug(f"  Left: {final_bbox.left:.4f} user units ({self.svg.uutounit(final_bbox.left, 'mm'):.4f} mm)")
        inkex.utils.debug(f"  Top: {final_bbox.top:.4f} user units ({self.svg.uutounit(final_bbox.top, 'mm'):.4f} mm)")
        inkex.utils.debug(f"  Right: {final_bbox.right:.4f} user units ({self.svg.uutounit(final_bbox.right, 'mm'):.4f} mm)")
        inkex.utils.debug(f"  Bottom: {final_bbox.bottom:.4f} user units ({self.svg.uutounit(final_bbox.bottom, 'mm'):.4f} mm)")
        inkex.utils.debug(f"  Width: {final_bbox.width:.4f} user units ({self.svg.uutounit(final_bbox.width, 'mm'):.4f} mm)")
        inkex.utils.debug(f"  Height: {final_bbox.height:.4f} user units ({self.svg.uutounit(final_bbox.height, 'mm'):.4f} mm)")

        inkex.utils.debug(f"\n✓ Text converted to paths and aligned to bottom-right corner")
        inkex.utils.debug(f"  Bbox.right should equal canvas width ({canvas_width:.4f})")
        inkex.utils.debug(f"  Bbox.bottom should equal canvas height ({canvas_height:.4f})")

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


if __name__ == '__main__':
    PositioningTool().run()
