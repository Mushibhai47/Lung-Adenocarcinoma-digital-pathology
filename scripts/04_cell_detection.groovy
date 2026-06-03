/**
 * 04_cell_detection.groovy
 * ==========================
 * Runs cell detection within Tumor and Stroma annotation regions.
 * Detects all nuclei using watershed cell detection on the Hematoxylin channel.
 *
 * Prerequisites:
 *   - Pixel classifier applied (annotations with Tumor/Stroma classes exist)
 *   - OR manual annotations with Tumor/Stroma classes
 *
 * Usage:
 *   - Single image: Script Editor → Run
 *   - All images: Script Editor → Run for project
 */

// ============================================================
// CONFIGURATION — Cell Detection Parameters
// ============================================================

// Detection threshold — adjust if too many/few cells detected (0.05-0.3 range)
def threshold = 0.1

// ============================================================
// RUN DETECTION
// ============================================================

def imageData = getCurrentImageData()
if (imageData == null) {
    println "ERROR: No image is open."
    return
}

// Set image type and slide-specific stain vectors (estimated from this slide)
setImageType('BRIGHTFIELD_H_E')
setColorDeconvolutionStains('{"Name" : "H&E default", "Stain 1" : "Hematoxylin", "Values 1" : "0.6511078257574492 0.7011930431234068 0.29049426072255424", "Stain 2" : "Eosin", "Values 2" : "0.21589893562087106 0.8011960501132093 0.5580972485873467", "Background" : " 255 255 255"}')

// Select annotations to process (Tumor and Stroma only)
def annotations = getAnnotationObjects().findAll {
    def cls = it.getPathClass()?.toString()
    cls == "Tumor" || cls == "Stroma"
}

if (annotations.isEmpty()) {
    println "ERROR: No Tumor or Stroma annotations found."
    println "Run the pixel classifier first (script 03) or create manual annotations."
    return
}

println "Found ${annotations.size()} annotation(s) to process:"
annotations.each { println "  - ${it.getPathClass()}: ${it}" }

// Select all target annotations
selectObjects(annotations)

println "\nRunning cell detection (Hematoxylin OD channel, threshold=${threshold})..."

// Use exact parameter format confirmed working in QuPath 0.6 GUI
def paramString = """{"detectionImageBrightfield":"Hematoxylin OD","requestedPixelSizeMicrons":0.5,"backgroundRadiusMicrons":8.0,"backgroundByReconstruction":true,"medianRadiusMicrons":0.0,"sigmaMicrons":1.5,"minAreaMicrons":10.0,"maxAreaMicrons":400.0,"threshold":${threshold},"maxBackground":2.0,"watershedPostProcess":true,"cellExpansionMicrons":5.0,"includeNuclei":true,"smoothBoundaries":true,"makeMeasurements":true}"""

// Run the watershed cell detection
runPlugin('qupath.imagej.detect.cells.WatershedCellDetection', paramString)

// ============================================================
// REPORT RESULTS
// ============================================================

def allDetections = getDetectionObjects()
println "\n======================================"
println "CELL DETECTION RESULTS"
println "======================================"
println "Total cells detected: ${allDetections.size()}"

// Count detections per annotation class
annotations.each { annotation ->
    def className = annotation.getPathClass()?.toString()
    def childDetections = annotation.getChildObjects().findAll { it.isDetection() }
    println "  ${className}: ${childDetections.size()} cells"
}

println "\nNext step: Run script 05 for lymphocyte classification."
println "Toggle cell detections visibility with 'D' key."
