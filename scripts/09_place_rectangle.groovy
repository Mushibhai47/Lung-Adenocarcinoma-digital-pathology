/**
 * 09_place_rectangle.groovy
 * ==========================
 * Places a fixed-size rectangle annotation at the center of the current view.
 *
 * HOW TO USE:
 *   1. Open your slide in QuPath
 *   2. Navigate to the area of interest
 *   3. Run this script — a rectangle appears at the center of your view
 *   4. Repeat for each area you want to analyze
 *   5. Save the project (Ctrl+S) when done
 *
 * To move a rectangle after placing: select it with the pointer tool and drag.
 */

import qupath.lib.objects.PathAnnotationObject
import qupath.lib.roi.RectangleROI
import qupath.lib.objects.classes.PathClassFactory

// ============================================================
// CONFIGURATION — change rectangle size here (in micrometres)
// ============================================================
def widthUM  = 70.0   // width in µm
def heightUM = 70.0   // height in µm
def className = "Tumor" // class assigned to each rectangle

// ============================================================
// PLACE RECTANGLE AT CENTER OF CURRENT VIEW
// ============================================================

def viewer = getCurrentViewer()
def imageData = getCurrentImageData()
def server = imageData.getServer()
def cal = server.getPixelCalibration()

// Get pixel size in µm
def pixelWidthUM = cal.getPixelWidth().doubleValue()
def pixelHeightUM = cal.getPixelHeight().doubleValue()

// Convert µm dimensions to pixels
def widthPx  = widthUM  / pixelWidthUM
def heightPx = heightUM / pixelHeightUM

// Get center of current view in image pixel coordinates
def centerX = viewer.getCenterPixelX()
def centerY = viewer.getCenterPixelY()

// Calculate top-left corner
def x = centerX - widthPx / 2
def y = centerY - heightPx / 2

// Create rectangle ROI and annotation
def roi = new RectangleROI(x, y, widthPx, heightPx)
def pathClass = PathClassFactory.getPathClass(className)
def annotation = new PathAnnotationObject(roi, pathClass)

// Add to image
addObject(annotation)
fireHierarchyUpdate()

println "Rectangle placed at center (${Math.round(centerX)}, ${Math.round(centerY)}) — ${widthUM}x${heightUM} µm — class: ${className}"
println "Navigate to next area and run again to place another rectangle."
