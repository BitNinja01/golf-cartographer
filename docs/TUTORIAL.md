# Golf Cartographer Tutorial

## Complete Step-by-Step Guide to Creating Your Yardage Book

This tutorial walks you through creating a complete, print-ready golf yardage book from an OpenStreetMap SVG export. By following these steps, you'll transform raw OSM data into a professional 18-hole booklet in approximately 10-15 minutes.

---

## Before You Start: Prerequisites and Setup

### What You'll Need

1. **Inkscape 1.4.2 or later** - Download from [inkscape.org](https://inkscape.org)
2. **Golf Cartographer extensions installed** - See "Installation" below
3. **An OpenStreetMap SVG export** of your golf course - Download from [overpass-turbo.eu](https://overpass-turbo.eu)
4. **Course yardage information** - Hole numbers, pars, and tee box yardages for all 18 holes
5. **A printer capable of double-sided printing** (for final output)

### Installation

Before you can use Golf Cartographer, you need to install the extension files into Inkscape:

**Step 1: Locate your Inkscape extensions folder**

The location depends on your operating system:
- **Linux**: `~/.config/inkscape/extensions/`
- **macOS**: `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
- **Windows**: `%APPDATA%\inkscape\extensions\`

**Step 2: Copy Golf Cartographer files**

Copy all files from the `golf-cartographer/` folder into your extensions folder. You need both the `.inx` (metadata) and `.py` (code) files for each extension.

```bash
# Linux/macOS example:
cp -r golf-cartographer/* ~/.config/inkscape/extensions/
```

**Step 3: Restart Inkscape**

Close Inkscape completely and reopen it. Extensions are loaded at startup, not dynamically.

**Step 4: Verify installation**

Open Inkscape and look for `Extensions > Golf Cartographer` in the menu. You should see 5 numbered tools:
1. Flatten SVG
2. Group Hole
3. Auto-Place Holes and Scale Greens
4. Add Hole Label
5. Export PDFs

If you don't see these, check that both `.inx` and `.py` files were copied, and restart Inkscape again.

<!-- SCREENSHOT: CRITICAL - Installation Verification
     Show: Inkscape menu navigation: Extensions > Golf Cartographer with all 5 numbered tools visible in submenu
     Why: Users verify correct installation and see exact menu structure -->

### Document Setup

Before processing your OSM export, you must configure Inkscape's document units correctly.

**Step 1: Open your OSM SVG export in Inkscape**

The file will likely appear as a jumbled mess of colored elements with no clear organization. This is normal—that's what Stage 1 fixes.

**Step 2: Set document units to inches**

Go to `File > Document Properties` and look for the "Units" dropdown. Change it from the default (usually `px`) to `in` (inches). This is critical because Golf Cartographer uses inch-based positioning throughout.

<!-- SCREENSHOT: CRITICAL - Document Units Dialog
     Show: Inkscape's File > Document Properties dialog with Units dropdown clearly showing "in" (inches) selected
     Why: Critical prerequisite mentioned multiple times - shows exactly where and how to set this
     Prevents positioning failures -->

**Step 3: Save your document**

Save the file with a memorable name like `course_working.svg`. You'll be working with this file throughout all five stages.

---

## Stage 1: Flatten SVG

**What You'll Accomplish**

Your raw OSM export contains hundreds of ungrouped elements with inconsistent structure. Stage 1 organizes these elements into color-based groups (greens, fairways, bunkers, water, trees, paths) creating a foundation for the remaining stages.

**Expected Time**: 5-15 seconds

**Step-by-Step Instructions**

1. **Open your OSM SVG file in Inkscape** with document units already set to inches

2. **Run the Flatten SVG tool**
   - Go to `Extensions > Golf Cartographer > 1. Flatten SVG`
   - You'll see a progress message in Inkscape's notification area
   - The tool runs automatically with no dialog (takes 5-15 seconds)

3. **Wait for the process to complete**
   - Watch the Inkscape interface for the notification to clear
   - You may see brief UI updates as elements are processed

4. **Save your work**
   - Go to `File > Save` (Ctrl+S / Cmd+S)
   - Your document now has organized element groups

**What to Look For (Verification)**

After Stage 1 completes, open the Layers panel (`Object > Objects` or press Shift+Ctrl+O) and look for these organized groups:

- A `greens` group containing all green/putting surface elements
- A `fairways` group with fairway elements
- A `bunkers` group with sand bunker elements
- A `water` group with water hazard elements
- A `trees` group with tree/vegetation elements
- Other groups for paths and miscellaneous elements

Your elements should be visually organized in the layers panel hierarchy, even if the canvas still looks somewhat messy.

<!-- SCREENSHOT: CRITICAL - Stage 1 Before/After Comparison
     Show: Side-by-side showing raw OSM SVG (left) vs flattened organized groups (right) with layers panel visible showing group hierarchy
     Why: "Organized element groups by color" is abstract - visual proof shows transformation value
     Reference: examples/course_stage_1.svg with layers panel -->

**Common Issues**

| Problem | Solution |
|---------|----------|
| Tool doesn't appear in Extensions menu | Verify both `.inx` and `.py` files copied, restart Inkscape |
| "ImportError" message appears | Check all utility files present (transform_utils.py, geometry_utils.py, color_utils.py) |
| Elements not organized into groups | Your OSM export may use non-standard colors; see "Fixing Color Detection" in README |
| Progress is very slow (>30s) | Your OSM export may contain thousands of elements; this is normal for large courses |

---

## Stage 2: Group Hole (Run This 18 Times—Once Per Hole)

**What You'll Accomplish**

You'll organize elements for each individual hole into hierarchical groups. This separates terrain elements (the hole layout) from green elements (the putting surface), creating the foundation for positioning in Stage 3.

**Expected Time**: 3-8 seconds per hole (1-2 minutes total for all 18)

### Before You Start: Preparing Your Work

You need to process all 18 holes. For each hole, you'll:
1. Select all elements belonging to that hole (terrain, green, bunkers, water, trees)
2. Run the Group Hole tool
3. Enter the hole number in a dialog

**Preparing hole selection is the most time-consuming part of this stage.** Consider using Inkscape's color selection tools to help identify which elements belong to each hole.

### Step-by-Step for Each Hole (Repeat 18 Times)

**Step 1: Identify and select all elements for hole 1**

In Inkscape, use the selection tool (press 's') to select all elements that belong to your first hole. This typically includes:
- The hole outline/fairway shape
- The green/putting surface
- Any bunkers near the hole
- Water hazards
- Trees and vegetation
- Paths leading to the green

Tip: Use `Edit > Select All` (Ctrl+A) and then deselect elements you don't want. Or use the "Select by Color" tool to quickly grab elements of similar colors.

<!-- SCREENSHOT: CRITICAL - Hole Selection & Dialog
     Show: Inkscape with hole elements selected (highlighted in blue) + Group Hole dialog with hole number input field visible
     Why: "Select all elements belonging to that hole" is ambiguous - shows what proper selection looks like
     Reference: examples/course_stage_2.svg with a hole selected -->

**Step 2: Run the Group Hole tool**

- Go to `Extensions > Golf Cartographer > 2. Group Hole`
- A dialog appears asking for the hole number (1-18)

**Step 3: Enter the hole number**

- In the dialog, enter the hole number (1 for your first hole)
- Click OK or press Enter
- The tool runs for 3-8 seconds

**Step 4: Verify the grouping**

- Open the Layers panel
- Look for a new group named `hole_01` (or whatever number you entered)
- Inside this group, you should see:
  - A `terrain` subgroup containing the hole outline, fairways, trees, water, etc.
  - A `green` subgroup containing the putting surface elements

<!-- SCREENSHOT: HIGH - Hole Grouping Layers Panel
     Show: Inkscape layers panel showing properly grouped hole (hole_01 with terrain/green subelements in clear hierarchy)
     Why: Shows actual layer structure users should verify after Stage 2
     Reference: examples/course_stage_2.svg layers panel zoomed on single hole -->

**Step 5: Save your work**

- Press Ctrl+S / Cmd+S to save
- This preserves your grouping structure

**Step 6: Repeat for holes 2-18**

- Select elements for hole 2
- Run Group Hole tool
- Enter "2" in the dialog
- Verify the `hole_02` group appears in Layers panel
- Save
- Continue this process for all remaining holes through hole 18

**Verification Checklist**

When you've completed all 18 holes, your Layers panel should show:

```
hole_01
  ├── terrain
  └── green
hole_02
  ├── terrain
  └── green
... (repeating structure)
hole_18
  ├── terrain
  └── green
```

If any holes are missing or improperly grouped, repeat that hole's Group Hole step.

**Common Issues**

| Problem | Solution |
|---------|----------|
| Dialog doesn't appear | Ensure elements are selected before running the tool |
| Wrong elements grouped together | You may have selected elements from multiple holes; deselect and try again |
| hole_01 group created but structure is wrong | The tool expects both terrain and green elements; verify you selected both types |
| Some holes missing | It's easy to miss a hole when processing 18—refer to your hole list and run Group Hole for missing ones |
| Elements grouped into wrong hole numbers | Delete the incorrectly numbered group and rerun the tool with the correct number |

**Performance Note**

Processing all 18 holes takes 1-2 minutes total. If you need to verify your work, open one of the example files to see what a properly grouped document looks like:
- `examples/course_stage_2.svg` shows all 18 holes properly grouped

---

## Stage 3: Auto-Place Holes and Scale Greens

**What You'll Accomplish**

Stage 3 is where the magic happens. The tool automatically:
- Positions all 18 holes in a "top" area (3.736" wide × 6.756" tall)
- Rotates each hole to face its green optimally
- Extracts green details and scales them to fit a "bottom" area (3.75" × 3.75")
- Applies appropriate margins (10% around holes, 20% around green details)

After this stage, your document transforms from a messy collection of elements into a structured layout ready for labeling and PDF export.

**Expected Time**: 30-60 seconds

**Step-by-Step Instructions**

1. **Ensure all 18 holes are properly grouped**

   Before running Stage 3, verify that your document has all 18 holes grouped (from Stage 2). Open the Layers panel and confirm you see `hole_01` through `hole_18`, each with `terrain` and `green` subgroups.

2. **Run the Auto-Place Holes and Scale Greens tool**

   - Go to `Extensions > Golf Cartographer > 3. Auto-Place Holes and Scale Greens`
   - No dialog appears—the tool runs automatically
   - Processing takes 30-60 seconds; you'll see status updates in Inkscape

3. **Wait for completion**

   - You may see brief visual updates as holes are positioned and scaled
   - When complete, you'll see a notification that the process finished

4. **Examine the results**

   - Zoom out to see your entire document
   - You should now see a clear division:
     - A "top" area with all 18 holes positioned in a grid/organized layout
     - A "bottom" area with green details scaled down for reference

5. **Save your work**

   - Press Ctrl+S / Cmd+S to save

<!-- SCREENSHOT: CRITICAL - Stage 3 Output
     Show: Inkscape canvas after Stage 3 with holes positioned in "top" area and greens scaled in "bottom" area with visible page boundaries and clear division between sections
     Why: Complex transformation hard to visualize - shows actual layout positioning and top/bottom division
     Reference: examples/course_stage_3_c.svg with page boundaries visible -->

**What to Look For (Verification)**

After Stage 3 completes:

- **Top area (hole layouts)**: You should see all 18 hole outlines and terrain neatly positioned, typically in a grid pattern or organized layout
- **Bottom area (green details)**: Below the holes, you should see scaled-down versions of each green
- **Page structure**: Your document should have clear visual divisions showing where pages will break when exporting

If holes overlap, are positioned outside the page boundaries, or greens are not scaled, check the Common Issues section below.

**Common Issues**

| Problem | Solution |
|---------|----------|
| Holes don't appear positioned correctly | Verify all 18 holes are grouped in Stage 2; run Stage 2 again for any missing holes |
| Greens are missing or too small | Ensure `green` subgroups exist inside each `hole_XX` group |
| Elements positioned way off the page | Verify document units are set to inches (File > Document Properties > Units = "in") |
| Holes overlap each other | The tool may need more space; verify your document is large enough for 18 holes |
| Tool takes longer than 60 seconds | This is normal for complex OSM exports; wait for it to complete |

**Understanding the Layout**

Golf Cartographer arranges holes in a specific pattern designed for printing:

- **Top area (3.736" × 6.756")**: Contains all 18 hole layouts arranged vertically or in a grid
- **Bottom area (3.75" × 3.75")**: Contains scaled green details for reference while reading the hole

This layout is optimized for the 4.25" × 14" page size used for narrow PDF pages in Stage 5.

**Advanced: Customizing Hole Positioning**

If you need custom hole positioning (for example, if your course has unusual dimensions or you want different margins), you can edit `auto_place_holes.py`:

```python
# Top area (hole layouts)
BOUNDING_BOX = {
    'x': 0.257,      # Left margin in inches
    'y': 0.247,      # Top margin in inches
    'width': 3.736,  # Hole layout width in inches
    'height': 6.756  # Hole layout height in inches
}
EDGE_BUFFER = 0.90  # Use 90% of box (10% margin)

# Bottom area (green details)
TARGET_BOX = {
    'x': 0.250,      # Left margin in inches
    'y': 7.000,      # Start position in inches
    'width': 3.750,  # Green detail width in inches
    'height': 3.750  # Green detail height in inches
}
GREEN_EDGE_BUFFER = 0.80  # Use 80% of box (20% margin)
```

After editing, restart Inkscape and run Stage 3 again.

---

## Stage 4: Add Hole Label (Run This 18 Times—Once Per Hole)

**What You'll Accomplish**

You'll add professional hole labels with:
- Hole number in a circle
- Par value (3, 4, 5, or 6)
- Tee box names and yardages (up to 6 different tee boxes)

These labels appear on each hole's layout in the top area, providing essential course information at a glance.

**Expected Time**: 3-5 seconds per hole (1-2 minutes total for all 18)

### Before You Start: Gathering Course Information

You'll need the following information for each of your 18 holes:

1. **Hole number** (1-18)
2. **Par value** (typically 3, 4, or 5; sometimes 6)
3. **Tee box names and yardages**, such as:
   - Championship: 425 yards
   - Men's: 395 yards
   - Senior: 360 yards
   - Women's: 320 yards

Create a simple list or spreadsheet with this information before you start. For example:

```
Hole 1: Par 4
  - Championship: 425
  - Men's: 395
  - Senior: 360
  - Women's: 320

Hole 2: Par 3
  - Championship: 175
  - Men's: 155
  - Senior: 140
  - Women's: 120
```

### Step-by-Step for Each Hole (Repeat 18 Times)

**Step 1: Run the Add Hole Label tool**

- Go to `Extensions > Golf Cartographer > 4. Add Hole Label`
- A dialog appears with input fields

**Step 2: Enter the hole number**

- In the "Hole Number" field, enter 1 (for your first hole)
- The tool uses this to find the correct `hole_01` group

**Step 3: Enter the par value**

- In the "Par" field, enter the par for this hole (3, 4, 5, or 6)
- This value appears next to the hole number in the label

**Step 4: Enter tee box names and yardages**

The dialog has fields for up to 6 tee boxes:
- **Tee Box 1 Name** (e.g., "Championship")
- **Tee Box 1 Yardage** (e.g., "425")
- **Tee Box 2 Name** (e.g., "Men's")
- **Tee Box 2 Yardage** (e.g., "395")
- And so on...

Only fill in fields for tee boxes your course actually uses. Leave blank fields empty.

<!-- SCREENSHOT: CRITICAL - Add Hole Label Dialog
     Show: Add Hole Label dialog showing all input fields (hole number, par, tee box names, yardages) with example data filled in
     Why: Users need to know what information to prepare before running this stage -->

**Step 5: (Optional) Customize fonts**

The dialog also includes optional font customization:
- **Number Font**: Font for the hole number (e.g., "Sans Bold")
- **Par Font**: Font for the par text
- **Yardage Font**: Font for the tee box yardages

Leave these as default unless you have specific preferences. The defaults work well for printing.

**Step 6: Click OK**

- Click the OK button or press Enter
- The tool runs for 3-5 seconds

**Step 7: Verify the label was added**

- Look at the hole in the top area of your document
- You should see a new label with:
  - A circle with the hole number inside
  - The par value displayed prominently
  - The tee box names and yardages listed below

<!-- SCREENSHOT: HIGH - Hole Label Result
     Show: Close-up of a finished hole label showing circle, hole number in center, par value, and tee box yardages below
     Why: Users verify Stage 4 worked correctly by seeing expected visual result
     Reference: examples/course_stage_4.svg zoomed in on a hole label -->

**Step 8: Save your work**

- Press Ctrl+S / Cmd+S to save

**Step 9: Repeat for holes 2-18**

- For hole 2: Run Add Hole Label, enter "2" as hole number, enter par and tee yardages, click OK
- Verify the label appears in hole 2's layout
- Save
- Continue for all holes through 18

**Tips for Efficient Labeling**

- **Use standard yardage values**: Most courses follow a standard set of tee boxes (Championship, Men's, Senior, Women's). Use the same names for all 18 holes for consistency
- **Copy/paste yardages**: If your tee box yardages don't change much from hole to hole, you can copy typical values and modify slightly
- **Verify as you go**: After adding each label, take a quick look to ensure it appears in the correct hole
- **Save frequently**: Save after every few holes to avoid losing work

**Common Issues**

| Problem | Solution |
|---------|----------|
| Dialog doesn't appear | The tool always shows a dialog; if you don't see it, restart Inkscape |
| Label appears in wrong hole | Verify you entered the correct hole number (1-18, not 01-18) |
| Label doesn't appear at all | Ensure the `hole_XX` group exists from Stage 2; run Stage 2 for that hole if missing |
| Text is too large or too small | Customize font sizes in the dialog (higher font sizes = larger text) |
| Tee box names look wrong | Verify spelling in the dialog; the text appears exactly as you type it |
| Some holes are skipped | It's easy to skip a hole when labeling 18; keep a checklist and verify all are labeled |

**Verification Checklist**

When you've completed all 18 holes, verify:

- [ ] Each hole (1-18) has a visible label in the top area
- [ ] Each label includes the hole number, par, and at least one tee box yardage
- [ ] All labels are formatted consistently (same fonts, similar sizes)
- [ ] No labels overlap with hole terrain or other labels
- [ ] Document saved with all labels intact

---

## Stage 5: Export PDFs

**What You'll Accomplish**

Stage 5 generates your complete yardage book through a three-step automated process:

1. **Export 20 narrow PDFs** (4.25" × 14" each) with strategic hole/green pairings
2. **Combine pairs into 10 wide PDFs** (8.5" × 14" each)
3. **Create 5 booklet PDFs** (2 pages each) ready for saddle-stitch printing

After Stage 5, you'll have print-ready PDFs that just need to be printed, assembled, and stapled.

**Expected Time**: 2-5 minutes total

**Step-by-Step Instructions**

**Step 1: Run the Export PDFs tool**

- Go to `Extensions > Golf Cartographer > 5. Export PDFs`
- A dialog appears with three settings

<!-- SCREENSHOT: HIGH - Export PDFs Dialog
     Show: Export PDFs dialog showing three input fields (Output Directory, Filename Prefix, Combine into Booklets checkbox) with default values visible
     Why: Users need to know what parameters to set before running the longest stage -->

**Step 2: Set the output directory**

- The "Output Directory" field specifies where PDFs will be saved
- Default is your Desktop (`~/Desktop` or equivalent)
- Change this if you prefer a different location (e.g., a Documents folder)
- Click the folder icon to browse and select a directory

**Step 3: Set the filename prefix**

- The "Filename Prefix" field determines how PDFs are named
- Default is `yardage_book_`
- Your PDFs will be named `yardage_book_9_9.pdf`, `yardage_book_8_10.pdf`, etc.
- You can change this to something custom like `my_course_` if desired

**Step 4: Enable booklet combination**

- Leave the "Combine into Booklets" checkbox checked (default)
- This creates the 5 saddle-stitch booklet PDFs
- If you only want the 20 individual narrow PDFs, uncheck this (not recommended for printing)

**Step 5: Click OK**

- Click the OK button
- The tool begins processing; this takes 2-5 minutes
- You'll see status messages in Inkscape as PDFs are exported and combined

**Step 6: Wait for completion**

- PDFs are being exported to your specified directory
- Processing large SVGs can take several minutes; be patient
- When complete, you'll see a notification

**Step 7: Verify the output**

- Open your specified output directory (Desktop by default)
- You should see multiple PDF files:
  - 20 narrow PDFs (if "Combine into Booklets" was checked): `yardage_book_9_9.pdf` through `yardage_book_back_cover.pdf`
  - 10 wide PDFs (if combined): `yardage_book_wide_1.pdf` through `yardage_book_wide_10.pdf`
  - 5 booklet PDFs (if combined): `yardage_book_01.pdf` through `yardage_book_05.pdf`

- Click on one of the booklet PDFs to preview
- You should see a professional-looking page with a hole layout on one side and a green detail on the other

**What to Look For (Verification)**

After PDF export completes:

- **Booklet PDFs exist**: You should see 5 files named `yardage_book_01.pdf` through `yardage_book_05.pdf`
- **PDFs are non-zero size**: Each booklet should be several hundred kilobytes
- **PDFs contain visible content**: Open one and verify you see hole layouts and green details
- **Pages are properly formatted**: Each page should show a hole layout on the left and a green detail on the right

If you don't see the booklet files, check the Common Issues section.

**Common Issues**

| Problem | Solution |
|---------|----------|
| Dialog doesn't appear | Ensure all 18 holes are labeled from Stage 4 |
| "ImportError" when exporting | Verify all utility files are present and Python 3.7+ is available |
| PDFs fail to generate | Check that output directory exists and is writable; try using Desktop |
| Only 20 narrow PDFs appear, not booklets | "Combine into Booklets" may have been unchecked; rerun Stage 5 with it checked |
| PDFs are blank or show wrong content | Ensure holes are properly positioned from Stage 3 and labeled from Stage 4 |
| Export takes more than 5 minutes | This is normal for large, complex SVG files; wait for it to complete |
| File permissions error | Ensure you have write permissions to the output directory |

**Understanding the PDF Output**

### The 20 Narrow PDFs (4.25" × 14" each)

Golf Cartographer uses a strategic pairing system where each hole layout is paired with a different hole's green detail. This provides mid-round reference for greens at other holes on the course.

The 20 narrow PDFs are:

```
Pages 1-10 (Front nine + transition):
1. Hole 9 layout + Green 9
2. Hole 8 layout + Green 10
3. Hole 7 layout + Green 11
4. Hole 6 layout + Green 12
5. Hole 5 layout + Green 13
6. Hole 4 layout + Green 14
7. Hole 3 layout + Green 15
8. Hole 2 layout + Green 16
9. Hole 1 layout + Green 17
10. Scorecard + Green 18

Pages 11-20 (Back nine):
11. Hole 10 layout + Green 8
12. Hole 11 layout + Green 7
13. Hole 12 layout + Green 6
14. Hole 13 layout + Green 5
15. Hole 14 layout + Green 4
16. Hole 15 layout + Green 3
17. Hole 16 layout + Green 2
18. Hole 17 layout + Green 1
19. Hole 18 layout + Notes
20. Back cover
```

### The 10 Wide PDFs (8.5" × 14" each)

These combine pairs of narrow PDFs side-by-side:

```
Wide Page 1: Narrow 1 + Narrow 2
Wide Page 2: Narrow 3 + Narrow 4
... (continuing in pairs)
Wide Page 10: Narrow 19 + Narrow 20
```

### The 5 Booklet PDFs (Final Output)

These are pre-formatted for saddle-stitch printing (folding and stapling):

```
yardage_book_01.pdf: Wide pages 1 + 2 (innermost sheet)
yardage_book_02.pdf: Wide pages 3 + 4
yardage_book_03.pdf: Wide pages 5 + 6 (middle sheet)
yardage_book_04.pdf: Wide pages 7 + 8
yardage_book_05.pdf: Wide pages 9 + 10 (outermost sheet)
```

---

## Final Steps: Printing and Assembly

You now have 5 PDF booklets ready to print. Here's how to assemble them into a professional yardage book.

### Print Instructions

**Step 1: Print each booklet**

- Open `yardage_book_01.pdf` in your PDF reader (Preview, Adobe Reader, etc.)
- Go to Print settings
- Enable "Double-sided printing" and set to flip on the short edge
- Print to your printer (color printing is recommended for terrain and greens visibility)
- Repeat for `yardage_book_02.pdf`, `yardage_book_03.pdf`, `yardage_book_04.pdf`, and `yardage_book_05.pdf`

<!-- SCREENSHOT: HIGH - Booklet Assembly Diagram
     Show: Illustration showing physical assembly steps - 5 booklets stacked with 05 labeled on outside, 01 on inside, then folding and stapling along center
     Why: Saddle-stitch printing instructions hard to visualize - reduces printing errors and wasted paper -->

**Step 2: Prepare for assembly**

When all 5 booklets are printed, you'll have:
- Booklet 01 (innermost, should be in the middle)
- Booklet 02
- Booklet 03 (center booklet)
- Booklet 04
- Booklet 05 (outermost, should be on the outside)

**Step 3: Stack the booklets**

- Start with Booklet 05 as the bottom (outside cover)
- Stack Booklet 04 on top
- Stack Booklet 03 (middle booklet)
- Stack Booklet 02
- Stack Booklet 01 on top (inside)

This creates a nested stack with Booklet 05's cover on the outside and Booklet 01's pages at the center.

**Step 4: Fold in half**

- Hold the entire stack
- Fold the stack in half along the center
- Align all edges carefully

**Step 5: Staple along the center**

- Use a saddle-stitch stapler (industrial stapler) if available, or a regular stapler
- Open the folded booklet to reveal the center spine
- Staple 2-3 times along the center spine, spacing staples evenly from top to bottom

**Result**

You now have a complete, professional golf yardage book with:
- 20 pages (front and back)
- Hole layouts on the front of each page
- Green details and scoring areas on the back
- All hole numbers, pars, and tee box yardages included
- Professional layout optimized for in-round use

### Using Your Yardage Book

Your finished yardage book is designed for golfers to:
1. Look at the hole layout at the start of each hole
2. Understand the hole's features (greens, bunkers, water, trees)
3. Reference tee yardages to select the right club
4. Flip to see the green detail for shot planning
5. Use the scoring grid to track strokes

---

## Troubleshooting Common Problems

### Installation Issues

**Extensions don't appear in Extensions menu**

- Verify both `.inx` and `.py` files are in your extensions folder
- Check folder path is correct for your operating system
- Restart Inkscape completely (don't just close and reopen a window)
- Check Inkscape version is 1.4.2 or later (Help > About Inkscape)

**"ImportError: No module named..." appears when running a tool**

- Ensure all utility files are present:
  - `transform_utils.py`
  - `geometry_utils.py`
  - `color_utils.py`
  - `glyph_library.py` (if using Stage 4)
- All files must be in the same folder as the extension `.py` files

**Python errors when running tools**

- Verify Python 3.7+ is available (check with `python --version`)
- Close and restart Inkscape
- Try running the tool again

### Document Structure Issues

**Document units are wrong causing positioning errors**

- Go to File > Document Properties
- Find the "Units" dropdown
- Change from `px` to `in` (inches)
- Save your document
- Rerun the stage that failed

**Elements positioned way off the page**

- Verify document units are set to inches
- Check that all holes were properly grouped in Stage 2
- Zoom out to see entire document (View > Zoom > Fit Page in Window)

**Holes appear to overlap or are positioned incorrectly**

- Verify all holes were grouped in Stage 2 with both terrain and green elements
- Check that Stage 3 completed successfully (no error messages)
- Ensure your course is not larger than the template allows (very large courses may need custom positioning)

### Stage-Specific Issues

**Stage 1: Elements not organized into groups**

- OSM export may use non-standard colors
- Edit `color_utils.py` to adjust color detection thresholds
- Alternatively, manually organize elements by color in Inkscape and run Stage 1 again

**Stage 2: Selected elements don't group properly**

- Ensure both terrain AND green elements are selected
- Verify you're selecting elements from only one hole
- Run the tool again with correct selection

**Stage 3: Holes don't position correctly**

- Verify all 18 holes are grouped from Stage 2
- Check document units are in inches
- Ensure no holes are locked (right-click hole group > unlock)

**Stage 4: Labels don't appear**

- Verify hole groups exist from Stage 2 (check Layers panel)
- Ensure hole number entered in dialog matches the hole_XX group name
- Verify you entered a valid par (3, 4, 5, or 6)

**Stage 5: PDF export fails or hangs**

- Ensure all 18 holes are labeled from Stage 4
- Verify output directory exists and is writable
- Try saving to Desktop first, then a different location
- Wait 5+ minutes for processing to complete (complex SVGs can be slow)
- Check Inkscape error console (Help > Show/Print System Console)

### Performance Issues

**A stage is running very slowly**

- This is normal for large, complex OSM exports with thousands of elements
- Wait for the stage to complete (can take 5+ minutes for very large courses)
- Consider simplifying your SVG by removing unnecessary elements before importing

**Computer becomes unresponsive during export**

- This is normal during Stage 5 PDF export
- Don't force quit; wait for the process to complete
- Close other applications to free up memory

---

## Tips and Best Practices

### Before You Start

1. **Prepare your course information** - Gather all hole numbers, pars, and tee yardages before starting
2. **Test with an example** - Use `examples/course_stage_5.svg` to understand the workflow before your own course
3. **Back up your files** - Save copies of your SVG at each stage
4. **Use consistent naming** - Use the same tee box names for all 18 holes

### During Processing

1. **Take breaks between stages** - Process one stage, save, take a break, then start the next
2. **Verify each stage** - Check that each stage produced expected results before moving to the next
3. **Save frequently** - Save after each hole in Stages 2 and 4 to avoid losing work
4. **Don't edit during processing** - Don't make changes to your SVG while a stage is running

### Quality Assurance

1. **Compare to examples** - Open the corresponding example file to see what proper output looks like
2. **Check layer structure** - Use the Layers panel to verify groups and subgroups are created correctly
3. **Print a test page** - Before printing all 5 booklets, print a single page from yardage_book_01.pdf and verify quality
4. **Review hole labels** - Before stage 5, zoom in on several holes and verify labels are legible and positioned well

### Customization

1. **Adjust hole positioning** - Edit BOUNDING_BOX values in `auto_place_holes.py` if needed
2. **Customize fonts** - Use the dialog in Stage 4 to select fonts that match your course branding
3. **Change PDF names** - Use the Filename Prefix in Stage 5 to create custom PDF names
4. **Modify colors** - Edit `color_utils.py` if your OSM export uses non-standard colors

---

## Frequently Asked Questions

**Q: How long does the complete workflow take?**
A: Typically 10-15 minutes, depending on your course size and computer speed. Stages 2 and 4 require manual work (selecting elements, entering data), while other stages are automated.

**Q: Can I edit the yardage book after exporting PDFs?**
A: Yes! Your SVG file remains editable. You can make changes and re-export. Use File > Revert to get back to your last saved version if you make unwanted changes.

**Q: What if I make a mistake in a hole label?**
A: Run Stage 4 again for that hole with the correct information. The new label will replace the old one.

**Q: Can I use a different page size?**
A: Yes, but it requires editing the positioning code in `auto_place_holes.py`. The default is optimized for 8.5" × 11" (letter) or A4 paper.

**Q: How do I handle a par 6 hole?**
A: Enter "6" in the Par field during Stage 4. The tool supports pars from 3-6.

**Q: Can I add more than 6 tee boxes?**
A: The dialog supports up to 6 tee boxes. If your course has more, use the most popular tees and note additional ones manually on the printed booklet.

**Q: What if my OSM export has errors or missing data?**
A: Edit the SVG in Inkscape to fix errors before running Stage 1. You can add missing elements or adjust colors to match OSM standards.

**Q: Can I create a yardage book for just 9 holes?**
A: Yes, but the tool is designed for 18. Run Stages 1-3 normally, then in Stages 2 and 4, only process your 9 holes. Stage 5 will export fewer pages.

**Q: How large can an OSM export be?**
A: Golf Cartographer handles courses with thousands of elements. Very large, complex courses may take longer to process, but will still work.

---

## Next Steps

Congratulations! You've created a professional golf yardage book. Here are some ideas for next steps:

1. **Distribute your yardage book** - Share PDFs with golfers at your course
2. **Get feedback** - Ask golfers if labels are clear and positioning is useful
3. **Create variant editions** - Export multiple versions with different tee box combinations
4. **Document your course** - Keep your SVG file for future updates when the course changes
5. **Explore enhancements** - Check [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md) for upcoming features

---

## Getting Help

If you encounter issues not covered here:

1. **Check the README.md** - Contains detailed reference information about each tool
2. **Review example files** - `examples/course_stage_X.svg` show what proper output looks like at each stage
3. **Consult FUTURE_ENHANCEMENTS.md** - Details upcoming features and known limitations
4. **Examine source code** - Each extension's `.py` file contains detailed comments explaining the logic

---

## File Reference

Key files you'll work with:

| File | Purpose |
|------|---------|
| `flatten_svg.inx / .py` | Stage 1 - Organizes elements by color |
| `group_hole.inx / .py` | Stage 2 - Creates hole groups (run 18 times) |
| `auto_place_holes.inx / .py` | Stage 3 - Positions holes and scales greens |
| `add_hole_label.inx / .py` | Stage 4 - Adds hole labels (run 18 times) |
| `export_pdfs.inx / .py` | Stage 5 - Exports PDF booklets |
| `examples/course_stage_X.svg` | Example output at each stage (X = 1-5) |
| `examples/exported_pdfs/` | Sample PDF pages showing final output |

---

## Document Revision History

**Version 1.0** - Initial tutorial for Golf Cartographer v1.0
- Complete five-stage workflow
- Step-by-step instructions for all 18 holes
- Screenshots markers for visual reference
- Troubleshooting and FAQ sections
