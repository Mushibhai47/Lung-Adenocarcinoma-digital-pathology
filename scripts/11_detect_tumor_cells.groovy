/**
 * 11_detect_tumor_cells.groovy
 * ==============================
 * Detects ALL cells, then removes lymphocytes using the EXACT same
 * criteria that script 10 uses to detect lymphocytes.
 * What remains = tumor cells.
 *
 * Logic: detect everything → subtract lymphocytes → TumorCell
 *
 * Usage: Run for project (processes all slides)
 */

import qupath.lib.objects.classes.PathClass

// ============================================================
// CONFIGURATION
// ============================================================

// Broad detection — catch all cells including lightly stained tumor cells
def cellDetectionParams = '{"detectionImageBrightfield":"Hematoxylin OD","requestedPixelSizeMicrons":0.5,"backgroundRadiusMicrons":8.0,"backgroundByReconstruction":true,"medianRadiusMicrons":0.0,"sigmaMicrons":2.0,"minAreaMicrons":10.0,"maxAreaMicrons":1000.0,"threshold":0.05,"maxBackground":2.0,"watershedPostProcess":true,"cellExpansionMicrons":1.0,"includeNuclei":true,"smoothBoundaries":true,"makeMeasurements":true}'

// Lymphocyte criteria — EXACT same as script 10 (validated by Vania)
// A cell matching ALL of these is a lymphocyte → removed
def minLymphNucleusArea = 15.0
def maxLymphNucleusArea = 80.0
def minLymphCircularity = 0.65
def minLymphHemaOD      = 0.08
def maxLymphCellNucRatio = 7.0

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

println "=== TUMOR CELL DETECTION: ${imageName} ==="

def tumorAnnotations = getAnnotationObjects().findAll {
    it.getPathClass()?.toString() == "Tumor"
}

if (tumorAnnotations.isEmpty()) {
    println "WARNING: No Tumor annotations found. Skipping."
    return
}

// Detect all cells
selectObjects(tumorAnnotations)
runPlugin('qupath.imagej.detect.cells.WatershedCellDetection', cellDetectionParams)

println "  Total detected: ${getDetectionObjects().size()}"

def tumorCellClass = PathClass.fromString("TumorCell")
def toRemove = []
def toKeep   = []

getDetectionObjects().each { cell ->
    def m  = cell.getMeasurements()
    def na = getM(m, "Nucleus: Area µm^2", "Nucleus: Area µm²", "Nucleus: Area")
    def ci = getM(m, "Nucleus: Circularity")
    def hm = getM(m, "Hematoxylin: Nucleus: Mean", "Nucleus: Hematoxylin OD mean")
    def ca = getM(m, "Cell: Area µm^2", "Cell: Area µm²", "Cell: Area")

    // Apply script 10 lymphocyte criteria — ALL must pass to be excluded
    boolean isLymph = false
    if (na != null && !na.isNaN() && na >= minLymphNucleusArea && na <= maxLymphNucleusArea) {
        boolean circOk  = (ci == null || ci.isNaN() || ci >= minLymphCircularity)
        boolean hemaOk  = (hm == null || hm.isNaN() || hm >= minLymphHemaOD)
        boolean ratioOk = (ca == null || ca.isNaN() || na <= 0 || (ca / na) <= maxLymphCellNucRatio)
        isLymph = circOk && hemaOk && ratioOk
    }

    if (isLymph) { toRemove << cell }
    else         { cell.setPathClass(tumorCellClass); toKeep << cell }
}

removeObjects(toRemove, true)
println "  Tumor cells kept: ${toKeep.size()} | Lymphocytes removed: ${toRemove.size()}"

// Export CSV
def csvFile = new File(outputDir, "tumor_cell_results.csv")
def writeHeader = !csvFile.exists() || csvFile.length() == 0
def writer = csvFile.newWriter(true)

if (writeHeader) {
    writer.writeLine(["Image","Region_Index","Rectangle_Area_mm2",
                      "Tumor_Cells","Tumor_Cell_Density_per_mm2"].join(","))
}

tumorAnnotations.eachWithIndex { ann, idx ->
    def areaMM2 = ann.getROI().getArea() * pixelWidthMM * pixelHeightMM
    def tc      = ann.getChildObjects().findAll {
        it.isDetection() && it.getPathClass()?.toString() == "TumorCell"
    }.size()
    def density = areaMM2 > 0 ? tc / areaMM2 : 0.0

    writer.writeLine(["\"${imageName}\"", idx+1,
                      String.format('%.6f', areaMM2),
                      tc,
                      String.format('%.2f', density)].join(","))
}
writer.close()

fireHierarchyUpdate()
println "Results saved to: tumor_cell_results.csv"

def getM(def m, String... names) {
    for (n in names) { if (m.containsKey(n)) return m.get(n) }
    return null
}
