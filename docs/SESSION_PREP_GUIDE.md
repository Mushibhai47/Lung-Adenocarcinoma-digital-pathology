# COMPLETE SESSION PREP GUIDE
## Everything Musharaf Needs To Do Before Wednesday Feb 12

---

# PART 1: SETUP (Do This TODAY — Feb 9-10)

---

## Step 1: Install QuPath

1. Go to: https://qupath.github.io/
2. Click **Download** → Choose **Windows** → Download the `.msi` installer
3. Run the installer, install to default location
4. Launch QuPath
5. **IMPORTANT — Set Memory:**
   - Edit → Preferences → scroll to "Memory"
   - Set to **8GB minimum** (16GB if your PC has 32GB RAM)
   - Restart QuPath after changing memory

**Verify it works:** You should see the QuPath window with a dark toolbar and empty viewer.

---

## Step 2: Download Vania's Sample Slides

1. Open this link in browser:
   https://drive.google.com/drive/folders/1E90nESMFlEfaSX2Vaz4tm_44G9tyVA2U?usp=sharing
2. Download ALL 5 files
3. Save them to: `C:\Users\musha\Desktop\QuPath\slides\`
4. Note the file format (.svs, .ndpi, .mrxs, .tiff, etc.)

**File sizes:** Whole slide images are typically 500MB–3GB each. Make sure you have enough disk space (~15-20GB free).

---

## Step 3: Create a QuPath Project & Load Slides

1. Open QuPath
2. **File → Project → Create project**
3. Navigate to: `C:\Users\musha\Desktop\QuPath\project\`
4. Click "Select Folder" (or "Open")
5. QuPath creates `project.qpproj` inside that folder
6. **Add slides to project:**
   - File → Project → Add images
   - Navigate to `slides/` folder
   - Select ALL 5 files → Open
   - Import type: leave as "Image server" (auto-detect)
   - Click "Import"
7. You should now see 5 thumbnails in the left "Project" panel

**Verify:** Double-click any thumbnail → the slide should open in the viewer.

---

# PART 2: LEARN THE BASICS (Do This Feb 10-11)

---

## Step 4: Navigation — Practice These Until They're Muscle Memory

Open any slide and practice:

| Action | How | Practice |
|--------|-----|----------|
| **Zoom in** | Scroll wheel UP | Zoom into a tissue region |
| **Zoom out** | Scroll wheel DOWN | Zoom out to see full slide |
| **Pan** | Click + drag | Move around the tissue |
| **Fit to screen** | Shift+F or double-click thumbnail | Reset view |
| **Toggle annotations** | Press `A` | Show/hide annotations |
| **Toggle detections** | Press `D` | Show/hide cell detections |
| **Toggle fill** | Shift+F | Fill annotations with color |
| **Brightness/Contrast** | Shift+C | Adjust if slide is too dark/light |
| **Show measurement table** | Ctrl+Shift+S | View measurements |

**Spend 10 minutes** just zooming, panning, and exploring a slide. Get comfortable.

---

## Step 5: Understand What You're Looking At (H&E Basics)

H&E staining produces TWO colors:

### Hematoxylin (BLUE/PURPLE)
- Stains **nuclei** (cell centers)
- Lymphocytes appear as **small, very dark blue dots**
- Tumor nuclei tend to be **larger, irregular, darker**

### Eosin (PINK)
- Stains **cytoplasm and connective tissue**
- Stroma appears as **pink fibrous tissue** between cell clusters
- Blood vessels have pink walls

### What Tumor vs Stroma Looks Like:

**TUMOR regions:**
- Dense clusters of cells with large, dark, irregular nuclei
- Cells packed tightly together
- Less pink stroma between cells
- Often form gland-like structures (if adenocarcinoma) or solid nests
- "Busy" looking — lots of blue/purple nuclei

**STROMA regions:**
- Pink fibrous connective tissue
- Fewer scattered cells (fibroblasts, immune cells)
- More "open" appearance with visible extracellular matrix
- Can contain blood vessels, inflammatory infiltrates
- "Quieter" looking — more pink, fewer nuclei

**BACKGROUND:**
- White/empty glass areas with no tissue
- Edges of tissue sections
- Folds or torn areas (mark as Ignore*)

### Lymphocytes (What We're Counting):
- **Very small** cells (6-10 µm diameter)
- **Round** — nearly perfect circles
- **Dark blue** — intense hematoxylin staining
- **Minimal cytoplasm** — almost all nucleus
- Found in both tumor and stroma, sometimes in clusters
- They look like small dark blue dots scattered among larger cells

**IMPORTANT:** You don't need to be a pathologist. Vania and her resident will define the criteria. You just need to recognize the general patterns well enough to assist them.

---

## Step 6: Practice Annotation Tools

### 6a. Setup Classes First

1. Open a slide in QuPath
2. Go to: **Automate → Show script editor**
3. Open file: `C:\Users\musha\Desktop\QuPath\scripts\01_setup_classes.groovy`
4. Click **Run**
5. Close script editor

Now in the **Annotations** tab (left panel), you should see class options.

### 6b. Practice with Brush Tool (PRIMARY TOOL)

1. Press `B` to select Brush tool
2. In the Annotations tab, select "Tumor" class (or set class after drawing)
3. **Draw:** Hold left mouse button and paint over a tumor region
4. **Adjust brush size:** Press `[` to shrink, `]` to enlarge
5. **Erase within annotation:** Hold `Alt` + paint to subtract from annotation
6. **Finish:** Release mouse → annotation is created
7. **Set/Change class:** Right-click annotation → Set class → choose Tumor/Stroma

**Practice drawing 5 Tumor regions and 5 Stroma regions.**

### 6c. Practice with Polygon Tool

1. Press `P` to select Polygon tool
2. Click to place vertices around a region
3. Double-click to close the polygon
4. Right-click → Set class

### 6d. Practice with Wand Tool

1. Press `W` to select Wand tool
2. Click inside a region — it auto-detects boundaries
3. Adjust sensitivity with `[` and `]`
4. Good for well-defined tissue boundaries

### 6e. Managing Annotations

| Action | How |
|--------|-----|
| Select annotation | Click on it with Move tool (M) |
| Delete annotation | Select → press Delete key |
| Lock annotation | Right-click → Lock (prevents accidental edits) |
| Change class | Right-click → Set class |
| See all annotations | View → Annotation list (or check left panel) |
| Merge annotations | Select multiple (Ctrl+click) → right-click → Merge |

---

## Step 7: Run a Test Cell Detection

After creating some practice annotations:

1. Select a Tumor or Stroma annotation (click on it)
2. Go to: **Analyze → Cell detection**
3. Use these settings:
   - Detection image: **Hematoxylin**
   - Requested pixel size: **0.5 µm**
   - Background radius: **8 µm**
   - Threshold: **0.15** (adjust if too many/few detections)
   - Min area: **10 µm²**
   - Max area: **400 µm²**
   - Split by shape: **checked**
   - Cell expansion: **5 µm**
4. Click **Run**
5. Press `D` to toggle detections on/off
6. Zoom in to see detected cells — each should have a colored boundary

**What to look for:**
- Are most nuclei detected? (if many missed → lower threshold)
- Are there false detections in empty areas? (if yes → raise threshold)
- Are touching nuclei separated? (split by shape should handle this)

---

## Step 8: Practice the Pixel Classifier (Interactive)

1. Go to: **Classify → Pixel classification → Train pixel classifier**
2. Settings:
   - Classifier: **Random Trees**
   - Resolution: **20 µm/px** (start coarse for speed, refine to 10 later)
   - Features: Check ALL boxes
   - Scales: **1, 2, 4, 8**
   - Region: **Annotations**
   - Output: **Classification**
3. Click **Live preview**
4. The entire slide gets colored — red for Tumor, green for Stroma
5. **Evaluate:** Zoom into different areas
   - Does the classification match what you see?
   - Are boundaries reasonable?
6. If bad: add more annotations, click **Live preview** again
7. When satisfied: **Save** → name it `tumor_stroma_v1`

---

# PART 3: SESSION DAY CHECKLIST (Feb 12)

---

## 1 Hour Before Session:

- [ ] QuPath is open with the project loaded
- [ ] All 5 slides visible in project panel
- [ ] One slide already open in the viewer
- [ ] Script editor ready (Automate → Show script editor)
- [ ] Classes are set up (Tumor, Stroma, Background, Lymphocyte)
- [ ] Google Meet link created and shared with Vania
- [ ] Screen sharing tested
- [ ] Stable internet connection
- [ ] Second monitor if available (one for QuPath, one for video call)

## During Session — Flow:

### Opening (5 min)
- Greet Vania and the resident
- "I've set up the project with your 5 sample slides. Let me walk you through the interface first."

### Navigation Demo (10 min)
- Share screen showing QuPath
- Demo zoom, pan, fit-to-screen
- Show overview panel (small map in corner)
- Show how to switch between slides in the project panel
- "Now you try — open one of the slides on your QuPath"

### H&E Orientation (10 min)
- Ask Vania: "Can you point out a typical tumor region and a stroma region?"
- This is where HER expertise matters — she defines the criteria
- Take notes on what she says (you'll use this for classifier training)
- Ask: "Are there any edge cases or difficult areas I should be aware of?"

### Annotation Demo (15 min)
- Demo the Brush tool on a tumor region
- Demo changing brush size
- Demo setting the class
- Demo the Polygon tool for larger regions
- Show how to delete/undo mistakes
- "Let me show you what a good annotation looks like vs a bad one"

### Resident Practices (30 min)
- Hand control to the resident (she shares her screen or you guide verbally)
- She draws annotations while you guide:
  - "That's a good tumor region, nice and clean"
  - "Try to avoid including stroma at the edges"
  - "Now do a stroma region — pick an area with clear fibrous tissue"
  - "Good — now try one more from a different part of the slide"
- Goal: 5+ annotations per class on one slide

### Review & Next Steps (10 min)
- Review all annotations together
- Discuss any borderline cases with Vania
- "For homework: try to annotate the other 2 pilot slides using the same approach"
- "Send me the project when done, or we can review in the next session"
- Mention: "Once annotations are validated, I'll train the classifier and show you the results"

---

# PART 4: KEY THINGS TO SAY / NOT SAY

---

## DO Say:
- "Your histological expertise is essential here — I handle the technical side"
- "Let me know if the classification doesn't match your expectations"
- "We can always refine and retrain"
- "The pilot is exactly for this — finding the right parameters"
- "I've prepared automated scripts that will make the full dataset processing fast"

## DON'T Say:
- Don't pretend to be a pathologist — defer all tissue interpretation to Vania
- Don't say "I think this is tumor" — say "Based on what you've described, this area matches your criteria"
- Don't rush — let them take time with each annotation
- Don't overwhelm with technical details about the scripts/code

## If You Don't Know Something:
- "Let me check that and get back to you" (then ask me)
- "That's a great question — let me look into the best approach for that"
- Never bluff — Vania is a researcher, she'll respect honesty

---

# PART 5: AFTER THE SESSION

---

1. Save the QuPath project (File → Save)
2. Note down any specific criteria Vania mentioned for:
   - What makes a region "Tumor" vs "Stroma"
   - Any special cases (necrosis, inflammation, artifacts)
   - How strict the boundaries should be
3. Come back to me with these notes — I'll help you refine the scripts and thresholds
4. Wait for the resident to complete annotations on pilot slides
5. Once annotations are done → train the pixel classifier → show Vania results

---

# QUICK REFERENCE CARD (Print This)

```
SHORTCUTS:
  B = Brush tool          P = Polygon tool
  W = Wand tool           M = Move tool
  A = Toggle annotations  D = Toggle detections
  [ = Smaller brush       ] = Bigger brush
  Alt+paint = Erase       Delete = Remove selected
  Ctrl+Z = Undo           Shift+C = Brightness
  Ctrl+S = Save

WORKFLOW ORDER:
  1. Set classes (Tumor, Stroma, Background)
  2. Annotate ground truth (Brush tool, 5+ per class)
  3. Train pixel classifier (Classify → Train pixel classifier)
  4. Apply classifier to full image
  5. Cell detection (Analyze → Cell detection)
  6. Classify lymphocytes (script 05)
  7. Quantify density (script 06)
  8. Export CSV (script 07)

WHAT TO ANNOTATE:
  TUMOR  = Dense cell clusters, large dark nuclei, packed tight
  STROMA = Pink fibrous tissue, scattered cells, open structure
  BACKGROUND = Empty glass, no tissue
```
