from PySide6.QtCore import Qt, QSignalBlocker
from models.member_table_model import MemberTableModel
from models.member import Member
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QComboBox,
    QPushButton,
    QSplitter,
    QTableView,
    QStatusBar,
    QHeaderView,
)


def display(value):
    return "" if value is None else str(value)


def clean_text(value):
    """Convert blank UI text back to NULL-friendly Python values."""
    value = value.strip()
    return value if value else None


class MainWindow(QMainWindow):
    """Main App 3 window.

    This class intentionally talks to the database only through the SagpDatabase
    API.  It should not import sqlite3 or issue SQL directly.
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)

        self.db = db
        self.members = self.db.list_members()
        self.current_member = None
        self._loading_member_details = False
        self._details_dirty = False

        self.setWindowTitle("SAGP Membership Manager")
        self.resize(1400, 800)

        self._create_menu()
        self._create_statusbar()
        self._build_ui()
        self._connect_signals()
        self._select_first_member()

    def _create_menu(self):
        menu = self.menuBar()
        menu.addMenu("&File")
        menu.addMenu("&Members")
        menu.addMenu("&Reports")
        menu.addMenu("&Help")

    def _create_statusbar(self):
        status = QStatusBar()
        summary = self.db.get_summary()
        status.showMessage(
            f"Ready — {summary.member_count:,} members loaded; "
            f"{summary.source_appearance_count:,} source appearances; "
            f"{summary.membership_code_history_count:,} code-history rows"
        )
        self.setStatusBar(status)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Search name, institution, email, region, status, code..."
        )
        search_layout.addWidget(self.search_edit)

        self.clear_button = QPushButton("Clear")
        search_layout.addWidget(self.clear_button)
        main_layout.addLayout(search_layout)

        splitter = QSplitter(Qt.Horizontal)

        self.member_table = QTableView()
        self.model = MemberTableModel(self.members)
        self.member_table.setModel(self.model)

        header = self.member_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.member_table.setAlternatingRowColors(True)
        self.member_table.setSortingEnabled(True)
        self.member_table.sortByColumn(1, Qt.AscendingOrder)
        self.member_table.setSelectionBehavior(QTableView.SelectRows)
        self.member_table.setSelectionMode(QTableView.SingleSelection)

        splitter.addWidget(self.member_table)

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
                "",
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
        self.region.addItems(["", "PA", "NJ", "NY", "Canada", "World", "Other"])

        self.source_appearances = QPlainTextEdit()
        self.code_history = QPlainTextEdit()
        self.notes = QPlainTextEdit()

        editable_widgets = [
            self.display_name,
            self.first_name,
            self.last_name,
            self.institution,
            self.primary_email,
            self.membership_status,
            self.region,
            self.notes,
        ]
        for widget in editable_widgets:
            widget.setEnabled(False)

        self.source_appearances.setReadOnly(True)
        self.code_history.setReadOnly(True)
        self.source_appearances.setPlaceholderText("Read-only provenance from App 2")
        self.code_history.setPlaceholderText("Read-only membership-code history from App 2")

        form.addRow("Display Name", self.display_name)
        form.addRow("First Name", self.first_name)
        form.addRow("Last Name", self.last_name)
        form.addRow("Institution", self.institution)
        form.addRow("Primary Email", self.primary_email)
        form.addRow("Membership Status", self.membership_status)
        form.addRow("Region", self.region)
        form.addRow("Source Appearances", self.source_appearances)
        form.addRow("Code History", self.code_history)
        form.addRow("Notes", self.notes)

        self.save_button = QPushButton("Save")
        self.save_button.setEnabled(False)
        form.addRow(self.save_button)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)

    def _connect_signals(self):
        self.search_edit.textChanged.connect(self._refresh_member_list)
        self.clear_button.clicked.connect(self.search_edit.clear)
        self.member_table.selectionModel().currentRowChanged.connect(
            self._on_current_row_changed
        )
        self.save_button.clicked.connect(self._save_current_member)

        for widget in [
            self.display_name,
            self.first_name,
            self.last_name,
            self.institution,
            self.primary_email,
        ]:
            widget.textEdited.connect(self._mark_details_dirty)

        self.notes.textChanged.connect(self._mark_details_dirty)
        self.membership_status.currentTextChanged.connect(self._mark_details_dirty)
        self.region.currentTextChanged.connect(self._mark_details_dirty)

    def _refresh_member_list(self):
        text = self.search_edit.text()
        self.members = self.db.search_members(text)
        self.model.set_members(self.members)
        self.statusBar().showMessage(
            f"Showing {len(self.members):,} matching members"
        )
        self._select_first_member()

    def _select_first_member(self):
        if self.model.rowCount() == 0:
            self._populate_member_details(None)
            return
        self.member_table.selectRow(0)
        self._populate_member_details(self.model.member_at(0))

    def _on_current_row_changed(self, current, previous):
        if not current.isValid():
            self._populate_member_details(None)
            return
        self._populate_member_details(self.model.member_at(current.row()))

    def _populate_member_details(self, member):
        self.current_member = member
        self._loading_member_details = True

        editable_widgets = [
            self.display_name,
            self.first_name,
            self.last_name,
            self.institution,
            self.primary_email,
            self.membership_status,
            self.region,
            self.notes,
        ]

        if member is None:
            for widget in editable_widgets:
                widget.setEnabled(False)

            self.display_name.clear()
            self.first_name.clear()
            self.last_name.clear()
            self.institution.clear()
            self.primary_email.clear()
            self.membership_status.setCurrentText("")
            self.region.setCurrentText("")
            self.source_appearances.clear()
            self.code_history.clear()
            self.notes.clear()
            self._loading_member_details = False
            self._set_details_dirty(False)
            return

        for widget in editable_widgets:
            widget.setEnabled(True)

        # Block signals while loading database values so we do not mark the form
        # dirty merely because a new row was selected.
        blockers = [QSignalBlocker(widget) for widget in editable_widgets]
        try:
            self.display_name.setText(display(member.display_name))
            self.first_name.setText(display(member.first_name))
            self.last_name.setText(display(member.last_name))
            self.institution.setText(display(member.institution))
            self.primary_email.setText(display(member.primary_email))
            self.membership_status.setCurrentText(display(member.membership_status))
            self.region.setCurrentText(display(member.region))
            self.notes.setPlainText(display(member.notes))
        finally:
            del blockers

        appearances = self.db.get_source_appearances(member.person_id)
        self.source_appearances.setPlainText(
            "\n".join(a.source_file for a in appearances)
        )

        code_history = self.db.get_membership_code_history(member.person_id)
        self.code_history.setPlainText("\n".join(entry.code for entry in code_history))

        self._loading_member_details = False
        self._set_details_dirty(False)

    def _mark_details_dirty(self, *args):
        if self._loading_member_details or self.current_member is None:
            return
        self._set_details_dirty(True)

    def _set_details_dirty(self, dirty):
        self._details_dirty = dirty
        self.save_button.setEnabled(dirty and self.current_member is not None)

    def _member_from_form(self):
        """Build a full Member object, preserving non-visible fields."""

        member = self.current_member
        if member is None:
            return None

        return Member(
            person_id=member.person_id,
            display_name=self.display_name.text().strip() or member.display_name,
            title=member.title,
            first_name=clean_text(self.first_name.text()),
            middle_name=member.middle_name,
            last_name=clean_text(self.last_name.text()),
            suffix=member.suffix,
            institution=clean_text(self.institution.text()),
            primary_email=clean_text(self.primary_email.text()),
            secondary_email=member.secondary_email,
            phone=member.phone,
            address1=member.address1,
            address2=member.address2,
            city=member.city,
            state_province=member.state_province,
            postal_code=member.postal_code,
            country=member.country,
            region=clean_text(self.region.currentText()),
            membership_status=clean_text(self.membership_status.currentText()),
            original_membership_code=member.original_membership_code,
            member_since=member.member_since,
            last_paid_year=member.last_paid_year,
            active=member.active,
            notes=clean_text(self.notes.toPlainText()),
            created_at=member.created_at,
            updated_at=member.updated_at,
        )

    def _save_current_member(self):
        updated_member = self._member_from_form()
        if updated_member is None:
            return

        try:
            self.db.update_member(updated_member)
            refreshed_member = self.db.get_member(updated_member.person_id) or updated_member
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Could not save member record:\n\n{exc}",
            )
            return

        self.current_member = refreshed_member
        self.model.update_member(refreshed_member)
        self._set_details_dirty(False)
        self.statusBar().showMessage(
            f"Saved {display(refreshed_member.display_name)}", 5000
        )
