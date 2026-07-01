"""Backward-compatible import wrapper for the App 3 database API.

New App 3 code should import SagpDatabase from database_api.  The Database alias
keeps existing launch code and older imports working during the transition.
"""

from database_api import (  # noqa: F401
    DatabaseSummary,
    MembershipCodeHistoryEntry,
    SagpDatabase,
    SourceAppearance,
)

Database = SagpDatabase
