from dataclasses import dataclass


@dataclass
class Member:
    """App 3 representation of one row in the canonical App 2 members table.

    This class intentionally mirrors schema/sagp_members_schema.sql.  Optional
    SQLite TEXT fields are represented as str | None; the UI can display None
    as an empty string.
    """

    person_id: str
    display_name: str

    title: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    suffix: str | None = None

    institution: str | None = None
    primary_email: str | None = None
    secondary_email: str | None = None

    phone: str | None = None
    address1: str | None = None
    address2: str | None = None
    city: str | None = None
    state_province: str | None = None
    postal_code: str | None = None
    country: str | None = None
    region: str | None = None

    membership_status: str | None = None
    original_membership_code: str | None = None
    member_since: str | None = None
    last_paid_year: int | None = None

    active: bool = True
    notes: str | None = None

    created_at: str | None = None
    updated_at: str | None = None
