/**
 * 06_quantify_density.groovy
 * ============================
 * Quantifies lymphocyte density in Tumor and Stroma regions.
 *
 * Calculates:
 *   - Lymphocyte count per region
 *   - Region area (mm²)
 *   - Lymphocyte density (cells/mm²)
 *   - Percentage of lymphocytes vs total cells
 *
 * Prerequisites:
 *   - Cells detected (script 04) and classified (script 05)
 *
 * Usage:
 *   - Single image: Script Editor → Run
 *   - All images: Script Editor → Run for project
 */

import qupath.lib.objects.PathObjects

// ============================================================
// QUANTIFICATION
// ============================================================

def imageData = getCurrentImageData()
if (imageData == null) {
    println "ERROR: No image is open."
    return
}

def server = imageData.getServer()
def cal = server.getPixelCalibration()
def imageName = server.getMetadata().getName()

// Get all annotations (Tumor and Stroma)
def annotations = getAnnotationObjects().findAll {
    def cls = it.getPathClass()?.toString()
    cls == "Tumor" || cls == "Stroma"
}

if (annotations.isEmpty()) {
    println "ERROR: No Tumor or Stroma annotations found."
    return
}

println "=============================================="
println "LYMPHOCYTE DENSITY QUANTIFICATION"
println "Image: ${imageName}"
println "=============================================="

// Summary accumulators
def summaryData = []

annotations.eachWithIndex { annotation, idx ->
    def className = annotation.getPathClass()?.toString()

    // Calculate area in mm²
    def areaPixels = annotation.getROI().getArea()
    def pixelWidthMM = cal.getPixelWidth().doubleValue() / 1000.0  // µm to mm
    def pixelHeightMM = cal.getPixelHeight().doubleValue() / 1000.0
    def areaMM2 = areaPixels * pixelWidthMM * pixelHeightMM

    // Get child detections
    def allCells = annotation.getChildObjects().findAll { it.isDetection() }
    def lymphocytes = allCells.findAll { it.getPathClass()?.toString() == "Lymphocyte" }
    def otherCells = allCells.findAll { it.getPathClass()?.toString() != "Lymphocyte" }

    // Calculate density
    def lymphDensity = areaMM2 > 0 ? lymphocytes.size() / areaMM2 : 0
    def totalDensity = areaMM2 > 0 ? allCells.size() / areaMM2 : 0
    def lymphPercentage = allCells.size() > 0 ? (lymphocytes.size() * 100.0 / allCells.size()) : 0

    println "\n--- ${className} Region ${idx + 1} ---"
    println "  Area:              ${String.format('%.4f', areaMM2)} mm²"
    println "  Total cells:       ${allCells.size()}"
    println "  Lymphocytes:       ${lymphocytes.size()}"
    println "  Other cells:       ${otherCells.size()}"
    println "  Lymphocyte %:      ${String.format('%.1f', lymphPercentage)}%"
    println "  Lymph. density:    ${String.format('%.0f', lymphDensity)} cells/mm²"
    println "  Total cell density:${String.format('%.0f', totalDensity)} cells/mm²"

    // Store for summary
    summaryData << [
        image: imageName,
        regionClass: className,
        regionIndex: idx + 1,
        areaMM2: areaMM2,
        totalCells: allCells.size(),
        lymphocytes: lymphocytes.size(),
        otherCells: otherCells.size(),
        lymphPercentage: lymphPercentage,
        lymphDensity: lymphDensity,
        totalDensity: totalDensity
    ]

    // Add measurements to the annotation object for export
    annotation.getMeasurements().put("Lymphocyte count", lymphocytes.size() as double)
    annotation.getMeasurements().put("Total cell count", allCells.size() as double)
    annotation.getMeasurements().put("Area mm2", areaMM2)
    annotation.getMeasurements().put("Lymphocyte density (cells/mm2)", lymphDensity)
    annotation.getMeasurements().put("Lymphocyte percentage", lymphPercentage)
    annotation.getMeasurements().put("Total cell density (cells/mm2)", totalDensity)
}

// ============================================================
// AGGREGATED SUMMARY BY CLASS
// ============================================================

println "\n=============================================="
println "AGGREGATED SUMMARY"
println "=============================================="

["Tumor", "Stroma"].each { cls ->
    def regions = summaryData.findAll { it.regionClass == cls }
    if (regions.isEmpty()) return

    def totalArea = regions.sum { it.areaMM2 }
    def totalLymph = regions.sum { it.lymphocytes }
    def totalCells = regions.sum { it.totalCells }
    def avgDensity = totalArea > 0 ? totalLymph / totalArea : 0
    def avgPercentage = totalCells > 0 ? (totalLymph * 100.0 / totalCells) : 0

    println "\n${cls.toUpperCase()}:"
    println "  Total regions:     ${regions.size()}"
    println "  Combined area:     ${String.format('%.4f', totalArea)} mm²"
    println "  Total lymphocytes: ${totalLymph}"
    println "  Total cells:       ${totalCells}"
    println "  Overall density:   ${String.format('%.0f', avgDensity)} lymphocytes/mm²"
    println "  Overall lymph %:   ${String.format('%.1f', avgPercentage)}%"
}

// Tumor vs Stroma comparison
def tumorRegions = summaryData.findAll { it.regionClass == "Tumor" }
def stromaRegions = summaryData.findAll { it.regionClass == "Stroma" }

if (!tumorRegions.isEmpty() && !stromaRegions.isEmpty()) {
    def tumorDensity = tumorRegions.sum { it.lymphocytes } / tumorRegions.sum { it.areaMM2 }
    def stromaDensity = stromaRegions.sum { it.lymphocytes } / stromaRegions.sum { it.areaMM2 }
    def ratio = stromaDensity > 0 ? tumorDensity / stromaDensity : 0

    println "\n--- TUMOR vs STROMA ---"
    println "  Tumor lymph density:  ${String.format('%.0f', tumorDensity)} cells/mm²"
    println "  Stroma lymph density: ${String.format('%.0f', stromaDensity)} cells/mm²"
    println "  Ratio (T/S):          ${String.format('%.2f', ratio)}"
}

fireHierarchyUpdate()
println "\nMeasurements added to annotation objects."
println "Next step: Run script 07 for CSV export."
