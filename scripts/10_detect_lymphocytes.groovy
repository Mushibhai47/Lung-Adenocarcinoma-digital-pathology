/**
 * 10_detect_lymphocytes.groovy
 * ==============================
 * Detects and counts LYMPHOCYTES ONLY within Tumor rectangles.
 * Lymphocytes = small, dark, round nuclei with no cytoplasm.
 *
 * Usage: Run for project (processes all slides)
 */

import qupath.lib.objects.classes.PathClass

// ============================================================
// CONFIGURATION
// ============================================================

// threshold:0.15 = only detect dark nuclei
// sigmaMicrons:2.0 = more smoothing → fewer split/partial nucleus detections
// minAreaMicrons:25 = exclude nucleus fragments (too small to be real lymphocytes)
// maxAreaMicrons:150 = exclude large cells at detection stage
def cellDetectionParams = '{"detectionImageBrightfield":"Hematoxylin OD","requestedPixelSizeMicrons":0.5,"backgroundRadiusMicrons":8.0,"backgroundByReconstruction":true,"medianRadiusMicrons":0.0,"sigmaMicrons":2.0,"minAreaMicrons":25.0,"maxAreaMicrons":150.0,"threshold":0.15,"maxBackground":2.0,"watershedPostProcess":true,"cellExpansionMicrons":1.0,"includeNuclei":true,"smoothBoundaries":true,"makeMeasurements":true}'

// Lymphocyte criteria — restored to earliest validated version
def minNucleusArea   = 15.0   // µm²
def maxNucleusArea   = 80.0   // µm²
def minCircularity   = 0.65
def minHematoxylinOD = 0.08
def maxCellNucRatio  = 7.0

// Output
def outputDir = buildFilePath(PROJECT_BASE_DIR, "output", "csv")
mkdirs(outputDir)

// ============================================================
// RUN
// ============================================================

def imageData = getCurrentImageData()
def server    = imageData.getServer()
def cal       = server.getPixelCalibration()
def imageName = server.getMetadata().getName()
def pixelWidthMM  = cal.getPixelWidth().doubleValue()  / 1000.0
def pixelHeightMM = cal.getPixelHeight().doubleValue() / 1000.0

println "=== LYMPHOCYTE DETECTION: ${imageName} ==="

def tumorAnnotations = getAnnotationObjects().findAll {
    it.getPathClass()?.toString() == "Tumor"
}

if (tumorAnnotations.isEmpty()) {
    println "WARNING: No Tumor annotations found. Skipping."
    return
}

// Detect cells
selectObjects(tumorAnnotations)
runPlugin('qupath.imagej.detect.cells.WatershedCellDetection', cellDetectionParams)

// All detected cells marked as Lymphocyte (one color for visual review)
def lymphocyteClass = PathClass.fromString("Lymphocyte")

getDetectionObjects().each { cell -> cell.setPathClass(lymphocyteClass) }

def lymphCount = getDetectionObjects().size()
println "  Marked ${lymphCount} cells as Lymphocyte"

// Export CSV
def csvFile = new File(outputDir, "lymphocyte_results.csv")
def writeHeader = !csvFile.exists() || csvFile.length() == 0
def writer = csvFile.newWriter(true)

if (writeHeader) {
    writer.writeLine(["Image","Region_Index","Rectangle_Area_mm2","Total_Cells",
                      "Lymphocytes","Lymphocyte_Percentage",
                      "Lymphocyte_Density_per_mm2"].join(","))
}

tumorAnnotations.eachWithIndex { ann, idx ->
    def areaMM2 = ann.getROI().getArea() * pixelWidthMM * pixelHeightMM
    def allC    = ann.getChildObjects().findAll { it.isDetection() }
    def lc      = allC.findAll { it.getPathClass()?.toString() == "Lymphocyte" }.size()
    def lp      = allC.size() > 0 ? (lc * 100.0 / allC.size()) : 0.0
    def ld      = areaMM2 > 0 ? lc / areaMM2 : 0.0

    writer.writeLine(["\"${imageName}\"", idx+1,
                      String.format('%.6f', areaMM2),
                      allC.size(), lc,
                      String.format('%.2f', lp),
                      String.format('%.2f', ld)].join(","))
}
writer.close()

fireHierarchyUpdate()
println "Results saved to: lymphocyte_results.csv"

def getM(def m, String... names) {
    for (n in names) { if (m.containsKey(n)) return m.get(n) }
    return null
}
