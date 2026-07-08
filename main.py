import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from database import Database
from views.main_window import MainWindow


def default_database_path():
    """Use the Membership Manager live operational database by default.

    sagp_member_import creates a bootstrap/import database from historical CSVs.
    Once sagp_member_manager is used to edit records, the manager database is
    the authoritative operational database.
    """
    candidates = [
        Path("sagp_member_manager/output/sagp_members.db"),
        Path("output/sagp_members.db"),
        Path("sagp_member_import/output/sagp_members.db"),
        Path("../sagp_member_import/output/sagp_members.db"),
        Path("sagp_member_db/output/sagp_members.db"),      # compatibility alias
        Path("../sagp_member_db/output/sagp_members.db"),   # compatibility alias
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(candidates[0])

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="SAGP Membership Manager")
    parser.add_argument(
        "database",
        nargs="?",
        default=None,
        help="Path to the canonical App 2 SQLite database",
    )
    parser.add_argument(
        "--db",
        dest="database_option",
        default=None,
        help="Path to the canonical App 2 SQLite database",
    )
    args = parser.parse_args(argv)
    args.database = args.database_option or args.database or default_database_path()
    return args


def main(argv=None):
    args = parse_args(argv)

    app = QApplication(sys.argv if argv is None else [sys.argv[0], *argv])

    db = Database(Path(args.database))
    window = MainWindow(db)
    window.show()

    exit_code = app.exec()
    db.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
