# Glyph Libraries for Golf Cartographer

## Overview

Glyph libraries are SVG files containing pre-converted character glyphs as vector paths. This system enables precise, measurable text positioning in Inkscape extensions where runtime text measurement is unavailable.

**Why this approach?**
- Inkscape's Python API (inkex) operates at XML/DOM level, not rendering level
- Text bounding boxes return position fallbacks, not actual dimensions
- Text-to-path conversion in inkex creates empty paths (no access to font data)
- **Solution**: Pre-convert glyphs to paths with measurable bounding boxes

## SVG File Structure

Each glyph library is a standalone SVG file containing all needed characters as `<path>` elements with unique IDs.

### Required Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="1000" height="200"
     viewBox="0 0 1000 200">

  <!-- Digit glyphs -->
  <path id="glyph-0" d="M12.5,10.2 L18.3,10.2 ..." />
  <path id="glyph-1" d="M34.1,10.2 L39.8,10.2 ..." />
  <path id="glyph-2" d="M55.7,10.2 L61.4,10.2 ..." />
  <!-- ... remaining digits ... -->

  <!-- Special characters -->
  <path id="glyph-colon" d="M123.4,15.6 L125.2,17.8 ..." />
  <path id="glyph-space" d="" />  <!-- Empty path for spacing -->

  <!-- Letter glyphs (case-sensitive) -->
  <path id="glyph-P" d="M145.2,10.2 L151.8,10.2 ..." />
  <path id="glyph-a" d="M167.3,10.2 L172.9,10.2 ..." />
  <path id="glyph-r" d="M189.5,10.2 L194.8,10.2 ..." />

</svg>
```

### Key Requirements

1. **ID Naming Convention**:
   - Digits: `glyph-0`, `glyph-1`, `glyph-2`, ..., `glyph-9`
   - Letters: `glyph-P`, `glyph-a`, `glyph-r` (case-sensitive!)
   - Special: `glyph-colon`, `glyph-space`, `glyph-period`, etc.

2. **Path Data**:
   - Each `<path>` element MUST have a `d` attribute with actual path data
   - Empty `d=""` is only acceptable for `glyph-space` (acts as spacing)
   - Path data contains the vector outline of the character

3. **Reference Size**:
   - Create glyphs at 24pt font size (reference size)
   - Runtime code will scale paths for different sizes

4. **Positioning**:
   - Physical position of paths in the SVG doesn't matter
   - The `glyph_library.py` loader will measure and clone paths
   - Keep glyphs spaced out for easy visual inspection

## Creating a Glyph Library in Inkscape

### Method 1: Automated Preparation (Recommended)

The **Prepare Glyph Library** utility automates the initial setup:

#### 1. Run the Utility
- Launch Inkscape
- Extensions → Golf Cartographer → **Prepare Glyph Library**
- Set your desired font family and style
- Click Apply

#### 2. What It Creates
The utility automatically creates:
- All digits (0-9) as individual text elements
- All capitals (A-Z) as individual text elements
- All lowercases (a-z) as individual text elements
- Canvas sized to 40mm × 200mm
- All text at 24pt in your chosen font
- Characters spaced 7mm apart
- Organized into three groups
- **IDs pre-assigned**: Each character already has the correct glyph ID (`glyph-0`, `glyph-A`, `glyph-a`, etc.)
- **Visual order**: Characters appear left-to-right (0→9, A→Z, a→z)
- **DOM order**: Elements added in reverse order for proper stacking after path conversion
- **Clean document**: Removes all existing layers for a clean starting point

#### 3. Convert to Paths
- Select all text elements (Ctrl+A or click each group)
- Menu: **Path → Object to Path** (Shift+Ctrl+C)
- Menu: **Path → Break Apart** (Shift+Ctrl+K)

#### 4. Verify Glyph IDs
The IDs are already set correctly by the utility:
- Digits: `glyph-0`, `glyph-1`, ..., `glyph-9`
- Capitals: `glyph-A`, `glyph-B`, ..., `glyph-Z`
- Lowercases: `glyph-a`, `glyph-b`, ..., `glyph-z`

You can verify by selecting a glyph and checking Object → Object Properties (Shift+Ctrl+O).

#### 5. Add Special Characters (Optional)
If you need additional characters (`:`, `.`, `-`, etc.):
- Use Text Tool to add them
- Convert to path (Path → Object to Path)
- Assign IDs: `glyph-colon`, `glyph-period`, `glyph-hyphen`

#### 6. Save the Library
- File → Save As → **Plain SVG** (not Inkscape SVG!)
- Filename: `fontname_24pt.svg` (e.g., `arial_24pt.svg`)
- Location: `golf-cartographer/glyph_libraries/`
- The IDs are already set, so the library is ready to use!

---

### Method 2: Manual Creation

If you prefer manual setup or need a custom character set:

#### 1. Open Blank Document
- Launch Inkscape
- File → New (or Ctrl+N)

#### 2. Create Source Text
- Select Text Tool (T key)
- Click on canvas and type all needed characters:
  ```
  0123456789: Par
  ```
- Select the text, then set font properties:
  - **Font**: Arial (or your target font)
  - **Size**: 24pt
  - **Style**: Regular (Bold/Italic as needed)

#### 3. Convert Text to Paths
- Select the text element
- Menu: **Path → Object to Path** (or Shift+Ctrl+C)
- This converts the text to vector paths

#### 4. Break Into Individual Glyphs
- With the converted path still selected
- Menu: **Path → Break Apart** (or Shift+Ctrl+K)
- This separates each character into its own path element

#### 5. Assign Glyph IDs
For each character path (select one at a time):
- Menu: **Object → Object Properties** (or Shift+Ctrl+O)
- In the "ID" field, enter the appropriate ID:

**For digits** (left to right):
- First '0' → `glyph-0`
- Second '1' → `glyph-1`
- Third '2' → `glyph-2`
- ... through `glyph-9`

**For special characters**:
- ':' (colon) → `glyph-colon`

**For letters** (case-sensitive!):
- 'P' (capital) → `glyph-P`
- 'a' (lowercase) → `glyph-a`
- 'r' (lowercase) → `glyph-r`

#### 6. Optional: Organize Visually
- Arrange glyphs in a logical order for easy visual verification
- Suggested layout: digits in one row, letters in another
- Spacing doesn't matter (only IDs and path data matter)

#### 7. Save the Library
- File → Save As
- Navigate to: `golf-cartographer/glyph_libraries/`
- Filename: `arial_24pt.svg` (or your font name + size)
- Format: **Plain SVG** (not Inkscape SVG)
- Click Save

#### 8. Verify the Output
Open the saved SVG in a text editor and verify:
- Each `<path>` has correct `id="glyph-X"` attribute
- Each `<path>` has a `d="M..."` attribute with actual data (not empty)
- All needed characters are present

## Required Characters for Golf Cartographer

### Minimal Set (for yardage labels)
```
Characters: 0123456789: Par
Glyph IDs:
  glyph-0, glyph-1, glyph-2, glyph-3, glyph-4,
  glyph-5, glyph-6, glyph-7, glyph-8, glyph-9,
  glyph-colon, glyph-space,
  glyph-P, glyph-a, glyph-r
```

### Extended Set (for future features)
```
Additional: ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz .,!?-
```

## Example SVG Snippet

Here's what a correctly formatted glyph looks like:

```xml
<path
  id="glyph-3"
  d="M 45.234,12.567 C 48.123,12.567 50.456,13.789 52.234,16.234
     L 52.234,18.901 C 50.456,21.345 48.123,22.567 45.234,22.567
     C 42.345,22.567 40.012,21.345 38.234,18.901
     L 38.234,16.234 C 40.012,13.789 42.345,12.567 45.234,12.567 Z"
  style="fill:#000000;stroke:none" />
```

**Key points**:
- `id="glyph-3"` → identifies this as the digit "3"
- `d="M 45.234,12.567 C ..."` → actual vector path data (will vary by font)
- `style` → optional, can include fill color, stroke, etc.

## Creating Custom Libraries

### For Different Fonts
1. Repeat the creation process with your desired font
2. Save with descriptive name: `helvetica_24pt.svg`, `times_24pt.svg`
3. Use the same glyph ID naming convention

### For Different Sizes
You can create libraries at different reference sizes, but **24pt is recommended**:
- Consistent reference size across all fonts
- Runtime code scales paths mathematically
- Easier to maintain and compare libraries

### For Different Styles
Create separate libraries for each style:
- `arial_24pt_regular.svg`
- `arial_24pt_bold.svg`
- `arial_24pt_italic.svg`

## Troubleshooting

### Problem: Text-to-Path creates grouped objects
**Solution**: The Break Apart step should separate them. If not:
- Select the group
- Object → Ungroup (Shift+Ctrl+G)
- Then try Path → Break Apart again

### Problem: Can't find Object Properties
**Solution**:
- Menu: Object → Object Properties (Shift+Ctrl+O)
- Or right-click the object → Object Properties

### Problem: Saved SVG has transform attributes
**Solution**: This is okay! The `glyph_library.py` loader handles transforms.
- For cleaner output: Edit → Select All, then Object → Transform → Apply
- This bakes transforms into the path data

### Problem: Empty path `d=""` for all glyphs
**Solution**: This means text wasn't converted properly:
1. Undo back to text state
2. Ensure text is selected (not in edit mode)
3. Try Path → Object to Path again
4. If still failing, check Inkscape version (1.4.2+ required)

## Usage in Code

Once created, the glyph library is loaded by `glyph_library.py`:

```python
from glyph_library import GlyphLibrary

# Load library (once per extension execution)
lib = GlyphLibrary('golf-cartographer/glyph_libraries/arial_24pt.svg')

# Compose text from glyphs
group, width, height = lib.compose_text(
    text="350",
    x=100,
    y=100,
    font_size=12,    # Scales from 24pt reference
    spacing=2         # Pixels between glyphs
)

# Add to document
self.svg.append(group)

# Use measured dimensions for alignment
right_edge = x + width
```

## Technical Notes

### Why Paths Are Measurable

Unlike text elements, path elements have **geometric bounding boxes** that inkex can measure reliably:

```python
# Text: returns fallback (position as dimensions)
text_bbox = text_elem.bounding_box()  # ❌ 100x100 for text at (100,100)

# Path: returns actual vector bounds
path_bbox = path_elem.bounding_box()  # ✅ 45.2x18.7 (real dimensions!)
```

This is why the glyph library system works where text measurement fails.

### Font Licensing

When creating glyph libraries from commercial fonts:
- Ensure you have rights to embed/distribute font outlines
- Most system fonts (Arial, Helvetica, Times) are freely usable
- For commercial projects, verify font licenses
- Consider using open fonts (Liberation Sans, etc.)

## Next Steps

After creating your first library:
1. Verify SVG structure (text editor check)
2. Test with `glyph_library.py` loader
3. Use `positioning.py` utility for visual verification
4. Create additional libraries as needed
