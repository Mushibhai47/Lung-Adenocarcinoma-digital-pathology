/**
 * calibration_script.groovy
 * ==========================
 * Reads Vania's circle/square annotations and matches to detected cells.
 */

import org.locationtech.jts.geom.GeometryFactory
import org.locationtech.jts.geom.Coordinate
import qupath.lib.objects.PathObjectTools

def factory = new GeometryFactory()

def allAnnotations = getAnnotationObjects()
def tumorRects     = allAnnotations.findAll { it.getPathClass()?.toString() == "Tumor" }

def circleAnnotations = allAnnotations.findAll {
    it.getROI().getClass().getSimpleName().toLowerCase().contains("ellipse")
}
def squareAnnotations = allAnnotations.findAll {
    it.getROI().getClass().getSimpleName().toLowerCase().contains("rectangle") &&
    !tumorRects.contains(it)
}

def allDetections = getDetectionObjects().findAll { it.isDetection() }

println "=== COORDINATE DEBUG ==="
println "Circles: ${circleAnnotations.size()} | Squares: ${squareAnnotations.size()} | Cells: ${allDetections.size()}"

// Print first annotation bounds
if (circleAnnotations) {
    def r = circleAnnotations[0].getROI()
    println "\nFirst circle bounds: x=${r.getBoundsX().round()}  y=${r.getBoundsY().round()}  w=${r.getBoundsWidth().round()}  h=${r.getBoundsHeight().round()}"
}
if (squareAnnotations) {
    def r = squareAnnotations[0].getROI()
    println "First square bounds: x=${r.getBoundsX().round()}  y=${r.getBoundsY().round()}  w=${r.getBoundsWidth().round()}  h=${r.getBoundsHeight().round()}"
}

// Print first 3 cell centroids
println "\nFirst 3 cell centroids:"
allDetections.take(3).each { cell ->
    println "  cx=${cell.getROI().getCentroidX().round()}  cy=${cell.getROI().getCentroidY().round()}"
}

// Try PathObjectTools approach (QuPath-native spatial lookup)
println "\n=== MATCHING CELLS TO ANNOTATIONS ==="

def tumorCells    = [] as Set
def nonTumorCells = [] as Set

circleAnnotations.each { ann ->
    def found = PathObjectTools.getObjectsForROI(null, ann.getROI(), allDetections)
    tumorCells.addAll(found)
}
squareAnnotations.each { ann ->
    def found = PathObjectTools.getObjectsForROI(null, ann.getROI(), allDetections)
    nonTumorCells.addAll(found)
}

println "Cells inside circles (TUMOR):     ${tumorCells.size()}"
println "Cells inside squares (NON-TUMOR): ${nonTumorCells.size()}"

// If still 0, try JTS geometry approach as fallback
if (tumorCells.isEmpty() && nonTumorCells.isEmpty()) {
    println "\nPathObjectTools returned 0 — trying JTS geometry fallback..."
    circleAnnotations.each { ann ->
        def geom = ann.getROI().getGeometry()
        allDetections.each { cell ->
            def pt = factory.createPoint(new Coordinate(cell.getROI().getCentroidX(), cell.getROI().getCentroidY()))
            if (geom.intersects(pt)) tumorCells << cell
        }
    }
    squareAnnotations.each { ann ->
        def geom = ann.getROI().getGeometry()
        allDetections.each { cell ->
            def pt = factory.createPoint(new Coordinate(cell.getROI().getCentroidX(), cell.getROI().getCentroidY()))
            if (geom.intersects(pt)) nonTumorCells << cell
        }
    }
    println "After JTS fallback — Tumor: ${tumorCells.size()}  Non-tumor: ${nonTumorCells.size()}"
}

def printStats = { label, cells ->
    if (cells.isEmpty()) { println "\n${label}: no cells found"; return }

    def naVals = cells.collect { getM(it.getMeasurements(), "Nucleus: Area µm^2", "Nucleus: Area µm²", "Nucleus: Area") }.findAll { it != null && !it.isNaN() }
    def ciVals = cells.collect { getM(it.getMeasurements(), "Nucleus: Circularity") }.findAll { it != null && !it.isNaN() }
    def hmVals = cells.collect { getM(it.getMeasurements(), "Hematoxylin: Nucleus: Mean", "Nucleus: Hematoxylin OD mean") }.findAll { it != null && !it.isNaN() }

    naVals.sort(); ciVals.sort(); hmVals.sort()

    println "\n--- ${label} (n=${cells.size()}) ---"
    if (naVals) println "  Nucleus Area µm²: min=${f(naVals.min())}  p25=${f(naVals[(naVals.size()*0.25).toInteger()])}  median=${f(naVals[naVals.size()/2])}  p75=${f(naVals[(naVals.size()*0.75).toInteger()])}  max=${f(naVals.max())}"
    if (ciVals) println "  Circularity:      min=${f2(ciVals.min())}  median=${f2(ciVals[ciVals.size()/2])}  max=${f2(ciVals.max())}"
    if (hmVals) println "  Hematoxylin OD:   min=${f2(hmVals.min())}  median=${f2(hmVals[hmVals.size()/2])}  max=${f2(hmVals.max())}"
}

printStats("TUMOR CELLS (circles)", tumorCells as List)
printStats("NON-TUMOR (squares)",   nonTumorCells as List)

println "\n=== DONE ==="

def getM(def m, String... names) {
    for (n in names) { if (m.containsKey(n)) return m.get(n) }
    return null
}
def f(v)  { String.format('%.1f', v) }
def f2(v) { String.format('%.3f', v) }
