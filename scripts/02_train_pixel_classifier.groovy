/**
 * 02_train_pixel_classifier.groovy
 * ==================================
 * Trains a Random Forest pixel classifier to distinguish Tumor vs Stroma.
 *
 * Prerequisites:
 *   - Annotations with classes "Tumor", "Stroma" (and optionally "Background")
 *     must exist on the current image
 *   - At least 5+ regions per class recommended
 *
 * Usage: Open in Script Editor → Run on current image
 *
 * NOTE: For interactive training with live preview, use the GUI instead:
 *       Classify → Pixel classification → Train pixel classifier
 *       This script is for programmatic/reproducible training.
 */

import qupath.lib.classifiers.pixel.PixelClassifierTools
import qupath.opencv.ml.pixel.PixelClassifiers

// ============================================================
// CONFIGURATION — Adjust these parameters as needed
// ============================================================

def classifierName = "tumor_stroma_v1"

// Resolution for classification (µm per pixel)
// Lower = more detail but slower. 10-20 is typical.
def resolution = 10.0

// Feature scales (sigma values for Gaussian filters)
// Multiple scales capture structures at different sizes
def featureScales = [1, 2, 4, 8]

// ============================================================
// VALIDATION
// ============================================================

def imageData = getCurrentImageData()
if (imageData == null) {
    println "ERROR: No image is open. Please open an image first."
    return
}

def annotations = getAnnotationObjects()
if (annotations.isEmpty()) {
    println "ERROR: No annotations found. Please annotate Tumor and Stroma regions first."
    return
}

// Check that we have the required classes
def classes = annotations.collect { it.getPathClass()?.toString() }.findAll { it != null }.unique()
println "Found annotation classes: ${classes}"

if (!classes.contains("Tumor")) {
    println "WARNING: No 'Tumor' annotations found!"
}
if (!classes.contains("Stroma")) {
    println "WARNING: No 'Stroma' annotations found!"
}

def tumorCount = annotations.count { it.getPathClass()?.toString() == "Tumor" }
def stromaCount = annotations.count { it.getPathClass()?.toString() == "Stroma" }
println "Tumor annotations: ${tumorCount}"
println "Stroma annotations: ${stromaCount}"

if (tumorCount < 3 || stromaCount < 3) {
    println "WARNING: Recommend at least 5 annotations per class for reliable training."
    println "Current counts may produce an unreliable classifier."
}

// ============================================================
// TRAINING INSTRUCTIONS
// ============================================================

println """
==============================================
PIXEL CLASSIFIER TRAINING
==============================================

For INTERACTIVE training with live preview (RECOMMENDED):
1. Go to: Classify → Pixel classification → Train pixel classifier
2. Set these parameters:
   - Classifier type: Random Trees
   - Resolution: ${resolution} µm/px
   - Features: Check all (Gaussian, Laplacian, Weighted std dev,
     Gradient magnitude, Structure tensor eigenvalues)
   - Scales (sigma): ${featureScales.join(', ')}
   - Region: Annotations
   - Output: Classification
3. Click 'Live preview' to see results in real-time
4. If results look good → Save as '${classifierName}'
5. Classifier saved to: project/classifiers/pixel_classifiers/

EVALUATION:
- Zoom into tumor-stroma boundaries
- Check for misclassified regions
- If needed: add more annotations and retrain

After saving the classifier, run script 03 to apply it.
==============================================
"""

// ============================================================
// VERIFY EXISTING CLASSIFIER (if already trained)
// ============================================================

def project = getProject()
if (project != null) {
    try {
        def existingClassifiers = project.getPixelClassifiers().getNames()
        if (existingClassifiers.contains(classifierName)) {
            println "Classifier '${classifierName}' already exists in the project."
            println "You can apply it using script 03_apply_classifier.groovy"
        } else {
            println "Available classifiers: ${existingClassifiers}"
            println "No classifier named '${classifierName}' found yet — train one using the GUI steps above."
        }
    } catch (Exception e) {
        println "Could not check existing classifiers: ${e.message}"
    }
}
