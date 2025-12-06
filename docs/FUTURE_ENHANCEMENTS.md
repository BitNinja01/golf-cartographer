# Future Enhancements

Ideas and planned improvements for Golf Cartographer. These enhancements are organized by priority and feasibility based on the current architecture.

---

## High Priority - Workflow Improvements

### 1. Batch Hole Grouping (Stage 2 Automation)

**Problem**: Currently requires running "2. Group Hole" 18 times manually

**Solution**: Create a single tool that prompts for all 18 holes in sequence
- Present modal: "Select elements for Hole 1" → "Select elements for Hole 2" → etc.
- Store selections between prompts
- Create all 18 hole groups in one operation
- Undo entire operation if user cancels mid-way

**Technical approach**:
- Use Inkscape's selection changed events
- Maintain state between user selections
- Similar to existing `group_hole.py` but with iteration logic

**Impact**: Reduces Stage 2 from ~90-144 seconds to ~30-60 seconds (single operation)

---

### 2. Auto-Detect Holes from Greens

**Problem**: User must manually select which elements belong to each hole

**Solution**: Automatically detect hole boundaries using green locations
- Find all green elements (color detection already exists in `color_utils.py`)
- For each green, find nearby fairways, bunkers, water within radius
- Group elements by proximity to green centroid
- Present preview for user to confirm/adjust

**Technical approach**:
- Use existing `calculate_centroid()` from `geometry_utils.py`
- Implement spatial clustering (k-means or distance-based)
- Add proximity threshold parameter (default: 200 yards in SVG units)

**Impact**: Could eliminate manual selection entirely for well-structured OSM data

---

### 3. Undo Support for All Stages

**Problem**: No way to undo extension operations without manual Ctrl+Z spam

**Solution**: Add "Undo Last Operation" tool
- Store pre-operation SVG state
- Restore on demand
- Keep history for last N operations (default: 5)

**Technical approach**:
- Serialize document state before each extension runs
- Store in temp directory: `/tmp/golf-cartographer-history/`
- Create new tool: "0. Undo Last Golf Tool Operation"

**Impact**: Safer experimentation, easier error recovery

---

## Medium Priority - Customization & Configuration

### 4. Configuration File for Positioning

**Problem**: Changing bounding boxes requires editing Python code

**Solution**: Create `.golf-config.json` file in document directory
```json
{
  "hole_placement": {
    "x": 0.257,
    "y": 0.247,
    "width": 3.736,
    "height": 6.756,
    "buffer": 0.90
  },
  "green_scaling": {
    "x": 0.250,
    "y": 7.000,
    "width": 3.750,
    "height": 3.750,
    "buffer": 0.80
  },
  "units": "inches"
}
```

**Technical approach**:
- Add config loading to utility modules
- Fall back to hardcoded defaults if config missing
- Validate config schema on load

**Impact**: Users can customize without editing code

---

### 5. Interactive Parameter Dialog

**Problem**: No UI for adjusting parameters without code edits

**Solution**: Add dialog boxes to each tool with adjustable parameters
- Stage 1: Off-canvas tolerance, color detection sensitivity
- Stage 2: Hole number input (1-18)
- Stage 3: Bounding box coordinates, buffer percentages, rotation angle offset
- Stage 4: Output directory, PDF naming scheme

**Technical approach**:
- Use Inkscape's `<param>` tags in `.inx` files
- Access via `self.options.parameter_name` in Python
- Add validation and helpful tooltips

**Impact**: More accessible to non-developers

---

### 6. Template Library System

**Problem**: Single hardcoded yardage book layout

**Solution**: Support multiple templates
- Templates directory: `~/.config/golf-cartographer/templates/`
- Each template defines: page size, hole positions, green positions, PDF export scheme
- User selects template from dropdown in Stage 3

**Templates to create**:
- `default.json` - Current 4.25" x 11" booklet
- `a5.json` - A5 paper size
- `pocket.json` - Small 3" x 5" cards
- `digital.json` - Optimized for tablet viewing

**Technical approach**:
- Template JSON schema with validation
- Template selector parameter in Stage 3 `.inx`
- Load template and override default constants

**Impact**: Support different printing formats and devices

---

## Medium Priority - Golf-Specific Features

### 7. Yardage Line Generation

**Problem**: Yardage lines must be added manually to OSM data

**Solution**: Auto-generate yardage lines from centerline
- User draws single centerline path from tee to green
- Tool generates perpendicular yardage markers every 25 yards
- Labels with distance to green
- Color-coded by distance (e.g., red < 100yd, white 100-200yd, blue > 200yd)

**Technical approach**:
- Path interpolation using `inkex.paths` API
- Calculate perpendicular vectors at intervals
- Create line elements with text labels
- Use existing transform utilities

**Impact**: Eliminates most tedious manual work

---

### 8. Hazard Distance Calculator

**Problem**: No automatic distance measurements to hazards

**Solution**: Click-to-measure tool for landing zones
- User clicks on tee box → hazard → green
- Tool calculates and displays distances
- Optionally adds text labels to SVG

**Technical approach**:
- Interactive mode with click handlers
- Use document units and scaling from `get_canvas_bounds()`
- Real-world distance = SVG distance × scale factor
- Convert to yards/meters based on preference

**Impact**: Faster yardage book annotation

---

### 9. Elevation Profile Support

**Problem**: No elevation data in yardage books

**Solution**: Import elevation data and visualize
- Accept GPS track with elevation (GPX format)
- Generate elevation profile graph per hole
- Position profile in yardage book layout
- Show uphill/downhill indicators

**Technical approach**:
- Parse GPX using `xml.etree.ElementTree`
- Generate SVG path for elevation profile
- Scale to fit in designated area (e.g., bottom of page)
- Add grid lines and labels

**Impact**: Professional-quality yardage books with elevation

---

## Low Priority - Quality of Life

### 10. Progress Indicators

**Problem**: No feedback during long operations (Stage 4 takes 2-5 minutes)

**Solution**: Show progress bar or status updates
- "Processing hole 5 of 18..."
- "Exporting PDF 12 of 20..."
- Estimated time remaining

**Technical approach**:
- Use `inkex.errormsg()` for status updates
- Update every N iterations
- Consider Inkscape's progress API if available

**Impact**: Better UX, less uncertainty

---

### 11. Dry Run / Preview Mode

**Problem**: Can't preview changes before applying

**Solution**: Add "Preview" checkbox to each tool
- Shows what would change without modifying document
- Highlights affected elements
- Displays summary: "Would create 18 hole groups, affecting 342 elements"

**Technical approach**:
- Run logic without committing changes
- Use temporary layer for preview
- Delete preview layer after user confirms

**Impact**: Safer workflow, easier learning

---

### 12. Validation & Pre-flight Checks

**Problem**: Extensions fail silently or with cryptic errors

**Solution**: Add validation before each stage
- Stage 1: Check document has content, valid units
- Stage 2: Verify at least N elements selected
- Stage 3: Confirm exactly 18 hole groups exist, template layer present
- Stage 4: Verify all required layers/groups exist

**Technical approach**:
- Validation functions in each tool's `effect()` method
- Clear error messages with remediation steps
- Use `inkex.errormsg()` for user feedback

**Impact**: Fewer confused users, better error messages

---

## Low Priority - Advanced Features

### 13. Course Database Integration

**Problem**: No way to share/reuse course data

**Solution**: Community course database
- Export course configuration + grouped holes
- Import pre-configured courses
- Cloud storage or GitHub-based repository
- Search by course name, location, difficulty

**Technical approach**:
- Export format: `.golf-course` file (ZIP containing SVG + metadata JSON)
- Metadata: course name, location, par, rating, slope
- Web interface for browsing/downloading

**Impact**: Easier to create books for popular courses

---

### 14. Multi-Course Yardage Book

**Problem**: Can only process one course per document

**Solution**: Support multiple courses in single yardage book
- "Front 9 at Course A, Back 9 at Course B" use case
- User selects which holes to include from each course
- Merge into single PDF export

**Technical approach**:
- Course selection UI
- Import holes from multiple SVG files
- Renumber holes as needed
- Adjust PDF export logic

**Impact**: Useful for courses with multiple 9-hole layouts

---

### 15. Live GPS Integration (Future)

**Problem**: Static yardage books don't update with pin positions

**Solution**: Export to format compatible with GPS apps
- Generate GeoJSON with hole polygons
- Include green contours, hazards, yardage markers
- Compatible with common golf GPS apps

**Technical approach**:
- Convert SVG coordinates to lat/lon using reference points
- Export GeoJSON with feature properties
- Document calibration process

**Impact**: Bridge between paper and digital yardage books

---

## Technical Debt & Code Quality

### 16. Unit Tests for Utility Modules

**Problem**: No automated testing

**Solution**: Add pytest-based tests for utilities
- Test `calculate_centroid()` with known shapes
- Test `get_cumulative_scale()` with various transform chains
- Test `categorize_element_by_color()` with color palette variations
- Mock Inkscape API for testing

**Technical approach**:
- Create `tests/` directory
- Use pytest + pytest-mock
- Mock `inkex` elements with test fixtures
- CI/CD with GitHub Actions

**Impact**: Safer refactoring, fewer regressions

---

### 17. Logging System

**Problem**: Debugging requires print statements

**Solution**: Comprehensive logging
- Log level control (DEBUG, INFO, WARNING, ERROR)
- Output to file: `~/.config/golf-cartographer/logs/extension.log`
- Configurable verbosity
- Include timing information for performance analysis

**Technical approach**:
- Enhance existing `logging.getLogger(__name__)` usage
- Configure handlers in each extension
- Add `--verbose` parameter to `.inx` files

**Impact**: Easier debugging and issue reporting

---

### 18. Refactor Tool #4 (Export PDFs)

**Problem**: Tool #4 hasn't received the same code quality treatment as Tools #1-3

**Solution**: Apply consistent patterns
- Add type hints with `from __future__ import annotations`
- Replace silent exception handling with logging
- Use specific exception types
- Extract any shared utilities
- Get python-expert agent review

**Technical approach**:
- Read `export_pdfs.py`
- Apply same refactoring patterns used in previous session
- Consider extracting PDF export logic to utility module

**Impact**: Consistent code quality across all tools

---

## Performance Optimizations

### 19. Caching for Repeated Operations

**Problem**: Recalculating centroids, bounding boxes for same elements

**Solution**: Add caching layer
- Cache centroid calculations by element ID
- Cache bounding box measurements
- Invalidate on transform changes
- Use LRU cache with size limit

**Technical approach**:
- Add `@lru_cache` decorators to expensive functions
- Create cache key from element ID + transform hash
- Clear cache between extension runs

**Impact**: Faster processing, especially for large courses

---

### 20. Parallel PDF Export

**Problem**: Exporting 20 PDFs sequentially takes 2-5 minutes

**Solution**: Export PDFs in parallel
- Use Python's `multiprocessing` or `concurrent.futures`
- Export 4-8 PDFs simultaneously
- Combine results after all complete

**Technical approach**:
- Create worker pool in `export_pdfs.py`
- Each worker exports one PDF
- Handle Inkscape API thread-safety

**Impact**: Reduce Stage 4 time by 50-75%

---

## Documentation Improvements

### 21. Video Tutorial Series

**Solution**: Create screencasts for each stage
- Stage 1: Preparing OSM data and flattening
- Stage 2: Grouping holes efficiently
- Stage 3: Understanding positioning and scaling
- Stage 4: Exporting and printing PDFs
- End-to-end: Complete workflow from OSM to print

**Impact**: Easier onboarding for visual learners

---

### 22. Troubleshooting Guide

**Solution**: Comprehensive troubleshooting documentation
- Common error messages with solutions
- FAQ section
- "My holes are positioned wrong" → step-by-step diagnosis
- Color detection calibration guide

**Impact**: Reduced support burden

---

## Contributing

Want to work on any of these enhancements?

1. **Check GitHub issues** - Some may already be in progress
2. **Comment on the issue** - Discuss approach before implementing
3. **Start small** - Pick a "Low Priority - Quality of Life" item first
4. **Follow patterns** - Match existing code quality standards
5. **Test thoroughly** - Manual testing on real golf courses

---

## Priority Legend

- **High Priority**: Biggest workflow improvements, relatively straightforward implementation
- **Medium Priority**: Valuable features requiring more design work
- **Low Priority**: Nice-to-have features, simpler implementations
- **Advanced**: Complex features requiring significant architecture changes

---

**Last Updated**: 2025-12-06

**Total Enhancement Ideas**: 22
