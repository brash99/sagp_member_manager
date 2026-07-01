from PySide6.QtWidgets import QApplication, QLabel
import sys

app = QApplication(sys.argv)

label = QLabel("SAGP Membership Manager")
label.resize(500, 120)
label.show()

sys.exit(app.exec())
