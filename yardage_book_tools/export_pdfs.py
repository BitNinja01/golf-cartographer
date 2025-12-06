#!/usr/bin/env python3
"""
PDF Exporter Tool - Stage 5 of Golf Yardage Book Extension Suite

This extension exports a complete yardage book as 20 individual PDF files with
different hole combinations for flexible printing. It toggles visibility for
different hole combinations on each page and calls the Inkscape CLI to generate
PDFs at 300 DPI.

Exports:
- 17 regular pages with hole pairs in reverse order (1-17, 2-16, etc.)
- 3 special pages (18-notes, back-cover, yardage_chart-18)

Author: Golf Yardage Book Extension Suite
License: MIT
"""

import inkex
import os
import sys
import subprocess
import tempfile


class ExportPDFs(inkex.EffectExtension):
    """
    Exports complete yardage book as 20 individual PDFs with different hole
    combinations for flexible printing.
    """

    def add_arguments(self, pars):
        """Add command-line arguments."""
        pars.add_argument("--output_dir", type=str, default="~/Desktop",
                         help="Output directory for PDF files")
        pars.add_argument("--filename_prefix", type=str, default="yardage_book_",
                         help="Filename prefix for PDF files")

    def effect(self):
        """
        Main execution method.

        Operations:
        1. Validate document structure (all required groups exist)
        2. Detect Inkscape CLI path for PDF generation
        3. For each PDF configuration:
           - Hide all holes in "top" and "bottom" groups
           - Hide all special groups (notes, cover, back, yardage_chart)
           - Show specified hole/group in "top"
           - Show specified hole/group in "bottom"
           - Export to PDF at 300 DPI
        4. Report summary of successful/failed exports
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

        try:
            # Export 17 regular pages (hole pairs in reverse order)
            # Each page pairs holes from opposite ends: 1+17, 2+16, 3+15, ..., 17+1
            # This creates a symmetric booklet layout
            for i in range(1, 18):
                top_hole = f"hole_{i:02d}"
                bottom_hole = f"hole_{18-i:02d}"
                filename = f"{self.options.filename_prefix}{i}_{18-i}.pdf"
                output_path = os.path.join(output_dir, filename)

                try:
                    self._configure_visibility(top_hole, bottom_hole)
                    self._export_to_pdf(inkscape_path, output_path)
                    successful_exports.append(filename)
                except Exception as e:
                    failed_exports.append((filename, str(e)))
                    inkex.errormsg(f"Failed to export {filename}: {e}")

            # Export special page: hole 18 (final hole) with notes section
            filename = f"{self.options.filename_prefix}18_notes.pdf"
            output_path = os.path.join(output_dir, filename)
            try:
                self._configure_visibility("hole_18", "notes", special_bottom=True)
                self._export_to_pdf(inkscape_path, output_path)
                successful_exports.append(filename)
            except Exception as e:
                failed_exports.append((filename, str(e)))
                inkex.errormsg(f"Failed to export {filename}: {e}")

            # Export special page: back cover with front cover
            filename = f"{self.options.filename_prefix}back_cover.pdf"
            output_path = os.path.join(output_dir, filename)
            try:
                self._configure_visibility("back", "cover", special_top=True, special_bottom=True)
                self._export_to_pdf(inkscape_path, output_path)
                successful_exports.append(filename)
            except Exception as e:
                failed_exports.append((filename, str(e)))
                inkex.errormsg(f"Failed to export {filename}: {e}")

            # Export special page: yardage chart with hole 18
            filename = f"{self.options.filename_prefix}yardage_chart_18.pdf"
            output_path = os.path.join(output_dir, filename)
            try:
                self._configure_visibility("yardage_chart", "hole_18", special_top=True)
                self._export_to_pdf(inkscape_path, output_path)
                successful_exports.append(filename)
            except Exception as e:
                failed_exports.append((filename, str(e)))
                inkex.errormsg(f"Failed to export {filename}: {e}")

        finally:
            # Restore original visibility states
            self._restore_visibility_states(original_states)

        # Report summary
        summary = f"PDF Export Complete:\n"
        summary += f"  Successful: {len(successful_exports)}/20 PDFs\n"
        if failed_exports:
            summary += f"  Failed: {len(failed_exports)}/20 PDFs\n"
            summary += "\nFailed exports:\n"
            for filename, error in failed_exports:
                summary += f"  - {filename}: {error}\n"
        summary += f"\nOutput directory: {output_dir}"

        inkex.errormsg(summary)

    def _validate_document_structure(self):
        """
        Validate that document contains all required groups.

        Returns:
            dict: Contains 'valid' (bool), 'error' (str), and group references
        """
        root = self.document.getroot()
        required_groups = {
            "top": None,
            "bottom": None,
            "notes": None,
            "cover": None,
            "back": None,
            "yardage_chart": None
        }

        # Find all required groups
        for element in root:
            if isinstance(element, inkex.Group):
                label = element.label
                if label in required_groups:
                    required_groups[label] = element

        # Check for missing groups
        missing_groups = [name for name, group in required_groups.items() if group is None]
        if missing_groups:
            error_msg = "Missing required groups:\n"
            for name in missing_groups:
                error_msg += f"  - {name}/\n"
            return {"valid": False, "error": error_msg}

        # Validate top and bottom groups have 18 hole_XX children
        for group_name in ["top", "bottom"]:
            group = required_groups[group_name]
            hole_count = 0
            for child in group:
                if isinstance(child, inkex.Group) and child.label and child.label.startswith("hole_"):
                    hole_count += 1

            if hole_count < 18:
                return {
                    "valid": False,
                    "error": f"Group '{group_name}/' should contain 18 hole_XX children (found {hole_count})"
                }

        # All validation passed
        result = {"valid": True, "error": None}
        result.update(required_groups)
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
        self._hide_all_holes(self.bottom_group)

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
            # Show special group directly
            if bottom_visible == "cover":
                self._show_element_direct(self.cover_group)
            elif bottom_visible == "notes":
                self._show_element_direct(self.notes_group)
        else:
            # Show hole in bottom group (hole_XX format)
            self._show_element_in_group(self.bottom_group, bottom_visible)

    def _hide_all_holes(self, group):
        """
        Hide all hole_XX children in a group.

        Args:
            group: Parent group element
        """
        for child in group:
            if isinstance(child, inkex.Group) and child.label and child.label.startswith("hole_"):
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


if __name__ == '__main__':
    ExportPDFs().run()
