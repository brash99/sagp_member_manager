"""Stable App 3 database API for the frozen SAGP SQLite contract.

This module is the intentional boundary between the GUI and the App 2 database.
Qt widgets and other App 3 features should call this API instead of issuing SQL
against sqlite3 directly.  That keeps the App 2 -> App 3 contract small, named,
and testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterable

from models.member import Member


REQUIRED_TABLES = {
    "members",
    "source_appearances",
    "membership_code_history",
    "schema_info",
    "import_log",
}

REQUIRED_MEMBER_COLUMNS = {
    "person_id",
    "display_name",
    "title",
    "first_name",
    "middle_name",
    "last_name",
    "suffix",
    "institution",
    "primary_email",
    "secondary_email",
    "phone",
    "address1",
    "address2",
    "city",
    "state_province",
    "postal_code",
    "country",
    "region",
    "membership_status",
    "original_membership_code",
    "member_since",
    "last_paid_year",
    "active",
    "notes",
    "created_at",
    "updated_at",
}

MEMBER_ORDER_BY = """
    lower(coalesce(last_name, display_name)),
    lower(coalesce(first_name, '')),
    lower(coalesce(middle_name, '')),
    lower(person_id)
"""


@dataclass(frozen=True)
class DatabaseSummary:
    """Small health/overview object for status bars and future dashboards."""

    member_count: int
    source_appearance_count: int
    membership_code_history_count: int
    schema_version: str | None = None
    app_name: str | None = None
    created_at: str | None = None


@dataclass(frozen=True)
class SourceAppearance:
    person_id: str
    source_file: str


@dataclass(frozen=True)
class MembershipCodeHistoryEntry:
    person_id: str
    code: str


class SagpDatabase:
    """Named API for App 3 access to the canonical App 2 SQLite database."""

    def __init__(self, filename: str | Path):
        self.filename = str(filename)
        if not Path(self.filename).exists():
            raise FileNotFoundError(
                f"SAGP database not found: {self.filename}. "
                "Build it with App 2 or pass a database path to main.py."
            )

        self.conn = sqlite3.connect(self.filename)
        self.conn.row_factory = sqlite3.Row
        self.validate_schema()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "SagpDatabase":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Contract / health checks
    # ------------------------------------------------------------------

    def validate_schema(self) -> None:
        """Fail loudly if this is not an App 2 database App 3 can use."""

        tables = self._table_names()
        missing_tables = sorted(REQUIRED_TABLES - tables)
        if missing_tables:
            raise RuntimeError(
                "This database does not match the frozen SAGP App 2/App 3 contract. "
                f"Missing tables: {missing_tables}"
            )

        columns = {row[1] for row in self.conn.execute("PRAGMA table_info(members)")}
        missing_columns = sorted(REQUIRED_MEMBER_COLUMNS - columns)
        if missing_columns:
            raise RuntimeError(
                "This database does not match the frozen SAGP App 2/App 3 contract. "
                f"Missing members columns: {missing_columns}"
            )

    def get_summary(self) -> DatabaseSummary:
        schema_info = self.get_schema_info()
        return DatabaseSummary(
            member_count=self.count_members(),
            source_appearance_count=self._count_rows("source_appearances"),
            membership_code_history_count=self._count_rows("membership_code_history"),
            schema_version=schema_info.get("schema_version"),
            app_name=schema_info.get("app_name"),
            created_at=schema_info.get("created_at"),
        )

    def get_schema_info(self) -> dict[str, str]:
        rows = self.conn.execute("SELECT key, value FROM schema_info").fetchall()
        return {row["key"]: row["value"] for row in rows}

    # ------------------------------------------------------------------
    # Member read API
    # ------------------------------------------------------------------

    def count_members(self) -> int:
        return self._count_rows("members")

    def list_members(self, limit: int | None = None, offset: int = 0) -> list[Member]:
        sql = f"SELECT * FROM members ORDER BY {MEMBER_ORDER_BY}"
        params: list[int] = []
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        rows = self.conn.execute(sql, params).fetchall()
        return [self._row_to_member(row) for row in rows]

    def get_member(self, person_id: str) -> Member | None:
        row = self.conn.execute(
            "SELECT * FROM members WHERE person_id = ?", (person_id,)
        ).fetchone()
        return None if row is None else self._row_to_member(row)

    def search_members(self, text: str, limit: int | None = None) -> list[Member]:
        text = (text or "").strip()
        if not text:
            return self.list_members(limit=limit)

        pattern = f"%{text}%"
        sql = f"""
            SELECT *
            FROM members
            WHERE display_name LIKE ?
               OR institution LIKE ?
               OR primary_email LIKE ?
               OR secondary_email LIKE ?
               OR last_name LIKE ?
               OR first_name LIKE ?
               OR city LIKE ?
               OR state_province LIKE ?
               OR country LIKE ?
               OR region LIKE ?
               OR membership_status LIKE ?
               OR original_membership_code LIKE ?
            ORDER BY {MEMBER_ORDER_BY}
        """
        params: list[str | int] = [pattern] * 12
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [self._row_to_member(row) for row in rows]

    # ------------------------------------------------------------------
    # Provenance/history read API
    # ------------------------------------------------------------------

    def get_source_appearances(self, person_id: str) -> list[SourceAppearance]:
        rows = self.conn.execute(
            """
            SELECT person_id, source_file
            FROM source_appearances
            WHERE person_id = ?
            ORDER BY lower(source_file)
            """,
            (person_id,),
        ).fetchall()
        return [SourceAppearance(row["person_id"], row["source_file"]) for row in rows]

    def get_membership_code_history(
        self, person_id: str
    ) -> list[MembershipCodeHistoryEntry]:
        rows = self.conn.execute(
            """
            SELECT person_id, code
            FROM membership_code_history
            WHERE person_id = ?
            ORDER BY lower(code)
            """,
            (person_id,),
        ).fetchall()
        return [MembershipCodeHistoryEntry(row["person_id"], row["code"]) for row in rows]

    # ------------------------------------------------------------------
    # Conservative member write API
    # ------------------------------------------------------------------

    def update_member(self, member: Member) -> None:
        """Persist editable fields that exist in the frozen members table."""

        self.conn.execute(
            """
            UPDATE members
            SET display_name=?,
                title=?,
                first_name=?,
                middle_name=?,
                last_name=?,
                suffix=?,
                institution=?,
                primary_email=?,
                secondary_email=?,
                phone=?,
                address1=?,
                address2=?,
                city=?,
                state_province=?,
                postal_code=?,
                country=?,
                region=?,
                membership_status=?,
                original_membership_code=?,
                member_since=?,
                last_paid_year=?,
                notes=?,
                active=?,
                updated_at=datetime('now')
            WHERE person_id=?
            """,
            (
                member.display_name,
                member.title,
                member.first_name,
                member.middle_name,
                member.last_name,
                member.suffix,
                member.institution,
                member.primary_email,
                member.secondary_email,
                member.phone,
                member.address1,
                member.address2,
                member.city,
                member.state_province,
                member.postal_code,
                member.country,
                member.region,
                member.membership_status,
                member.original_membership_code,
                member.member_since,
                member.last_paid_year,
                member.notes,
                1 if member.active else 0,
                member.person_id,
            ),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Backward-compatible aliases for the first App 3 prototype
    # ------------------------------------------------------------------

    def get_member_count(self) -> int:
        return self.count_members()

    def get_all_members(self) -> list[Member]:
        return self.list_members()

    def save_member(self, member: Member) -> None:
        self.update_member(member)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _table_names(self) -> set[str]:
        rows = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        return {row["name"] for row in rows}

    def _count_rows(self, table_name: str) -> int:
        if table_name not in REQUIRED_TABLES:
            raise ValueError(f"Refusing to count unknown table: {table_name}")
        return int(self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])

    @staticmethod
    def _row_to_member(row: sqlite3.Row) -> Member:
        return Member(
            person_id=row["person_id"],
            display_name=row["display_name"],
            title=row["title"],
            first_name=row["first_name"],
            middle_name=row["middle_name"],
            last_name=row["last_name"],
            suffix=row["suffix"],
            institution=row["institution"],
            primary_email=row["primary_email"],
            secondary_email=row["secondary_email"],
            phone=row["phone"],
            address1=row["address1"],
            address2=row["address2"],
            city=row["city"],
            state_province=row["state_province"],
            postal_code=row["postal_code"],
            country=row["country"],
            region=row["region"],
            membership_status=row["membership_status"],
            original_membership_code=row["original_membership_code"],
            member_since=row["member_since"],
            last_paid_year=row["last_paid_year"],
            active=bool(row["active"]),
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
