/**
 * export_labels.groovy
 * Exports the label image from every slide in the project.
 * Run with: Run for project
 * Output: one PNG per slide saved to Desktop/slide_labels/
 */

import qupath.lib.gui.QuPathGUI
import javax.imageio.ImageIO
import java.awt.image.BufferedImage

def outputDir = new File(System.getProperty("user.home"), "Desktop/slide_labels")
outputDir.mkdirs()

def imageData = getCurrentImageData()
def server    = imageData.getServer()
def slideName = server.getMetadata().getName()

// Extract slide ID (e.g. R1-S7)
def slideId = slideName.replaceAll(".*-(R\\d+-S\\d+)\\.mrxs", "\$1")

try {
    def associatedImages = server.getAssociatedImageList()
    if (associatedImages.contains("label")) {
        def labelServer = server.getAssociatedImage("label")
        def img = labelServer.readRegion(1.0, 0, 0, labelServer.getWidth(), labelServer.getHeight())
        def outFile = new File(outputDir, "${slideId}.png")
        ImageIO.write(img, "PNG", outFile)
        println "Saved: ${outFile.name}"
    } else {
        println "No label found for: ${slideId}"
    }
} catch (Exception e) {
    println "ERROR for ${slideId}: ${e.getMessage()}"
}
