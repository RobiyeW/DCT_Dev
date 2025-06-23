from PyQt5.QtWidgets import QApplication, QWidget
import sys

class DCTGui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DCT v2 GUI")
        self.resize(600, 400)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = DCTGui()
    gui.show
    sys.exit(app.exec_())
