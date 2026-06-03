import qupath.lib.gui.QuPathGUI
import javax.imageio.ImageIO
import java.awt.image.BufferedImage

// Output folder on Desktop
def desktop = new File(System.getProperty("user.home"), "Desktop")
def outputDir = new File(desktop, "slide_labels")
outputDir.mkdirs()

def imageData = getCurrentImageData()
def server = imageData.getServer()
def name = server.getMetadata().getName()

// Get slide ID from name (e.g. R1-S7)
def slideId = name.replaceAll(/.*-(R\d+-S\d+)\.mrxs.*/, '$1')
if (slideId == name) slideId = name.replace(".mrxs", "")

def outFile = new File(outputDir, slideId + ".png")

// Skip if already done
if (outFile.exists()) {
    println "Already done: ${slideId}"
    return
}

try {
    def associated = server.getAssociatedImageList()
    if (!associated.contains("label")) {
        println "No label: ${slideId}"
        return
    }
    def labelServer = server.getAssociatedImage("label")
    def request = qupath.lib.regions.RegionRequest.createInstance(
        labelServer.getPath(), 1.0, 0, 0,
        labelServer.getWidth(), labelServer.getHeight()
    )
    def img = labelServer.readRegion(request)
    ImageIO.write(img, "PNG", outFile)
    println "Saved: ${slideId}.png"
} catch (Exception e) {
    println "Error ${slideId}: ${e.message}"
}
