import sys
from PyQt6.QtWidgets import QApplication
from booth_window import CowboyBooth

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CowboyBooth()
    window.show()
    sys.exit(app.exec()) 