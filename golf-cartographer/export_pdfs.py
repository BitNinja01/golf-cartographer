#!/usr/bin/env python3
"""
PDF Exporter Tool - Stage 5 of Golf Yardage Book Extension Suite

This extension exports a complete yardage book through a three-step process:

Step 1: Export 20 individual narrow PDFs (4.25" x 14" each)
- Each page shows a hole layout (top) with a green (bottom)
- Uses cross-pairing: hole layouts paired with different hole greens
- Includes special pages: yardage_chart, back, cover, notes

Step 2: Combine pairs side-by-side into 10 full-width pages (8.5" x 14" each)
- Using pypdf to merge PDFs horizontally (left + right)
- Sequential pairs: pages 1+2, 3+4, 5+6, etc.

Step 3: Combine into 5 booklet PDFs for saddle-stitch printing (2 pages each)
- yardage_book_01.pdf: wide pages 1+2 (innermost sheet)
- yardage_book_02.pdf: wide pages 3+4
- yardage_book_03.pdf: wide pages 5+6 (middle sheet)
- yardage_book_04.pdf: wide pages 7+8
- yardage_book_05.pdf: wide pages 9+10 (outermost sheet)

Print double-sided (flip on short edge), stack in order, fold in half, and
staple along center fold for a complete yardage book.

Author: Golf Yardage Book Extension Suite
License: MIT
"""

import inkex
import os
import sys
import subprocess
import tempfile

# Add python_libraries to path (for bundled pypdf)
lib_path = os.path.join(os.path.dirname(__file__), 'python_libraries')
sys.path.insert(0, lib_path)

from pypdf import PdfWriter, PdfReader


class ExportPDFs(inkex.EffectExtension):
    """
    Exports complete yardage book as individual PDF pages and combines them
    into booklet format for saddle-stitch printing.
    """

    def add_arguments(self, pars):
        """Add command-line arguments."""
        pars.add_argument("--output_dir", type=str, default="~/Desktop",
                         help="Output directory for PDF files")
        pars.add_argument("--filename_prefix", type=str, default="yardage_book_",
                         help="Filename prefix for PDF files")
        pars.add_argument("--combine_booklets", type=inkex.Boolean, default=True,
                         help="Combine individual PDFs into printable booklet format")

    def effect(self):
        """
        Main execution method.

        Operations:
        1. Validate document structure (all required groups exist)
        2. Detect Inkscape CLI path for PDF generation
        3. Export 20 individual narrow PDFs (4.25" x 14" each):
           - Configure visibility for each top/bottom pairing
           - Export to temporary PDF at 300 DPI
        4. If combine_booklets is enabled:
           - Combine pairs side-by-side into 10 full-width pages (8.5" x 14")
           - Combine 10 wide pages into 5 booklet PDFs (2 pages each)
           - Clean up all temporary files
        5. Report summary of successful/failed exports with print instructions
        """
        root = self.document.getroot()

        # Validate document structure
        validation_result = self._validate_document_structure()
        if not validation_result["valid"]:
            inkex.errormsg(f"Document structure validation failed:\n{validation_result['error']}")
            return

        # Store references to required groups
        self.top_group = validation_result["top"]
        self.bottom_group = validation_result["bottom"]
        self.notes_group = validation_result["notes"]
        self.cover_group = validation_result["cover"]
        self.back_group = validation_result["back"]
        self.yardage_chart_group = validation_result["yardage_chart"]
        self.greens_guide_group = validation_result["greens_guide"]

        # Detect Inkscape CLI path
        inkscape_path = self._find_inkscape_cli()
        if not inkscape_path:
            inkex.errormsg("Inkscape CLI not found. Please ensure Inkscape is installed and in your PATH.")
            return

        # Expand output directory path (handle ~)
        output_dir = os.path.expanduser(self.options.output_dir)
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                inkex.errormsg(f"Failed to create output directory: {e}")
                return

        # Track successful and failed exports
        successful_exports = []
        failed_exports = []

        # Store original visibility states for restoration
        original_states = self._save_visibility_states()

        # Step 1: Define all 20 individual narrow page exports (4.25" x 14" each)
        # Format: (top_element, bottom_element, special_top, special_bottom)
        # Using top-bottom notation: "9-9" means hole 9 layout with green 9
        individual_page_configs = [
            # Pages 1-10
            ("hole_09", "hole_09", False, False),           # 1. 9-9
            ("hole_08", "hole_10", False, False),           # 2. 8-10
            ("hole_07", "hole_11", False, False),           # 3. 7-11
            ("hole_06", "hole_12", False, False),           # 4. 6-12
            ("hole_05", "hole_13", False, False),           # 5. 5-13
            ("hole_04", "hole_14", False, False),           # 6. 4-14
            ("hole_03", "hole_15", False, False),           # 7. 3-15
            ("hole_02", "hole_16", False, False),           # 8. 2-16
            ("hole_01", "hole_17", False, False),           # 9. 1-17
            ("yardage_chart", "hole_18", True, False),      # 10. yardage_chart-18
            # Pages 11-20
            ("hole_10", "hole_08", False, False),           # 11. 10-8
            ("hole_11", "hole_07", False, False),           # 12. 11-7
            ("hole_12", "hole_06", False, False),           # 13. 12-6
            ("hole_13", "hole_05", False, False),           # 14. 13-5
            ("hole_14", "hole_04", False, False),           # 15. 14-4
            ("hole_15", "hole_03", False, False),           # 16. 15-3
            ("hole_16", "hole_02", False, False),           # 17. 16-2
            ("hole_17", "hole_01", False, False),           # 18. 17-1
            ("hole_18", "notes", False, True),              # 19. 18-notes
            ("back", "cover", True, True),                  # 20. back-cover
        ]

        # Step 2: Define how to combine into 10 full-width pages (side-by-side pairs)
        # Combine sequential pairs: 1+2, 3+4, 5+6, etc.
        page_combinations = [
            (0, 1),    # Wide Page 1: narrow pages 1+2
            (2, 3),    # Wide Page 2: narrow pages 3+4
            (4, 5),    # Wide Page 3: narrow pages 5+6
            (6, 7),    # Wide Page 4: narrow pages 7+8
            (8, 9),    # Wide Page 5: narrow pages 9+10
            (10, 11),  # Wide Page 6: narrow pages 11+12
            (12, 13),  # Wide Page 7: narrow pages 13+14
            (14, 15),  # Wide Page 8: narrow pages 15+16
            (16, 17),  # Wide Page 9: narrow pages 17+18
            (18, 19),  # Wide Page 10: narrow pages 19+20
        ]

        try:
            # Step 1: Export 20 individual narrow PDFs (4.25" x 14" each)
            individual_pdf_paths = []
            for idx, (top, bottom, special_top, special_bottom) in enumerate(individual_page_configs, 1):
                filename = self._generate_narrow_filename(top, bottom, special_top, special_bottom)
                output_path = os.path.join(output_dir, filename)
                individual_pdf_paths.append(output_path)

                try:
                    self._configure_visibility(top, bottom, special_top, special_bottom)
                    self._export_to_pdf(inkscape_path, output_path)
                    successful_exports.append(filename)
                except Exception as e:
                    failed_exports.append((filename, str(e)))
                    inkex.errormsg(f"Failed to export {filename}: {e}")

            # Step 2: Combine pairs side-by-side into 10 full-width pages (8.5" x 14" each)
            combined_page_paths = []
            if self.options.combine_booklets and len(individual_pdf_paths) == 20:
                for idx, (left_idx, right_idx) in enumerate(page_combinations, 1):
                    left_path = individual_pdf_paths[left_idx]
                    right_path = individual_pdf_paths[right_idx]

                    if os.path.exists(left_path) and os.path.exists(right_path):
                        left_config = individual_page_configs[left_idx]
                        right_config = individual_page_configs[right_idx]
                        combined_filename = self._generate_wide_filename(left_config, right_config)
                        combined_path = os.path.join(output_dir, combined_filename)

                        try:
                            self._combine_side_by_side(left_path, right_path, combined_path)
                            combined_page_paths.append(combined_path)
                        except Exception as e:
                            inkex.errormsg(f"Failed to combine {combined_filename}: {e}")

                # Clean up individual narrow PDFs after combining
                for pdf_path in individual_pdf_paths:
                    try:
                        if os.path.exists(pdf_path):
                            os.unlink(pdf_path)
                    except:
                        pass

            # Step 3: Combine pages into booklet PDFs
            booklet_files = []
            if self.options.combine_booklets and len(combined_page_paths) == 10:
                booklet_files = self._combine_into_booklets(combined_page_paths, output_dir)

                # Clean up temporary combined page files
                for temp_path in combined_page_paths:
                    try:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                    except:
                        pass  # Silently ignore cleanup errors

        finally:
            # Restore original visibility states
            self._restore_visibility_states(original_states)

        # Report summary
        summary = f"PDF Export Complete:\n"
        if self.options.combine_booklets and booklet_files:
            summary += f"  Exported {len(successful_exports)} individual pages (4.25\" x 14\")\n"
            summary += f"  Combined into {len(combined_page_paths)} full pages (8.5\" x 14\")\n"
            summary += f"  Created {len(booklet_files)} booklet PDFs for saddle-stitch printing:\n"
            for booklet_file in booklet_files:
                summary += f"    - {booklet_file}\n"
            summary += f"\n  Print Instructions:\n"
            summary += f"    1. Print each PDF double-sided (flip on short edge)\n"
            summary += f"    2. Stack in order (05 on outside, 01 in center)\n"
            summary += f"    3. Fold the stack in half\n"
            summary += f"    4. Staple along center fold\n"
        else:
            summary += f"  Successful: {len(successful_exports)}/20 individual pages\n"
        if failed_exports:
            summary += f"\n  Failed: {len(failed_exports)}/20 pages\n"
            summary += "\nFailed exports:\n"
            for filename, error in failed_exports:
                summary += f"  - {filename}: {error}\n"
        summary += f"\nOutput directory: {output_dir}"

        inkex.errormsg(summary)

    def _format_element_name(self, element_name, is_special):
        """
        Format element name for use in filenames.

        Args:
            element_name: Element label (e.g., "hole_09", "yardage_chart", "back")
            is_special: True if element is a special page (not a hole)

        Returns:
            str: Formatted name (e.g., "9", "yardage_chart", "back")
        """
        if is_special:
            return element_name
        # Extract number from hole_XX format
        if element_name.startswith("hole_"):
            return element_name.replace("hole_", "").lstrip("0") or "0"
        return element_name

    def _generate_narrow_filename(self, top, bottom, special_top, special_bottom):
        """
        Generate descriptive filename for narrow PDF based on content.

        Args:
            top: Top element name
            bottom: Bottom element name
            special_top: True if top is a special page
            special_bottom: True if bottom is a special page

        Returns:
            str: Descriptive filename (e.g., "temp_narrow_9-9.pdf", "temp_narrow_back-cover.pdf")
        """
        top_name = self._format_element_name(top, special_top)
        bottom_name = self._format_element_name(bottom, special_bottom)
        return f"temp_narrow_{top_name}-{bottom_name}.pdf"

    def _generate_wide_filename(self, left_config, right_config):
        """
        Generate descriptive filename for wide PDF based on the tops of both narrow pages.

        Args:
            left_config: Tuple (top, bottom, special_top, special_bottom) for left narrow page
            right_config: Tuple (top, bottom, special_top, special_bottom) for right narrow page

        Returns:
            str: Descriptive filename (e.g., "temp_wide_9-8.pdf", "temp_wide_18-back.pdf")
        """
        left_top = self._format_element_name(left_config[0], left_config[2])
        right_top = self._format_element_name(right_config[0], right_config[2])
        return f"temp_wide_{left_top}-{right_top}.pdf"

    def _validate_document_structure(self):
        """
        Validate that document contains all required groups.

        Returns:
            dict: Contains 'valid' (bool), 'error' (str), and group references
        """
        root = self.document.getroot()

        # First find top and bottom groups at root level
        root_groups = {
            "top": None,
            "bottom": None
        }

        for element in root:
            if isinstance(element, inkex.Group):
                label = element.label
                if label in root_groups:
                    root_groups[label] = element

        # Check for missing root groups
        missing_root = [name for name, group in root_groups.items() if group is None]
        if missing_root:
            error_msg = "Missing required root groups:\n"
            for name in missing_root:
                error_msg += f"  - {name}/\n"
            return {"valid": False, "error": error_msg}

        # Now search for special groups inside top and bottom
        special_groups = {
            "notes": None,
            "cover": None,
            "back": None,
            "yardage_chart": None
        }

        # Also find greens_guide (optional, in bottom group)
        greens_guide = None

        # Search in both top and bottom groups
        for parent_group in [root_groups["top"], root_groups["bottom"]]:
            for child in parent_group:
                if isinstance(child, inkex.Group):
                    label = child.label
                    if label in special_groups and special_groups[label] is None:
                        special_groups[label] = child
                    elif label == "greens_guide":
                        greens_guide = child

        # Check for missing special groups
        missing_special = [name for name, group in special_groups.items() if group is None]
        if missing_special:
            error_msg = "Missing required groups (should be inside top/ or bottom/):\n"
            for name in missing_special:
                error_msg += f"  - {name}/\n"
            return {"valid": False, "error": error_msg}

        # Validate top group has 18 hole_XX children
        top_group = root_groups["top"]
        hole_count = 0
        for child in top_group:
            if isinstance(child, inkex.Group) and child.label and child.label.startswith("hole_"):
                hole_count += 1

        if hole_count < 18:
            return {
                "valid": False,
                "error": f"Group 'top/' should contain 18 hole_XX children (found {hole_count})"
            }

        # Validate bottom group has 18 green_XX_bottom children
        bottom_group = root_groups["bottom"]
        green_count = 0
        for child in bottom_group:
            if child.label and child.label.startswith("green_") and child.label.endswith("_bottom"):
                green_count += 1

        if green_count < 18:
            return {
                "valid": False,
                "error": f"Group 'bottom/' should contain 18 green_XX_bottom children (found {green_count})"
            }

        # All validation passed
        result = {"valid": True, "error": None}
        result.update(root_groups)
        result.update(special_groups)
        result["greens_guide"] = greens_guide
        return result

    def _find_inkscape_cli(self):
        """
        Detect Inkscape CLI path across different platforms.

        Searches common installation paths for each OS and falls back to
        checking the system PATH if standard locations are not found.

        Returns:
            str: Path to Inkscape CLI binary or None if not found
        """
        paths = []

        # Define platform-specific search paths for Inkscape installation
        if sys.platform == 'linux':
            paths = [
                '/usr/bin/inkscape',           # Standard Debian/Ubuntu/Fedora
                '/usr/local/bin/inkscape',     # Custom compiled installation
                '/snap/bin/inkscape'           # Snap package installation
            ]
        elif sys.platform == 'darwin':
            # macOS: two possible locations in application bundle
            paths = [
                '/Applications/Inkscape.app/Contents/MacOS/inkscape',
                '/Applications/Inkscape.app/Contents/Resources/bin/inkscape'
            ]
        elif sys.platform == 'win32':
            # Windows: check both Program Files and Program Files (x86)
            paths = [
                'C:\\Program Files\\Inkscape\\bin\\inkscape.exe',
                'C:\\Program Files (x86)\\Inkscape\\bin\\inkscape.exe'
            ]

        # Check each standard path
        for path in paths:
            if os.path.exists(path):
                return path

        # Fallback: check system PATH by running 'inkscape --version'
        # This covers cases where Inkscape is in user's PATH or environment
        try:
            result = subprocess.run(['inkscape', '--version'],
                                   capture_output=True,
                                   timeout=5)
            if result.returncode == 0:
                return 'inkscape'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def _save_visibility_states(self):
        """
        Save current visibility states of all groups and their children.

        Returns:
            dict: Mapping of element IDs to their visibility states
        """
        states = {}

        groups_to_check = [
            self.top_group,
            self.bottom_group,
            self.notes_group,
            self.cover_group,
            self.back_group,
            self.yardage_chart_group
        ]

        for group in groups_to_check:
            # Save group state
            element_id = group.get('id')
            if element_id:
                states[element_id] = self._get_visibility_state(group)

            # Save children states
            for child in group:
                child_id = child.get('id')
                if child_id:
                    states[child_id] = self._get_visibility_state(child)

        return states

    def _get_visibility_state(self, element):
        """
        Get visibility state of an element.

        Args:
            element: SVG element

        Returns:
            dict: Contains 'display' and 'visibility' style properties
        """
        style = element.style if element.style else inkex.Style()
        return {
            'display': style.get('display', 'inline'),
            'visibility': style.get('visibility', 'visible')
        }

    def _restore_visibility_states(self, states):
        """
        Restore visibility states of elements.

        Args:
            states: dict mapping element IDs to visibility states
        """
        root = self.document.getroot()

        for element_id, state in states.items():
            element = self.svg.getElementById(element_id)
            if element is not None:
                if element.style is None:
                    element.style = inkex.Style()
                element.style['display'] = state['display']
                element.style['visibility'] = state['visibility']

    def _configure_visibility(self, top_visible, bottom_visible,
                            special_top=False, special_bottom=False):
        """
        Configure visibility for top and bottom groups plus special groups.

        Hides everything first, then shows only the specified elements.
        This ensures each PDF page contains exactly one top and one bottom element.

        Args:
            top_visible: Label of element to show in top group (or special group name)
            bottom_visible: Label of element to show in bottom group (or special group name)
            special_top: If True, top_visible refers to a special group (not a hole)
            special_bottom: If True, bottom_visible refers to a special group (not a hole)
        """
        # First pass: hide everything to ensure clean slate
        # This prevents accidentally showing multiple holes in the same PDF
        self._hide_all_holes(self.top_group)
        self._hide_all_greens(self.bottom_group)

        # Hide all special page groups
        self._hide_element(self.notes_group)
        self._hide_element(self.cover_group)
        self._hide_element(self.back_group)
        self._hide_element(self.yardage_chart_group)

        # Second pass: show only the specified top element
        # If special_top is True, top_visible is a special group name (e.g., "back", "yardage_chart")
        # Otherwise, top_visible is a hole label (e.g., "hole_01", "hole_18")
        if special_top:
            # Show special group directly
            if top_visible == "back":
                self._show_element_direct(self.back_group)
            elif top_visible == "yardage_chart":
                self._show_element_direct(self.yardage_chart_group)
        else:
            # Show hole in top group (hole_XX format)
            self._show_element_in_group(self.top_group, top_visible)

        # Third pass: show only the specified bottom element
        if special_bottom:
            # Show special group directly and hide greens_guide
            if bottom_visible == "cover":
                self._show_element_direct(self.cover_group)
                if self.greens_guide_group is not None:
                    self._hide_element(self.greens_guide_group)
            elif bottom_visible == "notes":
                self._show_element_direct(self.notes_group)
                if self.greens_guide_group is not None:
                    self._hide_element(self.greens_guide_group)
        else:
            # Convert hole_XX to green_XX_bottom format for bottom group
            # e.g., "hole_01" -> "green_01_bottom"
            if bottom_visible.startswith("hole_"):
                hole_num = bottom_visible.replace("hole_", "")
                green_label = f"green_{hole_num}_bottom"
            else:
                green_label = bottom_visible
            self._show_element_in_group(self.bottom_group, green_label)
            # Ensure greens_guide is visible for regular pages and yardage_chart
            if self.greens_guide_group is not None:
                self._show_element_direct(self.greens_guide_group)

    def _hide_all_holes(self, group):
        """
        Hide all hole_XX children in a group.

        Args:
            group: Parent group element
        """
        for child in group:
            if isinstance(child, inkex.Group) and child.label and child.label.startswith("hole_"):
                self._hide_element(child)

    def _hide_all_greens(self, group):
        """
        Hide all green_XX_bottom children in a group.

        Args:
            group: Parent group element
        """
        for child in group:
            if child.label and child.label.startswith("green_") and child.label.endswith("_bottom"):
                self._hide_element(child)

    def _hide_element(self, element):
        """
        Hide an element by setting display:none.

        Args:
            element: SVG element to hide
        """
        if element.style is None:
            element.style = inkex.Style()
        element.style['display'] = 'none'

    def _show_element_direct(self, element):
        """
        Show an element directly by setting display:inline and visibility:visible.

        Args:
            element: SVG element to show
        """
        if element.style is None:
            element.style = inkex.Style()
        element.style['display'] = 'inline'
        element.style['visibility'] = 'visible'

    def _show_element_in_group(self, group, label):
        """
        Find and show a specific element by label within a group.

        Args:
            group: Parent group to search in
            label: Label of element to show
        """
        for child in group:
            if child.label == label:
                self._show_element_direct(child)
                return

        # If not found, log warning but continue
        inkex.errormsg(f"Warning: Element with label '{label}' not found in group '{group.label}'")

    def _export_to_pdf(self, inkscape_path, output_path):
        """
        Export document to PDF using Inkscape CLI.

        Creates a temporary SVG file with the current document state
        (including all visibility changes), passes it to Inkscape CLI for
        PDF export, then cleans up the temp file.

        Args:
            inkscape_path: Path to Inkscape CLI binary
            output_path: Output PDF file path

        Raises:
            Exception: If Inkscape export fails
        """
        # Create temporary SVG file with current visibility state
        # This preserves all visibility changes made by _configure_visibility()
        temp_svg_fd, temp_svg_path = tempfile.mkstemp(suffix='.svg', prefix='yardage_book_')
        try:
            # Write current document state to temp SVG file
            # The document includes all the visibility manipulations for this specific PDF
            os.close(temp_svg_fd)  # Close file descriptor before writing to file
            with open(temp_svg_path, 'wb') as f:
                self.document.write(f)

            # Call Inkscape CLI to export PDF from the temp SVG
            # Using high DPI (300) for print-quality output
            result = subprocess.run([
                inkscape_path,
                temp_svg_path,
                '--export-type=pdf',
                f'--export-filename={output_path}',
                '--export-dpi=300'           # Print quality resolution
            ], capture_output=True, text=True, timeout=30)

            # Check if export succeeded
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                raise Exception(f"Inkscape export failed: {error_msg}")

        finally:
            # Clean up temporary SVG file
            # Use try-except to ensure cleanup happens even if it fails
            try:
                if os.path.exists(temp_svg_path):
                    os.unlink(temp_svg_path)
            except:
                pass  # Silently ignore cleanup errors (temp file will be deleted by OS eventually)

    def _combine_side_by_side(self, left_pdf_path, right_pdf_path, output_path):
        """
        Combine two 4.25" x 14" PDFs side-by-side into one 8.5" x 14" PDF.

        Uses pypdf to create a new page with double width and positions both
        PDFs horizontally adjacent to each other.

        Args:
            left_pdf_path: Path to left PDF (4.25" x 14")
            right_pdf_path: Path to right PDF (4.25" x 14")
            output_path: Path for combined output PDF (8.5" x 14")
        """
        from pypdf import Transformation, PageObject

        # Read both PDFs
        left_reader = PdfReader(left_pdf_path)
        right_reader = PdfReader(right_pdf_path)

        # Get the first page from each
        left_page = left_reader.pages[0]
        right_page = right_reader.pages[0]

        # Get original dimensions (should be ~306 x 1008 points for 4.25" x 14")
        original_width = float(left_page.mediabox.width)
        original_height = float(left_page.mediabox.height)

        # Create a new blank page with double width (8.5" x 14" = 612 x 1008 points)
        combined_page = PageObject.create_blank_page(width=original_width * 2, height=original_height)

        # Merge left page at original position (no transformation needed)
        combined_page.merge_page(left_page)

        # Merge right page with translation to position it on the right side
        combined_page.merge_transformed_page(
            right_page,
            Transformation().translate(tx=original_width, ty=0)
        )

        # Write the combined page to output
        writer = PdfWriter()
        writer.add_page(combined_page)

        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

    def _combine_into_booklets(self, page_paths, output_dir):
        """
        Combine individual PDF pages into booklet format for saddle-stitch printing.

        Creates 5 booklet PDFs, each with 2 pages, ordered for proper reading sequence
        when printed double-sided, stacked, folded, and stapled.

        Booklet structure:
        - yardage_book_01.pdf: 9-8 / 10-11
        - yardage_book_02.pdf: 7-6 / 12-13
        - yardage_book_03.pdf: 5-4 / 14-15
        - yardage_book_04.pdf: 3-2 / 16-17
        - yardage_book_05.pdf: 1-yardage_chart / 18-back

        Args:
            page_paths: List of 10 individual PDF page file paths
            output_dir: Directory for output booklet PDFs

        Returns:
            list: Filenames of created booklet PDFs
        """
        booklet_files = []

        # Define booklet combinations (pairs of page indices)
        # Each booklet gets 2 pages that form a double-sided sheet
        # Pairing front nine with back nine for proper reading sequence
        booklet_configs = [
            (1, "yardage_book_01.pdf", [0, 5]),  # 9-8 / 10-11
            (2, "yardage_book_02.pdf", [1, 6]),  # 7-6 / 12-13
            (3, "yardage_book_03.pdf", [2, 7]),  # 5-4 / 14-15
            (4, "yardage_book_04.pdf", [3, 8]),  # 3-2 / 16-17
            (5, "yardage_book_05.pdf", [4, 9]),  # 1-yardage_chart / 18-back
        ]

        for booklet_num, filename, page_indices in booklet_configs:
            try:
                output_path = os.path.join(output_dir, filename)
                writer = PdfWriter()

                # Add each page to the booklet
                for page_idx in page_indices:
                    if page_idx < len(page_paths) and os.path.exists(page_paths[page_idx]):
                        reader = PdfReader(page_paths[page_idx])
                        if len(reader.pages) > 0:
                            writer.add_page(reader.pages[0])

                # Write the combined booklet PDF
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)

                booklet_files.append(filename)

            except Exception as e:
                inkex.errormsg(f"Failed to create booklet {filename}: {e}")

        return booklet_files


if __name__ == '__main__':
    ExportPDFs().run()
