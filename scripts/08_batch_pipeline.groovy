/**
 * 08_batch_pipeline.groovy
 * ==========================
 * FULL BATCH PROCESSING PIPELINE
 *
 * Uses existing Tumor annotations (rectangles drawn by Vania) to:
 *   1. Run cell detection within Tumor rectangles
 *   2. Classify cells as Lymphocyte vs Other (tumor cells)
 *   3. Calculate Tumor-Stroma Ratio (TSR)
 *   4. Export results to CSV
 *
 * Prerequisites:
 *   - .qpdata files loaded for each slide (Tumor rectangles visible)
 *   - All slides added to the project
 *
 * Usage:
 *   Script Editor → Run for project
 *   (Processes ALL images in the project sequentially)
 */

import qupath.lib.objects.classes.PathClass

// ============================================================
// CONFIGURATION
// ============================================================

// Cell detection parameters — cellExpansionMicrons=5.0 for full cell body measurement (TSR)
def cellDetectionParams = '{"detectionImageBrightfield":"Hematoxylin OD","requestedPixelSizeMicrons":0.5,"backgroundRadiusMicrons":8.0,"backgroundByReconstruction":true,"medianRadiusMicrons":0.0,"sigmaMicrons":1.5,"minAreaMicrons":10.0,"maxAreaMicrons":800.0,"threshold":0.05,"maxBackground":2.0,"watershedPostProcess":true,"cellExpansionMicrons":1.0,"includeNuclei":true,"smoothBoundaries":true,"makeMeasurements":true}'

// Lymphocyte thresholds
// Note: with 5µm expansion, cell:nucleus ratio is high for all cells — rely on size/shape/staining
def minNucleusArea    = 30.0   // µm² — exclude tiny cells
def maxNucleusArea    = 80.0   // µm² — lymphocytes have small nuclei
def minCircularity    = 0.85   // very round nuclei
def minHematoxylinOD  = 0.12   // darkest nuclei only
def maxCellNucRatio   = 15.0   // disabled — not reliable with 5µm expansion

// Output directory
def outputDir = buildFilePath(PROJECT_BASE_DIR, "output", "csv")
mkdirs(outputDir)

// ============================================================
// PIPELINE START
// ============================================================

def imageData = getCurrentImageData()
def server    = imageData.getServer()
def cal       = server.getPixelCalibration()
def imageName = server.getMetadata().getName()

println "=============================================="
println "BATCH PIPELINE — Processing: ${imageName}"
println "=============================================="

def startTime = System.currentTimeMillis()

// ============================================================
// STEP 1: Find Tumor annotations
// ============================================================

def tumorAnnotations = getAnnotationObjects().findAll {
    it.getPathClass()?.toString() == "Tumor"
}

if (tumorAnnotations.isEmpty()) {
    println "WARNING: No Tumor annotations found for ${imageName}. Skipping."
    return
}

println "\n[STEP 1] Found ${tumorAnnotations.size()} Tumor annotation(s)."

// ============================================================
// STEP 2: Cell Detection
// ============================================================

println "\n[STEP 2] Running cell detection..."

selectObjects(tumorAnnotations)
runPlugin('qupath.imagej.detect.cells.WatershedCellDetection', cellDetectionParams)

def totalCells = getDetectionObjects().size()
println "  Detected ${totalCells} cells"

if (totalCells == 0) {
    println "  WARNING: No cells detected. Check stain vectors or threshold."
    return
}

// ============================================================
// STEP 3: Classify Lymphocytes
// ============================================================

println "\n[STEP 3] Classifying lymphocytes..."

def lymphocyteClass = PathClass.fromString("Lymphocyte")
def otherClass      = PathClass.fromString("Other")

int lymphCount = 0
int otherCount = 0

getDetectionObjects().each { cell ->
    def m = cell.getMeasurements()

    def nucleusArea = getM(m, "Nucleus: Area µm^2", "Nucleus: Area µm²", "Nucleus: Area")
    def circularity  = getM(m, "Nucleus: Circularity")
    def hematoxylin  = getM(m, "Hematoxylin: Nucleus: Mean", "Nucleus: Hematoxylin OD mean")
    def cellArea     = getM(m, "Cell: Area µm^2", "Cell: Area µm²", "Cell: Area")

    boolean isLymph = true

    if (nucleusArea == null || nucleusArea.isNaN()) {
        isLymph = false
    } else {
        if (nucleusArea < minNucleusArea || nucleusArea > maxNucleusArea) isLymph = false
        if (circularity != null && !circularity.isNaN() && circularity < minCircularity) isLymph = false
        if (hematoxylin != null && !hematoxylin.isNaN() && hematoxylin < minHematoxylinOD) isLymph = false
        if (cellArea != null && !cellArea.isNaN() && nucleusArea > 0 && (cellArea / nucleusArea) > maxCellNucRatio) isLymph = false
    }

    if (isLymph) { cell.setPathClass(lymphocyteClass); lymphCount++ }
    else         { cell.setPathClass(otherClass);       otherCount++ }
}

println "  Lymphocytes: ${lymphCount} | Other (tumor): ${otherCount}"

// ============================================================
// STEP 4: Export Results
// ============================================================

println "\n[STEP 4] Exporting results..."

def sep = ","
def pixelWidthMM  = cal.getPixelWidth().doubleValue()  / 1000.0
def pixelHeightMM = cal.getPixelHeight().doubleValue() / 1000.0
def um2ToMm2      = (cal.getPixelWidth().doubleValue() * cal.getPixelHeight().doubleValue()) / 1e6

// --- Region-level CSV ---
def regionFile = new File(outputDir, "region_results.csv")
def writeRegionHeader = !regionFile.exists() || regionFile.length() == 0
def rw = regionFile.newWriter(true)

if (writeRegionHeader) {
    rw.writeLine(["Image","Region_Index","Rectangle_Area_mm2",
                  "Total_Cells","Lymphocytes","Tumor_Cells",
                  "Lymphocyte_Percentage","Lymphocyte_Density_per_mm2",
                  "Tumor_Cell_Area_mm2","Stroma_Area_mm2","TSR"].join(sep))
}

tumorAnnotations.eachWithIndex { ann, idx ->
    def rectAreaMM2 = ann.getROI().getArea() * pixelWidthMM * pixelHeightMM
    def allC        = ann.getChildObjects().findAll { it.isDetection() }
    def lymphs      = allC.findAll { it.getPathClass()?.toString() == "Lymphocyte" }
    def others      = allC.findAll { it.getPathClass()?.toString() == "Other" }

    def lc = lymphs.size()
    def oc = others.size()
    def lp = allC.size() > 0 ? (lc * 100.0 / allC.size()) : 0.0
    def ld = rectAreaMM2 > 0 ? lc / rectAreaMM2 : 0.0

    // TSR calculation: tumor cell area / (tumor cell area + stroma area)
    // Stroma area = rectangle area - all detected cell areas
    def tumorCellAreaMM2 = others.sum { cell ->
        def ca = getM(cell.getMeasurements(), "Cell: Area µm^2", "Cell: Area µm²", "Cell: Area")
        (ca != null && !ca.isNaN()) ? ca * um2ToMm2 : 0.0
    } ?: 0.0

    def lymphCellAreaMM2 = lymphs.sum { cell ->
        def ca = getM(cell.getMeasurements(), "Cell: Area µm^2", "Cell: Area µm²", "Cell: Area")
        (ca != null && !ca.isNaN()) ? ca * um2ToMm2 : 0.0
    } ?: 0.0

    def allCellAreaMM2 = tumorCellAreaMM2 + lymphCellAreaMM2
    def stromaAreaMM2  = Math.max(rectAreaMM2 - allCellAreaMM2, 0.0)
    def tsr            = (tumorCellAreaMM2 + stromaAreaMM2) > 0 ?
                         tumorCellAreaMM2 / (tumorCellAreaMM2 + stromaAreaMM2) : 0.0

    rw.writeLine(["\"${imageName}\"", idx+1,
                  String.format('%.6f', rectAreaMM2),
                  allC.size(), lc, oc,
                  String.format('%.2f', lp),
                  String.format('%.2f', ld),
                  String.format('%.6f', tumorCellAreaMM2),
                  String.format('%.6f', stromaAreaMM2),
                  String.format('%.4f', tsr)].join(sep))
}
rw.close()

// --- Image-level summary CSV ---
def summaryFile = new File(outputDir, "image_summary.csv")
def writeSumHeader = !summaryFile.exists() || summaryFile.length() == 0
def sw = summaryFile.newWriter(true)

if (writeSumHeader) {
    sw.writeLine(["Image","Total_Rectangle_Area_mm2","Total_Cells","Lymphocytes","Tumor_Cells",
                  "Lymphocyte_Density_per_mm2","Lymphocyte_Percentage",
                  "Total_Tumor_Cell_Area_mm2","Total_Stroma_Area_mm2","Overall_TSR"].join(sep))
}

def totalRectArea   = 0.0
def totalCellsAll   = 0
def totalLymphs     = 0
def totalTumorArea  = 0.0
def totalStromaArea = 0.0

tumorAnnotations.each { ann ->
    def rectAreaMM2 = ann.getROI().getArea() * pixelWidthMM * pixelHeightMM
    def allC        = ann.getChildObjects().findAll { it.isDetection() }
    def lymphs      = allC.findAll { it.getPathClass()?.toString() == "Lymphocyte" }
    def others      = allC.findAll { it.getPathClass()?.toString() == "Other" }

    def tca = others.sum { cell ->
        def ca = getM(cell.getMeasurements(), "Cell: Area µm^2", "Cell: Area µm²", "Cell: Area")
        (ca != null && !ca.isNaN()) ? ca * um2ToMm2 : 0.0
    } ?: 0.0

    def lca = lymphs.sum { cell ->
        def ca = getM(cell.getMeasurements(), "Cell: Area µm^2", "Cell: Area µm²", "Cell: Area")
        (ca != null && !ca.isNaN()) ? ca * um2ToMm2 : 0.0
    } ?: 0.0

    def stroma = Math.max(rectAreaMM2 - tca - lca, 0.0)

    totalRectArea   += rectAreaMM2
    totalCellsAll   += allC.size()
    totalLymphs     += lymphs.size()
    totalTumorArea  += tca
    totalStromaArea += stroma
}

def overallDensity = totalRectArea > 0 ? totalLymphs / totalRectArea : 0.0
def overallPct     = totalCellsAll > 0 ? (totalLymphs * 100.0 / totalCellsAll) : 0.0
def overallTSR     = (totalTumorArea + totalStromaArea) > 0 ?
                     totalTumorArea / (totalTumorArea + totalStromaArea) : 0.0

sw.writeLine(["\"${imageName}\"",
              String.format('%.6f', totalRectArea),
              totalCellsAll, totalLymphs, (totalCellsAll - totalLymphs),
              String.format('%.2f', overallDensity),
              String.format('%.2f', overallPct),
              String.format('%.6f', totalTumorArea),
              String.format('%.6f', totalStromaArea),
              String.format('%.4f', overallTSR)].join(sep))
sw.close()

fireHierarchyUpdate()

def elapsed = (System.currentTimeMillis() - startTime) / 1000.0
println "\n=============================================="
println "COMPLETE: ${imageName}"
println "Cells: ${totalCellsAll} | Lymphocytes: ${totalLymphs} (${String.format('%.1f', overallPct)}%)"
println "Overall TSR: ${String.format('%.4f', overallTSR)}"
println "Time: ${String.format('%.1f', elapsed)}s"
println "=============================================="

// ============================================================
// HELPER
// ============================================================

def getM(def measurements, String... names) {
    for (n in names) {
        if (measurements.containsKey(n)) return measurements.get(n)
    }
    return null
}
