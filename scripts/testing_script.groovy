/**
 * testing_script.groovy
 * ==============================
 * Diagnostic — prints actual measurement values for detected cells.
 * Run AFTER cell detection to see real nucleus area, circularity,
 * and hematoxylin OD values so thresholds can be calibrated.
 *
 * Usage: Run on current image (not for project)
 */

def cells = getDetectionObjects().findAll { it.isDetection() }
println "Total cells: ${cells.size()}"
def byClass = cells.groupBy { it.getPathClass()?.toString() ?: "Unclassified" }
byClass.each { cls, list -> println "  ${cls}: ${list.size()}" }

if (cells.isEmpty()) {
    println "No cells detected. Run cell detection first."
    return
}

println "\n--- Sample measurements (first 20 cells) ---"
cells.take(20).each { cell ->
    def m  = cell.getMeasurements()
    def na = getM(m, "Nucleus: Area µm^2", "Nucleus: Area µm²", "Nucleus: Area")
    def ci = getM(m, "Nucleus: Circularity")
    def hm = getM(m, "Hematoxylin: Nucleus: Mean", "Nucleus: Hematoxylin OD mean")
    def ca = getM(m, "Cell: Area µm^2", "Cell: Area µm²", "Cell: Area")
    def ratio = (ca != null && na != null && na > 0) ? ca / na : null

    println "[${cell.getPathClass()}] " +
            "NucArea=${String.format('%.1f', na ?: 0)}  " +
            "Circ=${String.format('%.2f', ci ?: 0)}  " +
            "HemaOD=${String.format('%.3f', hm ?: 0)}  " +
            "CellArea=${String.format('%.1f', ca ?: 0)}  " +
            "CellNucRatio=${ratio != null ? String.format('%.2f', ratio) : 'N/A'}"
}

// Summary statistics
println "\n--- Statistics across all cells ---"
def naValues = cells.collect {
    getM(it.getMeasurements(), "Nucleus: Area µm^2", "Nucleus: Area µm²", "Nucleus: Area")
}.findAll { it != null && !it.isNaN() }

def ciValues = cells.collect {
    getM(it.getMeasurements(), "Nucleus: Circularity")
}.findAll { it != null && !it.isNaN() }

def hmValues = cells.collect {
    getM(it.getMeasurements(), "Hematoxylin: Nucleus: Mean", "Nucleus: Hematoxylin OD mean")
}.findAll { it != null && !it.isNaN() }

if (naValues) {
    naValues.sort()
    println "Nucleus Area µm²  — min: ${String.format('%.1f', naValues.min())}  " +
            "max: ${String.format('%.1f', naValues.max())}  " +
            "median: ${String.format('%.1f', naValues[naValues.size()/2])}  " +
            "p10: ${String.format('%.1f', naValues[(naValues.size()*0.10).toInteger()])}  " +
            "p90: ${String.format('%.1f', naValues[(naValues.size()*0.90).toInteger()])}"
}

if (ciValues) {
    ciValues.sort()
    println "Circularity       — min: ${String.format('%.2f', ciValues.min())}  " +
            "max: ${String.format('%.2f', ciValues.max())}  " +
            "median: ${String.format('%.2f', ciValues[ciValues.size()/2])}"
}

if (hmValues) {
    hmValues.sort()
    println "Hematoxylin OD    — min: ${String.format('%.3f', hmValues.min())}  " +
            "max: ${String.format('%.3f', hmValues.max())}  " +
            "median: ${String.format('%.3f', hmValues[hmValues.size()/2])}  " +
            "p10: ${String.format('%.3f', hmValues[(hmValues.size()*0.10).toInteger()])}  " +
            "p90: ${String.format('%.3f', hmValues[(hmValues.size()*0.90).toInteger()])}"
}

println "\nDone. Use these values to set thresholds in script 10."

def getM(def m, String... names) {
    for (n in names) { if (m.containsKey(n)) return m.get(n) }
    return null
}
