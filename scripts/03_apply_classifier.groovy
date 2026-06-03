/**
 * 03_apply_classifier.groovy
 * ============================
 * Applies a trained pixel classifier to the current image and
 * creates annotation objects from the classified regions.
 *
 * Prerequisites:
 *   - A trained pixel classifier saved in the project
 *   - Image open in QuPath
 *
 * Usage:
 *   - Single image: Script Editor → Run
 *   - All images: Script Editor → Run for project
 */

import qupath.opencv.ml.pixel.PixelClassifierTools
import qupath.lib.objects.PathObjects
import qupath.lib.roi.RoiTools

// ============================================================
// CONFIGURATION
// ============================================================

def classifierName = "tumor_classification"

// Minimum region area to keep (in µm²) — filters out tiny fragments
def minAreaUM2 = 500.0

// Whether to delete existing annotations before applying
// Set to false if you want to keep manual annotations
def clearExisting = true

// ============================================================
// APPLY CLASSIFIER
// ============================================================

def imageData = getCurrentImageData()
if (imageData == null) {
    println "ERROR: No image is open."
    return
}

println "Applying pixel classifier '${classifierName}'..."

// Load the classifier from the project
def project = getProject()
def classifier = null

try {
    classifier = project.getPixelClassifiers().get(classifierName)
    println "Classifier loaded successfully."
} catch (Exception e) {
    println "ERROR: Could not load classifier '${classifierName}'."
    println "Make sure you trained and saved it first (see script 02)."
    println "Error: ${e.message}"
    return
}

// Optionally clear existing annotations
if (clearExisting) {
    clearAnnotations()
    println "Cleared existing annotations."
}

// Apply the classifier to create annotation objects
try {
    // Create annotations from the pixel classification (returns boolean in QuPath 0.6)
    PixelClassifierTools.createAnnotationsFromPixelClassifier(
        imageData,
        classifier,
        minAreaUM2,     // minimum area threshold
        minAreaUM2      // minimum hole area
    )

    // Get the created annotations from the hierarchy
    def classifiedRegions = getAnnotationObjects().findAll {
        def cls = it.getPathClass()?.toString()
        cls == "Tumor" || cls == "Stroma"
    }

    println "Created ${classifiedRegions.size()} annotation(s) from classification."

    // Report areas
    def cal = imageData.getServer().getPixelCalibration()
    classifiedRegions.each { annotation ->
        def className = annotation.getPathClass()?.toString() ?: "Unclassified"
        def areaPixels = annotation.getROI().getArea()
        def areaMM2 = areaPixels * cal.getPixelWidth().doubleValue() * cal.getPixelHeight().doubleValue() / 1e6
        println "  ${className}: ${String.format('%.2f', areaMM2)} mm²"
    }

} catch (Exception e) {
    println "ERROR applying classifier: ${e.message}"
    e.printStackTrace()
    return
}

// Fire update
fireHierarchyUpdate()
println "\nClassifier applied successfully. Check the annotations overlay."
println "Next step: Run script 04 for cell detection."
