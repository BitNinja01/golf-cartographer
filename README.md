# Golf Cartographer

**Automate golf yardage book creation from OpenStreetMap data in Inkscape**

Transform raw OSM exports into professional, print-ready 20-page yardage books through an intelligent five-stage pipeline. No more hours of manual layer organization, positioning, and PDF exports.

---

## What It Does

Golf Cartographer is a suite of 5 Inkscape extensions that automate the complete yardage book workflow:

1. **Flatten SVG** - Organize raw OSM data into structured element groups by color
2. **Group Hole** (×18) - Organize elements into per-hole groups with terrain and greens
3. **Auto-Place Holes and Scale Greens** - Position holes and scale green details automatically
4. **Add Hole Label** (×18) - Add hole numbers, par, and tee box yardages
5. **Export PDFs** - Generate 20 print-ready PDFs in booklet format

Result: A complete yardage book ready for saddle-stitch printing, all from a single OSM export.

---

## Requirements

- **Inkscape 1.4.2 or later** (required - earlier versions have incompatible APIs)
- **Python 3.7+** (bundled with modern Inkscape)
- **OpenStreetMap SVG export** of your golf course

<!-- SCREENSHOT: NICE-TO-HAVE - Raw OSM Export
     Show: Screenshot of raw OSM export opened in Inkscape showing typical messy, ungrouped structure
     Why: First-time users see what OSM exports look like and understand why Stage 1 is necessary -->

---

## Installation

1. **Locate your Inkscape extensions folder**:
   - **Linux**: `~/.config/inkscape/extensions/`
   - **macOS**: `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
   - **Windows**: `%APPDATA%\inkscape\extensions\`

2. **Copy extension files**:
   ```bash
   cp golf-cartographer/* ~/.config/inkscape/extensions/
   ```

3. **Restart Inkscape**

4. **Verify**: Open Inkscape and check `Extensions > Golf Cartographer` - you should see 5 numbered tools

<!-- SCREENSHOT: CRITICAL - Installation Verification
     Show: Inkscape menu navigation: Extensions > Golf Cartographer with all 5 numbered tools visible in submenu
     Why: Users verify correct installation and see exact menu structure -->

---

## Quick Start

### The Five-Stage Workflow

#### Stage 1: Flatten SVG
```
Extensions > Golf Cartographer > 1. Flatten SVG
```
Processes raw OSM data. Takes ~5-15 seconds. Creates organized element groups by color (greens, fairways, bunkers, water, trees, paths).

<!-- SCREENSHOT: CRITICAL - Stage 1 Before/After Comparison
     Show: Side-by-side showing raw OSM SVG (left) vs flattened organized groups (right) with layers panel visible
     Why: "Organized element groups by color" is abstract - visual proof shows transformation value
     Reference: examples/course_stage_1.svg with layers panel -->

#### Stage 2: Group Hole (Run 18 times)
```
Extensions > Golf Cartographer > 2. Group Hole
```
For each hole 1-18:
1. Select all elements belonging to that hole
2. Run the tool
3. Enter hole number (1-18) in dialog

Takes ~3-8 seconds per hole. Each creates a `hole_N` group with terrain and green elements organized separately.

<!-- SCREENSHOT: CRITICAL - Hole Selection & Dialog
     Show: Inkscape with hole elements selected (highlighted) + Group Hole dialog with hole number input field
     Why: "Select all elements belonging to that hole" is ambiguous - shows what proper selection looks like -->

<!-- SCREENSHOT: HIGH - Hole Grouping Layers Panel
     Show: Inkscape layers panel showing properly grouped hole (hole_N with terrain/green subelements in hierarchy)
     Why: Shows actual layer structure users should verify after Stage 2
     Reference: examples/course_stage_2.svg layers panel -->

#### Stage 3: Auto-Place Holes and Scale Greens
```
Extensions > Golf Cartographer > 3. Auto-Place Holes and Scale Greens
```
No parameters needed. Runs once. Takes ~30-60 seconds.

Automatically:
- Positions all 18 holes in page "top" area (3.736" × 6.756")
- Rotates holes to face greens for optimal viewing
- Extracts and scales greens to fit "bottom" area (3.75" × 3.75")
- Applies 10% margins around holes, 20% around green details

<!-- SCREENSHOT: CRITICAL - Stage 3 Output
     Show: Inkscape canvas after Stage 3 with holes positioned in "top" area and greens scaled in "bottom" area with visible page boundaries
     Why: Complex transformation hard to visualize - shows actual layout positioning and top/bottom division
     Reference: examples/course_stage_3.svg with page boundaries visible -->

#### Stage 4: Add Hole Label (Run 18 times)
```
Extensions > Golf Cartographer > 4. Add Hole Label
```
For each hole 1-18:
1. Run the tool
2. Enter:
   - Hole number (1-18)
   - Par (3-6)
   - Tee box names and yardages (up to 6 tees)
3. Customize fonts if desired

Takes ~3-5 seconds per hole. Each adds a circle with hole number, par text, and tee yardages. Supports custom fonts from glyph library.

<!-- SCREENSHOT: CRITICAL - Add Hole Label Dialog
     Show: Add Hole Label dialog showing all input fields (hole number, par, tee box names, yardages)
     Why: Users need to know what information to prepare before running this stage -->

<!-- SCREENSHOT: HIGH - Hole Label Result
     Show: Close-up of a finished hole label showing circle, hole number, par, and tee box yardages
     Why: Users verify Stage 4 worked correctly by seeing expected visual result
     Reference: examples/course_stage_4.svg zoomed on hole label -->

#### Stage 5: Export PDFs
```
Extensions > Golf Cartographer > 5. Export PDFs
```
Parameters:
- **Output Directory**: Where to save PDFs (default: Desktop)
- **Filename Prefix**: Prefix for all files (default: `yardage_book_`)
- **Combine into Booklets**: Enable saddle-stitch format (default: enabled)

Takes ~2-5 minutes total. Generates 20 PDFs:
- **Narrow PDFs** (4.25" × 14" each): 20 individual hole pages with strategic cross-pairing
- **Wide PDFs** (8.5" × 14" each): 10 pages with pairs side-by-side
- **Booklet PDFs** (5 files): Print-ready saddle-stitch booklets (2 pages each)

<!-- SCREENSHOT: HIGH - Export PDFs Dialog
     Show: Export PDFs dialog showing three input fields (Output Directory, Filename Prefix, Combine into Booklets checkbox)
     Why: Users need to know what parameters to set before running the longest stage -->

**Print Instructions**:
1. Print each booklet double-sided (flip on short edge)
2. Stack in order (booklet 5 outside, booklet 1 innermost)
3. Fold in half and staple along center

<!-- SCREENSHOT: HIGH - Booklet Assembly Diagram
     Show: Illustration showing physical assembly steps - 5 booklets stacked (05 outside), folding, stapling along center
     Why: Saddle-stitch printing instructions hard to visualize - reduces printing errors and wasted paper -->

---

## Understanding the PDF Output

The 20 narrow PDFs are strategically paired for a complete 18-hole booklet:

| Page | Layout | Page | Layout |
|------|--------|------|--------|
| 1 | Hole 9 + Green 9 | 11 | Hole 10 + Green 8 |
| 2 | Hole 8 + Green 10 | 12 | Hole 11 + Green 7 |
| 3 | Hole 7 + Green 11 | 13 | Hole 12 + Green 6 |
| 4 | Hole 6 + Green 12 | 14 | Hole 13 + Green 5 |
| 5 | Hole 5 + Green 13 | 15 | Hole 14 + Green 4 |
| 6 | Hole 4 + Green 14 | 16 | Hole 15 + Green 3 |
| 7 | Hole 3 + Green 15 | 17 | Hole 16 + Green 2 |
| 8 | Hole 2 + Green 16 | 18 | Hole 17 + Green 1 |
| 9 | Hole 1 + Green 17 | 19 | Hole 18 + Notes |
| 10 | Scorecard + Green 18 | 20 | Back + Cover |

Each hole gets paired with a different hole's green for strategic mid-round reference (hole 9 appears twice as the turning point).

<!-- SCREENSHOT: HIGH - PDF Sample Pages
     Show: 2-3 sample narrow PDF pages side-by-side (4.25" × 14" format) with hole layout on top and green detail on bottom, clearly labeled
     Why: Users can't visualize cross-paired narrow PDFs - seeing real examples helps understand workflow value
     Reference: examples/exported_pdfs/ sample pages -->

---

## Configuration

All measurements use **inches**. Verify document units in Inkscape before running.

<!-- SCREENSHOT: CRITICAL - Document Units Dialog
     Show: Inkscape's File > Document Properties dialog with Units dropdown clearly showing "in" (inches) selected
     Why: Critical prerequisite mentioned multiple times - shows exactly where and how to set this
     Prevents positioning failures -->

### Adjusting Hole Placement

Edit `auto_place_holes.py` if you need custom positioning:

```python
# Top area (hole layouts)
BOUNDING_BOX = {
    'x': 0.257,      # Left margin
    'y': 0.247,      # Top margin
    'width': 3.736,  # Hole layout width
    'height': 6.756  # Hole layout height
}
EDGE_BUFFER = 0.90  # Use 90% of box (10% margin)

# Bottom area (green details)
TARGET_BOX = {
    'x': 0.250,      # Left margin
    'y': 7.000,      # Start position
    'width': 3.750,  # Green detail width
    'height': 3.750  # Green detail height
}
GREEN_EDGE_BUFFER = 0.80  # Use 80% of box (20% margin)
```

### Fixing Color Detection

If elements aren't categorized correctly, OSM colors may differ from defaults. Adjust thresholds in `color_utils.py` for your specific OSM export.

---

## Troubleshooting

### Extensions don't appear in menu
- Verify both `.py` and `.inx` files copied to extensions folder
- Restart Inkscape completely
- Check Inkscape version is 1.4.2+

### ImportError when running tool
- All utility files must be present: `transform_utils.py`, `geometry_utils.py`, `color_utils.py`
- Verify Python 3.7+ is available

### Color detection not working
- Check element colors match OSM palette
- Verify elements have fill or stroke colors set
- Manually adjust colors in Inkscape if needed, then retry

### Holes positioned incorrectly
- Verify document units set to inches (File > Document Properties > Units)
- Ensure holes properly grouped in Stage 2 with both terrain and greens
- Check BOUNDING_BOX values match your template

### PDFs fail to export
- All holes must be named `hole_1` through `hole_18` (Stage 2 creates these)
- Output directory must exist and be writable
- Check no holes are locked in Inkscape
- Verify Inkscape is accessible from command line (for PDF export)

---

## File Structure

```
golf-cartographer/
├── flatten_svg.inx / .py          # Stage 1
├── group_hole.inx / .py            # Stage 2
├── auto_place_holes.inx / .py      # Stage 3
├── add_hole_label.inx / .py        # Stage 4
├── export_pdfs.inx / .py           # Stage 5
├── transform_utils.py              # Shared transform utilities
├── geometry_utils.py               # Shared geometry utilities
├── color_utils.py                  # Color detection and matching
├── glyph_library.py                # Font/glyph utilities
├── prepare_glyph_library.inx / .py # Utility for glyph setup
└── python_libraries/               # Bundled dependencies
    ├── pypdf/                      # PDF manipulation (v6.4.2)
    └── typing_extensions.py        # Python compatibility
```

---

## Examples

The `examples/` folder contains SVG files showing output at each stage:

- `examples/course_stage_1.svg` - After Stage 1 (flattened elements)
- `examples/course_stage_2.svg` - After Stage 2 (grouped holes ×18)
- `examples/course_stage_3.svg` - After Stage 3 (positioned holes and scaled greens)
- `examples/course_stage_4.svg` - After Stage 4 (hole labels added ×18)
- `examples/course_stage_5.svg` - After Stage 5 (final yardage book)
- `examples/exported_pdfs/` - Sample output PDFs

---

## Performance

Expected processing times on typical hardware:

| Stage | Time |
|-------|------|
| Stage 1 (Flatten) | 5-15s |
| Stage 2 per hole | 3-8s (×18 = 1-2 min total) |
| Stage 3 (Auto-Place) | 30-60s |
| Stage 4 per hole | 3-5s (×18 = 1-2 min total) |
| Stage 5 (Export PDFs) | 2-5 min |
| **Total** | **~10-15 minutes** |

---

## Contributing

Contributions welcome! Check [FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md) for ideas:

**High Priority**: Batch hole grouping, auto-detect holes, undo support
**Medium Priority**: Configuration files, template library, interactive dialogs
**Golf Features**: Yardage lines, hazard calculator, elevation profiles
**Performance**: Parallel PDF export, unit tests, enhanced logging

To contribute:
1. Read [FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md)
2. Add type hints and docstrings
3. Test manually in Inkscape
4. Submit PR with clear description and example SVG

---

## License

MIT License - see [LICENSE](LICENSE) for details

Copyright (c) 2025 BitNinja01
