# Golf Cartographer

**An Inkscape extension suite that automates golf yardage book creation from OpenStreetMap data**

Transform raw OSM exports into professional, print-ready golf yardage books through an intelligent five-stage pipeline that handles flattening, grouping, positioning, labeling, and PDF export.

---

## Overview

Golf Cartographer eliminates the tedious manual work of creating golf course yardage books. Instead of spending hours organizing SVG layers, positioning holes, and exporting individual PDFs, this extension suite automates the entire workflow from raw OpenStreetMap data to a complete 20-page yardage book ready for printing.

### What It Does

- **Flattens** complex nested SVG hierarchies from OSM exports
- **Groups** golf course elements by hole using intelligent color detection
- **Positions and scales** all 18 holes with automatic rotation, placing holes and greens appropriately
- **Labels** holes with numbers, par, and tee box yardages
- **Exports** 20 PDFs with strategic hole combinations for printing

### Key Features

- 🎯 **Intelligent Color Detection** - Automatically categorizes greens, fairways, bunkers, water, and paths
- 🔄 **Automatic Rotation** - Orients holes toward the green for optimal viewing
- 📐 **Smart Positioning** - Fits holes within defined bounding boxes with appropriate margins
- 📄 **Batch PDF Export** - Generates all 20 yardage book pages in one click
- 🛠️ **Modular Pipeline** - Each stage produces reusable intermediate output
- 🔧 **Extensible Architecture** - Shared utilities enable easy customization

---

## Requirements

- **Inkscape 1.4.2 or later** (REQUIRED - earlier versions have incompatible APIs)
- **Python 3.7+** (included with modern Inkscape installations)
- **OpenStreetMap SVG export** of your golf course

---

## Installation

1. **Locate your Inkscape extensions directory**:
   - **Linux**: `~/.config/inkscape/extensions/`
   - **macOS**: `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
   - **Windows**: `%APPDATA%\inkscape\extensions\`

2. **Copy the extension files**:
   ```bash
   cp golf-cartographer/* ~/.config/inkscape/extensions/
   ```

3. **Restart Inkscape** to load the extensions

4. **Verify installation**:
   - Open Inkscape
   - Navigate to `Extensions > Golf Cartographer`
   - You should see 5 tools numbered 1-5

---

## Quick Start

### Basic Workflow

1. **Export your golf course** from OpenStreetMap as SVG
2. **Open the SVG** in Inkscape
3. **Run each tool in sequence**:
   - `Extensions > Golf Cartographer > 1. Flatten SVG`
   - `Extensions > Golf Cartographer > 2. Group Hole` (run 18 times, once per hole)
   - `Extensions > Golf Cartographer > 3. Auto-Place Holes and Scale Greens`
   - `Extensions > Golf Cartographer > 4. Add Hole Label` (run 18 times, once per hole)
   - `Extensions > Golf Cartographer > 5. Export PDFs`

4. **Find your PDFs** in `examples/exported_pdfs/` (or your configured output directory)

### Expected Processing Time

- **Stage 1** (Flatten SVG): ~5-15 seconds
- **Stage 2** (Group Hole): ~3-8 seconds per hole × 18 holes
- **Stage 3** (Auto-Place Holes and Scale Greens): ~30-60 seconds
- **Stage 4** (Add Hole Label): ~3-5 seconds per hole × 18 holes
- **Stage 5** (Export PDFs): ~2-5 minutes for all 20 PDFs

---

## Five-Stage Pipeline

### Stage 1: Flatten SVG

**Tool**: `1. Flatten SVG`
**Input**: Raw OpenStreetMap SVG export
**Output**: Flattened hierarchy with organized element groups

**What it does**:
- Collapses all nested SVG groups to top level
- Categorizes elements by color into greens, fairways, bunkers, water, trees, paths
- Removes elements outside canvas bounds
- Creates structured groups for downstream processing

**Example**: `examples/course_stage_1.svg`

---

### Stage 2: Group Hole

**Tool**: `2. Group Hole` (run 18 times)
**Input**: Flattened SVG from Stage 1
**Output**: 18 hierarchical hole groups

**What it does**:
- Prompts user to select elements for one hole
- Groups selected elements into `hole_N` structure
- Preserves terrain (fairways, bunkers) and green elements separately
- Calculates hole centroid for downstream rotation

**How to use**:
1. Select all elements belonging to hole 1
2. Run `Extensions > Golf Cartographer > 2. Group Hole`
3. Repeat for holes 2-18

**Example**: `examples/course_stage_2.svg`

---

### Stage 3: Auto-Place Holes and Scale Greens

**Tool**: `3. Auto-Place Holes and Scale Greens`
**Input**: Grouped holes from Stage 2 + yardage book template
**Output**: Positioned holes in "top" area, scaled greens in "bottom" area

**What it does**:
- **Hole Placement**:
  - Finds all `hole_N` groups (1-18)
  - Rotates each hole to face the green
  - Positions holes in 3.736" × 6.756" bounding box
  - Applies 10% edge buffer for spacing
- **Green Scaling**:
  - Extracts green elements from each hole
  - Scales greens to fit 3.75" × 3.75" box
  - Applies 20% edge buffer for detail visibility
  - Positions scaled greens in "bottom" yardage book area

**Configuration** (in `auto_place_holes.py`):
```python
# Top area for hole layouts
BOUNDING_BOX = {
    'x': 0.257,
    'y': 0.247,
    'width': 3.736,
    'height': 6.756
}
EDGE_BUFFER = 0.90  # 90% of box (10% margin)

# Bottom area for scaled greens
TARGET_BOX = {
    'x': 0.250,
    'y': 7.000,
    'width': 3.750,
    'height': 3.750
}
GREEN_EDGE_BUFFER = 0.80  # 80% of box (20% margin)
```

**Example**: `examples/course_stage_3.svg`

---

### Stage 4: Add Hole Label

**Tool**: `4. Add Hole Label` (run 18 times)
**Input**: Positioned holes from Stage 3
**Output**: Holes with labels containing number, par, and tee yardages

**What it does**:
- Adds a circle with hole number
- Displays par information
- Shows yardages for up to 6 tee boxes
- Uses custom glyph libraries for consistent typography

**How to use**:
1. Run `Extensions > Golf Cartographer > 4. Add Hole Label`
2. Enter hole number, par, and tee box information
3. Repeat for holes 1-18

**Example**: `examples/course_stage_4.svg`

---

### Stage 5: Export PDFs

**Tool**: `5. Export PDFs`
**Input**: Complete yardage book from Stage 4
**Output**: 20 PDF files with strategic hole combinations

**What it does**:
- Exports 18 individual hole pages (holes 1-17 with opposite-side hole)
- Exports special pages:
  - `yardage_book_18_notes.pdf` - Hole 18/notes
  - `yardage_book_back_cover.pdf` - Back/Cover
  - `yardage_book_chart_18.pdf` - Yardage chart/hole 18

**Example output**: `examples/exported_pdfs/` (20 PDF files)

**Example**: `examples/course_stage_5.svg`

---

### PDF Export Combinations

The export tool generates these strategic page layouts:

- **Holes 1-17**: Each paired with opposite-side hole (e.g., `1_17.pdf`, `2_16.pdf`)
- **Hole 18**: Paired with notes section (`18_notes.pdf`)
- **Turn Page**: Hole 9 shown twice for mid-round reference (`9_9.pdf`)
- **Back Cover**: Course overview (`back_cover.pdf`)
- **Scorecard**: 18-hole chart (`chart_18.pdf`)

---

## Configuration

All measurements use **inches** as document units. Verify your Inkscape document settings before running the pipeline.

### Customizable Parameters

Edit these constants in `auto_place_holes.py` to adjust positioning:

```python
# Stage 3: Hole placement area (top of page)
BOUNDING_BOX = {
    'x': 0.257,      # Left margin (inches)
    'y': 0.247,      # Top margin (inches)
    'width': 3.736,  # Available width (inches)
    'height': 6.756  # Available height (inches)
}
EDGE_BUFFER = 0.90  # Use 90% of box (10% margin)

# Stage 3: Green detail area (bottom of page)
TARGET_BOX = {
    'x': 0.250,      # Left margin (inches)
    'y': 7.000,      # Top of green area (inches)
    'width': 3.750,  # Green area width (inches)
    'height': 3.750  # Green area height (inches)
}
GREEN_EDGE_BUFFER = 0.80  # Use 80% of box (20% margin)
```

### Color Calibration

OSM exports may use varying color palettes. If color detection fails, adjust fuzzy matching thresholds in `color_utils.py`.

---

## Troubleshooting

### Extensions don't appear in Inkscape menu

- ✅ Verify both `.py` and `.inx` files are in extensions directory
- ✅ Check file permissions (should be readable)
- ✅ Restart Inkscape completely
- ✅ Check Inkscape version (requires 1.4.2+)

### ImportError when running extensions

- ✅ Ensure all utility files (`transform_utils.py`, `geometry_utils.py`, `color_utils.py`) are present
- ✅ Verify Python 3.7+ is available
- ✅ Check that files use absolute imports (not relative imports with dots)

### Elements not categorized correctly

- ✅ Check element colors match expected OSM palette
- ✅ Adjust color matching thresholds in `color_utils.py`
- ✅ Verify elements have fill or stroke colors
- ✅ Try manually setting element colors before running Stage 1

### Holes positioned incorrectly

- ✅ Verify document units are set to inches
- ✅ Check that holes are properly grouped in Stage 2
- ✅ Ensure hole groups contain both terrain and green elements
- ✅ Adjust `BOUNDING_BOX` coordinates if using custom template

### PDFs fail to export

- ✅ Ensure all holes are named `hole_1` through `hole_18`
- ✅ Check that output directory exists and is writable
- ✅ Verify no holes are locked or hidden in Inkscape
- ✅ Try exporting individual holes first to isolate issues

---

## Development

### Requirements for Development

- Python 3.7+ with type hint support
- Inkscape 1.4.2+ for testing
- Understanding of SVG transforms and coordinate systems
- Familiarity with Inkscape extension API (`inkex` library)

---

## Contributing

Contributions are welcome! Here's how to get started:

1. **Read the documentation**:
   - [FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md) for planned features

2. **Check existing issues** before starting work

3. **Follow code quality standards**:
   - Add type hints
   - Include comprehensive docstrings
   - Use specific exception types
   - Test manually in Inkscape

4. **Submit pull requests** with:
   - Clear description of changes
   - Example SVG demonstrating the feature/fix

### Ideas for Contributions

See [FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md) for the complete list of 22+ enhancement ideas!

**High Priority (Workflow Improvements)**:
- Batch Hole Grouping - Run Stage 2 once instead of 18 times
- Auto-Detect Holes from Greens - Eliminate manual selection
- Undo Support - Safer experimentation and error recovery

**Medium Priority (Customization)**:
- Configuration File - JSON-based positioning without code edits
- Interactive Parameter Dialogs - UI for adjusting all parameters
- Template Library - Support multiple page sizes and formats

**Golf-Specific Features**:
- Yardage Line Generation - Auto-generate distance markers
- Hazard Distance Calculator - Click-to-measure tool
- Elevation Profile Support - Import and visualize GPX elevation data

**Performance & Quality**:
- Parallel PDF Export - 50-75% faster Stage 4
- Unit Tests for Utilities - Automated testing
- Enhanced Logging - Better debugging and diagnostics

---

## License

MIT License - see [LICENSE](LICENSE) for details

Copyright (c) 2025 BitNinja01

---

## Support

For issues, questions, or feature requests:

1. Check the [troubleshooting section](#troubleshooting)
2. Review existing GitHub issues
3. Create a new issue with:
   - Inkscape version
   - Python version
   - Steps to reproduce
   - Example SVG file (if applicable)
---

**Built with ❤️ for golfers who love automation**
