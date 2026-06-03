/**
 * 07_export_results.groovy
 * ==========================
 * Exports all quantification results to CSV files.
 *
 * Generates:
 *   1. Per-region results (one row per Tumor/Stroma annotation)
 *   2. Per-image summary (one row per image with aggregated stats)
 *   3. Per-cell data (detailed cell measurements — optional, can be large)
 *
 * Prerequisites:
 *   - Full pipeline completed (scripts 01-06)
 *
 * Usage:
 *   - Run for project: Script Editor → Run for project
 *     (this processes all images and appends to the CSV)
 */

import qupath.lib.gui.QuPathGUI

// ============================================================
// CONFIGURATION
// ============================================================

// Output directory — change this to your desired export location
def outputDir = buildFilePath(PROJECT_BASE_DIR, "output", "csv")
mkdirs(outputDir)

// Whether to export individual cell measurements (WARNING: can be very large)
def exportCellData = false

// Separator for CSV
def sep = ","

// ============================================================
// GATHER DATA
// ============================================================

def imageData = getCurrentImageData()
if (imageData == null) {
    println "ERROR: No image is open."
    return
}

def server = imageData.getServer()
def cal = server.getPixelCalibration()
def imageName = server.getMetadata().getName()
// Clean up image name for use in filenames
def cleanName = imageName.replaceAll('[^a-zA-Z0-9_.-]', '_')

def annotations = getAnnotationObjects().findAll {
    def cls = it.getPathClass()?.toString()
    cls == "Tumor" || cls == "Stroma"
}

if (annotations.isEmpty()) {
    println "WARNING: No Tumor/Stroma annotations found for ${imageName}. Skipping."
    return
}

// ============================================================
// 1. PER-REGION EXPORT
// ============================================================

def regionFile = new File(outputDir, "region_results.csv")
def writeHeader = !regionFile.exists() || regionFile.length() == 0

def regionWriter = regionFile.newWriter(true) // append mode

if (writeHeader) {
    regionWriter.writeLine([
        "Image",
        "Region_Class",
        "Region_Index",
        "Area_mm2",
        "Total_Cells",
        "Lymphocytes",
        "Other_Cells",
        "Lymphocyte_Percentage",
        "Lymphocyte_Density_per_mm2",
        "Total_Cell_Density_per_mm2"
    ].join(sep))
}

annotations.eachWithIndex { annotation, idx ->
    def className = annotation.getPathClass()?.toString()

    def areaPixels = annotation.getROI().getArea()
    def pixelWidthMM = cal.getPixelWidth().doubleValue() / 1000.0
    def pixelHeightMM = cal.getPixelHeight().doubleValue() / 1000.0
    def areaMM2 = areaPixels * pixelWidthMM * pixelHeightMM

    def allCells = annotation.getChildObjects().findAll { it.isDetection() }
    def lymphocytes = allCells.findAll { it.getPathClass()?.toString() == "Lymphocyte" }
    def otherCells = allCells.size() - lymphocytes.size()

    def lymphDensity = areaMM2 > 0 ? lymphocytes.size() / areaMM2 : 0.0
    def totalDensity = areaMM2 > 0 ? allCells.size() / areaMM2 : 0.0
    def lymphPct = allCells.size() > 0 ? (lymphocytes.size() * 100.0 / allCells.size()) : 0.0

    regionWriter.writeLine([
        "\"${imageName}\"",
        className,
        idx + 1,
        String.format('%.6f', areaMM2),
        allCells.size(),
        lymphocytes.size(),
        otherCells,
        String.format('%.2f', lymphPct),
        String.format('%.2f', lymphDensity),
        String.format('%.2f', totalDensity)
    ].join(sep))
}

regionWriter.close()
println "Region results written to: ${regionFile.getAbsolutePath()}"

// ============================================================
// 2. PER-IMAGE SUMMARY EXPORT
// ============================================================

def summaryFile = new File(outputDir, "image_summary.csv")
def writeSummaryHeader = !summaryFile.exists() || summaryFile.length() == 0

def summaryWriter = summaryFile.newWriter(true) // append mode

if (writeSummaryHeader) {
    summaryWriter.writeLine([
        "Image",
        "Tumor_Area_mm2",
        "Stroma_Area_mm2",
        "Total_Area_mm2",
        "Tumor_Stroma_Ratio",
        "Tumor_Total_Cells",
        "Tumor_Lymphocytes",
        "Tumor_Lymph_Density_per_mm2",
        "Tumor_Lymph_Percentage",
        "Stroma_Total_Cells",
        "Stroma_Lymphocytes",
        "Stroma_Lymph_Density_per_mm2",
        "Stroma_Lymph_Percentage",
        "Overall_Lymphocytes",
        "Overall_Lymph_Density_per_mm2",
        "Intratumoral_vs_Stromal_Ratio"
    ].join(sep))
}

// Aggregate by class
def tumorAnns = annotations.findAll { it.getPathClass()?.toString() == "Tumor" }
def stromaAnns = annotations.findAll { it.getPathClass()?.toString() == "Stroma" }

def calcStats = { anns ->
    def totalArea = 0.0
    def totalCells = 0
    def totalLymph = 0

    anns.each { ann ->
        def areaPixels = ann.getROI().getArea()
        def pixelWidthMM = cal.getPixelWidth().doubleValue() / 1000.0
        def pixelHeightMM = cal.getPixelHeight().doubleValue() / 1000.0
        totalArea += areaPixels * pixelWidthMM * pixelHeightMM

        def cells = ann.getChildObjects().findAll { it.isDetection() }
        totalCells += cells.size()
        totalLymph += cells.findAll { it.getPathClass()?.toString() == "Lymphocyte" }.size()
    }

    return [
        area: totalArea,
        cells: totalCells,
        lymph: totalLymph,
        density: totalArea > 0 ? totalLymph / totalArea : 0.0,
        pct: totalCells > 0 ? (totalLymph * 100.0 / totalCells) : 0.0
    ]
}

def tumorStats = calcStats(tumorAnns)
def stromaStats = calcStats(stromaAnns)
def totalArea = tumorStats.area + stromaStats.area
def tsRatio = stromaStats.area > 0 ? tumorStats.area / stromaStats.area : 0.0
def overallLymph = tumorStats.lymph + stromaStats.lymph
def overallDensity = totalArea > 0 ? overallLymph / totalArea : 0.0
def itRatio = stromaStats.density > 0 ? tumorStats.density / stromaStats.density : 0.0

summaryWriter.writeLine([
    "\"${imageName}\"",
    String.format('%.6f', tumorStats.area),
    String.format('%.6f', stromaStats.area),
    String.format('%.6f', totalArea),
    String.format('%.4f', tsRatio),
    tumorStats.cells,
    tumorStats.lymph,
    String.format('%.2f', tumorStats.density),
    String.format('%.2f', tumorStats.pct),
    stromaStats.cells,
    stromaStats.lymph,
    String.format('%.2f', stromaStats.density),
    String.format('%.2f', stromaStats.pct),
    overallLymph,
    String.format('%.2f', overallDensity),
    String.format('%.4f', itRatio)
].join(sep))

summaryWriter.close()
println "Image summary written to: ${summaryFile.getAbsolutePath()}"

// ============================================================
// 3. PER-CELL EXPORT (Optional)
// ============================================================

if (exportCellData) {
    def cellFile = new File(outputDir, "cell_data_${cleanName}.csv")
    def cellWriter = cellFile.newWriter(false)

    // Header
    cellWriter.writeLine([
        "Image",
        "Region_Class",
        "Cell_Class",
        "Centroid_X",
        "Centroid_Y",
        "Nucleus_Area_um2",
        "Nucleus_Circularity",
        "Hematoxylin_Mean"
    ].join(sep))

    annotations.each { annotation ->
        def regionClass = annotation.getPathClass()?.toString()
        def cells = annotation.getChildObjects().findAll { it.isDetection() }

        cells.each { cell ->
            def roi = cell.getROI()
            def m = cell.getMeasurements()

            cellWriter.writeLine([
                "\"${imageName}\"",
                regionClass,
                cell.getPathClass()?.toString() ?: "Unclassified",
                String.format('%.1f', roi.getCentroidX()),
                String.format('%.1f', roi.getCentroidY()),
                String.format('%.2f', m.getOrDefault("Nucleus: Area µm^2", Double.NaN)),
                String.format('%.4f', m.getOrDefault("Nucleus: Circularity", Double.NaN)),
                String.format('%.4f', m.getOrDefault("Hematoxylin: Nucleus: Mean", Double.NaN))
            ].join(sep))
        }
    }

    cellWriter.close()
    println "Cell data written to: ${cellFile.getAbsolutePath()}"
}

println "\n--- Export complete for: ${imageName} ---"
