# Golf Cartographer

**An Inkscape extension suite that automates golf yardage book creation from OpenStreetMap data**

Transform raw OSM exports into professional, print-ready golf yardage books through an intelligent four-stage pipeline that handles flattening, grouping, positioning, and PDF export.

---

## Overview

Golf Cartographer eliminates the tedious manual work of creating golf course yardage books. Instead of spending hours organizing SVG layers, positioning holes, and exporting individual PDFs, this extension suite automates the entire workflow from raw OpenStreetMap data to a complete 20-page yardage book ready for printing.

### What It Does

- **Flattens** complex nested SVG hierarchies from OSM exports
- **Groups** golf course elements by hole using intelligent color detection
- **Positions** all 18 holes with automatic rotation and scaling
- **Scales** greens to appropriate detail size for yardage books
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
   - Navigate to `Extensions > Golf Yardage Book`
   - You should see 4 tools numbered 1-4

---

## Quick Start

### Basic Workflow

1. **Export your golf course** from OpenStreetMap as SVG
2. **Open the SVG** in Inkscape
3. **Run each tool in sequence**:
   - `Extensions > Golf Yardage Book > 1. Flatten SVG`
   - `Extensions > Golf Yardage Book > 2. Group Hole` (run 18 times, once per hole)
   - `Extensions > Golf Yardage Book > 3. Auto-Place Holes and Scale Greens`
   - `Extensions > Golf Yardage Book > 4. Export PDFs`

4. **Find your PDFs** in `examples/exported_pdfs/` (or your configured output directory)

### Expected Processing Time

- **Stage 1** (Flatten): ~5-15 seconds
- **Stage 2** (Group Hole): ~3-8 seconds per hole × 18 holes
- **Stage 3** (Auto-Place & Scale): ~30-60 seconds
- **Stage 4** (Export PDFs): ~2-5 minutes for all 20 PDFs

---

## Four-Stage Pipeline

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
2. Run `Extensions > Golf Yardage Book > 2. Group Hole`
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

**Example**: `examples/course_stage_3_a.svg`, `examples/course_stage_3_b.svg`

---

### Stage 4: Export PDFs

**Tool**: `4. Export PDFs`
**Input**: Complete yardage book from Stage 3
**Output**: 20 PDF files with strategic hole combinations

**What it does**:
- Exports 18 individual hole pages (holes 1-17 with opposite-side hole)
- Exports special pages:
  - `yardage_book_18_notes.pdf` - Hole 18 with notes section
  - `yardage_book_9_9.pdf` - Turn page (holes 9/9)
  - `yardage_book_back_cover.pdf` - Back cover
  - `yardage_book_chart_18.pdf` - Scorecard page

**Example output**: `examples/exported_pdfs/` (20 PDF files)

**Example**: `examples/course_stage_5.svg`

---

## Project Structure

```
golf-cartographer/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── CLAUDE.md                          # Developer guide for AI assistants
├── PICKUP_PROMPT.md                   # Session continuity for development
│
├── docs/                              # Documentation
│   └── FUTURE_ENHANCEMENTS.md        # Planned features and improvements
│
├── examples/                          # Example files showing each stage
│   ├── course_stage_1.svg            # After Stage 1 (flattening)
│   ├── course_stage_2.svg            # After Stage 2 (18 grouped holes)
│   ├── course_stage_3_a.svg          # After Stage 3 (positioned holes)
│   ├── course_stage_3_b.svg          # After Stage 3 (scaled greens)
│   ├── course_stage_5.svg            # Final yardage book
│   └── exported_pdfs/                # 20 exported PDF files
│
└── golf-cartographer/                 # Inkscape extension files
    ├── flatten_svg.py                # Stage 1: Flatten SVG
    ├── flatten_svg.inx               # Stage 1: Metadata
    ├── group_hole.py                 # Stage 2: Group Hole
    ├── group_hole.inx                # Stage 2: Metadata
    ├── auto_place_holes.py           # Stage 3: Auto-Place & Scale
    ├── auto_place_holes.inx          # Stage 3: Metadata
    ├── export_pdfs.py                # Stage 4: Export PDFs
    ├── export_pdfs.inx               # Stage 4: Metadata
    │
    ├── transform_utils.py            # Shared transform utilities
    ├── geometry_utils.py             # Shared geometry utilities
    └── color_utils.py                # Shared color detection utilities
```

---

## Technical Architecture

### Utility Modules

The extension suite uses three shared utility modules to eliminate code duplication:

#### `transform_utils.py` (361 lines)
- `SimpleBoundingBox` - Type-safe bounding box class
- `get_cumulative_scale()` - Extract scale from transform chains
- `set_stroke_recursive()` - Apply stroke widths to element trees
- `apply_stroke_compensation()` - Adjust stroke widths after scaling
- `measure_elements_via_temp_group()` - Accurate bounding box measurement

#### `geometry_utils.py` (247 lines)
- `calculate_centroid()` - Shoelace formula with 3-level fallback
- `calculate_rotation_angle()` - Orient elements toward target direction
- `get_canvas_bounds()` - Extract document dimensions

#### `color_utils.py` (304 lines)
- `categorize_element_by_color()` - Fuzzy color matching for OSM elements
- Supports greens, fairways, bunkers, water, trees, paths, and mapping lines

### Design Principles

- **Modular Pipeline**: Each stage produces standalone output
- **No Side Effects**: Temporary groups guarantee document restoration
- **Type Safety**: Comprehensive type hints throughout
- **Error Handling**: Specific exceptions with detailed logging
- **Transform Preservation**: Careful handling of SVG transform matrices

---

## Code Statistics

- **Total Python Code**: ~2,959 lines
- **Main Tools**: ~2,047 lines
- **Shared Utilities**: ~912 lines
- **Code Deduplication**: Eliminated ~475 lines of duplicate code

### File Sizes

| File | Lines | Purpose |
|------|-------|---------|
| `auto_place_holes.py` | 624 | Stage 3: Combined placement & scaling |
| `group_hole.py` | 527 | Stage 2: Hole grouping |
| `export_pdfs.py` | 474 | Stage 4: PDF export |
| `flatten_svg.py` | 422 | Stage 1: SVG flattening |
| `transform_utils.py` | 361 | Transform utilities |
| `color_utils.py` | 304 | Color detection utilities |
| `geometry_utils.py` | 247 | Geometry utilities |

---

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Developer guide for AI assistants (architecture, workflow, requirements)
- **[FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md)** - Planned features and improvement ideas
- **[PICKUP_PROMPT.md](PICKUP_PROMPT.md)** - Development session continuity guide

---

## Examples

The `examples/` directory contains a complete workflow demonstration:

1. **`course_stage_1.svg`** - After flattening (5.3 MB)
2. **`course_stage_2.svg`** - After grouping 18 holes (4.2 MB)
3. **`course_stage_3_a.svg`** - Holes positioned in top area (23.5 MB)
4. **`course_stage_3_b.svg`** - Greens scaled in bottom area (6.5 MB)
5. **`course_stage_5.svg`** - Complete yardage book ready for export (21.6 MB)
6. **`exported_pdfs/`** - 20 PDF files (1.5 MB total)

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

# Stage 4: Green detail area (bottom of page)
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

### Testing Workflow

Since Inkscape extensions don't support automated testing:

1. Make code changes
2. Copy updated files to extensions directory
3. Restart Inkscape
4. Test on example SVG files
5. Verify output at each pipeline stage

### Code Quality Standards

- ✅ Type hints throughout (using `from __future__ import annotations`)
- ✅ Specific exception types (not bare `except:`)
- ✅ Logging with `%s` style (not f-strings)
- ✅ Comprehensive docstrings for all functions/classes
- ✅ Try/finally guarantees for temporary modifications

### Import Pattern

**CRITICAL**: Inkscape runs extensions directly, not as packages. Always use absolute imports:

```python
# ✅ Correct
from transform_utils import SimpleBoundingBox
from geometry_utils import calculate_centroid

# ❌ Incorrect (will fail)
from .transform_utils import SimpleBoundingBox
from .geometry_utils import calculate_centroid
```

---

## Contributing

Contributions are welcome! Here's how to get started:

1. **Read the documentation**:
   - [CLAUDE.md](CLAUDE.md) for architecture and development setup
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
   - Verification that all 4 stages still work

### Ideas for Contributions

See [FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md) for a full list of planned features, including:

- Batch processing for multiple courses
- Configurable parameters via UI dialogs
- Enhanced color detection with ML
- Distance measurement tools
- Multiple export format support
- Template management system

---

## License

MIT License - see [LICENSE](LICENSE) for details

Copyright (c) 2025 BitNinja01

---

## Acknowledgments

- **OpenStreetMap** for providing golf course data
- **Inkscape** for the excellent extension API
- **Golf community** for feedback and testing

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
