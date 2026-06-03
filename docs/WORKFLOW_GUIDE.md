# QuPath H&E Analysis Workflow Guide
## For Musharaf — Master This Before Guiding Vania

---

## 1. UNDERSTANDING THE PROJECT

**Goal:** Quantify lymphocyte density in Tumor vs Stroma regions across ~100-120 H&E whole-slide images.

**Pipeline Overview:**
```
Slides → QuPath Project → Annotate ROIs (Tumor/Stroma) → Train Pixel Classifier →
Detect Cells → Classify Lymphocytes → Quantify Density → Export CSV
```

**Key Terms:**
- **H&E (Hematoxylin & Eosin):** Standard histology stain. Hematoxylin = blue/purple (nuclei), Eosin = pink (cytoplasm/stroma)
- **ROI (Region of Interest):** Areas you mark on the slide for analysis
- **Pixel Classifier:** Machine learning model (Random Forest) that classifies every pixel as Tumor, Stroma, or Background
- **Ground Truth:** The manually annotated examples that train the classifier
- **Lymphocytes:** Small round dark-blue cells (immune cells) — the target to count

---

## 2. QUPATH SETUP & BASICS

### 2.1 Installing QuPath
- Download from: https://qupath.github.io (latest v0.5.x or v0.6.x)
- Install — works out of the box, no dependencies needed
- Allocate memory: Edit → Preferences → set memory to at least 8GB (16GB recommended for WSI)

### 2.2 Creating a Project
1. **File → Project → Create project** → Select the `project` folder
2. **Add images:** File → Project → Add images → Select the .svs/.ndpi/.mrxs files from `slides/` folder
3. QuPath creates a `project.qpproj` file and `data/` folder automatically

### 2.3 Navigation Controls
| Action | Control |
|--------|---------|
| Pan | Click + drag (or middle mouse) |
| Zoom | Scroll wheel |
| Fit to screen | Double-click on slide thumbnail |
| Toggle annotations | A key |
| Toggle detections | D key |
| Toggle fill | Shift+F |
| Brightness/Contrast | Shift+C |

### 2.4 Annotation Tools
| Tool | Shortcut | When to Use |
|------|----------|-------------|
| Rectangle | R | Quick rectangular ROIs |
| Ellipse | O | Circular regions |
| Polygon | P | Precise irregular boundaries |
| Brush | B | Paint-style freehand (BEST for ground truth) |
| Wand | W | Auto-edge detection (good for well-defined regions) |
| Points | . | Mark individual cells |

**For this project, primarily use Brush (B) and Polygon (P).**

---

## 3. ANNOTATION WORKFLOW (What You'll Guide Vania Through)

### 3.1 Setting Up Annotation Classes
Before annotating, define the classes:
1. Right-click in the **Annotations** tab → **Set class**
2. Or use: **Automate → Show script editor** → Run this quick script:

```groovy
// Define annotation classes
def pathClasses = [
    PathClass.fromString("Tumor"),
    PathClass.fromString("Stroma"),
    PathClass.fromString("Background"),
    PathClass.fromString("Ignore*")
]
// The classes will appear in the annotation class list
println "Classes defined: " + pathClasses
```

3. In the Annotations pane, the classes will appear. You can assign colors.

### 3.2 How to Annotate (Step-by-Step for Live Session)

**Step 1: Select the Brush tool (B)**
- Adjust brush size with `[` and `]` keys

**Step 2: Select the class FIRST**
- In the Annotations tab on the left, click "Tumor" class
- Now everything you draw will be Tumor

**Step 3: Draw representative regions**
- For TUMOR: Select areas of dense epithelial tumor cells
- For STROMA: Select areas of connective tissue between tumor nests
- For BACKGROUND: Select glass/empty areas (optional but helps classifier)

**Step 4: Key annotation rules to tell Vania:**
- Draw **at least 5-10 regions per class** for good training
- Make annotations **representative** — include variety (dense/sparse, dark/light stained)
- **Do NOT overlap** annotations of different classes
- Keep borders **clean** — don't include mixed regions at edges
- Annotate from **different parts** of the slide (not all from one corner)
- Use **Lock annotations** (right-click → Lock) when finalized

### 3.3 Annotation Validation Checklist
Before training the classifier, verify:
- [ ] At least 5 regions per class
- [ ] No overlapping annotations
- [ ] Annotations from multiple areas of the slide
- [ ] Both typical and edge-case examples included
- [ ] Vania has reviewed and approved each annotation

---

## 4. PIXEL CLASSIFIER TRAINING

### 4.1 How the Pixel Classifier Works
- Uses **Random Trees (Random Forest)** algorithm
- Looks at pixel-level features: color, texture, edges, smoothing at multiple scales
- Trained on the annotated ground truth regions
- Outputs a classification for every pixel in the image

### 4.2 Training Steps (In QuPath GUI)
1. **Classify → Pixel classification → Train pixel classifier**
2. Settings:
   - **Classifier:** Random Trees
   - **Resolution:** Medium (20 µm/px for speed, 10 µm/px for accuracy)
   - **Features:** All defaults (Gaussian, Laplacian of Gaussian, Weighted deviation, Gradient magnitude, Structure tensor)
   - **Scales:** σ = 1, 2, 4, 8 (multiple scales captures different structure sizes)
   - **Output:** Classification
   - **Region:** Annotations only (trains on your ground truth)
   - **Classes:** Tumor, Stroma (+ Background if annotated)
3. Click **Live preview** — the classifier runs in real-time
4. Visually inspect: Does it match your expectations?
5. If good → **Save** → Name it (e.g., "tumor_stroma_v1")

### 4.3 Evaluating the Classifier
- Look for **misclassified regions** — zoom into boundaries
- If tumor is bleeding into stroma → add more stroma annotations at boundaries
- If background is classified as stroma → add background annotations
- **Iterate:** Add more ground truth → retrain → re-evaluate
- The classifier is saved in: `project/classifiers/pixel_classifiers/`

---

## 5. CELL DETECTION & LYMPHOCYTE QUANTIFICATION

### 5.1 Cell Detection
1. **Analyze → Cell detection** (or StarDist if available)
2. Key parameters:
   - **Detection image:** Hematoxylin (separates nuclei channel via color deconvolution)
   - **Requested pixel size:** 0.5 µm (standard for cell detection)
   - **Background radius:** 8 µm
   - **Minimum area:** 10 µm²
   - **Maximum area:** 400 µm²
   - **Threshold:** 0.1 - 0.2 (adjust based on staining intensity)
   - **Split by shape:** Yes (separates touching nuclei)
   - **Cell expansion:** 5 µm (creates estimated cell boundary)
3. Run → Check detections visually (toggle D key)

### 5.2 Identifying Lymphocytes
Lymphocytes have distinctive features:
- **Small** (typically 6-10 µm diameter → area 28-78 µm²)
- **Round** (high circularity/solidity)
- **Dark** (intense hematoxylin staining)
- **Minimal cytoplasm** (nucleus:cell ratio is high)

Classification approach:
- Use **object classifier** or **measurement-based thresholds**
- Key measurements: Nucleus area, Nucleus circularity, Hematoxylin OD mean, Cell:Nucleus ratio

### 5.3 Lymphocyte Density Calculation
```
Density = Number of lymphocytes in region / Area of region (mm²)
```
- Calculated separately for Tumor and Stroma regions
- Reported as: lymphocytes/mm²

---

## 6. BATCH PROCESSING

### 6.1 How It Works
- Write a Groovy script that does the full pipeline
- Run it via: **Automate → Script editor → Run for project**
- This applies the script to ALL images in the project
- Results saved per-image in the project data

### 6.2 Pipeline Order
1. Load pixel classifier → Apply to full image
2. Create annotation objects from classified regions
3. Run cell detection within annotations
4. Classify cells (lymphocytes vs other)
5. Calculate density measurements
6. Export results

---

## 7. LIVE SESSION SCRIPT (What to Say/Do)

### Session 1 Agenda (~60-90 min)

**Opening (5 min):**
"Let me share my screen. I'll walk you through QuPath step by step. By the end, you'll be able to annotate tumor vs stroma regions independently."

**Project Setup (10 min):**
- Show how to create project
- Add the sample slides
- Navigate around a slide (zoom, pan)
- Explain the H&E appearance

**Annotation Demo (20 min):**
- Set up Tumor/Stroma/Background classes
- Demo the Brush tool on one region
- Explain what Tumor looks like vs Stroma
- "Now you try — I'll guide you"

**Vania Practices (30 min):**
- She annotates while you guide
- Give feedback: "That's a good tumor region" / "Try to keep the boundary tighter"
- Ensure she covers different areas

**Review & Next Steps (10 min):**
- Review all annotations together
- Discuss any unclear regions
- Plan: "For the next session, try to complete annotations on the remaining pilot slides"

---

## 8. KEY QUPATH GROOVY SCRIPTING CONCEPTS

```groovy
// Get current image
def imageData = getCurrentImageData()

// Get hierarchy (contains all objects)
def hierarchy = imageData.getHierarchy()

// Get all annotations
def annotations = getAnnotationObjects()

// Filter by class
def tumorAnnotations = annotations.findAll { it.getPathClass() == getPathClass("Tumor") }

// Get detections (cells) within an annotation
def cells = hierarchy.getObjectsForROI(null, annotation.getROI())

// Measurements
def area = annotation.getROI().getArea()  // in pixels
def pixelSize = imageData.getServer().getPixelCalibration()
def areaUM2 = area * pixelSize.getPixelWidth() * pixelSize.getPixelHeight()  // in µm²
def areaMM2 = areaUM2 / 1e6  // in mm²

// Run cell detection programmatically
import qupath.lib.plugins.parameters.ParameterList
runPlugin('qupath.imagej.detect.cells.WatershedCellDetection', '{"detectionImage":"Hematoxylin",...}')
```

---

## 9. TROUBLESHOOTING COMMON ISSUES

| Issue | Solution |
|-------|----------|
| Slide won't open | Install OpenSlide, check file format (.svs, .ndpi, .mrxs supported) |
| Out of memory | Edit → Preferences → increase memory to 16GB+ |
| Classifier looks bad | Add more training annotations, especially at boundaries |
| Too many false detections | Increase detection threshold, adjust min/max area |
| Cells not splitting | Enable "Split by shape", decrease threshold |
| Slow processing | Lower resolution (increase µm/px), use SSD drive |
| Annotations disappeared | Press A to toggle visibility |

---

## 10. DELIVERABLES CHECKLIST

- [ ] QuPath project with all slides loaded
- [ ] Trained pixel classifier (tumor_stroma_v1.json)
- [ ] Validated annotations on 2-3 pilot slides
- [ ] Cell detection parameters optimized
- [ ] Lymphocyte classification criteria defined
- [ ] Batch processing script tested on pilot
- [ ] CSV exports with density measurements per slide
- [ ] Reproducible workflow documented
