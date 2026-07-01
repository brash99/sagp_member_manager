from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QComboBox,
    QPushButton,
    QSplitter,
    QTableView,
    QMenuBar,
    QStatusBar,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SAGP Membership Manager")
        self.resize(1400, 800)

        self._create_menu()
        self._create_statusbar()
        self._build_ui()

    def _create_menu(self):
        menu = self.menuBar()

        menu.addMenu("&File")
        menu.addMenu("&Members")
        menu.addMenu("&Reports")
        menu.addMenu("&Help")

    def _create_statusbar(self):
        status = QStatusBar()
        status.showMessage("Ready")
        self.setStatusBar(status)

    def _build_ui(self):

        #
        # ----- Central Widget -----
        #

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        #
        # ----- Search Bar -----
        #

        search_layout = QHBoxLayout()

        search_layout.addWidget(QLabel("Search:"))

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Search name, institution, email..."
        )

        search_layout.addWidget(self.search_edit)

        self.clear_button = QPushButton("Clear")
        search_layout.addWidget(self.clear_button)

        main_layout.addLayout(search_layout)

        #
        # ----- Splitter -----
        #

        splitter = QSplitter(Qt.Horizontal)

        #
        # LEFT SIDE
        #

        self.member_table = QTableView()

        splitter.addWidget(self.member_table)

        #
        # RIGHT SIDE
        #

        right_widget = QWidget()

        form = QFormLayout(right_widget)

        self.display_name = QLineEdit()
        self.first_name = QLineEdit()
        self.last_name = QLineEdit()

        self.institution = QLineEdit()

        self.primary_email = QLineEdit()

        self.membership_status = QComboBox()
        self.membership_status.addItems(
            [
                "Current Paid Member",
                "Current Unpaid Member",
                "Past Member",
                "Associate Member",
                "Executive Member",
                "Honorary Member",
                "Unknown",
            ]
        )

        self.region = QComboBox()
        self.region.addItems(
            [
                "",
                "PA",
                "NJ",
                "NY",
                "Canada",
                "World",
                "Other",
            ]
        )

        self.notes = QPlainTextEdit()

        #
        # Read only for now
        #

        widgets = [
            self.display_name,
            self.first_name,
            self.last_name,
            self.institution,
            self.primary_email,
            self.membership_status,
            self.region,
            self.notes,
        ]

        for w in widgets:
            w.setEnabled(False)

        form.addRow("Display Name", self.display_name)
        form.addRow("First Name", self.first_name)
        form.addRow("Last Name", self.last_name)
        form.addRow("Institution", self.institution)
        form.addRow("Primary Email", self.primary_email)
        form.addRow("Membership Status", self.membership_status)
        form.addRow("Region", self.region)
        form.addRow("Notes", self.notes)

        self.save_button = QPushButton("Save")
        self.save_button.setEnabled(False)

        form.addRow(self.save_button)

        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)
