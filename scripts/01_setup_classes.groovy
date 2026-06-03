/**
 * 01_setup_classes.groovy
 * ========================
 * Sets up annotation classes for the project.
 * Run this ONCE when starting a new project.
 *
 * Classes: Tumor, Stroma, Background, Ignore*
 *
 * Usage: Open in Script Editor → Run
 */

import qupath.lib.objects.classes.PathClass

// Define the annotation classes with colors
def classList = [
    ["Tumor",      getColorRGB(200, 50, 50)],    // Red
    ["Stroma",     getColorRGB(50, 150, 50)],     // Green
    ["Background", getColorRGB(180, 180, 180)],   // Gray
    ["Ignore*",    getColorRGB(120, 120, 120)],    // Dark gray
    ["Lymphocyte", getColorRGB(50, 50, 200)]       // Blue
]

classList.each { name, color ->
    def pathClass = PathClass.fromString(name)
    if (color != null) {
        pathClass = PathClass.fromString(name, color)
    }
    println "Class defined: ${name}"
}

println "\n--- Annotation classes are ready ---"
println "How to use:"
println "1. Select a class in the Annotations tab (left panel)"
println "2. Use Brush (B) or Polygon (P) tool to draw"
println "3. The annotation will automatically get the selected class"


// Helper function for RGB color
int getColorRGB(int r, int g, int b) {
    return (r << 16) | (g << 8) | b
}
