# Future Enhancements

Ideas and planned improvements for Golf Cartographer. These enhancements are organized by priority and feasibility based on the current architecture.

---

## Medium Priority - Customization & Configuration

### 1. Configuration File for Positioning

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

**Alternative approach**: Detect the 'guide' for the top and bottom pages that we need to fit stuff in. Use these to automatically figure out where stuff needs to go. This way, users could size the base template any way they want, and the code will still position holes and greens in expected places.

**Impact**: Users can customize without editing code

---

### 2. Interactive Parameter Dialog

**Problem**: No UI for adjusting parameters without code edits

**Solution**: Add dialog boxes to each tool with adjustable parameters
- Stage 1: Off-canvas tolerance, color detection sensitivity
- Stage 2: Hole number input (1-18)
- Stage 3: Bounding box coordinates, buffer percentages, rotation angle offset
- Stage 4: Font options, label positioning
- Stage 5: Output directory, PDF naming scheme

**Technical approach**:
- Use Inkscape's `<param>` tags in `.inx` files
- Access via `self.options.parameter_name` in Python
- Add validation and helpful tooltips

**Impact**  : More accessible to non-developers
**Consider**: This could bloat the UI. Should be done with great care. 

---

### 6. Elevation Profile Support

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

**Impact**: Professional-quality green sections with elevation data

---

## Low Priority - Quality of Life

### 7. Progress Indicators

**Problem**: No feedback during long operations (Stage 5 takes 2-5 minutes)

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

### 9. Validation & Pre-flight Checks

**Problem**: Extensions fail silently or with cryptic errors

**Solution**: Add validation before each stage
- Stage 1: Check document has content, valid units
- Stage 2: Verify at least N elements selected
- Stage 3: Template layer present
- Stage 4: Verify hole groups exist for labeling
- Stage 5: Verify all required layers/groups exist for export

**Technical approach**:
- Validation functions in each tool's `effect()` method
- Clear error messages with remediation steps
- Use `inkex.errormsg()` for user feedback

**Impact**: Fewer confused users, better error messages

---

## Low Priority - Advanced Features

### 10. Course Database Integration

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

### 11. Multi-Course Yardage Book

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

## Technical Debt & Code Quality

### 13. Unit Tests for Utility Modules

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

### 14. Logging System

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

**Impact**: Reduce Stage 5 time by 50-75%

---

## Documentation Improvements

### 21. Video Tutorial Series

**Solution**: Create screencasts for each stage
- Stage 1: Preparing OSM data and flattening
- Stage 2: Grouping holes efficiently
- Stage 3: Understanding positioning and scaling
- Stage 4: Adding hole labels with custom fonts
- Stage 5: Exporting and printing PDFs
- End-to-end: Complete workflow from OSM to print

**Impact**: Easier onboarding for visual learners
